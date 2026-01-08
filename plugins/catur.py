import json
import os
import asyncio
from telethon import events
from config import OWNER_ID

# File configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

# Game bot configuration
GAME_BOT = '@GameFactoryBot'

def get_live_prefix():
    """Get current prefix directly from file with caching"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def setup(bot, user):
    # Chess command handler (following AFK plugin pattern exactly)
    @user.on(events.NewMessage(
        outgoing=True,
        from_users=OWNER_ID
    ))
    async def chess_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check for chess command (same pattern as AFK)
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
            await event.delete()
            
            async with user.conversation(GAME_BOT) as conv:
                # Step 1: Start the game bot
                await conv.send_message('/start')
                start_response = await conv.get_response()
                
                # Step 2: Click the first button (chess)
                if start_response.buttons:
                    await start_response.click(0)
                    game_response = await conv.get_response()
                    
                    # Step 3: Forward the actual game message
                    if game_response:
                        await user.forward_messages(
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
            error_msg = await event.respond(f"❌ Gagal: {str(e)}")
            await asyncio.sleep(5)
            await error_msg.delete()