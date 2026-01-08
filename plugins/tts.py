# plugins/tts.py
import os
import asyncio
import time
import json
import re
from telethon import events
from config import OWNER_ID, BOT_USERNAME
import gtts
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment

def get_prefix():
    """Get current prefix from config (supports 'no' prefix mode)"""
    try:
        with open('data/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open('data/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def setup(bot, user):
    @user.on(events.NewMessage())
    async def tts_handler(event):
        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        # Check if message is a tts command
        is_tts = (
            (current_prefix == "no" and message.startswith("tts ")) or
            (message.startswith(current_prefix.lower()) and 
             message[len(current_prefix):].strip().startswith("tts "))
        )
        
        if not is_tts:
            return

        # Extract text after command
        if current_prefix == "no":
            text = message[4:].strip()
        else:
            text = message[len(current_prefix):].strip()[4:].strip()

        if not text:
            await event.reply(f"❌ **Penggunaan:** `tts <teks>`" if current_prefix == "no" else f"❌ **Penggunaan:** `{current_prefix}tts <teks>`")
            return

        if len(text) > 500:
            await event.reply("❌ **Teks terlalu panjang! Maksimal 500 karakter.**")
            return

        try:
            # Create TTS audio
            tts = gtts.gTTS(text, lang='id')
            
            # Save to temporary file
            temp_file = "data/temp_audio/tts_temp.mp3"
            tts.save(temp_file)
            
            # Convert to OGG format for Telegram voice message
            sound = AudioSegment.from_mp3(temp_file)
            ogg_file = "data/temp_audio/tts_temp.ogg"
            sound.export(ogg_file, format="ogg")
            
            # Send as voice message
            await event.client.send_file(
                event.chat_id,
                ogg_file,
                voice_note=True,
                reply_to=event.reply_to_msg_id
            )
            
            # Clean up
            os.remove(temp_file)
            os.remove(ogg_file)
            
        except Exception as e:
            await event.reply(f"❌ **Error:** {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(ogg_file):
                os.remove(ogg_file)

    @user.on(events.NewMessage())
    async def vtxt_handler(event):
        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        # Check if message is a vtxt command
        is_vtxt = (
            (current_prefix == "no" and message == "vtxt") or
            (message.startswith(current_prefix.lower()) and 
             message[len(current_prefix):].strip() == "vtxt")
        )
        
        if not is_vtxt or not event.is_reply:
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg.voice and not reply_msg.audio:
            await event.reply("❌ **Pesan yang dibalas bukan pesan suara/audio!**")
            return

        try:
            # Download the voice message
            await event.reply("🔍 **Memproses pesan suara...**")
            voice_file = await reply_msg.download_media("data/temp_audio/voice_temp.ogg")
            
            # Convert to WAV format for speech recognition
            sound = AudioSegment.from_ogg(voice_file)
            wav_file = "data/temp_audio/voice_temp.wav"
            sound.export(wav_file, format="wav")
            
            # Initialize recognizer
            recognizer = sr.Recognizer()
            
            # Convert voice to text
            with sr.AudioFile(wav_file) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language='id-ID')
            
            # Clean up
            os.remove(voice_file)
            os.remove(wav_file)
            
            await event.reply(f"{text}")
        except sr.UnknownValueError:
            await event.reply("❌ **Tidak dapat mengenali ucapan dalam pesan suara**")
        except sr.RequestError:
            await event.reply("❌ **Error: Layanan speech recognition tidak tersedia**")
        except Exception as e:
            await event.reply(f"❌ **Error:** {str(e)}")
            if os.path.exists(voice_file):
                os.remove(voice_file)
            if os.path.exists(wav_file):
                os.remove(wav_file)

    @user.on(events.NewMessage())
    async def tts_help_handler(event):
        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        # Check if message is a ttshelp command
        is_ttshelp = (
            (current_prefix == "no" and message == "ttshelp") or
            (message.startswith(current_prefix.lower()) and 
             message[len(current_prefix):].strip() == "ttshelp")
        )
        
        if not is_ttshelp:
            return

        help_text = f"""
🔊 **Text-to-Speech & Voice-to-Text Help**

{"`tts <teks>`" if current_prefix == "no" else f"`{current_prefix}tts <teks>`"} - Ubah teks menjadi pesan suara
{"`vtxt`" if current_prefix == "no" else f"`{current_prefix}vtxt`"} - Balas ke pesan suara untuk mengubah menjadi teks
{"`ttshelp`" if current_prefix == "no" else f"`{current_prefix}ttshelp`"} - Tampilkan pesan bantuan ini

**Contoh:**
{"`tts halo dunia`" if current_prefix == "no" else f"`{current_prefix}tts halo dunia`"}
Balas pesan suara dengan {"`vtxt`" if current_prefix == "no" else f"`{current_prefix}vtxt`"}
"""
        await event.reply(help_text)