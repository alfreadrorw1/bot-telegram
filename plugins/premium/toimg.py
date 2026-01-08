import os
import json
import random
import asyncio
from telethon import events
from telethon.tl.types import DocumentAttributeVideo
from telethon.errors import MessageNotModifiedError, MessageDeleteForbiddenError
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
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
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
    except (MessageDeleteForbiddenError, Exception):
        pass

async def safe_edit(message, text):
    """Safely edit a message with error handling"""
    try:
        await message.edit(text)
    except (MessageNotModifiedError, Exception):
        pass

async def setup(bot, client, user_id):
    """Setup sticker creation commands for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def sticker_handler(event):
        """Handle sticker creation commands"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # Check command format
        is_sticker_cmd = False
        command = ""
        args = ""
        
        if current_prefix:
            if msg.startswith(current_prefix):
                cmd_part = msg[len(current_prefix):].strip().split(maxsplit=1)
                if cmd_part and cmd_part[0].lower() in ['img']:
                    is_sticker_cmd = True
                    command = cmd_part[0].lower()
                    args = cmd_part[1] if len(cmd_part) > 1 else ""
        else:
            cmd_part = msg.lower().split(maxsplit=1)
            if cmd_part and cmd_part[0] in ['img']:
                is_sticker_cmd = True
                command = cmd_part[0].lower()
                args = cmd_part[1] if len(cmd_part) > 1 else ""
                
        if not is_sticker_cmd:
            return

        if not event.is_reply:
            status = await event.reply(f"```❌ Harus reply sticker dengan caption {current_prefix}{command}```")
            await asyncio.sleep(3)
            await safe_delete(status)
            await safe_delete(event)
            return

        reply_msg = await event.get_reply_message()
        status = await event.reply("```🔄 Memproses sticker...```")

        try:
            # Check media type
            if not (reply_msg.photo or reply_msg.video or 
                  (reply_msg.document and (reply_msg.document.mime_type.startswith('image/') or 
                                         reply_msg.document.mime_type.startswith('video/')))):
                await safe_edit(status, "```❌ Format tidak didukung! Hanya sticker```")
                await asyncio.sleep(3)
                await safe_delete(status)
                return

            # Process packname and author
            parts = args.split('|', 1)
            packname = parts[0].strip() if parts and parts[0].strip() else 'Sticker Pack'
            author = parts[1].strip() if len(parts) > 1 and parts[1].strip() else 'Userbot'

            # Video duration check
            if reply_msg.video or (reply_msg.document and reply_msg.document.mime_type.startswith('video/')):
                duration = 0
                for attr in reply_msg.document.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        duration = attr.duration
                        break
                if duration > 10:
                    await safe_edit(status, "```❌ Video terlalu panjang! Maksimal 10 detik```")
                    await asyncio.sleep(3)
                    await safe_delete(status)
                    return

            # Create user-specific sticker directory
            user_sticker_dir = os.path.join(get_user_folder(current_user_id), 'stickers')
            os.makedirs(user_sticker_dir, exist_ok=True)

            # Download media with proper file extension
            temp_file = os.path.join(user_sticker_dir, f"temp_{random.randint(1000,9999)}")
            if reply_msg.photo or (reply_msg.document and reply_msg.document.mime_type.startswith('image/')):
                temp_file += '.jpg'
            else:
                temp_file += '.mp4'
                
            await reply_msg.download_media(file=temp_file)
            
            # Send as sticker with explicit mime type
            if reply_msg.photo or (reply_msg.document and reply_msg.document.mime_type.startswith('image/')):
                mime_type = 'image/jpeg'
            else:
                mime_type = 'video/mp4'
            
            await client.send_file(
                event.chat_id,
                temp_file,
                force_document=False,
                allow_cache=False,
                sticker=True,
                attributes=[],
                reply_to=reply_msg.id,
                mime_type=mime_type,
                packname=packname,
                author=author
            )
            
            await safe_delete(status)
            await safe_delete(event)

        except Exception as e:
            await safe_edit(status, f"```❌ Gagal membuat sticker: {str(e)[:200]}```")
            await asyncio.sleep(5)
            await safe_delete(status)
        finally:
            try:
                if 'temp_file' in locals() and os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass