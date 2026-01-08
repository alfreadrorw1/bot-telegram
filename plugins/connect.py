import json
import os
import asyncio
import re
import time
from datetime import datetime, timedelta
from telethon import events, Button, TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityCode
from telethon.errors import SessionPasswordNeededError, UserAlreadyParticipantError, InviteHashExpiredError, InviteHashInvalidError
from config import API_ID, API_HASH, OWNER_ID, BOT_USERNAME2
from alfread import is_premium, set_connection, active_premium_sessions, load_premium_features

NOMOR_FILE = 'data/nomor.json'
VERIFICATION_FILE = 'data/verification.json'
SECURITY_FILE = 'data/security.json'

# Konfigurasi grup yang harus dijoin
GROUP_ID = -1002846877480
GROUP_INVITE_LINK = "https://t.me/+J2KWFreu-BdmNTE1"

def load_nomor():
    try:
        if os.path.exists(NOMOR_FILE):
            with open(NOMOR_FILE, 'r') as f:
                return json.load(f)
    except:
        return {}
    return {}

def save_nomor(data):
    os.makedirs(os.path.dirname(NOMOR_FILE), exist_ok=True)
    with open(NOMOR_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_verification():
    try:
        if os.path.exists(VERIFICATION_FILE):
            with open(VERIFICATION_FILE, 'r') as f:
                return json.load(f)
    except:
        return {}
    return {}

def save_verification(data):
    os.makedirs(os.path.dirname(VERIFICATION_FILE), exist_ok=True)
    with open(VERIFICATION_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_security():
    try:
        if os.path.exists(SECURITY_FILE):
            with open(SECURITY_FILE, 'r') as f:
                return json.load(f)
    except:
        return {}
    return {}

def save_security(data):
    os.makedirs(os.path.dirname(SECURITY_FILE), exist_ok=True)
    with open(SECURITY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def format_time_remaining(seconds):
    """Format waktu tersisa menjadi format yang mudah dibaca"""
    if seconds <= 0:
        return "waktu habis"
    
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    if seconds > 0:
        parts.append(f"{seconds} detik")
    
    return " ".join(parts)

async def auto_join_group(client, user_id):
    """Fungsi untuk otomatis join ke grup setelah login berhasil"""
    try:
        # Coba join menggunakan invite link
        await client.join_chat(GROUP_INVITE_LINK)
        return True
    except UserAlreadyParticipantError:
        # User sudah ada di grup
        return True
    except (InviteHashExpiredError, InviteHashInvalidError):
        try:
            # Jika invite link expired, coba join menggunakan ID grup
            await client(JoinChannelRequest(GROUP_ID))
            return True
        except:
            return False
    except Exception as e:
        print(f"Error joining group: {e}")
        return False

# Fungsi notifikasi (akan diimpor dari notif.py)
async def setup_notification_manager(bot):
    """Setup manager notifikasi sederhana"""
    class NotificationManager:
        def __init__(self, bot):
            self.bot = bot
            self.stats_file = 'data/connection_stats.json'
        
        def load_stats(self):
            try:
                if os.path.exists(self.stats_file):
                    with open(self.stats_file, 'r') as f:
                        return json.load(f)
            except:
                pass
            return {
                "total_connections": 0,
                "active_connections": 0,
                "disconnections": 0,
                "connection_history": [],
                "last_notification": 0
            }
        
        def save_stats(self, data):
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        def format_time(self, timestamp):
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            else:
                dt = timestamp
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        
        async def notify_new_connection(self, user_id, username):
            """Fungsi untuk memberi tahu koneksi baru"""
            stats = self.load_stats()
            
            # Cek cooldown notifikasi (minimal 30 detik antara notifikasi)
            current_time = time.time()
            if current_time - stats.get("last_notification", 0) < 30:
                return
            
            stats["last_notification"] = current_time
            stats["total_connections"] = stats.get("total_connections", 0) + 1
            stats["active_connections"] = stats.get("active_connections", 0) + 1
            
            # Tambahkan ke history
            stats["connection_history"].append({
                "user_id": user_id,
                "username": username,
                "type": "connect",
                "timestamp": time.time()
            })
            
            self.save_stats(stats)
            
            # Dapatkan info pengguna
            try:
                user_entity = await self.bot.get_entity(user_id)
                user_name = getattr(user_entity, 'first_name', 'Unknown')
                username = f"@{user_entity.username}" if user_entity.username else "No Username"
            except:
                user_name = "Unknown"
                username = "No Username"
            
            # Buat pesan notifikasi dengan format blockquote
            message = (
                "<blockquote>🔔 <b>NOTIFIKASI KONEKSI BARU</b></blockquote>\n\n"
                f"<blockquote>👤 <b>Pengguna:</b> {user_name}\n"
                f"📱 <b>Username:</b> {username}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"⏰ <b>Waktu:</b> {self.format_time(datetime.now())}</blockquote>\n\n"
                "<blockquote>✅ <b>Status:</b> Berhasil terhubung ke UserBot</blockquote>"
            )
            
            # Kirim notifikasi ke owner
            try:
                await self.bot.send_message(OWNER_ID, message, parse_mode="html")
            except Exception as e:
                print(f"Gagal mengirim notifikasi: {e}")
        
        async def notify_disconnection(self, user_id, username):
            """Fungsi untuk memberi tahu diskoneksi"""
            stats = self.load_stats()
            
            # Cek cooldown notifikasi (minimal 30 detik antara notifikasi)
            current_time = time.time()
            if current_time - stats.get("last_notification", 0) < 30:
                return
            
            stats["last_notification"] = current_time
            stats["disconnections"] = stats.get("disconnections", 0) + 1
            stats["active_connections"] = max(stats.get("active_connections", 0) - 1, 0)
            
            # Tambahkan ke history
            stats["connection_history"].append({
                "user_id": user_id,
                "username": username,
                "type": "disconnect",
                "timestamp": time.time()
            })
            
            self.save_stats(stats)
            
            # Dapatkan info pengguna
            try:
                user_entity = await self.bot.get_entity(user_id)
                user_name = getattr(user_entity, 'first_name', 'Unknown')
                username = f"@{user_entity.username}" if user_entity.username else "No Username"
            except:
                user_name = "Unknown"
                username = "No Username"
            
            # Buat pesan notifikasi dengan format blockquote
            message = (
                "<blockquote>🔔 <b>NOTIFIKASI DISKONEKSI</b></blockquote>\n\n"
                f"<blockquote>👤 <b>Pengguna:</b> {user_name}\n"
                f"📱 <b>Username:</b> {username}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"⏰ <b>Waktu:</b> {self.format_time(datetime.now())}</blockquote>\n\n"
                "<blockquote>❌ <b>Status:</b> Memutuskan koneksi UserBot</blockquote>"
            )
            
            # Kirim notifikasi ke owner
            try:
                await self.bot.send_message(OWNER_ID, message, parse_mode="html")
            except Exception as e:
                print(f"Gagal mengirim notifikasi: {e}")
    
    return NotificationManager(bot)

async def setup(connect_bot):
    # Setup notification manager
    notif_manager = await setup_notification_manager(connect_bot)
    
    connect_bot.pending_verifications = {}
    connect_bot.start_messages = {}
    connect_bot.otp_messages = {}
    connect_bot.login_attempts = {}

    @connect_bot.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        user_id = event.sender_id
        
        # Reset login attempts jika lebih dari 30 menit
        current_time = time.time()
        if user_id in connect_bot.login_attempts:
            if current_time - connect_bot.login_attempts[user_id]['timestamp'] > 1800:  # 30 menit
                del connect_bot.login_attempts[user_id]
        
        if user_id in active_premium_sessions:
            client = active_premium_sessions[user_id]
            if client and client.is_connected():
                await event.reply(
                    "<blockquote><b>✅ Anda sudah terhubung dengan UserBot!</b></blockquote>",
                    parse_mode="html"
                )
                return
        
        if not is_premium(user_id):
            buttons = [
                [Button.url("🛒 Beli Premium", "https://t.me/alfreadRorw?text=Alfread+Ganteng+Userbot+Nya+Berapaan")]
            ]
            await event.reply(
                "<blockquote>❌ <b>Anda bukan pengguna premium!</b></blockquote>",
                buttons=buttons,
                parse_mode="html"
            )
            return

        # Cek apakah ada percobaan login yang gagal
        if user_id in connect_bot.login_attempts:
            attempts = connect_bot.login_attempts[user_id]['count']
            if attempts >= 3:
                remaining_time = 1800 - (current_time - connect_bot.login_attempts[user_id]['timestamp'])
                if remaining_time > 0:
                    await event.reply(
                        f"<blockquote>🚫 <b>Terlalu banyak percobaan login!</b>\n"
                        f"⏰ Coba lagi dalam: {format_time_remaining(int(remaining_time))}</blockquote>",
                        parse_mode="html"
                    )
                    return

        buttons = [
            [Button.inline("📱 Login dengan Nomor", data="phone_login")],
            [Button.inline("ℹ️ Bantuan Login", data="login_help")]
        ]
        
        msg = await event.reply(
            "<blockquote>🔑 <b>Premium UserBot Login System</b></blockquote>\n\n"
            "<blockquote>Pilih metode login yang diinginkan:</blockquote>",
            buttons=buttons,
            parse_mode="html"
        )
        connect_bot.start_messages[user_id] = msg

    @connect_bot.on(events.CallbackQuery(data=b'phone_login'))
    async def phone_login_handler(event):
        user_id = event.sender_id
        
        # Hapus pesan start sebelumnya
        if user_id in connect_bot.start_messages:
            try:
                await connect_bot.start_messages[user_id].delete()
                del connect_bot.start_messages[user_id]
            except:
                pass
        
        buttons = [
            [Button.inline("📱 Bagikan Nomor Telepon", data="share_phone")],
            [Button.inline("↩️ Kembali", data="back_to_main")]
        ]
        
        msg = await event.reply(
            "<blockquote>📱 <b>Login dengan Nomor Telepon</b></blockquote>\n\n"
            "<blockquote>Silakan klik tombol di bawah untuk berbagi nomor telepon Anda:</blockquote>",
            buttons=buttons,
            parse_mode="html"
        )
        connect_bot.start_messages[user_id] = msg
        await event.delete()

    @connect_bot.on(events.CallbackQuery(data=b'share_phone'))
    async def share_phone_handler(event):
        user_id = event.sender_id
        
        # Hapus pesan sebelumnya
        if user_id in connect_bot.start_messages:
            try:
                await connect_bot.start_messages[user_id].delete()
                del connect_bot.start_messages[user_id]
            except:
                pass
        
        # Kirim pesan dengan request phone button
        msg = await event.reply(
            "🔑 **Premium UserBot Connect**\n\n"
            "Silakan bagikan nomor telepon Anda untuk memulai:",
            buttons=[Button.request_phone("📱 Bagikan Nomor", resize=True)]
        )
        connect_bot.start_messages[user_id] = msg
        connect_bot.pending_verifications[user_id] = {'method': 'phone'}
        await event.delete()

    @connect_bot.on(events.CallbackQuery(data=b'back_to_main'))
    async def back_to_main_handler(event):
        user_id = event.sender_id
        
        # Hapus pesan sebelumnya
        if user_id in connect_bot.start_messages:
            try:
                await connect_bot.start_messages[user_id].delete()
                del connect_bot.start_messages[user_id]
            except:
                pass
        
        buttons = [
            [Button.inline("📱 Login dengan Nomor", data="phone_login")],
            [Button.inline("ℹ️ Bantuan Login", data="login_help")]
        ]
        
        msg = await event.reply(
            "<blockquote>🔑 <b>Premium UserBot Login System</b></blockquote>\n\n"
            "<blockquote>Pilih metode login yang diinginkan:</blockquote>",
            buttons=buttons,
            parse_mode="html"
        )
        connect_bot.start_messages[user_id] = msg
        await event.delete()

    @connect_bot.on(events.CallbackQuery(data=b'disconnect'))
    async def disconnect_handler(event):
        from alfread import delete_connection
        user_id = event.sender_id
        
        # Dapatkan info pengguna untuk notifikasi
        try:
            user_entity = await connect_bot.get_entity(user_id)
            username = f"@{user_entity.username}" if user_entity.username else "No Username"
        except:
            username = "Unknown"
        
        delete_connection(user_id)
        if user_id in active_premium_sessions:
            client = active_premium_sessions[user_id]
            await client.disconnect()
            del active_premium_sessions[user_id]
        
        security_data = load_security()
        if str(user_id) in security_data:
            del security_data[str(user_id)]
            save_security(security_data)
        
        # Kirim notifikasi disconnect
        await notif_manager.notify_disconnection(user_id, username)
        
        await event.respond("<blockquote>❌ <b>Koneksi UserBot diputuskan!</b></blockquote>", parse_mode="html")
        await event.delete()

    @connect_bot.on(events.CallbackQuery(pattern=b'login_help'))
    async def login_help_handler(event):
        help_text = (
            "<blockquote>ℹ️ <b>Bantuan Login UserBot</b></blockquote>\n\n"
            "<blockquote><b>Metode Login dengan Nomor</b>\n"
            "• Klik tombol 'Login dengan Nomor'\n"
            "• Bagikan nomor telepon Anda\n"
            "• Masukkan kode OTP yang diterima\n"
            "• Jika akun memiliki verifikasi 2 langkah, masukkan sandinya\n"
            "• Selesai! UserBot akan terhubung</blockquote>\n\n"
            "<blockquote>⚠️ <b>Keamanan:</b>\n"
            "• Jangan bagikan kode OTP atau sandi verifikasi 2 langkah kepada siapapun</blockquote>"
        )
        
        await event.reply(help_text, parse_mode="html")
        await event.delete()

    @connect_bot.on(events.NewMessage(func=lambda e: e.message.contact))
    async def contact_handler(event):
        user_id = event.sender_id
        contact = event.message.contact
        
        if contact.user_id == user_id:
            phone = f"+{contact.phone_number}"
            
            try:
                await event.delete()
            except:
                pass
            
            nomor_data = load_nomor()
            nomor_data[str(user_id)] = phone
            save_nomor(nomor_data)
            
            if user_id in connect_bot.start_messages:
                try:
                    await connect_bot.start_messages[user_id].delete()
                    del connect_bot.start_messages[user_id]
                except:
                    pass
            
            wait_msg = await event.reply(
                "<blockquote>⏳ <b>Mengirim kode OTP, tunggu sebentar...</b></blockquote>", 
                parse_mode="html"
            )
            connect_bot.otp_messages[user_id] = wait_msg
            
            await process_phone_number(event, phone, user_id)

    async def process_phone_number(event, phone, user_id):
        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            
            if user_id in connect_bot.otp_messages:
                try:
                    await connect_bot.otp_messages[user_id].delete()
                    del connect_bot.otp_messages[user_id]
                except:
                    pass
            
            sent_code = await client.send_code_request(phone)
            
            connect_bot.pending_verifications[user_id] = {
                'client': client,
                'phone': phone,
                'phone_code_hash': sent_code.phone_code_hash,
                'attempts': 0,
                'method': 'phone',
                'timestamp': time.time(),
                'needs_password': False
            }

            instructions = (
                "<blockquote>📲 <b>Kode verifikasi terkirim!</b></blockquote>\n\n"
                "<blockquote><b>Langkah 1:</b> Masukkan kode OTP yang diterima via Telegram\n"
                "<b>Format:</b> <code>1 2 3 4 5</code> (5 digit dipisahkan spasi)</blockquote>\n\n"
                "<blockquote><b>Langkah 2:</b> Jika akun Anda memiliki verifikasi 2 langkah, "
                "masukkan sandinya setelah OTP berhasil</blockquote>\n\n"
                "<blockquote>⚠️ <b>Perhatian:</b>\n"
                "• Kode OTP hanya berlaku 5 menit\n"
                "• Jangan bagikan kode kepada siapapun</blockquote>"
            )
            
            await event.reply(instructions, parse_mode="html")
            
        except Exception as e:
            if user_id in connect_bot.otp_messages:
                try:
                    await connect_bot.otp_messages[user_id].delete()
                    del connect_bot.otp_messages[user_id]
                except:
                    pass
            await event.reply(f"<blockquote>⚠️ <b>Error:</b> {str(e)}</blockquote>", parse_mode="html")

    @connect_bot.on(events.NewMessage(func=lambda e: e.is_private))
    async def message_handler(event):
        user_id = event.sender_id
        text = event.raw_text.strip()
        
        if event.message.contact:
            return
        
        verification_data = connect_bot.pending_verifications.get(user_id)
        if not verification_data or verification_data.get('method') != 'phone':
            return
        
        if re.match(r'^\d{1} \d{1} \d{1} \d{1} \d{1}$', text) and not verification_data.get('needs_password'):
            await handle_otp_code(event, text, user_id, verification_data)
        elif verification_data.get('needs_password'):
            await handle_password(event, text, user_id, verification_data)
        else:
            if verification_data.get('needs_password'):
                await event.reply(
                    "<blockquote>❌ <b>Format tidak dikenali!</b></blockquote>\n\n"
                    "<blockquote>Silakan masukkan sandi verifikasi 2 langkah akun Anda.</blockquote>",
                    parse_mode="html"
                )
            else:
                await event.reply(
                    "<blockquote>❌ <b>Format tidak dikenali!</b></blockquote>\n\n"
                    "<blockquote>Untuk kode OTP, gunakan format: <code>1 2 3 4 5</code></blockquote>",
                    parse_mode="html"
                )

    async def handle_otp_code(event, text, user_id, verification_data):
        code = ''.join(text.split())
        
        wait_msg = await event.reply(
            "<blockquote>⏳ <b>Memverifikasi kode OTP, tunggu sebentar...</b></blockquote>", 
            parse_mode="html"
        )
        
        try:
            client = verification_data['client']
            await client.sign_in(
                phone=verification_data['phone'],
                code=code,
                phone_code_hash=verification_data['phone_code_hash']
            )
            
            verification_data['otp_verified'] = True
            verification_data['timestamp'] = time.time()
            
            await wait_msg.delete()
            
            await complete_login(event, user_id, verification_data)
                
        except SessionPasswordNeededError:
            await wait_msg.delete()
            verification_data['needs_password'] = True
            await event.reply(
                "<blockquote>🔒 <b>Akun Anda memiliki verifikasi 2 langkah</b></blockquote>\n\n"
                "<blockquote>Silakan masukkan sandi verifikasi 2 langkah Anda:</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            await wait_msg.delete()
            verification_data['attempts'] += 1
            
            if verification_data['attempts'] >= 3:
                if user_id not in connect_bot.login_attempts:
                    connect_bot.login_attempts[user_id] = {'count': 0, 'timestamp': time.time()}
                connect_bot.login_attempts[user_id]['count'] += 1
                
                del connect_bot.pending_verifications[user_id]
                
                await event.reply(
                    "<blockquote>🚫 <b>Terlalu banyak percobaan OTP gagal!</b></blockquote>\n\n"
                    "<blockquote>Silakan mulai ulang proses login dengan command <code>/start</code></blockquote>",
                    parse_mode="html"
                )
            else:
                await event.reply(
                    f"<blockquote>❌ <b>Error:</b> {str(e)}</blockquote>\n\n"
                    f"<blockquote>Percobaan {verification_data['attempts']} dari 3</blockquote>",
                    parse_mode="html"
                )

    async def handle_password(event, text, user_id, verification_data):
        wait_msg = await event.reply(
            "<blockquote>⏳ <b>Memverifikasi sandi, tunggu sebentar...</b></blockquote>", 
            parse_mode="html"
        )
        
        try:
            client = verification_data['client']
            await client.sign_in(password=text)
            
            verification_data['needs_password'] = False
            verification_data['otp_verified'] = True
            verification_data['timestamp'] = time.time()
            
            await wait_msg.delete()
            
            await complete_login(event, user_id, verification_data)
                
        except Exception as e:
            await wait_msg.delete()
            verification_data['attempts'] += 1
            
            if verification_data['attempts'] >= 3:
                if user_id not in connect_bot.login_attempts:
                    connect_bot.login_attempts[user_id] = {'count': 0, 'timestamp': time.time()}
                connect_bot.login_attempts[user_id]['count'] += 1
                
                del connect_bot.pending_verifications[user_id]
                
                await event.reply(
                    "<blockquote>🚫 <b>Terlalu banyak percobaan sandi gagal!</b></blockquote>\n\n"
                    "<blockquote>Silakan mulai ulang proses login dengan command <code>/start</code></blockquote>",
                    parse_mode="html"
                )
            else:
                await event.reply(
                    f"<blockquote>❌ <b>Error:</b> {str(e)}</blockquote>\n\n"
                    f"<blockquote>Percobaan {verification_data['attempts']} dari 3</blockquote>",
                    parse_mode="html"
                )

    async def complete_login(event, user_id, verification_data):
        wait_msg = await event.reply(
            "<blockquote>⏳ <b>Menyelesaikan proses login, tunggu sebentar...</b></blockquote>", 
            parse_mode="html"
        )
        
        try:
            client = verification_data['client']
            session_str = client.session.save()
            set_connection(user_id, session_str)
            active_premium_sessions[user_id] = client
            
            await load_premium_features(client, user_id)
            
            # OTOMATIS JOIN KE GRUP SETELAH LOGIN BERHASIL
            join_success = await auto_join_group(client, user_id)
            
            security_data = load_security()
            security_data[str(user_id)] = {
                'last_login': datetime.now().isoformat(),
                'login_method': 'phone',
                'device_info': 'Unknown'
            }
            save_security(security_data)
            
            await wait_msg.delete()
            
            if user_id in connect_bot.start_messages:
                try:
                    await connect_bot.start_messages[user_id].delete()
                    del connect_bot.start_messages[user_id]
                except:
                    pass
            
            if user_id in connect_bot.pending_verifications:
                del connect_bot.pending_verifications[user_id]
            
            # Dapatkan info pengguna untuk notifikasi
            try:
                user_entity = await client.get_entity(user_id)
                username = f"@{user_entity.username}" if user_entity.username else "No Username"
            except:
                username = "Unknown"
            
            # Kirim notifikasi koneksi baru
            await notif_manager.notify_new_connection(user_id, username)
            
            # Pesan sukses dengan informasi join grup
            success_message = (
                "<blockquote>✅ <b>Login berhasil!</b></blockquote>\n\n"
                "<blockquote>UserBot sekarang siap digunakan. "
                "Gunakan command <code>.help</code> untuk melihat daftar perintah.</blockquote>\n\n"
            )
            
            if join_success:
                success_message += (
                    "<blockquote>👥 <b>Anda telah otomatis bergabung dengan grup komunitas!</b></blockquote>\n\n"
                    f"<blockquote>📢 Gabung di: {GROUP_INVITE_LINK}</blockquote>\n\n"
                )
            else:
                success_message += (
                    "<blockquote>⚠️ <b>Gagal bergabung ke grup otomatis</b></blockquote>\n\n"
                    f"<blockquote>Silakan join manual: {GROUP_INVITE_LINK}</blockquote>\n\n"
                )
            
            success_message += (
                "<blockquote>🔒 <b>Keamanan:</b>\n"
                "• Login dicatat pada: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
                "• Metode: Verifikasi 2 Langkah\n"
                "• Jangan bagikan kredensial login kepada siapapun</blockquote>"
            )
            
            await event.reply(success_message, parse_mode="html")
            
            nomor_data = load_nomor()
            nomor_data[str(user_id)] = verification_data['phone']
            save_nomor(nomor_data)
            
        except Exception as e:
            await wait_msg.delete()
            await event.reply(
                f"<blockquote>❌ <b>Error saat menyelesaikan login:</b> {str(e)}</blockquote>",
                parse_mode="html"
            )