# plugins/premium/group.py
import os
import asyncio
import json
import re
from telethon import events, functions, types
from telethon.errors import (
    ChatAdminRequiredError,
    UserNotParticipantError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    ChannelPrivateError,
    FloodWaitError
)
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

async def setup(bot, connect_user, user_id=None):
    current_user_id = user_id  # Store user_id in a local variable

    @connect_user.on(events.NewMessage())
    async def group_manager_handler(event):
        """Handle group management commands"""
        # Check if user is owner or premium with active session
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id)
        )
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.raw_text or '').strip()
        
        # Check for group commands
        if not message.startswith(current_prefix):
            return

        cmd = message[len(current_prefix):].strip().lower()
        
        try:
            # JOIN command
            if cmd.startswith("join"):
                query = message[len(current_prefix)+4:].strip()
                await handle_join(event, query)
            
            # LEAVE command
            elif cmd.startswith("leave"):
                target = message[len(current_prefix)+5:].strip()
                await handle_leave(event, target)
            
            # LEAVEMUTE command
            elif cmd == "leavemute":
                await handle_leavemute(event)
            
            # PAPAY command
            elif cmd.startswith("papay"):
                target = message[len(current_prefix)+5:].strip() or None
                await handle_papay(event, target)
            
            # GROUPHELP command
            elif cmd == "grouphelp":
                await handle_grouphelp(event, current_prefix)
                
        except FloodWaitError as e:
            await event.reply(f"<blockquote>❌ <b>Tunggu {e.seconds} detik sebelum mencoba lagi</b></blockquote>", parse_mode="html")
        except Exception as e:
            await event.reply(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

    async def handle_join(event, query):
        """Handle join command"""
        processing_msg = None
        try:
            processing_msg = await event.reply("<blockquote>🔄 <b>Memproses permintaan join...</b></blockquote>", parse_mode="html")
            
            # Handle invite links
            if any(query.startswith(prefix) for prefix in ['https://t.me/', 't.me/', 'https://telegram.me/', 'telegram.me/']):
                if '+' in query:
                    hash_match = re.search(r'\+(.*?)(\/|$)', query)
                    if hash_match:
                        try:
                            await event.client(functions.messages.ImportChatInviteRequest(hash_match.group(1)))
                            await processing_msg.edit("<blockquote>✅ <b>Berhasil join via link undangan!</b></blockquote>", parse_mode="html")
                            return
                        except InviteHashExpiredError:
                            await processing_msg.edit("<blockquote>❌ <b>Link undangan sudah kadaluarsa</b></blockquote>", parse_mode="html")
                            return
                        except InviteHashInvalidError:
                            await processing_msg.edit("<blockquote>❌ <b>Link undangan tidak valid</b></blockquote>", parse_mode="html")
                            return
                        except ChannelPrivateError:
                            await processing_msg.edit("<blockquote>❌ <b>Grup bersifat private atau anda di-ban</b></blockquote>", parse_mode="html")
                            return
                        except Exception as e:
                            if "already a participant" in str(e):
                                await processing_msg.edit("<blockquote>ℹ️ <b>Anda sudah berada di grup ini</b></blockquote>", parse_mode="html")
                                return
                            raise
            
            # Try to resolve as username or ID
            try:
                entity = await event.client.get_entity(query)
                if isinstance(entity, (types.Channel, types.Chat)):
                    try:
                        await event.client(functions.channels.JoinChannelRequest(entity))
                        await processing_msg.edit(f"<blockquote>✅ <b>Berhasil join ke {entity.title}!</b></blockquote>", parse_mode="html")
                    except Exception as e:
                        if "already a participant" in str(e):
                            await processing_msg.edit(f"<blockquote>ℹ️ <b>Anda sudah berada di grup {entity.title}</b></blockquote>", parse_mode="html")
                        else:
                            raise
                else:
                    await processing_msg.edit("<blockquote>❌ <b>Target bukan grup/saluran yang valid</b></blockquote>", parse_mode="html")
            except ValueError:
                if not query.startswith('@'):
                    try:
                        entity = await event.client.get_entity(f'@{query}')
                        if isinstance(entity, (types.Channel, types.Chat)):
                            try:
                                await event.client(functions.channels.JoinChannelRequest(entity))
                                await processing_msg.edit(f"<blockquote>✅ <b>Berhasil join ke {entity.title}!</b></blockquote>", parse_mode="html")
                            except Exception as e:
                                if "already a participant" in str(e):
                                    await processing_msg.edit(f"<blockquote>ℹ️ <b>Anda sudah berada di grup {entity.title}</b></blockquote>", parse_mode="html")
                                else:
                                    raise
                        else:
                            await processing_msg.edit("<blockquote>❌ <b>Target bukan grup/saluran yang valid</b></blockquote>", parse_mode="html")
                    except Exception as e:
                        await processing_msg.edit("<blockquote>❌ <b>Tidak dapat menemukan grup/saluran tersebut</b></blockquote>", parse_mode="html")
            except UserNotParticipantError:
                await processing_msg.edit("<blockquote>❌ <b>Tidak bisa join, mungkin grup private atau membutuhkan approval</b></blockquote>", parse_mode="html")
            except Exception as e:
                await processing_msg.edit(f"<blockquote>❌ <b>Gagal join:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
        except Exception as e:
            if processing_msg:
                await processing_msg.edit(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
            else:
                await event.reply(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

    async def handle_leave(event, target):
        """Handle leave command"""
        processing_msg = None
        try:
            processing_msg = await event.reply("<blockquote>🔄 <b>Memproses permintaan leave...</b></blockquote>", parse_mode="html")
            
            if not target:
                await processing_msg.edit("<blockquote>❌ <b>Harap tentukan grup yang ingin ditinggalkan</b></blockquote>", parse_mode="html")
                return
                
            try:
                entity = await event.client.get_entity(target)
            except ValueError:
                if not target.startswith('@'):
                    try:
                        entity = await event.client.get_entity(f'@{target}')
                    except Exception:
                        await processing_msg.edit("<blockquote>❌ <b>Tidak dapat menemukan grup/saluran tersebut</b></blockquote>", parse_mode="html")
                        return
            
            if isinstance(entity, (types.Channel, types.Chat)):
                try:
                    await event.client(functions.channels.LeaveChannelRequest(entity))
                    await processing_msg.edit(f"<blockquote>✅ <b>Berhasil keluar dari {entity.title}!</b></blockquote>", parse_mode="html")
                except ChatAdminRequiredError:
                    await processing_msg.edit("<blockquote>❌ <b>Tidak bisa keluar karena anda admin</b></blockquote>", parse_mode="html")
                except Exception as e:
                    await processing_msg.edit(f"<blockquote>❌ <b>Gagal keluar:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
            else:
                await processing_msg.edit("<blockquote>❌ <b>Target bukan grup/saluran yang valid</b></blockquote>", parse_mode="html")
        except Exception as e:
            if processing_msg:
                await processing_msg.edit(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
            else:
                await event.reply(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

    async def handle_leavemute(event):
        """Handle leavemute command - LEAVE dari grup yang memute user"""
        processing_msg = None
        try:
            processing_msg = await event.reply("<blockquote>🔄 <b>Mencari grup yang memute anda...</b></blockquote>", parse_mode="html")
            
            # Dapatkan semua dialog
            dialogs = await event.client.get_dialogs()
            muted_groups = []
            
            for dialog in dialogs:
                # Hanya proses grup dan channel (bukan chat private)
                if dialog.is_group or dialog.is_channel:
                    try:
                        # Cek apakah user dimute di grup ini
                        participant = await event.client.get_permissions(dialog.entity, event.sender_id)
                        if participant and not participant.send_messages:
                            muted_groups.append(dialog.entity)
                    except Exception as e:
                        # Skip jika tidak bisa mendapatkan permissions
                        continue
            
            if not muted_groups:
                await processing_msg.edit("<blockquote>✅ <b>Tidak ada grup yang memute anda</b></blockquote>", parse_mode="html")
                return
            
            success = 0
            failed = 0
            results = []
            
            for group in muted_groups:
                try:
                    # Coba keluar dari grup
                    await event.client(functions.channels.LeaveChannelRequest(group))
                    success += 1
                    results.append(f"✅ Berhasil keluar dari: {getattr(group, 'title', 'Unknown Group')}")
                except ChatAdminRequiredError:
                    results.append(f"❌ Gagal keluar dari {getattr(group, 'title', 'Unknown Group')} (Anda admin)")
                    failed += 1
                except Exception as e:
                    results.append(f"❌ Gagal keluar dari {getattr(group, 'title', 'Unknown Group')}: {str(e)[:50]}")
                    failed += 1
                # Tunggu sebentar antara setiap operasi
                await asyncio.sleep(1)
            
            # Format hasil
            result_message = f"<blockquote>📊 <b>Hasil Leavemute:</b>\n"
            result_message += f"✅ <b>Berhasil:</b> {success}\n"
            result_message += f"❌ <b>Gagal:</b> {failed}\n\n"
            
            # Tambahkan detail untuk beberapa grup pertama
            for i, result in enumerate(results[:5]):  # Tampilkan maksimal 5 hasil
                result_message += f"{result}\n"
            
            if len(results) > 5:
                result_message += f"\n... dan {len(results) - 5} grup lainnya</blockquote>"
            else:
                result_message += "</blockquote>"
            
            await processing_msg.edit(result_message, parse_mode="html")
            
        except Exception as e:
            if processing_msg:
                await processing_msg.edit(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
            else:
                await event.reply(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

    async def handle_papay(event, target=None):
        """Handle papay command"""
        processing_msg = None
        try:
            if target:
                # Jika ada target, gunakan fungsi leave biasa
                await handle_leave(event, target)
            else:
                # Jika tidak ada target, keluar dari grup saat ini
                if event.is_private:
                    await event.reply("<blockquote>❌ <b>Command ini hanya bekerja di grup</b></blockquote>", parse_mode="html")
                    return
                
                processing_msg = await event.reply("<blockquote>🔄 <b>Memproses papay...</b></blockquote>", parse_mode="html")
                try:
                    await event.client(functions.channels.LeaveChannelRequest(event.chat_id))
                    await processing_msg.edit("<blockquote>Walah keluar si peler, papay juga</blockquote>", parse_mode="html")
                except ChatAdminRequiredError:
                    await processing_msg.edit("<blockquote>❌ <b>Tidak bisa keluar karena anda admin</b></blockquote>", parse_mode="html")
                except Exception as e:
                    await processing_msg.edit(f"<blockquote>❌ <b>Gagal keluar:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
        except Exception as e:
            if processing_msg:
                await processing_msg.edit(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")
            else:
                await event.reply(f"<blockquote>❌ <b>Error:</b> <code>{str(e)}</code></blockquote>", parse_mode="html")

    async def handle_grouphelp(event, prefix):
        """Handle grouphelp command"""
        help_text = f"""
<blockquote>
<b>⪼ Dokumen untuk Join/Leave</b>

<b>ᐈ Perintah:</b> <code>{prefix}join [link/username]</code>
<b>ᐉ Keterangan:</b> Gabung ke grup/channel (support invite link)

<b>ᐈ Perintah:</b> <code>{prefix}leave [target]</code>
<b>ᐉ Keterangan:</b> Keluar dari grup/channel (kecuali admin)

<b>ᐈ Perintah:</b> <code>{prefix}leavemute</code>
<b>ᐉ Keterangan:</b> Keluar dari semua grup yang memute anda

<b>ᐈ Perintah:</b> <code>{prefix}papay</code>
<b>ᐉ Keterangan:</b> Keluar dari grup saat ini
</blockquote>
"""
        await event.reply(help_text, parse_mode="html")