import json
import os
import time
from datetime import datetime
from telethon import events, Button
from config import OWNER_ID, BOT_USERNAME2

# File untuk menyimpan data statistik
STATS_FILE = 'data/connection_stats.json'

def load_stats():
    """Memuat data statistik koneksi"""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
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

def save_stats(data):
    """Menyimpan data statistik koneksi"""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def format_time(timestamp):
    """Format waktu menjadi string yang mudah dibaca"""
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = timestamp
    return dt.strftime("%Y-%m-%d %H:%M:%S")

async def send_notification(bot, user_id, username, connection_type):
    """Mengirim notifikasi ke owner tentang koneksi baru"""
    stats = load_stats()
    
    # Cek cooldown notifikasi (minimal 30 detik antara notifikasi)
    current_time = time.time()
    if current_time - stats.get("last_notification", 0) < 30:
        return
    
    stats["last_notification"] = current_time
    save_stats(stats)
    
    # Dapatkan info pengguna
    try:
        user_entity = await bot.get_entity(user_id)
        user_name = getattr(user_entity, 'first_name', 'Unknown')
        username = f"@{user_entity.username}" if user_entity.username else "No Username"
    except:
        user_name = "Unknown"
        username = "No Username"
    
    # Buat pesan notifikasi dengan format blockquote
    if connection_type == "connect":
        message = (
            "<blockquote>🔔 <b>NOTIFIKASI KONEKSI BARU</b></blockquote>\n\n"
            f"<blockquote>👤 <b>Pengguna:</b> {user_name}\n"
            f"📱 <b>Username:</b> {username}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"⏰ <b>Waktu:</b> {format_time(datetime.now())}</blockquote>\n\n"
            "<blockquote>✅ <b>Status:</b> Berhasil terhubung ke UserBot</blockquote>"
        )
    else:  # disconnect
        message = (
            "<blockquote>🔔 <b>NOTIFIKASI DISKONEKSI</b></blockquote>\n\n"
            f"<blockquote>👤 <b>Pengguna:</b> {user_name}\n"
            f"📱 <b>Username:</b> {username}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"⏰ <b>Waktu:</b> {format_time(datetime.now())}</blockquote>\n\n"
            "<blockquote>❌ <b>Status:</b> Memutuskan koneksi UserBot</blockquote>"
        )
    
    # Kirim notifikasi ke owner
    try:
        await bot.send_message(OWNER_ID, message, parse_mode="html")
    except Exception as e:
        print(f"Gagal mengirim notifikasi: {e}")

async def get_connection_stats(bot, event=None, user_id=None):
    """Mendapatkan statistik koneksi saat ini"""
    from alfread import active_premium_sessions
    
    stats = load_stats()
    active_count = len(active_premium_sessions)
    
    # Hitung status koneksi
    total_connected = stats.get("total_connections", 0)
    total_disconnected = stats.get("disconnections", 0)
    
    # Buat pesan statistik dengan format blockquote
    message = (
        "<blockquote>📊 <b>STATISTIK KONEKSI USERBOT</b></blockquote>\n\n"
        f"<blockquote>✅ <b>Aktif:</b> {active_count} pengguna\n"
        f"❌ <b>Non-aktif:</b> {total_connected - active_count} pengguna\n"
        f"🔗 <b>Total pernah connect:</b> {total_connected} pengguna\n"
        f"🚫 <b>Total disconnect:</b> {total_disconnected} pengguna</blockquote>\n\n"
        "<blockquote>⏰ <b>Update terakhir:</b> {}</blockquote>".format(format_time(datetime.now()))
    )
    
    # Jika dipanggil dari event, kirim sebagai reply
    if event:
        await event.reply(message, parse_mode="html")
    # Jika dipanggil langsung, kirim ke user_id tertentu
    elif user_id:
        try:
            await bot.send_message(user_id, message, parse_mode="html")
        except Exception as e:
            print(f"Gagal mengirim statistik: {e}")
    
    return message

async def setup(bot, user):
    """Setup notifikasi untuk koneksi userbot"""
    
    @bot.on(events.NewMessage(pattern='/stats'))
    async def stats_handler(event):
        """Handler untuk command /stats"""
        # Hanya owner yang bisa melihat statistik
        if event.sender_id != OWNER_ID:
            return
            
        await get_connection_stats(bot, event=event)
    
    # Simulasi hook untuk mendeteksi koneksi baru
    # Dalam implementasi nyata, ini akan dipanggil dari connect.py
    async def notify_new_connection(user_id, username):
        """Fungsi untuk memberi tahu koneksi baru"""
        # Update statistik
        stats = load_stats()
        stats["total_connections"] = stats.get("total_connections", 0) + 1
        stats["active_connections"] = stats.get("active_connections", 0) + 1
        
        # Tambahkan ke history
        stats["connection_history"].append({
            "user_id": user_id,
            "username": username,
            "type": "connect",
            "timestamp": time.time()
        })
        
        save_stats(stats)
        
        # Kirim notifikasi
        await send_notification(bot, user_id, username, "connect")
    
    # Simulasi hook untuk mendeteksi diskoneksi
    async def notify_disconnection(user_id, username):
        """Fungsi untuk memberi tahu diskoneksi"""
        # Update statistik
        stats = load_stats()
        stats["disconnections"] = stats.get("disconnections", 0) + 1
        stats["active_connections"] = max(stats.get("active_connections", 0) - 1, 0)
        
        # Tambahkan ke history
        stats["connection_history"].append({
            "user_id": user_id,
            "username": username,
            "type": "disconnect",
            "timestamp": time.time()
        })
        
        save_stats(stats)
        
        # Kirim notifikasi
        await send_notification(bot, user_id, username, "disconnect")
    
    # Ekspor fungsi agar bisa dipanggil dari modul lain
    return {
        "notify_new_connection": notify_new_connection,
        "notify_disconnection": notify_disconnection,
        "get_connection_stats": get_connection_stats
    }