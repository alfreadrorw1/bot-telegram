import os
import json
import asyncio
from telethon import events, Button
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import (
    InputReportReasonSpam, 
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonOther,
    InputReportReasonCopyright,
    InputReportReasonIllegalDrugs,
    InputReportReasonPersonalDetails,
    InputReportReasonGeoIrrelevant
)
from config import OWNER_ID, BOT_USERNAME2

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

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except:
        pass

# Mapping alasan report sesuai dengan tampilan Telegram
REASON_MAPPING = {
    'spam': InputReportReasonSpam(),
    'violence': InputReportReasonViolence(),
    'porn': InputReportReasonPornography(),
    'child': InputReportReasonChildAbuse(),
    'illegal': InputReportReasonIllegalDrugs(),
    'personal': InputReportReasonPersonalDetails(),
    'copyright': InputReportReasonCopyright(),
    'geo': InputReportReasonGeoIrrelevant(),
    'other': InputReportReasonOther()
}

REASON_DISPLAY_NAMES = {
    'spam': "Spam atau penipuan",
    'violence': "Kekerasan",
    'porn': "Konten dewasa ilegal",
    'child': "Pelecehan anak",
    'illegal': "Barang ilegal",
    'personal': "Data pribadi",
    'copyright': "Hak cipta",
    'geo': "Tidak ilegal namun harus diturunkan",
    'other': "Lainnya"
}

REASON_DETAILS = {
    'spam': {
        'phishing': "Phishing",
        'impersonation': "Peniruan/Impersonation",
        'fake_sale': "Penjualan palsu",
        'spam': "Spam"
    }
}

# Store user report states
user_report_states = {}

