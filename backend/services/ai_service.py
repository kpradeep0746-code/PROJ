import os
import json
import re
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODELS_LIST = [
    "gemini-flash-lite-latest",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-2.5-flash"
]


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise Exception("GEMINI_API_KEY is missing. Add it in .env file or environment variables.")

    return genai.Client(api_key=api_key)


def ask_gemini(prompt):
    client = get_gemini_client()
    last_err = None

    for model_name in MODELS_LIST:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            time.sleep(1)
            continue

    raise last_err if last_err else Exception("All Gemini models failed to respond.")


def generate_summary(transcript):
    try:
        if not transcript or not transcript.strip():
            return {
                "success": False,
                "message": "Transcript is empty. Cannot generate summary."
            }

        # Truncate if extreme length (>40k chars) to avoid timeout
        processed_transcript = transcript[:45000]

        prompt = f"""
You are an expert study notes creator.

Create clear, well-structured lecture study notes from the following YouTube lecture transcript.

Rules:
- Use simple and precise English
- Use clear Markdown headings (## Topic, ### Key Concept)
- Use bullet points for key takeaways
- Highlight definitions and core ideas in bold
- Keep it practical and valuable for students
- Do not repeat points

Transcript:
{processed_transcript}
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


def generate_timestamps(raw_transcript):
    try:
        if not raw_transcript:
            return {
                "success": False,
                "message": "No transcript data available for timestamps."
            }

        # Sample raw_transcript if too large (step every 20-30s)
        items_to_use = raw_transcript
        if len(raw_transcript) > 180:
            step = max(1, len(raw_transcript) // 120)
            items_to_use = raw_transcript[::step]

        transcript_with_time = ""
        for item in items_to_use:
            start_time = int(item.get("start", 0))
            time_format = seconds_to_time(start_time)
            text = item.get("text", "").strip()
            if text:
                transcript_with_time += f"{time_format} - {text}\n"

        prompt = f"""
You are a YouTube lecture timestamp generator.

Create topic-wise timestamps from this transcript timeline.

Rules:
- Group related content into 8 to 15 meaningful topics
- Use the actual timestamp numbers given
- Keep topic names concise and clear (3 to 7 words)
- Output ONLY a valid JSON array of objects with "time" and "topic" keys
- Do NOT output markdown code fences or any conversational text

JSON Format:
[
  {{
    "time": "00:00",
    "topic": "Introduction to the Topic"
  }}
]

Transcript Timeline:
{transcript_with_time[:35000]}
"""

        content = ask_gemini(prompt).strip()

        # Clean code fences if present
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        # Parse JSON
        timestamps = None
        match = re.search(r"\[\s*\{.*?\}\s*\]", content, re.DOTALL)
        if match:
            try:
                timestamps = json.loads(match.group(0))
            except Exception:
                pass

        if not timestamps:
            try:
                timestamps = json.loads(content)
            except Exception:
                # Text fallback parser
                extracted = []
                for line in content.split("\n"):
                    m = re.match(r"^[\*\-\s]*(\d{1,2}:\d{2})\s*[-–:]\s*(.+)", line.strip())
                    if m:
                        extracted.append({"time": m.group(1), "topic": m.group(2).strip()})
                timestamps = extracted if extracted else [{"time": "00:00", "topic": "Lecture Start"}]

        return {
            "success": True,
            "timestamps": timestamps
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


def translate_transcript(transcript, source_language, target_language):
    """
    Translate transcript text using Gemini.
    """
    try:
        source_hint = (
            "The source language is auto-detected."
            if source_language.lower() in ("auto detect", "auto", "")
            else f"The source language is {source_language}."
        )

        prompt = f"""You are a professional language translator.

{source_hint}
Translate the following transcript into {target_language}.

Rules:
- Translate ONLY — do not summarise, skip, or add any content.
- Preserve every paragraph break and blank line exactly as in the original.
- If the text contains timestamps in the format MM:SS or HH:MM:SS, keep them UNCHANGED.
- Do not add translator notes or disclaimers.
- Return only the translated text, nothing else.

Transcript:
{transcript[:35000]}
"""

        translated = ask_gemini(prompt)

        return {
            "success": True,
            "translated_transcript": translated
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


def format_transcript_with_gemini(transcript):
    """
    Formats raw YouTube transcript text into structured Markdown using Gemini API.
    """
    try:
        prompt = f"""You are a professional lecture editor and formatter.

Format the following raw, unstructured YouTube transcript into a clear, readable, and well-structured Markdown document.

Rules:
- Preserve all spoken concepts, technical terms, and meaning. Do not summarize or skip content.
- Organize the continuous text into logical, readable paragraphs.
- Add proper punctuation, capitalization, and minor grammar fixes.
- Insert clean Markdown headings (e.g. ### Section Title) to structure the lecture topics.
- Return ONLY the formatted transcript text. Do not add intro/outro preamble or explanations.

Transcript:
{transcript[:35000]}
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
