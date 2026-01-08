import os
import json
import asyncio
from telethon import events
from config import OWNER_ID

# File paths
NOTES_FILE = os.path.join('data', 'notes.json')

def ensure_data_dir():
    """Create data directory if not exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def get_live_prefix():
    """Get current prefix from config file"""
    try:
        with open('data/prefix.json', 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_data_dir()
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def load_notes():
    """Load notes from JSON file"""
    try:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r') as f:
                return json.load(f)
    except:
        return {}
    return {}

def save_notes(notes):
    """Save notes to JSON file"""
    ensure_data_dir()
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=4)

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def save_note_handler(event):
        """Handle save note command with reply support"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format with prefix
        if current_prefix:
            if not msg.startswith(f"{current_prefix}save"):
                return
            args = msg[len(current_prefix)+4:].strip()
        else:
            if not msg.lower().startswith("save"):
                return
            args = msg[4:].strip()

        reply_msg = await event.get_reply_message()
        
        if not args and not reply_msg:
            await event.edit("`❌ Format: [prefix]save <name> [content] atau reply pesan`")
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

            notes = load_notes()
            notes[name] = content
            save_notes(notes)
            
            await event.edit(f"`✅ Note '{name}' disimpan!`")
            await asyncio.sleep(2)
            await event.delete()
            
        except Exception as e:
            await event.edit(f"`❌ Error: {str(e)}`")

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def get_note_handler(event):
        """Handle get note command"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}get"):
                return
            name = msg[len(current_prefix)+3:].strip().lower()
        else:
            if not msg.lower().startswith("get"):
                return
            name = msg[3:].strip().lower()

        if not name:
            await event.edit("`❌ Format: [prefix]get <note name>`")
            return

        notes = load_notes()
        if name in notes:
            await event.edit(f"`📝 Note {name}:`\n\n{notes[name]}")
        else:
            await event.edit(f"`❌ Note '{name}' tidak ditemukan`")

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def list_notes_handler(event):
        """Handle list notes command"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}notes"):
                return
        else:
            if not msg.lower().startswith("notes"):
                return

        notes = load_notes()
        if not notes:
            await event.edit("`📭 Tidak ada notes yang disimpan`")
            return

        message = "╭──「 Notes 」\n"
        for idx, name in enumerate(notes.keys(), 1):
            message += f"│ {idx}. {name}\n"
        message += "╰──「 ᴀʟꜰʀᴇᴀᴅ  」"
        await event.edit(message)

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def clear_note_handler(event):
        """Handle clear note command"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}clear"):
                return
            args = msg[len(current_prefix)+5:].strip().lower()
        else:
            if not msg.lower().startswith("clear"):
                return
            args = msg[5:].strip().lower()

        if not args:
            await event.edit("`❌ Format: [prefix]clear <note name|all>`")
            return

        notes = load_notes()
        if args == "all":
            save_notes({})
            await event.edit("`✅ Semua notes telah dihapus!`")
        elif args in notes:
            del notes[args]
            save_notes(notes)
            await event.edit(f"`✅ Note '{args}' telah dihapus!`")
        else:
            await event.edit(f"`❌ Note '{args}' tidak ditemukan`")

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def notes_help_handler(event):
        """Show notes help"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        if current_prefix:
            if not msg.startswith(f"{current_prefix}noteshelp"):
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
        await event.edit(help_text)