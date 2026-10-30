import asyncio
from uuid import uuid4

from agents import flush_traces

from marketing_agents.service import (
    generate_marketing_response,
    stream_marketing_response,
    validate_request,
)

from tools.human_approval import (
    create_approval_request,
    get_approval_request,
)


TEST_ID = str(uuid4())[:8]
USER_ID = f"final_test_user_{TEST_ID}"
SESSION_ID = f"final_test_session_{TEST_ID}"


def test_validation():
    print("\nTEST 1: Input Validation")

    try:
        validate_request("", USER_ID, SESSION_ID)
        raise AssertionError("Empty input was accepted.")
    except ValueError:
        print("PASS: Empty input rejected.")

    try:
        validate_request("A" * 5001, USER_ID, SESSION_ID)
        raise AssertionError("Oversized input was accepted.")
    except ValueError:
        print("PASS: Oversized input rejected.")


def test_approval():
    print("\nTEST 2: Human Approval Database")

    request = create_approval_request(
        action="Final integration test",
        details=f"Testing approval database: {TEST_ID}",
    )

    saved_request = get_approval_request(
        request["request_id"]
    )

    assert saved_request is not None
    assert saved_request["status"] == "pending"

    print("PASS: Approval request saved.")
    print("Request ID:", saved_request["request_id"])
    print("Status:", saved_request["status"])


async def test_agent():
    print("\nTEST 3: Marketing Agent Response")

    response = await generate_marketing_response(
        user_message=(
            "Give me three simple Instagram marketing ideas "
            "for a bakery selling cakes and cookies."
        ),
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    assert isinstance(response, str)
    assert response.strip()

    print("PASS: Marketing Agent generated a response.")
    print("\nAgent response:\n")
    print(response)


async def test_streaming():
    print("\nTEST 4: Streaming")

    chunks = []

    async for chunk in stream_marketing_response(
        user_message="Give me one short bakery marketing tip.",
        user_id=USER_ID,
        session_id=f"{SESSION_ID}_stream",
    ):
        chunks.append(chunk)

    streamed_text = "".join(chunks)

    assert streamed_text.strip()

    print("PASS: Streaming generated text.")
    print("Streamed output:\n")
    print(streamed_text)


async def main():
    print("=" * 55)
    print("FINAL MARKETING AGENT BACKEND INTEGRATION TEST")
    print("=" * 55)

    passed = 0
    failed = 0

    tests = [
        ("Input Validation", test_validation),
        ("Approval Database", test_approval),
        ("Marketing Agent", test_agent),
        ("Streaming", test_streaming),
    ]

    try:
        for name, test_function in tests:
            try:
                result = test_function()

                if asyncio.iscoroutine(result):
                    await result

                passed += 1

            except Exception as error:
                failed += 1
                print(f"\nFAIL: {name}")
                print(f"Error: {type(error).__name__}: {error}")

    finally:
        print("\nFlushing tracing data...")

        try:
            flush_traces()
            print("Tracing flush completed.")
        except Exception as error:
            print(f"Tracing warning: {error}")

    print("\n" + "=" * 55)
    print("FINAL TEST SUMMARY")
    print("=" * 55)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nSUCCESS: All final integration tests passed!")
    else:
        print("\nCHECK NEEDED: Some tests failed.")


if __name__ == "__main__":
    asyncio.run(main())