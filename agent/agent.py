#!/usr/bin/env python3
"""
Main autonomous agent daemon for Termux.
ReAct-style loop with memory, structured tool calling, goal management,
self-reflection, and persistent background operation.
"""

import os
import sys
import time
import json
import logging
import argparse
import datetime
import signal
from pathlib import Path
from typing import Optional, Dict, Any

import ollama
import yaml

# Local imports
from .prompts import get_full_system_prompt
from .memory import Memory
from . import tools   # Will import all tools

# ==================== Configuration ====================
BASE_DIR = Path.home() / "termux-agentic-ai"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "agent.log"
CONFIG_FILE = BASE_DIR / "config.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TermuxAgent")

# Default config
DEFAULT_CONFIG = {
    "model": "gemma:2b",           # Change to phi3:mini, llama3.2:3b etc.
    "ollama_host": "http://localhost:11434",
    "check_interval_minutes": 30,
    "daily_report_time": "20:00",
    "max_cycles_before_reflect": 48,
    "monitor_only_crypto": True,   # Safety: no real trading by default
    "wake_lock": True,
    "tools_enabled": [
        "shell_execute", "termux_notify", "get_location", "get_battery",
        "crypto_price", "web_search", "file_read", "file_write",
        "list_dir", "reflect", "update_goal"
    ]
}

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **yaml.safe_load(f)}
    else:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG.copy()

CONFIG = load_config()

# ==================== Tool Registry ====================
TOOL_REGISTRY = {
    "shell_execute": tools.shell_execute,
    "termux_notify": tools.termux_notify,
    "get_location": tools.get_location,
    "get_battery": tools.get_battery,
    "crypto_price": tools.crypto_price,
    "web_search": tools.web_search,
    "file_read": tools.file_read,
    "file_write": tools.file_write,
    "list_dir": tools.list_dir,
    "reflect": tools.reflect,
    "update_goal": tools.update_goal,
    # Add more as you implement them in tools/
}

def get_current_context(memory: Memory) -> str:
    """Build context string injected into every prompt."""
    battery = tools.get_battery() if "get_battery" in CONFIG["tools_enabled"] else {}
    now = datetime.datetime.now()
    
    active_goals = memory.get_active_goals()
    goal_summary = "\n".join([f"- [{g['id']}] P{g['priority']}: {g['description']}" for g in active_goals[:5]]) or "No active goals."
    
    recent_reflections = memory.get_recent_reflections(2)
    reflection_summary = recent_reflections[0]['summary'] if recent_reflections else "No recent reflections."
    
    context = f"""Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}
Battery: {battery.get('percentage', 'N/A')}% (charging: {battery.get('charging', False)})
Active Goals ({len(active_goals)}):
{goal_summary}

Last reflection summary: {reflection_summary}

Crypto monitor only mode: {CONFIG['monitor_only_crypto']}
"""
    return context

def call_ollama(messages: list, model: str = None) -> str:
    """Call local Ollama with timeout and error handling."""
    model = model or CONFIG["model"]
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"temperature": 0.3, "num_predict": 800}  # Keep responses focused
        )
        return response['message']['content']
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return json.dumps({
            "thought": f"Ollama error: {str(e)}. Falling back to safe idle.",
            "action": None,
            "args": {},
            "goal_updates": [],
            "next_check_in_minutes": 60
        })

def parse_agent_response(raw_response: str) -> Dict[str, Any]:
    """Extract and validate JSON from model output. Very important for small models."""
    raw_response = raw_response.strip()
    
    # Try to find JSON block
    start = raw_response.find('{')
    end = raw_response.rfind('}') + 1
    
    if start == -1 or end == 0:
        logger.warning("No JSON found in response. Using fallback.")
        return {
            "thought": "Model did not return valid JSON. Entering safe idle mode.",
            "action": None,
            "args": {},
            "goal_updates": [],
            "next_check_in_minutes": 45
        }
    
    json_str = raw_response[start:end]
    
    try:
        parsed = json.loads(json_str)
        # Basic validation
        if "thought" not in parsed:
            parsed["thought"] = "No thought provided."
        if "action" not in parsed:
            parsed["action"] = None
        if "args" not in parsed:
            parsed["args"] = {}
        if "goal_updates" not in parsed:
            parsed["goal_updates"] = []
        if "next_check_in_minutes" not in parsed:
            parsed["next_check_in_minutes"] = CONFIG["check_interval_minutes"]
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {json_str[:300]}")
        return {
            "thought": "Failed to parse model JSON output. Safe idle.",
            "action": None,
            "args": {},
            "goal_updates": [],
            "next_check_in_minutes": 60
        }

