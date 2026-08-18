from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os
import uuid
import json
import re
import shutil
import subprocess
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

FFPROBE_AVAILABLE = shutil.which("ffprobe") is not None
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

if not (FFPROBE_AVAILABLE and FFMPEG_AVAILABLE):
    print(
        "WARNING: ffmpeg/ffprobe not found on PATH. Audio metadata "
        "(duration, sample rate, bitrate, loudness) will not be extracted. "
        "Install ffmpeg to enable this feature."
    )


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

    # Add new metadata columns if this is an existing DB created before
    # this feature was added. SQLite has no "ADD COLUMN IF NOT EXISTS",
    # so we check first.
    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(submissions)")}
    new_columns = {
        "duration_seconds": "REAL",
        "sample_rate_hz": "INTEGER",
        "bitrate_kbps": "INTEGER",
        "loudness_db": "REAL",
    }
    for col_name, col_type in new_columns.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE submissions ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


def allowed_file(filename, mimetype):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS and mimetype in ALLOWED_MIMES


def extract_audio_metadata(filepath):
    """
    Extract duration, sample rate, bitrate, and loudness from an audio
    file using ffprobe / ffmpeg. Returns a dict; any value that can't be
    determined is left as None so a failure never blocks the submission.
    """
    metadata = {
        "duration_seconds": None,
        "sample_rate_hz": None,
        "bitrate_kbps": None,
        "loudness_db": None,
    }

    if not (FFPROBE_AVAILABLE and FFMPEG_AVAILABLE):
        return metadata

    # --- duration, sample rate, bitrate via ffprobe ---
    try:
        probe = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                filepath,
            ],
            capture_output=True, text=True, timeout=30, check=True,
        )
        data = json.loads(probe.stdout)

        fmt = data.get("format", {})
        if fmt.get("duration"):
            metadata["duration_seconds"] = round(float(fmt["duration"]), 2)
        if fmt.get("bit_rate"):
            metadata["bitrate_kbps"] = round(int(fmt["bit_rate"]) / 1000)

        audio_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
            None,
        )
        if audio_stream:
            if audio_stream.get("sample_rate"):
                metadata["sample_rate_hz"] = int(audio_stream["sample_rate"])
            # Some containers (e.g. wav) only report bitrate on the stream,
            # not the format, so fall back to that.
            if metadata["bitrate_kbps"] is None and audio_stream.get("bit_rate"):
                metadata["bitrate_kbps"] = round(int(audio_stream["bit_rate"]) / 1000)
    except Exception as e:
        print(f"ffprobe metadata extraction failed for {filepath}: {e}")

    # --- loudness via ffmpeg's volumedetect filter (mean volume, dBFS) ---
    try:
        vol = subprocess.run(
            ["ffmpeg", "-i", filepath, "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=30,
        )
        match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", vol.stderr)
        if match:
            metadata["loudness_db"] = float(match.group(1))
    except Exception as e:
        print(f"ffmpeg loudness extraction failed for {filepath}: {e}")

    return metadata


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

    metadata = extract_audio_metadata(save_path)

    conn = get_db()
    cur = conn.execute("""
        INSERT INTO submissions
        (name, phone, original_filename, stored_filename, file_path,
         duration_seconds, sample_rate_hz, bitrate_kbps, loudness_db)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, phone, safe_original, stored_filename, save_path,
        metadata["duration_seconds"], metadata["sample_rate_hz"],
        metadata["bitrate_kbps"], metadata["loudness_db"],
    ))
    submission_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Submission received successfully.",
        "submission_id": submission_id,
        "metadata": metadata
    }), 201


@app.get("/api/submissions")
def list_submissions():
    conn = get_db()
    rows = conn.execute("""
        SELECT id, name, phone, original_filename, created_at,
               duration_seconds, sample_rate_hz, bitrate_kbps, loudness_db
        FROM submissions
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    results = []
    for row in rows:
        item = dict(row)
        item["sample_rate_khz"] = (
            round(item["sample_rate_hz"] / 1000, 1)
            if item["sample_rate_hz"] else None
        )
        results.append(item)

    return jsonify(results)


@app.get("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "File is too large. Maximum size is 25 MB."}), 413


init_db()

if __name__ == "__main__":
    app.run(debug=True)