async def setup(bot, client, user_id):
    """Setup report feature for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage(pattern=f'^({get_prefix(current_user_id)}|/)report$'))
    async def report_handler(event):
        """Handle report command"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        # Check if replying to a message
        if not event.is_reply:
            status = await event.reply(
                "🚫 Balas ke pesan yang ingin dilaporkan!",
                parse_mode="html"
            )
            await asyncio.sleep(3)
            await safe_delete(status)
            await safe_delete(event)
            return

        # Get the replied message
        replied_msg = await event.get_reply_message()
        if not replied_msg:
            status = await event.reply(
                "🚫 Tidak dapat mengambil pesan yang dibalas!",
                parse_mode="html"
            )
            await asyncio.sleep(3)
            await safe_delete(status)
            await safe_delete(event)
            return

        # Store report state
        user_report_states[sender_id] = {
            'replied_msg_id': replied_msg.id,
            'chat_id': event.chat_id,
            'step': 'main_reason'
        }

        # Show main reason selection with proper bot username in callback data
        buttons = []
        row = []
        for reason_key, reason_name in REASON_DISPLAY_NAMES.items():
            # Gunakan BOT_USERNAME2 dalam callback data
            row.append(Button.inline(reason_name, f"report_{BOT_USERNAME2}_{reason_key}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        report_message = await event.reply(
            "**📢 Laporkan**\n\n"
            "Apa yang salah dengan pesan ini?\n\n"
            "Pilih alasan pelaporan:",
            buttons=buttons,
            parse_mode="markdown"
        )
        
        # Simpan ID message untuk edit nanti
        user_report_states[sender_id]['message_id'] = report_message.id
        await safe_delete(event)

    @client.on(events.CallbackQuery(pattern=fr"report_{BOT_USERNAME2}_(.+)"))
    async def report_callback_handler(event):
        """Handle report reason selection"""
        sender_id = event.sender_id
        reason_key = event.pattern_match.group(1).decode()
        
        if sender_id not in user_report_states:
            await event.answer("Sesi report telah berakhir!", alert=True)
            await event.delete()
            return

        user_state = user_report_states[sender_id]
        
        if reason_key == 'spam':
            # Show spam sub-reasons
            user_state['step'] = 'spam_subreason'
            user_state['main_reason'] = reason_key
            
            buttons = []
            for sub_key, sub_name in REASON_DETAILS['spam'].items():
                buttons.append([Button.inline(sub_name, f"spam_{BOT_USERNAME2}_{sub_key}")])
            buttons.append([Button.inline("⬅️ Kembali", f"back_{BOT_USERNAME2}_main")])
            
            await event.edit(
                "**📢 Spam atau penipuan**\n\n"
                "Apa yang salah dengan pesan ini?\n\n"
                "Pilih jenis spam:",
                buttons=buttons,
                parse_mode="markdown"
            )
            
        else:
            # For other reasons, ask for comment
            user_state['step'] = 'comment'
            user_state['main_reason'] = reason_key
            
            await event.edit(
                f"**📢 {REASON_DISPLAY_NAMES[reason_key]}**\n\n"
                "Tambah Komentar (Opsional)\n\n"
                "Mohon bantu kami dengan memaparkan keluhan Anda atas pesan yang dilaporkan.\n\n"
                "Ketik komentar Anda atau kirim tanpa komentar:",
                buttons=[
                    [Button.inline("📨 Kirim Laporan", f"submit_{BOT_USERNAME2}")],
                    [Button.inline("⬅️ Kembali", f"back_{BOT_USERNAME2}_main")]
                ],
                parse_mode="markdown"
            )

    @client.on(events.CallbackQuery(pattern=fr"spam_{BOT_USERNAME2}_(.+)"))
    async def spam_subreason_handler(event):
        """Handle spam sub-reason selection"""
        sender_id = event.sender_id
        sub_reason = event.pattern_match.group(1).decode()
        
        if sender_id not in user_report_states:
            await event.answer("Sesi report telah berakhir!", alert=True)
            await event.delete()
            return

        user_state = user_report_states[sender_id]
        user_state['step'] = 'comment'
        user_state['sub_reason'] = sub_reason
        
        spam_type_name = REASON_DETAILS['spam'][sub_reason]
        
        await event.edit(
            f"**📢 {spam_type_name}**\n\n"
            "Tambah Komentar (Opsional)\n\n"
            "Mohon bantu kami dengan memaparkan keluhan Anda atas pesan yang dilaporkan.\n\n"
            "Ketik komentar Anda atau kirim tanpa komentar:",
            buttons=[
                [Button.inline("📨 Kirim Laporan", f"submit_{BOT_USERNAME2}")],
                [Button.inline("⬅️ Kembali", f"back_{BOT_USERNAME2}_spam")]
            ],
            parse_mode="markdown"
        )

    @client.on(events.CallbackQuery(pattern=fr"back_{BOT_USERNAME2}_main"))
    async def report_back_handler(event):
        """Handle back button from main reason"""
        sender_id = event.sender_id
        
        if sender_id not in user_report_states:
            await event.answer("Sesi report telah berakhir!", alert=True)
            await event.delete()
            return

        # Show main reason selection again
        buttons = []
        row = []
        for reason_key, reason_name in REASON_DISPLAY_NAMES.items():
            row.append(Button.inline(reason_name, f"report_{BOT_USERNAME2}_{reason_key}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        await event.edit(
            "**📢 Laporkan**\n\n"
            "Apa yang salah dengan pesan ini?\n\n"
            "Pilih alasan pelaporan:",
            buttons=buttons,
            parse_mode="markdown"
        )

    @client.on(events.CallbackQuery(pattern=fr"back_{BOT_USERNAME2}_spam"))
    async def spam_back_handler(event):
        """Handle back button from spam sub-reason"""
        sender_id = event.sender_id
        
        if sender_id not in user_report_states:
            await event.answer("Sesi report telah berakhir!", alert=True)
            await event.delete()
            return

        # Show spam sub-reasons again
        buttons = []
        for sub_key, sub_name in REASON_DETAILS['spam'].items():
            buttons.append([Button.inline(sub_name, f"spam_{BOT_USERNAME2}_{sub_key}")])
        buttons.append([Button.inline("⬅️ Kembali", f"back_{BOT_USERNAME2}_main")])
        
        await event.edit(
            "**📢 Spam atau penipuan**\n\n"
            "Apa yang salah dengan pesan ini?\n\n"
            "Pilih jenis spam:",
            buttons=buttons,
            parse_mode="markdown"
        )

    @client.on(events.NewMessage())
    async def report_comment_handler(event):
        """Handle report comment input"""
        sender_id = event.sender_id
        
        if sender_id not in user_report_states:
            return
        
        user_state = user_report_states[sender_id]
        if user_state['step'] != 'comment':
            return

        # Store comment
        user_state['comment'] = event.text
        user_state['step'] = 'ready_to_submit'
        
        # Show confirmation with comment
        main_reason = REASON_DISPLAY_NAMES[user_state['main_reason']]
        comment_preview = user_state['comment'][:50] + "..." if len(user_state['comment']) > 50 else user_state['comment']
        
        # Kirim pesan konfirmasi baru
        confirm_msg = await event.reply(
            f"**📢 Konfirmasi Laporan**\n\n"
            f"**Alasan:** {main_reason}\n"
            f"**Komentar:** {comment_preview}\n\n"
            "Kirim laporan ke Telegram?",
            buttons=[
                [Button.inline("✅ Kirim Laporan", f"submit_{BOT_USERNAME2}")],
                [Button.inline("❌ Batalkan", f"cancel_{BOT_USERNAME2}")]
            ],
            parse_mode="markdown"
        )
        
        # Simpan ID pesan konfirmasi
        user_state['confirm_msg_id'] = confirm_msg.id
        await safe_delete(event)

    @client.on(events.CallbackQuery(pattern=fr"submit_{BOT_USERNAME2}"))
    async def submit_report_handler(event):
        """Handle report submission"""
        sender_id = event.sender_id
        
        if sender_id not in user_report_states:
            await event.answer("Sesi report telah berakhir!", alert=True)
            await event.delete()
            return

        user_state = user_report_states[sender_id]
        
        try:
            # Determine report reason
            reason_key = user_state['main_reason']
            report_reason = REASON_MAPPING[reason_key]
            
            # Prepare report message
            report_message = REASON_DISPLAY_NAMES[reason_key]
            
            if reason_key == 'spam' and 'sub_reason' in user_state:
                spam_type = REASON_DETAILS['spam'][user_state['sub_reason']]
                report_message += f" - {spam_type}"
            
            if 'comment' in user_state and user_state['comment']:
                report_message += f"\nKomentar: {user_state['comment']}"
            
            # Send report to Telegram
            await client(ReportRequest(
                peer=await event.client.get_input_entity(user_state['chat_id']),
                id=[user_state['replied_msg_id']],
                reason=report_reason,
                message=report_message
            ))

            # Send success message
            await event.edit(
                "**✅ Laporan terkirim.**\n\n"
                "Moderator Telegram akan memeriksa laporan Anda. Terima kasih!",
                buttons=None,
                parse_mode="markdown"
            )
            
            # Clean up
            if sender_id in user_report_states:
                del user_report_states[sender_id]
            
        except Exception as e:
            await event.edit(
                f"**❌ Gagal mengirim laporan:**\n`{str(e)}`",
                buttons=None,
                parse_mode="markdown"
            )

    @client.on(events.CallbackQuery(pattern=fr"cancel_{BOT_USERNAME2}"))
    async def cancel_report_handler(event):
        """Handle report cancellation"""
        sender_id = event.sender_id
        
        if sender_id in user_report_states:
            del user_report_states[sender_id]
        
        await event.edit(
            "**❌ Laporan dibatalkan.**",
            buttons=None,
            parse_mode="markdown"
        )

    @client.on(events.NewMessage(pattern=f'^({get_prefix(current_user_id)}|/)reporthelp$'))
    async def report_help_handler(event):
        """Handle report help command"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        help_text = """
**📢 Panduan Report**

**Cara menggunakan:**
• Balas pesan yang ingin dilaporkan
• Ketik `.report` 
• Pilih alasan pelaporan dari menu
• Tambahkan komentar (opsional)
• Kirim laporan ke sistem Telegram

**Alasan yang tersedia:**
• Spam atau penipuan
• Kekerasan  
• Konten dewasa ilegal
• Pelecehan anak
• Barang ilegal
• Data pribadi
• Hak cipta
• Lainnya

Laporan dikirim langsung ke sistem moderasi Telegram.
        """

        help_msg = await event.reply(help_text, parse_mode="markdown")
        await asyncio.sleep(10)
        await safe_delete(help_msg)
        await safe_delete(event)

    # Cleanup expired report sessions
    async def cleanup_report_sessions():
        """Clean up expired report sessions"""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            current_time = asyncio.get_event_loop().time()
            expired_sessions = []
            
            for user_id, state in user_report_states.items():
                # Jika session lebih dari 10 menit, hapus
                if current_time - state.get('created_time', 0) > 600:
                    expired_sessions.append(user_id)
            
            for user_id in expired_sessions:
                del user_report_states[user_id]

    # Start cleanup task
    asyncio.create_task(cleanup_report_sessions())