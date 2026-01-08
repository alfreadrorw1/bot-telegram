import re
import json
import os
from telethon import events
from config import OWNER_ID

current_prefix = '.'  # Default

def ensure_data_dir():
    # Buat folder data jika belum ada
    if not os.path.exists("data"):
        os.makedirs("data")

def load_prefix():
    global current_prefix
    ensure_data_dir()  # Pastikan folder data ada
    try:
        with open('data/prefix.json', 'r') as f:
            data = json.load(f)
            current_prefix = data.get('prefix', '.')
    except FileNotFoundError:
        current_prefix = '.'
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': current_prefix}, f)

def save_prefix(new_prefix):
    global current_prefix
    ensure_data_dir()  # Pastikan folder data ada
    current_prefix = new_prefix
    with open('data/prefix.json', 'w') as f:
        json.dump({'prefix': new_prefix}, f)

def setup(bot, user):
    load_prefix()

    # Handler untuk ganti prefix
    @user.on(events.NewMessage(
        pattern=r"(?i)^setprefix\s+(.+)"
    ))
    async def setprefix_handler(event):
        if event.sender_id != OWNER_ID:
            await event.reply("🚫 **Hanya owner yang bisa mengganti prefix!**")
            return

        input_prefix = event.pattern_match.group(1).strip().lower()

        if input_prefix == "no":
            save_prefix("no")
            await event.reply("✅ **Prefix dinonaktifkan! Gunakan command tanpa prefix.**")
        elif len(input_prefix) == 1:
            save_prefix(input_prefix)
            await event.reply(f"✅ **Prefix diubah ke `{input_prefix}`**")
        else:
            await event.reply("❌ **Panjang prefix harus 1 karakter atau `setprefix no`!**")

    # Handler cek prefix
    @user.on(events.NewMessage(pattern=r"(?i)^prefix$"))
    async def prefix_check_handler(event):
        status = "`tidak ada`" if current_prefix == "no" else f"`{current_prefix}`"
        await event.reply(f"🔠 **Prefix saat ini:** {status}")