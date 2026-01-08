import json
import os
import time
from datetime import datetime, timedelta
from telethon import events
from config import OWNER_ID

# File configuration
CONFIG_DIR = 'data'
AFK_FILE = os.path.join(CONFIG_DIR, 'afk.json')
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

def get_live_prefix():
    """Get current prefix directly from file with caching"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

def load_afk():
    """Load AFK status from file"""
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            
        if os.path.exists(AFK_FILE):
            with open(AFK_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, KeyError):
        pass
    return {"is_afk": False}

def save_afk(data):
    """Save AFK status to file"""
    with open(AFK_FILE, 'w') as f:
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

async def setup(bot, user):
    # AFK Command Handler
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def afk_command_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check for AFK command
        is_afk_cmd = False
        reason = "Tidak ada alasan"
        
        if current_prefix == "no":
            if msg.lower().startswith("afk"):
                is_afk_cmd = True
                reason = msg[3:].strip() or reason
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd.startswith("afk"):
                    is_afk_cmd = True
                    reason = cmd[3:].strip() or reason
        
        if not is_afk_cmd:
            return
            
        data = {
            "is_afk": True,
            "reason": reason,
            "since": time.time(),
            "last_seen": datetime.now().isoformat()
        }
        save_afk(data)
        await event.delete()
        await event.respond(f"```🚀 AFK Mode Aktif\n📌 Alasan: {reason}```")

    # UNAFK Command Handler
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def unafk_command_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check for UNAFK command
        is_unafk_cmd = False
        
        if current_prefix == "no":
            if msg.lower() == "unafk":
                is_unafk_cmd = True
        else:
            if msg == f"{current_prefix}unafk":
                is_unafk_cmd = True
                
        if not is_unafk_cmd:
            return
            
        data = load_afk()
        if not data.get("is_afk"):
            await event.reply("```❌ Anda tidak sedang AFK```")
            return
        
        duration = format_time(time.time() - data.get("since", time.time()))
        data["is_afk"] = False
        save_afk(data)
        await event.delete()
        await event.respond(f"```🎉 Selamat datang kembali!\n⏱️ Durasi AFK: {duration}```")

    # AFK Notification Handler
    @user.on(events.NewMessage(
        incoming=True,
        func=lambda e: e.is_private or (
            e.message.mentioned and not e.message.text.startswith(get_live_prefix())
        )
    ))
    async def afk_notify_handler(event):
        data = load_afk()
        if not data.get("is_afk"):
            return
            
        reason = data.get("reason", "Tidak ada alasan")
        duration = format_time(time.time() - data.get("since", time.time()))
        
        await event.reply(
            f"```🙊 Sedang AFK\n"
            f"📌 Alasan: {reason}\n"
            f"⏱️ Durasi: {duration}```"
        )