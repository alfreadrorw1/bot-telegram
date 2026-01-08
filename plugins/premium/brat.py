# plugins/premium/brat.py
import os
import json
import re
import asyncio
import requests
from io import BytesIO
from PIL import Image
from telethon import events
from config import OWNER_ID
from telethon.errors import MessageNotModifiedError, MessageDeleteForbiddenError

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

async def generate_brat_image(text: str) -> BytesIO:
    """
    Generate a brat image from text using the caliphdev API
    Returns BytesIO object containing the WEBP image
    """
    try:
        # Make API request with timeout
        response = requests.get(
            "https://aqul-brat.hf.space",
            params={'text': text},
            stream=True,
            timeout=15
        )
        response.raise_for_status()

        # Process image
        with Image.open(BytesIO(response.content)) as img:
            img = img.convert("RGBA")
            max_size = (512, 512)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Create transparent canvas
            canvas = Image.new("RGBA", max_size, (0, 0, 0, 0))
            x = (max_size[0] - img.width) // 2
            y = (max_size[1] - img.height) // 2
            canvas.paste(img, (x, y), img)

            # Save as WEBP
            bio = BytesIO()
            bio.name = "sticker.webp"
            canvas.save(bio, format="WEBP", quality=95)
            bio.seek(0)
            return bio

    except Exception as e:
        raise Exception(f"Failed to generate brat image: {str(e)}")

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except (MessageDeleteForbiddenError, Exception):
        pass

async def setup(bot, client, user_id):
    """Setup brat sticker generator for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def brat_handler(event):
        """Handle brat sticker generation commands"""
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
        is_brat_cmd = False
        text = ""
        
        if current_prefix == "no":
            if msg.lower().startswith("brat"):
                is_brat_cmd = True
                text = msg[4:].strip()
        else:
            if msg.lower().startswith(f"{current_prefix}brat"):
                is_brat_cmd = True
                text = msg[len(current_prefix)+4:].strip()
                
        if not is_brat_cmd:
            return

        # Get text from reply if no text provided
        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text or reply.raw_text or ""

        if not text:
            status = await event.reply(
                "<blockquote>🚫 Masukan teksnya woii</blockquote>", 
                parse_mode="html"
            )
            await asyncio.sleep(5)
            await safe_delete(status)
            await safe_delete(event)
            return

        # Generate sticker
        status = await event.reply(
            "<blockquote>🔄 Sedang membuat sticker brat...</blockquote>",
            parse_mode="html"
        )
        
        try:
            sticker = await generate_brat_image(text)
            
            await client.send_file(
                event.chat_id,
                sticker,
                reply_to=event.reply_to_msg_id if event.is_reply else None,
                force_document=False,
                attributes=[],
                allow_cache=False
            )
            
        except Exception as e:
            await status.edit(
                f"<blockquote>❌ Gagal membuat sticker brat: {str(e)[:200]}</blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(5)
        finally:
            await safe_delete(status)
            await safe_delete(event)

    