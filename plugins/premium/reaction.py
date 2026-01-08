import json
import os
import random
from telethon import events, types
from telethon.tl.functions.messages import SendReactionRequest
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

def load_active_connections():
    """Load active premium connections from file"""
    try:
        with open('premium/active_connections.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"connections": {}}

async def setup(bot, client, user_id):
    """Setup reaction tracking for owner and premium users"""
    current_user_id = user_id
    
    # Store active premium clients from alfread.py
    from alfread import active_premium_sessions
    
    # Popular emoji sets for different reactions
    EMOJI_SETS = {
        'like': ['👍', '❤️', '🔥', '⭐', '🎯'],
        'love': ['❤️', '💕', '💖', '💗', '😍'],
        'laugh': ['😂', '🤣', '😆', '😄', '🎭'],
        'surprise': ['😮', '🤯', '😲', '👀', '✨'],
        'sad': ['😢', '😭', '💔', '😔', '🌧️'],
        'angry': ['😠', '🤬', '💢', '👿', '⚡'],
        'celebrate': ['🎉', '🎊', '🥳', '🎁', '🏆']
    }
    
    # Track owner's reactions to messages
    owner_reactions = {}
    
    @client.on(events.MessageEdited(chats=OWNER_ID))
    @client.on(events.NewMessage(from_users=OWNER_ID))
    async def track_owner_reactions(event):
        """Track when owner reacts to messages"""
        if event.reactions:
            # Get the latest reaction from owner
            reaction = event.reactions.results[-1] if event.reactions.results else None
            if reaction and hasattr(reaction, 'reaction'):
                # Store reaction info
                owner_reactions[event.id] = {
                    'chat_id': event.chat_id,
                    'message_id': event.id,
                    'reaction': reaction.reaction,
                    'timestamp': event.date.timestamp()
                }
    
    @client.on(events.MessageEdited(chats=OWNER_ID))
    @client.on(events.NewMessage(from_users=OWNER_ID))
    async def handle_owner_reaction(event):
        """Handle owner's reactions and mirror to premium users"""
        # Only process if it's a reaction update
        if not event.reactions:
            return
            
        # Get the message being reacted to
        if event.is_reply:
            replied_msg = await event.get_reply_message()
            msg_id = replied_msg.id
            chat_id = replied_msg.chat_id
        else:
            msg_id = event.id
            chat_id = event.chat_id
        
        # Get owner's reaction
        reaction_result = None
        if event.reactions.results:
            for result in event.reactions.results:
                if hasattr(result, 'reaction'):
                    reaction_result = result.reaction
                    break
        
        if not reaction_result:
            return
            
        # Determine reaction category based on emoji
        reaction_emoji = ""
        if isinstance(reaction_result, types.ReactionEmoji):
            reaction_emoji = reaction_result.emoticon
        elif isinstance(reaction_result, types.ReactionCustomEmoji):
            reaction_emoji = f"emoji_{reaction_result.document_id}"
        
        # Categorize the reaction to select appropriate emoji set
        reaction_category = 'like'  # default
        
        if reaction_emoji in ['❤️', '💕', '💖', '💗', '😍']:
            reaction_category = 'love'
        elif reaction_emoji in ['😂', '🤣', '😆', '😄']:
            reaction_category = 'laugh'
        elif reaction_emoji in ['😮', '🤯', '😲', '👀']:
            reaction_category = 'surprise'
        elif reaction_emoji in ['😢', '😭', '💔', '😔']:
            reaction_category = 'sad'
        elif reaction_emoji in ['😠', '🤬', '💢', '👿']:
            reaction_category = 'angry'
        elif reaction_emoji in ['🎉', '🎊', '🥳', '🎁']:
            reaction_category = 'celebrate'
        
        # Get available emojis for this category
        available_emojis = EMOJI_SETS.get(reaction_category, EMOJI_SETS['like'])
        
        # Send reactions from all active premium users
        active_connections = load_active_connections()
        reacted_users = 0
        
        for user_id_str, session_str in active_connections.get("connections", {}).items():
            try:
                user_id = int(user_id_str)
                
                # Get the premium client from active sessions
                premium_client = active_premium_sessions.get(user_id)
                if not premium_client or not premium_client.is_connected():
                    continue
                
                # Select a random emoji from the appropriate set (different for each user)
                user_emoji = random.choice(available_emojis)
                
                # Send reaction
                await premium_client(SendReactionRequest(
                    peer=chat_id,
                    msg_id=msg_id,
                    reaction=[types.ReactionEmoji(emoticon=user_emoji)]
                ))
                
                reacted_users += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                # Skip errors (user might not have access to the chat, etc.)
                continue
        
        # Log the reaction mirroring
        if reacted_users > 0:
            print(f"✅ Owner reaction mirrored by {reacted_users} premium users")
    
    # Also allow premium users to manually trigger reaction mirroring
    @client.on(events.NewMessage())
    async def premium_react_command(event):
        """Handle premium user react commands"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # Helper function to check commands
        def is_command(cmd):
            if current_prefix == "no":
                return msg.lower() == cmd.lower()
            return msg.lower().startswith(f"{current_prefix}{cmd.lower()}")
        
        # React command - mirror owner's last reaction
        if is_command("react"):
            if not owner_reactions:
                await event.reply("<blockquote>❌ No owner reactions found yet</blockquote>", parse_mode="html")
                return
            
            # Get the most recent owner reaction
            latest_reaction = max(owner_reactions.values(), key=lambda x: x['timestamp'])
            
            try:
                # Send the same reaction from premium user
                await client(SendReactionRequest(
                    peer=latest_reaction['chat_id'],
                    msg_id=latest_reaction['message_id'],
                    reaction=[latest_reaction['reaction']]
                ))
                
                await event.reply("<blockquote>✅ Reacted to owner's last message</blockquote>", parse_mode="html")
            except Exception as e:
                await event.reply(f"<blockquote>❌ Failed to react: {str(e)}</blockquote>", parse_mode="html")
        
        # Reactall command - make all premium users react to a message
        elif is_command("reactall") and event.is_reply:
            if event.sender_id != OWNER_ID:
                await event.reply("<blockquote>❌ This command is owner-only</blockquote>", parse_mode="html")
                return
                
            replied_msg = await event.get_reply_message()
            reaction_emoji = msg[len(current_prefix)+8:].strip() or "❤️"
            
            active_connections = load_active_connections()
            reacted_users = 0
            
            for user_id_str, session_str in active_connections.get("connections", {}).items():
                try:
                    user_id = int(user_id_str)
                    premium_client = active_premium_sessions.get(user_id)
                    if not premium_client or not premium_client.is_connected():
                        continue
                    
                    await premium_client(SendReactionRequest(
                        peer=replied_msg.chat_id,
                        msg_id=replied_msg.id,
                        reaction=[types.ReactionEmoji(emoticon=reaction_emoji)]
                    ))
                    
                    reacted_users += 1
                    await asyncio.sleep(0.1)
                    
                except Exception:
                    continue
            
            await event.reply(f"<blockquote>✅ {reacted_users} premium users reacted with {reaction_emoji}</blockquote>", parse_mode="html")