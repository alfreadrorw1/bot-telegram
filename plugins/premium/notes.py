import os
import json
import asyncio
from telethon import events
from config import OWNER_ID

# File structure
NOTES_DIR = 'data/notes'


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
        
def get_user_folder(user_id=None):
    """Get user-specific folder path"""
    if user_id is None or user_id == OWNER_ID:
        return 'premium'
    return f'premium/userprem_{user_id}'

def get_user_notes_file(user_id):
    """Get user-specific notes file path"""
    user_folder = get_user_folder(user_id)
    notes_dir = os.path.join(user_folder, 'notes')
    os.makedirs(notes_dir, exist_ok=True)
    return os.path.join(notes_dir, 'notes.json')

def is_premium_user(user_id):
    """Check if user is premium"""
    try:
        with open('premium/premium.json', 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return False

async def safe_edit(event, text):
    """Safely edit a message with error handling"""
    try:
        if event.out:
            await event.edit(text)
        else:
            await event.reply(text)
            try:
                await event.delete()
            except:
                pass
    except Exception:
        pass

def load_user_notes(user_id):
    """Load notes for specific user"""
    notes_file = get_user_notes_file(user_id)
    try:
        if os.path.exists(notes_file):
            with open(notes_file, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_user_notes(user_id, notes):
    """Save notes for specific user"""
    notes_file = get_user_notes_file(user_id)
    with open(notes_file, 'w') as f:
        json.dump(notes, f, indent=4)

async def setup(bot, client, user_id=None):
    """Setup notes commands for premium users"""
    current_user_id = user_id

    async def check_auth(event):
        """Check if user is authorized to use the command"""
        sender_id = event.sender_id
        return (sender_id == OWNER_ID or 
               (is_premium_user(sender_id) and current_user_id == sender_id))

    @client.on(events.NewMessage())
    async def save_note_handler(event):
        """Handle save note command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "save"):
                return
            args = msg[len(current_prefix)+4:].strip()
        else:
            if not msg.lower().startswith("save"):
                return
            args = msg[4:].strip()

        reply_msg = await event.get_reply_message()
        
        if not args and not reply_msg:
            await safe_edit(event, "`❌ Format: [prefix]save <name> [content] atau reply pesan`")
            return

        try:
            # Get note name and content
            if args:
                if reply_msg:  # Both args and reply
                    name = args.split()[0].lower()
                    content = reply_msg.text + "\n\n" + " ".join(args.split()[1:]) if len(args.split()) > 1 else reply_msg.text
                else:  # Only args
                    name, content = args.split(maxsplit=1)
                    name = name.lower()
            else:  # Only reply
                name = "temp"
                content = reply_msg.text

            notes = load_user_notes(event.sender_id)
            notes[name] = content
            save_user_notes(event.sender_id, notes)
            
            await safe_edit(event, f"`✅ Note '{name}' disimpan!`")
        except Exception as e:
            await safe_edit(event, f"`❌ Error: {str(e)}`")

    @client.on(events.NewMessage())
    async def get_note_handler(event):
        """Handle get note command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "get"):
                return
            name = msg[len(current_prefix)+3:].strip().lower()
        else:
            if not msg.lower().startswith("get"):
                return
            name = msg[3:].strip().lower()

        if not name:
            await safe_edit(event, "`❌ Format: [prefix]get <note name>`")
            return

        notes = load_user_notes(event.sender_id)
        if name in notes:
            await safe_edit(event, f"`📝 Note {name}:`\n\n{notes[name]}")
        else:
            await safe_edit(event, f"`❌ Note '{name}' tidak ditemukan`")

    @client.on(events.NewMessage())
    async def list_notes_handler(event):
        """Handle list notes command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "notes"):
                return
        else:
            if not msg.lower().startswith("notes"):
                return

        notes = load_user_notes(event.sender_id)
        if not notes:
            await safe_edit(event, "`📭 Tidak ada notes yang disimpan`")
            return

        message = "╭──「 Notes 」\n"
        for idx, name in enumerate(notes.keys(), 1):
            message += f"│ {idx}. {name}\n"
        message += "╰──「 ᴀʟꜰʀᴇᴀᴅ  」"
        await safe_edit(event, message)

    @client.on(events.NewMessage())
    async def clear_note_handler(event):
        """Handle clear note command"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "clear"):
                return
            args = msg[len(current_prefix)+5:].strip().lower()
        else:
            if not msg.lower().startswith("clear"):
                return
            args = msg[5:].strip().lower()

        if not args:
            await safe_edit(event, "`❌ Format: [prefix]clear <note name|all>`")
            return

        notes = load_user_notes(event.sender_id)
        if args == "all":
            save_user_notes(event.sender_id, {})
            await safe_edit(event, "`✅ Semua notes telah dihapus!`")
        elif args in notes:
            del notes[args]
            save_user_notes(event.sender_id, notes)
            await safe_edit(event, f"`✅ Note '{args}' telah dihapus!`")
        else:
            await safe_edit(event, f"`❌ Note '{args}' tidak ditemukan`")

    @client.on(events.NewMessage())
    async def notes_help_handler(event):
        """Show notes help"""
        if not await check_auth(event):
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(current_prefix + "noteshelp"):
                return
        else:
            if not msg.lower().startswith("noteshelp"):
                return

        prefix = current_prefix if current_prefix else ""
        help_text = (
            "╭──「 Notes 」\n"
            f"│ • {prefix}save <name> [content]: Save a note\n"
            f"│ • {prefix}save <name> (reply): Save replied\n"
            f"│ • {prefix}get <note name>: Get a note\n"
            f"│ • {prefix}notes: List all notes\n"
            f"│ • {prefix}clear <note name>: Delete a note\n"
            f"│ • {prefix}clear all: Delete all notes\n"
            "╰──「 ᴀʟꜰʀᴇᴀᴅ  」"
        )
        await safe_edit(event, help_text)