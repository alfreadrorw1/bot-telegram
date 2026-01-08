import os
import json
import asyncio
from io import BytesIO
from telethon import events
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    DocumentAttributeSticker,
    InputStickerSetShortName,
    InputDocument
)
from config import OWNER_ID
from PIL import Image, ImageOps, UnidentifiedImageError

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

async def convert_to_sticker(media_data: bytes, is_video: bool = False) -> BytesIO:
    """
    Convert media to sticker format with proper handling for both images and videos
    """
    bio = BytesIO()
    
    try:
        if is_video:
            # Handle video stickers
            bio.write(media_data)
            bio.name = "sticker.webm"  # Telegram prefers webm for video stickers
            bio.seek(0)
            return bio
        
        # Handle image stickers
        try:
            img = Image.open(BytesIO(media_data)).convert("RGBA")
        except UnidentifiedImageError:
            raise Exception("File bukan gambar yang valid atau format tidak didukung")
            
        # Remove exif orientation
        img = ImageOps.exif_transpose(img)
        
        # Resize while maintaining aspect ratio
        max_size = 512
        width, height = img.size
        if width > max_size or height > max_size:
            ratio = min(max_size/width, max_size/height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create transparent canvas
        canvas = Image.new("RGBA", (max_size, max_size), (0, 0, 0, 0))
        x = (max_size - img.width) // 2
        y = (max_size - img.height) // 2
        canvas.paste(img, (x, y), img)
        
        # Save as webp
        bio.name = "sticker.webp"
        canvas.save(bio, format="WEBP", quality=95, method=6)
        bio.seek(0)
        return bio
        
    except Exception as e:
        raise Exception(f"Gagal mengkonversi media: {str(e)}")

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def sticker_handler(event):
        """Convert replied media to proper sticker (including video stickers)"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format more strictly
        is_sticker_cmd = False
        
        if current_prefix:
            # Only trigger if message is exactly the prefix + 's' 
            # or prefix + 's' followed by space/end
            if msg == f"{current_prefix}s" or msg.startswith(f"{current_prefix}s "):
                is_sticker_cmd = True
        else:
            # For no prefix, only trigger for single 's' command
            if msg.lower() == "s":
                is_sticker_cmd = True
                
        if not is_sticker_cmd:
            return

        # Check if replying to media
        if not event.is_reply:
            status = await event.reply("🚫 **Reply ke gambar/video untuk dijadikan sticker!**")
            await asyncio.sleep(5)
            await status.delete()
            await event.delete()
            return

        reply = await event.get_reply_message()
        
        # Check if replied message has media
        if not reply.media:
            status = await event.reply("🚫 **Pesan yang di-reply tidak mengandung media!**")
            await asyncio.sleep(5)
            await status.delete()
            await event.delete()
            return

        status = await event.reply("```🔄 Sedang mengubah menjadi sticker...```")
        
        try:
            # Download media
            media_data = await user.download_media(reply.media, bytes)
            if not media_data:
                raise Exception("Gagal mengunduh media")
            
            # Check media type and get attributes
            is_video = False
            duration = 3  # Default duration for video stickers
            width = 512
            height = 512
            
            if hasattr(reply.media, 'document'):
                for attr in reply.media.document.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        is_video = True
                        duration = min(attr.duration, 3)  # Max 3 seconds for stickers
                        width = attr.w
                        height = attr.h
                    elif isinstance(attr, DocumentAttributeFilename):
                        ext = attr.file_name.split('.')[-1].lower()
                        if ext in ['mp4', 'webm', 'gif']:
                            is_video = True
            
            # Convert to sticker
            sticker = await convert_to_sticker(media_data, is_video)
            
            # Prepare attributes for sticker
            if is_video:
                attributes = [
                    DocumentAttributeVideo(
                        duration=duration,
                        w=width,
                        h=height,
                        round_message=True,  # This makes it a video sticker
                        supports_streaming=True
                    ),
                    DocumentAttributeSticker(alt="", stickerset=InputStickerSetShortName('default'))
                ]
            else:
                attributes = [
                    DocumentAttributeSticker(alt="", stickerset=InputStickerSetShortName('default'))
                ]
            
            # Send as sticker
            await user.send_file(
                event.chat_id,
                sticker,
                reply_to=reply.id,
                force_document=False,
                attributes=attributes,
                allow_cache=False
            )
            await status.delete()
            
        except Exception as e:
            await status.edit(f"```❌ Gagal membuat sticker: {str(e)}```")
            await asyncio.sleep(5)
            await status.delete()
        finally:
            await event.delete()