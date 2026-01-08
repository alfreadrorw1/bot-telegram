# plugins/mediafire_manager.py
import os
import re
import json
import time
import asyncio
import aiohttp
from telethon import events
from config import OWNER_ID
from urllib.parse import unquote, urlparse
from math import floor

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
DOWNLOAD_DIR = 'downloads'

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_live_prefix():
    """Get current prefix from config file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        with open(PREFIX_FILE, 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def download_from_mediafire(url, event):
    """Download file from MediaFire with progress tracking"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None, None, f"Failed to access URL (HTTP {resp.status})"
                
                html = await resp.text()
                match = re.search(r'aria-label="Download file"\s+href="([^"]+)"', html)
                if not match:
                    match = re.search(r'class="input popsok"\s+value="([^"]+)"', html)
                    if not match:
                        return None, None, "Download link not found"
                
                download_url = match.group(1)
                if download_url.startswith('//'):
                    download_url = 'https:' + download_url
                elif download_url.startswith('/'):
                    download_url = 'https://www.mediafire.com' + download_url
                
                filename = os.path.basename(unquote(urlparse(url).path)) or "mediafire_download"
                file_path = os.path.join(DOWNLOAD_DIR, filename)
                
                async with session.get(download_url) as resp:
                    if resp.status != 200:
                        return None, None, f"Download failed (HTTP {resp.status})"
                    
                    content_disposition = resp.headers.get('Content-Disposition', '')
                    if 'filename=' in content_disposition:
                        filename = unquote(content_disposition.split('filename=')[1].strip('"'))
                        file_path = os.path.join(DOWNLOAD_DIR, filename)
                    
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    last_progress = -1
                    start_time = time.time()

                    with open(file_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = floor((downloaded / total_size) * 100)

                            # Update every 5% or 1 second
                            now = time.time()
                            if progress >= last_progress + 5 or now - start_time >= 1:
                                last_progress = progress
                                start_time = now
                                text = (
                                    f"📥 **Downloading:** `{filename}`\n"
                                    f"📦 **Progress:** `{progress}%`\n"
                                    f"🔄 **Status:** `{human_readable_size(downloaded)}/{human_readable_size(total_size)}`"
                                )
                                if event.text != text:
                                    await event.edit(text)

                    return file_path, filename, None
                    
        except Exception as e:
            return None, None, f"Error: {str(e)}"

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def mediafire_handler(event):
        """Handle mediafire command (download)"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}mediafire"):
                return
            url = msg[len(current_prefix)+10:].strip()
        else:
            if not msg.lower().startswith("mediafire"):
                return
            url = msg[9:].strip()

        if 'mediafire.com' not in url:
            await event.edit("```❌ Invalid MediaFire URL```")
            return

        if event.text != "```📥 Preparing download...```":
            await event.edit("```📥 Preparing download...```")

        try:
            file_path, filename, error = await download_from_mediafire(url, event)
            if error:
                await event.edit(f"```❌ {error}```")
                return
            
            await bot.send_file(
                OWNER_ID,
                file_path,
                caption=f"```✅ Download complete```\n📁 `{filename}`"
            )
            await event.edit(f"```✅ File sent to private chat```\n📁 `{filename}`")
            
        except Exception as e:
            await event.edit(f"```❌ Error: {str(e)[:200]}```")
        finally:
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def mediafire_help_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}mfhelp"):
                return
        else:
            if not msg.lower().startswith("mfhelp"):
                return

        prefix = current_prefix if current_prefix else "[no prefix]"
        help_text = (
            f"```📢 MediaFire Manager Help```\n\n"
            f"• {prefix}mediafire <url> - Download from MediaFire\n"
            f"• {prefix}mfhelp - Show this help"
        )
        if event.text != help_text:
            await event.edit(help_text)