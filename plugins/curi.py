import os
import json
import asyncio
from datetime import datetime
from telethon import events, types
from config import OWNER_ID
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeVideo,
    DocumentAttributeAudio
)

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
MEDIA_TEMP_DIR = {
    'photo': os.path.join(CONFIG_DIR, 'temp_media'),
    'video': os.path.join(CONFIG_DIR, 'temp_video'),
    'audio': os.path.join(CONFIG_DIR, 'temp_audio')
}

# Create directories if they don't exist
os.makedirs(MEDIA_TEMP_DIR['photo'], exist_ok=True)
os.makedirs(MEDIA_TEMP_DIR['video'], exist_ok=True)
os.makedirs(MEDIA_TEMP_DIR['audio'], exist_ok=True)

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

class MediaBuffer:
    def __init__(self):
        self.buffered_media = None
        self.media_type = None
        self.file_path = None
        self.caption = None

media_buffer = MediaBuffer()

async def download_media(message, media_type):
    """Download media and save to appropriate directory"""
    try:
        timestamp = int(datetime.now().timestamp())
        
        if media_type == 'photo':
            ext = '.jpg'
            file_path = os.path.join(MEDIA_TEMP_DIR['photo'], f'photo_{timestamp}{ext}')
            await message.download_media(file=file_path)
        else:
            if media_type == 'video':
                dir_path = MEDIA_TEMP_DIR['video']
                ext = '.mp4'
            else:  # audio/voice
                dir_path = MEDIA_TEMP_DIR['audio']
                ext = '.ogg'
            
            file_path = os.path.join(dir_path, f'{media_type}_{timestamp}{ext}')
            await message.download_media(file=file_path)
        
        return file_path
    except Exception as e:
        raise Exception(f"Failed to download media: {str(e)}")

def determine_media_type(message):
    """Determine the type of media in the message"""
    if message.photo:
        return 'photo'
    elif message.media and isinstance(message.media, MessageMediaDocument):
        attributes = message.media.document.attributes
        for attr in attributes:
            if isinstance(attr, DocumentAttributeVideo):
                return 'video'
            elif isinstance(attr, DocumentAttributeAudio):
                if attr.voice:
                    return 'voice'
                return 'audio'
    return None

async def setup(bot, user):
    current_prefix = get_live_prefix()
    
    # Copy media command (b)
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID, pattern=f'^{current_prefix}b$'))
    async def copy_media_handler(event):
        """Copy media to buffer"""
        reply = await event.get_reply_message()
        if not reply:
            status = await event.reply("<blockquote>🚫 <b>Balas ke media yang ingin disalin!</b></blockquote>", parse_mode="html")
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()
            return
        
        media_type = determine_media_type(reply)
        if not media_type:
            status = await event.reply("<blockquote>🚫 <b>Tidak ada media yang ditemukan!</b></blockquote>", parse_mode="html")
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()
            return
        
        try:
            # Download and save the media
            file_path = await download_media(reply, media_type)
            
            # Store in buffer
            media_buffer.buffered_media = file_path
            media_buffer.media_type = media_type
            media_buffer.caption = reply.text
            
            status = await event.reply("<blockquote>✅ <b>Media berhasil disimpan!</b></blockquote>", parse_mode="html")
            await asyncio.sleep(1)
            await status.delete()
            await event.delete()
            
        except Exception as e:
            status = await event.reply(f"<blockquote>❌ <b>Gagal menyimpan media:</b> <code>{str(e)[:200]}</code></blockquote>", parse_mode="html")
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()

    # Paste media command (t)
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID, pattern=f'^{current_prefix}t(?: |$)(.*)'))
    async def paste_media_handler(event):
        """Paste media from buffer"""
        if not media_buffer.buffered_media or not os.path.exists(media_buffer.buffered_media):
            status = await event.reply("<blockquote>🚫 <b>Tidak ada media yang tersedia di buffer!</b></blockquote>", parse_mode="html")
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()
            return
        
        try:
            caption = event.pattern_match.group(1).strip() or media_buffer.caption
            file_path = media_buffer.buffered_media
            
            # Determine upload parameters based on media type
            if media_buffer.media_type == 'photo':
                await user.send_file(
                    event.chat_id,
                    file_path,
                    caption=caption,
                    force_document=False,
                    parse_mode="html"
                )
            elif media_buffer.media_type in ['video', 'audio', 'voice']:
                attributes = []
                if media_buffer.media_type == 'video':
                    attributes.append(types.DocumentAttributeVideo(
                        duration=0,
                        w=0,
                        h=0,
                        supports_streaming=True
                    ))
                elif media_buffer.media_type == 'voice':
                    attributes.append(types.DocumentAttributeAudio(
                        voice=True,
                        duration=0
                    ))
                
                await user.send_file(
                    event.chat_id,
                    file_path,
                    caption=caption,
                    attributes=attributes,
                    force_document=False,
                    voice_note=(media_buffer.media_type == 'voice'),
                    parse_mode="html"
                )
            
            await event.delete()
            
        except Exception as e:
            status = await event.reply(f"<blockquote>❌ <b>Gagal mengirim media:</b> <code>{str(e)[:200]}</code></blockquote>", parse_mode="html")
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()