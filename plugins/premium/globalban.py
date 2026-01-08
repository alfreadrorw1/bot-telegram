# plugins/premium/globalban.py
import os
import json
import random
import asyncio
from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins, Channel, Chat
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

async def get_admin_groups_fast(client, user_id):
    """Get all groups where the user is admin (fast version)"""
    admin_groups = []
    async for dialog in client.iter_dialogs(limit=100):  # Batasi jumlah dialog
        if dialog.is_group or (dialog.is_channel and not getattr(dialog.entity, 'broadcast', False)):
            try:
                # Cek cepat apakah user adalah creator (pemilik) grup
                if hasattr(dialog.entity, 'creator') and dialog.entity.creator:
                    if dialog.entity.creator and getattr(dialog.entity, 'id', None) == user_id:
                        admin_groups.append({
                            'id': dialog.id,
                            'title': dialog.name,
                        })
                        continue
                
                # Untuk grup non-broadcast, cek admin status dengan cara lebih cepat
                if not getattr(dialog.entity, 'broadcast', False):
                    # Coba akses admin rights langsung dari dialog jika tersedia
                    if hasattr(dialog, 'participant') and hasattr(dialog.participant, 'admin_rights'):
                        if dialog.participant.admin_rights:
                            admin_groups.append({
                                'id': dialog.id,
                                'title': dialog.name,
                            })
                            continue
                    
                    # Fallback: cek admin dengan metode yang lebih ringan
                    try:
                        # Coba dapatkan info chat yang lebih ringan
                        chat = await client.get_entity(dialog.id)
                        if hasattr(chat, 'admin_rights') and chat.admin_rights:
                            admin_groups.append({
                                'id': dialog.id,
                                'title': dialog.name,
                            })
                    except:
                        continue
            except Exception as e:
                # Skip dialog yang error
                continue
    
    return admin_groups

async def setup(bot, client, user_id):
    """Setup global ban commands for premium users"""
    current_user_id = user_id

    @client.on(events.NewMessage())
    async def globalban_handler(event):
        """Handle global ban commands"""
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
        is_gban_cmd = False
        is_gben_cmd = False
        
        if current_prefix == "no":
            if msg.lower().startswith("gban"):
                is_gban_cmd = True
            elif msg.lower().startswith("gben"):
                is_gben_cmd = True
        else:
            if msg.lower().startswith(f"{current_prefix}gban"):
                is_gban_cmd = True
            elif msg.lower().startswith(f"{current_prefix}gben"):
                is_gben_cmd = True
                
        if not (is_gban_cmd or is_gben_cmd):
            return

        # Extract target user
        target = None
        target_name = "Unknown User"
        target_username = "No Username"
        
        if is_gban_cmd:
            target_text = msg[len(current_prefix)+4:].strip() if current_prefix != "no" else msg[4:].strip()
        else:
            target_text = msg[len(current_prefix)+4:].strip() if current_prefix != "no" else msg[4:].strip()
            
        if not target_text and event.is_reply:
            reply = await event.get_reply_message()
            target = reply.sender_id
            try:
                target_entity = await client.get_entity(target)
                target_name = getattr(target_entity, 'first_name', '') 
                if getattr(target_entity, 'last_name', ''):
                    target_name += f" {target_entity.last_name}"
                target_username = f"@{target_entity.username}" if target_entity.username else "No Username"
            except:
                pass
        else:
            if target_text.startswith('@'):
                try:
                    target_entity = await client.get_entity(target_text)
                    target = target_entity.id
                    target_name = getattr(target_entity, 'first_name', '')
                    if getattr(target_entity, 'last_name', ''):
                        target_name += f" {target_entity.last_name}"
                    target_username = f"@{target_entity.username}" if target_entity.username else "No Username"
                except:
                    await event.reply("<blockquote>❌ User tidak ditemukan</blockquote>", parse_mode="html")
                    return
            else:
                try:
                    target = int(target_text)
                    target_entity = await client.get_entity(target)
                    target_name = getattr(target_entity, 'first_name', '')
                    if getattr(target_entity, 'last_name', ''):
                        target_name += f" {target_entity.last_name}"
                    target_username = f"@{target_entity.username}" if target_entity.username else "No Username"
                except:
                    await event.reply("<blockquote>❌ Format tidak valid. Gunakan: @username atau user_id</blockquote>", parse_mode="html")
                    return

        if not target:
            await event.reply("<blockquote>❌ Target tidak ditemukan</blockquote>", parse_mode="html")
            return

        # Check if trying to ban self or owner
        if target == sender_id:
            await event.reply("<blockquote>❌ Tidak bisa ban diri sendiri</blockquote>", parse_mode="html")
            return
            
        if target == OWNER_ID:
            await event.reply("<blockquote>❌ Tidak bisa ban owner bot</blockquote>", parse_mode="html")
            return

        # Process based on command type
        if is_gban_cmd:
            # Real GBAN - show processing message
            processing_msg = await event.reply(
                "<blockquote>🔍 Mencari grup dimana Anda adalah admin...</blockquote>",
                parse_mode="html"
            )
            
            try:
                # Get admin groups dengan timeout
                admin_groups = await asyncio.wait_for(
                    get_admin_groups_fast(client, sender_id), 
                    timeout=30  # Timeout 30 detik
                )
            except asyncio.TimeoutError:
                await processing_msg.edit("<blockquote>❌ Timeout: Pencarian grup terlalu lama</blockquote>", parse_mode="html")
                return
            
            if not admin_groups:
                await processing_msg.edit("<blockquote>❌ Anda bukan admin di grup manapun</blockquote>", parse_mode="html")
                return

            # Process real ban
            await processing_msg.edit(
                f"<blockquote>⚡ Memulai Global Ban pada {len(admin_groups)} grup...</blockquote>",
                parse_mode="html"
            )
            
            success = 0
            failed = 0
            
            for group in admin_groups:
                try:
                    await client.edit_permissions(
                        group['id'],
                        target,
                        view_messages=False
                    )
                    success += 1
                    await asyncio.sleep(0.5)  # Delay untuk menghindari flood
                except Exception as e:
                    failed += 1
                    # Skip error details untuk mempercepat
            
            # Send result
            result_msg = (
                f"<blockquote>✅ <b>GLOBAL BAN BERHASIL</b></blockquote>\n\n"
                f"<blockquote>👤 <b>Target:</b> {target_name} ({target_username})</blockquote>\n"
                f"<blockquote>🆔 <b>User ID:</b> <code>{target}</code></blockquote>\n\n"
                f"<blockquote>📊 <b>Hasil:</b></blockquote>\n"
                f"<blockquote>✅ <b>Sukses:</b> {success} grup</blockquote>\n"
                f"<blockquote>❌ <b>Gagal:</b> {failed} grup</blockquote>"
            )
            
            await processing_msg.edit(result_msg, parse_mode="html")
        
        else:
            # Fake GBEN - langsung kirim hasil fake tanpa proses
            success = random.randint(120, 180)  # Sukses antara 120-180
            failed = random.randint(5, 15)      # Gagal antara 5-15
            
            result_msg = (
                f"<blockquote><b>GLOBAL BAN BERHASIL</b></blockquote>\n\n"
                f"<blockquote><b>Target:</b> {target_name} ({target_username})</blockquote>\n"
                f"<blockquote><b>Sukses:</b> {success} grup</blockquote>\n"
                f"<blockquote><b>Gagal:</b> {failed} grup</blockquote>\n\n"
            )
            
            await event.reply(result_msg, parse_mode="html")