import asyncio

from marketing_agents.service import generate_marketing_response


async def main():
    print("Testing Web Search through Marketing Agent...\n")

    try:
        response = await generate_marketing_response(
            user_message=(
                "Research three current social media marketing "
                "trends for small bakery businesses in 2026. "
                "Use web search and include source links."
            ),
            user_id="web_search_test_user",
            session_id="web_search_test_session",
        )

        print("--- MARKETING AGENT RESPONSE ---")
        print(response)

    except Exception as error:
        print(f"Test failed: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())