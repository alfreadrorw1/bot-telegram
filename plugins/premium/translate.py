# translate.py
import os
import json
from telethon import events
from config import OWNER_ID
from googletrans import Translator

def get_user_folder(user_id=None):
    """Get user-specific folder path"""
    if user_id is None or user_id == OWNER_ID:
        return 'premium'
    return f'premium/userprem_{user_id}'

def get_prefix(user_id=None):
    """Get current prefix for specific user"""
    user_folder = get_user_folder(user_id)
    try:
        with open(f'{user_folder}/prefix.json', 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs(user_folder, exist_ok=True)
        with open(f'{user_folder}/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def is_premium_user(user_id):
    """Check if user is premium"""
    try:
        with open('premium/premium.json', 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def get_user_translate_file(user_id):
    """Get user-specific translate state file"""
    user_folder = get_user_folder(user_id)
    translate_dir = os.path.join(user_folder, 'translate')
    os.makedirs(translate_dir, exist_ok=True)
    return os.path.join(translate_dir, 'state.json')

def load_user_translate_state(user_id):
    """Load translate state for specific user"""
    state_file = get_user_translate_file(user_id)
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return json.load(f).get('auto_translate', False)
    except:
        pass
    return False

def save_user_translate_state(user_id, state):
    """Save translate state for specific user"""
    state_file = get_user_translate_file(user_id)
    with open(state_file, 'w') as f:
        json.dump({'auto_translate': state}, f, indent=2)

async def safe_edit(message, text):
    """Safely edit a message with error handling"""
    try:
        if message.out:
            await message.edit(text)
        else:
            await message.reply(text)
            try:
                await message.delete()
            except:
                pass
    except Exception:
        pass

async def setup(bot, client, user_id=None):
    """Setup translation commands for premium users"""
    current_user_id = user_id
    translator = Translator()

    async def check_auth(event):
        """Check if user is authorized to use the command"""
        sender_id = event.sender_id
        return (sender_id == OWNER_ID or 
               (is_premium_user(sender_id) and current_user_id == sender_id))

    # Translate Command Handler
    @client.on(events.NewMessage())
    async def translate_handler(event):
        """Handle manual translation requests"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "tr"):
                return
        elif not msg.lower().startswith("tr"):
            return

        if not event.is_reply:
            await safe_edit(event, "ℹ️ **Harap reply pesan yang ingin diterjemahkan!**")
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg.text:
            await safe_edit(event, "ℹ️ **Pesan yang di-reply tidak mengandung teks!**")
            return

        processing_msg = await event.reply("🔄 **Menerjemahkan...**")

        try:
            # Detect language first
            detected = translator.detect(reply_msg.text)
            
            # If already Indonesian, no need to translate
            if detected.lang == 'id':
                await safe_edit(processing_msg, "ℹ️ **Pesan sudah dalam bahasa Indonesia**")
                return

            # Translate to Indonesian
            translated = translator.translate(reply_msg.text, src=detected.lang, dest='id')
            
            # Send the translated text
            await event.client.send_message(
                event.chat_id,
                f"**Terjemahan:**\n{translated.text}",
                reply_to=reply_msg.id
            )
            
            await safe_delete(processing_msg)
            
        except Exception as e:
            await safe_edit(processing_msg, f"❌ **Gagal menerjemahkan:** {str(e)}")

    # Auto-Translate Toggle Handler
    @client.on(events.NewMessage())
    async def auto_translate_handler(event):
        """Toggle auto-translation state"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "trall"):
                return
        elif not msg.lower().startswith("trall"):
            return

        # Toggle auto-translation state
        current_state = load_user_translate_state(event.sender_id)
        new_state = not current_state
        save_user_translate_state(event.sender_id, new_state)

        status = "AKTIF" if new_state else "NONAKTIF"
        await safe_edit(event, f"🔄 **Mode Auto-Translate sekarang {status}**")

    # Auto-Translate Message Handler
    @client.on(events.NewMessage(incoming=True))
    async def auto_translate_message_handler(event):
        """Handle automatic translation of incoming messages"""
        if not event.text or not event.is_private:
            return
            
        # Check if sender has auto-translate enabled
        sender_id = event.sender_id
        if not load_user_translate_state(sender_id):
            return
            
        try:
            # Detect language
            detected = translator.detect(event.text)
            if detected.lang == 'id':
                return
                
            # Translate to Indonesian
            translated = translator.translate(event.text, src=detected.lang, dest='id')
            
            # Send translation
            await event.reply(f"**Terjemahan:**\n{translated.text}")
            
        except Exception as e:
            print(f"[TRANSLATE] Error: {str(e)}")