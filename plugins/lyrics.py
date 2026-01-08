import os
import json
import asyncio
import aiohttp
import logging
import re
import math
import time
from bs4 import BeautifulSoup
from telethon import events, types
from yt_dlp import YoutubeDL
from config import LYRICS_API_KEY, OWNER_ID
from telethon.errors import ChatAdminRequiredError

# Configuration
GENIUS_API = "https://api.genius.com"
TEMP_DIR = os.path.join('data', 'temp_audio')
MAX_LYRICS_LENGTH = 4000
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_data_dir():
    """Create data directory if not exists"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def get_live_prefix():
    """Get current prefix from config file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_data_dir()
        with open(PREFIX_FILE, 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

class DownloadProgress:
    def __init__(self, message):
        self.message = message
        self.last_update = 0
        self.last_percent = 0
        self.completed = False
    
    async def update(self, current, total):
        percent = math.floor((current / total) * 100)
        now = time.time()
        if percent >= self.last_percent + 5 or now - self.last_update >= 1 or percent == 100:
            self.last_percent = percent
            self.last_update = now
            try:
                if percent == 100 and not self.completed:
                    self.completed = True
                    return  # Skip the 100% update since we'll send the file immediately
                await self.message.edit(
                    f"📥 Download Progress: {percent}%\n"
                    f"🔄 {human_readable_size(current)}/{human_readable_size(total)}"
                )
            except Exception as e:
                logger.error(f"Progress update error: {str(e)}")

def human_readable_size(size):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f}{unit}"
        size /= 1024.0
    return f"{size:.2f}GB"

class YTDLProgressHook:
    def __init__(self, progress, loop):
        self.progress = progress
        self.loop = loop
    
    def hook(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                current = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0)
                asyncio.run_coroutine_threadsafe(
                    self.progress.update(current, total),
                    self.loop
                )

async def get_genius_song_info(session, query):
    """Search for song using Genius API"""
    try:
        headers = {"Authorization": f"Bearer {LYRICS_API_KEY}"}
        async with session.get(
            f"{GENIUS_API}/search",
            params={'q': query},
            headers=headers,
            timeout=15
        ) as response:
            if response.status != 200:
                return None
                
            data = await response.json()
            if not data['response']['hits']:
                return None
                
            hit = data['response']['hits'][0]['result']
            return {
                'url': hit['url'],
                'title': hit['title'],
                'artist': hit['primary_artist']['name']
            }
    except Exception as e:
        logger.error(f"Genius API Error: {str(e)}")
        return None

async def scrape_genius_lyrics(session, url):
    """Scrape lyrics from Genius page"""
    try:
        async with session.get(url, timeout=15) as response:
            if response.status != 200:
                return None
                
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try multiple selectors for robustness
            selectors = [
                {'data-lyrics-container': 'true'},  # New Genius
                {'class': 'lyrics'},                # Old Genius
                {'class': 'Lyrics__Container'}      # Alternate
            ]
            
            lyrics_container = None
            for selector in selectors:
                lyrics_container = soup.find('div', selector)
                if lyrics_container:
                    break
            
            if not lyrics_container:
                return None
                
            lyrics = lyrics_container.get_text(separator='\n')
            
            # Clean lyrics
            cleaned_lines = []
            for line in lyrics.split('\n'):
                line = line.strip()
                if line:
                    line = re.sub(r'[\[\(\{].*?[\]\)\}]', '', line)  # Remove annotations
                    line = re.sub(r'\d+', '', line)  # Remove numbers
                    line = line.replace('Embed', '').replace('URLCopyEmbedCopy', '')
                    if line:
                        cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
            
    except Exception as e:
        logger.error(f"Scraping Error: {str(e)}")
        return None

