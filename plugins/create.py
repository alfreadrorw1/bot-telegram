import os
import json
import re
from datetime import datetime
from telethon import events
from telethon.tl.functions.channels import CreateChannelRequest, DeleteChannelRequest
from telethon.tl.functions.messages import CreateChatRequest, ExportChatInviteRequest, DeleteChatRequest
from telethon.tl.types import InputUserSelf
from config import OWNER_ID

# Configuration
CONFIG_DIR = 'data'
PREFIX_FILE = os.path.join(CONFIG_DIR, 'prefix.json')
CREATION_LOG_FILE = os.path.join(CONFIG_DIR, 'created_chats.json')

def get_live_prefix():
    """Get current prefix directly from file"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
    except (FileNotFoundError, json.JSONDecodeError):
        return '.'

def load_created_chats():
    """Load list of created chats"""
    try:
        with open(CREATION_LOG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'groups': [], 'channels': []}

def save_created_chats(data):
    """Save list of created chats"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CREATION_LOG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def setup(bot, user):
    def is_command(msg, commands, prefix):
        """Check if message matches any of the commands"""
        msg = msg.strip()
        if not msg:
            return False
        
        if not prefix:  # When prefix is "no"
            first_word = msg.split()[0].lower() if msg else ""
            return first_word in commands
        else:
            return any(msg.startswith(f"{prefix}{cmd}") for cmd in commands)

    def get_args(msg, command, prefix):
        """Extract arguments from command"""
        msg = msg.strip()
        if not msg:
            return ""
        
        if not prefix:  # When prefix is "no"
            parts = msg.split()
            return ' '.join(parts[1:]) if len(parts) > 1 else ""
        else:
            return msg[len(prefix + command):].strip()

    @user.on(events.NewMessage(outgoing=True, from_users=OWNER_ID))
    async def creation_handler(event):
        msg = (event.text or '').strip()
        current_prefix = get_live_prefix()
        
        # Command definitions
        commands = {
            'creategc': {'type': 'group', 'aliases': ['creategroup']},
            'createch': {'type': 'channel', 'aliases': ['createchannel']},
            'delgc': {'type': 'delete_group', 'aliases': ['deletegroup']},
            'delch': {'type': 'delete_channel', 'aliases': ['deletechannel']},
            'createlist': {'type': 'list', 'aliases': ['listcreated']}
        }

        # Find matching command
        command_info = None
        used_command = None
        
        for cmd, info in commands.items():
            check_commands = [cmd] + info['aliases']
            if is_command(msg, check_commands, current_prefix):
                command_info = info
                used_command = next(
                    (c for c in check_commands 
                     if msg.startswith(f"{current_prefix}{c}" if current_prefix else c)),
                    None
                )
                break

        if not command_info or not used_command:
            return

        # Handle different command types
        if command_info['type'] in ['group', 'channel']:
            chat_type = "Group" if command_info['type'] == 'group' else "Channel"
            args = get_args(msg, used_command, current_prefix)
            
            if not args:
                await event.reply(
                    f"<blockquote>❌ <b>Format salah!</b>\n"
                    f"Gunakan: <code>{(current_prefix if current_prefix else '')}{used_command} &lt;nama&gt;</code></blockquote>",
                    parse_mode="html"
                )
                return

            processing_msg = await event.reply(
                "<blockquote>⏳ <b>Sedang membuat {}...</b></blockquote>".format(chat_type.lower()),
                parse_mode="html"
            )
            
            try:
                if command_info['type'] == 'group':
                    # Create group with self as participant
                    created = await user(CreateChatRequest(
                        users=[InputUserSelf()],
                        title=args
                    ))
                    chat_id = created.chats[0].id
                    invite = await user(ExportChatInviteRequest(peer=chat_id))
                else:
                    created = await user(CreateChannelRequest(
                        title=args, 
                        about="", 
                        megagroup=False,
                        broadcast=True
                    ))
                    chat_id = created.chats[0].id
                    invite = await user(ExportChatInviteRequest(peer=chat_id))

                # Save to created list
                created_chats = load_created_chats()
                key = 'groups' if command_info['type'] == 'group' else 'channels'
                created_chats[key].append({
                    'id': chat_id,
                    'title': args,
                    'link': invite.link,
                    'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                })
                save_created_chats(created_chats)

                # Format response
                response = (
                    "<blockquote>「 <b>Create {}</b> 」\n\n"
                    "▸ <b>Name:</b> {}\n"
                    "▸ <b>Owner:</b> <a href='tg://user?id={}'>You</a>\n"
                    "▸ <b>Creation:</b> {}\n\n"
                    "<a href='{}'>Join Link</a></blockquote>"
                ).format(
                    chat_type,
                    args,
                    OWNER_ID,
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    invite.link
                )
                
                await processing_msg.delete()
                await event.reply(response, parse_mode="html", link_preview=False)

            except Exception as e:
                await processing_msg.edit(
                    f"<blockquote>❌ <b>Gagal membuat {chat_type.lower()}:</b> <code>{str(e)[:200]}</code></blockquote>",
                    parse_mode="html"
                )
                return

        elif command_info['type'] in ['delete_group', 'delete_channel']:
            chat_type = "Group" if command_info['type'] == 'delete_group' else "Channel"
            args = get_args(msg, used_command, current_prefix)
            
            if not args:
                await event.reply(
                    f"<blockquote>❌ <b>Format salah!</b>\n"
                    f"Gunakan: <code>{(current_prefix if current_prefix else '')}{used_command} &lt;id_chat&gt;</code></blockquote>",
                    parse_mode="html"
                )
                return

            try:
                chat_id = int(args)
            except ValueError:
                await event.reply("<blockquote>❌ <b>ID harus berupa angka!</b></blockquote>", parse_mode="html")
                return

            processing_msg = await event.reply(
                f"<blockquote>⏳ <b>Sedang menghapus {chat_type.lower()}...</b></blockquote>",
                parse_mode="html"
            )
            
            try:
                if command_info['type'] == 'delete_group':
                    await user(DeleteChatRequest(chat_id))
                else:
                    await user(DeleteChannelRequest(channel=chat_id))

                # Remove from created list
                created_chats = load_created_chats()
                key = 'groups' if command_info['type'] == 'delete_group' else 'channels'
                created_chats[key] = [c for c in created_chats[key] if c['id'] != chat_id]
                save_created_chats(created_chats)

                await processing_msg.edit(
                    f"<blockquote>✅ <b>{chat_type} berhasil dihapus</b></blockquote>",
                    parse_mode="html"
                )
            except Exception as e:
                await processing_msg.edit(
                    f"<blockquote>❌ <b>Gagal menghapus {chat_type.lower()}:</b> <code>{str(e)[:200]}</code></blockquote>",
                    parse_mode="html"
                )
                return

        elif command_info['type'] == 'list':
            created_chats = load_created_chats()
            
            if not created_chats['groups'] and not created_chats['channels']:
                await event.reply("<blockquote>📭 <b>Belum ada grup/channel yang dibuat</b></blockquote>", parse_mode="html")
                return

            response = ["<blockquote>📋 <b>Daftar Chat yang Dibuat:</b>"]
            
            if created_chats['groups']:
                response.append("\n<b>Groups:</b>")
                for group in created_chats['groups']:
                    response.append(
                        f"├ <b>{group['title']}</b>\n"
                        f"├ ID: <code>{group['id']}</code>\n"
                        f"├ Dibuat: {group['date']}\n"
                        f"└ <a href='{group['link']}'>Join Link</a>"
                    )

            if created_chats['channels']:
                response.append("\n<b>Channels:</b>")
                for channel in created_chats['channels']:
                    response.append(
                        f"├ <b>{channel['title']}</b>\n"
                        f"├ ID: <code>{channel['id']}</code>\n"
                        f"├ Dibuat: {channel['date']}\n"
                        f"└ <a href='{channel['link']}'>Join Link</a>"
                    )
            
            response.append("</blockquote>")
            await event.reply('\n'.join(response), parse_mode="html", link_preview=False)