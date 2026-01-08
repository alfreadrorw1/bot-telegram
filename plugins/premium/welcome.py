import os
import json
from telethon import events
from telethon.tl.types import ChannelParticipantsRecent
from telethon.errors import FloodWaitError, ChatWriteForbiddenError
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

async def setup(bot, client, user_id):
    """Setup welcome message for specific group"""
    current_user_id = user_id

    @client.on(events.ChatAction(chats=[-1002269607086]))
    async def welcome_handler(event):
        """Handle new member join events in the specific group"""
        # Check if user is authorized to use this bot
        is_authorized = (
            current_user_id == OWNER_ID or 
            is_premium_user(current_user_id))
        
        if not is_authorized:
            return

        # Check if this is a new member join event
        if event.user_joined:
            # Get the user who joined
            user = await event.get_user()
            
            # Create welcome message with mention
            welcome_message = f"wlcm <a href='tg://user?id={user.id}'>{user.first_name}</a>"
            
            try:
                # Send welcome message
                await event.reply(welcome_message, parse_mode="html")
            except FloodWaitError as e:
                # Handle flood wait errors (rate limits)
                print(f"Flood wait error: Need to wait {e.seconds} seconds before sending message again.")
                # You can add additional logic here, like logging or notifying the bot owner
            except ChatWriteForbiddenError:
                # Handle case when bot doesn't have permission to send messages
                print("Bot doesn't have permission to send messages in this chat.")
            except Exception as e:
                # Handle any other unexpected errors
                print(f"Unexpected error when sending welcome message: {e}")