async def process_audio(event, song_info):
    """Download and send audio with proper async handling"""
    audio_file = None
    try:
        loop = asyncio.get_event_loop()
        progress_msg = await event.reply("📥 Downloading audio...")
        progress = DownloadProgress(progress_msg)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [YTDLProgressHook(progress, loop).hook],
            'matchfilter': lambda info: info.get('duration', 0) <= 600,
            'max_filesize': 50_000_000,
            'noplaylist': True,
            'default_search': 'ytsearch1:',
            'extract_flat': False
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(
                        f"{song_info['title']} {song_info['artist']}",
                        download=True
                    )
                )
                
                if not info or not info.get('entries'):
                    await progress_msg.edit("❌ Audio not found")
                    return
                    
                entry = info['entries'][0]
                audio_file = ydl.prepare_filename(entry)
                audio_file = os.path.splitext(audio_file)[0] + '.mp3'
                
                # Immediately send the file without waiting
                await event.client.send_file(
                    event.chat_id,
                    audio_file,
                    attributes=[
                        types.DocumentAttributeAudio(
                            duration=entry.get('duration', 0),
                            title=f"{song_info['title']} - {song_info['artist']}"[:64],
                            performer=song_info['artist'][:64]
                        )
                    ],
                    caption=f"🎧 {song_info['title']} - {song_info['artist']}\n"
                            f"💽 Quality: 192kbps\n"
                            f"⏱ Duration: {entry.get('duration', 0)//60}:{entry.get('duration', 0)%60:02d}"
                )
                await progress_msg.delete()
                
        except Exception as e:
            await progress_msg.edit(f"❌ Download error: {str(e)[:200]}")
            logger.error(f"Download error: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Audio processing error: {str(e)}")
        await event.reply(f"❌ Error: {str(e)[:200]}")
    finally:
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception as e:
                logger.error(f"Error deleting temp file: {str(e)}")

async def setup(bot, user):
    """Setup event handlers"""
    ensure_data_dir()
    os.makedirs(TEMP_DIR, exist_ok=True)
    current_prefix = get_live_prefix()

    @user.on(events.NewMessage(outgoing=True, pattern=f'^{current_prefix}lagu(?: |$)(.*)'))
    async def song_handler(event):
        """Handle song search and download command"""
        query = event.pattern_match.group(1).strip()
        if not query:
            return await event.reply(f"ℹ️ Usage: `{current_prefix}lagu <song title>`")
        
        async with aiohttp.ClientSession() as session:
            try:
                song_info = await get_genius_song_info(session, query)
                if not song_info:
                    return await event.reply("❌ Song not found")
                    
                await process_audio(event, song_info)
                
            except Exception as e:
                logger.error(f"Song Error: {str(e)}")
                await event.reply(f"❌ Error: {str(e)[:200]}")

    @user.on(events.NewMessage(outgoing=True, pattern=f'^{current_prefix}lirik(?: |$)(.*)'))
    async def lyrics_handler(event):
        """Handle lyrics-only search command"""
        query = event.pattern_match.group(1).strip()
        if not query:
            return await event.reply(f"ℹ️ Usage: `{current_prefix}lirik <song title>`")

        async with aiohttp.ClientSession() as session:
            try:
                progress_msg = await event.reply("🔍 Searching lyrics...")
                
                song_info = await get_genius_song_info(session, query)
                if not song_info:
                    return await progress_msg.edit("❌ Lyrics not found")
                    
                lyrics = await scrape_genius_lyrics(session, song_info['url'])
                if not lyrics:
                    return await progress_msg.edit("❌ Failed to get lyrics")
                    
                header = f"🎵 **{song_info['title']}** - {song_info['artist']}\n\n"
                max_length = MAX_LYRICS_LENGTH - len(header)
                
                # Send lyrics in chunks
                for i in range(0, len(lyrics), max_length):
                    chunk = lyrics[i:i+max_length]
                    await event.reply(f"{header}{chunk}", parse_mode='markdown')
                    header = ""  # Only show header for first message
                    
                await progress_msg.delete()
                
            except Exception as e:
                logger.error(f"Lyrics Error: {str(e)}")
                await event.reply(f"❌ Error: {str(e)[:200]}")
                try:
                    await progress_msg.delete()
                except:
                    pass

    @user.on(events.NewMessage(outgoing=True, pattern=f'^{current_prefix}lyrichelp'))
    async def lyrics_help_handler(event):
        """Show lyrics help"""
        help_text = (
            f"```🎵 Lyrics & Music Commands```\n\n"
            f"• `{current_prefix}lagu <query>` - Search and download song\n"
            f"• `{current_prefix}lirik <query>` - Search for lyrics\n"
            f"• `{current_prefix}setprefix <new>` - Change command prefix (Owner)\n"
            f"• `{current_prefix}lyrichelp` - Show this help"
        )
        await event.edit(help_text)