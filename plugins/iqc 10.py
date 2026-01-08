import os
import json
import aiohttp
import asyncio
from datetime import datetime
from telethon import events
from io import BytesIO
from PIL import Image
import random
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

async def download_iqc_image(message_text):
    """Download iPhone quoted image from API"""
    time = datetime.now().strftime('%H:%M')
    battery = random.randint(1, 100)
    
    api_url = f"https://brat.siputzx.my.id/iphone-quoted?time={time}&batteryPercentage={battery}&carrierName=INDOSAT&messageText={message_text}&emojiStyle=apple"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                image_data = await response.read()
                return image_data
            else:
                raise Exception(f"API returned status code: {response.status}")

async def setup(bot, user):
    def is_command(msg, commands, prefix):
        """Check if message matches any of the commands"""
        msg = msg.strip()
        if not msg:
            return False
        
        if not prefix:  # When prefix is "no"
            first_word = msg.split()[0].lower() if msg else ""
            return first_word in commands
        else:
            return any(msg.startswith(f"{prefix}{cmd}") for cmd in commands)

    def get_args(msg, command, prefix):
        """Extract arguments from command"""
        msg = msg.strip()
        if not msg:
            return ""
        
        if not prefix:  # When prefix is "no"
            parts = msg.split()
            return ' '.join(parts[1:]) if len(parts) > 1 else ""
        else:
            return msg[len(prefix + command):].strip()

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def iqc_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check if it's the iqc command
        commands = ['iqc', 'iphonequote']
        if not is_command(msg, commands, current_prefix):
            return

        # Get the command used
        used_command = next(
            (cmd for cmd in commands 
             if msg.startswith(f"{current_prefix}{cmd}" if current_prefix else cmd)),
            None
        )
        
        if not used_command:
            return

        # Extract arguments
        args = get_args(msg, used_command, current_prefix)
        
        if not args:
            await event.reply(
                f"<blockquote>❌ <b>Format salah!</b>\n"
                f"Gunakan: <code>{(current_prefix if current_prefix else '')}{used_command} &lt;teks&gt;</code></blockquote>\n"
                f"<blockquote>Contoh: <code>{(current_prefix if current_prefix else '')}{used_command} kadang iri liat org bahagia</code></blockquote>",
                parse_mode="html"
            )
            return

        processing_msg = await event.reply(
            "<blockquote>⏳ <b>Sedang membuat iPhone quote...</b></blockquote>",
            parse_mode="html"
        )
        
        try:
            # Download the image
            image_data = await download_iqc_image(args)
            
            # Send the image
            await user.send_file(
                event.chat_id,
                file=image_data,
                caption="<blockquote>✅ <b>Berhasil membuat iPhone quote!</b></blockquote>",
                parse_mode="html",
                reply_to=event.id
            )
            
            # Delete processing message
            await processing_msg.delete()
            
        except Exception as e:
            await processing_msg.edit(
                f"<blockquote>❌ <b>Gagal membuat iPhone quote:</b> <code>{str(e)[:200]}</code></blockquote>",
                parse_mode="html"
            )

