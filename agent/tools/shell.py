"""
Shell execution tool with safety restrictions.
"""

from .base import run_command

# Very restrictive allowlist for safety on phone
SAFE_COMMANDS = {
    "ls", "pwd", "df", "free", "uptime", "whoami", "date",
    "cat", "head", "tail", "wc", "grep", "find", "du",
    "ping", "curl", "wget", "git", "python", "pip"
}

def shell_execute(args: dict, config: dict = None) -> str:
    command = args.get("command", "")
    if not command:
        return "Error: No command provided"
    
    # Basic safety: only allow whitelisted base commands
    base_cmd = command.split()[0]
    if base_cmd not in SAFE_COMMANDS:
        return f"Error: Command '{base_cmd}' not in safe allowlist. Use with extreme caution or extend allowlist."
    
    # Additional dangerous pattern check
    dangerous = ["rm -rf", "mkfs", "dd if=", "shutdown", "reboot", ":(){ ", "eval"]
    for d in dangerous:
        if d in command:
            return f"Error: Potentially dangerous command blocked: {command}"
    
    return run_command(command.split(), timeout=args.get("timeout", 25))