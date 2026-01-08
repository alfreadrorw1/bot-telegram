# plugins/premium/broadcast.py
import os
import json
import asyncio
import time
import random
from telethon import events, types
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.messages import SendMessageRequest, ForwardMessagesRequest
from config import OWNER_ID

# Add emoji mapping function
def get_emoji(emoji_type):
    """Get emoji based on type"""
    emoji_map = {
        'broadcast': '📢',
        'total': '📊',
        'sukses': '✅',
        'gagal': '❌',
        'task': '🆔',
        'user': '👤',
        'cancel': '🚫',
        'error': '⚠️'
    }
    return emoji_map.get(emoji_type, '➡️')

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

def get_blacklist_file(user_id=None):
    """Get blacklist file path based on user"""
    user_folder = get_user_folder(user_id)
    return f'{user_folder}/broadcast_blacklist.json'

def load_blacklist(user_id=None):
    """Load blacklist from JSON file"""
    blacklist_file = get_blacklist_file(user_id)
    try:
        with open(blacklist_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_blacklist(data, user_id=None):
    """Save blacklist to JSON file"""
    blacklist_file = get_blacklist_file(user_id)
    os.makedirs(os.path.dirname(blacklist_file), exist_ok=True)
    with open(blacklist_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_delay_file(user_id=None):
    """Get delay settings file path"""
    user_folder = get_user_folder(user_id)
    return f'{user_folder}/broadcast_delay.json'

def load_delay(user_id=None):
    """Load delay settings"""
    delay_file = get_delay_file(user_id)
    try:
        with open(delay_file, 'r') as f:
            return json.load(f).get('delay', 1)
    except (FileNotFoundError, json.JSONDecodeError):
        return 1

def save_delay(delay, user_id=None):
    """Save delay settings"""
    delay_file = get_delay_file(user_id)
    os.makedirs(os.path.dirname(delay_file), exist_ok=True)
    with open(delay_file, 'w') as f:
        json.dump({'delay': delay}, f, indent=4)

def get_failed_file(user_id=None):
    """Get failed broadcasts file path"""
    user_folder = get_user_folder(user_id)
    return f'{user_folder}/broadcast_failed.json'

def load_failed(user_id=None):
    """Load failed broadcasts"""
    failed_file = get_failed_file(user_id)
    try:
        with open(failed_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_failed(data, user_id=None):
    """Save failed broadcasts"""
    failed_file = get_failed_file(user_id)
    os.makedirs(os.path.dirname(failed_file), exist_ok=True)
    with open(failed_file, 'w') as f:
        json.dump(data, f, indent=4)

async def setup(bot, connect_user, user_id=None):
    current_user_id = user_id  # Store user_id in a local variable
    broadcast_delay = load_delay(current_user_id)  # Load user-specific delay
    
    # Store active broadcasts for cancellation
    active_broadcasts = {}
    failed_broadcasts = {}

    async def send_broadcast(event, content, reply, is_group=False):
        """Helper function to send broadcasts"""
        if not await connect_user.is_user_authorized():
            return await event.respond("<blockquote>❗ UserBot not connected!</blockquote>", parse_mode="html")

        success = 0
        failed = 0
        failed_list = []
        target_type = "groups" if is_group else "private chats"
        
        # Generate a unique task ID
        task_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Get owner name
        try:
            owner_entity = await connect_user.get_entity(OWNER_ID)
            owner_name = getattr(owner_entity, 'first_name', 'Owner')
        except:
            owner_name = "Owner"
        
        # Count total targets
        total_targets = 0
        blacklist = load_blacklist(event.sender_id if event.sender_id != OWNER_ID else None)
        
        async for dialog in connect_user.iter_dialogs():
            if dialog.id in blacklist:
                continue
            if is_group and not dialog.is_group:
                continue
            if not is_group and (not dialog.is_user or getattr(dialog.entity, 'bot', False) or dialog.id == OWNER_ID):
                continue
            total_targets += 1
        
        # Initial status message
        status_msg = await event.respond(
            f"<blockquote>{get_emoji('broadcast')} <b>Starting broadcast to {total_targets} {target_type}...</b></blockquote>",
            parse_mode="html"
        )
        
        # Store the broadcast task
        active_broadcasts[task_id] = {
            'status_msg': status_msg,
            'cancelled': False,
            'type': 'gcast' if is_group else 'ucast'
        }
        
        # Send broadcasts
        async for dialog in connect_user.iter_dialogs():
            if active_broadcasts[task_id]['cancelled']:
                break
                
            if dialog.id in blacklist:
                continue
                
            if is_group and not dialog.is_group:
                continue
            if not is_group and (not dialog.is_user or getattr(dialog.entity, 'bot', False) or dialog.id == OWNER_ID):
                continue
                    
            try:
                if reply:
                    # Copy the message instead of forwarding to preserve formatting
                    if reply.media:
                        # Handle media messages
                        await connect_user.send_file(
                            dialog.id, 
                            reply.media, 
                            caption=reply.text if reply.text else None,
                            parse_mode='html'
                        )
                    else:
                        # Handle text messages
                        await connect_user.send_message(
                            dialog.id, 
                            reply.text, 
                            parse_mode='html'
                        )
                else:
                    # Send text message directly
                    await connect_user.send_message(
                        dialog.id, 
                        content, 
                        parse_mode='html'
                    )
                
                success += 1
                await asyncio.sleep(broadcast_delay)
                
            except Exception as e:
                failed += 1
                failed_list.append({
                    'id': dialog.id,
                    'name': getattr(dialog.entity, 'title', getattr(dialog.entity, 'first_name', 'Unknown')),
                    'error': str(e)
                })
                # Add a small delay even on failure to avoid rate limiting
                await asyncio.sleep(0.5)
                continue
        
        # Remove from active broadcasts
        if task_id in active_broadcasts:
            del active_broadcasts[task_id]
        
        # Save failed broadcasts for later viewing
        if failed_list:
            failed_data = load_failed(event.sender_id if event.sender_id != OWNER_ID else None)
            failed_data[task_id] = {
                'timestamp': int(time.time()),
                'failed_list': failed_list,
                'type': 'gcast' if is_group else 'ucast'
            }
            save_failed(failed_data, event.sender_id if event.sender_id != OWNER_ID else None)
        
        # Final result message
        result = f"""
<blockquote>{get_emoji('broadcast')} <b>ᴛʏᴘᴇ: {'gcast' if is_group else 'ucast'}</b>
{get_emoji('total')} <b>ᴛᴏᴛᴀʟ: {total_targets}</b>
{get_emoji('sukses')} <b>sᴜᴋsᴇs: {success}</b>
{get_emoji('gagal')} <b>ɢᴀɢᴀʟ: {failed}</b>
{get_emoji('task')} <b>ᴛᴀsᴋ ɪᴅ:</b> <code>{task_id}</code>
{get_emoji('user')} <b>ᴏᴡɴᴇʀ:</b> <a href='tg://user?id={OWNER_ID}'>{owner_name}</a>

<code>.bc-error {task_id}</code> <b>to view the failed!</b></blockquote>
"""
        await status_msg.edit(result, parse_mode="html")

    @connect_user.on(events.NewMessage())
    async def broadcast_handler(event):
        """Handle broadcast commands"""
        # Check if user is owner or premium with active session
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id)
        )
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.raw_text or '').strip()
        
        # Check for broadcast commands
        if not message.startswith(current_prefix):
            return

        cmd = message[len(current_prefix):].strip().lower()
        
        # GCAST command
        if cmd.startswith("gcast"):
            reply = await event.get_reply_message()
            content = message[len(current_prefix)+5:].strip()
            
            if not content and not reply:
                return await event.respond("<blockquote>❌ Reply to a message or include text</blockquote>", parse_mode="html")
            
            await send_broadcast(event, content, reply, is_group=True)
        
        # UCAST command
        elif cmd.startswith("ucast"):
            reply = await event.get_reply_message()
            content = message[len(current_prefix)+5:].strip()
            
            if not content and not reply:
                return await event.respond("<blockquote>❌ Reply to a message or include text</blockquote>", parse_mode="html")
            
            await send_broadcast(event, content, reply, is_group=False)
        
        # BCAST CANCEL command
        elif cmd.startswith("bc-cancel"):
            parts = cmd.split()
            if len(parts) > 1:
                task_id = parts[1]
                if task_id in active_broadcasts:
                    active_broadcasts[task_id]['cancelled'] = True
                    await event.respond(f"<blockquote>{get_emoji('cancel')} <b>Broadcast task {task_id} cancelled!</b></blockquote>", parse_mode="html")
                else:
                    await event.respond("<blockquote>❌ Task ID not found or already completed</blockquote>", parse_mode="html")
            else:
                await event.respond("<blockquote>❌ Please specify task ID: bc-cancel [task_id]</blockquote>", parse_mode="html")
        
        # BC-ERROR command
        elif cmd.startswith("bc-error"):
            parts = cmd.split()
            if len(parts) > 1:
                task_id = parts[1]
                failed_data = load_failed(sender_id if sender_id != OWNER_ID else None)
                
                if task_id in failed_data:
                    failed_list = failed_data[task_id]['failed_list']
                    message = f"<blockquote>{get_emoji('error')} <b>Failed broadcasts for task {task_id}</b></blockquote>\n\n"
                    
                    for i, failed_item in enumerate(failed_list[:10], 1):  # Show first 10 failures
                        message += f"<blockquote>{i}. {failed_item['name']} (<code>{failed_item['id']}</code>)\nError: {failed_item['error'][:50]}...</blockquote>\n"
                    
                    if len(failed_list) > 10:
                        message += f"<blockquote>... and {len(failed_list) - 10} more failures</blockquote>"
                    
                    await event.respond(message, parse_mode="html")
                else:
                    await event.respond("<blockquote>❌ No failed broadcasts found for this task ID</blockquote>", parse_mode="html")
            else:
                await event.respond("<blockquote>❌ Please specify task ID: bc-error [task_id]</blockquote>", parse_mode="html")
        
        # SETDELAY command
        elif cmd.startswith("setdelay"):
            try:
                parts = cmd.split()
                new_delay = int(parts[1]) if len(parts) > 1 else 1
                if new_delay < 1:
                    new_delay = 1
                nonlocal broadcast_delay
                broadcast_delay = new_delay
                save_delay(broadcast_delay, current_user_id)  # Save delay for current user
                await event.respond(
                    f"<blockquote>⏱ Broadcast delay set to: {broadcast_delay} seconds</blockquote>",
                    parse_mode="html"
                )
            except:
                await event.respond("<blockquote>❌ Invalid delay format! Use: setdelay [number]</blockquote>", parse_mode="html")
        
        # ADDBL command
        elif cmd.startswith("addbl"):
            chat_id = event.chat_id
            # Load the appropriate blacklist based on who's sending the command
            blacklist = load_blacklist(sender_id if sender_id != OWNER_ID else None)
            
            if chat_id in blacklist:
                return await event.respond("<blockquote>⚠️ Chat already in blacklist</blockquote>", parse_mode="html")
            
            blacklist.append(chat_id)
            save_blacklist(blacklist, sender_id if sender_id != OWNER_ID else None)
            
            try:
                entity = await connect_user.get_entity(chat_id)
                name = getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
            except:
                name = "Unknown"
                
            await event.respond(
                f"<blockquote>✅ Added to blacklist:</blockquote>\n"
                f"<blockquote>• Name: {name}\n"
                f"• ID: {chat_id}</blockquote>",
                parse_mode="html"
            )
        
        # DELBL command
        elif cmd.startswith("delbl"):
            chat_id = event.chat_id
            # Load the appropriate blacklist based on who's sending the command
            blacklist = load_blacklist(sender_id if sender_id != OWNER_ID else None)
            
            if chat_id not in blacklist:
                return await event.respond("<blockquote>⚠️ Chat not found in blacklist</blockquote>", parse_mode="html")
            
            blacklist.remove(chat_id)
            save_blacklist(blacklist, sender_id if sender_id != OWNER_ID else None)
            
            try:
                entity = await connect_user.get_entity(chat_id)
                name = getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
            except:
                name = "Unknown"
                
            await event.respond(
                f"<blockquote>✅ Removed from blacklist:</blockquote>\n"
                f"<blockquote>• Name: {name}\n"
                f"• ID: {chat_id}</blockquote>",
                parse_mode="html"
            )
        
        # LISTBL command (owner can view any user's blacklist)
        elif cmd.startswith("listbl"):
            target_user = None
            parts = cmd.split()
            
            # Owner can specify which user's blacklist to view
            if sender_id == OWNER_ID and len(parts) > 1:
                try:
                    target_user = int(parts[1])
                    if not is_premium_user(target_user):
                        return await event.respond("<blockquote>❌ User is not premium</blockquote>", parse_mode="html")
                except:
                    return await event.respond("<blockquote>❌ Invalid user ID format</blockquote>", parse_mode="html")
            
            # Load the appropriate blacklist
            blacklist = load_blacklist(target_user if target_user else (sender_id if sender_id != OWNER_ID else None))
            
            if not blacklist:
                user_info = f" (User ID: {target_user})" if target_user else ""
                return await event.respond(f"<blockquote>📭 Blacklist is empty{user_info}</blockquote>", parse_mode="html")

            groups = []
            users = []
            
            for chat_id in blacklist:
                try:
                    entity = await connect_user.get_entity(chat_id)
                    if isinstance(entity, (Channel, Chat)):
                        groups.append((chat_id, getattr(entity, 'title', 'Unknown Group')))
                    else:
                        users.append((chat_id, getattr(entity, 'first_name', 'Unknown User')))
                except:
                    if isinstance(chat_id, int) and chat_id > 0:
                        users.append((chat_id, "Unknown User"))
                    else:
                        groups.append((chat_id, "Unknown Group"))

            user_info = f" (User ID: {target_user})" if target_user else ""
            message = f"<blockquote>📋 Blacklist{user_info}</blockquote>\n"
            
            if users:
                message += "\n<blockquote>👤 Private Chats:</blockquote>\n"
                for idx, (user_id, name) in enumerate(users, 1):
                    message += f"{idx}. {name} (<code>{user_id}</code>)\n"
            
            if groups:
                message += "\n<blockquote>👥 Groups/Channels:</blockquote>\n"
                for idx, (group_id, name) in enumerate(groups, 1):
                    message += f"{idx}. {name} (<code>{group_id}</code>)\n"

            await event.respond(message, parse_mode="html")
        
        # BCHELP command
        elif cmd.startswith("bchelp"):
            help_text = (
                "<blockquote>📢 Broadcast Guide</blockquote>\n\n"
                "<blockquote>• Broadcast Commands:</blockquote>\n"
                f"{current_prefix}gcast [message/reply] - Broadcast to all groups\n"
                f"{current_prefix}ucast [message/reply] - Broadcast to all private chats\n\n"
                "<blockquote>• Settings:</blockquote>\n"
                f"{current_prefix}setdelay [seconds] - Set broadcast delay\n"
                f"{current_prefix}addbl - Add chat/group to blacklist\n"
                f"{current_prefix}delbl - Remove chat/group from blacklist\n"
                f"{current_prefix}listbl [user_id] - View blacklist (owner can specify user)\n\n"
                "<blockquote>• Task Management:</blockquote>\n"
                f"{current_prefix}bc-cancel [task_id] - Cancel a running broadcast\n"
                f"{current_prefix}bc-error [task_id] - View failed broadcasts for a task"
            )
            await event.respond(help_text, parse_mode="html")