# alkitab.py
import os
import json
import aiohttp
from telethon import events
from config import OWNER_ID
from bs4 import BeautifulSoup

# File configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def search_alkitab(query):
    """Search Alkitab verses"""
    try:
        url = f"https://alkitab.me/search?q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    verses = soup.find_all('div', class_='vw')
                    
                    for verse in verses:
                        title = verse.find('a').get_text(strip=True)
                        text = verse.find('p').get_text(strip=True)
                        link = verse.find('a')['href']
                        results.append({
                            'title': title,
                            'text': text,
                            'link': link
                        })
                    
                    return results
        return None
    except Exception as e:
        print(f"[ALKITAB] Error: {str(e)}")
        return None

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def alkitab_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check for alkitab command
        is_alkitab_cmd = False
        query = ""
        
        if current_prefix == "no":
            if msg.lower().startswith("alkitab"):
                is_alkitab_cmd = True
                query = msg[7:].strip()
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd.startswith("alkitab"):
                    is_alkitab_cmd = True
                    query = cmd[7:].strip()
        
        if not is_alkitab_cmd:
            return
            
        if not query:
            await event.reply(f"ℹ️ **Mohon masukkan teks pencarian!**\nContoh: `{current_prefix}alkitab kejadian`")
            return

        processing_msg = await event.reply("🔍 **Mencari ayat Alkitab...**")
        
        # Search Alkitab
        results = await search_alkitab(query)
        if not results:
            await processing_msg.edit("❌ **Tidak menemukan hasil pencarian!**")
            return

        # Format the response
        judul = "**────────「 Alkitab 」────────**"
        caption = "\n┄┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┄\n".join(
            f"💌 {result['title']}\n📮 {result['text']}" 
            for result in results
        )

        # Send result (without image if target is bot)
        try:
            if event.is_private and (await event.get_chat()).bot:
                # Send text only if target is bot
                await processing_msg.edit(f"{judul}\n\n{caption}")
            else:
                # Send with image for normal chats
                image_url = "https://telegra.ph/file/a333442553b1bc336cc55.jpg"
                await bot.send_file(
                    event.chat_id,
                    image_url,
                    caption=f"{judul}\n\n{caption}",
                    reply_to=event.message
                )
                await processing_msg.delete()
        except Exception as e:
            # Fallback to text if media send fails
            try:
                await processing_msg.edit(f"{judul}\n\n{caption}")
            except:
                await event.reply(f"{judul}\n\n{caption}")

    # Add similar handler for user client if needed
    @user.on(events.NewMessage(outgoing=True, pattern=r'^\.alkitab\s+(.+)$'))
    async def user_alkitab_handler(event):
        await alkitab_handler(event)