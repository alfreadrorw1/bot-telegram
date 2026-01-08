# plugins/premium/zodiak.py
import os
import re
import json
from datetime import datetime
from telethon import events
from config import OWNER_ID

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
        with open('premium/premium.json', 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def get_zodiac_sign(birth_date):
    """Determine zodiac sign from birth date"""
    zodiacs = [
        (12, 22, 1, 19, "Capricorn"),
        (1, 20, 2, 18, "Aquarius"),
        (2, 19, 3, 20, "Pisces"),
        (3, 21, 4, 19, "Aries"),
        (4, 20, 5, 20, "Taurus"),
        (5, 21, 6, 20, "Gemini"),
        (6, 21, 7, 22, "Cancer"),
        (7, 23, 8, 22, "Leo"),
        (8, 23, 9, 22, "Virgo"),
        (9, 23, 10, 22, "Libra"),
        (10, 23, 11, 21, "Scorpio"),
        (11, 22, 12, 21, "Sagittarius")
    ]
    
    birth_month = birth_date.month
    birth_day = birth_date.day
    
    for (start_month, start_day, end_month, end_day, sign) in zodiacs:
        if (birth_month == start_month and birth_day >= start_day) or \
           (birth_month == end_month and birth_day <= end_day):
            if sign == "Capricorn":
                if (birth_month == 12 and birth_day >= 22) or \
                   (birth_month == 1 and birth_day <= 19):
                    return sign
            else:
                return sign
    return "Unknown"

HOROSCOPE_PREDICTIONS = {
    "Aries": "🔥 Hari ini adalah waktu yang tepat untuk mengambil inisiatif!",
    "Taurus": "🌱 Fokus pada stabilitas keuangan dan pertumbuhan pribadi.",
    "Gemini": "💬 Komunikasi akan membawa keberuntungan hari ini.",
    "Cancer": "🏡 Waktunya memperkuat ikatan dengan keluarga tercinta.",
    "Leo": "🎉 Energi kreatifmu sedang tinggi - manfaatkan!",
    "Virgo": "📝 Perhatian pada detail akan membawa hasil terbaik.",
    "Libra": "⚖️ Cari keseimbangan antara pekerjaan dan kehidupan pribadi.",
    "Scorpio": "🕵️♂️ Percayalah pada instingmu yang tajam hari ini.",
    "Sagittarius": "🌍 Petualangan baru menanti di depan mata.",
    "Capricorn": "💼 Fokus pada tujuan karier jangka panjang.",
    "Aquarius": "💡 Ide-ide brilian akan muncul - siapkan catatan!",
    "Pisces": "🎨 Ekspresikan dirimu melalui seni dan kreativitas.",
    "Unknown": "🔮 Tidak dapat menentukan prediksi untuk zodiak ini."
}

async def setup(bot, client, user_id):
    current_user_id = user_id  # Store user_id in a local variable

    @client.on(events.NewMessage())
    async def zodiac_handler(event):
        """Handle zodiac command"""
        # Check if user is owner or premium with active session
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id)
        )
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # Check command format
        is_zodiac_cmd = False
        date_str = ""
        
        if msg.startswith(f"{current_prefix}zodiak "):
            is_zodiac_cmd = True
            date_str = msg[len(current_prefix)+7:].strip()
                
        if not is_zodiac_cmd:
            return

        try:
            # Validate date format (dd-mm-yyyy)
            if not re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', date_str):
                raise ValueError("Format tanggal salah")
            
            # Parse date
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            
            # Validate date is not in the future
            if date_obj > datetime.now():
                raise ValueError("Tanggal tidak boleh di masa depan")
            
            # Get zodiac sign
            sign = get_zodiac_sign(date_obj)
            horoscope = HOROSCOPE_PREDICTIONS.get(sign, HOROSCOPE_PREDICTIONS["Unknown"])
            
            # Format response
            response = (
                f"**📅 Tanggal Lahir:** `{date_obj.strftime('%d %B %Y')}`\n"
                f"**✨ Zodiak:** `{sign}`\n"
                f"**🔮 Ramalan Hari Ini:** {horoscope}\n\n"
                f"_Gunakan `{current_prefix}zodiak [tanggal]` untuk ramalan lain_"
            )
            
            await event.reply(response, link_preview=False)
            
        except ValueError as e:
            error_msg = str(e)
            if "format" in error_msg.lower():
                example = f"Contoh: `{current_prefix}zodiak 16-06-2006`"
                await event.reply(f"```❌ Format tanggal salah! {example}```")
            elif "masa depan" in error_msg.lower():
                await event.reply("```❌ Tanggal tidak boleh di masa depan```")
            else:
                await event.reply(f"```❌ {error_msg}```")
        except Exception as e:
            await event.reply(f"```❌ Terjadi kesalahan: {str(e)[:200]}```")
        finally:
            try:
                await event.delete()
            except:
                pass

    @client.on(events.NewMessage(pattern=f"^{get_prefix(current_user_id)}zodiachelp$"))
    async def zodiac_help(event):
        """Show zodiac command help"""
        help_text = (
            f"<blockquote>✨ <b>Zodiak Command Guide</b></blockquote>\n\n"
            f"<blockquote>• <code>{get_prefix(current_user_id)}zodiak [dd-mm-yyyy]</code> - "
            "Dapatkan ramalan zodiak berdasarkan tanggal lahir</blockquote>\n"
            f"<blockquote>Contoh: <code>{get_prefix(current_user_id)}zodiak 16-06-2006</code></blockquote>"
        )
        await event.reply(help_text, parse_mode="html")