import asyncio
import io
import math
import urllib.request
from os import remove
import os
import json
from secrets import choice
from telethon import events
from telethon.errors import PackShortNameOccupiedError
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl import functions, types
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeSticker,
    InputStickerSetID,
    MessageMediaPhoto,
    MessageMediaUnsupported,
)
from telethon.utils import get_input_document
from PIL import Image
import requests
from bs4 import BeautifulSoup as bs
from config import OWNER_ID

# Make sure data directory exists
os.makedirs('data', exist_ok=True)

KANGING_STR = [
    "Prosess Mengambil Sticker Pack!",
    "Mengambil Sticker Pack Anda",
    "Proses!",
    "Ijin Colong Stickernya Yaa :D",
]

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

def setup(bot, user):
    @user.on(events.NewMessage())
    async def kang_handler(event):
        # Check if sender is owner
        if event.sender_id != OWNER_ID:
            return
            
        # Get current prefix and message
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        # Check if message is a kang command
        is_kang = (
            (current_prefix == "no" and message in ["kang", "tikel"]) or
            (message.startswith(current_prefix.lower()) and 
             message[len(current_prefix):].strip().split()[0] in ["kang", "tikel"])
        )
        
        if not is_kang:
            return

        user_client = await user.get_me()
        if not user_client.username:
            user_client.username = user_client.first_name
        message_reply = await event.get_reply_message()
        photo = None
        emojibypass = False
        is_video = False
        is_anim = False
        emoji = "✨"  # Default emoji

        if not message_reply:
            return await event.reply("**Silahkan Reply Ke Pesan Media Untuk Mengambil Sticker itu!**")

        if isinstance(message_reply.media, MessageMediaPhoto):
            xx = await event.reply(f"`{choice(KANGING_STR)}`")
            photo = io.BytesIO()
            photo = await user.download_media(message_reply.photo, photo)
        elif isinstance(message_reply.media, MessageMediaUnsupported):
            return await event.reply("**File Tidak Didukung, Silahkan Reply ke Media Foto/GIF !**")
        elif message_reply.file and "image" in message_reply.file.mime_type.split("/"):
            xx = await event.reply(f"`{choice(KANGING_STR)}`")
            photo = io.BytesIO()
            await user.download_file(message_reply.media.document, photo)
            if (
                DocumentAttributeFilename(file_name="sticker.webp")
                in message_reply.media.document.attributes
            ):
                for attr in message_reply.media.document.attributes:
                    if isinstance(attr, DocumentAttributeSticker):
                        emoji = attr.alt or "✨"
                        emojibypass = True
        elif message_reply.file and "tgsticker" in message_reply.file.mime_type:
            xx = await event.reply(f"`{choice(KANGING_STR)}`")
            await user.download_file(message_reply.media.document, "AnimatedSticker.tgs")
            attributes = message_reply.media.document.attributes
            for attribute in attributes:
                if isinstance(attribute, DocumentAttributeSticker):
                    emoji = attribute.alt or "✨"
            emojibypass = True
            is_anim = True
            photo = 1
        elif message_reply.media.document.mime_type in ["video/mp4", "video/webm"]:
            if message_reply.media.document.mime_type == "video/webm":
                xx = await event.reply(f"`{choice(KANGING_STR)}`")
                await user.download_media(message_reply.media.document, "Video.webm")
            else:
                xx = await event.reply("`Downloading...`")
                await xx.edit(f"`{choice(KANGING_STR)}`")
            is_video = True
            emoji = "✨"
            emojibypass = True
            photo = 1
        else:
            return await event.reply("**File Tidak Didukung, Silahkan Reply ke Media Foto/GIF !**")

        if photo:
            splat = message.split()
            if not emojibypass:
                emoji = "✨"
            pack = 1
            if len(splat) == 3:
                pack = splat[2]
                emoji = splat[1] or "✨"
            elif len(splat) == 2:
                if splat[1].isnumeric():
                    pack = int(splat[1])
                else:
                    emoji = splat[1] or "✨"

            packname = f"Sticker_u{user_client.id}_Ke{pack}"
            packnick = f"Sticker Pack {user_client.username or user_client.first_name}"

            cmd = "/newpack"
            file = io.BytesIO()

            if is_video:
                packname += "_vid"
                packnick += " (Video)"
                cmd = "/newvideo"
            elif is_anim:
                packname += "_anim"
                packnick += " (Animated)"
                cmd = "/newanimated"
            else:
                image = await resize_photo(photo)
                file.name = "sticker.png"
                image.save(file, "PNG")

            response = urllib.request.urlopen(
                urllib.request.Request(f"http://t.me/addstickers/{packname}")
            )
            htmlstr = response.read().decode("utf8").split("\n")

            if (
                "  A <strong>Telegram</strong> user has created the <strong>Sticker&nbsp;Set</strong>."
                not in htmlstr
            ):
                async with user.conversation("@Stickers") as conv:
                    try:
                        await conv.send_message("/addsticker")
                    except YouBlockedUserError:
                        await user(UnblockRequest("@Stickers"))
                        await conv.send_message("/addsticker")
                    await conv.get_response()
                    await user.send_read_acknowledge(conv.chat_id)
                    await conv.send_message(packname)
                    x = await conv.get_response()
                    limit = "50" if (is_anim or is_video) else "120"
                    while limit in x.text:
                        pack += 1
                        packname = f"Sticker_u{user_client.id}_Ke{pack}"
                        packnick = f"Sticker Pack {user_client.username or user_client.first_name}"
                        await xx.edit(
                            "`Membuat Sticker Pack Baru "
                            + str(pack)
                            + " Karena Sticker Pack Sudah Penuh`"
                        )
                        await conv.send_message(packname)
                        x = await conv.get_response()
                        if x.text == "Gagal Memilih Pack.":
                            await conv.send_message(cmd)
                            await conv.get_response()
                            await user.send_read_acknowledge(conv.chat_id)
                            await conv.send_message(packnick)
                            await conv.get_response()
                            await user.send_read_acknowledge(conv.chat_id)
                            if is_anim:
                                await conv.send_file("AnimatedSticker.tgs")
                                remove("AnimatedSticker.tgs")
                            elif is_video:
                                await conv.send_file("Video.webm")
                                remove("Video.webm")
                            else:
                                file.seek(0)
                                await conv.send_file(file, force_document=True)
                            await conv.get_response()
                            if emoji:  # Ensure emoji is not empty
                                await conv.send_message(emoji)
                            else:
                                await conv.send_message("✨")
                            await user.send_read_acknowledge(conv.chat_id)
                            await conv.get_response()
                            await conv.send_message("/publish")
                            if is_anim:
                                await conv.get_response()
                                await conv.send_message(f"<{packnick}>")
                            await conv.get_response()
                            await user.send_read_acknowledge(conv.chat_id)
                            await conv.send_message("/skip")
                            await user.send_read_acknowledge(conv.chat_id)
                            await conv.get_response()
                            await conv.send_message(packname)
                            await user.send_read_acknowledge(conv.chat_id)
                            await conv.get_response()
                            await user.send_read_acknowledge(conv.chat_id)
                            return await xx.edit(
                                "`Sticker ditambahkan ke pack yang berbeda !"
                                "\nIni pack yang baru saja dibuat!"
                                f"\nTekan [Sticker Pack](t.me/addstickers/{packname}) Untuk Melihat Sticker Pack"
                            )
                    if is_anim:
                        await conv.send_file("AnimatedSticker.tgs")
                        remove("AnimatedSticker.tgs")
                    elif is_video:
                        await conv.send_file("Video.webm")
                        remove("Video.webm")
                    else:
                        file.seek(0)
                        await conv.send_file(file, force_document=True)
                    rsp = await conv.get_response()
                    if "Sorry, the file type is invalid." in rsp.text:
                        return await xx.edit(
                            "**Gagal Menambahkan Sticker, Gunakan @Stickers Bot Untuk Menambahkan Sticker Anda.**"
                        )
                    if emoji:  # Ensure emoji is not empty
                        await conv.send_message(emoji)
                    else:
                        await conv.send_message("✨")
                    await user.send_read_acknowledge(conv.chat_id)
                    await conv.get_response()
                    await conv.send_message("/done")
                    await conv.get_response()
                    await user.send_read_acknowledge(conv.chat_id)
            else:
                await xx.edit("`Membuat Sticker Pack Baru`")
                async with user.conversation("@Stickers") as conv:
                    try:
                        await conv.send_message(cmd)
                    except YouBlockedUserError:
                        await user(UnblockRequest("@Stickers"))
                        await conv.send_message(cmd)
                    await conv.get_response()
                    await user.send_read_acknowledge(conv.chat_id)
                    await conv.send_message(packnick)
                    await conv.get_response()
                    await user.send_read_acknowledge(conv.chat_id)
                    if is_anim:
                        await conv.send_file("AnimatedSticker.tgs")
                        remove("AnimatedSticker.tgs")
                    elif is_video:
                        await conv.send_file("Video.webm")
                        remove("Video.webm")
                    else:
                        file.seek(0)
                        await conv.send_file(file, force_document=True)
                    rsp = await conv.get_response()
                    if "Sorry, the file type is invalid." in rsp.text:
                        return await xx.edit(
                            "**Gagal Menambahkan Sticker, Gunakan @Stickers Bot Untuk Menambahkan Sticker.**"
                        )
                    if emoji:  # Ensure emoji is not empty
                        await conv.send_message(emoji)
                    else:
                        await conv.send_message("✨")
                    await user.send_read_acknowledge(conv.chat_id)
                    await conv.get_response()
                    await conv.send_message("/publish")
                    if is_anim:
                        await conv.get_response()
                        await conv.send_message(f"<{packnick}>")
                    await conv.get_response()
                    await user.send_read_acknowledge(conv.chat_id)
                    await conv.send_message("/skip")
                    await user.send_read_acknowledge(conv.chat_id)
                    await conv.get_response()
                    await conv.send_message(packname)
                    await user.send_read_acknowledge(conv.chat_id)
                    await conv.get_response()
                    await user.send_read_acknowledge(conv.chat_id)

            await xx.edit(
                "** Sticker Berhasil Ditambahkan!**"
                f"\n        >> **[KLIK DISINI](t.me/addstickers/{packname})** <<\n**Untuk Menggunakan Stickers**"
            )

    async def resize_photo(photo):
        image = Image.open(photo)
        if (image.width and image.height) < 512:
            size1 = image.width
            size2 = image.height
            if size1 > size2:
                scale = 512 / size1
                size1new = 512
                size2new = size2 * scale
            else:
                scale = 512 / size2
                size1new = size1 * scale
                size2new = 512
            size1new = math.floor(size1new)
            size2new = math.floor(size2new)
            sizenew = (size1new, size2new)
            image = image.resize(sizenew)
        else:
            maxsize = (512, 512)
            image.thumbnail(maxsize)
        return image