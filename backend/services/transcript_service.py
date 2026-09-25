import time
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp


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

    # If already a 11-char video ID
    if len(url) == 11 and " " not in url:
        return url

    return None


def fetch_via_ytt_api(video_id: str):
    """Try fetching transcript using youtube_transcript_api (compatible with v0.6+ and v1.0+)."""
    # 1. New v1.x class instance approach
    try:
        ytt_api = YouTubeTranscriptApi()
        if hasattr(ytt_api, "list"):
            transcript_list = ytt_api.list(video_id)
            try:
                transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
            except Exception:
                available = list(transcript_list)
                if not available:
                    raise Exception("No transcript found in list.")
                transcript = available[0]
                try:
                    transcript = transcript.translate("en")
                except Exception:
                    pass
            fetched = transcript.fetch()
            if hasattr(fetched, "to_raw_data"):
                return fetched.to_raw_data()
            return fetched
    except Exception:
        pass

    # 2. Classic static method approach (v0.6.x)
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
        except Exception:
            if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                available = list(transcript_list)
                if available:
                    transcript = available[0]
                    try:
                        transcript = transcript.translate("en")
                    except Exception:
                        pass
                    return transcript.fetch()

    # 3. Instance fetch fallback
    try:
        ytt_api = YouTubeTranscriptApi()
        if hasattr(ytt_api, "fetch"):
            fetched = ytt_api.fetch(video_id)
            if hasattr(fetched, "to_raw_data"):
                return fetched.to_raw_data()
            return fetched
    except Exception:
        pass

    return None


def fetch_via_ytdlp(video_id: str):
    """Fallback: fetch automatic captions or subtitles using yt-dlp."""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en.*", "en"],
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subs = info.get("subtitles") or info.get("automatic_captions")
            if subs:
                for lang_key in subs:
                    if lang_key.startswith("en"):
                        # Captions exist
                        return None
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
    for attempt in range(3):
        try:
            raw_transcript = fetch_via_ytt_api(video_id)
            if raw_transcript:
                transcript_text = " ".join(item.get("text", "") for item in raw_transcript)
                if transcript_text.strip():
                    return {
                        "success": True,
                        "video_id": video_id,
                        "transcript": transcript_text.strip(),
                        "raw_transcript": raw_transcript
                    }
        except Exception as e:
            last_error = str(e)
            if attempt < 2:
                time.sleep(1)

    return {
        "success": False,
        "video_id": video_id,
        "message": f"Could not retrieve transcript for this video. Details: {last_error or 'No subtitles found or video is restricted.'}"
    }