# plugins/id.py
import os
import json
from telethon import events
from config import OWNER_ID
from datetime import datetime

# Configuration
CONFIG_DIR = 'data'
os.makedirs(CONFIG_DIR, exist_ok=True)
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def setup(bot, user):
    current_prefix = get_live_prefix()
    
    @user.on(events.NewMessage(outgoing=True, pattern=f'^{current_prefix}id$'))
    async def id_handler(event):
        """Handle id command in both groups and PMs"""
        try:
            chat = await event.get_chat()
            if event.is_private:
                # PM case - show user ID
                user_id = chat.id
                await event.reply(f"<blockquote>👤 <b>ID Pengguna:</b> <code>{user_id}</code></blockquote>", parse_mode="html")
            else:
                # Group case - show group ID
                group_id = event.chat_id
                group_title = getattr(chat, 'title', 'Unknown Group')
                
                # Check if group has username
                username = getattr(chat, 'username', None)
                link = f"https://t.me/{username}" if username else None
                
                message = (
                    f"<blockquote>"
                    f"📌 <b>Info Grup</b>\n"
                    f"<b>Nama:</b> {group_title}\n"
                    f"<b>ID Grup:</b> <code>{group_id}</code>\n"
                )
                
                if link:
                    message += f"<b>Link:</b> <a href='{link}'>Klik disini</a>"
                
                message += "</blockquote>"
                
                await event.reply(message, parse_mode="html")
                
        except Exception as e:
            await event.reply(f"<blockquote>❌ Error: {str(e)}</blockquote>", parse_mode="html")