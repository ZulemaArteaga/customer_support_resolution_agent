# This file tells Claude what tools exist and how to call them.
TOOLS = [
    {
        "name": "get_customer",
        "description": "Fetch customer information by customer ID. Always call this first to verify the customer exists before taking any action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique customer identifier e.g. CUST-001"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "lookup_order",
        "description": "Look up order details by order ID. Call this after verifying the customer to get order information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The unique order identifier e.g. ORD-001"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": "Process a refund for a given order. Only call this after verifying the customer and looking up the order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order to refund"
                },
                "amount": {
                    "type": "number",
                    "description": "The refund amount in USD"
                }
            },
            "required": ["order_id", "amount"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the case to a human support agent when you cannot resolve the issue yourself.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer being escalated"
                },
                "reason": {
                    "type": "string",
                    "description": "Detailed reason for escalation"
                }
            },
            "required": ["customer_id", "reason"]
        }
    }
]