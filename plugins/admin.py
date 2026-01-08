import os
import json
import asyncio
import logging
import random
from datetime import datetime
from telethon import events, types
from telethon.errors import ChatAdminRequiredError, YouBlockedUserError
from telethon.tl.functions.channels import (
    EditBannedRequest,
    EditAdminRequest,
    GetParticipantsRequest,
    DeleteChannelRequest
)
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChannelParticipantsSearch,
    ChatBannedRights,
    ChatAdminRights,
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeVideo,
    DocumentAttributeAudio
)
from config import OWNER_ID

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

# Default admin rights for title changes
ADMIN_RIGHTS = ChatAdminRights(
    change_info=False,
    post_messages=False,
    edit_messages=False,
    delete_messages=False,
    ban_users=False,
    invite_users=False,
    pin_messages=False,
    add_admins=False,
    manage_call=False,
    other=True,
    anonymous=False,
)

# Ban rights (kick = ban + unban)
BAN_RIGHTS = ChatBannedRights(until_date=None, view_messages=True)
UNBAN_RIGHTS = ChatBannedRights(until_date=None, view_messages=False)

# Store active tagging sessions
active_tag_sessions = set()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaBuffer:
    def __init__(self):
        self.buffered_media = None
        self.media_type = None
        self.file_path = None
        self.caption = None

