import math
import json
import os
import asyncio
from telethon import events, Button
from config import BOT_USERNAME, OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

def get_live_prefix():
    """Get current prefix directly from file with caching"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'


FEATURES = {
    "ᴀꜰᴋ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>afk</code> [alasan]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴀᴋᴛɪꜰᴋᴀɴ ᴍᴏᴅᴇ ᴀꜰᴋ ᴅᴇɴɢᴀɴ ᴀʟᴀꜱᴀɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>unafk</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴍᴀᴛɪᴋᴀɴ ᴍᴏᴅᴇ ᴀꜰᴋ</blockquote>",

    "ᴀᴅᴍɪɴ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>kick</code> [reply user]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴋɪᴄᴋ ᴀɴɢɢᴏᴛᴀ ɢʀᴜᴘ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>del</code> [reply pesan]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ᴘᴇsᴀɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>staff</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴅᴀꜰᴛᴀʀ ᴀᴅᴍɪɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>title</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴜʙᴀʜ ᴛɪᴛʟᴇ ᴀᴅᴍɪɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>pin</code> [reply pesan]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴘɪɴ ᴘᴇsᴀɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>unpin</code> [reply pesan]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴜɴᴘɪɴ ᴘᴇsᴀɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>sg</code> [username]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ʜɪsᴛᴏʀʏ ᴜsᴇʀɴᴀᴍᴇ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>tag</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀɢ sᴇᴍᴜᴀ ᴘᴇɴɢɢᴜɴᴀ ᴅᴀʀɪ ɢʀᴜᴘ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>stag</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴇʀʜᴇɴᴛɪ ᴍᴇʟᴀᴋᴜᴋᴀɴ ᴛᴀɢ</blockquote>",

    "ᴄᴏᴘʏ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>c</code> [reply pesan]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴀʟɪɴ ᴘᴇsᴀɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>p</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴇᴍᴘᴇʟ ᴘᴇsᴀɴ ʏᴀɴɢ �ɪsᴀʟɪɴ</blockquote>",

    "ᴇꜰꜰᴇᴋ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>bass</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀᴍʙᴀʜᴋᴀɴ �ꜰᴇᴋ ʙᴀss</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>echo</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀᴍʙᴀʜᴋᴀɴ ᴇꜰᴇᴋ ᴇᴄʜᴏ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>nightcore</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀᴍʙᴀʜᴋᴀɴ ᴇꜰᴇᴋ ɴɪɢʜᴛᴄᴏʀᴇ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>slow</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴘᴇʀʟᴀᴍʙᴀᴛ ᴀᴜᴅɪᴏ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>fast</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴘᴇʀᴄᴇᴘᴀᴛ ᴀᴜᴅɪᴏ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>robot</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀᴍʙᴀʜᴋᴀɴ ᴇꜰᴇᴋ ʀᴏʙᴏᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>reverse</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴀʟɪᴋ ᴀᴜᴅɪᴏ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>reverb</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀᴍʙᴀʜᴋᴀɴ ᴇꜰᴇᴋ ʀᴇᴠᴇʀʙ</blockquote>",

    "ꜰᴏɴᴛ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>font list</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴅᴀꜰᴛᴀʀ ꜰᴏɴᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>font</code> [nama font] [teks]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ ᴛᴇᴋs ᴅᴇɴɢᴀɴ ꜰᴏɴᴛ ᴛᴇʀᴛᴇɴᴛᴜ</blockquote>",

    "ʙʀᴏᴀᴅᴄᴀꜱᴛ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>gcast</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴋᴇ sᴇᴍᴜᴀ ɢʀᴜᴘ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>ucast</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴋᴇ sᴇᴍᴜᴀ ᴄʜᴀᴛ ᴘʀɪʙᴀᴅɪ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>setdelay</code> [waktu]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴀᴛᴜʀ ᴅᴇʟᴀʏ ʙʀᴏᴀᴅᴄᴀsᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>addbl</code> [reply/group id]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀᴍʙᴀʜᴋᴀɴ ᴄʜᴀᴛ/ɢʀᴜᴘ ᴋᴇ ʙʟᴀᴄᴋʟɪsᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>delbl</code> id chat/grup\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ᴄʜᴀᴛ/ɢʀᴜᴘ ᴅᴀʀɪ ʙʟᴀᴄᴋʟɪsᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>listbl</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴅᴀꜰᴛᴀʀ ʙʟᴀᴄᴋʟɪsᴛ</blockquote>",

    "ᴀɴɪᴍᴀꜱɪ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>hack</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴀɴɪᴍᴀsɪ ʜᴀᴄᴋ ᴘᴀʟsᴜ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>wibu2</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʀᴀɴᴅᴏᴍ ᴀɴɪᴍᴀsɪ ᴡɪʙᴜ2</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>wibbu</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʀᴀɴᴅᴏᴍ ᴀɴɪᴍᴀsɪ ᴡɪʙʙᴜ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>sangean</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʀᴀɴᴅᴏᴍ ᴀɴɪᴍᴀsɪ sᴀɴɢᴇᴀɴ</blockquote>",

    "ɪɴꜰᴏ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>info</code> [reply/username]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ɪɴꜰᴏʀᴍᴀsɪ ᴜsᴇʀ</blockquote>",

    "ʟɪᴍɪᴛ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>limit</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴇᴋ sᴛᴀᴛᴜs ʟɪᴍɪᴛ ᴀᴋᴜɴ</blockquote>",

    "ʟᴏɢ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>log on</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴀᴋᴛɪꜰᴋᴀɴ ʟᴏɢ ɢʀᴜᴘ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>log off</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴍᴀᴛɪᴋᴀɴ ʟᴏɢ ɢʀᴜᴘ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>pmlog on</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴀᴋᴛɪꜰᴋᴀɴ ʟᴏɢ ᴘᴍ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>pmlog off</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴍᴀᴛɪᴋᴀɴ ʟᴏɢ ᴘᴍ</blockquote>",

    "ʟʏʀɪᴄꜱ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>lirik</code> [judul lagu]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴀʀɪ ʟɪʀɪᴋ ʟᴀɢᴜ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>lagu</code> [judul lagu]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴀʀɪ ᴅᴀɴ ᴋɪʀɪᴍ ᴀᴜᴅɪᴏ ʟᴀɢᴜ</blockquote>",

    "ᴛᴏxɪᴄ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>toxic on</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴀᴋᴛɪꜰᴋᴀɴ ᴀɴᴛɪ ᴛᴏxɪᴄ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>toxic off</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴍᴀᴛɪᴋᴀɴ ᴀɴᴛɪ ᴛᴏxɪᴄ</blockquote>",

    "ɴᴏᴛᴇꜱ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>save</code> [nama] [reply/text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sɪᴍᴘᴀɴ ɴᴏᴛᴇs</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>get</code> [nama]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴀᴍʙɪʟ ɴᴏᴛᴇs</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>notes</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴅᴀꜰᴛᴀʀ ɴᴏᴛᴇs</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>clear</code> [nama]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ɴᴏᴛᴇs</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>clearall</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs sᴇᴍᴜᴀ ɴᴏᴛᴇs</blockquote>",

    "ᴘɪɴɢ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>ping</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴇᴋ sᴛᴀᴛᴜs ʙᴏᴛ</blockquote>",

    "ᴘʀᴏꜰɪʟᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>adminlist</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴅᴀꜰᴛᴀʀ ᴀᴅᴍɪɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>my</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ɪɴꜰᴏ ᴀᴋᴜɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>setuname</code> [username]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴇᴛ ᴜsᴇʀɴᴀᴍᴇ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>remuname</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ᴜsᴇʀɴᴀᴍᴇ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>setbio</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴇᴛ ʙɪᴏ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>setname</code> [nama depan] [nama belakang]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴇᴛ ɴᴀᴍᴀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>block</code> [id/reply]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙʟᴏᴋɪʀ ᴜsᴇʀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>unblock</code> [id/reply]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴋᴀ ʙʟᴏᴋɪʀ ᴜsᴇʀ</blockquote>",

    "ᴘʀᴇꜰɪx": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>setprefix</code> [prefix]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴇᴛ ᴘʀᴇꜰɪx</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>setprefix no</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ᴘʀᴇꜰɪx</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>prefix</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴘʀᴇꜰɪx ᴀᴋᴛɪꜰ</blockquote>",

    "ꜱᴘᴀᴍ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>cspam</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴘᴀᴍ ᴋᴀʀᴀᴋᴛᴇʀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>wspam</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴘᴀᴍ ᴋᴀᴛᴀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>spam</code> [jumlah] [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴘᴀᴍ ᴘᴇsᴀɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>picspam</code> [jumlah] [url]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴘᴀᴍ ɢᴀᴍʙᴀʀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>delayspam</code> [delay] [jumlah] [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴘᴀᴍ ᴅᴇɴɢᴀɴ ᴅᴇʟᴀʏ</blockquote>",

    "ꜱᴛɪᴄᴋᴇʀ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>kang</code> [reply sticker]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴜʀɪ sᴛɪᴄᴋᴇʀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>packkang</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴜʀɪ sᴇᴍᴜᴀ sᴛɪᴄᴋᴇʀ ᴅᴀʟᴀᴍ ᴘᴀᴄᴋ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>sticker</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ sᴛɪᴄᴋᴇʀ ᴅᴀʀɪ ᴛᴇᴋs</blockquote>",

    "ᴛᴀɢ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>tag</code> [pesan]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴀɢ sᴇᴍᴜᴀ ᴍᴇᴍʙᴇʀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>stag</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴇʀʜᴇɴᴛɪ ᴛᴀɢ</blockquote>",

    "ᴢᴏᴅɪᴀᴋ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>zodiak</code> [tanggal-bulan-tahun]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴇᴋ ᴢᴏᴅɪᴀᴋ (ᴄᴏɴᴛᴏʜ: 16-06-2006)</blockquote>",

    "ɪɴꜱᴛᴀɢʀᴀᴍ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>igp</code> [username/reply]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ɪɴꜰᴏ ᴀᴋᴜɴ ɪɢ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>iglist</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ sᴇᴍᴜᴀ ɪɴꜰᴏ ɪɢ ᴛᴇʀsɪᴍᴘᴀɴ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>igclear</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ɪɴꜰᴏ ɪɢ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>iglogin</code> [username],[password]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟᴏɢɪɴ ɪɢ</blockquote>",

    "ᴍᴇᴅɪᴀꜰɪʀᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>mediafire</code> [url]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴅᴏᴡɴʟᴏᴀᴅ ꜰɪʟᴇ ᴅᴀʀɪ ᴍᴇᴅɪᴀꜰɪʀᴇ</blockquote>",

    "ɢᴀᴍᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>game</code> [1-25]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴍᴀɪɴᴋᴀɴ ɢᴀᴍᴇ (ʟɪʜᴀᴛ ʟɪsᴛ ᴅᴇɴɢᴀɴ <code>game list</code>)</blockquote>",

    "ᴄᴀᴛᴜʀ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>catur</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴍᴀɪɴᴋᴀɴ ɢᴀᴍᴇ ᴄᴀᴛᴜʀ</blockquote>",

    "ᴄᴜᴀᴄᴀ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>cuaca</code> [kota]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴇᴋ ᴄᴜᴀᴄᴀ</blockquote>",

    "ǫᴄ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>qc</code> [reply/username] [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴍᴇᴍʙᴜᴀᴛ sᴛɪᴄᴋᴇʀ ǫᴜᴏᴛᴇ</blockquote>",

    "ʙʀᴀᴛ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>brat</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ ᴛᴇᴋs ʙʀᴀᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>bvideo</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ ᴛᴇᴋs ʙʀᴀᴛ ᴠɪᴅᴇᴏ</blockquote>",

    "ᴛᴏᴜʀʟ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>tourl</code> [reply gambar]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴏɴᴠᴇʀᴛ ɢᴀᴍʙᴀʀ ᴋᴇ ᴜʀʟ</blockquote>",

    "ᴛʀᴀɴꜱʟᴀᴛᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>tr</code> [reply text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴇʀᴊᴇᴍᴀʜᴋᴀɴ ᴛᴇᴋs (ᴅᴇꜰᴀᴜʟᴛ: ɪɴɢɢʀɪs ᴋᴇ ɪɴᴅᴏɴᴇsɪᴀ)</blockquote>",

    "ᴄʀᴇᴀᴛᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>creategc</code> [nama]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ ɢʀᴜᴘ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>createch</code> [nama]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ ᴄʜᴀɴɴᴇʟ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>delgc</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ɢʀᴜᴘ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>delch</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ᴄʜᴀɴɴᴇʟ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>createlist</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴅᴀꜰᴛᴀʀ ʙᴜᴀᴛᴀɴ</blockquote>",

    "ᴀʟᴋɪᴛᴀʙ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>alkitab</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴀʀɪ ᴀʏᴀᴛ ᴀʟᴋɪᴛᴀʙ</blockquote>",

    "ᴋʜᴏᴅᴀᴍ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>cekkhodam</code> [nama/reply]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴇᴋ ᴋʜᴏᴅᴀᴍ</blockquote>",

    "ᴀɴɪᴍᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>anime</code> [judul]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴀʀɪ ɪɴꜰᴏ ᴀɴɪᴍᴇ</blockquote>",

    "ᴛᴛꜱ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>tts</code> [text]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴏɴᴠᴇʀᴛ ᴛᴇᴋs ᴋᴇ sᴜᴀʀᴀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>vtxt</code> [reply audio]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴏɴᴠᴇʀᴛ sᴜᴀʀᴀ ᴋᴇ ᴛᴇᴋs</blockquote>",

    "ᴘᴜʀɢᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>purge</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ᴊᴇᴊᴀᴋ ᴄʜᴀᴛ</blockquote>",

    "ᴠᴄᴛᴏᴏʟꜱ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>startvc</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>stopvc</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴇɴᴛɪᴋᴀɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>joinvc</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴊᴏɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>leavevc</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴋᴇʟᴜᴀʀ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</blockquote>",

    "ᴛᴇʟᴇɢʀᴀᴘʜ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>telegraph</code> [judul],[pesan]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʙᴜᴀᴛ ʟɪɴᴋ ᴛᴇʟᴇɢʀᴀᴘʜ</blockquote>",

    "ɢʀᴏᴜᴘ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>join</code> [link]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴊᴏɪɴ ɢʀᴜᴘ/ᴄʜᴀɴɴᴇʟ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>leave</code> [link]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴋᴇʟᴜᴀʀ ɢʀᴜᴘ/ᴄʜᴀɴɴᴇʟ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>leavemute</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴋᴇʟᴜᴀʀ ᴅᴀʀɪ ɢʀᴜᴘ ʏᴀɴɢ ᴍᴜᴛᴇ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>papay</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴋᴇʟᴜᴀʀ ᴅᴀʀɪ ɢʀᴜᴘ (ꜰᴜɴ)</blockquote>",

    "ᴀᴄᴛɪᴏɴ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>fake</code> [durasi] [action]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ꜰᴀᴋᴇ ᴀᴄᴛɪᴏɴ (ᴠɪᴅᴇᴏ/ᴀᴜᴅɪᴏ/ꜰɪʟᴇ/ᴘʜᴏᴛᴏ)</blockquote>",

    "ᴄᴜʀɪ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>b</code> [reply media]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sᴀʟɪɴ ᴍᴇᴅɪᴀ sᴇᴋᴀʟɪ ʟɪʜᴀᴛ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>t</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴛᴇᴍᴘᴇʟ ᴍᴇᴅɪᴀ ʏᴀɴɢ ᴅɪsᴀʟɪɴ</blockquote>",

    "ᴊᴀᴅɪꜱ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>s</code> [reply media]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴏɴᴠᴇʀᴛ ᴍᴇᴅɪᴀ ᴊᴀᴅɪ sᴛɪᴄᴋᴇʀ</blockquote>",

    "ɪᴍᴀɢᴇ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>img</code> [reply sticker]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ᴄᴏɴᴠᴇʀᴛ sᴛɪᴄᴋᴇʀ ᴊᴀᴅɪ ɢᴀᴍʙᴀʀ</blockquote>",

    "ᴘᴏᴛᴏ": "<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>addpoto</code> [reply gambar]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> sɪᴍᴘᴀɴ ɢᴀᴍʙᴀʀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>delpoto</code> [nomor]\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʜᴀᴘᴜs ɢᴀᴍʙᴀʀ</blockquote>\n\n<blockquote><b>ᐈ𝗖𝗼𝗺𝗺𝗮𝗻𝗱:</b> <code>poto</code>\n<b>ᐈ𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:</b> ʟɪʜᴀᴛ ᴅᴀꜰᴛᴀʀ ɢᴀᴍʙᴀʀ</blockquote>"
}

FEATURES_LIST = list(FEATURES.keys())
ITEMS_PER_PAGE = 8
TOTAL_PAGES = math.ceil(len(FEATURES_LIST) / ITEMS_PER_PAGE)

def create_help_caption(page, user_name):
    return (
        f"╭──「 Help Menu 」\n"
        f"│• total fitur 139\n"
        f"│• Halaman {page+1}/{TOTAL_PAGES}\n"
        f"╰──「 {user_name} 」\n"
        f"<blockquote>⚡ ᴜꜱᴇʀʙᴏᴛ ʙʏ ᴀʟꜰʀᴇᴀᴅʀᴏʀᴡ ⚡</blockquote>"
    )

def get_page_markup(page):
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_features = FEATURES_LIST[start_idx:end_idx]

    buttons = []
    for i in range(0, len(page_features), 2):
        row = []
        if i < len(page_features):
            feature = page_features[i]
            row.append(Button.inline(feature, data=f"detail_{feature}_{page}"))
        if i + 1 < len(page_features):
            feature = page_features[i+1]
            row.append(Button.inline(feature, data=f"detail_{feature}_{page}"))
        buttons.append(row)

    nav = [
        Button.inline("☜", data=f"page_{(page - 1) % TOTAL_PAGES}"),
        Button.inline("★", data="close"),
        Button.inline("☞", data=f"page_{(page + 1) % TOTAL_PAGES}")
    ]
    buttons.append(nav)
    
    return buttons

async def setup(bot, user):
    # Inline handler (BOT)
    @bot.on(events.InlineQuery)
    async def inline_handler(event):
        if event.text and event.text.strip() == "help":
            try:
                result = event.builder.article(
                    title="🔥Help Menu",
                    description="Punya Alfread Ye reng",
                    text=create_help_caption(0, event.sender.first_name),
                    buttons=get_page_markup(0),
                    parse_mode='html'
                )
                await event.answer([result])
            except Exception as e:
                print(f"Error in inline_handler: {e}")

    @bot.on(events.CallbackQuery(pattern=r'page_(\d+)'))
    async def page_callback(event):
        try:
            page = int(event.pattern_match.group(1))
            await event.edit(
                create_help_caption(page, event.sender.first_name),
                buttons=get_page_markup(page),
                parse_mode='html'
            )
        except Exception as e:
            print(f"Error in page_callback: {e}")
            await event.answer("⚠️ Gagal memuat halaman", alert=True)

    @bot.on(events.CallbackQuery(pattern=r'detail_([^_]+)_(\d+)'))
    async def detail_callback(event):
        try:
            fitur = event.pattern_match.group(1).decode('utf-8') if isinstance(event.pattern_match.group(1), bytes) else event.pattern_match.group(1)
            page = int(event.pattern_match.group(2))
            detail_text = (
                f"<blockquote>⪼ ᴅᴏᴋᴜᴍᴇɴ ᴜɴᴛᴜᴋ {fitur.capitalize()}</blockquote>\n\n"
                f"{FEATURES[fitur]}\n\n"
                f"<blockquote>Dibuka Oleh {event.sender.first_name} メ</blockquote>"
            )
            await event.edit(
                detail_text,
                buttons=[[Button.inline("☜ Back", data=f"page_{page}")]],
                parse_mode='html'
            )
        except Exception as e:
            print(f"Error in detail_callback: {e}")
            await event.answer("⚠️ Gagal memuat detail", alert=True)

    @bot.on(events.CallbackQuery(pattern=r'close'))
    async def close_callback(event):
        try:
            await event.delete()
        except Exception as e:
            print(f"Error in close_callback: {e}")
            try:
                await event.answer("Pesan sudah dihapus")
            except:
                pass

    # Userbot handler: trigger inline
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def help_command_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()

        is_help_cmd = False
        
        if current_prefix == "no":
            if msg.lower() == "help":
                is_help_cmd = True
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd == "help":
                    is_help_cmd = True

        if not is_help_cmd:
            return

        try:
            await event.delete()

            result = await user.inline_query(BOT_USERNAME, "help")
            if result:
                await result[0].click(event.chat_id, reply_to=event.reply_to_msg_id)

        except Exception as e:
            print(f"Error in help_command_handler: {e}")
            await event.respond("⚠️ Gagal memunculkan menu bantuan", parse_mode='html')