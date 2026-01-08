import os
import json
import asyncio
import time
from telethon import events, types
from telethon.tl.types import ChannelParticipantsBanned
from telethon.errors import FloodWaitError
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
    async def unmuteall_handler(event):
        """Handle unmuteall command"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_unmute_cmd = False
        
        if current_prefix:
            if msg == f"{current_prefix}unmuteall":
                is_unmute_cmd = True
        else:
            if msg.lower() == "unmuteall":
                is_unmute_cmd = True
                
        if not is_unmute_cmd:
            return

        # Validate chat type
        if event.is_private:
            await event.reply("```❌ Perintah ini hanya untuk grup/supergrup```")
            return

        try:
            # Get chat object
            chat = await event.get_chat()
            
            # Check chat type
            if not isinstance(chat, (types.Chat, types.Channel)):
                await event.reply("```❌ Perintah hanya untuk grup/supergrup```")
                return

            # Check admin permissions
            is_admin = False
            if isinstance(chat, types.Channel):
                if chat.admin_rights:
                    is_admin = chat.admin_rights.ban_users
            else:
                is_admin = chat.admin

            if not is_admin:
                await event.reply("```❌ Bot harus admin dengan izin Ban Users```")
                return

            # Confirmation system
            confirm_msg = await event.reply(
                "```⚠️ PERINGATAN! Ini akan unmute SEMUA member```\n"
                "```Balas dengan 'CONFIRM_UNMUTE_ALL' untuk melanjutkan```"
            )

            # Wait for confirmation
            future = asyncio.Future()
            
            def check_confirmation(e):
                if (e.sender_id == event.sender_id 
                    and e.text == "CONFIRM_UNMUTE_ALL"
                    and e.is_reply 
                    and e.reply_to_msg_id == confirm_msg.id):
                    future.set_result(True)
                    return True
                return False

            user.add_event_handler(
                check_confirmation,
                events.NewMessage(incoming=True, from_users=event.sender_id)
            )

            try:
                await asyncio.wait_for(future, timeout=30)
            except asyncio.TimeoutError:
                await confirm_msg.edit("```❌ Waktu konfirmasi habis```")
                return
            finally:
                user.remove_event_handler(check_confirmation)

            # Start unmute process
            start_time = time.time()
            status_msg = await event.reply("```🔄 Memulai proses unmute...```")
            
            total_unmuted = 0
            async for member in user.iter_participants(
                event.chat_id,
                filter=ChannelParticipantsBanned,
                aggressive=True
            ):
                try:
                    await user.edit_permissions(
                        event.chat_id,
                        member.id,
                        view_messages=True,
                        send_messages=True,
                        send_media=True,
                        send_stickers=True,
                        send_gifs=True,
                        send_games=True,
                        send_inline=True
                    )
                    total_unmuted += 1
                    await asyncio.sleep(2)  # Rate limiting
                except FloodWaitError as e:
                    await status_msg.edit(f"```⏳ Menunggu {e.seconds} detik karena flood limit```")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    continue

            # Final report
            duration = time.time() - start_time
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            await event.reply(
                f"```✅ Selesai!```\n"
                f"```• Total di-unmute: {total_unmuted}```\n"
                f"```• Durasi: {minutes}m {seconds}s```"
            )

        except Exception as e:
            error_msg = str(e)[:200]  # Limit error message length
            await event.reply(f"```❌ Error: {error_msg}```")
        finally:
            try:
                await confirm_msg.delete()
                await status_msg.delete()
            except:
                pass
            await event.delete()