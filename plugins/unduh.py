# plugins/unduh.py
import os
import re
import json
from telethon import events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.tl.functions.channels import GetFullChannelRequest
from config import OWNER_ID

def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("data/temp_video"):
        os.makedirs("data/temp_video")

def get_prefix():
    """Get current prefix from config (supports 'no' prefix mode)"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_data_dir()
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def get_channel_info(user, channel_identifier):
    """Get channel name and ID from username or channel ID"""
    try:
        # Coba dapatkan entity baik dengan username maupun ID
        channel = await user.get_entity(channel_identifier)
        
        if hasattr(channel, 'title'):
            # Clean channel name for filename
            clean_name = re.sub(r'[\\/*?:"<>|]', '', channel.title).strip()
            return clean_name or f"channel_{channel.id}", channel.id
        return f"channel_{channel.id}", channel.id
    except ValueError:
        # Jika ValueError, mungkin ID channel numerik
        try:
            # Coba akses sebagai channel ID
            channel_id = int(channel_identifier)
            channel = await user.get_entity(channel_id)
            if hasattr(channel, 'title'):
                clean_name = re.sub(r'[\\/*?:"<>|]', '', channel.title).strip()
                return clean_name or f"channel_{channel_id}", channel_id
            return f"channel_{channel_id}", channel_id
        except Exception:
            return f"channel_{channel_identifier}", channel_identifier
    except Exception:
        return f"channel_{channel_identifier}", channel_identifier

def cleanup_file(file_path):
    """Clean up downloaded file after sending"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {str(e)}")

def setup(bot, user):
    ensure_data_dir()

    @user.on(events.NewMessage())
    async def download_handler(event):
        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check if message is a download command
        pattern = (
            r'^unduh\s+(https://t\.me/(?:c/\d+|[\w_]+)/\d+)$' if current_prefix == "no" else
            r'^{}unduh\s+(https://t\.me/(?:c/\d+|[\w_]+)/\d+)$'.format(re.escape(current_prefix))
        )
        
        match = re.match(pattern, message, re.IGNORECASE)
        if not match or event.sender_id != OWNER_ID:
            return

        url = match.group(1)
        
        # Extract channel identifier and message ID from URL
        url_match = re.match(r'https://t\.me/(?:c/(\d+)|([\w_]+))/(\d+)', url)
        if not url_match:
            await event.reply("❌ Format URL tidak valid. Gunakan format:\n"
                            "https://t.me/c/channel_id/message_id\n"
                            "atau\n"
                            "https://t.me/channel_username/message_id")
            return

        channel_identifier = url_match.group(1) or url_match.group(2)
        message_id = int(url_match.group(3))

        try:
            # Get channel info (name and ID)
            channel_name, channel_id = await get_channel_info(user, channel_identifier)
            
            # Get the message - try both by ID and by peer
            try:
                msg = await user.get_messages(entity=channel_id, ids=message_id)
            except Exception:
                # Fallback untuk channel ID numerik
                try:
                    msg = await user.get_messages(entity=int(channel_id), ids=message_id)
                except Exception as e:
                    await event.reply(f"❌ Gagal mengakses channel: {str(e)}")
                    return

            if not msg or not msg.media:
                await event.reply("❌ Pesan tidak ditemukan atau tidak mengandung media")
                return

            # Send processing message
            processing_msg = await event.reply("⏳ Mengunduh media...")

            # Prepare filename
            base_filename = f"data/temp_video/{channel_name}"

            # Download media
            if isinstance(msg.media, MessageMediaPhoto):
                file_path = await user.download_media(msg, file=f"{base_filename}.jpg")
                file_type = "gambar"
            elif isinstance(msg.media, MessageMediaDocument):
                # Get original file extension if available
                ext = '.mp4'
                if hasattr(msg.media.document, 'attributes'):
                    for attr in msg.media.document.attributes:
                        if hasattr(attr, 'file_name'):
                            original_name = attr.file_name
                            ext = os.path.splitext(original_name)[1] or '.mp4'
                            break
                file_path = await user.download_media(msg, file=f"{base_filename}{ext}")
                file_type = "video"
            else:
                await processing_msg.edit("❌ Jenis media tidak didukung")
                return

            # Send result
            await processing_msg.edit(f"✅ **{file_type.capitalize()} berhasil diunduh!**\n📁 Mengirim...")
            
            # Send the downloaded file
            try:
                await event.reply(file=file_path)
                await processing_msg.delete()
            except Exception as send_error:
                await processing_msg.edit(f"❌ Gagal mengirim file: {str(send_error)}")
            
            # Clean up file after sending
            cleanup_file(file_path)
            
        except Exception as e:
            await event.reply(f"❌ Gagal mengunduh: {str(e)}")
            # Clean up file if exists
            if 'file_path' in locals() and os.path.exists(file_path):
                cleanup_file(file_path)