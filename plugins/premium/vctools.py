# plugins/vctools.py
from telethon import events, functions, types
from config import OWNER_ID
import asyncio
import random
import logging
import json
import os
import time
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            prefix = json.load(f).get('prefix', '.')
            return prefix if prefix != "no" else ""
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

async def setup(bot, client, user_id):
    current_user_id = user_id
    active_calls = {}  # Track active calls to prevent auto-leaving
    MIN_JOIN_TIME = 300  # Minimum time to stay in VC (5 minutes)
    
    async def get_active_call(chat):
        try:
            if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
                full_chat = await client(functions.channels.GetFullChannelRequest(chat))
                if full_chat and hasattr(full_chat.full_chat, 'call'):
                    return full_chat.full_chat.call
            return None
        except Exception as e:
            logger.error(f"Error getting active call: {e}")
            return None

    async def resolve_chat_entity(chat_input):
        """Resolve chat entity from various input formats"""
        try:
            if chat_input is None:
                return None
                
            # Try to get entity directly
            if isinstance(chat_input, (int, str)):
                return await client.get_entity(chat_input)
            return chat_input
        except Exception as e:
            logger.error(f"Error resolving chat entity: {e}")
            return None

    @client.on(events.NewMessage())
    async def vc_handler(event):
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        message = (event.raw_text or '').strip()
        
        # Check if message is a VC command
        vc_commands = ["startvc", "stavc", "stopvc", "stovc", "joinvc", "jvc", "leavevc", "lvc"]
        
        is_vc_cmd = False
        cmd = ""
        
        if current_prefix == "":
            # No prefix mode
            for vc_cmd in vc_commands:
                if message.lower().startswith(vc_cmd):
                    is_vc_cmd = True
                    cmd = vc_cmd
                    break
        else:
            # With prefix mode
            if message.startswith(current_prefix):
                msg_without_prefix = message[len(current_prefix):].strip().lower()
                for vc_cmd in vc_commands:
                    if msg_without_prefix.startswith(vc_cmd):
                        is_vc_cmd = True
                        cmd = vc_cmd
                        break
        
        if not is_vc_cmd:
            return

        # Extract target chat if provided
        target_chat = None
        if " " in message:
            # Extract the part after the command
            if current_prefix == "":
                parts = message.split(" ", 1)
                if len(parts) > 1:
                    target_chat = parts[1].strip()
            else:
                parts = message[len(current_prefix):].strip().split(" ", 1)
                if len(parts) > 1:
                    target_chat = parts[1].strip()
        
        # Map aliases to main commands
        if cmd in ["stavc"]:
            cmd = "startvc"
        elif cmd in ["stovc"]:
            cmd = "stopvc"
        elif cmd in ["jvc"]:
            cmd = "joinvc"
        elif cmd in ["lvc"]:
            cmd = "leavevc"
        
        if cmd == "startvc":
            await handle_startvc(event, target_chat)
        elif cmd == "stopvc":
            await handle_stopvc(event, target_chat)
        elif cmd == "joinvc":
            await handle_joinvc(event, target_chat)
        elif cmd == "leavevc":
            await handle_leavevc(event, target_chat)

    async def handle_startvc(event, target_chat=None):
        reply = await event.reply("<blockquote>🔄 Memulai voice chat...</blockquote>", parse_mode="html")
        try:
            chat = None
            if target_chat:
                # Use specified chat
                chat = await resolve_chat_entity(target_chat)
                if not chat:
                    await reply.edit("<blockquote>❌ Tidak dapat menemukan chat yang dimaksud</blockquote>", parse_mode="html")
                    return
            else:
                # Use current chat
                chat = await event.get_chat()
            
            input_peer = await client.get_input_entity(chat)
            
            if not isinstance(input_peer, (types.InputPeerChannel, types.InputPeerChat)):
                await reply.edit("<blockquote>❌ Jenis chat tidak didukung</blockquote>", parse_mode="html")
                return

            result = await client(functions.phone.CreateGroupCallRequest(
                peer=input_peer,
                random_id=random.randint(0, 0x7fffffff)
            ))
            await reply.edit(
                f"<blockquote><b>✅ Voice chat dimulai di:</b> {getattr(chat, 'title', 'Unknown Chat')}</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            logger.error(f"StartVC error: {e}")
            await reply.edit(
                f"<blockquote>❌ Gagal memulai: {str(e)}</blockquote>",
                parse_mode="html"
            )

    async def handle_stopvc(event, target_chat=None):
        reply = await event.reply("<blockquote>🔄 Menghentikan voice chat...</blockquote>", parse_mode="html")
        try:
            chat = None
            if target_chat:
                # Use specified chat
                chat = await resolve_chat_entity(target_chat)
                if not chat:
                    await reply.edit("<blockquote>❌ Tidak dapat menemukan chat yang dimaksud</blockquote>", parse_mode="html")
                    return
            else:
                # Use current chat
                chat = await event.get_chat()
            
            input_peer = await client.get_input_entity(chat)
            call = await get_active_call(input_peer)
            
            if not call:
                await reply.edit("<blockquote>❌ Tidak ada voice chat aktif</blockquote>", parse_mode="html")
                return

            await client(functions.phone.DiscardGroupCallRequest(
                call=types.InputGroupCall(
                    id=int(call.id),
                    access_hash=int(call.access_hash)
                )
            ))
            await reply.edit(
                f"<blockquote><b>✅ Voice chat dihentikan di:</b> {getattr(chat, 'title', 'Unknown Chat')}</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            logger.error(f"StopVC error: {e}")
            await reply.edit(
                f"<blockquote>❌ Gagal menghentikan: {str(e)}</blockquote>",
                parse_mode="html"
            )

    async def handle_joinvc(event, target_chat=None):
        reply = await event.reply("<blockquote>🔄 Bergabung ke voice chat...</blockquote>", parse_mode="html")
        try:
            chat = None
            if target_chat:
                # Use specified chat
                chat = await resolve_chat_entity(target_chat)
                if not chat:
                    await reply.edit("<blockquote>❌ Tidak dapat menemukan chat yang dimaksud</blockquote>", parse_mode="html")
                    return
            else:
                # Use current chat
                chat = await event.get_chat()
            
            input_peer = await client.get_input_entity(chat)
            call = await get_active_call(input_peer)
            
            if not call:
                await reply.edit("<blockquote>❌ Tidak ada voice chat aktif</blockquote>", parse_mode="html")
                return

            me = await client.get_me()
            input_user = types.InputPeerUser(
                user_id=me.id,
                access_hash=me.access_hash
            )
            
            # Create proper InputGroupCall object
            input_group_call = types.InputGroupCall(
                id=call.id,
                access_hash=call.access_hash
            )
            
            # Create proper join parameters
            join_params = {
                'ufrag': str(random.randint(100000, 999999)),
                'pwd': str(random.randint(1000000, 9999999)),
                'fingerprints': [],
                'ssrc': random.randint(1, 2147483647),
                'ssrc-groups': [],
                'rtcp-mux': True
            }
            
            await client(functions.phone.JoinGroupCallRequest(
                call=input_group_call,
                join_as=input_user,
                muted=False,
                video_stopped=False,
                params=types.DataJSON(data=json.dumps(join_params))
            ))
            
            # Track this call to prevent auto-leaving
            chat_id = chat.id if hasattr(chat, 'id') else event.chat_id
            active_calls[call.id] = {
                'chat_id': chat_id,
                'join_time': time.time(),
                'manual_join': True  # Mark as manually joined
            }
            
            await reply.edit(
                f"<blockquote><b>✅ Bergabung ke voice chat di:</b> {getattr(chat, 'title', 'Unknown Chat')}</blockquote>",
                parse_mode="html"
            )
            
        except Exception as e:
            logger.error(f"JoinVC error: {e}")
            await reply.edit(
                f"<blockquote>❌ Gagal bergabung: {str(e)}</blockquote>",
                parse_mode="html"
            )

    async def handle_leavevc(event, target_chat=None):
        reply = await event.reply("<blockquote>🔄 Meninggalkan voice chat...</blockquote>", parse_mode="html")
        try:
            chat = None
            if target_chat:
                # Use specified chat
                chat = await resolve_chat_entity(target_chat)
                if not chat:
                    await reply.edit("<blockquote>❌ Tidak dapat menemukan chat yang dimaksud</blockquote>", parse_mode="html")
                    return
            else:
                # Use current chat
                chat = await event.get_chat()
            
            input_peer = await client.get_input_entity(chat)
            call = await get_active_call(input_peer)
            
            if not call:
                await reply.edit("<blockquote>❌ Tidak ada voice chat aktif</blockquote>", parse_mode="html")
                return

            me = await client.get_me()
            await client(functions.phone.LeaveGroupCallRequest(
                call=types.InputGroupCall(
                    id=int(call.id),
                    access_hash=int(call.access_hash)
                ),
                source=0  # Using simple source instead of InputPeer
            ))
            
            # Remove from active calls tracking
            if call.id in active_calls:
                del active_calls[call.id]
                
            await reply.edit(
                f"<blockquote><b>✅ Meninggalkan voice chat di:</b> {getattr(chat, 'title', 'Unknown Chat')}</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            logger.error(f"LeaveVC error: {e}")
            await reply.edit(
                f"<blockquote>❌ Gagal meninggalkan: {str(e)}</blockquote>",
                parse_mode="html"
            )

    # Background task to keep the bot in VC
    async def keep_in_vc():
        while True:
            try:
                current_time = time.time()
                for call_id, call_data in list(active_calls.items()):
                    # Only rejoin if it was a manual join and we've been in the call for more than MIN_JOIN_TIME
                    if call_data.get('manual_join') and current_time - call_data['join_time'] > MIN_JOIN_TIME:
                        try:
                            chat = await client.get_input_entity(call_data['chat_id'])
                            call = await get_active_call(chat)
                            
                            if call and call.id == call_id:
                                me = await client.get_me()
                                await client(functions.phone.JoinGroupCallRequest(
                                    call=types.InputGroupCall(
                                        id=call.id,
                                        access_hash=call.access_hash
                                    ),
                                    join_as=types.InputPeerUser(
                                        user_id=me.id,
                                        access_hash=me.access_hash
                                    ),
                                    muted=True,
                                    video_stopped=False,
                                    params=types.DataJSON(data=json.dumps({
                                        'ufrag': str(random.randint(100000, 999999)),
                                        'pwd': str(random.randint(1000000, 9999999)),
                                        'fingerprints': [],
                                        'ssrc': random.randint(1, 2147483647),
                                        'ssrc-groups': [],
                                        'rtcp-mux': True
                                    }))
                                ))
                                active_calls[call_id]['join_time'] = current_time
                                logger.info(f"Rejoined VC in chat {call_data['chat_id']}")
                        except Exception as e:
                            logger.error(f"KeepInVC error: {e}")
                            if call_id in active_calls:
                                del active_calls[call_id]
            except Exception as e:
                logger.error(f"Background task error: {e}")
            
            await asyncio.sleep(60)  # Check every minute

    # Start the background task
    asyncio.create_task(keep_in_vc())