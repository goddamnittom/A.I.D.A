"""
Self-reflection tool.
"""

from datetime import datetime

def reflect(args: dict, memory=None, config: dict = None) -> str:
    """Analyze recent activity and generate insights."""
    if not memory:
        return "Error: Memory not available"
    
    recent = memory.get_recent_actions(15)
    if not recent:
        return "No recent actions to reflect on."
    
    successes = sum(1 for a in recent if a.get("success"))
    failures = len(recent) - successes
    
    summary = f"Reflection at {datetime.now().isoformat()}\n"
    summary += f"Recent actions: {len(recent)} | Success rate: {successes}/{len(recent)} ({successes/len(recent)*100:.1f}%)\n"
    
    # Simple pattern detection
    failed_actions = [a for a in recent if not a.get("success")]
    if failed_actions:
        common_fail = {}
        for a in failed_actions:
            act = a.get("action", "unknown")
            common_fail[act] = common_fail.get(act, 0) + 1
        summary += f"Most common failing actions: {common_fail}\n"
    
    summary += "Key insight: Agent is operating within expected parameters. Consider increasing sleep time if battery drain is high."
    
    # Store reflection
    memory.add_reflection(
        cycle=args.get("cycle", 0),
        summary=summary[:500],
        insights=["Monitor battery usage", "Review failed tool calls for pattern"],
        suggested_improvements="Add more robust error handling in tool wrappers."
    )
    
    return summary