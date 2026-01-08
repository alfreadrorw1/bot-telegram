from asyncio import sleep, TimeoutError
from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
import logging
import asyncio
import os
import json
from config import OWNER_ID

def get_user_folder(user_id=None):
    """Get user-specific folder path"""
    if user_id is None or user_id == OWNER_ID:
        return 'premium'
    return f'premium/userprem_{user_id}'

def get_prefix(user_id=None):
    """Get current prefix for specific user"""
    user_folder = get_user_folder(user_id)
    try:
        with open(f'{user_folder}/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs(user_folder, exist_ok=True)
        with open(f'{user_folder}/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def is_premium_user(user_id):
    """Check if user is premium"""
    try:
        with open('premium/premium.json', 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return False

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except:
        pass

async def setup(bot, client, user_id):
    """Setup sangmata command for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def sangmata_beta(event):
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message_raw = (event.raw_text or '').strip()
        message_lower = message_raw.lower()
        command = "sg"

        if not message_lower:
            return

        if current_prefix == "no":
            parts = message_lower.split(maxsplit=1)
            if not parts or parts[0] != command:
                return
            args_text = parts[1] if len(parts) > 1 else ""
        else:
            if not message_lower.startswith(current_prefix.lower()):
                return
            cmd_body = message_raw[len(current_prefix):].strip()
            parts = cmd_body.split(maxsplit=1)
            if not parts or parts[0].lower() != command:
                return
            args_text = parts[1] if len(parts) > 1 else ""

        reply = await event.get_reply_message()
        chat = "SangMata_beta_bot"
        processing_msg = await event.edit("**⏳ ᴘʀᴏsᴇs...**")
        delete_after = False

        try:
            user_id = None

            if args_text:
                input_text = args_text.strip()
                if input_text.isdigit():
                    user_id = int(input_text)
                else:
                    username = input_text
                    if username.startswith("@"):
                        username = username[1:]
                    if "t.me/" in username:
                        username = username.split("t.me/")[-1].strip("/")
                    try:
                        entity = await client.get_entity(username)
                        user_id = entity.id
                    except Exception:
                        response_msg = await processing_msg.edit("**❌ Tidak dapat menemukan pengguna:** `{args_text}`")
                        delete_after = True
                        return
            elif reply:
                user_id = reply.sender_id
            else:
                response_msg = await processing_msg.edit("**❌ Gunakan perintah dengan:** `sg @username / t.me/username / ID / reply pesan`")
                delete_after = True
                return

            try:
                async with client.conversation(chat, timeout=20) as conv:
                    await conv.send_message(f"/allhistory {user_id}")
                    response = await conv.get_response()

                    if "No data available" in response.text:
                        response_msg = await processing_msg.edit("**⚠️ Tidak ada data history yang tersedia**")
                        delete_after = True
                    elif "Daily limit" in response.text:
                        response_msg = await processing_msg.edit("**⚠️ Kuota harian telah habis, coba lagi besok**")
                        delete_after = True
                    elif "User ID" in response.text or "Username" in response.text:
                        formatted_text = response.text.replace("--", "—").replace("  ", " ")
                        await event.edit(f"{formatted_text}")
                        delete_after = False 
                    else:
                        await event.edit("**🔍 Data ditemukan:**\n\n" + response.text)
                        delete_after = False 

            except TimeoutError:
                response_msg = await processing_msg.edit("**⏰ Waktu tunggu habis, coba lagi nanti**")
                delete_after = True
            except Exception as e:
                response_msg = await processing_msg.edit(f"**❌ Error saat memproses: {str(e)[:200]}**")
                delete_after = True

        except YouBlockedUserError:
            response_msg = await processing_msg.edit("**⚠️ Silakan unblock @SangMata_beta_bot terlebih dahulu**")
            delete_after = True
        except Exception as ex:
            logging.error(f"Error in sg command: {str(ex)}")
            response_msg = await processing_msg.edit("**❌ Terjadi kesalahan internal**")
            delete_after = True
        finally:
            if delete_after:
                await asyncio.sleep(5)
                try:
                    await safe_delete(processing_msg)
                    if 'response_msg' in locals():
                        await safe_delete(response_msg)
                except:
                    pass