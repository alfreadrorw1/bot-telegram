import asyncio
import os
import json
from telethon import events
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

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
    async def spam_handler(event):
        """Handle all spam commands"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Determine command type
        command = None
        if current_prefix:
            if msg.startswith(f"{current_prefix}cspam "):
                command = "cspam"
                text = msg[len(current_prefix)+6:].replace(" ", "")
            elif msg.startswith(f"{current_prefix}wspam "):
                command = "wspam"
                text = msg[len(current_prefix)+6:].split()
            elif msg.startswith(f"{current_prefix}spam "):
                command = "spam"
                parts = msg[len(current_prefix)+5:].split(maxsplit=1)
            elif msg.startswith(f"{current_prefix}picspam "):
                command = "picspam"
                parts = msg[len(current_prefix)+8:].split(maxsplit=1)
            elif msg.startswith(f"{current_prefix}delayspam "):
                command = "delayspam"
                parts = msg[len(current_prefix)+10:].split(maxsplit=2)
        else:
            if msg.lower().startswith("cspam "):
                command = "cspam"
                text = msg[6:].replace(" ", "")
            elif msg.lower().startswith("wspam "):
                command = "wspam"
                text = msg[6:].split()
            elif msg.lower().startswith("spam "):
                command = "spam"
                parts = msg[5:].split(maxsplit=1)
            elif msg.lower().startswith("picspam "):
                command = "picspam"
                parts = msg[8:].split(maxsplit=1)
            elif msg.lower().startswith("delayspam "):
                command = "delayspam"
                parts = msg[10:].split(maxsplit=2)
                
        if not command:
            return
            
        try:
            await event.delete()
            
            if command == "cspam":
                for char in text:
                    await event.respond(char)
                    await asyncio.sleep(0.1)
                    
            elif command == "wspam":
                for word in text:
                    await event.respond(word)
                    await asyncio.sleep(0.1)
                    
            elif command == "spam":
                if len(parts) < 1:
                    return await event.respond("```Usage: .spam <count> [text] or reply to media```")
                
                try:
                    count = int(parts[0])
                except ValueError:
                    return await event.respond("```Invalid count number```")
                
                reply = await event.get_reply_message()
                if reply and reply.media and len(parts) == 1:
                    for _ in range(count):
                        await user.send_file(event.chat_id, reply.media)
                        await asyncio.sleep(0.1)
                elif len(parts) > 1:
                    for _ in range(count):
                        await event.respond(parts[1])
                        await asyncio.sleep(0.1)
                else:
                    await event.respond("```Usage: .spam <count> <text> or reply to media```")
                    
            elif command == "picspam":
                if len(parts) < 2:
                    return await event.respond("```Usage: .picspam <count> <url>```")
                
                try:
                    count = int(parts[0])
                except ValueError:
                    return await event.respond("```Invalid count number```")
                
                for _ in range(count):
                    await user.send_file(event.chat_id, parts[1])
                    await asyncio.sleep(0.1)
                    
            elif command == "delayspam":
                if len(parts) < 3:
                    return await event.respond("```Usage: .delayspam <delay> <count> <text>```")
                
                try:
                    delay = float(parts[0])
                    count = int(parts[1])
                except ValueError:
                    return await event.respond("```Invalid delay or count```")
                
                for _ in range(count):
                    await event.respond(parts[2])
                    await asyncio.sleep(delay)
                    
        except Exception as e:
            await event.respond(f"```Error: {str(e)[:200]}```")