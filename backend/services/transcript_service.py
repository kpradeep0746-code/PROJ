import json
import re
import time
import urllib.request
from urllib.parse import parse_qs, urlparse
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

from services.ai_service import ask_gemini, get_video_metadata


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

    if len(url) == 11 and " " not in url:
        return url

    return None


def fetch_via_ytt_api(video_id: str):
    """Attempt fetching using youtube_transcript_api across all available languages."""
    # 1. Fetch direct with language preference
    try:
        ytt_api = YouTubeTranscriptApi()
        try:
            fetched = ytt_api.fetch(video_id, languages=["en", "en-US", "en-GB", "en-IN"])
        except Exception:
            fetched = ytt_api.fetch(video_id)

        if hasattr(fetched, "to_raw_data"):
            return fetched.to_raw_data()
        if hasattr(fetched, "snippets"):
            return [
                {
                    "start": getattr(s, "start", 0),
                    "text": getattr(s, "text", ""),
                    "duration": getattr(s, "duration", 0)
                }
                for s in fetched.snippets
            ]
        return fetched
    except Exception:
        pass

    # 2. List transcripts and fetch/translate first available
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        available = list(transcript_list)
        if available:
            # Prefer English or translate
            selected = available[0]
            try:
                for t in available:
                    if t.language_code.startswith("en"):
                        selected = t
                        break
            except Exception:
                pass
            fetched = selected.fetch()
            if hasattr(fetched, "to_raw_data"):
                return fetched.to_raw_data()
            if hasattr(fetched, "snippets"):
                return [
                    {
                        "start": getattr(s, "start", 0),
                        "text": getattr(s, "text", ""),
                        "duration": getattr(s, "duration", 0)
                    }
                    for s in fetched.snippets
                ]
            return fetched
    except Exception:
        pass

    # 3. Static fallback for older v0.6.x
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        try:
            return YouTubeTranscriptApi.get_transcript(video_id)
        except Exception:
            pass

    return None


def fetch_via_ytdlp(video_id: str):
    """Extract subtitles / auto-captions via yt-dlp."""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            captions_dict = info.get("subtitles") or {}
            auto_captions = info.get("automatic_captions") or {}

            sub_formats = None
            for lang in ["en", "en-US", "en-GB", "en-IN", "en-orig"]:
                if lang in captions_dict:
                    sub_formats = captions_dict[lang]
                    break
                if lang in auto_captions:
                    sub_formats = auto_captions[lang]
                    break

            if not sub_formats:
                if captions_dict:
                    sub_formats = next(iter(captions_dict.values()))
                elif auto_captions:
                    sub_formats = next(iter(auto_captions.values()))

            if not sub_formats:
                return None

            # Look for json3 track
            json3_track = next((s for s in sub_formats if s.get("ext") == "json3"), None)
            if json3_track and json3_track.get("url"):
                req = urllib.request.Request(
                    json3_track["url"],
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    events = data.get("events", [])
                    raw = []
                    for e in events:
                        segs = e.get("segs", [])
                        t = "".join(s.get("utf8", "") for s in segs).strip()
                        if t and t != "\n":
                            raw.append({
                                "start": e.get("tStartMs", 0) / 1000.0,
                                "duration": e.get("dDurationMs", 0) / 1000.0,
                                "text": t
                            })
                    if raw:
                        return raw

            # Look for vtt track
            vtt_track = next((s for s in sub_formats if s.get("ext") == "vtt"), None)
            if vtt_track and vtt_track.get("url"):
                req = urllib.request.Request(
                    vtt_track["url"],
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    vtt_text = resp.read().decode("utf-8")
                    lines = vtt_text.split("\n")
                    raw = []
                    for line in lines:
                        cleaned = re.sub(r"<[^>]+>", "", line).strip()
                        if cleaned and "-->" not in cleaned and not cleaned.isdigit() and not cleaned.startswith("WEBVTT"):
                            raw.append({
                                "start": 0,
                                "duration": 0,
                                "text": cleaned
                            })
                    if raw:
                        return raw
    except Exception:
        pass

    return None


def generate_ai_fallback_transcript(url: str, video_id: str):
    """When no subtitle track exists on YouTube, generate lecture breakdown via Gemini."""
    try:
        meta = get_video_metadata(url)
        title = meta.get("title", f"Video {video_id}")
        description = meta.get("description", "")
        channel = meta.get("channel", "")

        prompt = f"""You are a professional educational transcript generator.

A user has requested the transcript for this YouTube lecture video, but closed captions/subtitles are not enabled on this video.
Using the video title, description, and channel topic, generate a comprehensive, detailed, and structured lecture transcript and breakdown that covers the complete topic thoroughly.

Video Title: {title}
Channel: {channel}
Video Description: {description}

Rules:
- Write in clean, highly informative English.
- Break down into clear Markdown sections (### Section Title) with extensive explanations of the concepts.
- Provide practical explanations as if transcribing the lecture speaker.
- Return ONLY the formatted transcript text.
"""
        transcript = ask_gemini(prompt)
        if transcript and len(transcript.strip()) > 50:
            return {
                "success": True,
                "video_id": video_id,
                "transcript": transcript.strip(),
                "raw_transcript": [
                    {"start": 0, "duration": 30, "text": f"Introduction to {title}"},
                    {"start": 30, "duration": 60, "text": transcript[:300]}
                ],
                "is_ai_generated": True
            }
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

    # 1. Try youtube_transcript_api
    raw_data = fetch_via_ytt_api(video_id)

    # 2. Fallback to yt-dlp captions
    if not raw_data:
        raw_data = fetch_via_ytdlp(video_id)

    if raw_data:
        normalized = []
        for item in raw_data:
            if isinstance(item, dict):
                normalized.append({
                    "start": item.get("start", 0),
                    "duration": item.get("duration", 0),
                    "text": str(item.get("text", "")).strip()
                })
            else:
                normalized.append({
                    "start": getattr(item, "start", 0),
                    "duration": getattr(item, "duration", 0),
                    "text": str(getattr(item, "text", "")).strip()
                })

        full_text = " ".join(i["text"] for i in normalized if i["text"]).strip()
        if full_text:
            return {
                "success": True,
                "video_id": video_id,
                "transcript": full_text,
                "raw_transcript": normalized
            }

    # 3. Always succeed with AI Video Topic Generator fallback
    ai_result = generate_ai_fallback_transcript(url, video_id)
    if ai_result:
        return ai_result

    return {
        "success": False,
        "video_id": video_id,
        "message": "No captions found and unable to generate lecture content."
    }