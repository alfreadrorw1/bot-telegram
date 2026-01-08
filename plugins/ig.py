import instaloader
import os
import re
import json
import asyncio
from telethon import events
from urllib.request import urlretrieve

try:
    from config import OWNER_ID
except ImportError:
    OWNER_ID = 0  # Ganti dengan ID Telegram Anda

def get_live_prefix():
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.') or '.'
    except:
        return '.' 

def save_igp_username(username):
    file_path = 'data/igp.json'
    try:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except (json.JSONDecodeError, FileNotFoundError):
                data = []
        else:
            data = []
        
        if username not in data:
            data.append(username)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving username: {str(e)}")

async def send_profile_info(event, profile, success_msg=None):
    try:
        prof_pic_url = profile.profile_pic_url.replace('s150x150', 's1080x1080')
        filename = f"downloads/{profile.username}_profile.jpg"
        urlretrieve(prof_pic_url, filename)
        
        bio = profile.biography.replace('\n', '\n  ') if profile.biography else "Tidak ada bio"
        
        caption = (
            f"<blockquote>"
            f"<b>✨ PROFIL INSTAGRAM ✨</b>\n\n"
            f"👤 <b>Nama Lengkap:</b> {profile.full_name}\n"
            f"🔗 <b>Username:</b> @{profile.username}\n"
            f"📌 <b>Bio:</b> {bio}\n\n"
            f"<b>📊 Statistik:</b>\n"
            f"  • 🔥 <b>Pengikut:</b> {profile.followers:,}\n"
            f"  • 👥 <b>Mengikuti:</b> {profile.followees:,}\n"
            f"  • 📷 <b>Postingan:</b> {profile.mediacount:,}\n"
            f"  • 🔒 <b>Privat:</b> {'Ya' if profile.is_private else 'Tidak'}\n"
            f"  • ✓ <b>Verifikasi:</b> {'Ya' if profile.is_verified else 'Tidak'}\n"
            f"  • 🌐 <b>Website:</b> {profile.external_url or 'Tidak ada'}\n"
            f"</blockquote>"
        )
        
        if success_msg:
            caption = f"<blockquote>{success_msg}</blockquote>\n\n" + caption
        
        await event.client.send_file(
            event.chat_id,
            filename,
            caption=caption,
            parse_mode="html",
            force_document=False
        )
        await event.delete()
    except Exception as e:
        await event.edit(f"<blockquote>❌ <b>Gagal menampilkan profil:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

async def setup(bot, user):
    os.makedirs('downloads', exist_ok=True)
    os.makedirs('cache', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    L = instaloader.Instaloader(
        sleep=True,
        quiet=True,
        user_agent="Mozilla/5.0 (Linux; Android 10; SM-A305F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36"
    )

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def insta_handler(event):
        msg = (event.text or '').strip()
        prefix = get_live_prefix()
        actual_prefix = prefix if prefix != "no" else ""
        
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            msg = reply_msg.text or ''

        pattern = rf"^{re.escape(actual_prefix)}(igp|ighelp|iglist|iglogin|igclear|igc)\s*(.*)" if actual_prefix else r"^(igp|ighelp|iglist|iglogin|igclear|igc)\s*(.*)"
        match = re.match(pattern, msg, re.IGNORECASE)
        
        if not match:
            return

        command = match.group(1).lower()
        content = match.group(2).strip()

        try:
            if command == "ighelp":
                help_msg = (
                    "<blockquote>"
                    "<b>📷 Instagram Tools</b>\n\n"
                    f"<code>{actual_prefix}iglogin username,password</code> - Login ke akun IG\n"
                    f"<code>{actual_prefix}igp [@username/reply]</code> - Lihat info profil\n"
                    f"<code>{actual_prefix}iglist</code> - Tampilkan riwayat pencarian\n"
                    f"<code>{actual_prefix}igclear</code> atau <code>{actual_prefix}igc @username</code> - Hapus username dari riwayat\n"
                    "\n<b>🔍 Fitur:</b>\n"
                    "• Dapatkan info profil lengkap\n"
                    "• Simpan riwayat pencarian\n"
                    "• Login dengan sesi IG\n"
                    "</blockquote>"
                )
                await event.edit(help_msg, parse_mode="html")
                return
                
            elif command == "igp":
                if event.is_reply:
                    reply_msg = await event.get_reply_message()
                    content = reply_msg.text or ''
                
                match_username = re.search(r'@?([a-zA-Z0-9_.]+)', content)
                if not match_username:
                    return await event.edit("<blockquote>❌ <b>Format username tidak valid!</b></blockquote>", parse_mode="html")
                
                target_username = match_username.group(1)
                await event.edit(f"<blockquote>🔍 <b>Mencari @{target_username}...</b></blockquote>", parse_mode="html")
                
                try:
                    profile = instaloader.Profile.from_username(L.context, target_username)
                    save_igp_username(profile.username)
                    await send_profile_info(event, profile)
                except instaloader.exceptions.ProfileNotExistsException:
                    await event.edit("<blockquote>❌ <b>Profil tidak ditemukan!</b></blockquote>", parse_mode="html")
                except Exception as e:
                    await event.edit(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

            elif command in ["igclear", "igc"]:
                if not content:
                    return await event.edit(f"<blockquote>❌ <b>Format salah!</b> Gunakan: <code>{actual_prefix}{command} @username</code></blockquote>", parse_mode="html")
                
                match_username = re.search(r'@?([a-zA-Z0-9_.]+)', content)
                if not match_username:
                    return await event.edit("<blockquote>❌ <b>Format username tidak valid!</b></blockquote>", parse_mode="html")
                
                target_username = match_username.group(1)
                
                try:
                    if not os.path.exists('data/igp.json'):
                        return await event.edit("<blockquote>📁 <b>Belum ada data yang tersimpan!</b></blockquote>", parse_mode="html")
                    
                    with open('data/igp.json', 'r') as f:
                        try:
                            usernames = json.load(f)
                            if not isinstance(usernames, list):
                                usernames = []
                        except json.JSONDecodeError:
                            usernames = []
                    
                    if target_username not in usernames:
                        return await event.edit(f"<blockquote>❌ <b>@{target_username} tidak ditemukan dalam riwayat!</b></blockquote>", parse_mode="html")
                    
                    # Remove the username
                    usernames = [u for u in usernames if u != target_username]
                    
                    with open('data/igp.json', 'w') as f:
                        json.dump(usernames, f, indent=2)
                    
                    await event.edit(f"<blockquote>✅ <b>@{target_username} berhasil dihapus dari riwayat!</b></blockquote>", parse_mode="html")
                    
                except Exception as e:
                    await event.edit(f"<blockquote>❌ <b>Gagal menghapus username:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

            elif command == "iglogin":
                if ',' not in content:
                    return await event.edit(f"<blockquote>❌ <b>Format salah!</b> Gunakan: <code>{actual_prefix}iglogin username,password</code></blockquote>", parse_mode="html")
                
                username, password = content.split(',', 1)
                username = username.strip()
                password = password.strip()
                
                await event.edit(f"<blockquote>🔐 <b>Mencoba login ke @{username}...</b></blockquote>", parse_mode="html")
                
                try:
                    # Try to load existing session first
                    try:
                        L.load_session_from_file(username)
                        await event.edit(f"<blockquote>✅ <b>Berhasil login menggunakan sesi yang tersimpan untuk @{username}</b></blockquote>", parse_mode="html")
                    except (FileNotFoundError, instaloader.exceptions.ConnectionException):
                        # If no session exists or it's invalid, perform fresh login
                        L.login(username, password)
                        L.save_session_to_file(filename=username)
                        await event.edit(f"<blockquote>✅ <b>Login berhasil! Sesi disimpan untuk @{username}</b></blockquote>", parse_mode="html")
                    
                    # Test the session by getting own profile
                    profile = instaloader.Profile.from_username(L.context, username)
                    await send_profile_info(event, profile, f"✅ <b>Berhasil login sebagai @{username}</b>")
                    
                except instaloader.exceptions.BadCredentialsException:
                    await event.edit("<blockquote>❌ <b>Login gagal! Username atau password salah.</b></blockquote>", parse_mode="html")
                except instaloader.exceptions.TwoFactorAuthRequiredException:
                    await event.edit("<blockquote>❌ <b>Login membutuhkan verifikasi 2 faktor!</b></blockquote>", parse_mode="html")
                except Exception as e:
                    await event.edit(f"<blockquote>❌ <b>Error saat login:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

            elif command == "iglist":
                try:
                    if not os.path.exists('data/igp.json'):
                        return await event.edit("<blockquote>📁 <b>Belum ada data yang tersimpan!</b></blockquote>", parse_mode="html")
                    
                    with open('data/igp.json', 'r') as f:
                        try:
                            usernames = json.load(f)
                            if not isinstance(usernames, list):
                                usernames = []
                        except json.JSONDecodeError:
                            usernames = []
                    
                    if not usernames:
                        await event.edit("<blockquote>📭 <b>Daftar pencarian kosong!</b></blockquote>", parse_mode="html")
                    else:
                        response = (
                            "<blockquote>"
                            "<b>🔍 Riwayat Pencarian IG:</b>\n\n" + 
                            "\n".join([f"▫️ @{username}" for username in usernames[-20:]]) +
                            "</blockquote>"
                        )
                        await event.edit(response, parse_mode="html")
                        
                except Exception as e:
                    await event.edit(f"<blockquote>❌ <b>Gagal membaca data:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

        except Exception as e:
            await event.edit(f"<blockquote>⚠️ <b>Error sistem:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")