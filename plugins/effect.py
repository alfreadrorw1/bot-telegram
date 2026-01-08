import os
import json
import subprocess
import asyncio
from telethon import events
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
CACHE_DIR = 'cache'

def ensure_dirs():
    """Ensure required directories exist"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        ensure_dirs()
        with open(PREFIX_FILE, 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def apply_effect(input_file, effect):
    """Apply audio effect using ffmpeg"""
    # Clean filename to prevent issues with spaces/special chars
    clean_input = input_file.replace(" ", "_").replace("(", "").replace(")", "")
    if input_file != clean_input:
        os.rename(input_file, clean_input)
        input_file = clean_input
    
    output_file = os.path.join(CACHE_DIR, f"effect_{os.path.basename(input_file)}")
    
    effects = {
        'bass': 'bass=g=20:d=0.8',
        'echo': 'aecho=0.8:0.9:1000:0.3',
        'nightcore': 'atempo=1.06,asetrate=44100*1.25',
        'slow': 'atempo=0.5',
        'fast': 'atempo=2.0',
        'robot': 'asetrate=44100*0.8,atempo=1.25,afftfilt=real=\'hypot(re,im)*sin(0)\':imag=\'hypot(re,im)*cos(0)\':win_size=512:overlap=0.75',
        'reverse': 'areverse',
        'reverb': 'aecho=0.8:0.88:60:0.4'        
    }
    
    cmd = [
        'ffmpeg',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', input_file,
        '-af', effects[effect],
        '-y',  # Overwrite output file if exists
        output_file
    ]
    
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error applying effect: {e}")
        return None
    finally:
        # Clean up the renamed file if it exists
        if os.path.exists(clean_input) and clean_input != input_file:
            os.remove(clean_input)

async def setup(bot, user):
    ensure_dirs()
    current_prefix = get_live_prefix()
    
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def effect_handler(event):
        """Handle audio effect commands"""
        msg = (event.text or '').strip().lower()
        
        # Available effects
        effects = [
            'bass', 'echo', 'nightcore', 'slow', 
            'fast', 'robot', 'reverse', 'reverb'
        ]
        
        # Check command format
        effect = None
        if not current_prefix:
            if msg in effects and event.is_reply:
                effect = msg
        else:
            if msg.startswith(current_prefix):
                cmd_part = msg[len(current_prefix):].strip()
                if cmd_part in effects and event.is_reply:
                    effect = cmd_part
        
        if not effect:
            return
            
        reply_msg = await event.get_reply_message()
        if not (reply_msg.voice or reply_msg.audio):
            status = await event.reply(
                "<blockquote>❌ <b>Balas ke pesan audio atau voice note!</b></blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(3)
            await status.delete()
            await event.delete()
            return

        processing_msg = None
        try:
            processing_msg = await event.reply(
                f"<blockquote>🔄 <b>Memproses efek {effect}...</b></blockquote>",
                parse_mode="html"
            )
            
            # Download the media
            input_file = await reply_msg.download_media(CACHE_DIR + '/')
            if not input_file:
                await processing_msg.edit(
                    "<blockquote>❌ <b>Gagal mengunduh media!</b></blockquote>",
                    parse_mode="html"
                )
                await asyncio.sleep(3)
                await processing_msg.delete()
                await event.delete()
                return
                
            # Apply effect
            output_file = await apply_effect(input_file, effect)
            if not output_file:
                await processing_msg.edit(
                    "<blockquote>❌ <b>Gagal memproses efek!</b></blockquote>",
                    parse_mode="html"
                )
                await asyncio.sleep(3)
                await processing_msg.delete()
                await event.delete()
                return
                
            # Send the result
            if reply_msg.voice:
                await user.send_file(
                    event.chat_id,
                    output_file,
                    voice_note=True,
                    reply_to=reply_msg.id,
                    parse_mode="html"
                )
            else:
                await user.send_file(
                    event.chat_id,
                    output_file,
                    reply_to=reply_msg.id,
                    parse_mode="html"
                )
            
            await processing_msg.delete()
            await event.delete()
            
        except Exception as e:
            error_msg = await event.reply(
                f"<blockquote>❌ <b>Error:</b> <code>{str(e)[:200]}</code></blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(3)
            await error_msg.delete()
            if processing_msg:
                await processing_msg.delete()
            await event.delete()
        finally:
            # Clean up files
            try:
                if 'input_file' in locals() and os.path.exists(input_file):
                    os.remove(input_file)
                if 'output_file' in locals() and os.path.exists(output_file):
                    os.remove(output_file)
            except:
                pass

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID, pattern=f'^{current_prefix}effects$'))
    async def list_effects_handler(event):
        """List available effects"""
        effects_list = [
            "🎵 <b>Daftar Efek Audio:</b>",
            "",
            "• <code>bass</code> - Boost frekuensi bass",
            "• <code>echo</code> - Efek gema",
            "• <code>nightcore</code> - Efek musik nightcore",
            "• <code>slow</code> - Memperlambat audio",
            "• <code>fast</code> - Mempercepat audio",
            "• <code>robot</code> - Efek suara robot",
            "• <code>reverse</code> - Memutar balik audio",
            "• <code>reverb</code> - Efek ruangan bergema",
            "• <code>squirrel</code> - Efek suara tupai (cepat & tinggi)",
            "",
            f"<b>Usage:</b> <code>{current_prefix}[efek]</code> balas ke audio/voice note"
        ]
        
        await event.reply(
            "<blockquote>" + "\n".join(effects_list) + "</blockquote>",
            parse_mode="html"
        )
        await event.delete()