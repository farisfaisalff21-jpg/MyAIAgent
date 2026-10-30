from agents import Runner

from marketing_agents.marketing_agent import get_marketing_agent
from tools.human_approval import list_pending_requests


def main():
    print("Testing Marketing Agent Human Approval Integration...\n")

    agent = get_marketing_agent()

    request_text = (
        "Please register a human approval request to publish "
        "a proposed Instagram marketing campaign for Sweet Corner. "
        "The campaign will promote cakes and cookies. "
        "Do not publish anything yet. Create the approval request only."
    )

    print("Running Marketing Agent...\n")

    result = Runner.run_sync(agent, request_text)

    print("Agent response:")
    print(result.final_output)

    print("\nChecking pending approval requests...")

    pending_requests = list_pending_requests()

    matching_requests = [
        request
        for request in pending_requests
        if request["action"].lower().find("publish") >= 0
        and "sweet corner" in request["details"].lower()
    ]

    if matching_requests:
        print("\nPASS: Approval request found in the database.")

        for request in matching_requests:
            print(f"Request ID: {request['request_id']}")
            print(f"Action: {request['action']}")
            print(f"Status: {request['status']}")

        print("\nNo campaign was published.")
    else:
        print(
            "\nCHECK NEEDED: No matching pending request was found. "
            "Review the agent response and database."
        )


if __name__ == "__main__":
    main()