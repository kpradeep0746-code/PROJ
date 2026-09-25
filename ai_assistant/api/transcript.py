import os
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
from rag.lecture_manager import extract_youtube_video_id
from youtube_transcript_api import YouTubeTranscriptApi
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class TranscriptRequest(BaseModel):
    url: str


class TranscriptResponse(BaseModel):
    success: bool
    transcript: str = ""
    video_id: str = ""
    message: str = ""
    warning: str = ""



@router.post("/api/transcript", response_model=TranscriptResponse)
async def get_youtube_transcript(request: TranscriptRequest):
    """Fetches YouTube transcripts dynamically using youtube-transcript-api."""
    video_id = extract_youtube_video_id(request.url)
    if not video_id:
        return TranscriptResponse(success=False, message="Invalid YouTube URL or Video ID.")

    try:
        transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=['en', 'te', 'hi'])
        full_text = " ".join([chunk.text for chunk in transcript_list])
        return TranscriptResponse(success=True, video_id=video_id, transcript=full_text)
    except Exception as e:
        logger.error(f"Error fetching transcript for video {video_id}: {str(e)}")
        return TranscriptResponse(
            success=False,
            message=f"Failed to load transcript for video {video_id}: {str(e)}"
        )


def format_transcript_with_gemini_sync(api_key: str, transcript: str) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""You are a professional lecture editor and formatter.

Format the following raw, unstructured YouTube transcript into a clear, readable, and well-structured Markdown document.

Rules:
- Preserve all spoken concepts, technical terms, and meaning. Do not summarize or skip content.
- Organize the continuous text into logical, readable paragraphs.
- Add proper punctuation, capitalization, and minor grammar fixes.
- Insert clean Markdown headings (e.g. ### Section Title) to structure the lecture topics.
- Return ONLY the formatted transcript text. Do not add intro/outro preamble or explanations.

Transcript:
{transcript}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


async def format_transcript_with_gemini(transcript: str) -> str:
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY is missing. Add it in .env file.")
    
    loop = asyncio.get_running_loop()
    formatted = await loop.run_in_executor(
        None, format_transcript_with_gemini_sync, api_key, transcript
    )
    return formatted


@router.post("/api/transcript/formatted", response_model=TranscriptResponse)
async def get_formatted_transcript(request: TranscriptRequest):
    """Fetches YouTube transcripts dynamically and structures them using Gemini."""
    video_id = extract_youtube_video_id(request.url)
    if not video_id:
        return TranscriptResponse(success=False, message="Invalid YouTube URL or Video ID.")

    try:
        transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=['en', 'te', 'hi'])
        full_text = " ".join([chunk.text for chunk in transcript_list])
    except Exception as e:
        logger.error(f"Error fetching transcript for video {video_id}: {str(e)}")
        return TranscriptResponse(
            success=False,
            message=f"Failed to load transcript for video {video_id}: {str(e)}"
        )

    try:
        formatted = await format_transcript_with_gemini(full_text)
        return TranscriptResponse(success=True, video_id=video_id, transcript=formatted)
    except Exception as e:
        logger.error(f"Error formatting transcript for video {video_id} with Gemini: {str(e)}")
        # Graceful fallback to raw transcript with warning
        return TranscriptResponse(
            success=True,
            video_id=video_id,
            transcript=full_text,
            warning=f"Gemini formatting failed. Showing raw transcript. Error: {str(e)}"
        )


