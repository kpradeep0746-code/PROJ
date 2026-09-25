import logging
import json
from typing import AsyncGenerator
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ai.prompt_builder import build_prompt
from ai.memory import add_message
from ai.response_formatter import format_response
from config import settings

logger = logging.getLogger(__name__)


async def generate_response(
    db: AsyncSession, student_id: str, lecture_id: str, question: str
) -> str:
    """Generates an answer using local Ollama REST API and saves the conversation."""
    if not question or not question.strip():
        return "Please ask a valid question."

    try:
        messages = await build_prompt(db, student_id, lecture_id, question)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            result = response.json()
            answer = result.get("message", {}).get("content", "")

        answer = format_response(answer)

        await add_message(db, student_id, "user", question)
        await add_message(db, student_id, "assistant", answer)

        return answer

    except Exception as e:
        logger.error(f"Error in generate_response: {str(e)}", exc_info=True)
        return (
            "I'm sorry, I'm having trouble connecting to the local AI engine. "
            "Please ensure Ollama is running and the model is pulled."
        )


async def generate_response_stream(
    db: AsyncSession, student_id: str, lecture_id: str, question: str
) -> AsyncGenerator[str, None]:
    """Generates streaming tokens using local Ollama REST API and saves conversation context on completion."""
    if not question or not question.strip():
        yield "Please ask a valid question."
        return

    try:
        messages = await build_prompt(db, student_id, lecture_id, question)

        full_response_parts = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            full_response_parts.append(content)
                            yield content
                    except json.JSONDecodeError:
                        continue

        full_answer = "".join(full_response_parts)
        full_answer = format_response(full_answer)

        await add_message(db, student_id, "user", question)
        await add_message(db, student_id, "assistant", full_answer)

    except Exception as e:
        logger.error(f"Error in generate_response_stream: {str(e)}", exc_info=True)
        yield (
            "\n[Connection Error]: Failed to stream from local Ollama service. "
            "Please ensure Ollama is running at the configured address."
        )
