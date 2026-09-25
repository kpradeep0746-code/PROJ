import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

from services.transcript_service import get_transcript
from services.ai_service import (
    generate_summary,
    generate_timestamps,
    translate_transcript,
    format_transcript_with_gemini,
    ask_gemini,
    ask_gemini_stream
)

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "notes.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ── Health Check ─────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "YouTube Notes Maker Backend is running",
        "status": "healthy"
    })


# ── Transcripts ──────────────────────────────────────────────────────────────
@app.route("/api/transcript", methods=["POST"])
@app.route("/api/transcript/formatted", methods=["POST"])
def transcript_api():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(url)

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result), 200

    # Format transcript with Gemini for structured markdown
    formatted_result = format_transcript_with_gemini(transcript_result["transcript"])

    final_transcript = (
        formatted_result.get("transcript")
        if formatted_result.get("success")
        else transcript_result.get("transcript")
    )

    return jsonify({
        "success": True,
        "video_id": transcript_result.get("video_id"),
        "transcript": final_transcript
    })


# ── Summarization ────────────────────────────────────────────────────────────
@app.route("/api/summary", methods=["POST"])
def summary_api():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(url)

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result), 200

    summary_result = generate_summary(transcript_result["transcript"])

    if summary_result.get("success") is not True:
        return jsonify({
            "success": False,
            "video_id": transcript_result.get("video_id"),
            "message": summary_result.get("message")
        }), 200

    return jsonify({
        "success": True,
        "video_id": transcript_result.get("video_id"),
        "summary": summary_result.get("summary")
    })


# ── Timestamps ───────────────────────────────────────────────────────────────
@app.route("/api/timestamps", methods=["POST"])
def timestamps_api():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(url)

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result), 200

    timestamp_result = generate_timestamps(transcript_result.get("raw_transcript", []))

    if timestamp_result.get("success") is not True:
        return jsonify({
            "success": False,
            "video_id": transcript_result.get("video_id"),
            "message": timestamp_result.get("message")
        }), 200

    return jsonify({
        "success": True,
        "video_id": transcript_result.get("video_id"),
        "timestamps": timestamp_result.get("timestamps")
    })


# ── Analyze (Summary + Timestamps) ───────────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
def analyze_api():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({
            "success": False,
            "message": "YouTube URL is required"
        }), 400

    transcript_result = get_transcript(url)

    if transcript_result.get("success") is not True:
        return jsonify(transcript_result), 200

    summary_result = generate_summary(transcript_result["transcript"])
    timestamp_result = generate_timestamps(transcript_result.get("raw_transcript", []))

    return jsonify({
        "success": summary_result.get("success") is True and timestamp_result.get("success") is True,
        "video_id": transcript_result.get("video_id"),
        "summary": summary_result.get("summary"),
        "timestamps": timestamp_result.get("timestamps"),
        "summary_error": summary_result.get("message"),
        "timestamps_error": timestamp_result.get("message")
    })


# ── Translation ──────────────────────────────────────────────────────────────
@app.route("/api/translate", methods=["POST"])
def translate_api():
    data = request.get_json() or {}
    text = data.get("transcript") or data.get("text")
    source_language = data.get("source_language", "Auto Detect")
    target_language = data.get("target_language") or data.get("target_lang", "English")

    if not text or not text.strip():
        return jsonify({
            "success": False,
            "message": "'transcript' or 'text' field is required"
        }), 400

    result = translate_transcript(text, source_language, target_language)

    if result.get("success") is not True:
        return jsonify({
            "success": False,
            "message": result.get("message", "Translation failed")
        }), 500

    return jsonify(result)


# ── Chatbot & Question Answering ─────────────────────────────────────────────
@app.route("/ask", methods=["POST"])
def ask_api():
    data = request.get_json() or {}
    question = data.get("question")
    lecture_id = data.get("lecture_id") or data.get("video_url")

    if not question:
        return jsonify({"answer": "Please provide a question."}), 400

    context = ""
    if lecture_id and ("youtube.com" in lecture_id or "youtu.be" in lecture_id):
        t_res = get_transcript(lecture_id)
        if t_res.get("success"):
            context = f"\n\nVideo Transcript Context:\n{t_res['transcript'][:15000]}"

    prompt = f"""You are NOA, a friendly and intelligent AI study assistant.
Answer the student's question accurately and helpfully using the provided lecture context if available.

{context}

Student Question:
{question}
"""
    try:
        answer = ask_gemini(prompt)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"Error generating answer: {str(e)}"}), 500


@app.route("/ask/stream", methods=["POST"])
def ask_stream_api():
    data = request.get_json() or {}
    question = data.get("question")
    lecture_id = data.get("lecture_id") or data.get("video_url")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    context = ""
    if lecture_id and ("youtube.com" in lecture_id or "youtu.be" in lecture_id):
        t_res = get_transcript(lecture_id)
        if t_res.get("success"):
            context = f"\n\nVideo Transcript Context:\n{t_res['transcript'][:15000]}"

    prompt = f"""You are NOA, a helpful and knowledgeable AI study assistant.
Answer the student's question clearly, in concise Markdown.

{context}

Student Question:
{question}
"""
    def generate():
        try:
            for token in ask_gemini_stream(prompt):
                yield f"data:{token}\n\n"
        except Exception as e:
            yield f"data:Error: {str(e)}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# ── Personal Notes API (SQLite) ──────────────────────────────────────────────
@app.route("/api/notes", methods=["GET"])
def get_notes_api():
    student_id = request.args.get("student_id", "")
    query = request.args.get("q", "").strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if query:
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT id, student_id, title, content, created_at, updated_at
            FROM personal_notes
            WHERE student_id = ? AND (title LIKE ? OR content LIKE ?)
            ORDER BY updated_at DESC
        """, (student_id, search_term, search_term))
    else:
        cursor.execute("""
            SELECT id, student_id, title, content, created_at, updated_at
            FROM personal_notes
            WHERE student_id = ?
            ORDER BY updated_at DESC
        """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    notes = [
        {
            "id": r[0],
            "student_id": r[1],
            "title": r[2],
            "content": r[3],
            "created_at": r[4],
            "updated_at": r[5]
        }
        for r in rows
    ]
    return jsonify(notes)


@app.route("/api/notes", methods=["POST"])
def create_note_api():
    data = request.get_json() or {}
    student_id = data.get("student_id", "student_user")
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return jsonify({"message": "Title and content are required"}), 400

    now_iso = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO personal_notes (student_id, title, content, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, title, content, now_iso, now_iso))
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "id": note_id,
        "student_id": student_id,
        "title": title,
        "content": content,
        "created_at": now_iso,
        "updated_at": now_iso
    }), 201


@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note_api(note_id):
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return jsonify({"message": "Title and content are required"}), 400

    now_iso = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE personal_notes
        SET title = ?, content = ?, updated_at = ?
        WHERE id = ?
    """, (title, content, now_iso, note_id))
    rows_affected = cursor.rowcount
    conn.commit()

    if rows_affected == 0:
        conn.close()
        return jsonify({"message": "Note not found"}), 404

    cursor.execute("SELECT student_id, created_at FROM personal_notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()

    return jsonify({
        "id": note_id,
        "student_id": row[0] if row else "",
        "title": title,
        "content": content,
        "created_at": row[1] if row else now_iso,
        "updated_at": now_iso
    })


@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note_api(note_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM personal_notes WHERE id = ?", (note_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()

    if rows_affected == 0:
        return jsonify({"message": "Note not found"}), 404

    return jsonify({"success": True, "message": "Note deleted successfully"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        debug=False,
        host="0.0.0.0",
        port=port
    )