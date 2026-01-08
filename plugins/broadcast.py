import os
import json
import asyncio
from telethon import events, types
from telethon.tl.types import Channel, Chat, User
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
BLACKLIST_FILE = os.path.join(CONFIG_DIR, 'broadcast_blacklist.json')
DEFAULT_DELAY = 1

def ensure_data_dir():
    """Create data directory if not exists"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def get_live_prefix():
    """Get current prefix from config file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_data_dir()
        with open(PREFIX_FILE, 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def load_blacklist():
    """Load blacklist from JSON file"""
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def save_blacklist(data):
    """Save blacklist to JSON file"""
    ensure_data_dir()
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_owner(event):
    """Check if sender is owner"""
    return event.sender_id == OWNER_ID

async def setup(bot, user):
    ensure_data_dir()
    broadcast_delay = DEFAULT_DELAY
    blacklist = load_blacklist()

    # Helper function to send messages
    async def send_broadcast(event, content, reply, is_group=False):
        success = 0
        failed = 0
        target_type = "grup" if is_group else "chat pribadi"
        
        status_msg = await event.reply(
            f"<blockquote>🔄 Mengirim broadcast ke semua {target_type}...</blockquote>",
            parse_mode="html"
        )

        async for dialog in user.iter_dialogs():
            if dialog.id in blacklist:
                continue
                
            if is_group and not dialog.is_group:
                continue
            if not is_group and (not dialog.is_user or getattr(dialog.entity, 'bot', False) or dialog.id == OWNER_ID):
                continue

            try:
                if reply:
                    if reply.media:
                        if isinstance(reply.media, types.MessageMediaPhoto):
                            await user.send_file(dialog.id, reply.photo, caption=reply.text)
                        elif isinstance(reply.media, types.MessageMediaDocument):
                            if reply.document.mime_type == 'video/mp4':
                                await user.send_file(dialog.id, reply.video, caption=reply.text)
                            elif reply.document.mime_type == 'audio/ogg':  # Voice note
                                await user.send_file(dialog.id, reply.voice, voice_note=True)
                            elif reply.sticker:
                                await user.send_file(dialog.id, reply.sticker)
                            else:
                                await user.send_file(dialog.id, reply.document, caption=reply.text)
                        else:
                            await user.send_file(dialog.id, reply.media, caption=reply.text)
                    else:
                        await user.send_message(dialog.id, reply.text)
                else:
                    await user.send_message(dialog.id, content)
                
                success += 1
                await asyncio.sleep(broadcast_delay)
                
                # Update progress every 10 sends
                if success % 10 == 0:
                    await status_msg.edit(
                        f"<blockquote>🔄 Mengirim broadcast ke semua {target_type}...</blockquote>\n"
                        f"<blockquote>• Berhasil: {success}\n"
                        f"• Gagal: {failed}</blockquote>",
                        parse_mode="html"
                    )
            except Exception:
                failed += 1
                continue

        # Edit the original status message with final results
        await status_msg.edit(
            f"<blockquote><b>✅ Broadcast {target_type} selesai</b></blockquote>\n"
            f"<blockquote>• Berhasil: {success} {target_type}\n"
            f"• Gagal: {failed} {target_type}\n"
            f"• Delay: {broadcast_delay} detik</blockquote>",
            parse_mode="html"
        )
        return success, failed

    # GCAST Handler
    @user.on(events.NewMessage(outgoing=True))
    async def gcast_handler(event):
        """Handle gcast command"""
        if not is_owner(event):
            return
            
        current_prefix = get_live_prefix()
        msg = event.text.strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}gcast"):
                return
            content = msg[len(current_prefix)+5:].strip()
        else:
            if not msg.lower().startswith("gcast"):
                return
            content = msg[5:].strip()

        reply = await event.get_reply_message()
        if not content and not reply:
            await event.edit("<blockquote>❌ Balas pesan atau ketik pesan</blockquote>", parse_mode="html")
            return
        
        try:
            await event.delete()
            await send_broadcast(event, content, reply, is_group=True)
        except Exception as e:
            await event.reply(f"<blockquote>❌ Gagal broadcast: {str(e)}</blockquote>", parse_mode="html")

    # UCAST Handler
    @user.on(events.NewMessage(outgoing=True))
    async def ucast_handler(event):
        """Handle ucast command"""
        if not is_owner(event):
            return
            
        current_prefix = get_live_prefix()
        msg = event.text.strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}ucast"):
                return
            content = msg[len(current_prefix)+5:].strip()
        else:
            if not msg.lower().startswith("ucast"):
                return
            content = msg[5:].strip()

        reply = await event.get_reply_message()
        if not content and not reply:
            await event.edit("<blockquote>❌ Balas pesan atau ketik pesan</blockquote>", parse_mode="html")
            return
        
        try:
            await event.delete()
            await send_broadcast(event, content, reply, is_group=False)
        except Exception as e:
            await event.reply(f"<blockquote>❌ Gagal broadcast: {str(e)}</blockquote>", parse_mode="html")

    # Set Delay Handler
    @user.on(events.NewMessage(outgoing=True))
    async def set_delay_handler(event):
        """Set broadcast delay"""
        if not is_owner(event):
            return
            
        current_prefix = get_live_prefix()
        msg = event.text.strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}setdelay"):
                return
            parts = msg[len(current_prefix)+8:].strip().split()
        else:
            if not msg.lower().startswith("setdelay"):
                return
            parts = msg[8:].strip().split()

        try:
            nonlocal broadcast_delay
            broadcast_delay = int(parts[0])
            if broadcast_delay < 1:
                broadcast_delay = 1
            await event.edit(
                f"<blockquote><b>⏱ Delay broadcast disetel ke:</b> {broadcast_delay} detik</blockquote>",
                parse_mode="html"
            )
        except (IndexError, ValueError):
            await event.edit("<blockquote>❌ Format delay tidak valid! Gunakan: setdelay [angka]</blockquote>", parse_mode="html")

    # Add Blacklist Handler
    @user.on(events.NewMessage(outgoing=True))
    async def add_blacklist_handler(event):
        """Add chat to blacklist"""
        if not is_owner(event):
            return
            
        current_prefix = get_live_prefix()
        msg = event.text.strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}addbl"):
                return
            parts = msg[len(current_prefix)+5:].strip().split()
        else:
            if not msg.lower().startswith("addbl"):
                return
            parts = msg[5:].strip().split()
        
        chat_id = None
        if parts and parts[0].isdigit():
            chat_id = int(parts[0])
        elif event.is_private or event.is_group:
            chat_id = event.chat_id
        else:
            await event.edit("<blockquote>❌ Gunakan di PM/grup atau berikan ID chat</blockquote>", parse_mode="html")
            return

        if chat_id in blacklist:
            await event.edit("<blockquote>⚠️ Chat sudah ada di blacklist</blockquote>", parse_mode="html")
            return

        blacklist.append(chat_id)
        save_blacklist(blacklist)
        
        try:
            entity = await user.get_entity(chat_id)
            name = getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
        except:
            name = "Unknown"
            
        await event.edit(
            f"<blockquote><b>✅ Ditambahkan ke blacklist:</b></blockquote>\n"
            f"<blockquote>• Nama: {name}\n"
            f"• ID: {chat_id}</blockquote>",
            parse_mode="html"
        )

    # Remove Blacklist Handler
    @user.on(events.NewMessage(outgoing=True))
    async def del_blacklist_handler(event):
        """Remove chat from blacklist"""
        if not is_owner(event):
            return
            
        current_prefix = get_live_prefix()
        msg = event.text.strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}delbl"):
                return
            parts = msg[len(current_prefix)+5:].strip().split()
        else:
            if not msg.lower().startswith("delbl"):
                return
            parts = msg[5:].strip().split()
        
        chat_id = None
        if parts and parts[0].isdigit():
            chat_id = int(parts[0])
        elif event.is_private or event.is_group:
            chat_id = event.chat_id
        else:
            await event.edit("<blockquote>❌ Berikan ID chat atau gunakan di PM/grup</blockquote>", parse_mode="html")
            return

        if chat_id not in blacklist:
            await event.edit("<blockquote>⚠️ Chat tidak ditemukan di blacklist</blockquote>", parse_mode="html")
            return

        blacklist.remove(chat_id)
        save_blacklist(blacklist)
        
        try:
            entity = await user.get_entity(chat_id)
            name = getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
        except:
            name = "Unknown"
            
        await event.edit(
            f"<blockquote><b>✅ Dihapus dari blacklist:</b></blockquote>\n"
            f"<blockquote>• Nama: {name}\n"
            f"• ID: {chat_id}</blockquote>",
            parse_mode="html"
        )

    # List Blacklist Handler
    @user.on(events.NewMessage(outgoing=True))
    async def list_blacklist_handler(event):
        """List blacklisted chats"""
        if not is_owner(event):
            return
            
        current_prefix = get_live_prefix()
        msg = event.text.strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}listbl"):
                return
        else:
            if not msg.lower().startswith("listbl"):
                return

        if not blacklist:
            await event.edit("<blockquote>📭 Daftar blacklist kosong</blockquote>", parse_mode="html")
            return

        groups = []
        users = []
        
        for chat_id in blacklist:
            try:
                entity = await user.get_entity(chat_id)
                if isinstance(entity, (Channel, Chat)):
                    groups.append((chat_id, getattr(entity, 'title', 'Unknown Group')))
                else:
                    users.append((chat_id, getattr(entity, 'first_name', 'Unknown User')))
            except:
                if isinstance(chat_id, int) and chat_id > 0:
                    users.append((chat_id, "Unknown User"))
                else:
                    groups.append((chat_id, "Unknown Group"))

        message = "<blockquote><b>📋 Daftar Blacklist</b></blockquote>\n"
        
        if users:
            message += "\n<blockquote><b>👤 Chat Pribadi:</b></blockquote>\n"
            for idx, (user_id, name) in enumerate(users, 1):
                message += f"<blockquote>{idx}. {name} (<code>{user_id}</code>)</blockquote>\n"
        
        if groups:
            message += "\n<blockquote><b>👥 Grup/Channel:</b></blockquote>\n"
            for idx, (group_id, name) in enumerate(groups, 1):
                message += f"<blockquote>{idx}. {name} (<code>{group_id}</code>)</blockquote>\n"

        await event.edit(message, parse_mode="html")

    # Help Handler
    @user.on(events.NewMessage(outgoing=True))
    async def broadcast_help_handler(event):
        """Show broadcast help"""
        if not is_owner(event):
            return
            
        current_prefix = get_live_prefix()
        msg = event.text.strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}bchelp"):
                return
        else:
            if not msg.lower().startswith("bchelp"):
                return

        prefix = current_prefix if current_prefix else "[tanpa prefix]"
        help_text = (
            "<blockquote><b>📢 Panduan Broadcast</b></blockquote>\n\n"
            "<blockquote><b>• Broadcast:</b></blockquote>\n"
            f"<blockquote>{prefix}gcast [pesan/reply] - Broadcast ke semua grup\n"
            f"{prefix}ucast [pesan/reply] - Broadcast ke semua chat pribadi</blockquote>\n\n"
            "<blockquote><b>• Pengaturan:</b></blockquote>\n"
            f"<blockquote>{prefix}setdelay [detik] - Atur delay pengiriman\n"
            f"{prefix}addbl [id] - Tambah chat/grup ke blacklist\n"
            f"{prefix}delbl [id] - Hapus chat/grup dari blacklist\n"
            f"{prefix}listbl - Lihat daftar blacklist</blockquote>"
        )
        await event.edit(help_text, parse_mode="html")