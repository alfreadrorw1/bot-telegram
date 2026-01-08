# plugins/premium/help.py
import os
import json
import logging
from telethon import events, Button
from config import BOT_USERNAME, OWNER_ID
from ..help import FEATURES, FEATURES_LIST, ITEMS_PER_PAGE, TOTAL_PAGES, create_help_caption, get_page_markup

logger = logging.getLogger(__name__)

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
            return json.load(f).get('prefix', '.')
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

async def setup(bot, client, user_id):
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def help_handler(event):
        """Handle help command with prefix"""
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.raw_text or '').strip()
        
        if not message.startswith(current_prefix):
            return

        cmd = message[len(current_prefix):].strip().lower()
        
        if cmd == "help":
            try:
                await event.delete()
                result = await client.inline_query(BOT_USERNAME, "help")
                if result:
                    await result[0].click(event.chat_id, reply_to=event.reply_to_msg_id)
                else:
                    await event.respond("⚠️ Failed to load help menu")
            except Exception as e:
                logger.error(f"Help command error: {e}")
                await event.respond("⚠️ Error loading help menu")

    @client.on(events.CallbackQuery(pattern=r'page_(\d+)'))
    async def page_handler(event):
        try:
            page = int(event.pattern_match.group(1))
            await event.edit(
                create_help_caption(page, event.sender.first_name),
                buttons=get_page_markup(page),
                parse_mode='html'
            )
        except Exception as e:
            logger.error(f"Page error: {e}")
            await event.answer("⚠️ Page load failed", alert=True)

    @client.on(events.CallbackQuery(pattern=r'detail_([^_]+)_(\d+)'))
    async def detail_handler(event):
        try:
            feature = event.pattern_match.group(1)
            if isinstance(feature, bytes):
                feature = feature.decode('utf-8')
            page = int(event.pattern_match.group(2))
            detail_text = (
                f"<blockquote>📌 {feature.capitalize()} Details</blockquote>\n\n"
                f"{FEATURES[feature]}\n\n"
                f"<blockquote>Requested by {event.sender.first_name}</blockquote>"
            )
            await event.edit(
                detail_text,
                buttons=[[Button.inline("🔙 Back", data=f"page_{page}")]],
                parse_mode='html'
            )
        except Exception as e:
            logger.error(f"Detail error: {e}")
            await event.answer("⚠️ Details load failed", alert=True)

    @client.on(events.CallbackQuery(pattern=r'close'))
    async def close_handler(event):
        try:
            await event.delete()
        except Exception as e:
            logger.error(f"Close error: {e}")
            await event.answer("Already deleted")

    logger.info(f"Help system ready for user {user_id}")