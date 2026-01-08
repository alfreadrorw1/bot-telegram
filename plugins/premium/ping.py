# plugins/premium/ping.py
import time
import json
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

async def setup(bot, connect_user, user_id=None):
    """
    Setup ping command for premium users with proper authorization.
    
    Parameters:
        bot: The main bot client
        connect_user: The connected user client
        user_id: The user ID of the premium user
    """
    current_user_id = user_id  # Store user_id in a local variable

    @connect_user.on(events.NewMessage())
    async def ping_handler(event):
        """Handle ping commands from premium users"""
        # Check if user is owner or premium with active session
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id)
        )
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.raw_text or '').strip()
        
        # Check for ping command with user's prefix
        is_ping_cmd = False
        if current_prefix == "no":
            if message.lower() == "ping":
                is_ping_cmd = True
        else:
            if message.lower().startswith(current_prefix.lower()):
                cmd = message[len(current_prefix):].strip().lower()
                if cmd == "ping":
                    is_ping_cmd = True
        
        if not is_ping_cmd:
            return

        # Execute ping command
        start = time.perf_counter()
        msg = await event.respond("<blockquote>ᴘɪɴɢɪɴɢ...</blockquote>", parse_mode='html')
        end = time.perf_counter()

        latency = (end - start) * 1000
        me = await connect_user.get_me()

        response = (
            f"<blockquote>𝗽𝗼𝗻𝗴: <b>{latency:.2f} ms</b>\n"
            f"𝗨𝘀𝗲𝗿𝗯𝗼𝘁: <b>AlfreadRorw</b></blockquote>\n\n"
        )
        
        if sender_id != OWNER_ID:
            try:
                owner_entity = await bot.get_entity(OWNER_ID)
                response += f"<blockquote><i>Owner: {owner_entity.first_name}</i></blockquote>"
            except:
                response += f"<blockquote><i>Owner: ID {OWNER_ID}</i></blockquote>"
        else:
            response += f"<blockquote><i>You: {me.first_name}</i></blockquote>"

        await msg.edit(response, parse_mode='html')