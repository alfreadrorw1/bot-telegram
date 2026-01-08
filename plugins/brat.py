import os
import json
import re
import asyncio
import requests
from io import BytesIO
from PIL import Image
from telethon import events
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def generate_brat_image(text: str) -> BytesIO:
    """
    Generate a brat image from text using the caliphdev API
    """
    try:
        response = requests.get(
            "https://aqul-brat.hf.space",
            params={'text': text},
            stream=True,
            timeout=15
        )
        response.raise_for_status()

        # Convert to sticker format
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        max_size = (512, 512)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Create transparent canvas
        canvas = Image.new("RGBA", max_size, (0, 0, 0, 0))
        x = (max_size[0] - img.width) // 2
        y = (max_size[1] - img.height) // 2
        canvas.paste(img, (x, y), img)

        bio = BytesIO()
        bio.name = "sticker.webp"
        canvas.save(bio, format="WEBP", quality=95)
        bio.seek(0)
        return bio

    except Exception as e:
        raise Exception(f"Failed to generate brat image: {str(e)}")

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def brat_handler(event):
        """Generate brat sticker from text"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_brat_cmd = False
        text = ""
        
        if current_prefix:
            if msg.startswith(f"{current_prefix}brat"):
                is_brat_cmd = True
                text = msg[len(current_prefix)+5:].strip()
        else:
            if msg.lower().startswith("brat"):
                is_brat_cmd = True
                text = msg[4:].strip()
                
        if not is_brat_cmd:
            return

        # Check if text is provided
        if not text:
            # Try to get quoted message
            if event.is_reply:
                reply = await event.get_reply_message()
                text = reply.text or reply.raw_text or ""
            
            if not text:
                status = await event.reply(f"<blockquote>🚫Masukan teksnya woii</blockquote>", parse_mode="html")
                await asyncio.sleep(5)
                await status.delete()
                await event.delete()
                return

        status = await event.reply("<blockquote>🔄 Sedang membuat sticker brat...</blockquote>", parse_mode="html")
        
        try:
            # Generate brat image and convert to sticker
            sticker = await generate_brat_image(text)
            
            # Send sticker
            await user.send_file(
                event.chat_id,
                sticker,
                reply_to=event.id if event.is_reply else None,
                force_document=False,
                attributes=[],
                allow_cache=False
            )
            await status.delete()
            
        except Exception as e:
            await status.edit(f"<blockquote>❌ Gagal membuat sticker brat: {str(e)[:200]}</blockquote>", parse_mode="html")
            await asyncio.sleep(5)
            await status.delete()
        finally:
            await event.delete()