"""
Base utilities for tools.
"""

import subprocess
import json
from pathlib import Path
from typing import Any, Dict

def run_command(cmd: list[str], timeout: int = 30) -> str:
    """Safe-ish command runner with timeout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.home()
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error (code {result.returncode}): {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def safe_json_loads(text: str, default: dict = None) -> dict:
    try:
        return json.loads(text)
    except:
        return default or {}