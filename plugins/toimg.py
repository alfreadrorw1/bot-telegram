# plugins/colong.py
import os
import json
import random
import asyncio
from telethon import events
from telethon.tl.types import DocumentAttributeVideo
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
STICKER_DIR = os.path.join(CONFIG_DIR, 'img')
os.makedirs(STICKER_DIR, exist_ok=True)

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def sticker_handler(event):
        """Handle sticker creation commands"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_sticker_cmd = False
        command = ""
        args = ""
        
        if current_prefix:
            if msg.startswith(current_prefix):
                cmd_part = msg[len(current_prefix):].strip().split(maxsplit=1)
                if cmd_part and cmd_part[0].lower() in ['img']:
                    is_sticker_cmd = True
                    command = cmd_part[0].lower()
                    args = cmd_part[1] if len(cmd_part) > 1 else ""
        else:
            cmd_part = msg.lower().split(maxsplit=1)
            if cmd_part and cmd_part[0] in ['img']:
                is_sticker_cmd = True
                command = cmd_part[0].lower()
                args = cmd_part[1] if len(cmd_part) > 1 else ""
                
        if not is_sticker_cmd:
            return

        if not event.is_reply:
            status = await event.reply(f"```❌ Harus reply sticker dengan caption {current_prefix}{command}```")
            await asyncio.sleep(3)
            await event.delete()
            await status.delete()
            return

        reply_msg = await event.get_reply_message()
        status = await event.reply("```🔄 Memproses sticker...```")

        try:
            # Check media type
            if not (reply_msg.photo or reply_msg.video or 
                  (reply_msg.document and (reply_msg.document.mime_type.startswith('image/') or 
                                         reply_msg.document.mime_type.startswith('video/')))):
                await status.edit("```❌ Format tidak didukung! Hanya sticker```")
                await asyncio.sleep(3)
                await status.delete()
                return

            # Process packname and author
            parts = args.split('|', 1)
            packname = parts[0].strip() if parts and parts[0].strip() else 'Sticker Pack'
            author = parts[1].strip() if len(parts) > 1 and parts[1].strip() else 'Userbot'

            # Video duration check
            if reply_msg.video or (reply_msg.document and reply_msg.document.mime_type.startswith('video/')):
                duration = 0
                for attr in reply_msg.document.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        duration = attr.duration
                        break
                if duration > 10:
                    await status.edit("```❌ Video terlalu panjang! Maksimal 10 detik```")
                    await asyncio.sleep(3)
                    await status.delete()
                    return

            # Download media with proper file extension
            temp_file = os.path.join(STICKER_DIR, f"temp_{random.randint(1000,9999)}")
            if reply_msg.photo or (reply_msg.document and reply_msg.document.mime_type.startswith('image/')):
                temp_file += '.jpg'
            else:
                temp_file += '.mp4'
                
            await reply_msg.download_media(file=temp_file)
            
            # Send as sticker with explicit mime type
            if reply_msg.photo or (reply_msg.document and reply_msg.document.mime_type.startswith('image/')):
                mime_type = 'image/jpeg'
            else:
                mime_type = 'video/mp4'
            
            await user.send_file(
                event.chat_id,
                temp_file,
                force_document=False,
                allow_cache=False,
                sticker=True,
                attributes=[],
                reply_to=reply_msg.id,
                mime_type=mime_type,
                packname=packname,
                author=author
            )
            
            await status.delete()
            await event.delete()

        except Exception as e:
            await status.edit(f"```❌ Gagal membuat sticker: {str(e)[:200]}```")
            await asyncio.sleep(5)
            await status.delete()
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)