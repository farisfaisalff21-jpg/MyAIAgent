import asyncio

from marketing_agents.service import stream_marketing_response


async def main():
    print("Testing user-scoped streaming...\n")

    try:
        async for chunk in stream_marketing_response(
            "Write a short marketing caption for a bakery.",
            session_id="streaming_test_01",
            user_id="user_A",
        ):
            print(chunk, end="", flush=True)

        print("\n\nSUCCESS: User-scoped streaming test completed.")

    except Exception as error:
        print(
            f"\nSTREAMING TEST FAILED: "
            f"{type(error).__name__}: {error}"
        )


if __name__ == "__main__":
    asyncio.run(main())