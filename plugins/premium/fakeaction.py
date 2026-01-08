# plugins/fakeaction.py
import re
import asyncio
import json
import os
from telethon import events
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import (
    SendMessageUploadVideoAction,
    SendMessageUploadAudioAction,
    SendMessageUploadPhotoAction,
    SendMessageUploadDocumentAction
)
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

async def setup(bot, client, user_id):
    """Setup fake action commands for premium users"""
    current_user_id = user_id
    active_actions = {}

    @client.on(events.NewMessage())
    async def fake_action_handler(event):
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        # Get current prefix and message
        current_prefix = get_prefix(current_user_id)
        message = (event.text or '').strip()
        
        # Check if message matches the fake action pattern
        pattern = (
            r'^fake\s+(\d+)?\s?(video|audio|photo|file|cancel)$' if not current_prefix else
            rf'^{re.escape(current_prefix)}fake\s+(\d+)?\s?(video|audio|photo|file|cancel)$'
        )
        
        match = re.match(pattern, message, re.IGNORECASE)
        if not match:
            return

        # Extract action type and duration
        duration_str = match.group(1)
        action_type = match.group(2).lower()
        
        try:
            duration = int(duration_str) if duration_str else 1
            if duration < 1 or duration > 120:  # Limit to 2 hours max (120 minutes)
                duration = 1
        except ValueError:
            duration = 1

        # Action mapping
        action_map = {
            'video': SendMessageUploadVideoAction(progress=0),
            'audio': SendMessageUploadAudioAction(progress=0),
            'photo': SendMessageUploadPhotoAction(progress=0),
            'file': SendMessageUploadDocumentAction(progress=0),
            'cancel': 'cancel'
        }

        action = action_map.get(action_type)
        if action is None:
            return

        chat_id = event.chat_id

        if action == 'cancel':
            if chat_id in active_actions:
                active_actions[chat_id].cancel()
                del active_actions[chat_id]
            await event.delete()
            return

        async def simulate_action():
            try:
                total_seconds = duration * 60  # Convert minutes to seconds
                start_time = asyncio.get_event_loop().time()
                
                while (asyncio.get_event_loop().time() - start_time) < total_seconds:
                    progress = min((asyncio.get_event_loop().time() - start_time) / total_seconds, 1.0)
                    progress_percent = int(progress * 100)
                    
                    updated_action = action.__class__(progress=progress_percent)
                    await client(SetTypingRequest(chat_id, updated_action))
                    await asyncio.sleep(2.5)
                
                # Delete the command message after action completes
                await event.delete()
            except Exception as e:
                error_msg = await event.reply(f"<blockquote>⚠️ Error: {str(e)[:200]}</blockquote>", parse_mode="html")
                await asyncio.sleep(3)
                await error_msg.delete()
            finally:
                if chat_id in active_actions:
                    del active_actions[chat_id]

        if chat_id in active_actions:
            reply = await event.reply("<blockquote>⚠️ Harap batalkan action sebelumnya!</blockquote>", parse_mode="html")
            await asyncio.sleep(0.3)
            await event.delete()
            await reply.delete()
        else:
            task = asyncio.create_task(simulate_action())
            active_actions[chat_id] = task
            await asyncio.sleep(0.1)
            await event.delete()