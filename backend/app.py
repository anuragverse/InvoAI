import logging
import os
import re
import time

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from gemini_service import GeminiError, ask_gemini
from pdf_reader import PdfError, extract_text_from_pdf_bytes
from store import RateLimiter, SessionStore

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("invoai")


def _int_env(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


MAX_UPLOAD_BYTES = _int_env("MAX_UPLOAD_MB", 10) * 1024 * 1024
MAX_PAGES = _int_env("MAX_PAGES", 30)
MAX_TEXT_CHARS = _int_env("MAX_TEXT_CHARS", 60000)
MAX_QUESTION_CHARS = 500

UPLOADS_PER_10_MIN = _int_env("UPLOADS_PER_10_MIN", 10)
ASKS_PER_10_MIN = _int_env("ASKS_PER_10_MIN", 30)
GLOBAL_ASKS_PER_MIN = _int_env("GLOBAL_ASKS_PER_MIN", 40)

# Browser origins that may call this API (comma separated, no trailing slash).
# Set CLIENT_URL to your deployed frontend URL.
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CLIENT_URL", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app = FastAPI(title="InvoAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

sessions = SessionStore()
limiter = RateLimiter()


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    session_id: str = Field(min_length=8, max_length=64)


def client_ip(request: Request):
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_limit(key, limit, window, message):
    wait = limiter.check(key, limit, window)
    if wait:
        raise HTTPException(
            status_code=429,
            detail=message,
            headers={"Retry-After": str(wait)},
        )


def safe_filename(name):
    """Only used for display. Files are never saved to disk."""
    name = os.path.basename(name or "invoice.pdf")
    name = re.sub(r"[^\w.\- ]", "_", name).strip()
    return (name or "invoice.pdf")[:120]


def read_upload(upload: UploadFile):
    data = bytearray()
    while True:
        chunk = upload.file.read(1024 * 1024)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"The file is too large. The limit is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
            )
    return bytes(data)


@app.exception_handler(PdfError)
def pdf_error_handler(request, error: PdfError):
    return JSONResponse(status_code=error.status_code, content={"detail": error.message})


@app.exception_handler(GeminiError)
def gemini_error_handler(request, error: GeminiError):
    return JSONResponse(status_code=error.status_code, content={"detail": error.message})


@app.get("/")
def home():
    return {"message": "InvoAI Backend is Running!"}


@app.get("/health")
def health():
    return {"status": "ok"}


# These are plain `def` endpoints on purpose: FastAPI runs them in a worker thread,
# so the slow PDF parsing and AI calls do not block other visitors.
@app.post("/upload")
def upload_invoice(request: Request, file: UploadFile = File(...)):
    enforce_limit(
        f"upload:{client_ip(request)}",
        UPLOADS_PER_10_MIN,
        600,
        "Too many uploads. Please wait a few minutes and try again.",
    )

    filename = safe_filename(file.filename)

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    data = read_upload(file)

    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if b"%PDF-" not in data[:1024]:
        raise HTTPException(status_code=400, detail="This file is not a valid PDF.")

    text, total_pages, pages_read = extract_text_from_pdf_bytes(data, MAX_PAGES)

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text was found in this PDF. Scanned or image-only invoices are not supported yet.",
        )

    truncated = len(text) > MAX_TEXT_CHARS or pages_read < total_pages
    text = text[:MAX_TEXT_CHARS]

    session_id = sessions.create(filename, text)

    return {
        "message": "File uploaded successfully!",
        "session_id": session_id,
        "filename": filename,
        "pages": total_pages,
        "truncated": truncated,
        "text": text,
    }


@app.post("/ask")
def ask_invoice(request: Request, body: AskBody):
    enforce_limit(
        f"ask:{client_ip(request)}",
        ASKS_PER_10_MIN,
        600,
        "You are asking too quickly. Please wait a few minutes and try again.",
    )
    enforce_limit(
        "ask:global",
        GLOBAL_ASKS_PER_MIN,
        60,
        "The service is busy right now. Please try again in a minute.",
    )

    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Your invoice session has expired. Please upload the invoice again.",
        )

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please enter a question.")

    started = time.time()
    answer = ask_gemini(session["text"], question)
    log.info("answered a question in %.1fs", time.time() - started)

    return {"question": question, "answer": answer}
