# plugins/premium/limit.py
import os
import json
import asyncio
from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
from config import OWNER_ID

def get_user_folder(user_id=None):
    """Get user-specific folder path"""
    if user_id is None or str(user_id) == str(OWNER_ID):
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

async def setup(bot, connect_user, user_id=None):
    """
    Setup limit checker for premium users with proper authorization.
    
    Parameters:
        bot: The main bot client
        connect_user: The connected user client
        user_id: The user ID of the premium user
    """
    current_user_id = user_id  # Store user_id in a local variable

    @connect_user.on(events.NewMessage())
    async def limit_handler(event):
        """Handle limit check commands"""
        # Check if user is owner or premium with active session
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.raw_text or '').strip().lower()
        
        # Check for limit command with user's prefix
        is_limit_cmd = False
        if current_prefix == "no":
            if message == "limit":
                is_limit_cmd = True
        else:
            if message.startswith(current_prefix.lower()):
                cmd = message[len(current_prefix):].strip().lower()
                if cmd == "limit":
                    is_limit_cmd = True
        
        if not is_limit_cmd:
            return

        processing_msg = await event.respond("<i>🔍 Checking Telegram limits...</i>", parse_mode="html")
        
        try:
            async with connect_user.conversation('@SpamBot') as conv:
                # Send initial command
                await conv.send_message('/start')
                response = await conv.get_response()
                await connect_user.send_read_acknowledge(conv.chat_id)
                
                # Get user info
                user = await event.get_sender()
                name = user.first_name or "User"
                
                # Format response - fixed f-string issue
                response_text = response.text.replace('\n', '<br>')
                result = (
                    "<blockquote><b>📊 Telegram Limit Status</b> for {}</blockquote>\n"
                    "<blockquote>{}</blockquote>\n\n"
                    "<i>Checked via AlfreadRorw Premium</i>"
                ).format(name, response_text)
                
                await processing_msg.edit(result, parse_mode="html", link_preview=False)
                
        except YouBlockedUserError:
            await processing_msg.edit(
                "<blockquote>❌ <b>Error:</b> You've blocked @SpamBot</blockquote>\n"
                "<blockquote><i>Please unblock @SpamBot to use this feature</i></blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            await processing_msg.edit(
                "<blockquote>⚠️ <b>Error checking limits:</b></blockquote>\n"
                "<code>{}</code>".format(str(e)),
                parse_mode="html"
            )