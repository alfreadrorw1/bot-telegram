import os
import json
import asyncio
from telethon import events, functions, types
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from config import OWNER_ID

def ensure_data_dir():
    if not os.path.exists('data'):
        os.makedirs('data')

def get_live_prefix():
    try:
        with open('data/prefix.json', 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_data_dir()
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def setup(bot, user):
    # ADMINLIST
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def adminlist_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}adminlist"):
                return
        else:
            if not msg.lower().startswith("adminlist"):
                return

        if not event.is_private:
            try:
                admins = await user.get_participants(event.chat_id, filter=types.ChannelParticipantsAdmins)
                admin_list = "╭──「 Admins 」\n"
                for admin in admins:
                    admin_list += f"│ • {admin.first_name} {admin.last_name or ''} ({admin.id})\n"
                admin_list += "╰──「 ᴀʟꜰʀᴇᴀᴅ  」"
                await event.edit(admin_list)
            except Exception as e:
                await event.edit(f"`❌ Error: {str(e)}`")
        else:
            await event.edit("`❌ Only works in groups/channels`")

    # ME (ACCOUNT INFO)
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def me_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}my"):
                return
        else:
            if not msg.lower().startswith("my"):
                return

        try:
            me = await user.get_me()
            full_name = f"{me.first_name} {me.last_name or ''}"
            username = f"@{me.username}" if me.username else "None"
            
            # Get bio reliably
            try:
                full_user = await user(functions.users.GetFullUserRequest(me))
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
            await event.edit(stats)
        except Exception as e:
            await event.edit(f"`❌ Error: {str(e)}`")

    # SET USERNAME
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def setuname_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}setuname"):
                return
            new_username = msg[len(current_prefix)+8:].strip().lower()
        else:
            if not msg.lower().startswith("setuname"):
                return
            new_username = msg[8:].strip().lower()

        if not new_username:
            await event.edit("`❌ Format: [prefix]setuname <new_username>`")
            return

        try:
            # Validate username
            if len(new_username) < 5 or len(new_username) > 32:
                raise ValueError("Username must be 5-32 characters")
            if not new_username.replace('_', '').isalnum():
                raise ValueError("Only a-z, 0-9 and underscores allowed")
            if new_username[0].isdigit():
                raise ValueError("Cannot start with number")
                
            await user(functions.account.UpdateUsernameRequest(username=new_username))
            await event.edit(f"`✅ Username changed to @{new_username}`")
        except Exception as e:
            error = str(e).replace("(caused by UpdateUsernameRequest)", "").strip()
            await event.edit(f"`❌ Failed to change username: {error}`")

    # REMOVE USERNAME
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def remuname_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}remuname"):
                return
        else:
            if not msg.lower().startswith("remuname"):
                return

        try:
            await user(functions.account.UpdateUsernameRequest(username=""))
            await event.edit("`✅ Username removed successfully`")
        except Exception as e:
            await event.edit(f"`❌ Failed to remove username: {str(e)}`")

    # SET BIO
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def setbio_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}setbio"):
                return
            new_bio = msg[len(current_prefix)+6:].strip()
        else:
            if not msg.lower().startswith("setbio"):
                return
            new_bio = msg[6:].strip()

        if not new_bio:
            await event.edit("`❌ Format: [prefix]setbio <new_bio>`")
            return

        try:
            await user(functions.account.UpdateProfileRequest(about=new_bio))
            await event.edit("`✅ Bio updated successfully`")
        except Exception as e:
            await event.edit(f"`❌ Failed to update bio: {str(e)}`")

    # SET NAME
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def setname_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}setname"):
                return
            name_parts = msg[len(current_prefix)+8:].strip().split(maxsplit=1)
        else:
            if not msg.lower().startswith("setname"):
                return
            name_parts = msg[7:].strip().split(maxsplit=1)

        if len(name_parts) < 2:
            await event.edit("`❌ Format: [prefix]setname <first_name> <last_name>`")
            return

        first_name, last_name = name_parts[0], name_parts[1]
        try:
            await user(functions.account.UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name
            ))
            await event.edit(f"`✅ Name changed to {first_name} {last_name}`")
        except Exception as e:
            await event.edit(f"`❌ Failed to change name: {str(e)}`")

    # SET PROFILE PICTURE
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def setpp_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}setpp"):
                return
        else:
            if not msg.lower().startswith("setpp"):
                return

        reply_msg = await event.get_reply_message()
        if reply_msg and reply_msg.photo:
            try:
                # Download photo
                photo = await reply_msg.download_media(file=bytes)
                
                # Upload new profile photo
                await user(UploadProfilePhotoRequest(
                    file=await user.upload_file(photo)
                ))
                await event.edit("`✅ Profile picture updated`")
            except Exception as e:
                await event.edit(f"`❌ Failed to update profile picture: {str(e)}`")
        else:
            await event.edit("`❌ Reply to a photo message`")

    # BLOCK USER
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def block_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}block"):
                return
            user_id = msg[len(current_prefix)+5:].strip()
        else:
            if not msg.lower().startswith("block"):
                return
            user_id = msg[5:].strip()

        reply_msg = await event.get_reply_message()
        if not user_id and reply_msg:
            user_id = str(reply_msg.sender_id)

        if not user_id:
            await event.edit("`❌ Format: [prefix]block <user_id> or reply`")
            return

        try:
            await user(functions.contacts.BlockRequest(id=int(user_id)))
            await event.edit(f"`✅ User {user_id} blocked`")
        except Exception as e:
            await event.edit(f"`❌ Failed to block user: {str(e)}`")

    # UNBLOCK USER
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def unblock_handler(event):
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}unblock"):
                return
            user_id = msg[len(current_prefix)+7:].strip()
        else:
            if not msg.lower().startswith("unblock"):
                return
            user_id = msg[7:].strip()

        reply_msg = await event.get_reply_message()
        if not user_id and reply_msg:
            user_id = str(reply_msg.sender_id)

        if not user_id:
            await event.edit("`❌ Format: [prefix]unblock <user_id> or reply`")
            return

        try:
            await user(functions.contacts.UnblockRequest(id=int(user_id)))
            await event.edit(f"`✅ User {user_id} unblocked`")
        except Exception as e:
            await event.edit(f"`❌ Failed to unblock user: {str(e)}`")

    