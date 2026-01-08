import os
import json
import aiohttp
from telethon import events
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
WEATHER_API_KEY = "060a6bcfa19809c2cd4d97a212b19273"  # OpenWeatherMap API key

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def get_weather_data(location):
    """Get weather data from OpenWeatherMap API"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={WEATHER_API_KEY}&lang=id"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        print(f"[WEATHER] Error fetching data: {str(e)}")
        return None

def format_weather_response(weather_data, location):
    """Format weather data into HTML message"""
    weather_emoji = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌁',
        'Drizzle': '🌦️'
    }
    
    condition = weather_data['weather'][0]['main']
    emoji = weather_emoji.get(condition, '🌤️')
    
    message = [
        f"<blockquote>✨ {emoji} <b>Cuaca di {location.capitalize()}</b> {emoji}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"• <b>Suhu:</b> <code>{weather_data['main']['temp']}°C</code>",
        f"• <b>Terasa seperti:</b> <code>{weather_data['main']['feels_like']}°C</code>",
        f"• <b>Kondisi:</b> {weather_data['weather'][0]['description'].capitalize()}",
        f"• <b>Kelembapan:</b> <code>{weather_data['main']['humidity']}%</code>",
        f"• <b>Angin:</b> <code>{weather_data['wind']['speed']} m/s</code>",
        f"• <b>Tekanan:</b> <code>{weather_data['main']['pressure']} hPa</code>",
        "━━━━━━━━━━━━━━━━━━━━",
        "📍 <b>Lokasi:</b>",
        f"   - <b>Latitude:</b> <code>{weather_data['coord']['lat']}°</code>",
        f"   - <b>Longitude:</b> <code>{weather_data['coord']['lon']}°</code>"
    ]
    
    if 'country' in weather_data['sys']:
        message.append(f"   - <b>Negara:</b> <code>{weather_data['sys']['country']}</code>")
    
    message.append("<br>Tetap jaga kesehatan ya! 😊</blockquote>")
    return "\n".join(message)

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def weather_handler(event):
        """Handle weather command requests"""
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        is_weather_cmd = False
        location = ""
        
        if not current_prefix:
            # No prefix mode
            if msg.lower().startswith(("cuaca", "weather")):
                is_weather_cmd = True
                parts = msg.split(maxsplit=1)
                location = parts[1] if len(parts) > 1 else ""
        else:
            # Prefix mode
            if msg.startswith(current_prefix):
                cmd_part = msg[len(current_prefix):].strip().lower()
                if cmd_part.startswith(("cuaca", "weather")):
                    is_weather_cmd = True
                    parts = cmd_part.split(maxsplit=1)
                    location = parts[1] if len(parts) > 1 else ""
        
        if not is_weather_cmd:
            return
            
        if not location:
            await event.reply(
                "<blockquote>🌍 <b>Mohon sertakan nama lokasi</b>\n"
                "Contoh: <code>{}cuaca Jakarta</code></blockquote>".format(current_prefix + " " if current_prefix else ""),
                parse_mode="html"
            )
            return

        processing_msg = await event.reply(
            "<blockquote>⏳ <b>Sedang memeriksa cuaca...</b></blockquote>",
            parse_mode="html"
        )
        
        # Get weather data
        weather_data = await get_weather_data(location)
        if not weather_data:
            await processing_msg.edit(
                "<blockquote>❌ <b>Gagal mendapatkan data cuaca</b>\n"
                "Coba cek lagi nama lokasinya atau coba beberapa saat lagi</blockquote>",
                parse_mode="html"
            )
            return

        # Format and send response
        weather_message = format_weather_response(weather_data, location)
        
        await processing_msg.delete()
        await event.reply(weather_message, parse_mode="html")