def execute_tool(tool_name: str, args: dict, memory: Memory) -> tuple[str, bool]:
    """Execute a registered tool safely."""
    if tool_name not in TOOL_REGISTRY:
        return f"Error: Unknown tool '{tool_name}'", False
    
    tool_func = TOOL_REGISTRY[tool_name]
    
    try:
        # Some tools need memory
        if tool_name in ["reflect", "update_goal"]:
            result = tool_func(args, memory=memory, config=CONFIG)
        else:
            result = tool_func(args, config=CONFIG)
        
        success = not str(result).startswith("Error")
        return str(result)[:1500], success
    except Exception as e:
        logger.exception(f"Tool {tool_name} failed")
        return f"Tool execution error: {str(e)}", False

def send_daily_report(memory: Memory):
    """Generate and send daily summary notification."""
    try:
        goals = memory.get_active_goals()
        recent_actions = memory.get_recent_actions(10)
        
        summary = f"Daily Agent Report ({datetime.date.today()})\n\n"
        summary += f"Active Goals: {len(goals)}\n"
        for g in goals[:3]:
            summary += f"• {g['description'][:60]}...\n"
        
        summary += f"\nRecent activity logged. Battery OK."
        
        tools.termux_notify({
            "title": "TermuxAgent Daily Report",
            "content": summary,
            "priority": "default"
        })
        logger.info("Daily report sent.")
    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")

def main_loop(memory: Memory):
    """The core autonomous loop."""
    cycle = memory.get_value("cycle_count", 0)
    last_report_date = memory.get_value("last_report_date", "")
    
    logger.info("=== Starting TermuxAgent main loop ===")
    
    while True:
        cycle += 1
        memory.set_value("cycle_count", cycle)
        logger.info(f"--- Cycle {cycle} ---")
        
        try:
            # 1. Build context
            context = get_current_context(memory)
            
            # 2. Get full prompt
            system_prompt = get_full_system_prompt(context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Current cycle: {cycle}. Review goals and decide next actions."}
            ]
            
            # 3. Call model
            raw_response = call_ollama(messages)
            parsed = parse_agent_response(raw_response)
            
            logger.info(f"Thought: {parsed['thought'][:200]}...")
            
            # 4. Handle goal updates
            for update in parsed.get("goal_updates", []):
                if update.get("action") == "create":
                    gid = memory.create_goal(
                        update.get("description", "Unnamed goal"),
                        priority=update.get("priority", 3)
                    )
                    logger.info(f"Created goal #{gid}")
                elif update.get("action") in ["update", "complete"] and "goal_id" in update:
                    memory.update_goal(
                        update["goal_id"],
                        status=update.get("status", "active"),
                        description=update.get("description")
                    )
            
            # 5. Execute tool if requested
            action = parsed.get("action")
            result_str = ""
            success = True
            
            if action and action != "null":
                result_str, success = execute_tool(action, parsed.get("args", {}), memory)
                logger.info(f"Tool '{action}' result: {result_str[:150]}...")
            
            # 6. Log the action
            memory.log_action(
                thought=parsed["thought"],
                action=action or "none",
                args=parsed.get("args", {}),
                result=result_str,
                success=success,
                cycle=cycle
            )
            
            # 7. Daily report check
            today = datetime.date.today().isoformat()
            current_time = datetime.datetime.now().strftime("%H:%M")
            if current_time >= CONFIG["daily_report_time"] and last_report_date != today:
                send_daily_report(memory)
                memory.set_value("last_report_date", today)
            
            # 8. Periodic self-reflection
            if cycle % CONFIG["max_cycles_before_reflect"] == 0:
                logger.info("Triggering periodic reflection...")
                # Could call reflect tool here or inline simple analysis
            
            # 9. Sleep
            sleep_minutes = int(parsed.get("next_check_in_minutes", CONFIG["check_interval_minutes"]))
            sleep_minutes = max(5, min(sleep_minutes, 240))  # Safety bounds
            logger.info(f"Sleeping for {sleep_minutes} minutes...")
            time.sleep(sleep_minutes * 60)
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user.")
            break
        except Exception as e:
            logger.exception(f"Error in main loop cycle {cycle}: {e}")
            # Resilient: sleep and continue
            time.sleep(300)  # 5 minutes on error

def daemonize():
    """Basic daemonization (already running in background usually via service)."""
    # In Termux we usually rely on termux-services or nohup
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    
    if args.daemon:
        daemonize()
    
    memory = Memory()
    
    # Seed initial goals if none exist
    if not memory.get_active_goals():
        memory.create_goal("Perform daily crypto price monitoring and notify on significant moves", priority=2)
        memory.create_goal("Run daily system health check (battery, storage, connectivity)", priority=3)
        memory.create_goal("Generate evening summary report via notification", priority=4)
        logger.info("Seeded initial goals.")
    
    # Handle signals gracefully
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal. Exiting cleanly...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main_loop(memory)
    finally:
        memory.close()
        logger.info("Agent shutdown complete.")