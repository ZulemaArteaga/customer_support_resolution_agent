# Each scenario defines:
# - name: what we are testing
# - message: the customer input
# - session_name: for session management
# - resume: whether to resume a session
# - expected: what we expect to see in the output

SCENARIOS = [
    {
        "id": 1,
        "name": "Standard Refund — Happy Path",
        "description": "Customer requests refund on delivered order under $500",
        "message": "Hi, my customer ID is CUST-001. I want a refund for order ORD-001.",
        "session_name": "test_scenario_1",
        "resume": False,
        "expected": {
            "tools_called": ["get_customer", "lookup_order", "process_refund"],
            "keywords_in_response": ["refund", "approved", "89.99"],
            "should_escalate": False,
            "should_fail": False
        }
    },
    {
        "id": 2,
        "name": "High Value Refund — Policy Enforcement",
        "description": "Customer requests refund over $500 — should escalate to human",
        "message": "Hi, my customer ID is CUST-004. I want a refund for order ORD-005.",
        "session_name": "test_scenario_2",
        "resume": False,
        "expected": {
            "tools_called": ["get_customer", "lookup_order", "escalate_to_human"],
            "keywords_in_response": ["escalat", "human", "support"],
            "should_escalate": True,
            "should_fail": False
        }
    }
]