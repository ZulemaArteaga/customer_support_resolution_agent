import json
from agent.client import get_client, DEFAULT_MODEL
from agent.tool_definitions import TOOLS
from agent.tool_executor import execute_tool
from agent.decomposer import decompose_request
from agent.session_manager import save_session, load_session
from agent.subagents.refund_agent import run_refund_agent
from agent.subagents.order_status_agent import run_order_status_agent
from agent.subagents.escalation_agent import run_escalation_agent

COORDINATOR_PROMPT = """You are a customer support coordinator.

Your job is to:
1. Verify the customer identity using get_customer
2. Look up any orders mentioned using lookup_order
3. Delegate specialized tasks to subagents
4. Synthesize all results into a unified response

You are the hub — you gather all information first, then delegate.
Never skip customer verification.
"""

SYNTHESIS_PROMPT = """You are a customer support coordinator writing a final response.

Based on the results from your specialized subagents, write a clear, 
friendly and unified response to the customer that addresses all their concerns.

Customer name: {customer_name}
Subagent results:
{results}

Write a single cohesive response that summarizes everything clearly.
"""

def verify_customer(client, customer_id: str) -> dict:
    """
    Coordinator verifies customer before delegating to any subagent.
    This is the first gate — nothing proceeds without this.
    """
    completed_tools = []

    messages = [
        {"role": "user", "content": f"Verify customer with ID: {customer_id}"}
    ]

    # print(f"\n[Coordinator] Verifying customer {customer_id}")

    while True:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=512,
            system=COORDINATOR_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({
            "role": "assistant",
            "content": response.content
        })

        if response.stop_reason == "end_turn":
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
                    # Return customer data directly when found
                    if block.name == "get_customer" and "error" not in result:
                        return result

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })

    return {"error": f"Could not verify customer {customer_id}"}

def lookup_order_data(client, order_id: str, completed_tools: list) -> dict:
    """
    Coordinator looks up order data before passing to subagent.
    """
    from tools.mcp_tools import lookup_order
    from agent.hooks import post_tool_use_hook

    # print(f"\n[Coordinator] Looking up order {order_id}")
    result = lookup_order(order_id)
    normalized = post_tool_use_hook("lookup_order", result)
    completed_tools.append("lookup_order")
    # print(f"[Tool Result] {normalized}")
    return normalized

def synthesize_response(client, customer_name: str, results: list) -> str:
    """
    Coordinator synthesizes all subagent results into one unified response.
    """
    results_text = "\n\n".join([
        f"Concern {i+1} ({r['type']}):\n{r['result']}"
        for i, r in enumerate(results)
    ])

    prompt = SYNTHESIS_PROMPT.format(
        customer_name=customer_name,
        results=results_text
    )

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

def run_agentic_loop_with_synthesis(client, messages, completed_tools, customer_data, session_name):
    """
    Runs the agentic loop for resumed sessions and saves updated session.
    """
    final_text = ""
    while True:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            system=COORDINATOR_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
                    # print(f"\n--- Agent: {final_text}")
            break

        elif response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input, completed_tools)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })
            messages.append({"role": "user", "content": tool_results})

    # Save updated session
    save_session(session_name, messages, completed_tools, customer_data)
    return final_text

def run_coordinator(user_message: str, session_name: str = None, resume: bool = False) -> str:
    """
    Main coordinator entry point.
    Orchestrates the full multi-agent flow with session management.
    """
    client = get_client()

    # print(f"\n--- Customer: {user_message}")
    # print("-" * 50)

    # Session resumption — load existing session
    if resume and session_name:
        session = load_session(session_name)
        if session:
            customer_data = session['customer_data']
            completed_tools = session['completed_tools']
            messages = session['messages']
            # print(f"\n[Coordinator] Resuming session for {customer_data.get('name')}")

            # Add new message to existing history
            messages.append({"role": "user", "content": user_message})

            # Run the agentic loop with resumed context
            return run_agentic_loop_with_synthesis(
                client, messages, completed_tools, customer_data, session_name
            )

    # Fresh session — decompose and handle normally
    decomposition = decompose_request(user_message)

    # Extract customer ID from concerns
    customer_id = None
    for concern in decomposition['concerns']:
        if concern.get('customer_id'):
            customer_id = concern['customer_id']
            break

    if not customer_id:
        return "I need your customer ID to assist you. Could you please provide it?"

    # Verify customer — nothing proceeds without this
    customer_data = verify_customer(client, customer_id)
    if "error" in customer_data:
        return "I'm sorry, I couldn't verify your account. Please contact support."

    # print(f"\n[Coordinator] Customer verified: {customer_data['name']}")

    # Delegate each concern to the right subagent
    completed_tools = ["get_customer"]
    subagent_results = []

    for concern in decomposition['concerns']:
        concern_type = concern['type']
        order_id = concern.get('order_id')

        # print(f"\n[Coordinator] Delegating: {concern_type} to subagent")

        if concern_type == "refund" and order_id:
            order_data = lookup_order_data(client, order_id, completed_tools)
            result = run_refund_agent(
                customer_data=customer_data,
                order_data=order_data,
                reason=concern['description']
            )
            subagent_results.append({"type": concern_type, "result": result['result']})

        elif concern_type == "order_status" and order_id:
            result = run_order_status_agent(
                customer_data=customer_data,
                order_id=order_id
            )
            subagent_results.append({"type": concern_type, "result": result['result']})

        elif concern_type in ["billing_dispute", "account_issue", "other"]:
            result = run_escalation_agent(
                customer_data=customer_data,
                reason=concern['description'],
                context={"order_id": order_id} if order_id else {}
            )
            subagent_results.append({"type": concern_type, "result": result['result']})

    # Synthesize all results into one response
    # print(f"\n[Coordinator] Synthesizing {len(subagent_results)} result(s)")
    final_response = synthesize_response(client, customer_data['name'], subagent_results)
    # print(f"\n--- Agent: {final_response}")

    # Save session if a name was provided
    if session_name:
        messages = [{"role": "user", "content": user_message}]
        messages.append({"role": "assistant", "content": final_response})
        save_session(session_name, messages, completed_tools, customer_data)

    return final_response