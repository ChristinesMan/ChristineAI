"""
Handles the http server used for management, external signals, etc
"""
import os
import subprocess
import threading
import json
from datetime import datetime

# pylint: disable=missing-function-docstring,no-member
from bottle import TEMPLATE_PATH, route, run, template, request, debug, response, abort, install

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.parietal_lobe import parietal_lobe

debug(True)

TEMPLATE_PATH.append("./httpserver/")

# Store chat messages in memory
chat_messages = []

# Simple security token
SECURITY_TOKEN = CONFIG.http_security_token

def auth_middleware(callback):
    """Simple token-based authentication middleware"""
    def wrapper(*args, **kwargs):
        # Get token from URL parameter or form data
        token = request.query.get('token') or request.forms.get('token')
        
        # For API calls, also check for token in POST body (JSON)
        if not token and request.content_type == 'application/json':
            try:
                json_data = request.json
                if json_data is not None:
                    token = json_data.get('token')
            except:
                pass
        
        # Check if token matches
        if token == SECURITY_TOKEN:
            return callback(*args, **kwargs)
        else:
            log.main.warning("Unauthorized access attempt from %s to %s", 
                           request.environ.get('REMOTE_ADDR'), request.path)
            abort(403, "Access denied")
    
    return wrapper

# Install the authentication middleware
install(auth_middleware)

@route("/")
def index():
    # Get the token from URL parameter to pass to template
    token = request.query.get('token', '')
    return template("index", token=token)

