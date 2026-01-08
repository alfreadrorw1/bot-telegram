import os
import json
from datetime import datetime
from telethon import events, functions
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import (
    UserStatusOnline, UserStatusOffline, UserStatusRecently,
    UserStatusLastWeek, UserStatusLastMonth,
    ChannelParticipantCreator, ChannelParticipantAdmin,
    ChannelParticipantBanned
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

async def setup(bot, connect_user, user_id=None):
    """Setup info command for premium users"""
    
    @connect_user.on(events.NewMessage())
    async def info_handler(event):
        """Handle info command"""
        # Check authorization
        sender_id = event.sender_id
        current_prefix = get_prefix(sender_id)
        msg = (event.text or '').strip()
        
        # Check command format
        is_info_cmd = (
            (current_prefix == "no" and (msg.lower() == "info" or msg.lower().startswith("info "))) or
            (msg.lower().startswith(f"{current_prefix}info"))
        )
        
        if not is_info_cmd:
            return
            
        # Check authorization
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and sender_id == user_id)
        )
        
        if not is_authorized:
            return

        # Extract target from command
        if current_prefix == "no":
            target = msg[4:].strip()
        else:
            target = msg[len(current_prefix)+4:].strip()

        # Get target user
        try:
            if target:
                try:
                    # Try to parse as user ID first
                    user_id = int(target)
                    user_entity = await connect_user.get_entity(user_id)
                except ValueError:
                    # Try as username/phone
                    user_entity = await connect_user.get_entity(target)
            else:
                reply = await event.get_reply_message()
                if not reply:
                    await event.reply("```Reply to a message or provide username/ID```")
                    return
                user_entity = await connect_user.get_entity(reply.sender_id)
        except Exception as e:
            await event.reply(f"```Couldn't find user: {str(e)}```")
            return

        # Get full user info
        try:
            full = await connect_user(GetFullUserRequest(user_entity.id))
            full_user = full.full_user
        except Exception as e:
            await event.reply(f"```Couldn't get full info: {str(e)}```")
            return

        # Get common chats count
        try:
            common = await connect_user(functions.messages.GetCommonChatsRequest(
                user_id=user_entity.id,
                max_id=0,
                limit=1
            ))
            common_chats = len(common.chats)
        except:
            common_chats = 0

        # Prepare info lines
        info_lines = [
            "**🔍 User Information**",
            f"**First Name:** `{escape_markdown(user_entity.first_name or 'None')}`",
            f"**Last Name:** `{escape_markdown(user_entity.last_name or 'None')}`",
            f"**User ID:** `{user_entity.id}`",
            f"**Username:** @{user_entity.username}" if user_entity.username else "**Username:** `None`",
            f"**Phone:** `{user_entity.phone or 'Hidden'}`",
            f"**Bio:** `{escape_markdown(getattr(full_user, 'about', 'None'))}`",
            "",
            "**📌 Account Details**",
            f"**Profile Photo:** `{'Yes' if user_entity.photo else 'No'}`",
            f"**Mutual Chats:** `{common_chats}+`",
            f"**Bot:** `{'Yes' if user_entity.bot else 'No'}`",
            f"**Verified:** `{'Yes' if user_entity.verified else 'No'}`",
            f"**Scam:** `{'Yes' if user_entity.scam else 'No'}`",
            f"**Support:** `{'Yes' if user_entity.support else 'No'}`",
            f"**Premium:** `{'Yes' if user_entity.premium else 'No'}`",
        ]

        # Add status info
        status = user_entity.status
        if isinstance(status, UserStatusOnline):
            status_str = "🟢 Online"
        elif isinstance(status, UserStatusRecently):
            status_str = "🟡 Recently"
        elif isinstance(status, UserStatusLastWeek):
            status_str = "🟠 Last week"
        elif isinstance(status, UserStatusLastMonth):
            status_str = "🔴 Last month"
        elif isinstance(status, UserStatusOffline):
            was = datetime.fromtimestamp(status.was_online)
            status_str = f"⚫ Last online {was.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            status_str = "⚪ Unknown status"
        info_lines.append(f"**Status:** {status_str}")

        # Add DC info if available
        if hasattr(user_entity, 'photo') and user_entity.photo:
            info_lines.append(f"**DC ID:** `{user_entity.photo.dc_id}`")

        # Add group role if in group
        if event.is_group:
            try:
                part = await connect_user(GetParticipantRequest(event.chat_id, user_entity.id))
                p = part.participant
                if isinstance(p, ChannelParticipantCreator):
                    role = "👑 Creator"
                elif isinstance(p, ChannelParticipantAdmin):
                    role = "🛡️ Admin"
                    if p.admin_rights.anonymous:
                        role += " (Anonymous)"
                elif isinstance(p, ChannelParticipantBanned):
                    role = "🚫 Banned"
                else:
                    role = "👤 Member"
                info_lines.append(f"**Group Role:** {role}")
            except:
                pass
       
def escape_markdown(text):
    """Helper function to escape markdown special characters"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)