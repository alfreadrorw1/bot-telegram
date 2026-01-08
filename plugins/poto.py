# plugins/yaudahpoto.py
import os
import json
import time
import asyncio
import math
from telethon import events, Button
from telethon.tl.types import InputPeerUser
from config import OWNER_ID, BOT_USERNAME

# File configuration
CONFIG_DIR = 'data/users'
PHOTO_DATA_FILE = os.path.join(CONFIG_DIR, 'photo_data.json')
PREFIX_FILE = os.path.join('data', 'prefix.json')

def get_live_prefix():
    """Get current prefix directly from file with caching"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

def load_photo_data():
    """Load photo data from file"""
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            
        if os.path.exists(PHOTO_DATA_FILE):
            with open(PHOTO_DATA_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, KeyError):
        pass
    return {"photos": [], "user_access": {}}

def save_photo_data(data):
    """Save photo data to file"""
    with open(PHOTO_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_photo_markup(user_id, photo_index, total_photos, current_page=0):
    buttons = [
        [
            Button.inline("««", data=f"prev_photo_{user_id}_{photo_index}_{current_page}"),
            Button.inline(f"{photo_index+1}/{total_photos}", data="photo_count"),
            Button.inline("»»", data=f"next_photo_{user_id}_{photo_index}_{current_page}")
        ],
        [Button.inline("⁠メ", data=f"close_photo_{user_id}")]
    ]
    return buttons

async def setup(bot, user):
    photo_data = load_photo_data()

    # Inline handler (BOT)
    @bot.on(events.InlineQuery)
    async def inline_handler(event):
        if event.text and event.text.strip().startswith("poto"):
            user_id = event.sender_id
            if str(user_id) not in photo_data["user_access"] or not photo_data["user_access"][str(user_id)]:
                result = event.builder.article(
                    title="❌ Tidak ada foto",
                    description="Anda belum menambahkan foto apapun",
                    text="Anda belum menambahkan foto apapun. Gunakan .addpoto untuk menambahkan foto."
                )
                await event.answer([result])
                return
            
            user_photos = photo_data["user_access"][str(user_id)]
            first_photo_index = user_photos[0]
            photo_info = photo_data["photos"][first_photo_index]
            
            try:
                result = event.builder.photo(
                    file=photo_info["file_path"],
                    buttons=get_photo_markup(user_id, 0, len(user_photos))
                )
                await event.answer([result])
            except Exception as e:
                print(f"Error in poto inline_handler: {e}")

    # Add Photo Command (mengikuti pola prefix)
    @user.on(events.NewMessage(outgoing=True))
    async def add_photo_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        is_addpoto_cmd = False
        
        if current_prefix == "no":
            if msg.lower().startswith("addpoto"):
                is_addpoto_cmd = True
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd.startswith("addpoto"):
                    is_addpoto_cmd = True
        
        if not is_addpoto_cmd or not event.is_reply:
            return
            
        user_id = event.sender_id
        if str(user_id) not in photo_data["user_access"]:
            photo_data["user_access"][str(user_id)] = []
        
        reply_msg = await event.get_reply_message()
        if not reply_msg.media:
            await event.edit("❌ Pesan yang di-reply bukan gambar!")
            return
        
        try:
            # Download photo
            photo_path = await user.download_media(
                reply_msg.media, 
                file=f'cache/photo_{user_id}_{len(photo_data["photos"])}.jpg'
            )
            
            # Add to data
            photo_data["photos"].append({
                "file_path": photo_path,
                "owner_id": user_id,
                "date_added": int(time.time())
            })
            
            # Update user access
            photo_data["user_access"][str(user_id)].append(len(photo_data["photos"]) - 1)
            
            save_photo_data(photo_data)
            await event.edit(f"✅ Foto berhasil ditambahkan! (Total: {len(photo_data['user_access'][str(user_id)])})")
        except Exception as e:
            await event.edit(f"❌ Gagal menambahkan foto: {str(e)}")

    # Show Photos Command (mengikuti pola prefix)
    @user.on(events.NewMessage(outgoing=True))
    async def show_photos_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        is_poto_cmd = False
        
        if current_prefix == "no":
            if msg.lower() == "poto":
                is_poto_cmd = True
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd == "poto":
                    is_poto_cmd = True
        
        if not is_poto_cmd:
            return
            
        user_id = event.sender_id
        if str(user_id) not in photo_data["user_access"] or not photo_data["user_access"][str(user_id)]:
            await event.edit("❌ Anda belum menambahkan foto apapun!")
            return
        
        try:
            await event.delete()
            result = await user.inline_query(BOT_USERNAME, "poto")
            if result:
                await result[0].click(event.chat_id)
        except Exception as e:
            print(f"Error in poto_command_handler: {e}")
            await event.respond("⚠️ Gagal memunculkan foto")

    # Delete Photo Command (mengikuti pola prefix)
    @user.on(events.NewMessage(outgoing=True))
    async def delete_photo_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        is_delpoto_cmd = False
        input_num = ""
        
        if current_prefix == "no":
            if msg.lower().startswith("delpoto"):
                is_delpoto_cmd = True
                input_num = msg[7:].strip()
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd.startswith("delpoto"):
                    is_delpoto_cmd = True
                    input_num = cmd[7:].strip()
        
        if not is_delpoto_cmd:
            return
            
        user_id = event.sender_id
        if not input_num:
            await event.edit("❌ Harap sertakan nomor foto yang ingin dihapus!")
            return
        
        try:
            photo_num = int(input_num) - 1  # Convert to 0-based index
            if str(user_id) not in photo_data["user_access"]:
                await event.edit("❌ Anda belum menambahkan foto apapun!")
                return
            
            user_photos = photo_data["user_access"][str(user_id)]
            if photo_num < 0 or photo_num >= len(user_photos):
                await event.edit("❌ Nomor foto tidak valid!")
                return
            
            # Dapatkan index sebenarnya di photo_data["photos"]
            actual_index = user_photos[photo_num]
            
            # Hapus file fisik
            try:
                os.remove(photo_data["photos"][actual_index]["file_path"])
            except:
                pass
            
            # Hapus dari daftar user
            user_photos.pop(photo_num)
            
            # Hapus dari daftar utama jika tidak ada user lain yang mengakses
            is_used = False
            for user_photos_list in photo_data["user_access"].values():
                if actual_index in user_photos_list:
                    is_used = True
                    break
            
            if not is_used:
                photo_data["photos"].pop(actual_index)
                # Perbaiki index untuk user lain
                for uid, photos_list in photo_data["user_access"].items():
                    photo_data["user_access"][uid] = [
                        idx - 1 if idx > actual_index else idx 
                        for idx in photos_list
                    ]
            
            save_photo_data(photo_data)
            await event.edit(f"✅ Foto #{input_num} berhasil dihapus!")
        except Exception as e:
            await event.edit(f"❌ Gagal menghapus foto: {str(e)}")

    # Button Callback Handler (BOT)
    @bot.on(events.CallbackQuery(pattern=r'prev_photo_(\d+)_(\d+)_(\d+)'))
    async def prev_photo_handler(event):
        try:
            user_id = int(event.pattern_match.group(1))
            current_index = int(event.pattern_match.group(2))
            current_page = int(event.pattern_match.group(3))
            
            if event.sender_id != user_id and event.sender_id != OWNER_ID:
                await event.answer("❌ Udah di bilangin lu bukan Owner!", alert=True)
                return
            
            user_photos = photo_data["user_access"].get(str(user_id), [])
            if not user_photos:
                await event.answer("❌ Tidak ada foto yang tersedia!", alert=True)
                return
            
            current_pos = user_photos.index(current_index)
            new_pos = current_pos - 1 if current_pos > 0 else len(user_photos) - 1
            new_index = user_photos[new_pos]
            
            # Edit pesan dengan foto baru
            photo_info = photo_data["photos"][new_index]
            buttons = get_photo_markup(user_id, new_pos, len(user_photos), current_page)
            
            await event.edit(
                file=photo_info["file_path"],
                buttons=buttons
            )
            await event.answer()
        except Exception as e:
            await event.answer(f"❌ Error: {str(e)}", alert=True)

    @bot.on(events.CallbackQuery(pattern=r'next_photo_(\d+)_(\d+)_(\d+)'))
    async def next_photo_handler(event):
        try:
            user_id = int(event.pattern_match.group(1))
            current_index = int(event.pattern_match.group(2))
            current_page = int(event.pattern_match.group(3))
            
            if event.sender_id != user_id and event.sender_id != OWNER_ID:
                await event.answer("❌ lu bukan owner kontol", alert=True)
                return
            
            user_photos = photo_data["user_access"].get(str(user_id), [])
            if not user_photos:
                await event.answer("❌ Tidak ada foto yang tersedia!", alert=True)
                return
            
            current_pos = user_photos.index(current_index)
            new_pos = current_pos + 1 if current_pos < len(user_photos) - 1 else 0
            new_index = user_photos[new_pos]
            
            # Edit pesan dengan foto baru
            photo_info = photo_data["photos"][new_index]
            buttons = get_photo_markup(user_id, new_pos, len(user_photos), current_page)
            
            await event.edit(
                file=photo_info["file_path"],
                buttons=buttons
            )
            await event.answer()
        except Exception as e:
            await event.answer(f"❌ Error: {str(e)}", alert=True)

    @bot.on(events.CallbackQuery(pattern=r'close_photo_(\d+)'))
    async def close_photo_handler(event):
        try:
            user_id = int(event.pattern_match.group(1))
            if event.sender_id == user_id or event.sender_id == OWNER_ID:
                await event.delete()
        except:
            await event.answer("❌ Gagal menutup", alert=True)

    @bot.on(events.CallbackQuery(pattern=r'photo_count'))
    async def photo_count_handler(event):
        await event.answer()