# Audio Submission App

A small full-stack application for collecting worker audio recordings.

## Stack

- Frontend: plain HTML/CSS/JavaScript
- Backend: Python Flask
- Database: SQLite
- Audio storage: local `uploads/` folder

## Data flow

1. Worker enters name and phone.
2. Worker selects an audio file.
3. Browser sends the form using `multipart/form-data`.
4. Flask validates the request.
5. Audio is saved in `uploads/`.
6. `ffprobe`/`ffmpeg` extract duration, sample rate, bitrate, and loudness.
7. A row is inserted into SQLite, including the extracted metadata.
8. The API returns a submission ID and the extracted metadata.

## Audio metadata extraction

On every upload, the server automatically extracts:

- **Duration** (seconds)
- **Sample rate** (Hz / kHz)
- **Bitrate** (kbps)
- **Loudness** (mean volume in dB, via ffmpeg's `volumedetect` filter)

This uses `ffmpeg`/`ffprobe` via `subprocess` calls — no extra Python
packages required. If ffmpeg isn't installed, submissions still work
normally; the metadata fields are just left as `null`, and a warning is
printed to the server log on startup.

### Install ffmpeg

Windows (with [Chocolatey](https://chocolatey.org/)):

    choco install ffmpeg

macOS (with [Homebrew](https://brew.sh/)):

    brew install ffmpeg

Debian/Ubuntu:

    sudo apt update && sudo apt install ffmpeg

Verify it's on your PATH:

    ffmpeg -version
    ffprobe -version

> Note on loudness: `volumedetect` reports mean volume relative to full
> scale (dBFS), which is simple and dependency-free. If you need
> broadcast-standard loudness (LUFS, EBU R128), swap the filter for
> `loudnorm=print_format=json` and parse `input_i` instead — same
> ffmpeg dependency, just a different filter.

## Run locally

### 1. Create a virtual environment

Windows:

    python -m venv venv
    venv\Scripts\activate

macOS/Linux:

    python3 -m venv venv
    source venv/bin/activate

### 2. Install dependencies

    pip install -r requirements.txt

### 3. Start the server

    python app.py

### 4. Open

    http://127.0.0.1:5000

The SQLite database `audio_projects.db` is created automatically.

## API

POST `/api/submissions`

Form fields:

- `name`
- `phone`
- `audio`

Response includes extracted metadata: `duration_seconds`, `sample_rate_hz`, `bitrate_kbps`, `loudness_db`.

GET `/api/submissions`

Returns submission records as JSON, including `duration_seconds`,
`sample_rate_hz`, `sample_rate_khz`, `bitrate_kbps`, and `loudness_db`
for each row.

## Important production changes

This demo stores files locally. For thousands of workers, use object storage such as S3-compatible storage, Google Cloud Storage, or Azure Blob Storage instead of keeping audio on the web server.

Also add authentication/admin access, HTTPS, stronger phone validation, rate limiting, malware/content scanning, database backups, and a proper file-storage lifecycle.