@route("/api/status")
def api_status():
    """Return current status as JSON"""
    response.content_type = 'application/json'
    status_data = STATE.to_json()
    # Add some additional computed values
    status_data["current_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_data["uptime"] = get_uptime()
    status_data["memory_usage"] = get_memory_usage()
    status_data["disk_usage"] = get_disk_usage()
    return json.dumps(status_data)

@route("/api/control/<action>", method="POST")
def api_control(action):
    """Handle control actions"""
    response.content_type = 'application/json'
    
    try:
        if action == "restart":
            log.main.info("Restart requested via web interface")
            STATE.please_shut_down = True
            # Schedule restart after a brief delay
            threading.Timer(2.0, lambda: os.system("sudo systemctl restart christine")).start()
            return json.dumps({"status": "success", "message": "Christine is restarting..."})
            
        elif action == "stop":
            log.main.info("Stop requested via web interface")
            STATE.please_shut_down = True
            return json.dumps({"status": "success", "message": "Christine is stopping..."})
            
        elif action == "reboot":
            log.main.info("Reboot requested via web interface")
            threading.Timer(2.0, lambda: os.system("sudo reboot")).start()
            return json.dumps({"status": "success", "message": "System is rebooting..."})
            
        elif action == "poweroff":
            log.main.info("Poweroff requested via web interface")
            threading.Timer(2.0, lambda: os.system("sudo poweroff")).start()
            return json.dumps({"status": "success", "message": "System is powering off..."})
            
        elif action == "toggle_wernicke":
            STATE.perceptions_blocked = not STATE.perceptions_blocked
            status = "disabled" if STATE.perceptions_blocked else "enabled"
            log.main.info("Wernicke %s via web interface", status)
            return json.dumps({"status": "success", "message": f"Wernicke {status}"})
            
        elif action == "test_sound":
            log.main.info("Test sound requested via web interface")
            # Play a simple beep sound instead of the ALSA "Front Left" announcement
            threading.Thread(target=lambda: os.system("aplay ./sounds/beep.wav"), daemon=True).start()
            return json.dumps({"status": "success", "message": "Test sound played"})
            
        elif action == "toggle_shush":
            STATE.shush_please_honey = not STATE.shush_please_honey
            status = "enabled" if STATE.shush_please_honey else "disabled"
            log.main.info("Shush %s via web interface", status)
            return json.dumps({"status": "success", "message": f"Shush {status}"})
            
        elif action == "toggle_silent":
            STATE.silent_mode = not STATE.silent_mode
            status = "enabled" if STATE.silent_mode else "disabled"
            log.main.info("Silent mode %s via web interface", status)
            return json.dumps({"status": "success", "message": f"Silent mode {status}"})
            
        else:
            return json.dumps({"status": "error", "message": "Unknown action"})
            
    except Exception as e:
        log.main.error("Error in control action %s: %s", action, str(e))
        return json.dumps({"status": "error", "message": str(e)})

@route("/api/chat", method="GET")
def api_chat_get():
    """Get chat messages"""
    response.content_type = 'application/json'
    return json.dumps(chat_messages)

@route("/api/chat", method="POST")
def api_chat_post():
    """Send a chat message"""
    response.content_type = 'application/json'
    
    try:
        data = request.json
        if data is None or not isinstance(data, dict):
            return json.dumps({"status": "error", "message": "No message provided"})
        
        # Now we know data is a dict, so we can safely check for key existence
        message = data.get('message')
        sender = data.get('sender')
        
        if not message:
            return json.dumps({"status": "error", "message": "No message provided"})
        
        if not sender:
            return json.dumps({"status": "error", "message": "No sender provided"})
            
        user_message = message.strip()
        user_sender = sender.strip()
        
        if not user_message:
            return json.dumps({"status": "error", "message": "Empty message"})
            
        if not user_sender:
            return json.dumps({"status": "error", "message": "Empty sender name"})
            
        # Add user message to chat
        timestamp = datetime.now().strftime("%H:%M:%S")
        chat_messages.append({
            "type": "user",
            "message": user_message,
            "timestamp": timestamp,
            "sender": user_sender
        })
        
        # Keep only last 50 messages to prevent memory issues
        if len(chat_messages) > 50:
            chat_messages.pop(0)
            
        # Send to parietal lobe for processing
        log.main.info("Chat message received from %s: %s", user_sender, user_message)
        parietal_lobe.web_chat_message(user_message, user_sender)
        
        return json.dumps({"status": "success", "message": "Message sent"})
        
    except Exception as e:
        log.main.error("Error in chat: %s", str(e))
        return json.dumps({"status": "error", "message": str(e)})

@route("/api/logs")
def api_logs():
    """Get recent log entries"""
    response.content_type = 'application/json'
    
    try:
        # Read last 100 lines from the most recent log file
        log_files = []
        log_dir = "/root/ChristineAI/logs"
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith('.log'):
                    log_files.append(os.path.join(log_dir, file))
        
        if log_files:
            # Get the most recent log file
            latest_log = max(log_files, key=os.path.getmtime)
            result = subprocess.run(['tail', '-100', latest_log], capture_output=True, text=True, check=False)
            log_lines = result.stdout.split('\n') if result.returncode == 0 else []
        else:
            log_lines = ["No log files found"]
            
        return json.dumps({"logs": log_lines})
        
    except Exception as e:
        return json.dumps({"logs": [f"Error reading logs: {str(e)}"]})

def get_uptime():
    """Get system uptime"""
    try:
        with open('/proc/uptime', 'r', encoding='utf-8') as f:
            uptime_seconds = float(f.readline().split()[0])
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    except (OSError, ValueError, IndexError):
        return "Unknown"

def get_memory_usage():
    """Get memory usage percentage"""
    try:
        result = subprocess.run(['free'], capture_output=True, text=True, check=False)
        lines = result.stdout.split('\n')
        if len(lines) > 1:
            mem_line = lines[1].split()
            total = int(mem_line[1])
            used = int(mem_line[2])
            percentage = int((used / total) * 100)
            return f"{percentage}%"
    except (subprocess.SubprocessError, ValueError, IndexError):
        return "Unknown"

def get_disk_usage():
    """Get disk usage percentage"""
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, check=False)
        lines = result.stdout.split('\n')
        if len(lines) > 1:
            usage = lines[1].split()[4]
            return usage
    except (subprocess.SubprocessError, IndexError):
        return "Unknown"

# Add Christine's responses to chat
def add_christine_response(message):
    """Add Christine's response to chat messages"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    chat_messages.append({
        "type": "christine",
        "message": message,
        "timestamp": timestamp,
        "sender": "Christine"
    })
    
    # Keep only last 50 messages
    if len(chat_messages) > 50:
        chat_messages.pop(0)

def add_user_message(message):
    """Add user's spoken message to chat messages"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    chat_messages.append({
        "type": "user",
        "message": message,
        "timestamp": timestamp,
        "sender": parietal_lobe.user_name  # Default to user for spoken messages
    })
    
    # Keep only last 50 messages
    if len(chat_messages) > 50:
        chat_messages.pop(0)

# run the server in a thread
# don't start the thread; that is done from __main__
httpserver = threading.Thread(
    target=run, daemon=True, name="httpserver", kwargs=dict(host="0.0.0.0", port=80)
)
