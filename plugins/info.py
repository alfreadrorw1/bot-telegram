import os
import json
from datetime import datetime
from telethon import events, functions
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import (
    UserStatusOnline, UserStatusOffline, UserStatusRecently,
    UserStatusLastWeek, UserStatusLastMonth,
    ChannelParticipantCreator, ChannelParticipantAdmin,
    ChannelParticipantBanned
)
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_data_dir()
        with open(PREFIX_FILE, 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def setup(bot, user):
    ensure_data_dir()

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def info_handler(event):
        """Handle info command"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        if current_prefix:
            if not msg.startswith(f"{current_prefix}info"):
                return
            target = msg[len(current_prefix)+4:].strip()
        else:
            if not msg.lower().startswith("info"):
                return
            target = msg[4:].strip()

        # Get target user
        try:
            if target:
                user_entity = await user.get_entity(target)
            else:
                reply = await event.get_reply_message()
                if not reply:
                    await event.reply("```Balas pesan atau berikan username/ID```")
                    return
                user_entity = await user.get_entity(reply.sender_id)
        except Exception as e:
            await event.reply(f"```Tidak dapat menemukan user: {str(e)}```")
            return

        # Get full user info
        try:
            full = await user(GetFullUserRequest(user_entity.id))
        except Exception as e:
            await event.reply(f"```Tidak dapat mendapatkan info lengkap: {str(e)}```")
            return

        # Get common chats count
        try:
            common = await user(functions.messages.GetCommonChatsRequest(
                user_id=user_entity.id,
                max_id=0,
                limit=1
            ))
            common_chats = len(common.chats)
        except:
            common_chats = 0

        # Prepare info lines
        info_lines = [
            "**🔍 Informasi User**",
            f"**Nama Depan:** `{user_entity.first_name or 'Tidak ada'}`",
            f"**Nama Belakang:** `{user_entity.last_name or 'Tidak ada'}`",
            f"**User ID:** `{user_entity.id}`",
            f"**Username:** `@{user_entity.username}`" if user_entity.username else "**Username:** `Tidak ada`",
            f"**Nomor HP:** `{user_entity.phone or 'Tersembunyi'}`",
            f"**Bio:** `{getattr(full.full_user, 'about', 'Tidak ada')}`",
            "",
            "**📌 Detail Akun**",
            f"**Foto Profil:** `{'Ada' if user_entity.photo else 'Tidak ada'}`",
            f"**Grup Bersama:** `{common_chats}+`",
            f"**Bot:** `{'Ya' if user_entity.bot else 'Tidak'}`",
            f"**Verified:** `{'Ya' if user_entity.verified else 'Tidak'}`",
            f"**Scam:** `{'Ya' if user_entity.scam else 'Tidak'}`",
            f"**Support:** `{'Ya' if user_entity.support else 'Tidak'}`",
            f"**Premium:** `{'Ya' if user_entity.premium else 'Tidak'}`",
        ]

        # Add status info
        status = user_entity.status
        if isinstance(status, UserStatusOnline):
            status_str = "🟢 Online"
        elif isinstance(status, UserStatusRecently):
            status_str = "🟡 Baru saja terlihat"
        elif isinstance(status, UserStatusLastWeek):
            status_str = "🟠 Terlihat seminggu lalu"
        elif isinstance(status, UserStatusLastMonth):
            status_str = "🔴 Terlihat sebulan lalu"
        elif isinstance(status, UserStatusOffline):
            was = datetime.fromtimestamp(status.was_online)
            status_str = f"⚫ Terakhir online {was.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            status_str = "⚪ Status tidak diketahui"
        info_lines.append(f"**Status:** {status_str}")

        # Add group role if in group
        if event.is_group:
            try:
                part = await user(GetParticipantRequest(event.chat_id, user_entity.id))
                p = part.participant
                if isinstance(p, ChannelParticipantCreator):
                    role = "👑 Creator"
                elif isinstance(p, ChannelParticipantAdmin):
                    role = "🛡️ Admin"
                elif isinstance(p, ChannelParticipantBanned):
                    role = "🚫 Banned"
                else:
                    role = "👤 Member"
                info_lines.append(f"**Role di grup:** {role}")
            except:
                pass

        await event.reply("\n".join(info_lines), link_preview=False)