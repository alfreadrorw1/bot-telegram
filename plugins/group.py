# plugins/groupmanager.py
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
from config import OWNER_ID, BOT_USERNAME

def get_prefix():
    """Get current prefix from config"""
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
    async def group_manager_handler(event):
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        lower_message = message.lower()
        
        # Check if message is a group manager command
        is_cmd = False
        cmd = None
        
        commands = {
            'join': (lambda m: m.startswith('join ')),
            'leave': (lambda m: m.startswith('leave ')),
            'leavemute': (lambda m: m == 'leavemute'),
            'papay': (lambda m: m.startswith('papay'))
        }
        
        for command, check in commands.items():
            if (current_prefix == "no" and check(lower_message)) or \
               (lower_message.startswith(current_prefix.lower()) and 
                check(lower_message[len(current_prefix):].strip())):
                is_cmd = True
                cmd = command
                break
        
        if not is_cmd or event.sender_id != OWNER_ID:
            return

        try:
            if cmd == "join":
                query = message.split(' ', 1)[1] if current_prefix == "no" else message[len(current_prefix):].strip().split(' ', 1)[1]
                await handle_join(event, query)
            elif cmd == "leave":
                target = message.split(' ', 1)[1] if current_prefix == "no" else message[len(current_prefix):].strip().split(' ', 1)[1]
                await handle_leave(event, target)
            elif cmd == "leavemute":
                await handle_leavemute(event)
            elif cmd == "papay":
                target = message.split(' ', 1)[1] if len(message.split()) > 1 else None
                await handle_papay(event, target)
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
        """Handle leavemute command"""
        processing_msg = None
        try:
            processing_msg = await event.reply("<blockquote>🔄 <b>Mencari grup yang memute anda...</b></blockquote>", parse_mode="html")
            dialogs = await event.client.get_dialogs()
            muted_groups = []
            
            for dialog in dialogs:
                if dialog.is_group or dialog.is_channel:
                    try:
                        participant = await event.client.get_permissions(dialog.entity, event.sender_id)
                        if participant and not participant.send_messages:
                            muted_groups.append(dialog.entity)
                    except Exception:
                        continue
            
            if not muted_groups:
                await processing_msg.edit("<blockquote>✅ <b>Tidak ada grup yang memute anda</b></blockquote>", parse_mode="html")
                return
            
            success = 0
            for group in muted_groups:
                try:
                    await event.client(functions.channels.LeaveChannelRequest(group))
                    success += 1
                except Exception:
                    continue
            
            await processing_msg.edit(f"<blockquote>✅ <b>Berhasil keluar dari {success} grup yang memute</b></blockquote>", parse_mode="html")
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
                await handle_leave(event, target)
            else:
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

    @user.on(events.NewMessage())
    async def group_manager_help(event):
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip().lower()
        
        is_help = (current_prefix == "no" and message == "grouphelp") or \
                 (message.startswith(current_prefix.lower()) and message[len(current_prefix):].strip() == "grouphelp")
        
        if not is_help:
            return

        help_text = f"""
<blockquote>
<b>⪼ Dokumen untuk Join/Leave</b>

<b>ᐈ Perintah:</b> <code>{"join [link/username]" if current_prefix == "no" else f"{current_prefix}join [link/username]"}</code>
<b>ᐉ Keterangan:</b> Gabung ke grup/channel (support invite link)

<b>ᐈ Perintah:</b> <code>{"leave [target]" if current_prefix == "no" else f"{current_prefix}leave [target]"}</code>
<b>ᐉ Keterangan:</b> Keluar dari grup/channel (kecuali admin)

<b>ᐈ Perintah:</b> <code>{"leavemute" if current_prefix == "no" else f"{current_prefix}leavemute"}</code>
<b>ᐉ Keterangan:</b> Keluar dari semua grup yang memute anda

<b>ᐈ Perintah:</b> <code>{"papay" if current_prefix == "no" else f"{current_prefix}papay"}</code>
<b>ᐉ Keterangan:</b> Keluar dari grup saat ini
</blockquote>
"""
        await event.reply(help_text, parse_mode="html")