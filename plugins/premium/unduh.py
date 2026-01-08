# plugins/premium/unduh.py
import os
import re
import json
from telethon import events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.tl.types import InputPeerChannel, InputPeerChat, InputPeerUser
from telethon.errors import ChannelPrivateError
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

def ensure_data_dir(user_id=None):
    """Ensure data directory exists for specific user"""
    user_folder = get_user_folder(user_id)
    temp_video_dir = f'{user_folder}/temp_video'
    if not os.path.exists(temp_video_dir):
        os.makedirs(temp_video_dir)
    return temp_video_dir

async def get_channel_entity(user, channel_identifier, message_id):
    """Get channel entity from identifier with proper handling"""
    try:
        # Try to get entity directly
        if channel_identifier.isdigit():
            # Handle numeric channel IDs (private channels)
            channel_id = int(channel_identifier)
            access_hash = await get_access_hash(user, channel_id)
            if access_hash:
                return InputPeerChannel(channel_id, access_hash)
            else:
                # Try to resolve as regular entity
                return await user.get_entity(channel_id)
        else:
            # Handle username-based channels
            return await user.get_entity(channel_identifier)
            
    except ValueError:
        # If it's a numeric string but not a valid ID
        try:
            return await user.get_entity(int(channel_identifier))
        except:
            raise Exception("Channel tidak dapat diakses")
    except Exception as e:
        raise Exception(f"Gagal mengakses channel: {str(e)}")

async def get_access_hash(user, channel_id):
    """Try to get access hash for private channels"""
    try:
        # Check if we're already a member of this channel
        async for dialog in user.iter_dialogs():
            if dialog.id == channel_id:
                if hasattr(dialog.entity, 'access_hash'):
                    return dialog.entity.access_hash
        return None
    except:
        return None

def cleanup_file(file_path):
    """Clean up downloaded file after sending"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {str(e)}")

async def setup(bot, user, user_id):
    """Setup download handler for premium users"""
    current_user_id = user_id

    @user.on(events.NewMessage())
    async def download_handler(event):
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        # Get current prefix and message
        current_prefix = get_prefix(current_user_id)
        message = (event.raw_text or '').strip()
        
        # Check if message is a download command
        pattern = (
            r'^unduh\s+(https://t\.me/(?:c/)?(\d+)/(\d+))$' if current_prefix == "no" else
            r'^{}unduh\s+(https://t\.me/(?:c/)?(\d+)/(\d+))$'.format(re.escape(current_prefix))
        )
        
        match = re.match(pattern, message, re.IGNORECASE)
        if not match:
            # Also check for username format
            pattern2 = (
                r'^unduh\s+(https://t\.me/([\w_]+)/(\d+))$' if current_prefix == "no" else
                r'^{}unduh\s+(https://t\.me/([\w_]+)/(\d+))$'.format(re.escape(current_prefix))
            )
            match = re.match(pattern2, message, re.IGNORECASE)
            if not match:
                return

        url = match.group(1)
        channel_identifier = match.group(2)
        message_id = int(match.group(3))

        try:
            # Send processing message
            processing_msg = await event.reply("⏳ Mengunduh media...")

            # Get channel entity with proper handling
            try:
                entity = await get_channel_entity(user, channel_identifier, message_id)
            except Exception as e:
                await processing_msg.edit(f"❌ {str(e)}")
                return

            # Get the message
            try:
                msg = await user.get_messages(entity, ids=message_id)
            except ChannelPrivateError:
                await processing_msg.edit("❌ Channel bersifat privat dan bot tidak memiliki akses")
                return
            except Exception as e:
                await processing_msg.edit(f"❌ Gagal mengambil pesan: {str(e)}")
                return

            if not msg or not msg.media:
                await processing_msg.edit("❌ Pesan tidak ditemukan atau tidak mengandung media")
                return

            # Prepare filename with user-specific directory
            temp_dir = ensure_data_dir(current_user_id)
            channel_name = f"channel_{channel_identifier}"
            base_filename = f"{temp_dir}/{channel_name}_{message_id}"

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
                await event.reply(
                    f"📥 **Berhasil diunduh dari:** {url}\n"
                    f"📊 **Tipe:** {file_type.capitalize()}",
                    file=file_path
                )
                await processing_msg.delete()
            except Exception as send_error:
                await processing_msg.edit(f"❌ Gagal mengirim file: {str(send_error)}")
            
            # Clean up file after sending
            cleanup_file(file_path)
            
        except Exception as e:
            error_msg = await event.reply(f"❌ Gagal mengunduh: {str(e)}")
            await asyncio.sleep(5)
            await error_msg.delete()
            # Clean up file if exists
            if 'file_path' in locals() and file_path and os.path.exists(file_path):
                cleanup_file(file_path)