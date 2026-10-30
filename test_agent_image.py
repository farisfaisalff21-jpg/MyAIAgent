import asyncio
from pathlib import Path

from dotenv import load_dotenv
from agents import Runner

from marketing_agents.marketing_agent import get_marketing_agent


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


async def main():
    agent = get_marketing_agent()

    prompt = (
        "Create a colorful Instagram promotional image for "
        "Sweet Corner bakery featuring cupcakes and cookies. "
        "Do not include text or logos."
    )

    try:
        print("Testing image generation through the marketing agent...")

        result = await Runner.run(agent, prompt)

        print("\n--- AGENT RESPONSE ---")
        print(result.final_output)

    except Exception as error:
        print(f"\nTEST FAILED: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())