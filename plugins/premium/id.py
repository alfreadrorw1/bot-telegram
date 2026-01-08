# plugins/premium/cek_id.py
import json
import os
from telethon import events, errors
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

def get_actual_chat_id(chat_id):
    """Convert chat ID to actual format (with -100 for groups/channels)"""
    # Jika chat_id sudah negatif, kembalikan langsung
    if chat_id < 0:
        return chat_id
    
    # Untuk user ID, kembalikan positif
    if chat_id > 0:
        return chat_id
    
    # Untuk supergroups/channels, format dengan -100
    # Telethon biasanya memberikan ID positif untuk supergroups/channels
    # tapi kita perlu mengonversi ke format yang benar
    try:
        # Coba konversi ke format supergroup
        return -1000000000000 - chat_id
    except:
        return chat_id

async def setup(bot, client, user_id):
    """Setup cek ID command for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def cek_id_handler(event):
        """Handle cek ID command"""
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
        is_cek_id_cmd = False
        target_arg = ""
        
        if current_prefix:
            if msg.startswith(f"{current_prefix}id"):
                is_cek_id_cmd = True
                target_arg = msg[len(current_prefix)+2:].strip()
        else:
            if msg.lower().startswith("id"):
                is_cek_id_cmd = True
                target_arg = msg[2:].strip()
                
        if not is_cek_id_cmd:
            return

        try:
            # Get target user
            target = None
            target_id = None
            
            # If replying to a message
            if event.is_reply:
                replied = await event.get_reply_message()
                target_id = replied.sender_id
                try:
                    target = await client.get_entity(target_id)
                except errors.rpcerrorlist.InputUserDeactivatedError:
                    await event.reply(f"<blockquote>👤 <b>Informasi User</b>\n\n🆔 <b>ID:</b> <code>{target_id}</code>\n📛 <b>Nama:</b> Akun dinonaktifkan\n👤 <b>Username:</b> Tidak tersedia\n📞 <b>Telepon:</b> Tidak tersedia\n🤖 <b>Bot:</b> Tidak\n✅ <b>Premium:</b> {'Ya' if is_premium_user(target_id) else 'Tidak'}</blockquote>", parse_mode="html")
                    return
            
            # If username/ID is provided
            elif target_arg:
                if target_arg.startswith('@'):
                    # Username provided
                    try:
                        target = await client.get_entity(target_arg)
                        target_id = target.id
                    except errors.rpcerrorlist.UsernameNotOccupiedError:
                        await event.reply("<blockquote>❌ Username tidak ditemukan</blockquote>", parse_mode="html")
                        return
                else:
                    try:
                        # Try to parse as user ID
                        target_id = int(target_arg)
                        try:
                            target = await client.get_entity(target_id)
                        except ValueError:
                            # If we can't get entity but have ID, show basic info
                            await event.reply(f"<blockquote>👤 <b>Informasi User</b>\n\n🆔 <b>ID:</b> <code>{target_id}</code>\n📛 <b>Nama:</b> Informasi terbatas\n👤 <b>Username:</b> Tidak tersedia\n📞 <b>Telepon:</b> Tidak tersedia\n🤖 <b>Bot:</b> Tidak diketahui\n✅ <b>Premium:</b> {'Ya' if is_premium_user(target_id) else 'Tidak'}</blockquote>", parse_mode="html")
                            return
                    except ValueError:
                        await event.reply("<blockquote>❌ Format ID tidak valid. Gunakan @username atau ID numerik</blockquote>", parse_mode="html")
                        return
            
            # If no target specified, check current chat
            else:
                if event.is_private:
                    # Private chat - get the other user
                    target_id = event.chat_id
                    try:
                        target = await client.get_entity(target_id)
                    except Exception:
                        await event.reply(f"<blockquote>👤 <b>Informasi User</b>\n\n🆔 <b>ID:</b> <code>{target_id}</code>\n📛 <b>Nama:</b> Informasi terbatas\n👤 <b>Username:</b> Tidak tersedia\n📞 <b>Telepon:</b> Tidak tersedia\n🤖 <b>Bot:</b> Tidak diketahui\n✅ <b>Premium:</b> {'Ya' if is_premium_user(target_id) else 'Tidak'}</blockquote>", parse_mode="html")
                        return
                else:
                    # Group/channel - get info about the chat itself
                    chat = await event.get_chat()
                    
                    # Get actual chat ID with proper format
                    actual_chat_id = get_actual_chat_id(chat.id)
                    
                    # Get participant count for groups
                    participants_count = "Tidak diketahui"
                    if hasattr(chat, 'participants_count'):
                        participants_count = chat.participants_count
                    elif not getattr(chat, 'broadcast', False):
                        try:
                            participants = await client.get_participants(chat)
                            participants_count = len(participants)
                        except:
                            pass
                    
                    chat_type = "Channel" if getattr(chat, 'broadcast', False) else "Group" if getattr(chat, 'megagroup', False) else "Chat"
                    
                    chat_info = f"""
