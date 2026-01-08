# plugins/premium/iqc.py
import os
import json
import aiohttp
import asyncio
import tempfile
import random
from datetime import datetime, timezone, timedelta
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

def get_wib_time():
    """Get current time in WIB (Waktu Indonesia Barat) format"""
    # UTC+7 for WIB (Western Indonesian Time)
    wib_tz = timezone(timedelta(hours=7))
    wib_time = datetime.now(wib_tz)
    
    # Format: HH:MM (24-hour format)
    return wib_time.strftime("%H:%M")

async def setup(bot, client, user_id):
    """Setup IQC command for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def iqc_handler(event):
        """Handle IQC command"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id)
        )
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.raw_text or '').strip()
        
        # Check command format
        is_iqc_cmd = False
        
        if current_prefix:
            if msg.startswith(f"{current_prefix}iqc"):
                is_iqc_cmd = True
        else:
            if msg.lower().startswith("iqc"):
                is_iqc_cmd = True
                
        if not is_iqc_cmd:
            return

        # Extract text
        if current_prefix:
            text = msg[len(current_prefix)+3:].strip()
        else:
            text = msg[3:].strip()
            
        if not text:
            await event.reply(
                "Masukkan teks setelah perintah\nContoh: .iqc kadang iri liat org bahagia kenapa aku gabisa kek mereka",
                parse_mode="html"
            )
            return

        # Send processing message
        processing_msg = await event.reply("Sabar Yaa Anjjjjjj...", parse_mode="html")
        
        try:
            # Prepare API parameters with WIB time
            wib_time = get_wib_time()
            battery = random.randint(1, 100)
            
            # List of Indonesian carriers for more authenticity
            carriers = ["INDOSAT", "TELKOMSEL", "XL", "3", "SMARTFREN"]
            carrier = random.choice(carriers)
            
            # API URL with WIB time
            api_url = f"https://brat.siputzx.my.id/iphone-quoted?time={wib_time}&batteryPercentage={battery}&carrierName={carrier}&messageText={text}&emojiStyle=apple"
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        await processing_msg.edit("❌ Gagal membuat gambar. API tidak merespons.", parse_mode="html")
                        return
                    
                    # Create temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        temp_file.write(await response.read())
                        temp_file_path = temp_file.name
            
            # Send image
            await client.send_file(
                event.chat_id,
                temp_file_path,
                caption=f"☑️Done Ketua",
                reply_to=event.id
            )
            
            # Clean up
            os.unlink(temp_file_path)
            await processing_msg.delete()
            
        except aiohttp.ClientError:
            await processing_msg.edit("❌ Gagal terhubung ke server. Silakan coba lagi nanti.", parse_mode="html")
        except asyncio.TimeoutError:
            await processing_msg.edit("❌ Timeout: Proses terlalu lama. Silakan coba lagi.", parse_mode="html")
        except Exception as e:
            error_msg = str(e)[:200]
            await processing_msg.edit(f"❌ Terjadi kesalahan: {error_msg}", parse_mode="html")
            
    