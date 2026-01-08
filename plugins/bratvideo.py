import os
import json
import asyncio
import aiohttp
from io import BytesIO
from pathlib import Path
import subprocess
from telethon import events
from telethon.tl.types import (
    DocumentAttributeVideo,
    DocumentAttributeSticker,
    InputStickerSetShortName
)
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
TEMP_DIR = Path('database/sampah')
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def get_brat_video(text: str) -> bytes:
    """Get brat video from API with fallback"""
    urls = [
        f'https://brat.caliphdev.com/api/brat?text={text}',
        f'https://aqul-brat.hf.space/?text={text}'
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.read()
            except:
                continue
        raise Exception("Semua API tidak merespon")

async def create_video_sticker(frame_paths: list, sender: str) -> BytesIO:
    """Combine frames into a video sticker with proper path handling"""
    file_list_path = TEMP_DIR / f'{sender}.txt'
    output_path = TEMP_DIR / f'{sender}-output.webm'
    
    # Create FFmpeg input file with relative paths
    with open(file_list_path, 'w') as f:
        for frame in frame_paths:
            frame_name = Path(frame).name
            f.write(f"file '{frame_name}'\nduration 0.5\n")
        f.write(f"file '{Path(frame_paths[-1]).name}'\nduration 3\n")
    
    # Run FFmpeg with suppressed output
    try:
        subprocess.run([
            'ffmpeg', '-y',
            '-loglevel', 'error',  # Suppress FFmpeg output
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path.name,
            '-vf', 'fps=30,scale=512:512:force_original_aspect_ratio=decrease,format=yuv420p',
            '-c:v', 'libvpx-vp9',
            '-b:v', '500k',
            '-crf', '37',
            '-auto-alt-ref', '0',
            '-preset', 'ultrafast',  # Faster encoding
            '-an',
            '-t', '00:00:10',
            output_path.name
        ], check=True, cwd=str(TEMP_DIR))
    except subprocess.CalledProcessError as e:
        raise Exception(f"Gagal memproses video: {str(e)}")

    # Read into BytesIO
    with open(output_path, 'rb') as f:
        bio = BytesIO(f.read())
    bio.name = "sticker.webm"
    bio.seek(0)
    
    # Cleanup
    for path in [file_list_path, output_path]:
        try:
            path.unlink()
        except:
            pass
    
    return bio

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def bratvid_handler(event):
        """Handle bratvid/bvideo commands"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        cmd = None
        if current_prefix:
            if msg.startswith(f"{current_prefix}bratvid"):
                cmd = "bratvid"
            elif msg.startswith(f"{current_prefix}bvideo"):
                cmd = "bvideo"
        else:
            if msg.lower().startswith("bratvid"):
                cmd = "bratvid"
            elif msg.lower().startswith("bvideo"):
                cmd = "bvideo"
                
        if not cmd:
            return

        # Extract text
        text = msg[len(cmd) + len(current_prefix or ''):].strip()
        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text
        
        if not text:
            status = await event.reply(f"Balas pesan atau ketik *{current_prefix or ''}{cmd}* teksnya")
            await asyncio.sleep(5)
            await status.delete()
            await event.delete()
            return

        processing_msg = await event.reply(f"<blockquote>⏳ Memproses video sticker...</blockquote>", parse_mode="html")
        frame_paths = []
        
        try:
            # Process text word by word
            words = text.split()
            
            # Fetch all videos concurrently
            tasks = []
            async with aiohttp.ClientSession() as session:
                for i in range(len(words)):
                    current_text = ' '.join(words[:i+1])
                    tasks.append(get_brat_video(current_text))
                
                videos = await asyncio.gather(*tasks)
                
                for i, video_data in enumerate(videos):
                    frame_path = TEMP_DIR / f'{event.sender_id}{i}.mp4'
                    with open(frame_path, 'wb') as f:
                        f.write(video_data)
                    frame_paths.append(str(frame_path))
            
            # Create video sticker
            sticker = await create_video_sticker(frame_paths, str(event.sender_id))
            
            # Send as proper video sticker
            await user.send_file(
                event.chat_id,
                sticker,
                reply_to=event.reply_to_msg_id,
                attributes=[
                    DocumentAttributeVideo(
                        duration=3,
                        w=512,
                        h=512,
                        round_message=True,
                        supports_streaming=True
                    ),
                    DocumentAttributeSticker(
                        alt="",
                        stickerset=InputStickerSetShortName('default')
                    )
                ],
                force_document=False
            )
            
        except Exception as e:
            await processing_msg.edit(f"❌ Gagal: {str(e)}")
            await asyncio.sleep(5)
        finally:
            # Cleanup frame files
            for path in frame_paths:
                try:
                    Path(path).unlink()
                except:
                    pass
            
            try:
                await processing_msg.delete()
                await event.delete()
            except:
                pass