<blockquote>
📋 <b>Informasi Chat</b>

🏷️ <b>Nama:</b> {getattr(chat, 'title', 'Tidak ada')}
🆔 <b>ID:</b> <code>{actual_chat_id}</code>
📝 <b>Tipe:</b> {chat_type}
👥 <b>Jumlah Anggota:</b> {participants_count}
📞 <b>Username:</b> {f'@{chat.username}' if getattr(chat, 'username', None) else 'Tidak ada'}
</blockquote>
                    """
                    await event.reply(chat_info, parse_mode="html")
                    return

            # Get user information
            if target:
                first_name = getattr(target, 'first_name', '') or ""
                last_name = getattr(target, 'last_name', '') or ""
                full_name = f"{first_name} {last_name}".strip()
                username = f"@{target.username}" if getattr(target, 'username', None) else "Tidak ada"
                phone = getattr(target, 'phone', 'Tidak tersedia')
                is_bot = 'Ya' if getattr(target, 'bot', False) else 'Tidak'
                
                user_info = f"""
<blockquote>
👤 <b>Informasi User</b>

🆔 <b>ID:</b> <code>{target.id}</code>
📛 <b>Nama:</b> {full_name}
👤 <b>Username:</b> {username}
📞 <b>Telepon:</b> <code>{phone}</code>
🤖 <b>Bot:</b> {is_bot}
✅ <b>Premium:</b> {'Ya' if is_premium_user(target.id) else 'Tidak'}
</blockquote>
                """
                
                await event.reply(user_info, parse_mode="html")
            elif target_id:
                # Fallback for when we have ID but can't get entity
                await event.reply(f"<blockquote>👤 <b>Informasi User</b>\n\n🆔 <b>ID:</b> <code>{target_id}</code>\n📛 <b>Nama:</b> Informasi terbatas\n👤 <b>Username:</b> Tidak tersedia\n📞 <b>Telepon:</b> Tidak tersedia\n🤖 <b>Bot:</b> Tidak diketahui\n✅ <b>Premium:</b> {'Ya' if is_premium_user(target_id) else 'Tidak'}</blockquote>", parse_mode="html")
            
        except errors.rpcerrorlist.InputUserDeactivatedError:
            await event.reply(f"<blockquote>👤 <b>Informasi User</b>\n\n🆔 <b>ID:</b> <code>{target_id}</code>\n📛 <b>Nama:</b> Akun dinonaktifkan\n👤 <b>Username:</b> Tidak tersedia\n📞 <b>Telepon:</b> Tidak tersedia\n🤖 <b>Bot:</b> Tidak\n✅ <b>Premium:</b> {'Ya' if is_premium_user(target_id) else 'Tidak'}</blockquote>", parse_mode="html")
        except Exception as e:
            error_msg = str(e)
            if "Could not find the input entity" in error_msg:
                if target_id:
                    await event.reply(f"<blockquote>👤 <b>Informasi User</b>\n\n🆔 <b>ID:</b> <code>{target_id}</code>\n📛 <b>Nama:</b> Tidak ditemukan di cache\n👤 <b>Username:</b> Tidak tersedia\n📞 <b>Telepon:</b> Tidak tersedia\n🤖 <b>Bot:</b> Tidak diketahui\n✅ <b>Premium:</b> {'Ya' if is_premium_user(target_id) else 'Tidak'}</blockquote>", parse_mode="html")
                else:
                    await event.reply("<blockquote>❌ User tidak ditemukan. Pastikan username/ID benar</blockquote>", parse_mode="html")
            else:
                await event.reply(f"<blockquote>❌ Error: {error_msg[:200]}</blockquote>", parse_mode="html")