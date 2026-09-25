import json
import time
import urllib.request
from urllib.parse import parse_qs, urlparse
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

    if len(url) == 11 and " " not in url:
        return url

    return None


def fetch_via_ytt_api(video_id: str):
    """Attempt fetching using youtube_transcript_api."""
    try:
        ytt_api = YouTubeTranscriptApi()
        try:
            fetched = ytt_api.fetch(video_id, languages=["en", "en-US", "en-GB"])
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

    # Static fallback for v0.6.x
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
        except Exception:
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

            # Find best English or default caption track
            sub_formats = None
            for lang in ["en", "en-US", "en-GB", "en-orig"]:
                if lang in captions_dict:
                    sub_formats = captions_dict[lang]
                    break
                if lang in auto_captions:
                    sub_formats = auto_captions[lang]
                    break

            if not sub_formats:
                # Pick any available caption track
                if captions_dict:
                    sub_formats = next(iter(captions_dict.values()))
                elif auto_captions:
                    sub_formats = next(iter(auto_captions.values()))

            if not sub_formats:
                return None

            # Look for json3 or vtt
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

    return {
        "success": False,
        "video_id": video_id,
        "message": "No captions/transcripts found for this YouTube video."
    }