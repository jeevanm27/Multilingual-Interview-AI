# 🤖 Multilingual Interview AI Bot

An AI-powered technical interview simulator that conducts full mock interviews in **6 languages** — English, German, Spanish, French, Tamil, and Telugu — complete with real-time voice playback of every question.

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="OpenAI" src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

---

## ✨ Why this project?

Most interview-prep tools are English-only and text-based. This bot generates **contextual, role-specific interview questions on the fly** using GPT-4o-mini, speaks them aloud in the candidate's chosen language via gTTS, evaluates spoken/typed answers, and closes with a short strengths/improvement summary — all through a lightweight FastAPI backend with zero external database dependency.



## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| LLM | OpenAI GPT-4o-mini |
| Text-to-Speech | gTTS (Google Text-to-Speech) |
| Frontend | Vanilla JS, HTML, CSS |
| Deployment | Docker, Docker Compose |
| Session storage | In-memory (no DB required) |

---

## 📁 Project Structure

```
Multilingual-Interview-AI/
├── main.py                  # FastAPI backend — routes, session logic, LLM calls
├── requirements.txt         # Python dependencies
├── Dockerfile                # Multi-stage Docker image (slim runtime)
├── docker-compose.yml        # Single-service Docker setup
├── .env.example               # Template — copy to .env and fill in your key
├── .gitignore
└── static/
    ├── index.html            # Single-page frontend (Vanilla JS)
    └── audio/                # gTTS-generated .mp3 files (auto-created at runtime)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (for Method 1)
- Docker Desktop (for Method 2)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Method 1: Plain Python (Fastest)

**1. Clone the repo**
```bash
git clone https://github.com/jeevanm27/Multilingual-Interview-AI.git
cd Multilingual-Interview-AI
```

**2. Create your `.env`**
```bash
cp .env.example .env        # macOS/Linux
# or
Copy-Item .env.example .env # Windows PowerShell
```
Open `.env` and set your real `OPENAI_API_KEY`.

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the server**
```bash
python main.py
```

**5. Open the app**
Visit → **http://localhost:8000**

---

### Method 2: Docker Compose

> Requires Docker Desktop to be running.

**1. Create your `.env`**
```bash
cp .env.example .env
```
Set `OPENAI_API_KEY` inside `.env`.

**2. Build and start**
```bash
docker-compose up --build
```

**3. Open the app**
Visit → **http://localhost:8000**

**Stop the app:**
```bash
docker-compose down
```

---

## 🔌 API Reference

### `POST /start-interview`
Starts a new session and returns the first question.

**Request**
```json
{
  "job_role": "Backend Engineer",
  "target_language": "Spanish"
}
```

**Response**
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
Submits an answer and returns the next question (or final feedback after `MAX_QUESTIONS`).

**Request**
```json
{
  "session_id": "uuid-here",
  "answer": "SQL is relational...",
  "target_language": "Spanish"
}
```

**Response**
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
2. **Voice Playback** — The question text is passed to gTTS, which generates an `.mp3`; the frontend auto-plays it.
3. **Submit Answer** — Client sends the answer back → server appends it to the conversation history → GPT generates the next question in the same language.
4. **Session End** — After `MAX_QUESTIONS` answers, GPT returns a performance summary (2 strengths + 1 improvement area) and the session is cleared from memory.

Sessions are stored in a plain Python dictionary in memory — no database or cache server required.

```
┌────────────┐     job_role, language      ┌────────────┐
│  Frontend  │ ───────────────────────────▶│  FastAPI    │
│ (index.html│                              │  main.py   │
└────────────┘◀─────────────────────────── └────┬───────┘
   plays .mp3      question_text, audio_url      │
                                                   ▼
                                          ┌─────────────────┐
                                          │  OpenAI GPT-4o- │
                                          │  mini (question │
                                          │  generation)     │
                                          └────────┬────────┘
                                                    ▼
                                          ┌─────────────────┐
                                          │      gTTS        │
                                          │ (text → speech)  │
                                          └─────────────────┘
```

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

## 🗺️ Roadmap

- [ ] Speech-to-text for spoken answers (Whisper API)
- [ ] Persistent session storage (Redis/Postgres)
- [ ] Downloadable PDF interview report
- [ ] More languages (Hindi, Japanese, Portuguese)
- [ ] Deployed live demo

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
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please open an issue first for major changes to discuss what you'd like to change.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Jeevan M**
- GitHub: [@jeevanm27](https://github.com/jeevanm27)

If you found this project useful, consider giving it a ⭐ on GitHub!
