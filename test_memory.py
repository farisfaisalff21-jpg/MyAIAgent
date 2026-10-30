import asyncio

from marketing_agents.service import generate_marketing_response


async def main():
    session_id = "memory_test_01"
    user_id = "user_A"

    try:
        first = await generate_marketing_response(
            "My bakery is called Sweet Corner. "
            "We sell cakes and cookies. Remember this for our conversation.",
            session_id=session_id,
            user_id=user_id,
        )

        print("\n--- FIRST RESPONSE ---")
        print(first)

        second = await generate_marketing_response(
            "What is my bakery called, and what products do I sell? "
            "Answer using our previous conversation.",
            session_id=session_id,
            user_id=user_id,
        )

        print("\n--- MEMORY TEST ---")
        print(second)

        if (
            "sweet corner" in second.lower()
            and "cakes" in second.lower()
            and "cookies" in second.lower()
        ):
            print("\nSUCCESS: User memory test passed.")
        else:
            print(
                "\nCHECK: The response may use different wording. "
                "Review the answer above."
            )

    except Exception as error:
        print(f"\nTEST FAILED: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())