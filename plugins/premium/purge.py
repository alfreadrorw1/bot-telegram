import asyncio
import time
import json
import os
from telethon import events
from config import OWNER_ID
from telethon.errors import MessageIdInvalidError, MessageNotModifiedError

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

async def delete_messages_in_chat(client, chat_id):
    """Delete all messages sent by me in a specific chat"""
    try:
        async for message in client.iter_messages(chat_id, from_user='me'):
            try:
                await message.delete()
                await asyncio.sleep(0.5)  # Increased delay to avoid flood
            except Exception:
                continue
    except Exception:
        pass

async def delete_all_chats(client):
    """Delete all messages in all chats (groups and PMs)"""
    try:
        async for dialog in client.iter_dialogs():
            try:
                await delete_messages_in_chat(client, dialog.id)
                await asyncio.sleep(1)  # Added delay between chats
            except Exception:
                continue
    except Exception:
        pass

async def delete_messages_with_text(client, chat_id, search_text):
    """Delete messages containing specific text"""
    try:
        async for message in client.iter_messages(chat_id, search=search_text, from_user='me'):
            try:
                await message.delete()
                await asyncio.sleep(0.5)
            except Exception:
                continue
    except Exception:
        pass

async def safe_edit_message(message, new_text):
    """Safely edit a message with error handling"""
    try:
        await message.edit(new_text)
    except (MessageIdInvalidError, MessageNotModifiedError):
        pass
    except Exception:
        pass

async def setup(bot, client, user_id):
    """Setup purge commands for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def purge_handler(event):
        """Handle purge commands"""
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
        if current_prefix:
            if not msg.startswith(current_prefix):
                return
            cmd_part = msg[len(current_prefix):].strip().lower()
        else:
            cmd_part = msg.lower()
        
        if not cmd_part.startswith("purge"):
            return

        args = cmd_part.split(maxsplit=2)
        chat_id = event.chat_id
        
        try:
            status = await event.reply("🚮 Memulai pembersihan pesan...")
            
            if len(args) == 1:
                # Basic purge command (current chat)
                await delete_messages_in_chat(client, chat_id)
                await safe_edit_message(status, "✅ Pembersihan pesan di chat ini selesai!")
            
            elif args[1] == "all":
                # Purge all chats
                await delete_all_chats(client)
                await safe_edit_message(status, "✅ Pembersihan SEMUA pesan selesai!")
            
            elif len(args) > 2:
                # Purge messages containing specific text
                search_text = args[2]
                await delete_messages_with_text(client, chat_id, search_text)
                await safe_edit_message(status, f"✅ Pembersihan pesan mengandung '{search_text}' selesai!")
            
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()
            
        except Exception as e:
            try:
                await event.reply(f"❌ Error: {str(e)}")
                await asyncio.sleep(5)
                await event.delete()
            except Exception:
                pass