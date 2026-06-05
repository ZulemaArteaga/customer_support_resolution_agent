import json
from agent.client import get_client, DEFAULT_MODEL
from agent.tool_definitions import TOOLS
from agent.tool_executor import execute_tool
from agent.decomposer import decompose_request

SYSTEM_PROMPT = """You are a customer support agent for an e-commerce company.

Your job is to help customers with:
- Order status and tracking
- Returns and refunds
- Billing disputes
- Account issues

Rules you must always follow:
1. Always verify the customer with get_customer before taking any action
2. Always look up the order with lookup_order before processing a refund
3. Only escalate to a human when you cannot resolve the issue yourself
4. Never make up information — always use your tools to get real data
5. Never process refunds above $500 — escalate to human instead
"""

CHAINING_PROMPT = """You are a customer support agent handling a single, specific request.

Resolve this concern step by step:
1. Verify the customer
2. Look up any relevant orders
3. Take the appropriate action
4. Confirm resolution clearly

Concern: {concern_description}
Type: {concern_type}
"""

DYNAMIC_PROMPT = """You are a customer support agent handling multiple customer concerns.

The customer has the following issues:
{concerns_list}

Instructions:
1. Verify the customer identity first
2. Investigate each concern separately using the appropriate tools
3. Resolve each issue one by one
4. Provide a single unified response that addresses all concerns clearly
"""

def run_agentic_loop(client, messages, completed_tools):
    """
    Core agentic loop — shared by both strategies.
    Runs until Claude reaches end_turn.
    """
    while True:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({
            "role": "assistant",
            "content": response.content
        })

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    pass
                    # print(f"\n--- Agent: {block.text}")
            break

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

def run_chaining_strategy(client, concern, customer_message):
    """
    Strategy 1 — Prompt Chaining.
    Used for single predictable requests.
    Fixed sequence of steps.
    """
    # print(f"\n[Strategy] Prompt Chaining")

    completed_tools = []

    # Build a focused prompt for this specific concern
    focused_message = CHAINING_PROMPT.format(
        concern_description=concern['description'],
        concern_type=concern['type']
    )

    # Include original customer message for context
    messages = [
        {"role": "user", "content": f"{focused_message}\n\nCustomer message: {customer_message}"}
    ]

    run_agentic_loop(client, messages, completed_tools)

def run_dynamic_strategy(client, decomposition, customer_message):
    """
    Strategy 2 — Dynamic Decomposition.
    Used for multiple or ambiguous concerns.
    Claude builds its own plan based on what it finds.
    """
    # print(f"\n[Strategy] Dynamic Decomposition")

    completed_tools = []

    # Format all concerns into a readable list for Claude
    concerns_list = "\n".join([
        f"{i+1}. [{c['type'].upper()}] {c['description']}"
        f"{' (Order: ' + c['order_id'] + ')' if c['order_id'] else ''}"
        for i, c in enumerate(decomposition['concerns'])
    ])

    # Build a dynamic prompt covering all concerns
    dynamic_message = DYNAMIC_PROMPT.format(
        concerns_list=concerns_list
    )

    messages = [
        {"role": "user", "content": f"{dynamic_message}\n\nOriginal message: {customer_message}"}
    ]

    run_agentic_loop(client, messages, completed_tools)

def run_agent(user_message: str):
    client = get_client()

    # print(f"\n--- Customer: {user_message}")
    # print("-" * 50)

    # Step 1: Decompose the request
    decomposition = decompose_request(user_message)

    # Step 2: Choose strategy based on decomposition
    if decomposition['strategy'] == 'chaining':
        run_chaining_strategy(
            client,
            decomposition['concerns'][0],
            user_message
        )
    else:
        run_dynamic_strategy(
            client,
            decomposition,
            user_message
        )

    # Multi-turn conversation
    # print("\n--- (Type your reply or 'done' to end the conversation)")
    while True:
        user_reply = input("Customer: ").strip()

        if user_reply.lower() == "done" or user_reply == "":
            # print("\n--- Session ended.")
            break