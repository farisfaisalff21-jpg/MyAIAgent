import asyncio
from pathlib import Path

from dotenv import load_dotenv
from agents.realtime import RealtimeAgent, RealtimeRunner

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


voice_agent = RealtimeAgent(
    name="Marketing Voice Assistant",
    instructions="""
    You are a friendly AI Marketing Assistant.
    Speak naturally and keep replies short.
    Help with social media captions, marketing ideas,
    content plans, and small-business marketing.
    Support English, Urdu, and Roman Urdu.
    Never invent business facts or guarantee results.
    """,
)

runner = RealtimeRunner(
    starting_agent=voice_agent,
    config={
        "model_settings": {
            "model_name": "gpt-realtime-2.1",
            "audio": {
                "input": {
                    "format": "pcm16",
                    "transcription": {
                        "model": "gpt-4o-mini-transcribe"
                    },
                    "turn_detection": {
                        "type": "semantic_vad",
                        "interrupt_response": True,
                    },
                },
                "output": {
                    "format": "pcm16",
                    "voice": "ash",
                },
            },
        }
    },
)


async def main():
    if not __import__("os").getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY was not found in .env.")
        return

    print("Connecting to the Realtime API...")

    try:
        session = await runner.run()

        async with session:
            await session.send_message(
                "Say hello and introduce yourself as my AI "
                "Marketing Assistant in one short sentence."
            )

            async for event in session:
                if event.type == "audio":
                    print("Audio response received.")

                elif event.type == "history_added":
                    print("Conversation event received.")

                elif event.type == "agent_end":
                    print("Assistant turn completed.")
                    break

                elif event.type == "error":
                    print("Realtime error:", event.error)
                    break

        print("Realtime backend test finished.")

    except Exception as error:
        print(
            f"TEST FAILED: {type(error).__name__}: {error}"
        )


if __name__ == "__main__":
    asyncio.run(main())