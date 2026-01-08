import os
import json
import requests
import base64
import asyncio
from io import BytesIO
from telethon import events, types
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
    except (MessageDeleteForbiddenError, Exception):
        pass

async def safe_edit(message, text):
    """Safely edit a message with error handling"""
    try:
        await message.edit(text)
    except (MessageNotModifiedError, Exception):
        pass

async def get_profile_photo(user, client):
    """Get user profile photo with error handling"""
    try:
        photo = await client.download_profile_photo(user, file=BytesIO())
        if photo:
            photo.seek(0)
            return photo
    except Exception:
        pass
    return None

async def photo_to_base64(photo_bytes):
    """Convert photo to base64 with error handling"""
    if photo_bytes:
        try:
            photo_bytes.seek(0)
            return base64.b64encode(photo_bytes.read()).decode("utf-8")
        except Exception:
            pass
    return None

def get_unique_color(user_id, offset=0):
    """Generate a unique color based on user ID"""
    hex_color = f"#{(user_id * 1234567 + offset) % 0xFFFFFF:06x}"
    return hex_color

def get_initials(name):
    """Get initials from name"""
    if not name:
        return "?"
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if len(name) >= 2 else name[0].upper()

async def generate_quote(user, text, avatar_b64=None):
    """Generate quote sticker using API"""
    try:
        text_color = get_unique_color(user.id)
        avatar_color = get_unique_color(user.id, 1)
        
        quote_data = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": "#000000",
            "width": 512,
            "height": 512,
            "scale": 2,
            "quality": 100,
            "messages": [{
                "entities": [],
                "avatar": True,
                "from": {
                    "id": user.id,
                    "name": user.first_name,
                    "photo": {
                        "url": f"data:image/png;base64,{avatar_b64}" if avatar_b64 else None,
                        "width": 512,
                        "height": 512,
                        "color": avatar_color if not avatar_b64 else None,
                        "initials": get_initials(user.first_name) if not avatar_b64 else None
                    }
                },
                "text": text,
                "textColor": text_color,
                "replyMessage": {}
            }]
        }

        response = requests.post(
            "https://bot.lyo.su/quote/generate",
            json=quote_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        response.raise_for_status()

        sticker_data = base64.b64decode(response.json()["result"]["image"])
        sticker = BytesIO(sticker_data)
        sticker.name = "sticker.webp"
        sticker.seek(0)
        return sticker
    except Exception as e:
        print(f"Error generating quote: {e}")
        return None

async def setup(bot, client, user_id):
    """Setup quote sticker commands for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def q_handler(event):
        """Handle quote sticker commands"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.text or '').strip()
        
        # Check command pattern
        is_quote_cmd = False
        cmd = ""
        
        if current_prefix == "no":
            if message.lower() == "q" or message.lower().startswith("q "):
                is_quote_cmd = True
                cmd = message[1:].strip() if len(message) > 1 else ""
        else:
            if message.lower() == current_prefix + "q" or message.lower().startswith(current_prefix + "q "):
                is_quote_cmd = True
                cmd = message[len(current_prefix)+1:].strip() if len(message) > len(current_prefix)+1 else ""
        
        if not is_quote_cmd:
            return

        # Initialize variables
        text = ""
        target_user = await client.get_me()  # Default to self
        
        # Case 1: Just "q" (must be reply)
        if not cmd and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text or reply.raw_text or ""
            target_user = await reply.get_sender()
        elif not cmd:
            error_msg = await event.reply("```🚫 Harus reply pesan atau sertakan text!```")
            await asyncio.sleep(3)
            await safe_delete(error_msg)
            await safe_delete(event)
            return
        else:
            # Case 2 and 3: Check for username mentions
            parts = cmd.split()
            username_in_cmd = None
            
            # Find username in command (can be anywhere)
            for part in parts:
                if part.startswith("@"):
                    username_in_cmd = part
                    parts.remove(part)
                    break
            
            text = " ".join(parts).strip()
            
            # If username found, use that user
            if username_in_cmd:
                try:
                    target_user = await client.get_entity(username_in_cmd)
                except:
                    error_msg = await event.reply("```❌ Username tidak ditemukan.```")
                    await asyncio.sleep(3)
                    await safe_delete(error_msg)
                    await safe_delete(event)
                    return
            # Else if no username and no reply, use owner profile with custom text
            elif not event.is_reply:
                target_user = await client.get_me()
            # Else if reply but with text, use owner profile with custom text (ignore replied message)
            else:
                target_user = await client.get_me()

        if not text:
            error_msg = await event.reply("```🚫 Tidak ada text untuk diquote!```")
            await asyncio.sleep(3)
            await safe_delete(error_msg)
            await safe_delete(event)
            return

        status = await event.reply("```Sedang membuat stiker quote...```")

        try:
            # Get profile photo
            avatar = await get_profile_photo(target_user, client)
            avatar_b64 = await photo_to_base64(avatar) if avatar else None

            # Generate sticker
            sticker = await generate_quote(target_user, text, avatar_b64)
            
            if sticker:
                await client.send_file(
                    event.chat_id,
                    sticker,
                    reply_to=event.reply_to_msg_id if event.is_reply and not cmd else None,
                    force_document=False,
                    attributes=[
                        types.DocumentAttributeFilename("sticker.webp"),
                        types.DocumentAttributeSticker(
                            alt="quote",
                            stickerset=types.InputStickerSetEmpty()
                        )
                    ]
                )
            else:
                await safe_edit(status, "❌ **Gagal membuat stiker quote**")
                await asyncio.sleep(3)
        except Exception as e:
            await safe_edit(status, f"❌ **Error:** `{str(e)[:200]}`")
            await asyncio.sleep(3)
        finally:
            await safe_delete(status)
            await safe_delete(event)