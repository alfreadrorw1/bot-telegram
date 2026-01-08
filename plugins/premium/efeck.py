# plugins/effect.py
import os
import json
import subprocess
from telethon import events
from config import OWNER_ID
import asyncio

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

# Daftar efek yang diperbarui (efek duplikat/serupa telah dihapus)
effect_list = [
    'bass', 'echo', 'nightcore', 'slow', 'fast', 'robot', 'reverse',
    'chipmunk', 'deep', 'vibrato', 'tremolo', 'phaser', 'flanger', 'alien',
    'radio', 'telephone', 'megaphone', '8d', 'underwater'
]

# Mapping efek ke filter FFmpeg
effect_filters = {
    'bass': 'bass=g=20,dynaudnorm',
    'echo': 'aecho=0.8:0.9:1000:0.3',
    'nightcore': 'asetrate=44100*1.25,atempo=1.1',
    'slow': 'atempo=0.8',
    'fast': 'atempo=1.5',
    'robot': 'afftfilt=real=\'hypot(re,im)*cos(0)\':imag=\'hypot(re,im)*sin(0)\':win_size=512:overlap=0.75',
    'reverse': 'areverse',
    'chipmunk': 'asetrate=44100*1.5,atempo=1.3',
    'deep': 'asetrate=44100*0.8,atempo=0.9',
    'vibrato': 'vibrato=f=6.5',
    'tremolo': 'tremolo=f=10.0:d=0.7',
    'phaser': 'aphaser',
    'flanger': 'flanger',
    'alien': 'asetrate=22050,atempo=1.5',
    'radio': 'highpass=f=200, lowpass=f=3000',
    'telephone': 'bandpass=f=1000:width_type=h:width=2000',
    'megaphone': 'highpass=f=1000, lowpass=f=3000',
    '8d': 'apulsator=hz=0.125',
    'underwater': 'lowpass=f=300',
}

async def apply_effect(input_file, effect):
    output_file = f"cache/effect_{os.path.basename(input_file)}"
    filter_str = effect_filters.get(effect)

    if not filter_str:
        return None

    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-af', filter_str,
        '-y',
        output_file
    ]

    try:
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return output_file
    except subprocess.CalledProcessError:
        return None

async def safe_delete(message):
    """Safely delete a message with error handling"""
    try:
        await message.delete()
    except:
        pass

async def setup(bot, client, user_id):
    """Setup effect commands for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def effect_handler(event):
        """Handle effect commands"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # Check command format
        is_listefek_cmd = False
        is_efek_cmd = False
        effect_num = None
        
        if current_prefix:
            if msg == f"{current_prefix}listefek":
                is_listefek_cmd = True
            elif msg == f"{current_prefix}efek":
                is_efek_cmd = True
            elif msg.startswith(f"{current_prefix}efek"):
                effect_num = msg[len(current_prefix)+4:].strip()
        else:
            if msg.lower() == "listefek":
                is_listefek_cmd = True
            elif msg.lower() == "efek":
                is_efek_cmd = True
            elif msg.lower().startswith("efek"):
                effect_num = msg[4:].strip()
                
        # LISTEFEK command
        if is_listefek_cmd:
            teks = "<blockquote>📄 Daftar Efek:</blockquote>\n"
            for i, name in enumerate(effect_list, start=1):
                if current_prefix:
                    teks += f"<blockquote>{i}. <code>{current_prefix}efek{i}</code> → {name}</blockquote>\n"
                else:
                    teks += f"<blockquote>{i}. <code>efek{i}</code> → {name}</blockquote>\n"
            await event.reply(teks, parse_mode="html")
            return

        # EFEK command (without number)
        if is_efek_cmd:
            if current_prefix:
                msg_text = await event.reply("<blockquote>❌ Cara pakeknya balas pesan suara/audio dengan perintah <code>{current_prefix}efek1,2,3</code>, dst!!</blockquote>", parse_mode="html")
            else:
                msg_text = await event.reply("<blockquote>❌ Cara pakeknya balas pesan suara/audio dengan perintah <code>efek1,2,3</code>, dst!!</blockquote>", parse_mode="html")
            await asyncio.sleep(5)
            await safe_delete(msg_text)
            return

        # EFEK command with number
        if effect_num is not None:
            if not effect_num.isdigit():
                return

            index = int(effect_num) - 1
            if index < 0 or index >= len(effect_list):
                if current_prefix:
                    msg_text = await event.reply(f"<blockquote>❌ Tidak ada efek nomor segitu! Gunakan <code>{current_prefix}listefek</code> untuk melihat daftar efek!!</blockquote>", parse_mode="html")
                else:
                    msg_text = await event.reply("<blockquote>❌ Tidak ada efek nomor segitu! Gunakan <code>listefek</code> untuk melihat daftar efek!!</blockquote>", parse_mode="html")
                await asyncio.sleep(5)
                await safe_delete(msg_text)
                return

            effect = effect_list[index]

            if not event.is_reply:
                msg_text = await event.reply("<blockquote>❌ Balas voice atau audio yg mau diberi efek!!</blockquote>", parse_mode="html")
                await asyncio.sleep(5)
                await safe_delete(msg_text)
                return

            reply_msg = await event.get_reply_message()
            if not (reply_msg.voice or reply_msg.audio):
                msg_text = await event.reply("<blockquote>❌ File harus berupa voice atau audio!!</blockquote>", parse_mode="html")
                await asyncio.sleep(5)
                await safe_delete(msg_text)
                return

            try:
                proses = await event.reply("<blockquote>🔄 Memproses efek...</blockquote>", parse_mode="html")
                input_file = await reply_msg.download_media('cache/')
                output_file = await apply_effect(input_file, effect)

                if not output_file:
                    await proses.edit("<blockquote>❌ Gagal memproses efek.</blockquote>", parse_mode="html")
                    await asyncio.sleep(5)
                    await safe_delete(proses)
                    return

                await client.send_file(
                    event.chat_id,
                    output_file,
                    voice_note=reply_msg.voice,
                    reply_to=event.reply_to_msg_id
                )
                await safe_delete(proses)
                
                # Cleanup
                try:
                    os.remove(input_file)
                    os.remove(output_file)
                except:
                    pass
                    
            except Exception as e:
                msg_text = await event.reply(f"<blockquote>❌ Error: {str(e)[:200]}</blockquote>", parse_mode="html")
                await asyncio.sleep(5)
                await safe_delete(msg_text)