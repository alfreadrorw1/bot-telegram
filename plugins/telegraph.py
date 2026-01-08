# plugins/telegraph.py
import json
import aiohttp
import os
import time
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

async def setup(bot, user):
    @user.on(events.NewMessage())
    async def telegraph_handler(event):
        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check if message is a telegraph command
        if current_prefix == "no":
            # No prefix mode - check for exact "telegraph" command
            if not message.lower().startswith('telegraph '):
                return
            cmd_part = message[9:].strip()  # Remove "telegraph "
        else:
            # Prefix mode - check for prefix followed by telegraph
            if not message.startswith(current_prefix):
                return
            cmd_part = message[len(current_prefix):].strip()
            if not cmd_part.lower().startswith('telegraph '):
                return
            cmd_part = cmd_part[9:].strip()  # Remove "telegraph "
        
        # Only allow in private chats or from owner
        if not event.is_private and event.sender_id != OWNER_ID:
            return

        # Split input by comma
        parts = [x.strip() for x in cmd_part.split(',', 1)]
        
        # Validate input
        if len(parts) < 2 or not all(parts):
            await event.reply('❌ Format salah.\nGunakan: telegraph judul,konten')
            return
            
        title, content = parts
        
        try:
            async with aiohttp.ClientSession() as session:
                # Create anonymous account
                async with session.post(
                    'https://api.telegra.ph/createAccount',
                    params={'short_name': 'AlfreadBot', 'author_name': 'Bot'}
                ) as acc_res:
                    acc_data = await acc_res.json()
                    access_token = acc_data.get('result', {}).get('access_token', '')
                
                if not access_token:
                    await event.reply('❌ Gagal membuat akun Telegraph')
                    return
                
                # Create page
                page_data = {
                    'access_token': access_token,
                    'title': title,
                    'content': [{'tag': 'p', 'children': [content]}],
                    'return_content': False
                }
                
                async with session.post(
                    'https://api.telegra.ph/createPage',
                    json=page_data
                ) as page_res:
                    page = await page_res.json()
                    
                    if page.get('ok'):
                        await event.reply(f'✅ Sukses! Artikel kamu:\nhttps://telegra.ph/{page["result"]["path"]}')
                    else:
                        error = page.get('error', 'Unknown error')
                        await event.reply(f'❌ Gagal membuat halaman: {error}')
                        
        except Exception as e:
            print(f'Telegraph error: {str(e)}')
            await event.reply('❌ Terjadi kesalahan saat membuat artikel Telegraph.')