import json
from tools.mcp_tools import get_customer, lookup_order, process_refund, escalate_to_human
from agent.hooks import post_tool_use_hook, pre_tool_call_hook

def execute_tool(tool_name: str, tool_input: dict, completed_tools: list) -> dict:
    # print(f"\n[Tool Call] {tool_name} → {tool_input}")

    # Run PreToolCall hook first — check gates and policies
    block = pre_tool_call_hook(tool_name, tool_input, completed_tools)
    if block:
        # print(f"[Tool Blocked] {block}")
        return block

    # Tool is allowed — execute it
    if tool_name == "get_customer":
        result = get_customer(**tool_input)
    elif tool_name == "lookup_order":
        result = lookup_order(**tool_input)
    elif tool_name == "process_refund":
        result = process_refund(**tool_input)
    elif tool_name == "escalate_to_human":
        result = escalate_to_human(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    # Run PostToolUse hook — normalize the result
    normalized_result = post_tool_use_hook(tool_name, result)

    # Record this tool as completed
    completed_tools.append(tool_name)

    # print(f"[Tool Result] {normalized_result}")
    return normalized_result