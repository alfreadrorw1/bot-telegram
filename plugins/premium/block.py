# plugins/block.py
import json
import os
import asyncio
from datetime import datetime
from telethon import events, functions, types
from telethon.errors import FloodWaitError
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
        # Pastikan direktori premium ada
        os.makedirs('premium', exist_ok=True)
        
        # Jika file tidak ada, buat file dengan struktur default
        if not os.path.exists('premium/premium.json'):
            with open('premium/premium.json', 'w') as f:
                json.dump({"users": []}, f)
            return False
            
        with open('premium/premium.json', 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        # Jika ada error, buat ulang file dengan struktur default
        try:
            with open('premium/premium.json', 'w') as f:
                json.dump({"users": []}, f)
        except:
            pass
        return False
    except Exception as e:
        print(f"Error checking premium user: {e}")
        return False

async def safe_edit(event, text, parse_mode="html"):
    """Safely edit a message with error handling"""
    try:
        await event.edit(text, parse_mode=parse_mode)
    except Exception:
        try:
            await event.respond(text, parse_mode=parse_mode)
        except Exception as e:
            print(f"Error handling message: {e}")

async def setup(bot, client, user_id):
    """Setup block/unblock commands for premium users"""
    current_user_id = user_id

    async def check_auth(event):
        """Check if user is authorized"""
        try:
            sender_id = event.sender_id
            is_authorized = (
                sender_id == OWNER_ID or 
                (is_premium_user(sender_id) and current_user_id == sender_id))
            return is_authorized
        except Exception as e:
            print(f"Auth check error: {e}")
            return False

    @client.on(events.NewMessage())
    async def block_handler(event):
        """Handle block command"""
        try:
            if not await check_auth(event):
                return

            current_prefix = get_prefix(current_user_id)
            msg = (event.text or '').strip()
            
            # Check command format
            is_block_cmd = False
            target = ""
            
            if current_prefix:
                if msg.startswith(current_prefix + "block"):
                    is_block_cmd = True
                    target = msg[len(current_prefix)+5:].strip()
            elif msg.lower().startswith("block"):
                is_block_cmd = True
                target = msg[5:].strip()
                
            if not is_block_cmd:
                return

            # Initialize variables
            target_id = None

            # Get target user
            reply_msg = await event.get_reply_message()
            if not target and reply_msg:
                target_id = reply_msg.sender_id
            elif target:
                if target.startswith('@'):
                    try:
                        entity = await client.get_entity(target)
                        target_id = entity.id
                    except Exception:
                        await safe_edit(event, "<blockquote>❌ Username tidak ditemukan</blockquote>")
                        return
                else:
                    try:
                        target_id = int(target)
                    except ValueError:
                        await safe_edit(event, "<blockquote>❌ ID harus angka atau username</blockquote>")
                        return
            else:
                await safe_edit(event, "<blockquote>❌ Format: block @username/user_id atau reply pesan</blockquote>")
                return

            # Prevent blocking owner
            if target_id == OWNER_ID:
                await safe_edit(event, "<blockquote>❌ ᴅɪᴀ ᴏᴡɴᴇʀ ʙᴇɢᴏ, ʟᴜ ᴛᴏʟᴏʟ ᴀᴘᴀ ɢɪᴍᴀɴᴀ ꜱɪʜ?</blockquote>")
                return

            try:
                await client(functions.contacts.BlockRequest(id=target_id))
                await safe_edit(event, "<blockquote>✅ ᴀɴᴀᴋ ᴀɴᴊɪɴɢ ɪɴɪ ʙᴇʀʜᴀꜱɪʟ ᴅɪ ʙʟᴏᴄᴋ</blockquote>")
            except FloodWaitError as e:
                await safe_edit(event, f"<blockquote>❌ Tunggu {e.seconds} detik sebelum mencoba lagi</blockquote>")
            except Exception as e:
                await safe_edit(event, f"<blockquote>❌ Gagal memblokir: {str(e)[:100]}</blockquote>")
                
        except Exception as e:
            print(f"Block handler error: {e}")

    @client.on(events.NewMessage())
    async def unblock_handler(event):
        """Handle unblock command"""
        try:
            if not await check_auth(event):
                return

            current_prefix = get_prefix(current_user_id)
            msg = (event.text or '').strip()
            
            # Check command format
            is_unblock_cmd = False
            target = ""
            
            if current_prefix:
                if msg.startswith(current_prefix + "unblock"):
                    is_unblock_cmd = True
                    target = msg[len(current_prefix)+7:].strip()
            elif msg.lower().startswith("unblock"):
                is_unblock_cmd = True
                target = msg[7:].strip()
                
            if not is_unblock_cmd:
                return

            # Initialize variables
            target_id = None

            # Get target user
            reply_msg = await event.get_reply_message()
            if not target and reply_msg:
                target_id = reply_msg.sender_id
            elif target:
                if target.startswith('@'):
                    try:
                        entity = await client.get_entity(target)
                        target_id = entity.id
                    except Exception:
                        await safe_edit(event, "<blockquote>❌ Username tidak ditemukan</blockquote>")
                        return
                else:
                    try:
                        target_id = int(target)
                    except ValueError:
                        await safe_edit(event, "<blockquote>❌ ID harus angka atau username</blockquote>")
                        return
            else:
                await safe_edit(event, "<blockquote>❌ Format: unblock @username/user_id atau reply pesan</blockquote>")
                return

            try:
                await client(functions.contacts.UnblockRequest(id=target_id))
                await safe_edit(event, "<blockquote>✅ ᴀɴᴀᴋ ᴀɴᴊɪɴɢ ɪɴɪ ʙᴇʀʜᴀꜱɪʟ ᴅɪ ᴜɴʙʟᴏᴄᴋ</blockquote>")
            except FloodWaitError as e:
                await safe_edit(event, f"<blockquote>❌ Tunggu {e.seconds} detik sebelum mencoba lagi</blockquote>")
            except Exception as e:
                await safe_edit(event, f"<blockquote>❌ Gagal mengunblokir: {str(e)[:100]}</blockquote>")
                
        except Exception as e:
            print(f"Unblock handler error: {e}")

    @client.on(events.NewMessage())
    async def blocklist_handler(event):
        """Handle blocklist command"""
        try:
            if not await check_auth(event):
                return

            current_prefix = get_prefix(current_user_id)
            msg = (event.text or '').strip()
            
            # Check command format
            is_blocklist_cmd = False
            
            if current_prefix:
                if msg == current_prefix + "blocklist":
                    is_blocklist_cmd = True
            elif msg.lower() == "blocklist":
                is_blocklist_cmd = True
                
            if not is_blocklist_cmd:
                return

            # Get blocked contacts
            try:
                blocked = await client(functions.contacts.GetBlockedRequest(offset=0, limit=100))
                if not blocked.users:
                    await safe_edit(event, "<blockquote>📋 Tidak ada yang diblokir</blockquote>")
                    return
                
                count = len(blocked.users)
                await safe_edit(event, f"<blockquote>📋 Total {count} user diblokir</blockquote>")
                
            except Exception as e:
                await safe_edit(event, f"<blockquote>❌ Gagal mendapatkan daftar blokir: {str(e)[:100]}</blockquote>")
                
        except Exception as e:
            print(f"Blocklist handler error: {e}")