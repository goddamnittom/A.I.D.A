"""
Termux-API tools: notifications, location, battery, etc.
"""

import subprocess
import json
from .base import run_command

def termux_notify(args: dict, config: dict = None) -> str:
    """Send Android notification."""
    title = args.get("title", "TermuxAgent")
    content = args.get("content", "Notification from agent")
    priority = args.get("priority", "default")  # default, high, low, max
    
    cmd = [
        "termux-notification",
        "--title", title,
        "--content", content,
        "--priority", priority
    ]
    
    if args.get("sound"):
        cmd.append("--sound")
    
    result = run_command(cmd)
    return "Notification sent successfully" if "Error" not in result else result

def get_location(args: dict = None, config: dict = None) -> str:
    """Get current location (requires permission)."""
    result = run_command(["termux-location", "-p", "gps", "-r", "once"])
    if result.startswith("Error"):
        return result
    try:
        loc = json.loads(result)
        return f"Latitude: {loc.get('latitude')}, Longitude: {loc.get('longitude')}, Accuracy: {loc.get('accuracy')}m"
    except:
        return f"Raw location data: {result}"

def get_battery(args: dict = None, config: dict = None) -> dict:
    """Get battery status."""
    result = run_command(["termux-battery-status"])
    if result.startswith("Error"):
        return {"error": result}
    try:
        return json.loads(result)
    except:
        return {"raw": result}