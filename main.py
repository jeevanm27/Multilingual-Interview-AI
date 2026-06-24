"""
main.py  –  Multilingual Interview AI Bot (No Redis)
Sessions are stored in a plain Python dict in memory.
Think of it like an Express app that uses a Map<sessionId, data>
instead of express-session + Redis.
"""

import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import aiofiles
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
import openai as openai_exc
from gtts import gTTS
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AUDIO_DIR      = Path(os.getenv("AUDIO_DIR", "static/audio"))
MAX_QUESTIONS  = int(os.getenv("MAX_QUESTIONS", 6))

AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# In-memory session store  (like a global Map in Node.js)
# Key: session_id (UUID string)  →  Value: dict with history + metadata
# ─────────────────────────────────────────────────────────────────────────────
SESSION_STORE: dict[str, dict] = {}

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    log.info("🚀  Interview AI Bot starting up — no Redis, in-memory sessions")
    yield
    log.info("🛑  Shutting down — clearing %d sessions", len(SESSION_STORE))
    SESSION_STORE.clear()

app = FastAPI(
    title="Multilingual Interview AI Bot",
    description="AI-powered multilingual technical interview simulator",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas  (like @RequestBody DTOs)
# ─────────────────────────────────────────────────────────────────────────────
class StartInterviewRequest(BaseModel):
    job_role: str        = Field(..., min_length=2, max_length=100, example="Backend Engineer")
    target_language: str = Field(..., example="Spanish")

class SubmitAnswerRequest(BaseModel):
    session_id: str      = Field(..., description="UUID from /start-interview")
    answer: str          = Field(..., min_length=1, max_length=4000)
    target_language: str = Field(..., example="Spanish")

class InterviewResponse(BaseModel):
    session_id:      str
    question_text:   str
    audio_url:       str
    question_number: int
    is_complete:     bool = False

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGE_CODE_MAP = {
    "english": "en",
    "german":  "de",
    "spanish": "es",
    "french":  "fr",
    "tamil":   "ta",
    "telugu":  "te",
}

def get_gtts_lang(language: str) -> str:
    return LANGUAGE_CODE_MAP.get(language.lower(), "en")


async def generate_audio(text: str, language: str, filename: str) -> str:
    """
    gTTS is blocking I/O — offload to a thread pool so the async event loop
    isn't blocked. Same idea as util.promisify() wrapping a sync callback in Node.
    """
    filepath = AUDIO_DIR / filename
    lang_code = get_gtts_lang(language)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: gTTS(text=text, lang=lang_code, slow=False).save(str(filepath))
    )
    return f"/static/audio/{filename}"


async def call_llm(messages: list[dict]) -> str:
    """Single wrapper around OpenAI Chat Completions — like an axios.post() call."""
    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except openai_exc.AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="❌ Invalid OpenAI API key. Please update OPENAI_API_KEY in your .env file."
        )
    except openai_exc.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="❌ OpenAI quota exceeded. Your API key has run out of credits. Please top up at https://platform.openai.com/account/billing"
        )
    except openai_exc.APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="❌ Could not connect to OpenAI. Please check your internet connection."
        )
    except openai_exc.OpenAIError as e:
        log.error("OpenAI error: %s", e)
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")


def build_system_prompt(job_role: str, language: str) -> str:
    return (
        f"You are a professional technical interviewer conducting an interview for "
        f"the role of '{job_role}'. Ask one clear, concise, technical question at a time. "
        f"IMPORTANT: Your ENTIRE response must be in {language} only. "
        f"Do not mix languages. Do not use English unless the target language IS English. "
        f"Keep questions practical and relevant to the role."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": OPENAI_MODEL,
        "active_sessions": len(SESSION_STORE),
    }


@app.post("/start-interview", response_model=InterviewResponse)
async def start_interview(payload: StartInterviewRequest):
    session_id    = str(uuid.uuid4())
    system_prompt = build_system_prompt(payload.job_role, payload.target_language)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Start the interview now. Ask the first technical question "
                f"for the role of {payload.job_role} in {payload.target_language}. "
                f"Output only the question — no preamble."
            ),
        },
    ]

    question_text = await call_llm(messages)
    log.info("Session %s | Role: %s | Lang: %s", session_id, payload.job_role, payload.target_language)

    audio_url = await generate_audio(question_text, payload.target_language, f"{session_id}_q1.mp3")

    # Store session in memory (replaces Redis)
    SESSION_STORE[session_id] = {
        "job_role":       payload.job_role,
        "language":       payload.target_language,
        "question_count": 1,
        "history": [
            {"role": "system",    "content": system_prompt},
            {"role": "assistant", "content": question_text},
        ],
    }

    return InterviewResponse(
        session_id=session_id,
        question_text=question_text,
        audio_url=audio_url,
        question_number=1,
    )


@app.post("/submit-answer", response_model=InterviewResponse)
async def submit_answer(payload: SubmitAnswerRequest):
    session = SESSION_STORE.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new interview.")

    q_count  = session["question_count"]
    is_final = (q_count >= MAX_QUESTIONS)

    session["history"].append({"role": "user", "content": payload.answer})

    if is_final:
        next_prompt = (
            f"The candidate has completed all {MAX_QUESTIONS} questions. "
            f"Give a brief, encouraging performance summary in {payload.target_language}. "
            f"Mention 2 strengths and 1 area to improve. Keep it under 120 words."
        )
    else:
        next_prompt = (
            f"In {payload.target_language}: Give a very brief (1 sentence) positive "
            f"acknowledgment of the answer, then immediately ask question "
            f"{q_count + 1} of {MAX_QUESTIONS} for a {session['job_role']}. "
            f"Stay entirely in {payload.target_language}."
        )

    session["history"].append({"role": "user", "content": next_prompt})
    ai_response = await call_llm(session["history"])
    session["history"].append({"role": "assistant", "content": ai_response})
    session["question_count"] = q_count + 1

    audio_url = await generate_audio(
        ai_response, payload.target_language, f"{payload.session_id}_q{q_count + 1}.mp3"
    )

    log.info("Session %s | Q%s answered | Final: %s", payload.session_id, q_count, is_final)

    # Clean up session after interview ends
    if is_final:
        SESSION_STORE.pop(payload.session_id, None)

    return InterviewResponse(
        session_id=payload.session_id,
        question_text=ai_response,
        audio_url=audio_url,
        question_number=q_count + 1,
        is_complete=is_final,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dev entry-point  (like: node index.js)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
