import os
import re
import random
import json
import asyncio
from telethon import events
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

# Bad word patterns
KATA_KASAR = re.compile(
    r'\b(anj([i!]ng)?|b(a|4)ngs?(a|4)t|bgst|t(o|0)l(o|0)l|knt(o|0)l|'
    r'p(a|4)ntek|ppk|m(e|3)m(e|3)k|(a|4)su|goblok|gblk|bego|b(e|3)g(o|0)|'
    r'j(a|4)ncok|jncok)\b',
    flags=re.IGNORECASE
)

# Positive replacements
KATA_BAIK = (
    "teman", "sahabat", "kawan", "sobat", "rekan",
    "bijak", "cerdas", "pandai", "jenius", "brilian"
)

def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_data_dir()
        with open(PREFIX_FILE, 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def generate_replacement(match):
    """Generate replacement word with random emoji"""
    word = match.group()
    replacement = random.choice(KATA_BAIK)
    
    if word.isupper():
        return replacement.upper()
    elif word.istitle():
        return replacement.title()
    
    if random.random() < 0.2:
        emoji = random.choice(["✨", "🌟", "💫", "👑", "🎯"])
        return f"{replacement}{emoji}"
    return replacement

async def setup(bot, user):
    ensure_data_dir()
    TOXIC_ACTIVE = False

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def toxic_handler(event):
        """Handle toxic filter commands"""
        nonlocal TOXIC_ACTIVE
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        if current_prefix:
            if not msg.startswith(f"{current_prefix}toxic"):
                return
            cmd = msg[len(current_prefix)+5:].strip().lower()
        else:
            if not msg.lower().startswith("toxic"):
                return
            cmd = msg[5:].strip().lower()

        if cmd in ["on", "off"]:
            TOXIC_ACTIVE = cmd == "on"
            status = "diaktifkan" if TOXIC_ACTIVE else "dimatikan"
            response = await event.reply(f"✅ Filter toxic {status}!")
            await asyncio.sleep(2)
            await response.delete()
            await event.delete()

    @user.on(events.NewMessage(outgoing=True))
    async def message_filter(event):
        """Filter toxic words in outgoing messages"""
        if not TOXIC_ACTIVE or not event.text:
            return

        if KATA_KASAR.search(event.text):
            new_text = KATA_KASAR.sub(generate_replacement, event.text)
            try:
                await event.edit(new_text)
            except:
                pass

    @user.on(events.NewMessage(outgoing=True, func=lambda e: e.is_reply))
    async def reply_filter(event):
        """Filter toxic words in replies"""
        await message_filter(event)