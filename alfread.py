import logging
from telethon import TelegramClient, events
import asyncio
import os
import importlib
import json
import inspect
import time
from telethon.sessions import StringSession
from config import *

# Setup folders and files
os.makedirs('cache', exist_ok=True)
os.makedirs('data/users', exist_ok=True)
os.makedirs('premium/premium_sessions', exist_ok=True)
os.makedirs('data', exist_ok=True)

# File paths
PREMIUM_FILE = 'premium/premium.json'
UPTIME_FILE = 'premium/uptime.json'
PREFIX_FILE = 'premium/prefix.json'
ACTIVE_CONNECTIONS_FILE = 'premium/active_connections.json'

logging.basicConfig(level=logging.WARNING)
logging.getLogger('telethon').setLevel(logging.WARNING)

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Initialize Clients
bot = TelegramClient('cache/bot_session', API_ID, API_HASH)
user = TelegramClient('cache/user_session', API_ID, API_HASH)
connect_bot = TelegramClient('cache/connect_bot_session', API_ID, API_HASH) if BOT_TOKEN2 else None

# In-memory storage
active_premium_sessions = {}  # {user_id: TelegramClient}

def print_success(message):
    """Print success message with green color and checkmark emoji"""
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    """Print error message with red color and cross emoji"""
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def print_info(message):
    """Print info message with blue color and info emoji"""
    print(f"{Colors.BLUE}👥  {message}{Colors.ENDC}")

def print_warning(message):
    """Print warning message with yellow color and warning emoji"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_header(message):
    """Print header message with bold and underline"""
    print(f"{Colors.BOLD}{Colors.UNDERLINE}{message}{Colors.ENDC}")

def print_premium(message):
    """Print premium message with special formatting"""
    print(f"{Colors.HEADER}🌟 {message}{Colors.ENDC}")

def load_premium_users():
    """Load premium users from file"""
    try:
        if os.path.exists(PREMIUM_FILE):
            with open(PREMIUM_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return {"users": []}

def save_premium_users(data):
    """Save premium users to file"""
    with open(PREMIUM_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_active_connections():
    """Load active premium connections from file"""
    try:
        if os.path.exists(ACTIVE_CONNECTIONS_FILE):
            with open(ACTIVE_CONNECTIONS_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return {"connections": {}}

def save_active_connections(data):
    """Save active premium connections to file"""
    with open(ACTIVE_CONNECTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_premium(user_id):
    """Check if user is premium"""
    premium_data = load_premium_users()
    return str(user_id) in premium_data.get("users", [])

def get_uptime():
    """Calculate bot uptime"""
    try:
        with open(UPTIME_FILE, 'r') as f:
            start_time = json.load(f).get('start_time', time.time())
    except (FileNotFoundError, json.JSONDecodeError):
        start_time = time.time()
        with open(UPTIME_FILE, 'w') as f:
            json.dump({'start_time': start_time}, f)
    
    uptime = int(time.time() - start_time)
    days, remainder = divmod(uptime, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")
    
    return ' '.join(parts)

def get_prefix():
    """Get current prefix"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        with open(PREFIX_FILE, 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

async def restore_premium_connections():
    """Restore active premium connections on startup"""
    connections_data = load_active_connections()
    premium_users = load_premium_users().get("users", [])
    
    print_header("\n🔍 RESTORING PREMIUM CONNECTIONS")
    print_info(f"Premium Users: {len(premium_users)}")
    print_info(f"Saved Connections: {len(connections_data.get('connections', {}))}")
    
    restored_count = 0
    for user_id_str, session_str in connections_data.get("connections", {}).items():
        try:
            user_id = int(user_id_str)
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await client.connect()
            
            if await client.is_user_authorized():
                active_premium_sessions[user_id] = client
                print_success(f"Restored connection for user {user_id}")
                restored_count += 1
                
                # Load premium features for this client
                await load_premium_features(client, user_id)
        except Exception as e:
            print_error(f"Error restoring connection for {user_id_str}: {str(e)}")
    
    print_info(f"Successfully restored: {restored_count} connections")
    return restored_count

def get_connection(user_id):
    """Get connection for a specific user"""
    return active_premium_sessions.get(user_id)

def set_connection(user_id, session_str):
    """Save a new connection"""
    connections_data = load_active_connections()
    connections_data["connections"][str(user_id)] = session_str
    save_active_connections(connections_data)

def delete_connection(user_id):
    """Delete a connection"""
    connections_data = load_active_connections()
    user_id_str = str(user_id)
    
    if user_id_str in connections_data["connections"]:
        del connections_data["connections"][user_id_str]
        save_active_connections(connections_data)
    
    # Remove from active sessions if exists
    if user_id in active_premium_sessions:
        try:
            client = active_premium_sessions[user_id]
            if client.is_connected():
                client.disconnect()
            del active_premium_sessions[user_id]
        except:
            pass