media_buffer = MediaBuffer()

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

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
    # ===== PIN/UNPIN =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def pin_handler(event):
        """Handle pin command"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_pin_cmd = False
        is_unpin_cmd = False
        
        if current_prefix:
            if msg == f"{current_prefix}pin":
                is_pin_cmd = True
            elif msg == f"{current_prefix}unpin":
                is_unpin_cmd = True
        else:
            if msg.lower() == "pin":
                is_pin_cmd = True
            elif msg.lower() == "unpin":
                is_unpin_cmd = True
                
        if not (is_pin_cmd or is_unpin_cmd):
            return

        # Common checks for both commands
        if not (event.is_group or event.is_channel):
            await event.reply("<blockquote>❌ <b>Perintah ini hanya bekerja di grup/channel</b></blockquote>", parse_mode="html")
            return

        reply = await event.get_reply_message()
        if not reply:
            await event.reply("<blockquote>❌ <b>Balas pesan yang ingin dipin/unpin</b></blockquote>", parse_mode="html")
            return

        try:
            if is_pin_cmd:
                await user.pin_message(event.chat_id, reply.id, notify=False)
                await event.reply("<blockquote>📌 <b>Pesan berhasil dipin</b></blockquote>", parse_mode="html")
            else:  # unpin
                await user.unpin_message(event.chat_id, reply.id)
                await event.reply("<blockquote>🔓 <b>Pesan berhasil diunpin</b></blockquote>", parse_mode="html")
                
        except ChatAdminRequiredError:
            await event.reply("<blockquote>❌ <b>Bot membutuhkan hak admin untuk melakukan ini</b></blockquote>", parse_mode="html")
        except Exception as e:
            error_msg = str(e)[:200]
            action = "mem-pin" if is_pin_cmd else "melepas pin"
            await event.reply(f"<blockquote>❌ <b>Gagal {action} pesan:</b> <code>{error_msg}</code></blockquote>", parse_mode="html")
        finally:
            await event.delete()

    # ===== TITLE =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def title_handler(event):
        """Handle title command"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_title_cmd = False
        title = ""
        
        if current_prefix:
            if msg.startswith(f"{current_prefix}title "):
                is_title_cmd = True
                title = msg[len(current_prefix)+6:].strip()
        else:
            if msg.lower().startswith("title "):
                is_title_cmd = True
                title = msg[6:].strip()
                
        if not is_title_cmd or not title:
            return

        # Validate chat type and permissions
        if not (event.is_group or event.is_channel):
            await event.reply("<blockquote>❌ <b>Perintah ini hanya bekerja di grup/channel</b></blockquote>", parse_mode="html")
            return

        reply = await event.get_reply_message()
        if not reply:
            await event.reply("<blockquote>❌ <b>Balas pesan dari user yang ingin diberi title</b></blockquote>", parse_mode="html")
            return

        try:
            # Set custom title
            await user(EditAdminRequest(
                channel=event.chat_id,
                user_id=reply.sender_id,
                admin_rights=ADMIN_RIGHTS,
                rank=title[:16]  # Limit title length to 16 characters
            ))
            
            await event.reply(f"<blockquote>✅ <b>Title berhasil diubah menjadi</b> <code>\"{title}\"</code></blockquote>", parse_mode="html")
            
        except Exception as e:
            error_msg = str(e)[:200]
            await event.reply(f"<blockquote>❌ <b>Gagal mengubah title:</b> <code>{error_msg}</code></blockquote>", parse_mode="html")
        finally:
            await event.delete()

    # ===== DELETE =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def del_handler(event):
        """Handle message deletion commands"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        if current_prefix:
            if not (msg == f"{current_prefix}del" and event.is_reply):
                return
        else:
            if not (msg.lower() == "del" and event.is_reply):
                return

        reply = await event.get_reply_message()
        if not reply:
            notif = await event.reply("<blockquote>❌ <b>Balas pesan yang ingin dihapus</b></blockquote>", parse_mode="html")
            await asyncio.sleep(2)
            await notif.delete()
            await event.delete()
            return

        try:
            # Delete both the command and replied message
            await user.delete_messages(
                entity=event.chat_id,
                message_ids=[reply.id, event.id]
            )
            
        except Exception as e:
            # Try deleting just the command if we can't delete the replied message
            try:
                await event.delete()
            except:
                pass
            
            error_msg = await event.reply(f"<blockquote>❌ <b>Gagal menghapus pesan:</b> <code>{str(e)[:200]}</code></blockquote>", parse_mode="html")
            await asyncio.sleep(3)
            await error_msg.delete()

    # ===== STAFF LIST =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def staff_handler(event):
        """Handle staff list command"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_staff_cmd = False
        
        if current_prefix:
            if msg == f"{current_prefix}staff":
                is_staff_cmd = True
        else:
            if msg.lower() == "staff":
                is_staff_cmd = True
                
        if not is_staff_cmd:
            return

        # Validate chat type
        if not (event.is_group or event.is_channel):
            await event.reply("<blockquote>❌ <b>Perintah ini hanya bekerja di grup/channel</b></blockquote>", parse_mode="html")
            return

        processing_msg = await event.reply("<blockquote>🔄 <b>Mengumpulkan daftar staff...</b></blockquote>", parse_mode="html")
        
        try:
            staff_list = []
            async for admin in user.iter_participants(
                event.chat_id,
                filter=ChannelParticipantsAdmins
            ):
                # Skip bots
                if getattr(admin, 'bot', False):
                    continue

                # Determine role
                if getattr(admin, 'is_creator', False):
                    role = "👑 Owner"
                elif getattr(admin, 'admin_rights', None):
                    role = "🛡️ Admin"
                else:
                    role = "👤 Staff"

                # Add custom title if available
                title = getattr(admin, 'rank', None)
                if title:
                    role += f" ({title})"

                mention = f"<a href='tg://user?id={admin.id}'>{admin.first_name or 'No Name'}</a>"
                username = f"@{admin.username}" if admin.username else "—"

                staff_list.append(
                    f"{role}\n"
                    f" ├ <b>Nama:</b> {mention}\n"
                    f" ├ <b>Username:</b> {username}\n"
                    f" └ <b>ID:</b> <code>{admin.id}</code>"
                )

            if not staff_list:
                await processing_msg.edit("<blockquote>❌ <b>Tidak ada staff/admin ditemukan</b></blockquote>", parse_mode="html")
                return

            # Split into chunks if too long
            header = "<b>✨ DAFTAR STAFF GRUP ✨</b>\n\n"
            full_text = "\n\n".join(staff_list)
            max_length = 4000 - len(header)
            
            if len(full_text) <= max_length:
                await processing_msg.edit(f"<blockquote>{header}{full_text}</blockquote>", parse_mode="html", link_preview=False)
            else:
                await processing_msg.delete()
                chunks = [full_text[i:i+max_length] for i in range(0, len(full_text), max_length)]
                await event.reply(f"<blockquote>{header}{chunks[0]}</blockquote>", parse_mode="html", link_preview=False)
                for chunk in chunks[1:]:
                    await event.reply(f"<blockquote>{chunk}</blockquote>", parse_mode="html", link_preview=False)
                    
        except Exception as e:
            error_msg = str(e)[:200]
            await processing_msg.edit(f"<blockquote>❌ <b>Gagal mengambil daftar staff</b>\n<b>Error:</b> <code>{error_msg}</code></blockquote>", parse_mode="html")
        finally:
            await event.delete()

    # ===== KICK =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def kick_handler(event):
        """Handle kick command"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        if current_prefix:
            if not msg.startswith(f"{current_prefix}kick"):
                return
            target = msg[len(current_prefix)+4:].strip()
        else:
            if not msg.lower().startswith("kick"):
                return
            target = msg[4:].strip()

        # Check if in group/channel
        if not event.is_group and not event.is_channel:
            await event.reply("<blockquote>⚠️ <b>Command ini hanya bekerja di grup/channel</b></blockquote>", parse_mode="html")
            return

        # Get target user
        try:
            if event.is_reply:
                reply = await event.get_reply_message()
                target_entity = await user.get_entity(reply.sender_id)
            elif target:
                target_entity = await user.get_entity(target)
            else:
                await event.reply("<blockquote>⚠️ <b>Reply pesan atau berikan username/ID</b></blockquote>", parse_mode="html")
                return
        except Exception as e:
            await event.reply(f"<blockquote>❌ <b>Tidak dapat menemukan user:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
            return

        # Check if we have admin rights
        try:
            # Perform kick (ban + unban)
            await user(EditBannedRequest(event.chat_id, target_entity, BAN_RIGHTS))
            await user(EditBannedRequest(event.chat_id, target_entity, UNBAN_RIGHTS))
            
            # Get user name for response
            user_name = getattr(target_entity, 'first_name', f"ID {target_entity.id}")
            await event.reply(f"<blockquote>✅ <b>Berhasil mengkick {user_name}</b></blockquote>", parse_mode="html")
        except Exception as e:
            error_msg = str(e).lower()
            if "admin" in error_msg:
                await event.reply("<blockquote>❌ <b>Bot perlu jadi admin dengan ban permission</b></blockquote>", parse_mode="html")
            else:
                await event.reply(f"<blockquote>❌ <b>Gagal mengkick:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

    # ===== HISTORY =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def sangmata_handler(event):
        """Handle sg command to fetch user history from SangMata bot"""
        delete_after = False
        processing_msg = None
        
        try:
            msg = (event.text or '').strip()
            current_prefix = get_live_prefix()
            
            # Check command format
            is_sg_cmd = False
            args = ""
            
            if current_prefix:
                if msg.startswith(f"{current_prefix}sg"):
                    is_sg_cmd = True
                    args = msg[len(current_prefix)+3:].strip()
            else:
                if msg.lower().startswith("sg"):
                    is_sg_cmd = True
                    args = msg[2:].strip()
            
            if not is_sg_cmd:
                return

            logger.info(f"Processing sg command with args: '{args}'")
            
            # Get target user
            reply = await event.get_reply_message()
            chat = "SangMata_beta_bot"
            
            processing_msg = await event.reply("<blockquote>🔄 <b>Proses...</b></blockquote>", parse_mode="html")

            # Identify target user
            if args:
                try:
                    entity = await user.get_entity(args)
                    user_id = entity.id
                    logger.info(f"Resolved user ID: {user_id}")
                except Exception as e:
                    logger.error(f"Entity resolution error: {e}")
                    await processing_msg.edit("<blockquote>⚠️ <b>Tidak dapat menemukan pengguna:</b> <code>{args}</code></blockquote>", parse_mode="html")
                    delete_after = True
                    return
            elif reply:
                user_id = reply.sender_id
                logger.info(f"Using replied user ID: {user_id}")
            else:
                await processing_msg.edit("<blockquote>🚫 <b>Gunakan perintah dengan:</b> <code>sg reply pesan/username.</code></blockquote>", parse_mode="html")
                delete_after = True
                return

            # Process request to SangMata bot
            try:
                async with user.conversation(chat, timeout=20) as conv:
                    try:
                        await conv.send_message(f"/allhistory {user_id}")
                        response = await conv.get_response()
                        logger.info("Received response from SangMata")

                        if "No data available" in response.text:
                            await processing_msg.edit("<blockquote>📭 <b>Tidak ada data history yang tersedia</b></blockquote>", parse_mode="html")
                            delete_after = True
                        elif "Daily limit" in response.text:
                            await processing_msg.edit("<blockquote>⚠️ <b>Kuota harian telah habis, coba lagi besok</b></blockquote>", parse_mode="html")
                            delete_after = True
                        elif "User ID" in response.text or "Username" in response.text:
                            formatted_text = response.text.replace("--", "—").replace("  ", " ")
                            await event.reply(f"<blockquote>🔍 <b>Hasil pencarian:</b>\n\n{formatted_text}</blockquote>", parse_mode="html")
                            await processing_msg.delete()
                        else:
                            await event.reply(f"<blockquote>🔍 <b>Data ditemukan:</b>\n\n{response.text}</blockquote>", parse_mode="html")
                            await processing_msg.delete()

                    except TimeoutError:
                        logger.error("Timeout with SangMata bot")
                        await processing_msg.edit("<blockquote>⏱️ <b>Waktu tunggu habis, coba lagi nanti</b></blockquote>", parse_mode="html")
                        delete_after = True
                    except Exception as e:
                        logger.error(f"Conversation error: {e}")
                        await processing_msg.edit(f"<blockquote>🚫 <b>Error saat memproses:</b> <code>{str(e)[:200]}</code></blockquote>", parse_mode="html")
                        delete_after = True

            except YouBlockedUserError:
                logger.error("User blocked SangMata bot")
                await processing_msg.edit("<blockquote>🔓 <b>Silakan unblock @SangMata_beta_bot terlebih dahulu</b></blockquote>", parse_mode="html")
                delete_after = True
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await processing_msg.edit("<blockquote>🚫 <b>Gagal memulai percakapan dengan SangMata bot</b></blockquote>", parse_mode="html")
                delete_after = True

        except Exception as ex:
            logger.error(f"Unexpected error in handler: {ex}")
            await event.reply("<blockquote>🚫 <b>Terjadi kesalahan internal</b></blockquote>", parse_mode="html")

        finally:
            if delete_after and processing_msg:
                await asyncio.sleep(5)
                try:
                    await processing_msg.delete()
                except:
                    pass

    # ===== TAG =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def tag_handler(event):
        """Handle tag command"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_tag_cmd = False
        is_stop_cmd = False
        message = "Halo semuanya!"
        
        if current_prefix:
            if msg.startswith(f"{current_prefix}tag"):
                is_tag_cmd = True
                message = msg[len(current_prefix)+4:].strip() or message
            elif msg == f"{current_prefix}stag":
                is_stop_cmd = True
        else:
            if msg.lower().startswith("tag"):
                is_tag_cmd = True
                message = msg[3:].strip() or message
            elif msg.lower() == "stag":
                is_stop_cmd = True
                
        if not (is_tag_cmd or is_stop_cmd):
            return

        # Handle stop tag command
        if is_stop_cmd:
            await stop_tag(event)
            return

        # Validate chat type
        if not (event.is_group or event.is_channel):
            await event.reply("<blockquote>❌ <b>Perintah ini hanya bekerja di grup/channel</b></blockquote>", parse_mode="html")
            return

        chat_id = event.chat_id
        
        # Check if already tagging in this chat
        if chat_id in active_tag_sessions:
            await event.reply("<blockquote>⚠️ <b>Sudah ada proses tag yang berjalan di chat ini</b></blockquote>", parse_mode="html")
            return

        emoji_list = ["🔥", "⚡", "✨", "💥", "🚀", "🎯", "⚔️", "🌟", "🎉", "🛡️"]
        mentions = []

        try:
            # Mark this chat as active
            active_tag_sessions.add(chat_id)
            await event.reply("<blockquote>🔄 <b>Memulai proses tag...</b></blockquote>", parse_mode="html")

            # Collect participants
            async for member in user.iter_participants(
                chat_id, 
                filter=ChannelParticipantsSearch("")
            ):
                # Skip bots and self
                if getattr(member, 'bot', False) or getattr(member, 'is_self', False):
                    continue

                mention = f"<a href='tg://user?id={member.id}'>{member.first_name or 'User'}</a>"
                emoji = random.choice(emoji_list)
                mentions.append(f"{emoji} {mention}")

            if not mentions:
                await event.reply("<blockquote>❌ <b>Tidak ada member yang bisa di-tag</b></blockquote>", parse_mode="html")
                return

            # Send initial message
            total_members = len(mentions)
            await event.reply(f"<blockquote>✅ <b>Akan men-tag {total_members} anggota. Ketik .stag untuk membatalkan.</b></blockquote>", parse_mode="html")

            # Send mentions in chunks of 5
            chunk_size = 5
            for i in range(0, len(mentions), chunk_size):
                if chat_id not in active_tag_sessions:
                    await event.reply("<blockquote>🛑 <b>Proses tag dihentikan</b></blockquote>", parse_mode="html")
                    break

                chunk = mentions[i:i + chunk_size]
                text = f"<b>{message}</b>\n\n" + "\n".join(chunk)
                await user.send_message(chat_id, text, parse_mode="html", link_preview=False)
                await asyncio.sleep(1.5)  # Rate limiting

            await event.reply(f"<blockquote>✅ <b>Selesai men-tag {total_members} anggota</b></blockquote>", parse_mode="html")

        except Exception as e:
            await event.reply(f"<blockquote>❌ <b>Gagal melakukan tag:</b> <code>{str(e)[:200]}</code></blockquote>", parse_mode="html")
        finally:
            active_tag_sessions.discard(chat_id)
            await event.delete()

    async def stop_tag(event):
        """Handle stop tag command"""
        chat_id = event.chat_id
        if chat_id in active_tag_sessions:
            active_tag_sessions.discard(chat_id)
            await event.reply("<blockquote>🛑 <b>Proses tag dihentikan</b></blockquote>", parse_mode="html")
        else:
            await event.reply("<blockquote>ℹ️ <b>Tidak ada proses tag yang berjalan</b></blockquote>", parse_mode="html")
        await event.delete()

    # ===== MEDIA BUFFER =====
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID, pattern=f'^{get_live_prefix()}b$'))
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

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID, pattern=f'^{get_live_prefix()}t(?: |$)(.*)'))
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

    logger.info("Admin plugin loaded successfully")