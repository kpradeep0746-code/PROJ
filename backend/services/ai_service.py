import os
import json
from dotenv import load_dotenv
from google import genai
import yt_dlp

load_dotenv()


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY is missing. Add it in Render environment variables or .env.")
    return genai.Client(api_key=api_key)


def ask_gemini(prompt: str) -> str:
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text or ""


def ask_gemini_stream(prompt: str):
    client = get_gemini_client()
    response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text


def get_video_metadata(url: str):
    try:
        ydl_opts = {"skip_download": True, "quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", ""),
                "description": (info.get("description") or "")[:2000],
                "channel": info.get("uploader", "")
            }
    except Exception:
        return {}


def generate_summary(transcript: str, url: str = None):
    try:
        extra_ctx = ""
        if (not transcript or len(transcript.strip()) < 50) and url:
            meta = get_video_metadata(url)
            extra_ctx = f"Video URL: {url}\nTitle: {meta.get('title')}\nDescription: {meta.get('description')}\n"

        prompt = f"""
You are an expert study notes creator and lecture summarizer.

Create clear, concise, and structured study notes from the following YouTube lecture.

Rules:
- Use simple, easy-to-understand English.
- Use clear Markdown headings (## Topic, ### Key Points).
- Use bullet points for takeaways and core concepts.
- Highlight important definitions, formulas, or takeaways in bold.
- Keep it highly practical and useful for students.
- Do NOT repeat points or include filler content.

{extra_ctx}
Transcript / Content:
{transcript}
"""
        summary = ask_gemini(prompt)
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


def seconds_to_time(seconds):
    seconds = int(seconds)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def generate_timestamps(raw_transcript, url: str = None):
    try:
        transcript_with_time = ""
        if raw_transcript:
            for item in raw_transcript[:250]:
                start_time = int(item.get("start", 0))
                time_format = seconds_to_time(start_time)
                text = item.get("text", "")
                transcript_with_time += f"{time_format} - {text}\n"

        extra_ctx = ""
        if not transcript_with_time.strip() and url:
            meta = get_video_metadata(url)
            extra_ctx = f"Video URL: {url}\nTitle: {meta.get('title')}\nDescription: {meta.get('description')}\n"

        prompt = f"""
You are a YouTube lecture timestamp generator.

Create key topic-wise timestamps from this transcript or video info.

Rules:
- Group related content into meaningful lecture topics.
- Keep topic names concise, informative, and relevant (3-7 words each).
- Return strictly a valid JSON array of objects with "time" and "topic" keys.
- Do NOT include markdown code fences or any text outside the JSON array.

JSON Format:
[
  {{
    "time": "00:00",
    "topic": "Introduction and Overview"
  }}
]

{extra_ctx}
Transcript:
{transcript_with_time}
"""
        content = ask_gemini(prompt).strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        try:
            timestamps = json.loads(content)
        except Exception:
            timestamps = [{"time": "00:00", "topic": "Lecture Start"}]

        return {
            "success": True,
            "timestamps": timestamps
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


def translate_transcript(transcript: str, source_language: str, target_language: str):
    try:
        source_hint = (
            "The source language is auto-detected."
            if source_language.lower() in ("auto detect", "auto", "")
            else f"The source language is {source_language}."
        )

        prompt = f"""You are a professional language translator.

{source_hint}
Translate the following lecture content into {target_language}.

Rules:
- Translate faithfully without summarizing or omitting content.
- Preserve all paragraph breaks and Markdown formatting.
- If timestamps (e.g. 02:15) are present, keep them unchanged.
- Return ONLY the translated text without introductory or concluding remarks.

Text:
{transcript}
"""
        translated = ask_gemini(prompt)
        return {
            "success": True,
            "translated_transcript": translated,
            "translated_text": translated
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


def format_transcript_with_gemini(transcript: str, url: str = None):
    """Formats raw transcript text into structured Markdown."""
    try:
        extra_ctx = ""
        if (not transcript or len(transcript.strip()) < 50) and url:
            meta = get_video_metadata(url)
            extra_ctx = f"Video: {meta.get('title')}\n"

        prompt = f"""You are a professional lecture editor and formatter.

Format the following raw, unstructured YouTube transcript into a clear, readable, and well-structured Markdown document.

Rules:
- Preserve all spoken concepts, technical terms, and meaning. Do not summarize or remove content.
- Organize the continuous text into logical, readable paragraphs.
- Add proper punctuation, capitalization, and minor grammar fixes.
- Insert clean Markdown headings (e.g. ### Section Title) to structure the lecture topics.
- Return ONLY the formatted transcript text. Do not add intro/outro preamble or explanations.

{extra_ctx}
Transcript:
{transcript}
"""
        formatted = ask_gemini(prompt)
        return {
            "success": True,
            "transcript": formatted
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
