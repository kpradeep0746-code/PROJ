import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from services.transcript_service import get_transcript
from services.ai_service import generate_summary, generate_timestamps, translate_transcript, format_transcript_with_gemini


app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "YouTube Notes Maker Backend is running"
    })


@app.route("/api/transcript", methods=["POST"])
def transcript_api():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(data["url"])

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result)

    # Use Gemini API to format and structure the transcript
    formatted_result = format_transcript_with_gemini(transcript_result["transcript"])

    if formatted_result.get("success") is True:
        return jsonify({
            "success": True,
            "video_id": transcript_result.get("video_id"),
            "transcript": formatted_result.get("transcript")
        })
    else:
        # Fallback to raw transcript if Gemini formatting fails
        return jsonify({
            "success": True,
            "video_id": transcript_result.get("video_id"),
            "transcript": transcript_result.get("transcript")
        })


@app.route("/api/summary", methods=["POST"])
def summary_api():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(data["url"])

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result)

    summary_result = generate_summary(transcript_result["transcript"])

    if summary_result.get("success") is not True:
        return jsonify({
            "success": False,
            "video_id": transcript_result.get("video_id"),
            "message": summary_result.get("message")
        })

    return jsonify({
        "success": True,
        "video_id": transcript_result.get("video_id"),
        "summary": summary_result.get("summary")
    })


@app.route("/api/timestamps", methods=["POST"])
def timestamps_api():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(data["url"])

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result)

    timestamp_result = generate_timestamps(transcript_result["raw_transcript"])

    if timestamp_result.get("success") is not True:
        return jsonify({
            "success": False,
            "video_id": transcript_result.get("video_id"),
            "message": timestamp_result.get("message")
        })

    return jsonify({
        "success": True,
        "video_id": transcript_result.get("video_id"),
        "timestamps": timestamp_result.get("timestamps")
    })


@app.route("/api/analyze", methods=["POST"])
def analyze_api():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(data["url"])

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result)

    summary_result = generate_summary(transcript_result["transcript"])
    timestamp_result = generate_timestamps(transcript_result["raw_transcript"])

    return jsonify({
        "success": summary_result.get("success") is True and timestamp_result.get("success") is True,
        "video_id": transcript_result.get("video_id"),

        "summary": summary_result.get("summary"),
        "timestamps": timestamp_result.get("timestamps"),

        "summary_error": summary_result.get("message"),
        "timestamps_error": timestamp_result.get("message")
    })


@app.route("/api/translate", methods=["POST"])
def translate_api():
    """
    POST /api/translate
    Body: {
        "transcript": "...",
        "source_language": "English",   # optional, defaults to Auto Detect
        "target_language": "Telugu"      # required
    }
    Response: { "success": bool, "translated_transcript": str }
    """
    data = request.get_json()

    if not data or "transcript" not in data:
        return jsonify({
            "success": False,
            "message": "'transcript' field is required"
        }), 400

    if "target_language" not in data or not data["target_language"].strip():
        return jsonify({
            "success": False,
            "message": "'target_language' field is required"
        }), 400

    transcript = data["transcript"]
    source_language = data.get("source_language", "Auto Detect")
    target_language = data["target_language"]

    result = translate_transcript(transcript, source_language, target_language)

    if result.get("success") is not True:
        return jsonify({
            "success": False,
            "message": result.get("message", "Translation failed")
        }), 500

    return jsonify({
        "success": True,
        "translated_transcript": result.get("translated_transcript")
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        debug=False,
        host="0.0.0.0",
        port=port
    )