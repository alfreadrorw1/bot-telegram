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

# Create temp directory if not exists
TEMP_DIR = Path('database/sampah')
TEMP_DIR.mkdir(parents=True, exist_ok=True)

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
            '-loglevel', 'error',
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path.name,
            '-vf', 'fps=30,scale=512:512:force_original_aspect_ratio=decrease,format=yuv420p',
            '-c:v', 'libvpx-vp9',
            '-b:v', '500k',
            '-crf', '37',
            '-auto-alt-ref', '0',
            '-preset', 'ultrafast',
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

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except:
        pass

async def setup(bot, client, user_id):
    """Setup brat video sticker generator for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def bratvid_handler(event):
        """Handle bratvid/bvideo commands"""
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
            text = reply.text or reply.raw_text or ""
        
        if not text:
            status = await event.reply(
                f"<blockquote>🚫 Balas pesan atau ketik {current_prefix or ''}{cmd} teksnya</blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(5)
            await safe_delete(status)
            await safe_delete(event)
            return

        processing_msg = await event.reply(
            "<blockquote>⏳ Memproses video sticker...</blockquote>",
            parse_mode="html"
        )
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
            await client.send_file(
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
            await processing_msg.edit(
                f"<blockquote>❌ Gagal: {str(e)[:200]}</blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(5)
        finally:
            # Cleanup frame files
            for path in frame_paths:
                try:
                    Path(path).unlink()
                except:
                    pass
            
            try:
                await safe_delete(processing_msg)
                await safe_delete(event)
            except:
                pass