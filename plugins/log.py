import os
import json
import aiohttp
import asyncio
from datetime import datetime
from telethon import events, Button
from telethon.tl.types import PeerUser
from telethon.errors import FloodWaitError
from config import OWNER_ID, BOT_TOKEN

# Configuration
CONFIG_DIR = 'data'
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs('downloads', exist_ok=True)  # Folder for downloaded media

PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
LOG_STATUS_FILE = os.path.join(CONFIG_DIR, 'log_status.json')
NOTIF_GROUP_ID = -1002394303346  # Replace with your log group ID

# Cache for bot information
bot_info_cache = {
    'me': None,
    'last_updated': 0
}

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

def get_log_status():
    """Get log notification statuses for groups and PM"""
    default_status = {"groups": False, "pm": False}
    try:
        if not os.path.exists(LOG_STATUS_FILE):
            with open(LOG_STATUS_FILE, 'w') as f:
                json.dump(default_status, f)
            return default_status
            
        with open(LOG_STATUS_FILE, 'r') as f:
            data = json.load(f)
            for key in default_status:
                if key not in data:
                    data[key] = default_status[key]
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return default_status

def set_log_status(status_type, status):
    """Set log status for groups or PM"""
    current_status = get_log_status()
    current_status[status_type] = status
    with open(LOG_STATUS_FILE, 'w') as f:
        json.dump(current_status, f)

async def get_bot_info(user):
    """Get cached bot info with flood wait handling"""
    global bot_info_cache
    
    if bot_info_cache['me'] and (datetime.now().timestamp() - bot_info_cache['last_updated'] < 300):
        return bot_info_cache['me']
    
    try:
        bot_info_cache['me'] = await user.get_me()
        bot_info_cache['last_updated'] = datetime.now().timestamp()
        return bot_info_cache['me']
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return await get_bot_info(user)
    except Exception:
        return None

async def download_media(event):
    """Download media to downloads folder"""
    try:
        ext_map = {
            'photo': 'jpg',
            'video': 'mp4',
            'sticker': 'webp',
            'audio': 'mp3',
            'voice': 'ogg',
            'gif': 'mp4',
            'document': 'bin'
        }
        
        for attr, ext in ext_map.items():
            if getattr(event, attr, None):
                filename = f"downloads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{attr}.{ext}"
                await event.download_media(file=filename)
                return filename, attr
        return None, None
    except Exception:
        return None, None

async def send_to_log(text, buttons=None, media_path=None, media_type=None):
    """Send message to log group with proper media handling"""
    try:
        if media_path and os.path.exists(media_path):
            # Determine the appropriate API endpoint based on media type
            api_map = {
                'photo': 'sendPhoto',
                'video': 'sendVideo',
                'sticker': 'sendSticker',
                'audio': 'sendAudio',
                'voice': 'sendVoice',
                'document': 'sendDocument'
            }
            
            endpoint = api_map.get(media_type, 'sendDocument')
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}"
            
            with open(media_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('chat_id', str(NOTIF_GROUP_ID))
                form.add_field('caption', text[:1024])
                form.add_field('parse_mode', 'markdown')
                
                # Special handling for different media types
                if media_type == 'sticker':
                    form.add_field('sticker', f)
                else:
                    form.add_field(media_type, f)
                
                async with aiohttp.ClientSession() as session:
                    await session.post(url, data=form)
                    
                # Clean up downloaded file
                os.remove(media_path)
                
            # Send buttons separately if they exist
            if buttons:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                data = {
                    "chat_id": NOTIF_GROUP_ID,
                    "text": "⬆️ Media above",
                    "reply_markup": {
                        "inline_keyboard": [[{"text": b.text, "url": b.url}] for b in buttons[0]]
                    }
                }
                async with aiohttp.ClientSession() as session:
                    await session.post(url, json=data)
        else:
            # Text-only message
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": NOTIF_GROUP_ID,
                "text": text,
                "parse_mode": "markdown",
            }
            if buttons:
                data["reply_markup"] = {
                    "inline_keyboard": [[{"text": b.text, "url": b.url}] for b in buttons[0]]
                }
            
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=data)
    except Exception:
        if media_path and os.path.exists(media_path):
            os.remove(media_path)

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def log_cmd(event):
        """Handle log enable/disable commands"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        if not msg.startswith((f"{current_prefix}log", f"{current_prefix}pmlog")):
            return
            
        args = msg.split()
        if len(args) < 2:
            return await event.delete()
        
        if args[0].lower() == f"{current_prefix}log":
            log_type = "groups"
        elif args[0].lower() == f"{current_prefix}pmlog":
            log_type = "pm"
        else:
            return
            
        if args[1].lower() not in ("on", "off"):
            return await event.delete()
            
        set_log_status(log_type, args[1].lower() == "on")
        status_text = "✅ diaktifkan" if args[1].lower() == "on" else "❌ dimatikan"
        await event.reply(f"**Log {log_type} {status_text}**")
        await event.delete()

    @user.on(events.NewMessage(incoming=True))
    async def notif_handler(event):
        """Handle incoming message notifications"""
        try:
            log_status = get_log_status()
            me = await get_bot_info(user)
            if not me:
                return
                
            sender = await event.get_sender()
            is_pm = isinstance(event.message.to_id, PeerUser)
            
            if is_pm:
                if not log_status["pm"] or sender.id == me.id:
                    return
            else:
                if not log_status["groups"]:
                    return
                    
                is_mentioned = (
                    getattr(event.message, "mentioned", False) or 
                    (me.username and f"@{me.username}" in (event.raw_text or "")))
                
                is_reply = False
                if event.is_reply:
                    reply_msg = await event.get_reply_message()
                    is_reply = reply_msg and reply_msg.sender_id == OWNER_ID
                
                if not (is_mentioned or is_reply):
                    return

            # Prepare message details
            sender_name = getattr(sender, "first_name", "Unknown")
            if getattr(sender, 'last_name', None):
                sender_name += f" {sender.last_name}"
                
            sender_id = sender.id
            chat = await event.get_chat()
            group_title = getattr(chat, "title", "Private Message")
            chat_id = event.chat_id
            message = event.raw_text or ""
            date_str = event.date.strftime("%Y-%m-%d %H:%M:%S")

            # Handle media
            media_path, media_type = await download_media(event)
            msg_type = "Text"
            type_emoji = {
                'photo': '🖼 Photo',
                'video': '🎥 Video',
                'sticker': '🧩 Sticker',
                'audio': '🎵 Audio',
                'voice': '🎤 Voice',
                'gif': '🎞 GIF',
                'document': '📄 Document'
            }
            
            if media_type:
                msg_type = type_emoji.get(media_type, media_type.capitalize())

            # Build notification
            notif_text = (
                f"```📨 {'PM' if is_pm else 'GROUP'} NOTIFICATION ```\n"
                f"**User:** {sender_name}\n"
                f"**ID:** `{sender_id}`\n"
                f"**Chat:** {group_title}\n"
                f"**Chat ID:** `{chat_id}`\n"
                f"**Time:** `{date_str}`\n"
                f"**Type:** {msg_type}\n"
            )

            if message and not media_type:
                notif_text += f"**Message:**\n```{message[:1000]}```\n"

            # Add button for group messages
            buttons = None
            if not is_pm and str(chat_id).startswith("-100"):
                url_chat = f"https://t.me/c/{str(chat_id)[4:]}/{event.id}"
                buttons = [[Button.url("📩 Open Message", url_chat)]]

            await send_to_log(notif_text, buttons, media_path, media_type)

        except FloodWaitError:
            return
        except Exception:
            return