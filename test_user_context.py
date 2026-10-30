import asyncio
from uuid import uuid4

from marketing_agents.service import generate_marketing_response


async def main():
    print("Testing Marketing Agent User Context...\n")

    unique_id = str(uuid4())[:8]

    user_a = f"user_a_{unique_id}"
    user_b = f"user_b_{unique_id}"

    session_1 = f"session_1_{unique_id}"
    session_2 = f"session_2_{unique_id}"

    # TEST 1: Save information for User A.
    print("Test 1: Save User A's business information")

    response_1 = await generate_marketing_response(
        user_message=(
            "My business name is Blue Star Bakery. "
            "Please remember this for our conversation."
        ),
        user_id=user_a,
        session_id=session_1,
    )

    print("PASS: First conversation completed.")
    print("Response:", response_1)

    # TEST 2: Check memory in the same session.
    print("\nTest 2: Check User A's conversation memory")

    response_2 = await generate_marketing_response(
        user_message=(
            "What is my business name? "
            "Answer using our previous conversation."
        ),
        user_id=user_a,
        session_id=session_1,
    )

    print("Response:", response_2)

    if "Blue Star Bakery" in response_2:
        print("PASS: Same-session memory works.")
    else:
        print("CHECK NEEDED: Same-session memory was not confirmed.")

    # TEST 3: Check isolation between different users.
    print("\nTest 3: Check User B's separate memory")

    response_3 = await generate_marketing_response(
        user_message=(
            "What is my business name? "
            "Only answer if I told you in this conversation."
        ),
        user_id=user_b,
        session_id=session_1,
    )

    print("Response:", response_3)

    if "Blue Star Bakery" not in response_3:
        print("PASS: User A's business name was not shared with User B.")
    else:
        print("CHECK NEEDED: User isolation needs investigation.")

    # TEST 4: Check separate sessions for the same user.
    print("\nTest 4: Check User A's separate session")

    response_4 = await generate_marketing_response(
        user_message=(
            "What is my business name? "
            "Only answer if I told you in this conversation."
        ),
        user_id=user_a,
        session_id=session_2,
    )

    print("Response:", response_4)

    if "Blue Star Bakery" not in response_4:
        print("PASS: Separate sessions have separate conversation history.")
    else:
        print("CHECK NEEDED: Session isolation needs investigation.")

    print("\nUser context testing completed.")


if __name__ == "__main__":
    asyncio.run(main())