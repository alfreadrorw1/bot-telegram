# plugins/premium/profile.py
import os
import json
import asyncio
from telethon import events, functions, types
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
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

async def safe_edit(event, text):
    """Safely edit a message or send a new one if editing fails"""
    try:
        if event.out:
            await event.edit(text)
        else:
            await event.reply(text)
            try:
                await event.delete()
            except:
                pass
    except Exception as e:
        await event.reply(f"Error: {str(e)}")

async def setup(bot, client, user_id=None):
    """Setup profile management commands for premium users"""
    current_user_id = user_id

    async def check_auth(event):
        """Check if user is authorized to use the command"""
        sender_id = event.sender_id
        return (sender_id == OWNER_ID or 
               (is_premium_user(sender_id) and current_user_id == sender_id))

    # ADMINLIST
    @client.on(events.NewMessage())
    async def adminlist_handler(event):
        """Handle adminlist command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "adminlist"):
                return
        elif not msg.lower().startswith("adminlist"):
            return

        if not event.is_private:
            try:
                admins = await client.get_participants(event.chat_id, filter=types.ChannelParticipantsAdmins)
                admin_list = "╭──「 Admins 」\n"
                for admin in admins:
                    admin_list += f"│ • {admin.first_name} {admin.last_name or ''} ({admin.id})\n"
                admin_list += "╰──「 ᴀʟꜰʀᴇᴀᴅ  」"
                await safe_edit(event, admin_list)
            except Exception as e:
                await safe_edit(event, f"`❌ Error: {str(e)}`")
        else:
            await safe_edit(event, "`❌ Only works in groups/channels`")

    # ME (ACCOUNT INFO)
    @client.on(events.NewMessage())
    async def me_handler(event):
        """Handle my command (account info)"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "my"):
                return
        elif not msg.lower().startswith("my"):
            return

        try:
            me = await client.get_me()
            full_name = f"{me.first_name} {me.last_name or ''}"
            username = f"@{me.username}" if me.username else "None"
            
            try:
                full_user = await client(functions.users.GetFullUserRequest(me))
                bio = full_user.about or "None"
            except:
                bio = "None"
            
            stats = (
                f"╭──「 Profile 」\n"
                f"│ • Name: {full_name}\n"
                f"│ • ID: {me.id}\n"
                f"│ • Username: {username}\n"
                f"│ • Bio: {bio}\n"
                f"│ • Premium: {'Yes' if me.premium else 'No'}\n"
                f"│ • Verified: {'Yes' if me.verified else 'No'}\n"
                f"│ • Restricted: {'Yes' if me.restricted else 'No'}\n"
                f"╰──「 ᴀʟꜰʀᴇᴀᴅ  」"
            )
            await safe_edit(event, stats)
        except Exception as e:
            await safe_edit(event, f"`❌ Error: {str(e)}`")

    # SET USERNAME
    @client.on(events.NewMessage())
    async def setuname_handler(event):
        """Handle setuname command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "setuname"):
                return
            new_username = msg[len(current_prefix)+8:].strip().lower()
        elif not msg.lower().startswith("setuname"):
            return
        else:
            new_username = msg[8:].strip().lower()

        if not new_username:
            await safe_edit(event, "`❌ Format: [prefix]setuname <new_username>`")
            return

        try:
            if len(new_username) < 5 or len(new_username) > 32:
                raise ValueError("Username must be 5-32 characters")
            if not new_username.replace('_', '').isalnum():
                raise ValueError("Only a-z, 0-9 and underscores allowed")
            if new_username[0].isdigit():
                raise ValueError("Cannot start with number")
                
            await client(functions.account.UpdateUsernameRequest(username=new_username))
            await safe_edit(event, f"`✅ Username changed to @{new_username}`")
        except Exception as e:
            error = str(e).replace("(caused by UpdateUsernameRequest)", "").strip()
            await safe_edit(event, f"`❌ Failed to change username: {error}`")

    # REMOVE USERNAME
    @client.on(events.NewMessage())
    async def remuname_handler(event):
        """Handle remuname command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "remuname"):
                return
        elif not msg.lower().startswith("remuname"):
            return

        try:
            await client(functions.account.UpdateUsernameRequest(username=""))
            await safe_edit(event, "`✅ Username removed successfully`")
        except Exception as e:
            await safe_edit(event, f"`❌ Failed to remove username: {str(e)}`")

    # SET BIO
    @client.on(events.NewMessage())
    async def setbio_handler(event):
        """Handle setbio command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "setbio"):
                return
            new_bio = msg[len(current_prefix)+6:].strip()
        elif not msg.lower().startswith("setbio"):
            return
        else:
            new_bio = msg[6:].strip()

        if not new_bio:
            await safe_edit(event, "`❌ Format: [prefix]setbio <new_bio>`")
            return

        try:
            await client(functions.account.UpdateProfileRequest(about=new_bio))
            await safe_edit(event, "`✅ Bio updated successfully`")
        except Exception as e:
            await safe_edit(event, f"`❌ Failed to update bio: {str(e)}`")

    # SET NAME
    @client.on(events.NewMessage())
    async def setname_handler(event):
        """Handle setname command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "setname"):
                return
            name_parts = msg[len(current_prefix)+8:].strip().split(maxsplit=1)
        elif not msg.lower().startswith("setname"):
            return
        else:
            name_parts = msg[7:].strip().split(maxsplit=1)

        if len(name_parts) < 2:
            await safe_edit(event, "`❌ Format: [prefix]setname <first_name> <last_name>`")
            return

        first_name, last_name = name_parts[0], name_parts[1]
        try:
            await client(functions.account.UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name
            ))
            await safe_edit(event, f"`✅ Name changed to {first_name} {last_name}`")
        except Exception as e:
            await safe_edit(event, f"`❌ Failed to change name: {str(e)}`")

    # SET PROFILE PICTURE
    @client.on(events.NewMessage())
    async def setpp_handler(event):
        """Handle setpp command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "setpp"):
                return
        elif not msg.lower().startswith("setpp"):
            return

        reply_msg = await event.get_reply_message()
        if reply_msg and reply_msg.photo:
            try:
                photo = await reply_msg.download_media(file=bytes)
                await client(UploadProfilePhotoRequest(
                    file=await client.upload_file(photo)
                ))
                await safe_edit(event, "`✅ Profile picture updated`")
            except Exception as e:
                await safe_edit(event, f"`❌ Failed to update profile picture: {str(e)}`")
        else:
            await safe_edit(event, "`❌ Reply to a photo message`")

   