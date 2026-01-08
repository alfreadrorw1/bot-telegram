import os
import json
import random
import asyncio
from telethon import events, types
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

# Create config directory if not exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# Khodam Database
KHODAM_TYPES = {
    "api": ["Phoenix", "Blaze", "Inferno", "Ember"],
    "jawa": ["Javanese Guardian", "Mystic Warrior", "Ancient Sage", "Spiritual Protector"],
    "arab": ["Djinn", "Ifrit", "Marid", "Shaitan"],
    "sunda": ["Sundanese Spirit", "Mountain Guardian", "Forest Keeper", "Ancient Sunda"]
}

KHODAM_LEVELS = ["Pemula", "Menengah", "Ahli", "Master", "Legenda"]

def get_live_prefix():
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

def generate_khodam_result(name):
    """Generate unique khodam analysis"""
    khodam_type = random.choice(list(KHODAM_TYPES.keys()))
    khodam_name = random.choice(KHODAM_TYPES[khodam_type])
    khodam_level = random.choice(KHODAM_LEVELS)
    power = random.randint(70, 100)
    compatibility = random.randint(60, 100)
    
    # Special effects based on power
    if power > 90:
        effect = "Aura Legendaris"
        element = "Cahaya"
    else:
        effect = "Energi Spiritual"
        element = random.choice(["Api", "Air", "Angin", "Tanah"])

    return {
        "name": name,
        "khodam_type": khodam_type,
        "khodam_name": khodam_name,
        "level": khodam_level,
        "power": power,
        "compatibility": compatibility,
        "effect": effect,
        "element": element,
        "chakra": random.randint(3, 7)
    }

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, pattern=r'^\.?cekkhodam(\s+[\w\s]+)?$'))
    async def cekkhodam_handler(event):
        try:
            # Get current prefix
            current_prefix = get_live_prefix()
            
            # Check if command is properly formatted
            msg = event.text.strip()
            if not msg.startswith(current_prefix) and not msg.lower().startswith('cekkhodam'):
                return

            # Get name from message or reply
            name = ""
            if event.is_reply:
                reply = await event.get_reply_message()
                name = reply.sender.first_name or "Unknown"
            else:
                parts = msg.split(maxsplit=1)
                if len(parts) > 1:
                    name = parts[1].strip()
                else:
                    await event.reply("⚠️ Mohon sertakan nama atau reply seseorang!\nContoh:\n`.cekkhodam [nama]`\natau reply `.cekkhodam` ke pesan seseorang")
                    return

            # Generate analysis
            result = generate_khodam_result(name)

            # Create response
            response = f"""
✨ **ANALISIS KHODAM** ✨

Pemilik: **{result['name']}**
➖➖➖➖➖➖
Tipe Khodam: **{result['khodam_type'].upper()}**
Nama Khodam: **{result['khodam_name']}**
Level: **{result['level']}** (Kekuatan {result['power']}%)

Karakteristik:
Elemen: **{result['element']}**
Aura: **{result['effect']}**
Chakra: **{'★' * result['chakra']}**

Kompabilitas: **{result['compatibility']}%**
➖➖➖➖➖➖
Analisis ini menunjukkan potensi spiritual Anda!
            """

            # Send response
            await event.respond(response, parse_mode='md')
            await event.delete()

            # Add dramatic effect
            await asyncio.sleep(1)
            await event.respond("Proses analisis selesai... ✨", parse_mode=None)

        except Exception as e:
            print(f"Error in cekkhodam handler: {e}")
            await event.respond("❌ Terjadi error saat memproses permintaan. Silakan coba lagi.")