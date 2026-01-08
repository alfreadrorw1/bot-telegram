# translate.py
import os
import json
from telethon import events
from config import OWNER_ID
from googletrans import Translator

# File configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
STATE_FILE = os.path.join(CONFIG_DIR, 'translate_state.json')

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

def load_translate_state():
    """Load auto-translate state from file"""
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f).get('auto_translate', False)
    except (json.JSONDecodeError, KeyError):
        pass
    return False

def save_translate_state(state):
    """Save auto-translate state to file"""
    with open(STATE_FILE, 'w') as f:
        json.dump({'auto_translate': state}, f, indent=2)

async def setup(bot, user):
    translator = Translator()
    current_prefix = get_live_prefix()

    # Translate Command Handler
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def translate_handler(event):
        msg = (event.text or '').strip()
        prefix = get_live_prefix()
        
        # Check for translate command
        is_translate_cmd = False
        
        if prefix == "no":
            if msg.lower() == "tr":
                is_translate_cmd = True
        else:
            if msg == f"{prefix}tr":
                is_translate_cmd = True
                
        if not is_translate_cmd:
            return
            
        if not event.is_reply:
            await event.reply("ℹ️ **Harap reply pesan yang ingin diterjemahkan!**")
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg.text:
            await event.reply("ℹ️ **Pesan yang di-reply tidak mengandung teks!**")
            return

        processing_msg = await event.reply("🔄 **Menerjemahkan...**")

        try:
            # Detect language first
            detected = translator.detect(reply_msg.text)
            
            # If already Indonesian, no need to translate
            if detected.lang == 'id':
                await processing_msg.edit("ℹ️ **Pesan sudah dalam bahasa Indonesia**")
                return

            # Translate to Indonesian
            translated = translator.translate(reply_msg.text, src=detected.lang, dest='id')
            
            # Send the translated text
            await event.client.send_message(
                event.chat_id,
                f"{translated.text}",
                reply_to=reply_msg.id
            )
            
            await processing_msg.delete()
            
        except Exception as e:
            await processing_msg.edit(f"❌ **Gagal menerjemahkan:** {str(e)}")

    # Auto-Translate Toggle Handler
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def auto_translate_handler(event):
        msg = (event.text or '').strip()
        prefix = get_live_prefix()
        
        # Check for auto-translate command
        is_auto_cmd = False
        
        if prefix == "no":
            if msg.lower() == "trall":
                is_auto_cmd = True
        else:
            if msg == f"{prefix}trall":
                is_auto_cmd = True
                
        if not is_auto_cmd:
            return
            
        # Toggle auto-translation state
        current_state = load_translate_state()
        new_state = not current_state
        save_translate_state(new_state)

        status = "AKTIF" if new_state else "NONAKTIF"
        await event.reply(f"🔄 **Mode Auto-Translate sekarang {status}**")

    # Auto-Translate Message Handler
    @user.on(events.NewMessage(incoming=True))
    async def auto_translate_message_handler(event):
        if not load_translate_state():
            return
            
        if not event.text or event.sender_id == OWNER_ID:
            return
            
        try:
            # Detect language
            detected = translator.detect(event.text)
            if detected.lang == 'id':
                return
                
            # Translate to Indonesian
            translated = translator.translate(event.text, src=detected.lang, dest='id')
            
            # Send translation
            await event.reply(f"{translated.text}")
            
        except Exception as e:
            print(f"[TRANSLATE] Error: {str(e)}")