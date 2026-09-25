import time
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    parsed_url = urlparse(url)

    if "youtu.be" in parsed_url.netloc:
        return parsed_url.path.strip("/").split("?")[0]

    if "youtube.com" in parsed_url.netloc:
        query = parse_qs(parsed_url.query)
        if "v" in query:
            return query["v"][0]
        if "/shorts/" in parsed_url.path:
            return parsed_url.path.split("/shorts/")[1].split("/")[0]
        if "/embed/" in parsed_url.path:
            return parsed_url.path.split("/embed/")[1].split("/")[0]
        if "/live/" in parsed_url.path:
            return parsed_url.path.split("/live/")[1].split("/")[0]

    # If already an 11-char video ID
    if len(url) == 11 and " " not in url:
        return url

    return None


def fetch_raw_transcript(video_id: str):
    """Fetch raw transcript segments using youtube_transcript_api."""
    # 1. Instance method: fetch with languages (v1.x)
    try:
        ytt_api = YouTubeTranscriptApi()
        if hasattr(ytt_api, "fetch"):
            try:
                fetched = ytt_api.fetch(video_id, languages=["en", "en-US", "en-GB"])
            except Exception:
                fetched = ytt_api.fetch(video_id)
            if hasattr(fetched, "to_raw_data"):
                return fetched.to_raw_data()
            if hasattr(fetched, "snippets"):
                return [
                    {"start": getattr(s, "start", 0), "text": getattr(s, "text", ""), "duration": getattr(s, "duration", 0)}
                    for s in fetched.snippets
                ]
            return fetched
    except Exception:
        pass

    # 2. Static method (v0.6.x)
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
        except Exception:
            try:
                return YouTubeTranscriptApi.get_transcript(video_id)
            except Exception:
                pass

    # 3. Instance method without params fallback
    try:
        ytt = YouTubeTranscriptApi()
        if hasattr(ytt, "fetch"):
            fetched = ytt.fetch(video_id)
            if hasattr(fetched, "to_raw_data"):
                return fetched.to_raw_data()
            return fetched
    except Exception:
        pass

    return None


def get_transcript(url: str):
    video_id = extract_video_id(url)
    if not video_id:
        return {
            "success": False,
            "message": "Invalid YouTube URL provided."
        }

    last_error = None
    for attempt in range(2):
        try:
            raw_data = fetch_raw_transcript(video_id)
            if raw_data:
                # Normalize raw_data into list of dicts with 'text' and 'start'
                normalized = []
                for item in raw_data:
                    if isinstance(item, dict):
                        normalized.append({
                            "start": item.get("start", 0),
                            "duration": item.get("duration", 0),
                            "text": str(item.get("text", "")).strip()
                        })
                    else:
                        start = getattr(item, "start", 0)
                        text = getattr(item, "text", "")
                        dur = getattr(item, "duration", 0)
                        normalized.append({
                            "start": start,
                            "duration": dur,
                            "text": str(text).strip()
                        })

                full_text = " ".join(item["text"] for item in normalized if item["text"]).strip()

                if full_text:
                    return {
                        "success": True,
                        "video_id": video_id,
                        "transcript": full_text,
                        "raw_transcript": normalized
                    }
        except Exception as e:
            last_error = str(e)
            if attempt < 1:
                time.sleep(1)

    return {
        "success": False,
        "video_id": video_id,
        "message": f"Could not retrieve transcript for this video. {last_error or 'No English or auto-generated captions are available for this video.'}"
    }