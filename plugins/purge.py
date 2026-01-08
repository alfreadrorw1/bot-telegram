# plugins/purge.py
import asyncio
import time
import json
import os
from telethon import events
from config import OWNER_ID

def get_prefix():
    """Get current prefix from config (supports 'no' prefix mode)"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def delete_messages_in_chat(client, chat_id):
    """Delete all messages sent by me in a specific chat"""
    try:
        # Get all messages in the chat
        async for message in client.iter_messages(chat_id, from_user='me'):
            try:
                await message.delete()
                await asyncio.sleep(0.2)  # Add delay to avoid flood limits
            except Exception as e:
                print(f"Error deleting message {message.id}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error iterating messages: {str(e)}")

def setup(bot, user):
    @user.on(events.NewMessage())
    async def purge_handler(event):
        # Only allow the owner to use this command
        if event.sender_id != OWNER_ID:
            return

        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        # Check if message is a purge command
        is_purge = (
            (current_prefix == "no" and message == "purge") or
            (message.startswith(current_prefix.lower()) and 
             "purge" in message[len(current_prefix):].strip())
        )
        
        if not is_purge:
            return

        # Get the chat where the command was sent
        chat_id = event.chat_id
        
        try:
            # Delete all messages in this chat
            await delete_messages_in_chat(user, chat_id)

        except Exception as e:
            await event.reply(f"❌ Error during purge: {str(e)}")