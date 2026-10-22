import os
import json
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BLACKLIST_FILE = os.path.join(DATA_DIR, "security_blacklist.json")
VISITORS_FILE = os.path.join(DATA_DIR, "visitors_stats.json")

# In-memory storage for high performance (sub-millisecond operations)
_active_sessions = {}  # device_id -> dict
_ip_rate_limits = {}   # ip -> [timestamps]
_blocked_ips = set()
_blocked_devices = set()
_blacklist_records = []
_today_visitors = set()
_current_date_str = ""

def load_blacklist():
    global _blocked_ips, _blocked_devices, _blacklist_records
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
        except Exception:
            pass

    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _blocked_ips = set(data.get("blocked_ips", []))
                _blocked_devices = set(data.get("blocked_devices", []))
                _blacklist_records = data.get("records", [])
        except Exception as e:
            print(f"[SECURITY] Error loading blacklist: {e}")
            _blocked_ips = set()
            _blocked_devices = set()
            _blacklist_records = []
    else:
        _blocked_ips = set()
        _blocked_devices = set()
        _blacklist_records = []

def save_blacklist():
    global _blocked_ips, _blocked_devices, _blacklist_records
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    try:
        data = {
            "blocked_ips": list(_blocked_ips),
            "blocked_devices": list(_blocked_devices),
            "records": _blacklist_records,
            "updated_at": datetime.now().isoformat()
        }
        with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SECURITY] Error saving blacklist: {e}")

# Initial load
load_blacklist()

def get_client_ip(req):
    """
    Extracts the true client IP from Cloudflare, Render proxy, or direct remote_addr.
    """
    cf_ip = req.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    
    forwarded = req.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = req.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
        
    return req.remote_addr or "127.0.0.1"

def parse_device_info(ua_string):
    """
    Analyzes user-agent string to identify OS, browser and device category.
    """
    if not ua_string:
        return "Dispositivo Desconocido"
    
    ua = ua_string.lower()
    
    # OS
    os_name = "Desconocido"
    if "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ios" in ua:
        os_name = "iPhone / iOS"
    elif "ipad" in ua:
        os_name = "iPad"
    elif "windows" in ua:
        os_name = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "Mac"
    elif "linux" in ua:
        os_name = "Linux"
        
    # Browser
    browser_name = "Web"
    if "edg" in ua:
        browser_name = "Edge"
    elif "chrome" in ua and "safari" in ua:
        browser_name = "Chrome"
    elif "safari" in ua and "chrome" not in ua:
        browser_name = "Safari"
    elif "firefox" in ua:
        browser_name = "Firefox"
    elif "opera" in ua or "opr" in ua:
        browser_name = "Opera"

    # Category
    cat = "📱 Móvil" if ("android" in ua or "iphone" in ua or "mobile" in ua) else ("💻 PC" if ("windows" in ua or "mac" in ua or "linux" in ua) else "📟 Tablet")
    
    return f"{cat} • {os_name} ({browser_name})"

def is_blocked(ip, device_id=None):
    """
    Checks if an IP or device ID is present in the active blacklist.
    Localhost and protected admin IPs are never blocked.
    """
    if ip and ip in ("127.0.0.1", "::1", "localhost"):
        return False
    if ip and ip in _blocked_ips:
        return True
    if device_id and device_id in _blocked_devices:
        return True
    return False

def block_target(target_type, value, reason="Bloqueo manual por administrador"):
    """
    Blocks an IP or a device ID. Protects loopback and localhost.
    """
    global _blocked_ips, _blocked_devices, _blacklist_records
    val_clean = str(value).strip()
    if not val_clean or val_clean in ("127.0.0.1", "::1", "localhost"):
        return False
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if target_type == "ip":
        _blocked_ips.add(val_clean)
    elif target_type == "device":
        _blocked_devices.add(val_clean)
    else:
        # Auto-detect if it looks like an IP
        if "." in val_clean or ":" in val_clean:
            _blocked_ips.add(val_clean)
            target_type = "ip"
        else:
            _blocked_devices.add(val_clean)
            target_type = "device"

    # Add record if not already recorded
    if not any(r.get("value") == val_clean for r in _blacklist_records):
        _blacklist_records.insert(0, {
            "type": target_type,
            "value": val_clean,
            "reason": reason,
            "created_at": now_str
        })
        
    # Evict from active sessions
    to_remove = []
    for d_id, s_info in _active_sessions.items():
        if d_id == val_clean or s_info.get("ip") == val_clean:
            to_remove.append(d_id)
    for d_id in to_remove:
        _active_sessions.pop(d_id, None)

    save_blacklist()
    return True

