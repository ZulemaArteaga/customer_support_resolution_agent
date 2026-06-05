import os
import sys
from agent.coordinator import run_coordinator

def main():
    # Check for the required API token
    token = os.getenv("MODEL_API_TOKEN") or os.getenv("ANTHROPIC_API_KEY")

    if not token:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please set it using: export ANTHROPIC_API_KEY='your_token_here'", file=sys.stderr)
        sys.exit(1)

    # Get inputs from command-line arguments or interactive input
    if len(sys.argv) >= 3:
        # Arguments provided
        customer_id = sys.argv[1]
        message = " ".join(sys.argv[2:])
    else:
        # Interactive mode
        print("Customer Support Agent at your service")
        print("-" * 50)
        customer_id = input("Hello. Please enter your customer ID: ").strip()
        message = input("How can we help you today? ").strip()

    # Format payload and session name
    full_message = f"Hi, my customer ID is {customer_id}. {message}"
    session_name = f"{customer_id}_session"

    # Trigger the coordinator agent
    response = run_coordinator(full_message, session_name=session_name)
    print(response)

if __name__ == "__main__":
    main()