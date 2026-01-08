# plugins/premium/sticker.py
import os
import json
import asyncio
from io import BytesIO
from telethon import events
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    DocumentAttributeSticker,
    InputStickerSetShortName
)
from config import OWNER_ID
from PIL import Image, ImageOps, UnidentifiedImageError

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

async def convert_to_sticker(media_data: bytes, is_video: bool = False) -> BytesIO:
    """
    Convert media to sticker format with proper handling for both images and videos
    Returns BytesIO object containing the sticker
    """
    bio = BytesIO()
    
    try:
        if is_video:
            # Handle video stickers
            bio.write(media_data)
            bio.name = "sticker.webm"
            bio.seek(0)
            return bio
        
        # Handle image stickers
        with Image.open(BytesIO(media_data)) as img:
            img = img.convert("RGBA")
            img = ImageOps.exif_transpose(img)  # Fix orientation
            
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
            
    except UnidentifiedImageError:
        raise Exception("File bukan gambar yang valid atau format tidak didukung")
    except Exception as e:
        raise Exception(f"Gagal mengkonversi media: {str(e)}")

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except Exception:
        pass

async def setup(bot, client, user_id):
    """Setup sticker converter for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def sticker_handler(event):
        """Convert replied media to proper sticker"""
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
        is_sticker_cmd = False
        
        if current_prefix == "no":
            if msg.lower() == "s":
                is_sticker_cmd = True
        else:
            if msg.lower() == f"{current_prefix}s" or msg.lower().startswith(f"{current_prefix}s "):
                is_sticker_cmd = True
                
        if not is_sticker_cmd:
            return

        # Check reply
        if not event.is_reply:
            status = await event.reply("🚫 **Reply ke gambar/video untuk dijadikan sticker!**")
            await asyncio.sleep(5)
            await safe_delete(status)
            await safe_delete(event)
            return

        reply = await event.get_reply_message()
        
        if not reply.media:
            status = await event.reply("🚫 **Pesan yang di-reply tidak mengandung media!**")
            await asyncio.sleep(5)
            await safe_delete(status)
            await safe_delete(event)
            return

        status = await event.reply("```🔄 Sedang mengubah menjadi sticker...```")
        
        try:
            # Download media
            media_data = await client.download_media(reply.media, bytes)
            if not media_data:
                raise Exception("Gagal mengunduh media")
            
            # Check media type
            is_video = False
            duration = 3  # Default duration for video stickers
            width = height = 512
            
            if hasattr(reply.media, 'document'):
                for attr in reply.media.document.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        is_video = True
                        duration = min(attr.duration, 3)
                        width = attr.w
                        height = attr.h
                    elif isinstance(attr, DocumentAttributeFilename):
                        if attr.file_name.split('.')[-1].lower() in ['mp4', 'webm', 'gif']:
                            is_video = True
            
            # Convert to sticker
            sticker = await convert_to_sticker(media_data, is_video)
            
            # Prepare attributes
            if is_video:
                attributes = [
                    DocumentAttributeVideo(
                        duration=duration,
                        w=width,
                        h=height,
                        round_message=True,
                        supports_streaming=True
                    ),
                    DocumentAttributeSticker(alt="", stickerset=InputStickerSetShortName('default'))
                ]
            else:
                attributes = [DocumentAttributeSticker(alt="", stickerset=InputStickerSetShortName('default'))]
            
            # Send sticker
            await client.send_file(
                event.chat_id,
                sticker,
                reply_to=reply.id,
                force_document=False,
                attributes=attributes,
                allow_cache=False
            )
            
        except Exception as e:
            await status.edit(f"```❌ Gagal membuat sticker: {str(e)}```")
            await asyncio.sleep(5)
        finally:
            await safe_delete(status)
            await safe_delete(event)

    