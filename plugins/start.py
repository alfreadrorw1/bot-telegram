# plugins/start.py
from telethon import events, Button
from config import OWNER_ID
import time
import json
import os
import math
from datetime import datetime, timedelta
from plugins.help import FEATURES, FEATURES_LIST, ITEMS_PER_PAGE, TOTAL_PAGES

USER_DATA_DIR = 'data/users'
os.makedirs(USER_DATA_DIR, exist_ok=True)

def get_user_file(user_id):
    return os.path.join(USER_DATA_DIR, f'{user_id}.json')

def load_user_data(user_id):
    try:
        with open(get_user_file(user_id), 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'premium': False,
            'expiry_date': None,
            'prefixes': ['.', '?', '!'],
            'months': 0,
            'subscription_date': None
        }

def save_user_data(user_id, data):
    with open(get_user_file(user_id), 'w') as f:
        json.dump(data, f, indent=4)

async def get_uptime():
    try:
        with open('cache/start_time.txt', 'r') as f:
            start_time = float(f.read())
    except:
        start_time = time.time()
    uptime_sec = time.time() - start_time
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h:{int(minutes)}m:{int(seconds)}s"

async def setup(bot, user):
    main_keyboard = [
        [Button.text('🤖 Mulai Buat Userbot', resize=True)],
        [Button.text('📊 Status Akun', resize=True), 
         Button.text('🔍 Cek Fitur', resize=True)]
    ]

    async def show_feature_page(event, page_num, user_obj):
        start_idx = page_num * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_features = FEATURES_LIST[start_idx:end_idx]
        
        buttons = []
        for i in range(0, len(page_features), 2):
            row = []
            if i < len(page_features):
                row.append(Button.inline(
                    page_features[i].capitalize(), 
                    data=f"start_feature_{page_features[i]}_{page_num}"
                ))
            if i+1 < len(page_features):
                row.append(Button.inline(
                    page_features[i+1].capitalize(), 
                    data=f"start_feature_{page_features[i+1]}_{page_num}"
                ))
            buttons.append(row)
        
        nav_buttons = []
        prev_page = TOTAL_PAGES - 1 if page_num == 0 else page_num - 1
        nav_buttons.append(Button.inline("☜", data=f"start_nav_prev_{prev_page}"))
        nav_buttons.append(Button.inline("★", data="start_nav_delete"))
        next_page = 0 if page_num == TOTAL_PAGES - 1 else page_num + 1
        nav_buttons.append(Button.inline("☞", data=f"start_nav_next_{next_page}"))
        buttons.append(nav_buttons)
        
        user_name = user_obj.first_name
        message = (
            f"╭──「 Daftar Fitur 」\n"
            f"│ • Halaman {page_num+1}/{TOTAL_PAGES}\n"
            f"╰──「 {user_name} 」\n"
            f"```✨ Userbot By AlfreadRorw```"
        )
        
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(message, buttons=buttons)
        else:
            await event.respond(message, buttons=buttons)

    async def show_feature_detail(event, feature, page_num, user_obj):
        user_name = user_obj.first_name
        message = (
            f"╭──「 {feature.capitalize()} 」\n"
            f"│ • {FEATURES[feature]}\n"
            f"╰──「 {user_name} 」\n"
            f"```✨ Userbot By AlfreadRorw```"
        )
        buttons = [[Button.inline("☜ Kembali", data=f"start_nav_back_{page_num}")]]
        await event.edit(message, buttons=buttons)

    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        await event.respond(
            f"```🤖Selamat Datang Ya kntol\n```"
            f"```Saya adalah bot buatan alfread dia gabut makanya gua di buat emang agak laen```\n"
            f"Jika anda ada kendalan silahkan hubungi: @alfreadRorw\n\n"
            f"```Jika punya Saran atau apa Langsng hubungi owner yah terima kasih```",
            buttons=main_keyboard
        )

    @bot.on(events.NewMessage(func=lambda e: e.message.message in ['🤖 Mulai Buat Userbot', '📊 Status Akun', '🔍 Cek Fitur']))
    async def text_button_handler(event):
        user_id = event.sender_id
        msg = event.message.message
        
        if msg == '🤖 Mulai Buat Userbot':
            terms_buttons = [
                [Button.inline('📃 Saya Setuju', 'agree_terms')],
                [Button.inline('🏠 Menu Utama', 'main_menu')]
            ]
            await event.respond(
                "```🤖ᴘʀᴇᴍɪᴜᴍ ᴜʙᴏᴛ - Kebijakan & Ketentuan\n\n"
                "💫 Kebijakan Pengembalian Dana:\n"
                "• 48 jam pengembalian dana\n"
                "• Tidak berlaku setelah menggunakan fitur\n\n"
                "🛟 Dukungan:\n"
                "• Panduan lengkap di @alfreadRorw\n"
                "• Setuju semua risiko dengan melanjutkan```",
                buttons=terms_buttons
            )
        
        elif msg == '📊 Status Akun':
            user_data = load_user_data(user_id)
            uptime = await get_uptime()
            status = "Premium" if user_data['premium'] else "Tidak Aktif"
            expiry = user_data['expiry_date'] or "Belum berlangganan"
            
            response = (
                f"```ᴘʀᴇᴍɪᴜᴍ sᴛᴀᴛᴜs\n"
                f"├ Akun: {status}\n"
                f"├ Tipe: {'Premium' if user_data['premium'] else 'Reguler'}\n"
                f"├ Prefix: {', '.join(user_data['prefixes'])}\n"
                f"├ Kedaluwarsa: {expiry}\n"
                f"└ Uptime: {uptime}```"
            )
            await event.respond(response)
        
        elif msg == '🔍 Cek Fitur':
            await show_feature_page(event, 0, event.sender)

    @bot.on(events.CallbackQuery(data=lambda d: d.startswith(b'start_')))
    async def start_callback_handler(event):
        data = event.data.decode()
        user = await event.get_sender()
        
        if data.startswith("start_feature_"):
            _, _, feature, page = data.split('_', 3)
            await show_feature_detail(event, feature, int(page), user)
            
        elif data.startswith("start_nav_"):
            action = data.split('_')[2]
            if action == "delete":
                await event.delete()
            elif action == "back":
                page = data.split('_')[3]
                await show_feature_page(event, int(page), user)
            elif action in ["prev", "next"]:
                page = data.split('_')[3]
                await show_feature_page(event, int(page), user)
        
        await event.answer()

    @bot.on(events.CallbackQuery(pattern=b'agree_terms'))
    async def terms_handler(event):
        user_id = event.sender_id
        user_data = load_user_data(user_id)
        user_data.update({'months': 0, 'subscription_date': int(time.time())})
        save_user_data(user_id, user_data)
        
        payment_buttons = [
            [Button.inline('➖ 1 Bulan', 'minus_month'),
             Button.inline('➕ 1 Bulan', 'plus_month')],
            [Button.inline('💳 Konfirmasi', 'confirm_payment')],
            [Button.inline('❌ Batal', 'cancel_payment')]
        ]
        
        await event.edit(
            f"```💳 Pembayaran Userbot\n\n"
            f"├ Harga/Bulan: Rp15.000\n"
            f"├ Total Bulan: {user_data['months']}\n"
            f"└ Total: Rp{user_data['months'] * 15000}\n\n"
            "Pilih jumlah bulan dan konfirmasi:```",
            buttons=payment_buttons
        )

    @bot.on(events.CallbackQuery(pattern=b'(plus|minus)_month'))
    async def month_adjust_handler(event):
        user_id = event.sender_id
        action = event.data.decode().split('_')[0]
        user_data = load_user_data(user_id)
        
        if action == 'plus':
            user_data['months'] += 1
        elif action == 'minus' and user_data['months'] > 0:
            user_data['months'] -= 1
        
        save_user_data(user_id, user_data)
        
        await event.edit(
            f"```💳 Pembayaran Userbot\n\n"
            f"├ Harga/Bulan: Rp15.000\n"
            f"├ Total Bulan: {user_data['months']}\n"
            f"└ Total: Rp{user_data['months'] * 15000}\n\n"
            "Pilih jumlah bulan dan konfirmasi```",
            buttons=[
                [Button.inline('➖ 1 Bulan', 'minus_month'),
                 Button.inline('➕ 1 Bulan', 'plus_month')],
                [Button.inline('💳 Konfirmasi', 'confirm_payment')],
                [Button.inline('❌ Batal', 'cancel_payment')]
            ]
        )

    @bot.on(events.CallbackQuery(pattern=b'confirm_payment'))
    async def confirm_payment_handler(event):
        user_id = event.sender_id
        user_data = load_user_data(user_id)
        
        if user_data['months'] < 1:
            await event.answer("Pilih minimal 1 bulan!", alert=True)
            return
        
        try:
            user_entity = await event.client.get_entity(user_id)
            username = f"@{user_entity.username}" if user_entity.username else user_entity.first_name
        except:
            username = "Unknown User"
        
        total_price = user_data['months'] * 15000
        
        owner_buttons = [
            [Button.url("💬 Hubungi User", f"tg://user?id={user_id}")],
            [Button.inline("✅ Konfirmasi Pembayaran", f"confirm_{user_id}")]
        ]
        
        await bot.send_message(
            OWNER_ID,
            f"```🚀 **PEMBELIAN BARU!\n\n"
            f"├ User: {username}\n"
            f"├ ID: `{user_id}`\n"
            f"├ Durasi: {user_data['months']} bulan\n"
            f"└ Total: Rp{total_price}\n\n"
            "Segera proses pembayaran!```",
            buttons=owner_buttons
        )
        
        user_buttons = [
            [Button.url("📘 Panduan Userbot", "https://t.me/alfreadRorw")],
            [Button.url("🛠 Dukungan Teknis", "https://t.me/alfreadRorw")]
        ]
        
        await event.respond(
            "```✅Permintaan pembayaran telah tercatat!\n\n"
            "Owner akan memverifikasi dalam 1x24 jam.\n"
            "Silakan tunggu notifikasi konfirmasi.```",
            buttons=user_buttons
        )
        await event.delete()

    @bot.on(events.CallbackQuery(pattern=r'confirm_\d+'))
    async def owner_confirm_handler(event):
        user_id = int(event.data.decode().split('_')[1])
        user_data = load_user_data(user_id)
        
        sub_date = datetime.now()
        expiry_date = sub_date + timedelta(days=30*user_data['months'])
        
        user_data.update({
            'premium': True,
            'expiry_date': expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        })
        save_user_data(user_id, user_data)
        
        try:
            await bot.send_message(
                user_id,
                f"```🎉 **AKUN PREMIUM AKTIF!**\n\n"
                f"✅ Masa aktif hingga: {expiry_date.strftime('%d-%m-%Y')}\n"
                "Gunakan /help untuk melihat fitur!```"
            )
        except Exception as e:
            print(f"Gagal mengirim notifikasi: {e}")
        
        await event.edit("```✅ Pembayaran dikonfirmasi dan akun diaktifkan!```")

    @bot.on(events.CallbackQuery(pattern=b'cancel_payment'))
    async def cancel_handler(event):
        await event.delete()
        await event.respond("```❌ Pembayaran dibatalkan```", buttons=main_keyboard)