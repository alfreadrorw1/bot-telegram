import time
import json
import re
import os
from telethon import events
from config import OWNER_ID

def get_uptime():
    """Calculate bot uptime in human-readable format"""
    try:
        with open('data/uptime.json', 'r') as f:
            start_time = json.load(f).get('start_time', time.time())
    except (FileNotFoundError, json.JSONDecodeError):
        start_time = time.time()
        os.makedirs('data', exist_ok=True)
        with open('data/uptime.json', 'w') as f:
            json.dump({'start_time': start_time}, f)
    
    uptime = int(time.time() - start_time)
    days, remainder = divmod(uptime, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")
    
    return ' '.join(parts)

def get_prefix():
    """Get current prefix from config (supports 'no' prefix mode)"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def setup(bot, user):
    @user.on(events.NewMessage())
    async def ping_handler(event):
        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        # Check if message is a ping command
        is_ping = (
            (current_prefix == "no" and message == "ping") or
            (message.startswith(current_prefix.lower()) and 
             "ping" in message[len(current_prefix):].strip())
        )
        
        if not is_ping or event.sender_id != OWNER_ID:
            return

        # Execute ping command
        start = time.perf_counter()
        msg = await event.respond("<blockquote>ᴘɪɴɢɪɴɢ...</blockquote>", parse_mode='html')
        end = time.perf_counter()

        latency = (end - start) * 1000
        uptime = get_uptime()
        me = await user.get_me()

        await msg.edit(
            f"<blockquote>𝗽𝗼𝗻𝗴: <b>{latency:.2f} ms</b>\n"
            f"𝗨𝗽𝘁𝗶𝗺𝗲: <b>{uptime}</b>\n"
            f"𝗨𝘀𝗲𝗿𝗯𝗼𝘁 :<b>AlfreadRorw</b></blockquote>\n\n"
            f"<blockquote><i>Owner: {me.first_name}</i></blockquote>",
            parse_mode='html'
        )