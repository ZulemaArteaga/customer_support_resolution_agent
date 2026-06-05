import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from behave import given, when, then

def capture_agent_output(message: str, session_name: str) -> str:
    """Run the agent with real API calls and capture all printed output."""
    from agent.coordinator import run_coordinator

    captured = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured

    try:
        # Calling the real coordinator without any mocks
        response = run_coordinator(message, session_name=session_name)
        print(f"--- Agent: {response}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        sys.stdout = original_stdout

    return captured.getvalue()

# --- GIVEN steps ---

@given('a customer with ID "{customer_id}"')
def step_given_customer(context, customer_id):
    context.customer_id = customer_id
    context.output = ""

# --- WHEN steps ---

@when('they request a refund for order "{order_id}"')
def step_when_refund(context, order_id):
    context.order_id = order_id
    message = (
        f"Hi, my customer ID is {context.customer_id}. "
        f"I want a refund for order {order_id}."
    )
    session_name = f"test_{context.customer_id}_{order_id}"

    # Use live API
    context.output = capture_agent_output(message, session_name)
    print(context.output)

# --- THEN steps ---

@then('the refund should be approved')
def step_then_refund_approved(context):
    output_lower = context.output.lower()
    assert "approved" in output_lower, (
        f"Expected 'approved' in output but got:\n{context.output}"
    )

@then('the response should contain "{keyword}"')
def step_then_response_contains(context, keyword):
    output_lower = context.output.lower()
    assert keyword.lower() in output_lower, (
        f"Expected '{keyword}' in output but got:\n{context.output}"
    )

@then('the case should be escalated to a human')
def step_then_escalated(context):
    output_lower = context.output.lower()
    assert "escalat" in output_lower, (
        f"Expected escalation in output but got:\n{context.output}"
    )

@then('no escalation should occur')
def step_then_no_escalation(context):
    output_lower = context.output.lower()
    assert "escalat" not in output_lower, (
        f"Expected no escalation but got:\n{context.output}"
    )

@then('the agent should respond with a graceful error')
def step_then_graceful_error(context):
    output_lower = context.output.lower()
    assert any(word in output_lower for word in ["sorry", "couldn't verify", "error", "not found"]), (
        f"Expected graceful error in output but got:\n{context.output}"
    )