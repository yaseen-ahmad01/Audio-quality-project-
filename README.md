# Audio Submission App

A  full-stack application for collecting user audio recordings and its qualtiy.

## Stack

- Frontend: plain HTML/CSS/JavaScript
- Backend: Python Flask
- Database: SQLite
- Audio storage: local `uploads/` folder

## Stuck Log
1. how to extract audio quality data. brainstrom with LLM , how to do that , chose 'ffmpeg and ffprobe' over mutagen and librose.
2. Data Base connection issue faced ,created a sperate file for submission but redict the submisson file to task 1 database

## Data flow

1. user enters name and phone.
2. user selects an audio file.
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

This uses `ffmpeg`/`ffprobe` via `subprocess` calls 

### Install ffmpeg

Windows (with [Chocolatey](https://chocolatey.org/)):

    choco install ffmpeg

Verify it's on your PATH:

    ffmpeg -version
    ffprobe -version

## Run locally

### 1. Create a virtual environment

Windows:

    python -m venv venv
    venv\Scripts\activate


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

## Submissions page

`/submissions` lists every submission with an inline audio player and
the extracted duration, sample rate, bitrate, and loudness. It's a plain
HTML/JS page (`templates/submissions.html`, `static/submissions.js`)
that calls the existing `/api/submissions` endpoint — no new backend
dependencies.
## Deploy on Railway . choose railway bacause its simple to setup and implimnet 