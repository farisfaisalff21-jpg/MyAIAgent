import asyncio
from marketing_agents.service import generate_marketing_response


async def main():
    session_id = "final_backend_test_01"

    print("Starting final backend test...")

    try:
        response = await generate_marketing_response(
            "Create a 3-day social media content plan for a bakery "
            "that sells cakes and cookies. Include a post idea and "
            "caption for each day.",
            session_id,
        )

        print("\nSUCCESS: The AI agent responded!")
        print("-" * 45)
        print(response)
        print("-" * 45)

    except Exception as error:
        print("\nBACKEND TEST FAILED")
        print(type(error).__name__, error)


if __name__ == "__main__":
    asyncio.run(main())