async def load_premium_features(client, user_id):
    """Load premium features for a specific user connection"""
    premium_dir = 'plugins/premium'
    if not os.path.isdir(premium_dir):
        return

    loaded_features = []
    for fname in os.listdir(premium_dir):
        if fname.endswith('.py') and not fname.startswith('_'):
            module_name = fname[:-3]
            try:
                module = importlib.import_module(f'plugins.premium.{module_name}')
                if hasattr(module, 'setup'):
                    setup_func = module.setup
                    if inspect.iscoroutinefunction(setup_func):
                        await setup_func(bot, client, user_id)  # Pass user ID
                    else:
                        setup_func(bot, client, user_id)
                    loaded_features.append(module_name)
            except Exception as e:
                print_error(f"Error loading {module_name} for user {user_id}: {str(e)}")
    
    if loaded_features:
        print_premium(f"User {user_id}: {', '.join(loaded_features)}")

async def init_userbot():
    try:
        await user.connect()
        if await user.is_user_authorized():
            print_success("Userbot auto-connected!")
            return True
        print_warning("User session not authorized")
        return False
    except Exception as e:
        print_error(f"Userbot Error: {str(e)}")
        return False

async def load_plugins():
    plugins_dir = 'plugins'
    if not os.path.isdir(plugins_dir):
        return

    priority_plugins = ['help', 'martin', 'addprem', 'connect']
    
    print_header("\n⏬ LOADING PLUGINS")
    
    # Load priority plugins first
    priority_loaded = 0
    for plugin in priority_plugins:
        try:
            module = importlib.import_module(f'plugins.{plugin}')
            if hasattr(module, 'setup'):
                setup_func = module.setup
                # Special setup for addprem (only needs user client)
                if plugin == 'addprem':
                    if inspect.iscoroutinefunction(setup_func):
                        await setup_func(user)
                    else:
                        setup_func(user)
                # Special setup for connect (needs connect_bot)
                elif plugin == 'connect':
                    if connect_bot:
                        if inspect.iscoroutinefunction(setup_func):
                            await setup_func(connect_bot)
                        else:
                            setup_func(connect_bot)
                else:
                    if inspect.iscoroutinefunction(setup_func):
                        await setup_func(bot, user)
                    else:
                        setup_func(bot, user)
                print_success(f"Priority-loaded: {plugin}")
                priority_loaded += 1
        except Exception as e:
            print_error(f"Error loading {plugin}: {str(e)}")

    # Load other plugins
    other_loaded = 0
    for fname in os.listdir(plugins_dir):
        if fname.endswith('.py') and not fname.startswith('_'):
            module_name = fname[:-3]
            if module_name not in priority_plugins:
                try:
                    module = importlib.import_module(f'plugins.{module_name}')
                    if hasattr(module, 'setup'):
                        setup_func = module.setup
                        if inspect.iscoroutinefunction(setup_func):
                            await setup_func(bot, user)
                        else:
                            setup_func(bot, user)
                        print_info(f"Loaded: {module_name}")
                        other_loaded += 1
                except Exception as e:
                    print_error(f"Error: {module_name} - {str(e)}")
    
    print_info(f"Priority plugins: {priority_loaded}")
    print_info(f"Other plugins: {other_loaded}")
    print_info(f"Total plugins: {priority_loaded + other_loaded}")

async def main():
    # Save start time
    with open(UPTIME_FILE, 'w') as f:
        json.dump({'start_time': time.time()}, f)
    
    print_header("\n🚀 STARTING BOT SYSTEM")
    
    # Start main bot
    await bot.start(bot_token=BOT_TOKEN)
    print_success("Main Bot Ready!")
    
    # Start connect bot if available
    if BOT_TOKEN2:
        await connect_bot.start(bot_token=BOT_TOKEN2)
        print_success("Connect Bot Ready!")
    else:
        print_warning("Connect Bot Token not configured")
    
    # Initialize userbot
    userbot_status = await init_userbot()
    if not userbot_status:
        print_warning("Userbot initialization failed - some features may not work")
    
    # Restore active premium connections
    await restore_premium_connections()
    
    # Load plugins
    await load_plugins()
    
    # Display summary
    premium_users = load_premium_users().get("users", [])
    print_header("\n📊 BOT MARTIN")
    print_info(f"Premium Users: {len(premium_users)}")
    print_info(f"Active Premium Sessions: {len(active_premium_sessions)}")
    print_info(f"Uptime: {get_uptime()}")
    
    print_success("\n🤖 Bot Running...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print_error("\nBot stopped by user")
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
    finally:
        print_header("\n🔌 SHUTTING DOWN")
        
        # Disconnect all premium clients
        premium_count = len(active_premium_sessions)
        for user_id, client in active_premium_sessions.items():
            try:
                if client.is_connected():
                    client.disconnect()
            except:
                pass
        
        # Disconnect main clients
        if bot.is_connected():
            bot.disconnect()
            print_info("Main bot disconnected")
        if connect_bot and connect_bot.is_connected():
            connect_bot.disconnect()
            print_info("Connect bot disconnected")
        if user.is_connected():
            user.disconnect()
            print_info("Userbot disconnected")
        
        print_info(f"Disconnected {premium_count} premium sessions")
        print_success("Shutdown completed successfully")
        
        loop.close()