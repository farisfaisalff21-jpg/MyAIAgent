import asyncio

from marketing_agents.service import generate_marketing_response


async def main():
    print("Testing File Search through Marketing Agent...\n")

    try:
        response = await generate_marketing_response(
            user_message=(
                "According to my uploaded business documents, "
                "what products does Sweet Corner sell, who is its "
                "target audience, and what is its brand tone? "
                "Use the business document search tool."
            ),
            user_id="file_search_test_user",
            session_id="file_search_test_session",
        )

        print("--- MARKETING AGENT RESPONSE ---")
        print(response)

    except Exception as error:
        print(f"Test failed: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())