import os
import asyncio
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telethon import events, utils
from config import OWNER_ID

# Configuration
FONTS_DIR = "data/fonts"
DEFAULT_FONT = "Arial.ttf"
MAX_FONT_SIZE = 200
MIN_FONT_SIZE = 50
BASE_LENGTH = 10
TEXT_MARGIN = 50
LINE_SPACING = 15

def get_available_fonts():
    """Get available fonts from fonts directory"""
    if not os.path.exists(FONTS_DIR):
        os.makedirs(FONTS_DIR, exist_ok=True)
        return []
    
    return sorted([f for f in os.listdir(FONTS_DIR) if f.lower().endswith('.ttf')])

async def generate_custom_image(text: str, font_file: str) -> BytesIO:
    bio = BytesIO()
    
    try:
        # 1. Load background image
        bg_url = "https://ar-hosting.pages.dev/1747413244830.jpg"
        response = requests.get(bg_url, stream=True, timeout=15)
        response.raise_for_status()
        bg_img = Image.open(BytesIO(response.content)).convert("RGBA")
        draw = ImageDraw.Draw(bg_img)
        
        # 2. Load font
        font_path = os.path.join(FONTS_DIR, font_file)
        
        # 3. Calculate dynamic font size
        text_length = len(text)
        font_size = min(MAX_FONT_SIZE, 
                       max(MIN_FONT_SIZE, 
                          MAX_FONT_SIZE - (text_length/BASE_LENGTH)*5))
        
        try:
            font = ImageFont.truetype(font_path, int(font_size))
        except Exception as e:
            raise Exception(f"Failed to load font: {str(e)}")
        
        # 4. Text wrapping and drawing
        max_width = bg_img.width - 2*TEXT_MARGIN
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # 5. Calculate position and draw text
        bbox = draw.textbbox((0, 0), "Test", font=font)
        line_height = bbox[3] - bbox[1] + LINE_SPACING
        total_height = len(lines) * line_height
        
        y = (bg_img.height - total_height) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (bg_img.width - text_width) // 2
            
            # Draw outline
            outline_size = max(2, int(font_size/25))
            for xo in [-outline_size, 0, outline_size]:
                for yo in [-outline_size, 0, outline_size]:
                    if xo != 0 or yo != 0:
                        draw.text((x+xo, y+yo), line, font=font, fill="white")
            
            draw.text((x, y), line, font=font, fill="black")
            y += line_height
        
        # 6. Save image
        bio.name = "sticker.webp"
        bg_img.save(bio, format="WEBP", quality=95)
        bio.seek(0)
        return bio

    except Exception as e:
        if 'bio' in locals():
            bio.close()
        raise Exception(f"Failed to generate image: {str(e)}")

async def setup(bot, user):
    fonts = get_available_fonts()
    
    if not fonts:
        print("[WARNING] No fonts found in data/fonts/")
        return
    
    @user.on(events.NewMessage(outgoing=True, pattern=r'^gen(\d+)\s*(.*)$'))
    async def custom_gen_handler(event):
        """Handle gen commands"""
        font_num = event.pattern_match.group(1)
        text = event.pattern_match.group(2).strip()
        
        # If replying and text is empty, use replied message text
        if not text and event.is_reply:
            reply_msg = await event.get_reply_message()
            text = reply_msg.text or reply_msg.raw_text or ""
        
        if not text:
            tmp = await event.reply(
                "<blockquote>"
                "🚫 <b>Mohon berikan teks!</b>\n\n"
                "<b>Contoh penggunaan:</b>\n"
                "<code>gen1 teks anda</code>\n"
                "Balas pesan dengan <code>gen1</code> untuk menggunakan teks mereka"
                "</blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(10)
            await tmp.delete()
            await event.delete()
            return

        # Select font
        try:
            font_index = int(font_num) - 1
            if font_index < 0 or font_index >= len(fonts):
                raise ValueError
            font_file = fonts[font_index]
        except:
            await event.reply(
                f"<blockquote>⚠ <b>Nomor font tidak valid!</b> Gunakan 1-{len(fonts)}</blockquote>",
                parse_mode="html"
            )
            return

        status = await event.reply(
            f"<blockquote>🔄 <b>Membuat gambar dengan font {font_file}...</b></blockquote>",
            parse_mode="html"
        )
        
        try:
            img = await generate_custom_image(text, font_file)
            await user.send_file(
                event.chat_id,
                img,
                reply_to=event.id if event.is_reply else None,
                force_document=False
            )
        except Exception as e:
            await status.edit(
                f"<blockquote>❌ <b>Gagal:</b> <code>{str(e)[:200]}</code></blockquote>",
                parse_mode="html"
            )
            await asyncio.sleep(5)
        finally:
            await status.delete()
            await event.delete()
    
    @user.on(events.NewMessage(outgoing=True, pattern=r'^gen$'))
    async def list_fonts_handler(event):
        """Show available fonts"""
        font_list = "\n".join(f"<b>{i+1}.</b> {f}" for i, f in enumerate(fonts))
        tmp = await event.reply(
            "<blockquote>"
            "📋 <b>Font yang tersedia:</b>\n"
            f"{font_list}\n\n"
            "<b>Contoh penggunaan:</b>\n"
            "<code>gen1 teks anda</code> - Gunakan font pertama\n"
            "Balas pesan dengan <code>gen1</code> untuk menggunakan teks mereka"
            "</blockquote>",
            parse_mode="html"
        )
        await asyncio.sleep(15)
        await tmp.delete()
        await event.delete()