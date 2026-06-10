"""
Goal management tool (called by agent via JSON).
"""

def update_goal(args: dict, memory=None, config: dict = None) -> str:
    """Create or update goals. Usually called via the goal_updates array in main loop,
    but can also be used as explicit tool."""
    if not memory:
        return "Error: Memory system unavailable"
    
    action = args.get("action", "create")
    
    if action == "create":
        gid = memory.create_goal(
            args.get("description", "New goal from tool"),
            priority=args.get("priority", 3)
        )
        return f"Created goal #{gid}"
    
    elif action in ["update", "complete"] and "goal_id" in args:
        memory.update_goal(
            args["goal_id"],
            status=args.get("status", "active"),
            description=args.get("description")
        )
        return f"Updated goal #{args['goal_id']}"
    
    return "Invalid goal update action"