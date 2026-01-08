# plugins/alfread.py (Perbaikan)
from telethon import events, errors, Button
from config import OWNER_ID
import asyncio
import logging
import re

# Setup logger
logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

pending = {}
MAX_RETRIES = 3  # Maksimal percobaan koneksi

def setup(bot, user):
    async def send_code_with_retry(phone):
        """Fungsi untuk mengirim kode dengan mekanisme retry"""
        for attempt in range(MAX_RETRIES):
            try:
                return await user.send_code_request(phone)
            except (errors.SecurityError, errors.RPCError) as e:
                logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES} failed: {str(e)}")
                if attempt < MAX_RETRIES-1:
                    await asyncio.sleep(2)  # Jeda 2 detik antar percobaan
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise
        raise Exception("Gagal setelah 3 percobaan")

    @bot.on(events.NewMessage(pattern=r'^/connect(?:\s+(\+\d{8,15}))?$'))
    async def connect_handler(event):
        """Handler untuk menghubungkan userbot"""
        try:
            logger.info(f"Connect request dari {event.sender_id}")
            
            if event.sender_id != OWNER_ID:
                await event.reply("<blockquote>🚫 Akses ditolak!</blockquote>", parse_mode="html")
                return

            # Check connection status
            if not user.is_connected():
                await user.connect()
                logger.info("User client terkoneksi")

            # Check if already logged in
            if await user.is_user_authorized():
                await event.reply(
                    "<blockquote>ℹ️ Anda sudah login sebagai UserBot!</blockquote>\n\n"
                    "<blockquote>Gunakan /reconnect jika perlu menghubungkan ulang akun</blockquote>",
                    parse_mode="html"
                )
                return

            # Check if phone number was provided
            phone_match = event.pattern_match.group(1)
            if phone_match:
                phone = phone_match.strip()
                await process_phone_number(event, phone)
            else:
                # Send phone number request with smaller share button
                share_button = [[Button.request_phone("📱 Share Number", resize=True)]]
                await event.reply(
                    "<blockquote>📲 Silakan bagikan nomor telepon Anda:</blockquote>\n\n"
                    "<blockquote>Gunakan tombol di bawah untuk membagikan nomor atau ketik /connect +62xxxxxxx</blockquote>",
                    parse_mode="html",
                    buttons=share_button
                )

        except errors.PhoneNumberInvalidError:
            await event.reply("<blockquote>❌ Format nomor tidak valid!</blockquote>", parse_mode="html")
        except Exception as e:
            logger.error(f"Error koneksi: {str(e)}", exc_info=True)
            await event.reply("<blockquote>⚠️ Terjadi kesalahan internal</blockquote>", parse_mode="html")

    async def process_phone_number(event, phone):
        """Process the phone number for login"""
        logger.info(f"Memproses nomor: {phone}")
        
        try:
            # Pastikan koneksi aktif
            if not user.is_connected():
                await user.connect()
                logger.info("User client terkoneksi")

            # Mengirim kode dengan retry mechanism
            result = await send_code_with_retry(phone)
            pending[event.chat_id] = {
                'phone': phone,
                'phone_code_hash': result.phone_code_hash,
                'attempts': 0
            }
            
            await event.reply(
                "<blockquote>📲 Kode verifikasi terkirim!</blockquote>\n\n"
                "<blockquote>Silakan balas dengan format: 1 2 3 4 5</blockquote>",
                parse_mode="html"
            )

        except errors.AuthRestartError:
            await event.reply(
                "<blockquote>⚠️ Telegram sedang mengalami masalah internal</blockquote>\n\n"
                "<blockquote>Silakan coba lagi beberapa saat</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            await event.reply(f"<blockquote>⚠️ Gagal mengirim kode: {str(e)}</blockquote>", parse_mode="html")
            if event.chat_id in pending:
                del pending[event.chat_id]

    @bot.on(events.NewMessage(func=lambda e: e.message.contact))
    async def contact_handler(event):
        """Handle shared phone number"""
        if event.sender_id != OWNER_ID:
            return
            
        contact = event.message.contact
        if contact.user_id == event.sender_id:
            await process_phone_number(event, f"+{contact.phone_number}")

    @bot.on(events.NewMessage(pattern=r'^[\d\s]+$'))  # Menerima kombinasi angka dan spasi
    async def code_handler(event):
        """Handler untuk memproses kode OTP langsung"""
        chat_id = event.chat_id
        logger.info(f"Menerima kode di chat {chat_id}")
        
        if chat_id not in pending:
            return  # Tidak ada permintaan aktif
        
        # Ekstrak semua digit dari pesan
        code = ''.join(filter(str.isdigit, event.raw_text))
        if len(code) != 5:
            return  # Bukan kode OTP valid
        
        entry = pending[chat_id]
        logger.info(f"Mencoba login dengan kode: {code}")
        
        try:
            await user.sign_in(
                phone=entry['phone'],
                code=code,
                phone_code_hash=entry['phone_code_hash']
            )
            
            await event.reply("<blockquote>✅ Login berhasil!</blockquote>\n<blockquote>UserBot siap digunakan.</blockquote>", parse_mode="html")
            del pending[chat_id]
            logger.info("Login sukses")

        except errors.SessionPasswordNeededError:
            logger.info("Diperlukan 2FA")
            await event.reply("<blockquote>🔐 Masukkan password 2FA:</blockquote>", parse_mode="html")
            pending[chat_id]['state'] = '2fa'
            
        except errors.PhoneCodeInvalidError:
            entry['attempts'] += 1
            if entry['attempts'] >= 3:
                del pending[chat_id]
                await event.reply("<blockquote>❌ Terlalu banyak percobaan gagal</blockquote>", parse_mode="html")
                logger.warning("Percobaan gagal melebihi batas")
            else:
                await event.reply(
                    f"<blockquote>❌ Kode salah. Percobaan {entry['attempts']}/3</blockquote>\n\n"
                    f"<blockquote>Coba kirim ulang kode: 1 2 3 4 5</blockquote>",
                    parse_mode="html"
                )
                
        except Exception as e:
            logger.error(f"Error kode: {str(e)}", exc_info=True)
            await event.reply("<blockquote>⚠️ Gagal memproses kode</blockquote>", parse_mode="html")

    @bot.on(events.NewMessage(pattern=r'^\d{6,}$'))  # Password minimal 6 digit
    async def twofa_handler(event):
        """Handler untuk 2FA"""
        chat_id = event.chat_id
        if chat_id not in pending or pending[chat_id].get('state') != '2fa':
            return

        password = event.text
        try:
            await user.sign_in(password=password)
            await event.reply("<blockquote>✅ Login 2FA berhasil!</blockquote>", parse_mode="html")
            del pending[chat_id]
            logger.info("2FA sukses")
        except Exception as e:
            logger.error(f"Error 2FA: {str(e)}", exc_info=True)
            await event.reply("<blockquote>❌ Password 2FA salah</blockquote>", parse_mode="html")

    @bot.on(events.NewMessage(pattern=r'^/(status|reconnect)$'))
    async def status_handler(event):
        """Cek status sistem atau reconnect"""
        command = event.pattern_match.group(1)
        
        if command == "reconnect":
            try:
                # Full reconnection process
                if user.is_connected():
                    await user.disconnect()
                
                # Clear any existing session
                await user.start(phone=lambda: '+0000000000')  # Dummy phone to clear
                await user.disconnect()
                
                # Reconnect properly
                await user.connect()
                
                if not await user.is_user_authorized():
                    await event.reply("<blockquote>ℹ️ Silakan login ulang dengan /connect</blockquote>", parse_mode="html")
                else:
                    await event.reply("<blockquote>✅ Berhasil reconnect UserBot!</blockquote>", parse_mode="html")
                return
            except Exception as e:
                await event.reply(f"<blockquote>❌ Gagal reconnect: {str(e)}</blockquote>\n\n<blockquote>Silakan coba /connect untuk login ulang</blockquote>", parse_mode="html")
                return
        
        # Status command
        status_msg = [
            "<blockquote>🔍 Status Sistem</blockquote>",
            f"<blockquote>Koneksi UserBot: {'✅' if user.is_connected() else '❌'}",
            f"Login status: {'✅' if await user.is_user_authorized() else '❌'}",
            f"Pending requests: {len(pending)}",
            f"OTP attempts: {sum([v['attempts'] for v in pending.values()])}</blockquote>"
        ]
        await event.reply('\n'.join(status_msg), parse_mode="html")