# plugins/premium/prefix.py
import re
import json
import os
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

def save_prefix(new_prefix, user_id=None):
    """Save prefix for specific user"""
    user_folder = get_user_folder(user_id)
    os.makedirs(user_folder, exist_ok=True)
    with open(f'{user_folder}/prefix.json', 'w') as f:
        json.dump({'prefix': new_prefix}, f)

def is_premium_user(user_id):
    """Check if user is premium"""
    try:
        with open('premium/premium.json', 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return False

async def setup(bot, client, user_id):
    current_user_id = user_id  # Store user_id in a local variable

    @client.on(events.NewMessage())
    async def prefix_handler(event):
        """Handle prefix commands"""
        # Check if user is owner or premium with active session
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id)
        )
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.text or '').strip()
        
        # Setprefix command
        if re.match(r"(?i)^setprefix\s+(.+)$", message):
            input_prefix = re.match(r"(?i)^setprefix\s+(.+)$", message).group(1).strip().lower()

            if input_prefix == "no":
                save_prefix("no", current_user_id)
                await event.reply(f"<blockquote> Prefix dinonaktifkan! Gunakan command tanpa prefix.</blockquote>", parse_mode="html")
            elif len(input_prefix) == 1:
                save_prefix(input_prefix, current_user_id)
                await event.reply(f"<blockquote>✅ Prefix diubah ke `{input_prefix}`</blockquote>", parse_mode="html")
            else:
                await event.reply(f"<blockquote> Panjang prefix harus 1 karakter atau `setprefix no`!</blockquote>", parse_mode="html")
        
        # Prefix check command
        elif message.lower() == "prefix":
            status = "`tidak ada`" if get_prefix(current_user_id) == "no" else f"`{get_prefix(current_user_id)}`"
            await event.reply(f"<blockquote>🔠 Prefix saat ini: {status}</blockquote>", parse_mode="html")
