import json
import os
from telethon import events
from config import OWNER_ID

PREMIUM_FILE = 'premium/premium.json'
NOMOR_FILE = 'data/nomor.json'

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
        with open(PREMIUM_FILE, 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return False

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

async def setup(bot, client, user_id):
    """Setup admin commands for owner only"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def admin_handler(event):
        """Handle admin commands (owner only)"""
        # Check if user is owner
        if event.sender_id != OWNER_ID:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # Helper function to check commands
        def is_command(cmd):
            return msg.startswith(f"{current_prefix}{cmd}")

        # ADD PREMIUM command
        if is_command("addprem"):
            target = msg[len(current_prefix)+7:].strip()
            if not target:
                if event.is_reply:
                    replied = await event.get_reply_message()
                    target_id = replied.sender_id
                else:
                    await event.reply("<blockquote>❌ Gunakan: <code>.addprem @username</code> atau reply pesan</blockquote>", parse_mode="html")
                    return
            else:
                if target.startswith('@'):
                    try:
                        entity = await client.get_entity(target)
                        target_id = entity.id
                    except Exception:
                        await event.reply("<blockquote>❌ Username tidak ditemukan</blockquote>", parse_mode="html")
                        return
                else:
                    try:
                        target_id = int(target)
                    except ValueError:
                        await event.reply("<blockquote>❌ ID harus angka atau username</blockquote>", parse_mode="html")
                        return

            premium_data = load_premium_users()
            if str(target_id) not in premium_data["users"]:
                premium_data["users"].append(str(target_id))
                save_premium_users(premium_data)

                try:
                    await client.send_message(
                        target_id,
                        "<blockquote>🎉 Anda sekarang pengguna premium!\nBot : @Alfreadprem_bot\nGunakan bot untuk connect UserBot.</blockquote>",
                        parse_mode="html"
                    )
                except Exception:
                    pass

                await event.reply(f"<blockquote>✅ Sukses</blockquote>", parse_mode="html")
            else:
                await event.reply("<blockquote>ℹ️ Pengguna sudah premium</blockquote>", parse_mode="html")

        # PVADDPREM command - Add premium untuk semua anggota grup
        elif is_command("pvaddprem"):
            if not event.is_group and not event.is_channel:
                await event.reply("<blockquote>❌ Command ini hanya bekerja di grup/channel</blockquote>", parse_mode="html")
                return

            processing_msg = await event.reply("<blockquote>🔄 <b>Memproses semua anggota grup...</b></blockquote>", parse_mode="html")
            
            premium_data = load_premium_users()
            added_count = 0
            already_premium_count = 0
            error_count = 0
            
            try:
                async for member in client.iter_participants(event.chat_id):
                    # Skip bots dan diri sendiri
                    if getattr(member, 'bot', False) or getattr(member, 'is_self', False):
                        continue
                    
                    user_id_str = str(member.id)
                    
                    if user_id_str not in premium_data["users"]:
                        premium_data["users"].append(user_id_str)
                        added_count += 1
                        
                        # Kirim notifikasi ke user yang berhasil ditambahkan
                        try:
                            await client.send_message(
                                member.id,
                                "<blockquote>🎉 Anda sekarang pengguna premium!\nBot : @Alfreadprem_bot\nGunakan bot untuk connect UserBot.</blockquote>",
                                parse_mode="html"
                            )
                        except Exception:
                            pass  # User mungkin tidak mengizinkan DM
                    else:
                        already_premium_count += 1
                
                save_premium_users(premium_data)
                
                result_message = (
                    f"<blockquote>✅ <b>Proses PVADDPREM Selesai!</b></blockquote>\n\n"
                    f"<blockquote>📊 <b>Hasil:</b>\n"
                    f"• ✅ Ditambahkan: {added_count} user\n"
                    f"• ℹ️ Sudah premium: {already_premium_count} user\n"
                    f"• ❌ Error: {error_count} user</blockquote>\n\n"
                    f"<blockquote>🎯 <b>Total user di grup:</b> {added_count + already_premium_count + error_count}</blockquote>"
                )
                
                await processing_msg.edit(result_message, parse_mode="html")
                
            except Exception as e:
                await processing_msg.edit(f"<blockquote>❌ <b>Error:</b> {str(e)}</blockquote>", parse_mode="html")

        # DELETE PREMIUM command
        elif is_command("delprem"):
            target = msg[len(current_prefix)+7:].strip()
            if not target:
                if event.is_reply:
                    replied = await event.get_reply_message()
                    target_id = replied.sender_id
                else:
                    await event.reply("<blockquote>❌ Gunakan: <code>.delprem @username</code> atau reply pesan</blockquote>", parse_mode="html")
                    return
            else:
                if target.startswith('@'):
                    try:
                        entity = await client.get_entity(target)
                        target_id = entity.id
                    except Exception:
                        await event.reply("<blockquote>❌ Username tidak ditemukan</blockquote>", parse_mode="html")
                        return
                else:
                    try:
                        target_id = int(target)
                    except ValueError:
                        await event.reply("<blockquote>❌ ID harus angka atau username</blockquote>", parse_mode="html")
                        return

            premium_data = load_premium_users()
            if str(target_id) in premium_data["users"]:
                premium_data["users"].remove(str(target_id))
                save_premium_users(premium_data)

                try:
                    await client.send_message(
                        target_id,
                        "<blockquote>⚠️ Status premium Anda telah dihapus!\n\nAnda tidak lagi memiliki akses premium.</blockquote>",
                        parse_mode="html"
                    )
                except Exception:
                    pass

                await event.reply(f"<blockquote>✅ Sukses</blockquote>", parse_mode="html")
            else:
                await event.reply("<blockquote>ℹ️ Pengguna bukan premium</blockquote>", parse_mode="html")

        # LIST PREMIUM command
        elif is_command("listprem"):
            premium_data = load_premium_users()
            users = premium_data.get("users", [])
            
            if not users:
                await event.reply("<blockquote>❌ Tidak ada pengguna premium</blockquote>", parse_mode="html")
                return

            message = "<blockquote>📋 Daftar Pengguna Premium:</blockquote>\n\n"
            for user_id in users:
                try:
                    entity = await client.get_entity(int(user_id))
                    name = entity.first_name
                    if entity.last_name:
                        name += f" {entity.last_name}"
                    username = f"@{entity.username}" if entity.username else "No Username"
                    message += f"<blockquote>• {name} ({username}) - <code>{user_id}</code></blockquote>\n"
                except Exception:
                    message += f"<blockquote>• <code>{user_id}</code></blockquote>\n"

            await event.reply(message, parse_mode="html")

        # DISCONNECT command
        elif is_command("disconnect"):
            target = msg[len(current_prefix)+10:].strip()
            if not target:
                await event.reply("<blockquote>❌ Gunakan: <code>.disconnect user_id</code></blockquote>", parse_mode="html")
                return
                
            try:
                target_id = int(target)
            except ValueError:
                await event.reply("<blockquote>❌ User ID harus angka</blockquote>", parse_mode="html")
                return
                
            # Import and call delete_connection function
            try:
                from alfread import delete_connection
                delete_connection(target_id)
                await event.reply(f"<blockquote>✅ Koneksi untuk user <code>{target_id}</code> telah diputuskan</blockquote>", parse_mode="html")
            except Exception as e:
                await event.reply(f"<blockquote>❌ Error: {str(e)}</blockquote>", parse_mode="html")

        # CEK NOMOR command
        elif is_command("ceknomor"):
            target = msg[len(current_prefix)+8:].strip()
            if not target:
                await event.reply("<blockquote>❌ Gunakan: <code>.ceknomor user_id</code></blockquote>", parse_mode="html")
                return
                
            try:
                user_id = int(target)
            except ValueError:
                await event.reply("<blockquote>❌ User ID harus angka</blockquote>", parse_mode="html")
                return
                
            nomor_data = load_nomor()
            nomor = nomor_data.get(str(user_id), "Tidak ada data")
            
            await event.reply(f"<blockquote>📱 Nomor untuk user <code>{user_id}</code>: <code>{nomor}</code></blockquote>", parse_mode="html")