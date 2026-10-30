import asyncio

from agents import Runner, InputGuardrailTripwireTriggered
from marketing_agents.marketing_agent import get_marketing_agent


async def main():
    agent = get_marketing_agent()

    print("Testing Marketing Agent Guardrails...\n")

    # Test 1: Empty input should be rejected.
    print("Test 1: Empty input")

    try:
        await Runner.run(agent, "")
        print("FAIL: Empty input was not blocked.")
    except (InputGuardrailTripwireTriggered, ValueError) as error:
        print(f"PASS: Empty input rejected ({type(error).__name__}).")

    # Test 2: Input longer than 5000 characters should be rejected.
    print("\nTest 2: Oversized input")

    try:
        await Runner.run(agent, "A" * 5001)
        print("FAIL: Oversized input was not blocked.")
    except (InputGuardrailTripwireTriggered, ValueError) as error:
        print(f"PASS: Oversized input rejected ({type(error).__name__}).")

    # Test 3: Normal marketing request should work.
    print("\nTest 3: Normal marketing request")

    try:
        result = await Runner.run(
            agent,
            "Give me three Instagram marketing ideas for a bakery."
        )
        print("PASS: Normal request completed.")
        print("\nAgent response:")
        print(result.final_output)

    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())