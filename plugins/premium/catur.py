# plugins/premium/catur.py
import json
import os
import asyncio
from telethon import events
from config import OWNER_ID

# Game bot configuration
GAME_BOT = '@GameFactoryBot'

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

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except:
        pass

async def setup(bot, client, user_id):
    """Setup chess command for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def chess_handler(event):
        """Handle chess command"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # Check command format
        is_chess_cmd = False
        
        if current_prefix == "no":
            if msg.lower() == "catur":
                is_chess_cmd = True
        else:
            if msg == f"{current_prefix}catur":
                is_chess_cmd = True
                
        if not is_chess_cmd:
            return

        try:
            await safe_delete(event)
            
            async with client.conversation(GAME_BOT) as conv:
                # Step 1: Start the game bot
                await conv.send_message('/start')
                start_response = await conv.get_response()
                
                # Step 2: Click the first button (chess)
                if start_response.buttons:
                    await start_response.click(0)
                    game_response = await conv.get_response()
                    
                    # Step 3: Forward the actual game message
                    if game_response:
                        await client.forward_messages(
                            entity=event.chat_id,
                            messages=game_response,
                            from_peer=GAME_BOT,
                            silent=True
                        )
                    else:
                        raise Exception("Tidak mendapatkan response game")
                else:
                    raise Exception("Tombol game tidak ditemukan")
                    
        except Exception as e:
            error_msg = await event.respond(f"<blockquote>❌ Gagal: {str(e)[:200]}</blockquote>", parse_mode="html")
            await asyncio.sleep(5)
            await safe_delete(error_msg)