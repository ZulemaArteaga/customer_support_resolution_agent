import json
from agent.client import get_client, DEFAULT_MODEL

DECOMPOSE_PROMPT = """You are a customer support request analyzer.

Your job is to read a customer message and identify ALL distinct issues or concerns.

For each concern, identify:
- type: one of [refund, order_status, billing_dispute, account_issue, other]
- description: brief description of the concern
- order_id: if mentioned (e.g. ORD-001), otherwise null
- customer_id: if mentioned (e.g. CUST-001), otherwise null

You must respond with ONLY a raw JSON object — no markdown, no backticks, no explanation, no preamble.
The very first character of your response must be { and the last must be }.

Use this exact format:
{
    "concern_count": <number>,
    "strategy": "chaining" or "dynamic",
    "concerns": [
        {
            "type": "<type>",
            "description": "<description>",
            "order_id": "<order_id or null>",
            "customer_id": "<customer_id or null>"
        }
    ]
}

Use "chaining" strategy when there is exactly one concern of a known predictable type.
Use "dynamic" strategy when there are multiple concerns or the request is ambiguous.
"""

def decompose_request(user_message: str) -> dict:
    """
    Analyzes a customer message and breaks it into
    distinct concerns with a recommended strategy.
    """
    client = get_client()

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        system=DECOMPOSE_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    raw = response.content[0].text.strip()

    try:
        # Strip any accidental markdown backticks
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
        # print(f"\n[Decomposer] Found {result['concern_count']} concern(s)")
        # print(f"[Decomposer] Strategy: {result['strategy']}")
        for i, concern in enumerate(result['concerns'], 1):
            # print(f"[Decomposer] Concern {i}: {concern['type']} — {concern['description']}")
            return result
    except json.JSONDecodeError:
        # Fallback — treat as single dynamic concern
        # print("[Decomposer] Could not parse response, falling back to dynamic")
        return {
            "concern_count": 1,
            "strategy": "dynamic",
            "concerns": [
                {
                    "type": "other",
                    "description": user_message,
                    "order_id": None,
                    "customer_id": None
                }
            ]
        }