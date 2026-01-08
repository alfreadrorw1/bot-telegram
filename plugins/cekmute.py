from telethon import events
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsBanned
from config import OWNER_ID
import asyncio
import math
import time
import json
import os

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
COOLDOWN_FILE = os.path.join(CONFIG_DIR, 'cekmute_cooldown.json')

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

def get_cooldown():
    """Get last command execution time"""
    try:
        with open(COOLDOWN_FILE, 'r') as f:
            return json.load(f).get('last_time', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def set_cooldown():
    """Update cooldown time"""
    with open(COOLDOWN_FILE, 'w') as f:
        json.dump({'last_time': time.time()}, f)

def format_username(user):
    """Format username neatly"""
    name = []
    if user.first_name:
        name.append(user.first_name)
    if user.last_name:
        name.append(user.last_name)
    username = " ".join(name) if name else "No Name"
    
    # Clean username from special characters that might break markdown
    username = re.sub(r'([\[\](){}<>_*~`])', r'\\\1', username)
    return username

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def cekmute_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_cekmute_cmd = False
        
        if current_prefix == "no":
            if msg.lower() == "cekmute":
                is_cekmute_cmd = True
        else:
            if msg == f"{current_prefix}cekmute":
                is_cekmute_cmd = True
                
        if not is_cekmute_cmd:
            return

        # Check cooldown (5 minutes)
        last_time = get_cooldown()
        if time.time() - last_time < 300:
            remaining = 300 - (time.time() - last_time)
            mins, secs = divmod(int(remaining), 60)
            await event.reply(
                f"<blockquote>⏳ <b>Cooldown aktif!</b> Coba lagi dalam {mins}m {secs}s</blockquote>",
                parse_mode="html"
            )
            return

        if event.is_private:
            return

        processing_msg = None
        try:
            # Get total muted count
            total_result = await user(GetParticipantsRequest(
                channel=await event.get_input_chat(),
                filter=ChannelParticipantsBanned(q=''),
                offset=0,
                limit=1,
                hash=0
            ))
            total_muted = total_result.count

            # Start processing
            start_time = time.time()
            processing_msg = await event.reply(
                "<blockquote>🔄 <b>Memproses</b> <code>{}</code> <b>member... (0%)</b>\n"
                "📌 <b>Gunakan command ini maksimal 1x per 5 menit</b></blockquote>".format(total_muted),
                parse_mode="html"
            )

            # Process muted members
            muted_users = []
            processed = 0
            async for participant in user.iter_participants(
                event.chat_id,
                filter=ChannelParticipantsBanned,
                aggressive=True
            ):
                processed += 1
                percent = math.floor((processed/total_muted)*100) if total_muted > 0 else 0
                
                # Update progress every 5% or 100 users
                if processed % 100 == 0 or percent % 5 == 0:
                    try:
                        await processing_msg.edit(
                            "<blockquote>🔄 <b>Memproses</b> <code>{}</code> <b>member... ({}%)</b>\n"
                            "✅ <b>Ditemukan:</b> <code>{}</code></blockquote>".format(
                                total_muted, percent, len(muted_users)
                            ),
                            parse_mode="html"
                        )
                    except:
                        pass
                
                username = format_username(participant)
                muted_users.append(f"‣ <a href='tg://user?id={participant.id}'>{username}</a>")
                await asyncio.sleep(0.02)

            # Delete processing message
            await processing_msg.delete()

            # Send results in chunks
            chunk_size = 30
            for i in range(0, len(muted_users), chunk_size):
                chunk = muted_users[i:i+chunk_size]
                await event.reply(
                    "<blockquote>{}</blockquote>".format("\n".join(chunk)),
                    parse_mode="html",
                    link_preview=False
                )
                await asyncio.sleep(1)

            # Update cooldown
            set_cooldown()

            # Send summary
            duration = time.time() - start_time
            await event.reply(
                "<blockquote>✅ <b>Selesai!</b>\n"
                "• <b>Total Muted:</b> <code>{}</code>\n"
                "• <b>Durasi:</b> <code>{:.2f}</code> detik\n\n"
                "⏳ <b>Cooldown 5 menit dimulai sekarang</b></blockquote>".format(
                    len(muted_users), duration
                ),
                parse_mode="html"
            )

        except Exception as e:
            await event.reply(
                "<blockquote>❌ <b>Error:</b> <code>{}</code></blockquote>".format(str(e)[:200]),
                parse_mode="html"
            )
            if processing_msg:
                await processing_msg.delete()