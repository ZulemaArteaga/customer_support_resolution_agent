import json
from agent.client import get_client, DEFAULT_MODEL
from agent.tool_definitions import TOOLS
from agent.tool_executor import execute_tool

REFUND_AGENT_PROMPT = """You are a refund specialist agent.

You have been given verified customer and order information by the coordinator.
Your ONLY job is to process the refund using the information provided.

Rules:
1. The customer has already been verified — do not call get_customer again
2. The order has already been looked up — do not call lookup_order again
3. Go straight to process_refund with the provided order_id and amount
4. If the refund amount exceeds $500 use escalate_to_human instead
5. Report the outcome clearly
"""

def run_refund_agent(customer_data: dict, order_data: dict, reason: str) -> dict:
    """
    Refund subagent — processes a refund for a verified customer and order.
    All context must be passed explicitly by the coordinator.
    """
    client = get_client()

    # All context is explicitly injected into the prompt
    # The subagent starts fresh but knows everything it needs
    prompt = f"""
Process a refund with the following verified information:

Customer:
{json.dumps(customer_data, indent=2)}

Order:
{json.dumps(order_data, indent=2)}

Reason for refund: {reason}

Process the full refund for this order now.
"""

    messages = [{"role": "user", "content": prompt}]

    # Subagent has its own completed_tools tracker
    completed_tools = ["get_customer", "lookup_order"]  # already done by coordinator

    # print(f"\n[Refund Agent] Starting with order {order_data.get('order_id')}")

    while True:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            system=REFUND_AGENT_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({
            "role": "assistant",
            "content": response.content
        })

        if response.stop_reason == "end_turn":
            # Extract final text and return as result
            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text = block.text
            # print(f"[Refund Agent] Completed")
            return {"status": "completed", "result": result_text}

        elif response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(
                        block.name,
                        block.input,
                        completed_tools
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })