import os
import json
import re
import random
import asyncio
import requests
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
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

async def search_image_bing(query: str) -> str:
    """
    Search for images using Bing and return a random image URL
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    params = {
        'q': query,
        'form': 'HDRSC2',
        'first': '1',
        'tsc': 'ImageHoverTitle',
        'count': 50  # Try to get more results
    }

    try:
        response = requests.get(
            'https://www.bing.com/images/search',
            params=params,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        image_elements = soup.find_all('a', class_='iusc')

        image_urls = []
        for elem in image_elements:
            m = re.search(r"murl&quot;:&quot;(.*?)&quot;", str(elem))
            if m and m.group(1).startswith(('http://', 'https://')):
                image_urls.append(m.group(1))

        if not image_urls:
            raise Exception("No images found for your query")

        return random.choice(image_urls[:50])  # Limit to first 50 results

    except Exception as e:
        raise Exception(f"Bing search failed: {str(e)}")

async def create_sticker(image_url: str) -> BytesIO:
    """Download image and convert to sticker format"""
    try:
        res = requests.get(image_url, stream=True, timeout=15)
        res.raise_for_status()

        img = Image.open(BytesIO(res.content)).convert("RGBA")
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
        raise Exception(f"Image processing failed: {str(e)}")

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def bing_sticker_handler(event):
        """Create sticker from Bing image search"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_sticker_cmd = False
        query = "meme"
        
        if current_prefix:
            if msg.startswith(f"{current_prefix}stikker"):
                is_sticker_cmd = True
                query = msg[len(current_prefix)+8:].strip() or "meme"
        else:
            if msg.lower().startswith("stikker"):
                is_sticker_cmd = True
                query = msg[7:].strip() or "meme"
                
        if not is_sticker_cmd:
            return

        status = await event.reply(f"```🔍 Mencari gambar '{query}'...```")
        
        try:
            # Step 1: Search for image
            image_url = await search_image_bing(query)
            
            # Step 2: Create sticker
            sticker = await create_sticker(image_url)
            
            # Step 3: Send sticker
            await user.send_file(
                event.chat_id,
                sticker,
                reply_to=event.id,
                force_document=False,
                attributes=[]
            )
            await status.delete()
            
        except Exception as e:
            await status.edit(f"```❌ Gagal membuat stiker: {str(e)[:200]}```")
            await asyncio.sleep(5)
            await status.delete()
        finally:
            await event.delete()