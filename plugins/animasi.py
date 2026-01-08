# plugins/animasi.py
from telethon import events
from config import OWNER_ID
import asyncio
import json
import os
import time
import math

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

async def setup(bot, user):
    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def animasi_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Check command format
        def is_command(cmd):
            if current_prefix == "no":
                return msg.lower() == cmd
            return msg.startswith(f"{current_prefix}{cmd}")
        
        # Bulan animation
        if is_command("bulan"):
            animation_chars = [
                "🌗.", "🌘.", "🌑.", "🌒.", "🌓.", "🌔.",
                "🌕.", "🌖.", "🌗.", "🌘.", "🌑.", "🌒.",
                "🌓.", "🌔.", "🌕.", "🌖.", "🌗.", "🌘.",
                "🌑.", "🌒.", "🌓.", "🌔.", "🌕.", "🌖."
            ]
            for char in animation_chars:
                await event.edit(char)
                await asyncio.sleep(0.1)
            return

        # Helikopter animation
        if is_command("helikopter"):
            await event.edit(
                "▬▬▬.◙.▬▬▬ \n"
                "═▂▄▄▓▄▄▂ \n"
                "◢◤ █▀▀████▄▄▄▄◢◤ \n"
                "█▄ █ █▄ ███▀▀▀▀▀▀▀╬ \n"
                "◥█████◤ \n"
                "══╩══╩══ \n"
                "╬═╬ \n"
                "╬═╬ \n"
                "╬═╬ \n"
                "╬═╬ \n"
                "╬═╬ \n"
                "╬═╬ \n"
                "╬═╬ Hallo Semuanya :) \n"
                "╬═╬☻/ \n"
                "╬═╬/▌ \n"
                "╬═╬/ \\"
            )
            return

        # Tembak animation
        if is_command("tembak"):
            await event.edit(
                "_/﹋\\_\n"
                "(҂`_´)\n"
                "<,︻╦╤─ ҉\n"
                "_/﹋\\_\n"
                "**Mau Jadi Pacarku Gak?!**"
            )
            return

        # Bundir animation
        if is_command("bundir"):
            await event.edit(
                "`Dadah Semuanya...`          \n　　　　　|\n"
                "　　　　　| \n"
                "　　　　　| \n"
                "　　　　　| \n"
                "　　　　　| \n"
                "　　　　　| \n"
                "　　　　　| \n"
                "　　　　　| \n"
                "　／￣￣＼| \n"
                "＜ ´･ 　　 |＼ \n"
                "　|　３　 | 丶＼ \n"
                "＜ 、･　　|　　＼ \n"
                "　＼＿＿／∪ _ ∪) \n"
                "　　　　　 Ｕ Ｕ"
            )
            return

        # Awkwok animation
        if is_command("awkwok"):
            await event.edit(
                "────██──────▀▀▀██\n"
                "──▄▀█▄▄▄─────▄▀█▄▄▄\n"
                "▄▀──█▄▄──────█─█▄▄\n"
                "─▄▄▄▀──▀▄───▄▄▄▀──▀▄\n"
                "─▀───────▀▀─▀───────▀▀\n"
                "`Awkwokwokwok..`"
            )
            return

        # Bernyanyi animation
        if is_command("bernyanyi"):
            animations = [
                "**Ganteng Doang Gak Bernyanyi (ง˙o˙)ว**",
                "**♪┗ ( ･o･) ┓♪┏ (・o･) ┛♪**",
                "**♪┏(・o･)┛♪┗ ( ･o･) ┓**",
                "**♪┗ ( ･o･) ┓♪┏ (・o･) ┛♪**",
                "**♪┏(・o･)┛♪┗ ( ･o･) ┓**",
                "**♪┗ ( ･o･) ┓♪┏ (・o･) ┛♪**",
                "**♪┏(・o･)┛♪┗ ( ･o･) ┓**",
                "**♪┗ ( ･o･) ┓♪┏ (・o･) ┛♪**",
                "**♪┏(・o･)┛♪┗ ( ･o･) ┓**",
                "**♪┗ ( ･o･) ┓♪┏ (・o･) ┛♪**",
                "**♪┏(・o･)┛♪┗ ( ･o･) ┓**",
                "**♪┗ ( ･o･) ┓♪┏ (・o･) ┛♪**",
                "**♪┏(・o･)┛♪┗ ( ･o･) ┓**",
                "**♪┗ ( ･o･) ┓♪┏ (・o･) ┛♪**",
                "**♪┏(・o･)┛♪┗ ( ･o･) ┓**"
            ]
            for anim in animations:
                await event.edit(anim)
                await asyncio.sleep(1)
            return
            
            
        if is_command("love"):
            loveyou = [
               "**Love You❤️**",
               "**Love You🧡**",
               "**Love You💛**",
               "**Love You💚**",
               "**Love You💙**",
               "**Love You💜**",
               "**Love You🖤**",
               "**❤️**",
               "**❤️🧡**",
               "**❤️🧡💚**",
               "**❤️🧡💚💛**",
               "**🧡💚💛💙**",
               "**💚💛💙💜**",
               "**💛💙💜🖤**",
               "**💙💜🖤❤️**",
               "**💜🖤❤️🧡**",
               "**🖤❤️🧡💚**",
               "**❤️🧡💚💛**",
               "**🧡💚💛💙**"            
            ]
            for anim in loveyou:
                await event.edit(anim)
                await asyncio.sleep(0.8)  # Kecepatan animasi (bisa diubah)
            return