import json
from agent.client import get_client, DEFAULT_MODEL
from agent.tool_definitions import TOOLS
from agent.tool_executor import execute_tool

ESCALATION_AGENT_PROMPT = """You are an escalation specialist agent.

You have been given verified customer information and a reason for escalation by the coordinator.
Your ONLY job is to escalate this case to a human agent with a clear structured summary.

Rules:
1. The customer has already been verified — do not call get_customer again
2. Call escalate_to_human with the customer_id and a detailed reason
3. The reason must include: what the customer wants, why it cannot be automated, 
   and any relevant order or account details
4. Confirm the escalation clearly to the coordinator
"""

def run_escalation_agent(customer_data: dict, reason: str, context: dict = None) -> dict:
    """
    Escalation subagent — creates a structured escalation to a human agent.
    All context must be passed explicitly by the coordinator.
    """
    client = get_client()

    prompt = f"""
Escalate this case to a human agent with the following information:

Customer:
{json.dumps(customer_data, indent=2)}

Reason for escalation: {reason}

Additional context:
{json.dumps(context or {}, indent=2)}

Create a structured escalation now.
"""

    messages = [{"role": "user", "content": prompt}]

    # Customer already verified by coordinator
    completed_tools = ["get_customer"]

    # print(f"\n[Escalation Agent] Escalating for customer {customer_data.get('customer_id')}")

    while True:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            system=ESCALATION_AGENT_PROMPT,
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
            # print(f"[Escalation Agent] Completed")
            return {"status": "escalated", "result": result_text}

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