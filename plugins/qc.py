import os
import json
import requests
import base64
import asyncio
from io import BytesIO
from telethon import events, types
from config import OWNER_ID

def get_prefix():
    """Get current prefix from config"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def get_profile_photo(user, client):
    try:
        photo = await client.download_profile_photo(user, file=BytesIO())
        if photo:
            photo.seek(0)
            return photo
    except:
        pass
    return None

async def photo_to_base64(photo_bytes):
    if photo_bytes:
        photo_bytes.seek(0)
        return base64.b64encode(photo_bytes.read()).decode("utf-8")
    return None

def get_unique_color(user_id, offset=0):
    hex_color = f"#{(user_id * 1234567 + offset) % 0xFFFFFF:06x}"
    return hex_color

def get_initials(name):
    if not name:
        return "?"
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if len(name) >= 2 else name[0].upper()

async def generate_quote(user, text, avatar_b64=None):
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

async def setup(bot, user):
    @user.on(events.NewMessage())
    async def q_handler(event):
        # Skip if not from owner
        if event.sender_id != OWNER_ID:
            return

        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
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
        username = None
        target_user = await user.get_me()  # Default to owner
        
        # Case 1: Just "q" (must be reply)
        if not cmd and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text or reply.raw_text or ""
            target_user = await reply.get_sender()
        elif not cmd:
            error_msg = await event.edit("```🚫 Harus reply pesan atau sertakan text!```")
            await asyncio.sleep(3)
            await error_msg.delete()
            await event.delete()
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
                    target_user = await user.get_entity(username_in_cmd)
                except:
                    error_msg = await event.edit("```❌ Username tidak ditemukan.```")
                    await asyncio.sleep(3)
                    await error_msg.delete()
                    await event.delete()
                    return
            # Else if no username and no reply, use owner profile with custom text
            elif not event.is_reply:
                target_user = await user.get_me()
            # Else if reply but with text, use owner profile with custom text (ignore replied message)
            else:
                target_user = await user.get_me()

        if not text:
            error_msg = await event.edit("```🚫 Tidak ada text untuk diquote!```")
            await asyncio.sleep(3)
            await error_msg.delete()
            await event.delete()
            return

        status = await event.edit("```Sabar Ya Ler........```")

        try:
            # Get profile photo
            avatar = await get_profile_photo(target_user, user)
            avatar_b64 = await photo_to_base64(avatar) if avatar else None

            # Generate sticker
            sticker = await generate_quote(target_user, text, avatar_b64)
            
            if sticker:
                await user.send_file(
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
                await status.edit("❌ **Gagal membuat stiker quote**")
                await asyncio.sleep(3)
        except Exception as e:
            await status.edit(f"❌ **Error:** `{str(e)[:200]}`")
            await asyncio.sleep(3)
        finally:
            await status.delete()
            await event.delete()