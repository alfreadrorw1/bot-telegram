# plugins/vctools.py
from telethon import events, functions, types
from config import OWNER_ID
import asyncio
import random
import logging
import json
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

async def setup(bot, user):
    active_calls = {}  # Track active calls to prevent auto-leaving
    MIN_JOIN_TIME = 300  # Minimum time to stay in VC (5 minutes)
    
    async def get_active_call(chat):
        try:
            if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
                full_chat = await user(functions.channels.GetFullChannelRequest(chat))
                if full_chat and hasattr(full_chat.full_chat, 'call'):
                    return full_chat.full_chat.call
            return None
        except Exception as e:
            logger.error(f"Error getting active call: {e}")
            return None

    @user.on(events.NewMessage())
    async def vc_handler(event):
        current_prefix = get_prefix()
        message = (event.raw_text or '').strip()
        
        # Check if message is a VC command
        is_vc_cmd = (
            (current_prefix == "no" and message.lower() in ["startvc", "stopvc", "joinvc", "leavevc"]) or
            (message.startswith(current_prefix) and 
             message[len(current_prefix):].strip().lower() in ["startvc", "stopvc", "joinvc", "leavevc"])
        )
        
        if not is_vc_cmd or event.sender_id != OWNER_ID:
            return

        cmd = message.lower() if current_prefix == "no" else message[len(current_prefix):].strip().lower()
        
        if cmd == "startvc":
            await handle_startvc(event)
        elif cmd == "stopvc":
            await handle_stopvc(event)
        elif cmd == "joinvc":
            await handle_joinvc(event)
        elif cmd == "leavevc":
            await handle_leavevc(event)

    async def handle_startvc(event):
        reply = await event.reply("<blockquote>🔄 Memulai voice chat...</blockquote>", parse_mode="html")
        try:
            chat = await event.get_chat()
            input_peer = await user.get_input_entity(chat)
            
            if not isinstance(input_peer, (types.InputPeerChannel, types.InputPeerChat)):
                await reply.edit("<blockquote>❌ Jenis chat tidak didukung</blockquote>", parse_mode="html")
                return

            result = await user(functions.phone.CreateGroupCallRequest(
                peer=input_peer,
                random_id=random.randint(0, 0x7fffffff)
            ))
            await reply.edit(
                f"<blockquote><b>✅ Voice chat dimulai di:</b> {chat.title}</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            logger.error(f"StartVC error: {e}")
            await reply.edit(
                f"<blockquote>❌ Gagal memulai: {str(e)}</blockquote>",
                parse_mode="html"
            )

    async def handle_stopvc(event):
        reply = await event.reply("<blockquote>🔄 Menghentikan voice chat...</blockquote>", parse_mode="html")
        try:
            chat = await event.get_chat()
            input_peer = await user.get_input_entity(chat)
            call = await get_active_call(input_peer)
            
            if not call:
                await reply.edit("<blockquote>❌ Tidak ada voice chat aktif</blockquote>", parse_mode="html")
                return

            await user(functions.phone.DiscardGroupCallRequest(
                call=types.InputGroupCall(
                    id=int(call.id),
                    access_hash=int(call.access_hash)
                )
            ))
            await reply.edit(
                f"<blockquote><b>✅ Voice chat dihentikan di:</b> {chat.title}</blockquote>",
                parse_mode="html"
            )
        except Exception as e:
            logger.error(f"StopVC error: {e}")
            await reply.edit(
                f"<blockquote>❌ Gagal menghentikan: {str(e)}</blockquote>",
                parse_mode="html"
            )

    async def handle_joinvc(event):
        reply = await event.reply("<blockquote>🔄 Bergabung ke voice chat...</blockquote>", parse_mode="html")
        try:
            chat = await event.get_chat()
            input_peer = await user.get_input_entity(chat)
            call = await get_active_call(input_peer)
            
            if not call:
                await reply.edit("<blockquote>❌ Tidak ada voice chat aktif</blockquote>", parse_mode="html")
                return

            me = await user.get_me()
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
            
            await user(functions.phone.JoinGroupCallRequest(
                call=input_group_call,
                join_as=input_user,
                muted=False,
                video_stopped=False,
                params=types.DataJSON(data=json.dumps(join_params))
            ))
            
            # Track this call to prevent auto-leaving
            active_calls[call.id] = {
                'chat_id': event.chat_id,
                'join_time': time.time(),
                'manual_join': True  # Mark as manually joined
            }
            
            await reply.edit(
                f"<blockquote><b>✅ Bergabung ke voice chat di:</b> {chat.title}</blockquote>",
                parse_mode="html"
            )
            
        except Exception as e:
            logger.error(f"JoinVC error: {e}")
            await reply.edit(
                f"<blockquote>❌ Gagal bergabung: {str(e)}</blockquote>",
                parse_mode="html"
            )

    async def handle_leavevc(event):
        reply = await event.reply("<blockquote>🔄 Meninggalkan voice chat...</blockquote>", parse_mode="html")
        try:
            chat = await event.get_chat()
            input_peer = await user.get_input_entity(chat)
            call = await get_active_call(input_peer)
            
            if not call:
                await reply.edit("<blockquote>❌ Tidak ada voice chat aktif</blockquote>", parse_mode="html")
                return

            me = await user.get_me()
            await user(functions.phone.LeaveGroupCallRequest(
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
                f"<blockquote><b>✅ Meninggalkan voice chat di:</b> {chat.title}</blockquote>",
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
                            chat = await user.get_input_entity(call_data['chat_id'])
                            call = await get_active_call(chat)
                            
                            if call and call.id == call_id:
                                me = await user.get_me()
                                await user(functions.phone.JoinGroupCallRequest(
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