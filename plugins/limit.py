import os
import json
import asyncio
from config import OWNER_ID
from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

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

async def check_limit_status(client):
    """Check account limit status with SpamBot"""
    try:
        async with client.conversation('@SpamBot') as conv:
            # Wait for response from SpamBot (user ID 178220800)
            response_event = conv.wait_event(
                events.NewMessage(incoming=True, from_users=178220800))
            
            await conv.send_message('/start')
            response = await response_event
            await client.send_read_acknowledge(conv.chat_id)
            
            return response.text
    except YouBlockedUserError:
        logger.warning("User has blocked @SpamBot")
        return None
    except Exception as e:
        logger.error(f"Error checking limit: {str(e)}")
        return None

def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def limit_handler(event):
        """Handle limit check command"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        if current_prefix:
            if msg != f"{current_prefix}limit":
                return
        else:
            if msg.lower() != "limit":
                return

        try:
            # Get sender info
            sender = await event.get_sender()
            name = sender.first_name or "Pengguna"
            
            # Send initial message
            progress_msg = await event.reply("<i>🔄 Memeriksa status limit...</i>", parse_mode="html")
            
            # Check limit status
            limit_info = await check_limit_status(user)
            
            if limit_info is None:
                await progress_msg.edit(
                    "<b>❗ Silakan unblock @SpamBot terlebih dahulu untuk memeriksa limit.</b>",
                    parse_mode="html"
                )
                return
            
            # Format the response
            formatted_response = limit_info.replace('\n', '<br>')
            result_message = (
                f"<blockquote><b>📊 Status Limit untuk:</b> {name}</blockquote>\n"
                f"<blockquote>{formatted_response}</blockquote>"
            )
            
            # Edit the progress message with results
            await progress_msg.edit(
                result_message, 
                parse_mode="html", 
                link_preview=False
            )
            
        except Exception as e:
            logger.error(f"Error in limit handler: {str(e)}")
            try:
                await event.reply(
                    f"<b>⚠️ Gagal memeriksa limit:</b> {str(e)}",
                    parse_mode="html"
                )
            except:
                pass