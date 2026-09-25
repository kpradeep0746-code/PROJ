import logging
import re
import httpx
from urllib.parse import urlparse, parse_qs
from rag.vector_store import vector_store
from rag.chunker import chunk_text
from rag.embedder import get_embedding
from lecture.lecture_manager import load_lecture
from config import settings

logger = logging.getLogger(__name__)


def extract_youtube_video_id(url_or_id: str) -> str | None:
    """Extracts the 11-character YouTube video ID from a URL or checks if it's already a video ID."""
    if not url_or_id:
        return None
    trimmed = url_or_id.strip()
    
    # 11-char plain video ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", trimmed):
        return trimmed

    # Try extracting using standard patterns
    patterns = [
        r"(?:watch\?v=|/videos/|/embed/|/shorts/|/live/|youtu\.be/)([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, trimmed)
        if match:
            return match.group(1)
            
    # Fallback to query parameters
    try:
        parsed_url = urlparse(trimmed)
        if parsed_url.netloc and ("youtube.com" in parsed_url.netloc or "youtu.be" in parsed_url.netloc):
            query = parse_qs(parsed_url.query)
            if "v" in query:
                return query["v"][0]
    except Exception:
        pass
        
    return None


async def ensure_lecture_indexed(lecture_id: str) -> bool:
    """Checks if lecture or YouTube transcript is indexed, otherwise fetches and indexes it."""
    if not lecture_id:
        return False

    video_id = extract_youtube_video_id(lecture_id)
    index_id = video_id if video_id else lecture_id

    if vector_store.is_lecture_indexed(index_id):
        logger.info(f"Lecture/Video '{index_id}' is already indexed.")
        return True

    logger.info(f"Indexing lecture/video '{index_id}'...")
    raw_content = None

    if video_id:
        # Construct the YouTube URL if only video_id was passed
        video_url = lecture_id if lecture_id.startswith("http") else f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            backend_url = settings.backend_url
            logger.info(f"Fetching transcript from Flask backend: {backend_url}/api/transcript for video {video_id}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{backend_url}/api/transcript",
                    json={"url": video_url}
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") and "transcript" in result:
                        raw_content = result["transcript"]
                        logger.info(f"Successfully obtained transcript from backend for {video_id}")
                    else:
                        logger.warning(f"Backend returned unsuccessful transcript result for {video_id}: {result.get('message')}")
                else:
                    logger.error(f"Flask backend returned status code {response.status_code} for {video_id}")
        except Exception as e:
            logger.error(f"Exception while contacting Flask backend for video {video_id}: {str(e)}")
    else:
        # Traditional local text file lecture
        raw_content = load_lecture(lecture_id)
    
    if not raw_content:
        logger.warning(f"No content available to index for: {lecture_id}")
        return False

    chunks = chunk_text(raw_content)
    if not chunks:
        logger.warning(f"No valid chunks generated for: {lecture_id}")
        return False

    try:
        embeddings = []
        for chunk in chunks:
            emb = await get_embedding(chunk)
            embeddings.append(emb)

        vector_store.add_lecture_chunks(index_id, chunks, embeddings)
        logger.info(f"Successfully indexed {len(chunks)} chunks for '{index_id}'.")
        return True

    except Exception as e:
        logger.error(f"Error during indexing of '{index_id}': {str(e)}")
        return False
