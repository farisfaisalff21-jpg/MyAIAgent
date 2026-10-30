from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
)
from agents.decorators import input_guardrail


MAX_MESSAGE_LENGTH = 5000


def extract_message(
    input_data: str | list[TResponseInputItem],
) -> str:
    """Convert supported agent input into text for basic validation."""

    if isinstance(input_data, str):
        return input_data

    parts = []

    for item in input_data:
        if isinstance(item, dict):
            content = item.get("content", "")

            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if isinstance(text, str):
                            parts.append(text)

    return "\n".join(parts)


@input_guardrail(run_in_parallel=False)
async def marketing_input_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Check message length and whether the request relates to marketing."""

    message = extract_message(input).strip()

    if not message:
        return GuardrailFunctionOutput(
            output_info="The message is empty.",
            tripwire_triggered=True,
        )

    if len(message) > MAX_MESSAGE_LENGTH:
        return GuardrailFunctionOutput(
            output_info="The message exceeds 5000 characters.",
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info="Basic input validation passed.",
        tripwire_triggered=False,
    )