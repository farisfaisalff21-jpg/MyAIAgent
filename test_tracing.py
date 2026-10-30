from agents import Runner, flush_traces

from marketing_agents.marketing_agent import get_marketing_agent


def main():
    print("Testing Marketing Agent Tracing...\n")

    agent = get_marketing_agent()

    try:
        result = Runner.run_sync(
            agent,
            "Give me three simple Instagram marketing ideas for "
            "Sweet Corner, a bakery selling cakes and cookies."
        )

        print("PASS: Agent run completed.")
        print("\nAgent response:")
        print(result.final_output)

    finally:
        print("\nFlushing tracing data...")
        flush_traces()
        print("Tracing flush completed.")


if __name__ == "__main__":
    main()