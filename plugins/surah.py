# audiosurah.py
import os
import json
import aiohttp
import time
import math
from telethon import events, types
from config import OWNER_ID

# File configuration
CONFIG_DIR = 'data'
TEMP_AUDIO_DIR = os.path.join(CONFIG_DIR, 'temp_audio')
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

# Create directories if they don't exist
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

SURAH_NAMES = {
    1: "Al-Fatihah (The Opening)",
    2: "Al-Baqarah (The Cow)",
    # ... (all 114 surahs)
    55: "Ar-Rahman (The Beneficent)",
    # ... (remaining surahs)
    114: "An-Nas (Mankind)"
}

def human_readable_size(size):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

async def download_audio(url, filename, event):
    """Download audio file with progress tracking"""
    filepath = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None, f"HTTP Error {response.status}"
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                last_progress = -1
                last_update = time.time()
                
                filepath = os.path.join(TEMP_AUDIO_DIR, filename)
                
                with open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        progress = math.floor((downloaded / total_size) * 100)
                        
                        if progress >= last_progress + 5 or time.time() - last_update >= 1:
                            last_progress = progress
                            last_update = time.time()
                            await event.edit(
                                f"📥 Downloading Surah Audio\n"
                                f"📦 Progress: {progress}%\n"
                                f"🔄 {human_readable_size(downloaded)}/{human_readable_size(total_size)}"
                            )
                
                return filepath, None
    except Exception as e:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return None, f"Download error: {str(e)}"

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def audiosurah_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Command detection
        if current_prefix == "no":
            if not msg.lower().startswith("audiosurah"):
                return
            surah_number = msg[10:].strip()
        else:
            if not msg.startswith(current_prefix):
                return
            cmd = msg[len(current_prefix):].strip().lower()
            if not cmd.startswith("audiosurah"):
                return
            surah_number = cmd[10:].strip()
        
        # Show help if no number provided
        if not surah_number:
            surah_list = "\n".join([f"{k}: {v}" for k,v in SURAH_NAMES.items()])
            await event.reply(
                "🔍 Usage:\n"
                f"{current_prefix}audiosurah [1-114]\n\n"
                "📜 Surah List:\n"
                f"{surah_list}"
            )
            return

        processing = await event.reply("📥 Preparing audio download...")
        filepath = None

        try:
            surah_num = int(surah_number)  # Fixed variable name
            if surah_num not in SURAH_NAMES:
                await processing.edit("❌ Surah number must be between 1-114")
                return

            surah_name = SURAH_NAMES[surah_num]
            audio_url = f"https://api.lolhuman.xyz/api/quran/audio/{surah_num}?apikey=efcb180d3fd3134748648887"  # Fixed variable name
            
            filename = f"surah_{surah_num}_{surah_name.split(' ')[0]}.mp3"
            filepath, error = await download_audio(audio_url, filename, processing)
            
            if error:
                await processing.edit(f"❌ {error}")
                return

            try:
                await bot.send_file(
                    event.chat_id,
                    filepath,
                    voice_note=True,
                    attributes=[
                        types.DocumentAttributeAudio(
                            voice=True,
                            title=f"Surah {surah_name}",
                            performer="Quran Recitation"
                        )
                    ],
                    caption=f"🎧 {surah_name}"
                )
                await processing.edit(f"✅ Successfully sent Surah {surah_name}")
            except:
                await bot.send_file(
                    event.chat_id,
                    filepath,
                    caption=f"🎧 {surah_name} (Audio)"
                )
                await processing.edit(f"✅ Successfully sent Surah {surah_name}")

        except ValueError:
            await processing.edit("❌ Please enter a valid surah number (1-114)")
        except Exception as e:
            await processing.edit(f"❌ Error: {str(e)[:200]}")
        finally:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass