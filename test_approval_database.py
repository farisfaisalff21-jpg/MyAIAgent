from tools.human_approval import (
    create_approval_request,
    get_approval_request,
    list_pending_requests,
    decide_approval,
)


def main():
    print("Testing SQLite Approval Workflow...\n")

    # Test 1: Create a request.
    request = create_approval_request(
        "Publish Instagram campaign",
        "Test campaign for Sweet Corner.",
    )
    request_id = request["request_id"]

    assert request["status"] == "pending"
    print("PASS: Request created as pending.")

    # Test 2: Retrieve the saved request.
    saved = get_approval_request(request_id)

    assert saved is not None
    assert saved["action"] == "Publish Instagram campaign"
    print("PASS: Request retrieved from SQLite.")

    # Test 3: Pending requests are listed.
    pending_ids = {
        item["request_id"]
        for item in list_pending_requests()
    }

    assert request_id in pending_ids
    print("PASS: Pending request appears in the list.")

    # Test 4: Record a human approval.
    approved = decide_approval(request_id, True)

    assert approved["status"] == "approved"
    assert approved["decided_at"] is not None
    print("PASS: Approval decision saved.")

    # Test 5: Prevent a second decision.
    try:
        decide_approval(request_id, False)
    except ValueError:
        print("PASS: Duplicate decision blocked.")
    else:
        raise AssertionError("Duplicate decision was allowed.")

    # Test 6: Reject another request.
    rejected_request = create_approval_request(
        "Send promotional email",
        "Test email approval request.",
    )

    rejected = decide_approval(
        rejected_request["request_id"],
        False,
    )

    assert rejected["status"] == "rejected"
    print("PASS: Rejection decision saved.")

    print("\nAll SQLite approval tests passed!")
    print("No external actions were executed.")


if __name__ == "__main__":
    main()  