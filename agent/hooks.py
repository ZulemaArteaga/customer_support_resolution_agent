import json
from datetime import datetime

def format_date(date_str: str) -> str:
    """Convert database date string to human readable format"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%B %d, %Y")
    except:
        return date_str

def format_amount(amount: float) -> str:
    """Format numeric amount to currency string"""
    try:
        return f"${float(amount):.2f} USD"
    except:
        return str(amount)

def format_status(status: str) -> str:
    """Normalize status codes to human readable with indicators"""
    status_map = {
        "active":    "Active ✓",
        "inactive":  "Inactive ✗",
        "delivered": "Delivered ✓",
        "pending":   "Pending ⏳",
        "cancelled": "Cancelled ✗",
        "approved":  "Approved ✓",
        "rejected":  "Rejected ✗",
        "open":      "Open ⚠️",
        "resolved":  "Resolved ✓",
        "escalated": "Escalated ⚠️",
    }
    return status_map.get(status.lower(), status.capitalize())

def normalize_customer(data: dict) -> dict:
    if "error" in data:
        return data
    return {
        **data,
        "status": format_status(data.get("status", ""))
    }

def normalize_order(data: dict) -> dict:
    if "error" in data:
        return data
    return {
        **data,
        "amount": format_amount(data.get("amount", 0)),
        "status": format_status(data.get("status", "")),
        "created_at": format_date(data.get("created_at", ""))
    }

def normalize_refund(data: dict) -> dict:
    if "error" in data:
        return data
    return {
        **data,
        "amount": format_amount(data.get("amount", 0)),
        "status": format_status(data.get("status", "")),
        "created_at": format_date(data.get("created_at", ""))
    }

def normalize_escalation(data: dict) -> dict:
    if "error" in data:
        return data
    return {
        **data,
        "status": format_status(data.get("status", "")),
        "created_at": format_date(data.get("created_at", ""))
    }

def post_tool_use_hook(tool_name: str, raw_result: dict) -> dict:
    """PostToolUse hook — normalizes tool results before Claude sees them"""
    normalizers = {
        "get_customer":      normalize_customer,
        "lookup_order":      normalize_order,
        "process_refund":    normalize_refund,
        "escalate_to_human": normalize_escalation,
    }
    normalizer = normalizers.get(tool_name)
    if normalizer:
        normalized = normalizer(raw_result)
        if normalized != raw_result:
            # print(f"[Hook] Normalized {tool_name} result")
            return normalized
    return raw_result

def pre_tool_call_hook(tool_name: str, tool_input: dict, completed_tools: list) -> dict:
    """PreToolCall hook — enforces gates and policies before tools run"""

    # Gate 1: lookup_order requires get_customer first
    if tool_name == "lookup_order":
        if "get_customer" not in completed_tools:
            # print(f"[Gate Blocked] lookup_order requires get_customer first")
            return {
                "error": "Cannot lookup order — customer must be verified first",
                "action_required": "Call get_customer before lookup_order"
            }

    # Gate 2: process_refund requires both get_customer and lookup_order
    if tool_name == "process_refund":
        if "get_customer" not in completed_tools:
            # print(f"[Gate Blocked] process_refund requires get_customer first")
            return {
                "error": "Cannot process refund — customer must be verified first",
                "action_required": "Call get_customer before process_refund"
            }
        if "lookup_order" not in completed_tools:
            # print(f"[Gate Blocked] process_refund requires lookup_order first")
            return {
                "error": "Cannot process refund — order must be looked up first",
                "action_required": "Call lookup_order before process_refund"
            }
        # Policy: block refunds above $500
        amount = tool_input.get("amount", 0)
        if amount > 500:
            # print(f"[Policy Blocked] Refund of ${amount} exceeds $500 limit")
            return {
                "error": f"Refund of ${amount} exceeds the $500 automated refund limit",
                "action_required": "Escalate to human agent for refunds above $500"
            }

    # Gate 3: escalate_to_human requires get_customer first
    if tool_name == "escalate_to_human":
        if "get_customer" not in completed_tools:
            # print(f"[Gate Blocked] escalate_to_human requires get_customer first")
            return {
                "error": "Cannot escalate — customer must be verified first",
                "action_required": "Call get_customer before escalating"
            }

    return None