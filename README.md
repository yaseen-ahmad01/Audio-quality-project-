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
6. A row is inserted into SQLite.
7. The API returns a submission ID.

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

GET `/api/submissions`

Returns submission records as JSON.

## Important production changes

This demo stores files locally. For thousands of workers, use object storage such as S3-compatible storage, Google Cloud Storage, or Azure Blob Storage instead of keeping audio on the web server.

Also add authentication/admin access, HTTPS, stronger phone validation, rate limiting, malware/content scanning, database backups, and a proper file-storage lifecycle.
