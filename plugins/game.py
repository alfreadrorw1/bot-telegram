import os
import json
import asyncio
from telethon import events
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
GAME_BOT = "@gamee"

# Game database
GAME_DB = {
    "1": "Skipper",
    "2": "Space Orbit",
    "3": "Karate Kido",
    "4": "Gravity Ninja",
    "5": "Basket Boy",
    "6": "SmartUp Shark",
    "7": "Basket Boy Rush",
    "8": "Mars Rover",
    "9": "Spiky Fish 3",
    "10": "Little Plane",
    "11": "Neon Racer",
    "12": "Beach Racer",
    "13": "MotoFX 2",
    "14": "F1 Racer",
    "15": "MotoFX",
    "16": "Neon Blaster",
    "17": "Space Traveler",
    "18": "Red and Blue",
    "19": "Tube Runner",
    "20": "Gravity Unicorns",
    "21": "Gravity Ninja 2",
    "22": "Moonshot",
    "23": "Globon Run",
    "24": "Hooked 2048",
    "25": "Color Hit",
}

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def game_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format (handles "game1", "game 1", etc.)
        is_game_cmd = False
        game_key = ""
        
        # Remove prefix if exists
        if current_prefix and msg.startswith(current_prefix):
            msg = msg[len(current_prefix):].strip()
        
        if msg.lower().startswith("game"):
            is_game_cmd = True
            game_key = msg[4:].strip()  # Get everything after "game"
        
        if not is_game_cmd:
            return

        # Clean game key (remove spaces)
        game_key = game_key.replace(" ", "")
        
        # Check if game exists
        game_name = GAME_DB.get(game_key)
        if not game_key or not game_name:
            # Show available games
            games_list = "\n".join([f"<b>{k}</b> - {v}" for k,v in GAME_DB.items()])
            status = await event.reply(
                "<blockquote>"
                "🚫 <b>Game tidak ditemukan!</b>\n\n"
                "🎮 <b>Game yang tersedia:</b>\n"
                f"{games_list}"
                "</blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(10)
            await status.delete()
            await event.delete()
            return

        # Send processing status
        status = await event.reply(
            f"<blockquote>🔄 <b>Memulai {game_name}...</b> (Mohon tunggu)</blockquote>",
            parse_mode="html"
        )
        
        try:
            # Clear any previous messages with the bot
            await user.send_read_acknowledge(GAME_BOT)
            
            # Send game command to @gamee
            await user.send_message(GAME_BOT, f"► {game_name}")
            
            # Wait for and capture the game response
            response = None
            attempts = 0
            while attempts < 5:  # Try for 5 seconds max
                async for message in user.iter_messages(GAME_BOT, limit=1):
                    if not message.out and message.text != f"► {game_name}":
                        response = message
                        break
                
                if response:
                    break
                    
                attempts += 1
                await asyncio.sleep(1)  # Wait 1 second between checks
            
            if response:
                await response.forward_to(event.chat_id)
            else:
                await event.reply(
                    "<blockquote>"
                    f"❌ <b>Gagal memulai {game_name}</b>\n\n"
                    "Coba lagi atau pilih game lain"
                    "</blockquote>",
                    parse_mode="html"
                )
            
        except Exception as e:
            await event.reply(
                f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>",
                parse_mode="html"
            )
        finally:
            await status.delete()
            await event.delete()