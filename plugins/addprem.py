import json
import os
from telethon import events
from config import OWNER_ID

PREMIUM_FILE = 'premium/premium.json'
NOMOR_FILE = 'data/nomor.json'

def load_premium_users():
    try:
        if os.path.exists(PREMIUM_FILE):
            with open(PREMIUM_FILE, 'r') as f:
                return json.load(f)
    except:
        return {"users": []}
    return {"users": []}

def save_premium_users(data):
    with open(PREMIUM_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_nomor():
    try:
        if os.path.exists(NOMOR_FILE):
            with open(NOMOR_FILE, 'r') as f:
                return json.load(f)
    except:
        return {}
    return {}

async def setup(user):
    @user.on(events.NewMessage(pattern=r'^\.addprem(?:\s+(@?\w+))?$', from_users=OWNER_ID))
    async def addprem_handler(event):
        """Add premium user"""
        target = event.pattern_match.group(1)
        if not target:
            if event.is_reply:
                replied = await event.get_reply_message()
                target_id = replied.sender_id
            else:
                await event.reply("❌ **Gunakan:** `.addprem @username` atau reply pesan")
                return
        else:
            if target.startswith('@'):
                try:
                    entity = await user.get_entity(target)
                    target_id = entity.id
                except Exception:
                    await event.reply("❌ **Username tidak ditemukan**")
                    return
            else:
                try:
                    target_id = int(target)
                except ValueError:
                    await event.reply("❌ **ID harus angka atau username**")
                    return

        premium_data = load_premium_users()
        if str(target_id) not in premium_data["users"]:
            premium_data["users"].append(str(target_id))
            save_premium_users(premium_data)

            try:
                await user.send_message(
                    target_id,
                    "🎉 **Anda sekarang pengguna premium!**\n\n"
                    f"Gunakan bot @{BOT_USERNAME2} untuk connect UserBot."
                )
            except Exception:
                pass

            await event.reply(f"✅ **Berhasil menambahkan premium untuk ID {target_id}**")
        else:
            await event.reply("ℹ️ **Pengguna sudah premium**")

    @user.on(events.NewMessage(pattern=r'^\.listprem$', from_users=OWNER_ID))
    async def listprem_handler(event):
        """List premium users"""
        premium_data = load_premium_users()
        users = premium_data.get("users", [])
        
        if not users:
            await event.reply("❌ **Tidak ada pengguna premium**")
            return

        message = "📋 **Daftar Pengguna Premium:**\n\n"
        for user_id in users:
            try:
                entity = await user.get_entity(int(user_id))
                name = entity.first_name
                if entity.last_name:
                    name += f" {entity.last_name}"
                username = f"@{entity.username}" if entity.username else "No Username"
                message += f"• {name} ({username}) - `{user_id}`\n"
            except Exception:
                message += f"• `{user_id}`\n"

        await event.reply(message)

    @user.on(events.NewMessage(pattern=r'^\.disconnect\s+(\d+)$', from_users=OWNER_ID))
    async def admin_disconnect_handler(event):
        """Admin disconnect a user"""
        target_id = int(event.pattern_match.group(1))
        from alfread import delete_connection
        delete_connection(target_id)
        await event.reply(f"✅ **Koneksi untuk user {target_id} telah diputuskan**")

    @user.on(events.NewMessage(pattern=r'^\.ceknomor(?:\s+(\d+))?$', from_users=OWNER_ID))
    async def ceknomor_handler(event):
        """Cek nomor premium user (owner only)"""
        target = event.pattern_match.group(1)
        if not target:
            await event.reply("❌ **Gunakan:** `.ceknomor <user_id>`")
            return
            
        try:
            user_id = int(target)
        except ValueError:
            await event.reply("❌ **User ID harus angka**")
            return
            
        nomor_data = load_nomor()
        nomor = nomor_data.get(str(user_id), "Tidak ada data")
        
        await event.reply(f"📱 **Nomor untuk user {user_id}:** `{nomor}`")