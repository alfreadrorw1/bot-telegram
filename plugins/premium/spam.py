import asyncio
import os
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
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
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

async def setup(bot, user, user_id):
    """Setup spam commands for premium users"""
    current_user_id = user_id

    @user.on(events.NewMessage())
    async def spam_handler(event):
        """Handle all spam commands"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        msg = (event.text or '').strip()
        current_prefix = get_prefix(current_user_id)
        
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
            await safe_delete(event)
            
            if command == "cspam":
                status = await event.respond("<blockquote>🚀 Starting character spam...</blockquote>", parse_mode="html")
                for char in text:
                    await event.respond(char)
                    await asyncio.sleep(0.1)
                await safe_delete(status)
                    
            elif command == "wspam":
                status = await event.respond("<blockquote>🚀 Starting word spam...</blockquote>", parse_mode="html")
                for word in text:
                    await event.respond(word)
                    await asyncio.sleep(0.1)
                await safe_delete(status)
                    
            elif command == "spam":
                if len(parts) < 1:
                    status = await event.respond("<blockquote>❌ Usage: .spam &lt;count&gt; [text] or reply to media</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(status)
                    return
                
                try:
                    count = int(parts[0])
                except ValueError:
                    status = await event.respond("<blockquote>❌ Invalid count number</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(status)
                    return
                
                status = await event.respond(f"<blockquote>🚀 Starting spam ({count} messages)...</blockquote>", parse_mode="html")
                
                reply = await event.get_reply_message()
                if reply and reply.media and len(parts) == 1:
                    for i in range(count):
                        await user.send_file(event.chat_id, reply.media)
                        await asyncio.sleep(0.1)
                        if (i + 1) % 10 == 0:
                            await status.edit(f"<blockquote>🚀 Spamming... ({i+1}/{count})</blockquote>", parse_mode="html")
                elif len(parts) > 1:
                    for i in range(count):
                        await event.respond(parts[1])
                        await asyncio.sleep(0.1)
                        if (i + 1) % 10 == 0:
                            await status.edit(f"<blockquote>🚀 Spamming... ({i+1}/{count})</blockquote>", parse_mode="html")
                else:
                    await status.edit("<blockquote>❌ Usage: .spam &lt;count&gt; &lt;text&gt; or reply to media</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(status)
                    return
                
                await safe_delete(status)
                    
            elif command == "picspam":
                if len(parts) < 2:
                    status = await event.respond("<blockquote>❌ Usage: .picspam &lt;count&gt; &lt;url&gt;</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(status)
                    return
                
                try:
                    count = int(parts[0])
                except ValueError:
                    status = await event.respond("<blockquote>❌ Invalid count number</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(status)
                    return
                
                status = await event.respond(f"<blockquote>🚀 Starting picture spam ({count} images)...</blockquote>", parse_mode="html")
                
                for i in range(count):
                    await user.send_file(event.chat_id, parts[1])
                    await asyncio.sleep(0.1)
                    if (i + 1) % 10 == 0:
                        await status.edit(f"<blockquote>🚀 Picture spamming... ({i+1}/{count})</blockquote>", parse_mode="html")
                
                await safe_delete(status)
                    
            elif command == "delayspam":
                if len(parts) < 3:
                    status = await event.respond("<blockquote>❌ Usage: .delayspam &lt;delay&gt; &lt;count&gt; &lt;text&gt;</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(status)
                    return
                
                try:
                    delay = float(parts[0])
                    count = int(parts[1])
                except ValueError:
                    status = await event.respond("<blockquote>❌ Invalid delay or count</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(status)
                    return
                
                status = await event.respond(f"<blockquote>🚀 Starting delay spam ({count} messages, {delay}s delay)...</blockquote>", parse_mode="html")
                
                for i in range(count):
                    await event.respond(parts[2])
                    await asyncio.sleep(delay)
                    if (i + 1) % 10 == 0:
                        await status.edit(f"<blockquote>🚀 Delay spamming... ({i+1}/{count})</blockquote>", parse_mode="html")
                
                await safe_delete(status)
                    
        except Exception as e:
            error_msg = await event.respond(f"<blockquote>❌ Error: {str(e)[:200]}</blockquote>", parse_mode="html")
            await asyncio.sleep(5)
            await safe_delete(error_msg)