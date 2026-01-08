import os
import random
import asyncio
import json
from telethon import events
from config import OWNER_ID
from alfread import user

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

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

def generate_progress_bar(percent, width=20):
    """Generate a text-based progress bar"""
    filled = '█' * int(percent / 100 * width)
    empty = '░' * (width - len(filled))
    return f"[{filled}{empty}]"

async def setup(bot, user):
    ensure_data_dir()

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def hack_handler(event):
        """Handle hack simulation command"""
        current_prefix = get_live_prefix()
        msg = (event.text or '').strip()
        
        # Check command format
        if current_prefix:
            if not msg.startswith(f"{current_prefix}hack"):
                return
            target = msg[len(current_prefix)+4:].strip()
        else:
            if not msg.lower().startswith("hack"):
                return
            target = msg[4:].strip()

        # Check if this is a reply
        if not target and event.is_reply:
            reply_msg = await event.get_reply_message()
            target = reply_msg.sender.first_name or "Unknown"
        
        if not target:
            await event.reply("⚠️ Gunakan: [prefix]hack <target> atau reply pesan dengan [prefix]hack")
            return

        # Delete the original command
        try:
            await event.delete()
        except:
            pass

        # Initial message
        progress_msg = await event.respond("""
الله أكبر
----------------------------------------------------------------------
```hack_berjalan....................```
```[░░░░░░░░░░░░░░░░░░░░] 0%```
        """.strip())

        # Hacking stages
        stages = [
            (5, "Memulai sistem..."),
            (10, "Mengumpulkan informasi dasar"),
            (20, "Memindai jaringan"),
            (30, "Mencari kerentanan"),
            (40, "Memecahkan enkripsi"),
            (50, "Menyusup ke sistem utama"),
            (60, "Mengakses database"),
            (70, "Mengunduh data sensitif"),
            (80, "Mengekstrak file penting"),
            (90, "Membersihkan jejak"),
            (100, "Finalisasi operasi")
        ]

        current_stage = 0
        current_text = "Memulai..."

        # Simulate hacking progress
        for percent in range(1, 101):
            # Update stage text
            if current_stage < len(stages) and percent >= stages[current_stage][0]:
                current_text = stages[current_stage][1]
                current_stage += 1

            # Update progress
            progress_bar = generate_progress_bar(percent)
            await progress_msg.edit(f"""
الله أكبر
----------------------------------------------------------------------
```hack_berjalan....................```
```{progress_bar} {percent}%```
🔍 {current_text}
            """.strip())
            await asyncio.sleep(random.uniform(0.05, 0.15))

        # Generate fake results
        fake_data = {
            'email': f"{target.lower().replace(' ', '_')}_{random.randint(100,999)}@mail.com",
            'password': ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10)),
            'ip': '.'.join(str(random.randint(1, 255)) for _ in range(4)),
            'files': [
                "chat_history.db",
                "photos_backup.zip",
                "contacts.json",
                "browser_history.txt"
            ]
        }

        # Final report
        await progress_msg.edit(f"""
الله أكبر
----------------------------------------------------------------------
✅ **Hack selesai!**

```[████████████████████] 100%```

📌 Target: {target}
📧 Email: {fake_data['email']}
🔑 Password: {fake_data['password']}
🌐 IP: {fake_data['ip']}
📂 File yang didapat:
  - {fake_data['files'][0]}
  - {fake_data['files'][1]}
  - {fake_data['files'][2]}
  - {fake_data['files'][3]}
        """.strip())