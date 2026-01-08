from telethon import events
import asyncio
import json
import os
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

# Dictionary untuk menyimpan pesan
message_storage = {}

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def setup(bot, user_client):
    """Setup handler untuk plugin"""
    global user
    user = user_client

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def copy_handler(event):
        """Handler untuk menyalin pesan"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        is_copy_cmd = False
        
        if current_prefix == "no":
            if msg == 'c' and event.is_reply:
                is_copy_cmd = True
        else:
            if msg == f"{current_prefix}c" and event.is_reply:
                is_copy_cmd = True
                
        if not is_copy_cmd:
            return
            
        reply_msg = await event.get_reply_message()
        message_storage[event.sender_id] = reply_msg
        
        notif = await event.respond("<blockquote>✅ <b>Pesan telah disalin!</b></blockquote>", parse_mode="html")
        await asyncio.sleep(1)
        await notif.delete()
        await event.delete()

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def paste_handler(event):
        """Handler untuk menempel pesan"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        is_paste_cmd = False
        
        if current_prefix == "no":
            if msg == 'p':
                is_paste_cmd = True
        else:
            if msg == f"{current_prefix}p":
                is_paste_cmd = True
                
        if not is_paste_cmd:
            return
            
        if event.sender_id not in message_storage:
            notif = await event.respond("<blockquote>❌ <b>Tidak ada pesan yang disalin!</b></blockquote>", parse_mode="html")
            await asyncio.sleep(1)
            await notif.delete()
            await event.delete()
            return
        
        await message_storage[event.sender_id].forward_to(event.chat_id)
        await event.delete()

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def paste_with_text_handler(event):
        """Handler untuk tempel dengan teks tambahan"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        is_paste_text_cmd = False
        additional_text = None
        
        if current_prefix == "no":
            if msg.startswith('p '):
                is_paste_text_cmd = True
                additional_text = msg[2:]
        else:
            if msg.startswith(f"{current_prefix}p "):
                is_paste_text_cmd = True
                additional_text = msg[len(current_prefix)+2:]
                
        if not is_paste_text_cmd:
            return
            
        if event.sender_id not in message_storage:
            notif = await event.respond("<blockquote>❌ <b>Tidak ada pesan yang disalin!</b></blockquote>", parse_mode="html")
            await asyncio.sleep(1)
            await notif.delete()
            await event.delete()
            return
        
        # Format additional text with blockquote if it's not empty
        if additional_text.strip():
            formatted_text = f"<blockquote>{additional_text}</blockquote>"
            await event.respond(formatted_text, parse_mode="html")
        
        await message_storage[event.sender_id].forward_to(event.chat_id)
        await event.delete()