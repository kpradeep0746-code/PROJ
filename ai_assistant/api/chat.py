from fastapi import APIRouter, Depends, HTTPException
import logging
import hashlib
import httpx
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from models.chat_model import ChatRequest
from models.chat_model import ChatResponse
from ai.ai_engine import generate_response, generate_response_stream
from api.deps import get_async_db
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cache for translations
# Key: hashlib.md5(f"{target_lang}:{text}").hexdigest()
# Value: translated_text
translation_cache = {}


class TranslateRequest(BaseModel):
    text: str
    target_lang: str  # "English" or "Telugu"


class TranslateResponse(BaseModel):
    success: bool
    translated_text: str
    message: str = ""


async def translate_text(text: str, target_lang: str) -> str:
    lang_code = "te" if target_lang.lower() == "telugu" else "en"
    cache_key = hashlib.md5(f"{lang_code}:{text}".encode("utf-8")).hexdigest()
    
    if cache_key in translation_cache:
        logger.info("Translation cache hit")
        return translation_cache[cache_key]

    # Split text into chunks to avoid Google API URL/body length limits
    chunks = []
    current_chunk = []
    current_len = 0
    for line in text.split("\n"):
        if current_len + len(line) > 2000:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_len = len(line)
        else:
            current_chunk.append(line)
            current_len += len(line) + 1
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    translated_chunks = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for chunk in chunks:
                if not chunk.strip():
                    translated_chunks.append(chunk)
                    continue
                response = await client.post(
                    "https://translate.googleapis.com/translate_a/single",
                    params={
                        "client": "gtx",
                        "sl": "auto",
                        "tl": lang_code,
                        "dt": "t"
                    },
                    data={"q": chunk}
                )
                response.raise_for_status()
                result = response.json()
                translated_chunk = ""
                if result and len(result) > 0 and result[0]:
                    for segment in result[0]:
                        if segment and len(segment) > 0:
                            translated_chunk += segment[0]
                translated_chunks.append(translated_chunk)
        
        final_translation = "\n".join(translated_chunks)
        translation_cache[cache_key] = final_translation
        return final_translation

    except Exception as e:
        logger.error(f"Google Translate failed, falling back to local Ollama translation: {str(e)}")
        try:
            prompt = (
                f"Translate the following text into {target_lang}. "
                f"Preserve the original formatting, paragraph breaks, and markdown structure. "
                f"Do not add any preamble, explanations, notes, or concluding remarks—output ONLY the translation:\n\n{text}"
            )
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/chat",
                    json={
                        "model": settings.llm_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "stream": False,
                    },
                )
                response.raise_for_status()
                result = response.json()
                translated_text = result.get("message", {}).get("content", "")
                if translated_text:
                    final_translation = translated_text.strip()
                    translation_cache[cache_key] = final_translation
                    return final_translation
        except Exception as oe:
            logger.error(f"Ollama fallback translation also failed: {str(oe)}")

        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: Google Translate offline and Ollama failed. Original: {str(e)}"
        )


@router.post("/api/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """Translates text between English and Telugu, utilizing a cache and offline/online fallback."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text to translate cannot be empty.")
    
    if request.target_lang not in ["English", "Telugu"]:
        raise HTTPException(status_code=400, detail="Only 'English' and 'Telugu' target languages are supported.")

    try:
        translated = await translate_text(request.text, request.target_lang)
        return TranslateResponse(success=True, translated_text=translated)
    except Exception as e:
        return TranslateResponse(success=False, translated_text="", message=str(e))


@router.post("/ask", response_model=ChatResponse)
async def ask(request: ChatRequest, db: AsyncSession = Depends(get_async_db)):
    """Handles the standard synchronous question-answering API. Fully backward compatible."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    answer = await generate_response(
        db,
        request.student_id,
        request.lecture_id,
        request.question
    )

    return ChatResponse(answer=answer)


@router.post("/ask/stream")
async def ask_stream(request: ChatRequest, db: AsyncSession = Depends(get_async_db)):
    """Handles the streaming question-answering API using Server-Sent Events (SSE)."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    async def event_generator():
        async for token in generate_response_stream(
            db=db,
            student_id=request.student_id,
            lecture_id=request.lecture_id,
            question=request.question
        ):
            yield {"data": token}

    return EventSourceResponse(event_generator())
