from tools.human_approval import (
    create_approval_request,
    decide_approval,
)


def test_approval_workflow():
    print("Testing Human-in-the-loop...\n")

    # Test 1: New request starts as pending.
    request = create_approval_request(
        "Publish campaign",
        "Publish Sweet Corner's Instagram campaign.",
    )

    assert request.status == "pending"
    print("PASS: New request starts as pending.")

    # Test 2: Approve the request.
    decide_approval(request, True)

    assert request.status == "approved"
    print("PASS: Approval decision recorded.")

    # Test 3: A second decision must be rejected.
    try:
        decide_approval(request, False)
        raise AssertionError("A second decision was incorrectly accepted.")
    except ValueError:
        print("PASS: Duplicate decision rejected.")

    # Test 4: Reject a separate request.
    rejected_request = create_approval_request(
        "Send promotional email",
        "Send the proposed promotion to customers.",
    )

    decide_approval(rejected_request, False)

    assert rejected_request.status == "rejected"
    print("PASS: Rejection decision recorded.")

    # Test 5: Empty action must be rejected.
    try:
        create_approval_request("", "Some details")
        raise AssertionError("Empty action was incorrectly accepted.")
    except ValueError:
        print("PASS: Empty action rejected.")

    print("\nAll Human-in-the-loop tests passed!")


if __name__ == "__main__":
    test_approval_workflow()