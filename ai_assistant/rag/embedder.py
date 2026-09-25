import logging
from typing import List
import httpx
from config import settings

logger = logging.getLogger(__name__)


async def get_embedding(text: str) -> List[float]:
    """Generates an embedding vector using local Ollama embeddings service."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={
                    "model": settings.embedding_model,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            result = response.json()
            embedding = result.get("embedding", [])
            if embedding:
                return list(embedding)
            raise ValueError("No embedding returned in response")
    except Exception as e:
        logger.error(f"Failed to generate embedding via Ollama: {str(e)}")
        return [0.0] * 768
