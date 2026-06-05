import json
from agent.client import get_client, DEFAULT_MODEL
from agent.tool_definitions import TOOLS
from agent.tool_executor import execute_tool

ORDER_STATUS_AGENT_PROMPT = """You are an order status specialist agent.

You have been given verified customer information by the coordinator.
Your ONLY job is to look up the order status and report it clearly.

Rules:
1. The customer has already been verified — do not call get_customer again
2. Call lookup_order with the provided order_id
3. Report the order status, product, amount and delivery date clearly
"""

def run_order_status_agent(customer_data: dict, order_id: str) -> dict:
    """
    Order status subagent — looks up and reports order status.
    All context must be passed explicitly by the coordinator.
    """
    client = get_client()

    prompt = f"""
Check the status of the following order for this verified customer:

Customer:
{json.dumps(customer_data, indent=2)}

Order ID to check: {order_id}

Look up this order and report its current status.
"""

    messages = [{"role": "user", "content": prompt}]

    # Customer already verified by coordinator
    completed_tools = ["get_customer"]

    # print(f"\n[Order Status Agent] Checking order {order_id}")

    while True:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            system=ORDER_STATUS_AGENT_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({
            "role": "assistant",
            "content": response.content
        })

        if response.stop_reason == "end_turn":
            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text = block.text
            # print(f"[Order Status Agent] Completed")
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