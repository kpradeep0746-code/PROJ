import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise Exception("GEMINI_API_KEY is missing. Add it in .env file.")

    return genai.Client(api_key=api_key)


def ask_gemini(prompt):
    client = get_gemini_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


def generate_summary(transcript):
    try:
        prompt = f"""
You are a study notes maker.

Create clear and simple lecture notes from this YouTube transcript.

Rules:
- Use simple English
- Use headings
- Use bullet points
- Keep it useful for students
- Do not add unnecessary information
- Do not repeat points

Transcript:
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


def generate_timestamps(raw_transcript):
    try:
        transcript_with_time = ""

        for item in raw_transcript:
            start_time = int(item["start"])
            time_format = seconds_to_time(start_time)
            text = item["text"]

            transcript_with_time += f"{time_format} - {text}\n"

        prompt = f"""
You are a YouTube lecture timestamp generator.

Create topic-wise timestamps from this transcript.

Rules:
- Use only the given timestamps
- Do not create fake timestamps
- Group related content into useful topics
- Keep topic names short and clear
- Return only valid JSON
- Do not include explanation outside JSON

JSON format:
[
  {{
    "time": "00:00",
    "topic": "Introduction"
  }}
]

Transcript:
{transcript_with_time}
"""

        content = ask_gemini(prompt)

        content = content.strip()

        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        try:
            timestamps = json.loads(content)
        except:
            timestamps = content

        return {
            "success": True,
            "timestamps": timestamps
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }