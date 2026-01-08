import os
import re
import json
import asyncio
from telethon import events
from config import OWNER_ID

# File configuration
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
    current_prefix = get_live_prefix()

    # Wibu2 Command Handler (user only)
    @user.on(events.NewMessage(
        pattern=rf'^{re.escape(current_prefix)}wibu2$',
        outgoing=True,
        from_users=OWNER_ID
    ))
    async def wibu2_handler(event):
        messages = [
            "**Sial Ada Wibu😨**",
            "**Sekuat Apapun Aku😭**",
            "**Jika Ada Wibu😨**",
            "**Aku Harus Lari🏃🏻**",
            "**Lari Cukkk Ada Wibuuu🏃🏻**",
            "**Argghh Bangkeee!🏃🏻**",
            "**Lari Sekencang-Kencangnya🤸🏻**",
            "**Karena Kita Sedang🤾🏻**",
            "**Menghadapi Ras Terkuat🤸🏻**",
            "**Yang Ada Di Dunia🏃🏻**",
            "**Wibuuuu🪂**",
            "**Arghhhhhhh🧗🏻**",
            "**Istrinya Kartun🤾🏻**",
            "**Dasar Wibu😨**",
            "**Maaf Wibu🤼‍♂️**",
            "**Aku Tidak Akan🤾🏻**",
            "**Mengulanginya Lagi🏃🏻**",
            "**Tapi Bo'ong🤾🏻**",
            "**Dasar Wibu, Istri Kartun🪂**",
            "**IUHH DEMEN KOK SAMA 2D😖**"
        ]
        
        try:
            for msg in messages:
                await event.edit(msg)
                await asyncio.sleep(0.7)
        except Exception as e:
            await event.reply(f"Error: {str(e)}")

    # Wibbu Command Handler (user only)
    @user.on(events.NewMessage(
        pattern=rf'^{re.escape(current_prefix)}wibbu$',
        outgoing=True,
        from_users=OWNER_ID
    ))
    async def wibbu_handler(event):
        try:
            await event.edit("**WI WIII WIIII WIIII.....**")
            await asyncio.sleep(1)
            await event.edit("__ARGHHH LARI ADA WIBUU!....__")
            await asyncio.sleep(1)
            
            # Running animation
            positions = [
                "`🏃                        🏂`",
                "`🏃                       🏂`",
                "`🏃                      🏂`",
                "`🏃                     🏂`",
                "`🏃   `LARII ADA WIBU`          🏂`",
                "`🏃                   🏂`",
                "`🏃                  🏂`",
                "`🏃                 🏂`",
                "`🏃                🏂`",
                "`🏃               🏂`",
                "`🏃              🏂`",
                "`🏃             🏂`",
                "`🏃            🏂`",
                "`🏃           🏂`",
                "`🏃..Tolong..🏂`",
                "`🏃           🏂`",
                "`🏃            🏂`",
                "`🏃             🏂`",
                "`🏃              🏂`",
                "`🏃               🏂`",
                "`🏃                🏂`",
                "`🏃                 🏂`",
                "`🏃                  🏂`",
                "`🏃                   🏂`",
                "`🏃                    🏂`",
                "`🏃                     🏂`",
                "`🏃  Huh-Huh-Huh       🏂`",
                "`🏃                   🏂`",
                "`🏃                  🏂`",
                "`🏃                 🏂`",
                "`🏃                🏂`",
                "`🏃               🏂`",
                "`🏃              🏂`",
                "`🏃             🏂`",
                "`🏃            🏂`",
                "`🏃           🏂`",
                "`🏃          🏂`",
                "`🏃         🏂`",
                "__KOK MAKIN DEKET SI WIBU__",
                "`🏃       🏂`",
                "`🏃      🏂`",
                "`🏃     🏂`",
                "`🏃    🏂`",
                "**Untung Ngga Kena Njir**",
                "🎯",
                "**Mampus Kau Wibu**"
            ]
            
            for pos in positions:
                await event.edit(pos)
                await asyncio.sleep(0.3)
                
        except Exception as e:
            await event.reply(f"Error: {str(e)}")
            
            
    @user.on(events.NewMessage(
        pattern=rf'^{re.escape(current_prefix)}sangean$',
        outgoing=True,
        from_users=OWNER_ID
    ))
    async def sangean_handler(event):
        messages = [
            "**S**",
            "**Sa**",
            "**San**",
            "**Sang**",
            "**Sange**",
            "**Sangea**",
            "**Sangean**",
            "**Sangean B**",
            "**Sangean Be**",
            "**Sangean Beg**",
            "**Sangean Bego**",
            "**Sangean Bego T**",
            "**Sangean Bego To**",
            "**Sangean Bego Tol**",
            "**Sangean Bego Tolo**",
            "**Sangean Bego Tolol**",
            "**Sangean Bego Tolol S**",
            "**Sangean Bego Tolol Si**",
            "**Sangean Bego Tolol Sin**",
            "**Sangean Bego Tolol Sini**",
            "**Sangean Bego Tolol Sini M**",
            "**Sangean Bego Tolol Sini Ma**",
            "**Sangean Bego Tolol Sini Mak**",
            "**Sangean Bego Tolol Sini Mak Lu**",
            "**Sangean Bego Tolol Sini Mak Lu G**",
            "**Sangean Bego Tolol Sini Mak Lu Gu**",
            "**Sangean Bego Tolol Sini Mak Lu Gua**",
            "**Sangean Bego Tolol Sini Mak Lu Gua E**",
            "**Sangean Bego Tolol Sini Mak Lu Gua En**",
            "**Sangean Bego Tolol Sini Mak Lu Gua Ent**",
            "**Sangean Bego Tolol Sini Mak Lu Gua Ento**",
            "**Sangean Bego Tolol Sini Mak Lu Gua Entot**",
            "**K**",
            "**Ka**",
            "**Kan**",
            "**Kan M**",
            "**Kan Ma**",
            "**Kan Mak**",
            "**Kan Mak L**",
            "**Kan Mak Lu**",
            "**Kan Mak Lu L**",
            "**Kan Mak Lu Lo**",
            "**Kan Mak Lu Lon**",
            "**Kan Mak Lu Lont**",
            "**Kan Mak Lu Lonte**",
            "**Haha**",
            "**Haha Haha**",
            "**Haha Haha Haha**"
        ]
        
        try:
            for msg in messages:
                await event.edit(msg)
                await asyncio.sleep(0.2)
        except Exception as e:
            await event.reply(f"Error: {str(e)}")

    # Wibu Help Command Handler (user only)
    @user.on(events.NewMessage(
        pattern=rf'^{re.escape(current_prefix)}wibuhelp$',
        outgoing=True,
        from_users=OWNER_ID
    ))
    async def wibu_help_handler(event):
        help_text = f"""
```📢 Wibu Commands:
• {current_prefix}wibbu - Animasi lari dari wibu
• {current_prefix}wibu2 - Spam text anti wibu
• {current_prefix}wibuhelp - Show this help```
"""
        await event.reply(help_text)