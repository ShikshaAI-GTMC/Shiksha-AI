# ShikshaAI

An AI-ready interactive audio learning platform that turns educational PDFs into summaries, flashcards, quizzes, and audio lesson scripts.

## Run locally

1. Start MongoDB locally (or set `MONGO_URI` to an Atlas connection string).
2. In `backend`, create and activate a Python 3.12+ virtual environment, then install dependencies. The dependency ranges support current Python 3.13 Windows wheels:

   `pip install -r requirements.txt`

3. Set a secure `JWT_SECRET` environment variable and start the API:

   `uvicorn main:app --reload`

4. Open **http://localhost:8000** in your browser. FastAPI serves the frontend and API together, so no separate Live Server or CORS configuration is needed. If you deploy the frontend separately, set `localStorage.shiksha_api` to the API URL.

## Architecture

- `frontend/`: responsive vanilla HTML, CSS and reusable JavaScript API/UI helpers.
- `backend/main.py`: FastAPI REST interface, authorization and orchestration.
- `backend/services/learning.py`: deterministic content-generation fallback. Replace these functions with OpenAI/Groq calls for production AI generation.
- MongoDB stores accounts, PDF metadata/text, summaries, flashcards, quizzes, history, and audio scripts.

## Security notes

Passwords are bcrypt-hashed. API routes holding student data use JWT bearer authentication. Before deployment, set a strong `JWT_SECRET`, a specific `CORS_ORIGINS` allowlist, and use managed MongoDB credentials. Configure a TTS provider in `generate_audio` to emit downloadable audio files.
