from flask import Flask, request, jsonify
from flask_cors import CORS

from services.transcript_service import get_transcript
from services.ai_service import generate_summary, generate_timestamps


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
        return jsonify(transcript_result), 500

    return jsonify(transcript_result)


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
        return jsonify(transcript_result), 500

    summary_result = generate_summary(transcript_result["transcript"])

    if summary_result.get("success") is not True:
        return jsonify({
            "success": False,
            "video_id": transcript_result.get("video_id"),
            "message": summary_result.get("message")
        }), 500

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
        return jsonify(transcript_result), 500

    timestamp_result = generate_timestamps(transcript_result["raw_transcript"])

    if timestamp_result.get("success") is not True:
        return jsonify({
            "success": False,
            "video_id": transcript_result.get("video_id"),
            "message": timestamp_result.get("message")
        }), 500

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
        return jsonify(transcript_result), 500

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


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )