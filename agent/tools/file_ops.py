"""
File system tools with basic safety.
"""

from pathlib import Path
from .base import run_command

BASE_DIR = Path.home() / "termux-agentic-ai"

def list_dir(args: dict, config: dict = None) -> str:
    path = args.get("path", str(BASE_DIR))
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return f"Error: Path does not exist: {path}"
        items = [f"{item.name}/" if item.is_dir() else item.name for item in p.iterdir()]
        return "\n".join(sorted(items)[:30])  # Limit output
    except Exception as e:
        return f"Error listing dir: {str(e)}"

def file_read(args: dict, config: dict = None) -> str:
    path = args.get("path", "")
    max_lines = args.get("max_lines", 50)
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return "Error: File not found"
        with open(p, "r", errors="ignore") as f:
            lines = f.readlines()[:max_lines]
        return "".join(lines)
    except Exception as e:
        return f"Error reading file: {str(e)}"

def file_write(args: dict, config: dict = None) -> str:
    path = args.get("path", "")
    content = args.get("content", "")
    mode = args.get("mode", "w")  # w or a
    
    # Safety: only allow writes inside the agent directory by default
    safe_base = BASE_DIR
    try:
        p = Path(path).expanduser().resolve()
        if not str(p).startswith(str(safe_base)):
            return "Error: Writing outside agent directory is restricted for safety."
        
        with open(p, mode, encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"