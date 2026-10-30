import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from agents import Runner

from marketing_agents.marketing_agent import get_marketing_agent


# Load environment variables from the project root .env file.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY was not found.")
        print("Check that your .env file is in E:\\MyAIAgent.")
        print("Ensure it contains OPENAI_API_KEY=your_key")
        return

    agent = get_marketing_agent()

    tests = [
        (
            "Caption Writer Handoff",
            "Write a short, friendly Instagram caption for Sweet Corner, "
            "a bakery selling cakes and cookies to families.",
        ),
        (
            "Content Planner Handoff",
            "Create a 7-day Instagram content plan for Sweet Corner, "
            "which sells cakes and cookies to families.",
        ),
    ]

    for name, message in tests:
        print(f"\n--- {name} ---")

        try:
            result = await Runner.run(agent, message)

            print("\nResponse:")
            print(result.final_output)

            print("\nAgent execution steps:")
            handoff_detected = False

            for item in result.new_items:
                if item.type == "handoff_call_item":
                    handoff_detected = True
                    print("Handoff call detected.")

                elif item.type == "handoff_output_item":
                    handoff_detected = True
                    print("Handoff completed.")

            if handoff_detected:
                print("Handoff verification: specialist delegation detected.")
            else:
                print(
                    "Handoff not detected in this run. "
                    "Review the agent execution steps."
                )

        except Exception as error:
            print(f"FAILED: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())