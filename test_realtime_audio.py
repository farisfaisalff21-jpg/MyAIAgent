import asyncio
import os
from pathlib import Path

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from agents.realtime import RealtimeAgent, RealtimeRunner

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SAMPLE_RATE = 24000
CHANNELS = 1
CHUNK_SIZE = 480

MICROPHONE_DEVICE = 1
SPEAKER_DEVICE = 3


agent = RealtimeAgent(
    name="Marketing Voice Assistant",
    instructions="""
You are a friendly AI Marketing Assistant.
Keep spoken replies natural and concise.
Help with marketing strategies, captions, and content plans.
Support English, Urdu, and Roman Urdu.
Never invent business facts or guarantee results.
""",
)

runner = RealtimeRunner(
    starting_agent=agent,
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


async def send_microphone_audio(session, microphone):
    print("Microphone is ON. Speak now.")

    while True:
        audio, overflowed = await asyncio.to_thread(
            microphone.read, CHUNK_SIZE
        )

        if overflowed:
            print("Microphone buffer overflow.")

        await session.send_audio(audio.tobytes())


async def receive_audio(session, speaker):
    print("Listening for the AI's response...")

    async for event in session:
        if event.type == "audio":
            audio_bytes = event.audio.data

            if audio_bytes:
                samples = np.frombuffer(
                    audio_bytes, dtype=np.int16
                )
                await asyncio.to_thread(speaker.write, samples)

        elif event.type == "audio_interrupted":
            print("\nAssistant audio interrupted.")

        elif event.type == "history_added":
            print(f"\nConversation event: {type(event.item).__name__}")

        elif event.type == "agent_end":
            print("\nAssistant finished this response.")

        elif event.type == "error":
            print(f"\nRealtime error: {event.error}")


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY was not found in .env.")
        return

    try:
        print("Opening your internal microphone and speakers...")

        with sd.InputStream(
            device=MICROPHONE_DEVICE,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
        ) as microphone, sd.OutputStream(
            device=SPEAKER_DEVICE,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
        ) as speaker:

            session = await runner.run()

            async with session:
                sender = asyncio.create_task(
                    send_microphone_audio(session, microphone)
                )
                receiver = asyncio.create_task(
                    receive_audio(session, speaker)
                )

                try:
                    await asyncio.gather(sender, receiver)
                finally:
                    sender.cancel()
                    receiver.cancel()
                    await asyncio.gather(
                        sender, receiver, return_exceptions=True
                    )

    except asyncio.CancelledError:
        pass
    except Exception as error:
        print(f"\nTEST FAILED: {type(error).__name__}: {error}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nVoice test stopped.")  