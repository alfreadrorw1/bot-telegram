# plugins/lagu.py
import os
import json
import yt_dlp
import asyncio
import aiohttp
from telethon import events, types
from config import OWNER_ID
from urllib.parse import quote
import re

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

def sanitize_filename(filename):
    """Sanitize filename untuk menghapus karakter tidak valid"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]  # Batasi panjang filename

async def search_youtube_video(query):
    """Search for YouTube video using alternative API"""
    try:
        search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                html = await response.text()
                
                # Extract video IDs from search results
                video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
                if video_ids:
                    return f"https://youtu.be/{video_ids[0]}"
                
        return None
    except:
        return None

async def download_youtube_audio(query, download_path):
    """Download audio dari YouTube dengan options yang lebih robust"""
    # Jika query bukan URL, cari video dulu
    if not query.startswith(('http://', 'https://', 'youtu.be', 'youtube.com')):
        video_url = await search_youtube_video(query)
        if video_url:
            query = video_url
        else:
            raise Exception("Tidak dapat menemukan video untuk query tersebut")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{download_path}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'writethumbnail': True,
        'embedthumbnail': True,
        'addmetadata': True,

        # Fix untuk error YouTube restriction (pakai web client, bukan android)
        'compat_opts': ['manifest-filesize-approx'],
        'extract_flat': False,

        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'player_skip': ['configs'],
            }
        },

        # User-Agent modern
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
        },

        # Network settings
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'continue_dl': True,

        # Throttling
        'buffersize': 1024 * 32,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info tanpa download dulu
            info = ydl.extract_info(query, download=False)
            
            # Cek jika video tersedia
            if info.get('availability') == 'unavailable':
                raise Exception("Video tidak tersedia atau dibatasi aksesnya")
            
            # Download video
            info = ydl.extract_info(query, download=True)
            
            filename = ydl.prepare_filename(info)
            
            # Ganti extension ke .mp3
            if filename.endswith('.webm'):
                mp3_filename = filename[:-5] + '.mp3'
            elif filename.endswith('.m4a'):
                mp3_filename = filename[:-4] + '.mp3'
            elif filename.endswith('.opus'):
                mp3_filename = filename[:-5] + '.mp3'
            else:
                mp3_filename = filename
                
            # Pastikan file MP3 benar-benar ada
            if not os.path.exists(mp3_filename):
                base_name = os.path.splitext(filename)[0]
                for ext in ['.mp3', '.webm', '.m4a', '.opus']:
                    possible_file = base_name + ext
                    if os.path.exists(possible_file):
                        mp3_filename = possible_file
                        break
            
            return mp3_filename, info
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "not available" in error_msg or "unavailable" in error_msg:
            raise Exception("Video tidak tersedia atau dibatasi aksesnya")
        elif "Private video" in error_msg:
            raise Exception("Video bersifat private")
        elif "Sign in" in error_msg:
            raise Exception("Video memerlukan login")
        elif "age restricted" in error_msg.lower():
            raise Exception("Video dibatasi usia (age restricted)")
        else:
            raise Exception(f"Gagal download: {error_msg[:100]}")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except:
        pass

async def setup(bot, client, user_id):
    """Setup lagu downloader for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def lagu_handler(event):
        """Handle lagu download commands"""
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
        is_lagu_cmd = False
        query = ""
        
        if current_prefix:
            if msg.startswith(f"{current_prefix}lagu "):
                is_lagu_cmd = True
                query = msg[len(current_prefix)+5:].strip()
        else:
            if msg.lower().startswith("lagu "):
                is_lagu_cmd = True
                query = msg[5:].strip()
                
        if not is_lagu_cmd or not query:
            return

        # Buat folder download jika belum ada
        download_dir = "data/download"
        os.makedirs(download_dir, exist_ok=True)

        processing_msg = await event.reply(
            "<blockquote>🔍 Mencari lagu...</blockquote>",
            parse_mode="html"
        )

        try:
            # Download audio
            temp_filename = os.path.join(download_dir, f"temp_{event.id}")
            mp3_filename, info = await download_youtube_audio(query, temp_filename)
            
            # Dapatkan metadata
            title = info.get('title', 'Unknown Title')
            artist = info.get('uploader', 'Unknown Artist')
            duration = info.get('duration', 0)
            
            # Format durasi
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
            
            # Sanitize filename
            safe_title = sanitize_filename(f"{artist} - {title}" if artist != 'Unknown Artist' else title)
            final_filename = os.path.join(download_dir, f"{safe_title}.mp3")
            
            if mp3_filename != final_filename and os.path.exists(mp3_filename):
                os.rename(mp3_filename, final_filename)
                mp3_filename = final_filename
            
            # Caption
            caption = (
                f"<b>🎵 {title}</b>\n"
                f"<b>👤 {artist}</b>\n"
                f"<b>⏱️ {duration_str}</b>\n\n"
                f"<i>Downloaded via @Alfreadprem_bot</i>"
            )
            
            # Cek ukuran file
            file_size = os.path.getsize(mp3_filename)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                await processing_msg.edit(
                    "<blockquote>❌ File terlalu besar (>50MB), tidak dapat dikirim</blockquote>",
                    parse_mode="html"
                )
                await asyncio.sleep(3)
                return
            
            await client.send_file(
                event.chat_id,
                mp3_filename,
                caption=caption,
                parse_mode="html",
                force_document=False,
                attributes=[
                    types.DocumentAttributeAudio(
                        duration=duration,
                        title=title,
                        performer=artist
                    )
                ]
            )
            
            await processing_msg.edit(
                "<blockquote>✅ Lagu berhasil didownload dan dikirim!</blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(3)
            await safe_delete(processing_msg)
            
        except Exception as e:
            error_msg = str(e)
            await processing_msg.edit(
                f"<blockquote>❌ Gagal download lagu: {error_msg[:150]}</blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(5)
            await safe_delete(processing_msg)
            
        finally:
            try:
                for file in os.listdir(download_dir):
                    if file.startswith(f"temp_{event.id}") or file.startswith("temp_download"):
                        file_path = os.path.join(download_dir, file)
                        if os.path.exists(file_path):
                            os.remove(file_path)
            except:
                pass

    @client.on(events.NewMessage())
    async def lagu_help_handler(event):
        """Handle lagu help command"""
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        is_help_cmd = False
        if current_prefix:
            if msg == f"{current_prefix}laguhelp":
                is_help_cmd = True
        else:
            if msg.lower() == "laguhelp":
                is_help_cmd = True
                
        if not is_help_cmd:
            return

        help_text = (
            "<blockquote>🎵 <b>Bantuan Download Lagu</b></blockquote>\n\n"
            "<blockquote><b>Cara penggunaan:</b></blockquote>\n"
            f"<blockquote><code>{current_prefix if current_prefix else ''}lagu [judul/link]</code></blockquote>\n\n"
            "<blockquote><b>Contoh:</b></blockquote>\n"
            f"<blockquote><code>{current_prefix if current_prefix else ''}lagu coldplay yellow</code></blockquote>\n"
            f"<blockquote><code>{current_prefix if current_prefix else ''}lagu https://youtu.be/abc123</code></blockquote>\n\n"
            "<blockquote><b>Fitur:</b></blockquote>\n"
            "<blockquote>• Download lagu dari YouTube</blockquote>\n"
            "<blockquote>• Kualitas audio 192kbps</blockquote>\n"
            "<blockquote>• Metadata lengkap (judul, artis, durasi)</blockquote>\n"
            "<blockquote>• Thumbnail embedded</blockquote>\n"
            "<blockquote>• Auto search jika diberikan judul</blockquote>"
        )
        
        await event.reply(help_text, parse_mode="html")
        await safe_delete(event)