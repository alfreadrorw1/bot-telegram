# anime.py
import json
import os
import aiohttp
from bs4 import BeautifulSoup
from telethon import events
from config import OWNER_ID

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

async def safe_get_text(element, default="N/A"):
    """Safely get text from BeautifulSoup element"""
    if element is None:
        return default
    text = element.get_text(strip=True)
    return text if text else default

async def scrape_mal_info(anime_name):
    """Improved MAL scraper with direct anime page access"""
    try:
        search_url = f"https://myanimelist.net/anime.php?q={anime_name.replace(' ', '+')}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            # Search for anime
            async with session.get(search_url, headers=headers) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find first anime result link
                result = soup.find('div', class_='js-categories-seasonal')
                if not result:
                    return None
                    
                anime_link = result.find('a', class_='hoverinfo_trigger')
                if not anime_link:
                    return None
                    
                anime_url = anime_link.get('href')
                if not anime_url:
                    return None
                
                # Get anime details page
                async with session.get(anime_url, headers=headers) as anime_response:
                    if anime_response.status != 200:
                        return None
                    
                    anime_html = await anime_response.text()
                    anime_soup = BeautifulSoup(anime_html, 'html.parser')
                    
                    # Extract information with better selectors
                    title = await safe_get_text(anime_soup.find('h1', class_='title-name'))
                    
                    # Image extraction with fallback
                    image = None
                    img_tag = anime_soup.find('img', {'data-src': True}) or anime_soup.find('img', {'src': True})
                    if img_tag:
                        image = img_tag.get('data-src') or img_tag.get('src')
                    
                    # Extract details from information table
                    details = {}
                    info_div = anime_soup.find('div', id='contentWrapper')
                    if info_div:
                        for entry in info_div.find_all('div', class_='spaceit_pad'):
                            if entry and ':' in entry.text:
                                parts = entry.text.split(':', 1)
                                if len(parts) == 2:
                                    details[parts[0].strip()] = parts[1].strip()
                    
                    # Get synopsis
                    synopsis_div = anime_soup.find('p', itemprop='description')
                    synopsis = await safe_get_text(synopsis_div) if synopsis_div else 'N/A'
                    
                    # Get score
                    score_div = anime_soup.find('div', class_='score-label')
                    score = await safe_get_text(score_div) if score_div else 'N/A'
                    
                    # Get genres
                    genres = []
                    genre_tags = anime_soup.find_all('span', itemprop='genre')
                    if genre_tags:
                        genres = [await safe_get_text(tag) for tag in genre_tags]
                    
                    # Format the information
                    anime_info = {
                        'title': title,
                        'picture': image or "https://via.placeholder.com/225x350.png?text=No+Image",
                        'type': details.get('Type', 'N/A'),
                        'episodes': details.get('Episodes', 'N/A'),
                        'status': details.get('Status', 'N/A'),
                        'premiered': details.get('Aired', 'N/A'),
                        'genres': ', '.join(genres) if genres else 'N/A',
                        'studios': details.get('Studios', 'N/A'),
                        'score': score,
                        'rating': details.get('Rating', 'N/A'),
                        'ranked': details.get('Ranked', 'N/A'),
                        'popularity': details.get('Popularity', 'N/A'),
                        'synopsis': synopsis,
                        'url': anime_url
                    }
                    
                    return anime_info
    except Exception as e:
        print(f"[ANIME] Error scraping MAL: {str(e)}")
        return None

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def anime_command_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check for anime command
        is_anime_cmd = False
        anime_name = ""
        
        if current_prefix == "no":
            if msg.lower().startswith("anime"):
                is_anime_cmd = True
                anime_name = msg[5:].strip()
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd.startswith("anime"):
                    is_anime_cmd = True
                    anime_name = cmd[5:].strip()
        
        if not is_anime_cmd or not anime_name:
            return

        # Send processing message
        processing_msg = await event.reply("🔍 **Mencari informasi anime...**")
        
        # Scrape MAL for anime info
        anime_info = await scrape_mal_info(anime_name)
        if not anime_info:
            await processing_msg.edit("❌ **Tidak dapat menemukan anime tersebut atau terjadi error!**")
            return

        # Format the response
        base_info = (
            f"🎀 **Title:** {anime_info['title']}\n"
            f"🎋 **Type:** {anime_info['type']}\n"
            f"🎐 **Premiered on:** {anime_info['premiered']}\n"
            f"💠 **Total Episodes:** {anime_info['episodes']}\n"
            f"📈 **Status:** {anime_info['status']}\n"
            f"💮 **Genres:** {anime_info['genres']}\n"
            f"📍 **Studio:** {anime_info['studios']}\n"
            f"🌟 **Score:** {anime_info['score']}\n"
            f"💎 **Rating:** {anime_info['rating']}\n"
            f"🏅 **Rank:** {anime_info['ranked']}\n"
            f"💫 **Popularity:** {anime_info['popularity']}\n"
            f"🌐 **URL:** {anime_info['url']}\n\n"
        )

        try:
            # First send image with base info
            await event.client.send_file(
                event.chat_id,
                anime_info['picture'],
                caption=base_info,
                reply_to=event.message
            )
            
            # Then send synopsis if it exists
            if anime_info['synopsis'] and anime_info['synopsis'] != 'N/A':
                await event.reply(f"❄ **Description:** {anime_info['synopsis']}")
            
            await processing_msg.delete()
        except Exception as e:
            await processing_msg.edit(f"❌ **Gagal mengirim hasil:** {str(e)}")