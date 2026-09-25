from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import time


def extract_video_id(url):
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

    return None


def get_transcript(url):
    video_id = extract_video_id(url)

    if not video_id:
        return {
            "success": False,
            "message": "Invalid YouTube URL"
        }

    for attempt in range(3):
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)
            
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            except Exception:
                available = list(transcript_list)
                if not available:
                    raise Exception("No transcript available for this video.")
                transcript = available[0]
                try:
                    transcript = transcript.translate('en')
                except Exception:
                    pass

            fetched_transcript = transcript.fetch()
            raw_transcript = fetched_transcript.to_raw_data()

            transcript_text = ""

            for item in raw_transcript:
                transcript_text += item["text"] + " "

            return {
                "success": True,
                "video_id": video_id,
                "transcript": transcript_text,
                "raw_transcript": raw_transcript
            }

        except Exception as e:
            error_message = str(e)

            if attempt < 2:
                time.sleep(2)
                continue

            return {
                "success": False,
                "message": error_message
            }