def unblock_target(target_type, value):
    """
    Removes an IP or device ID from the blacklist.
    """
    global _blocked_ips, _blocked_devices, _blacklist_records
    val_clean = str(value).strip()
    if not val_clean:
        return False

    if target_type == "ip":
        _blocked_ips.discard(val_clean)
    elif target_type == "device":
        _blocked_devices.discard(val_clean)
    else:
        _blocked_ips.discard(val_clean)
        _blocked_devices.discard(val_clean)

    _blacklist_records = [r for r in _blacklist_records if r.get("value") != val_clean]
    save_blacklist()
    return True

def register_heartbeat(device_id, ip, user_agent=""):
    """
    Registers a client heartbeat ping. Returns status and current online count.
    """
    global _today_visitors, _current_date_str
    now = time.time()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Check day turnover
    if _current_date_str != today_str:
        _current_date_str = today_str
        _today_visitors.clear()

    # Verify blacklist
    if is_blocked(ip, device_id):
        return {
            "blocked": True,
            "online": get_active_count()
        }

    # Register visitor
    v_key = f"{ip}_{device_id}" if device_id else ip
    _today_visitors.add(v_key)

    # Clean / sanitize device_id
    clean_id = (device_id or f"ip_{ip}").strip()
    dev_info = parse_device_info(user_agent)

    if clean_id not in _active_sessions:
        _active_sessions[clean_id] = {
            "device_id": clean_id,
            "ip": ip,
            "device_info": dev_info,
            "first_seen": now,
            "last_seen": now,
            "requests": 1
        }
    else:
        _active_sessions[clean_id]["last_seen"] = now
        _active_sessions[clean_id]["ip"] = ip
        _active_sessions[clean_id]["device_info"] = dev_info
        _active_sessions[clean_id]["requests"] = _active_sessions[clean_id].get("requests", 1) + 1

    return {
        "blocked": False,
        "online": get_active_count()
    }

def get_active_count(window_seconds=180):
    """
    Returns number of devices active in the last `window_seconds` (default 3 minutes).
    Ensures at least 1 is returned if server is running.
    """
    now = time.time()
    active = sum(1 for s in _active_sessions.values() if (now - s.get("last_seen", 0)) <= window_seconds)
    return max(1, active)

def get_active_sessions_list(window_seconds=300):
    """
    Returns list of active and recent sessions for the admin dashboard.
    """
    now = time.time()
    result = []
    
    # Prune very old sessions (> 30 mins)
    prune_keys = [k for k, s in _active_sessions.items() if (now - s.get("last_seen", 0)) > 1800]
    for k in prune_keys:
        _active_sessions.pop(k, None)

    for d_id, s in _active_sessions.items():
        diff = int(now - s.get("last_seen", 0))
        is_online = (diff <= 180)
        
        # Time display
        if diff < 15:
            seen_text = "Hace instantes"
        elif diff < 60:
            seen_text = f"Hace {diff}s"
        else:
            seen_text = f"Hace {diff // 60} min"
            
        first_diff = int(now - s.get("first_seen", now))
        connected_text = f"Hace {first_diff // 60} min" if first_diff >= 60 else "Reciente"
        
        is_dev_blocked = is_blocked(s.get("ip"), d_id)
        
        result.append({
            "device_id": d_id,
            "ip": s.get("ip"),
            "device_info": s.get("device_info", "Dispositivo"),
            "is_online": is_online,
            "is_blocked": is_dev_blocked,
            "last_seen_text": seen_text,
            "connected_duration": connected_text,
            "requests_count": s.get("requests", 1)
        })

    # Sort: online first, then by last_seen
    result.sort(key=lambda x: (1 if x["is_online"] else 0, x["requests_count"]), reverse=True)
    return result

def get_blacklist_records():
    return _blacklist_records

def get_stats_summary():
    """
    Quick KPI summary for admin dashboard.
    """
    return {
        "online_now": get_active_count(),
        "today_unique": max(1, len(_today_visitors)),
        "blocked_total": len(_blocked_ips) + len(_blocked_devices),
        "active_devices_tracked": len(_active_sessions)
    }

def check_rate_limit(ip, max_per_minute=90):
    """
    In-memory rate limiter to protect against bot scraping / flooding.
    Returns True if permitted, False if limit exceeded.
    """
    now = time.time()
    window = now - 60
    
    # Ignore localhost / loopback
    if ip in ("127.0.0.1", "::1", "localhost"):
        return True
        
    timestamps = _ip_rate_limits.get(ip, [])
    # Prune outside window
    timestamps = [t for t in timestamps if t > window]
    
    if len(timestamps) >= max_per_minute:
        _ip_rate_limits[ip] = timestamps
        return False
        
    timestamps.append(now)
    _ip_rate_limits[ip] = timestamps
    return True

