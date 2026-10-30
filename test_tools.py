import asyncio

from marketing_agents.service import generate_marketing_response


async def main():
    tests = [
        (
            "Caption Tool",
            "Generate one short Instagram caption for Sweet Corner, "
            "a bakery selling cakes and cookies for families and students. "
            "Use a friendly tone.",
            "tool_test_caption",
        ),
        (
            "Hashtag Tool",
            "Suggest relevant Instagram hashtags for a bakery selling "
            "cakes and cookies to families and students.",
            "tool_test_hashtags",
        ),
        (
            "Content Plan Tool",
            "Create a 7-day Instagram content plan for Sweet Corner, "
            "which sells cakes and cookies to families and students.",
            "tool_test_plan",
        ),
    ]

    for name, message, session_id in tests:
        print(f"\n--- {name} ---")

        try:
            response = await generate_marketing_response(
                message,
                session_id,
            )
            print(response)

        except Exception as error:
            print(f"FAILED: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())