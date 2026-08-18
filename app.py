from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "audio_projects.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "ogg", "webm"}
ALLOWED_MIMES = {
    "audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4",
    "audio/x-m4a", "audio/ogg", "audio/webm"
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def allowed_file(filename, mimetype):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS and mimetype in ALLOWED_MIMES


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/submissions")
def create_submission():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    audio = request.files.get("audio")

    if not name or not phone:
        return jsonify({"error": "Name and phone number are required."}), 400

    if not audio or not audio.filename:
        return jsonify({"error": "Please upload an audio file."}), 400

    if not allowed_file(audio.filename, audio.mimetype):
        return jsonify({"error": "Unsupported audio format."}), 400

    safe_original = secure_filename(audio.filename)
    ext = safe_original.rsplit(".", 1)[-1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, stored_filename)

    audio.save(save_path)

    conn = get_db()
    cur = conn.execute("""
        INSERT INTO submissions
        (name, phone, original_filename, stored_filename, file_path)
        VALUES (?, ?, ?, ?, ?)
    """, (name, phone, safe_original, stored_filename, save_path))
    submission_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Submission received successfully.",
        "submission_id": submission_id
    }), 201


@app.get("/api/submissions")
def list_submissions():
    conn = get_db()
    rows = conn.execute("""
        SELECT id, name, phone, original_filename, created_at
        FROM submissions
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.get("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "File is too large. Maximum size is 25 MB."}), 413


init_db()

if __name__ == "__main__":
    app.run(debug=True)
