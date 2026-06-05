import json
import os
from datetime import datetime

SESSIONS_DIR = "sessions"

def save_session(session_name: str, messages: list, completed_tools: list, customer_data: dict = None) -> str:
    """
    Save a conversation session to disk.
    Returns the path of the saved session file.
    """
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    session = {
        "session_name": session_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_data": customer_data or {},
        "completed_tools": completed_tools,
        "messages": _serialize_messages(messages)
    }

    path = os.path.join(SESSIONS_DIR, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(session, f, indent=2)

    # print(f"\n[Session] Saved: {path}")
    return path

def load_session(session_name: str) -> dict:
    """
    Load a previously saved session from disk.
    Returns session dict with messages, completed_tools, and customer_data.
    """
    path = os.path.join(SESSIONS_DIR, f"{session_name}.json")

    if not os.path.exists(path):
        # print(f"[Session] No session found: {session_name}")
        return None

    with open(path, "r") as f:
        session = json.load(f)

    # print(f"\n[Session] Loaded: {session_name}")
    # print(f"[Session] Customer: {session['customer_data'].get('name', 'Unknown')}")
    # print(f"[Session] Created: {session['created_at']}")
    # print(f"[Session] Messages: {len(session['messages'])}")
    return session

def fork_session(source_session_name: str, fork_name: str) -> dict:
    """
    Create an independent branch from an existing session.
    The fork starts with the same history but is completely independent.
    """
    source = load_session(source_session_name)
    if not source:
        # print(f"[Session] Cannot fork — source session not found: {source_session_name}")
        return None

    forked = {
        "session_name": fork_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "forked_from": source_session_name,
        "customer_data": source["customer_data"],
        "completed_tools": source["completed_tools"].copy(),
        "messages": source["messages"].copy()
    }

    path = os.path.join(SESSIONS_DIR, f"{fork_name}.json")
    with open(path, "w") as f:
        json.dump(forked, f, indent=2)

    # print(f"\n[Session] Forked '{source_session_name}' → '{fork_name}'")
    return forked

def list_sessions() -> list:
    """
    List all saved sessions.
    """
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    files = [f.replace(".json", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
    return files

def _serialize_messages(messages: list) -> list:
    """
    Convert message objects to JSON-serializable format.
    Claude API returns content as objects — we need plain dicts.
    """
    serialized = []
    for message in messages:
        if isinstance(message, dict):
            role = message.get("role")
            content = message.get("content")

            if isinstance(content, str):
                serialized.append({"role": role, "content": content})
            elif isinstance(content, list):
                serialized_content = []
                for block in content:
                    if isinstance(block, dict):
                        serialized_content.append(block)
                    else:
                        serialized_content.append(_block_to_dict(block))
                serialized.append({"role": role, "content": serialized_content})
    return serialized

def _block_to_dict(block) -> dict:
    """
    Convert a Claude API content block object to a plain dict.
    """
    if hasattr(block, "type"):
        if block.type == "text":
            return {"type": "text", "text": block.text}
        elif block.type == "tool_use":
            return {
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input
            }
        elif block.type == "tool_result":
            return {
                "type": "tool_result",
                "tool_use_id": block.tool_use_id,
                "content": block.content
            }
    return {}