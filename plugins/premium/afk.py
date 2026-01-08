# plugins/premium/afk.py
import json
import os
import time
from datetime import datetime, timedelta
from telethon import events
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

def get_afk_file(user_id=None):
    """Get AFK file path based on user"""
    user_folder = get_user_folder(user_id)
    return f'{user_folder}/afk.json'

def load_afk(user_id=None):
    """Load AFK status from file"""
    afk_file = get_afk_file(user_id)
    try:
        if not os.path.exists(os.path.dirname(afk_file)):
            os.makedirs(os.path.dirname(afk_file))
            
        if os.path.exists(afk_file):
            with open(afk_file, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, KeyError):
        pass
    return {"is_afk": False}

def save_afk(data, user_id=None):
    """Save AFK status to file"""
    afk_file = get_afk_file(user_id)
    with open(afk_file, 'w') as f:
        json.dump(data, f, indent=2)

def format_time(seconds):
    """Format time delta into human-readable format"""
    delta = timedelta(seconds=seconds)
    parts = []
    if delta.days > 0:
        parts.append(f"{delta.days}d")
    hours, remainder = divmod(delta.seconds, 3600)
    if hours > 0:
        parts.append(f"{hours}h")
    minutes, seconds = divmod(remainder, 60)
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return ' '.join(parts)

async def setup(bot, client, user_id):
    current_user_id = user_id  # Store user_id in a local variable

    @client.on(events.NewMessage())
    async def afk_handler(event):
        """Handle AFK commands and notifications"""
        # Check if user is owner or premium with active session
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # AFK Command
        if msg.startswith(f"{current_prefix}afk"):
            reason = msg[len(current_prefix)+3:].strip() or "Tidak ada alasan"
            
            data = {
                "is_afk": True,
                "reason": reason,
                "since": time.time(),
                "last_seen": datetime.now().isoformat()
            }
            save_afk(data, current_user_id)
            await event.delete()
            await event.respond(f"<blockquote>🚀 AFK Mode Aktif\n📌 Alasan: {reason}</blockquote>", parse_mode="html")
        
        # UNAFK Command
        elif msg == f"{current_prefix}unafk":
            data = load_afk(current_user_id)
            if not data.get("is_afk"):
                await event.reply("```❌ Anda tidak sedang AFK</blockquote>", parse_mode="html")
                return
            
            duration = format_time(time.time() - data.get("since", time.time()))
            data["is_afk"] = False
            save_afk(data, current_user_id)
            await event.delete()
            await event.respond(f"<blockquote>🎉 Selamat datang kembali!\n⏱️ Durasi AFK: {duration}</blockquote>", parse_mode="html")
        
        # AFK Notification (for mentions)
        elif event.is_private or (event.message.mentioned and not event.message.text.startswith(current_prefix)):
            data = load_afk(current_user_id)
            if not data.get("is_afk"):
                return
                
            reason = data.get("reason", "Tidak ada alasan")
            duration = format_time(time.time() - data.get("since", time.time()))
            
            await event.reply(
                f"<blockquote>🙊 Sedang AFK\n"
                f"📌 Alasan: {reason}\n"
                f"⏱️ Durasi: {duration}</blockquote>", parse_mode="html"
            )

    