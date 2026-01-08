import os
import json
import asyncio
from telethon import events
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
UPLOAD_BOT = "@AR_UrlUploaderBot"

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
    async def tourl_handler(event):
        """Forward media to upload bot and forward response"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_tourl_cmd = False
        if current_prefix:
            if msg.startswith(f"{current_prefix}tourl"):
                is_tourl_cmd = True
        else:
            if msg.lower().startswith("tourl"):
                is_tourl_cmd = True
                
        if not is_tourl_cmd:
            return

        # Check if replying to media
        if not event.is_reply:
            status = await event.reply("```🚫 Reply ke gambar/file!```")
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()
            return

        reply = await event.get_reply_message()
        
        # Check if replied message has media
        if not reply.media:
            status = await event.reply("```🚫 Pesan yang di-reply tidak mengandung media!```")
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()
            return

        # Send processing status
        processing_msg = await event.reply("```🔄 Mengupload media...```")
        
        try:
            # Forward media to upload bot
            await user.forward_messages(UPLOAD_BOT, reply)
            
            # Wait for 5 seconds
            await asyncio.sleep(5)
            
            # Get the last message from upload bot
            async for message in user.iter_messages(UPLOAD_BOT, limit=1):
                # Forward whatever response we got
                await message.forward_to(event.chat_id)
            
        except Exception as e:
            await event.reply(f"```❌ Error: {str(e)}```", reply_to=reply.id)
        finally:
            await processing_msg.delete()
            await event.delete()