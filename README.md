# 🤖 Multilingual Interview AI Bot

An AI-powered technical interview simulator that conducts interviews in **6 languages** — English, German, Spanish, French, Tamil, and Telugu — with real-time voice playback.

**Stack:** Python · FastAPI · OpenAI GPT-4o-mini · gTTS · Docker

---

## 📁 Project Structure

```
pfm 2/
├── main.py                  # FastAPI backend — all routes, session logic, LLM calls
├── requirements.txt         # Python dependencies
├── Dockerfile               # Multi-stage Docker image (slim runtime)
├── docker-compose.yml       # Single-service Docker setup
├── .env.example             # Template — copy to .env and fill in your key
├── .gitignore
└── static/
    ├── index.html           # Single-page frontend (Vanilla JS)
    └── audio/               # gTTS-generated .mp3 files (auto-created at runtime)
```

---

## 🚀 Quick Start

### Method 1: Plain Python (Fastest)

**Step 1 — Create your `.env`**
```powershell
# Windows PowerShell
Copy-Item .env.example .env
```
Open `.env` and set your real `OPENAI_API_KEY`.

**Step 2 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3 — Run**
```bash
python main.py
```

**Step 4 — Open the app**
Visit → **http://localhost:8000**

---

### Method 2: Docker Compose

> Requires Docker Desktop to be running.

**Step 1 — Create your `.env`**
```powershell
Copy-Item .env.example .env
```
Set `OPENAI_API_KEY` inside `.env`.

**Step 2 — Build and start**
```bash
docker-compose up --build
```

**Step 3 — Open the app**
Visit → **http://localhost:8000**

**Stop the app:**
```bash
docker-compose down
```

---

## 🔌 API Reference

### `POST /start-interview`
Starts a new session and returns the first question.

**Request:**
```json
{
  "job_role": "Backend Engineer",
  "target_language": "Spanish"
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "question_text": "¿Puedes explicar la diferencia entre SQL y NoSQL?",
  "audio_url": "/static/audio/uuid_q1.mp3",
  "question_number": 1,
  "is_complete": false
}
```

---

### `POST /submit-answer`
Submits an answer and returns the next question (or final feedback after 6 questions).

**Request:**
```json
{
  "session_id": "uuid-here",
  "answer": "SQL is relational...",
  "target_language": "Spanish"
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "question_text": "¡Excelente! Pregunta 2 de 6: ¿Qué es Docker?",
  "audio_url": "/static/audio/uuid_q2.mp3",
  "question_number": 2,
  "is_complete": false
}
```

---

### `GET /health`
Returns server health and active session count.

```json
{ "status": "ok", "model": "gpt-4o-mini", "active_sessions": 2 }
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI secret key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use (`gpt-4o` for higher quality) |
| `AUDIO_DIR` | `static/audio` | Directory where TTS audio files are saved |
| `MAX_QUESTIONS` | `6` | Number of questions per interview session |

---

## 🧠 How It Works

1. **Start Interview** — Client sends job role + language → server creates an in-memory session (UUID key) and asks GPT for the first question.
2. **Voice Playback** — The question text is passed to gTTS which generates an `.mp3`; the frontend auto-plays it.
3. **Submit Answer** — Client sends the answer back → server appends it to the conversation history → GPT generates the next question in the same language.
4. **Session End** — After `MAX_QUESTIONS` answers, GPT returns a performance summary (2 strengths + 1 improvement area) and the session is cleared from memory.

Sessions are stored in a plain Python dictionary in memory — no database or cache server required.

---

## 🌍 Supported Languages

| Language | gTTS Code |
|---|---|
| English | `en` |
| German | `de` |
| Spanish | `es` |
| French | `fr` |
| Tamil | `ta` |
| Telugu | `te` |

---

## 🐛 Troubleshooting

**`OPENAI_API_KEY` not set / 401 Unauthorized**
- Make sure `.env` exists and contains your real key (not the placeholder).

**`gTTS` fails for Tamil/Telugu**
- gTTS calls Google's TTS API — requires an active internet connection.
- Check your firewall or proxy settings.

**Audio not playing in browser**
- Some browsers block autoplay; click the audio player manually the first time.
- HTTPS is required for autoplay on mobile browsers.

**Port 8000 already in use**
```bash
# Find and kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```
