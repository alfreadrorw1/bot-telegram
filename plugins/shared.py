# plugins/shared.py
import json
import os

PREMIUM_FILE = 'premium/premium.json'
ACTIVE_CONNECTIONS_FILE = 'premium/active_connections.json'
UPTIME_FILE = 'premium/uptime.json'
PREFIX_FILE = 'premium/prefix.json'

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