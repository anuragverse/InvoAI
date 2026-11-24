import io

import pymupdf
import pytest
from fastapi.testclient import TestClient
from google.genai import errors

import app as app_module
import gemini_service
from store import RateLimiter, SessionStore


def make_pdf(text="Invoice #1001\nTotal: 250.00 USD\nDue: 2026-12-01"):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def blank_pdf():
    doc = pymupdf.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    monkeypatch.setattr(app_module, "sessions", SessionStore())
    monkeypatch.setattr(app_module, "limiter", RateLimiter())
    monkeypatch.setattr(gemini_service, "_client", None)
    monkeypatch.setattr(gemini_service, "_preferred_model", None)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def upload(client, data, name="invoice.pdf"):
    return client.post("/upload", files={"file": (name, io.BytesIO(data), "application/pdf")})


def test_upload_returns_session_and_text(client):
    response = upload(client, make_pdf())
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert "Invoice #1001" in body["text"]
    assert body["pages"] == 1
    assert body["truncated"] is False


def test_rejects_non_pdf_extension(client):
    response = upload(client, make_pdf(), name="notes.txt")
    assert response.status_code == 400


def test_rejects_fake_pdf_content(client):
    response = upload(client, b"this is definitely not a pdf at all", name="invoice.pdf")
    assert response.status_code == 400


def test_rejects_corrupt_pdf(client):
    response = upload(client, b"%PDF-1.7\ngarbage garbage garbage", name="invoice.pdf")
    assert response.status_code == 400


def test_rejects_empty_file(client):
    assert upload(client, b"").status_code == 400


def test_scanned_pdf_without_text_is_422(client):
    response = upload(client, blank_pdf())
    assert response.status_code == 422
    assert "No text" in response.json()["detail"]


def test_too_large_is_413(client, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_UPLOAD_BYTES", 1024)
    response = upload(client, make_pdf() + b"0" * 5000)
    assert response.status_code == 413


def test_path_traversal_filename_writes_nothing(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = upload(client, make_pdf(), name="../../evil.pdf")
    assert response.status_code == 200
    assert response.json()["filename"] == "evil.pdf"
    assert list(tmp_path.iterdir()) == []  # nothing is saved to disk


def test_page_limit_marks_truncated(client, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_PAGES", 1)
    doc = pymupdf.open()
    for i in range(3):
        doc.new_page().insert_text((72, 72), f"Page {i}")
    data = doc.tobytes()
    doc.close()
    body = upload(client, data).json()
    assert body["pages"] == 3
    assert body["truncated"] is True
    assert "Page 0" in body["text"] and "Page 2" not in body["text"]


def test_ask_requires_valid_session(client):
    response = client.post("/ask", json={"question": "Total?", "session_id": "does-not-exist-123"})
    assert response.status_code == 404


def test_ask_validation(client):
    assert client.post("/ask", json={"question": "", "session_id": "abcdefgh12"}).status_code == 422
    long_question = "q" * 501
    assert client.post("/ask", json={"question": long_question, "session_id": "abcdefgh12"}).status_code == 422


def test_each_visitor_only_sees_their_own_invoice(client, monkeypatch):
    seen = []
    monkeypatch.setattr(app_module, "ask_gemini", lambda text, q: (seen.append(text) or "ok"))

    a = upload(client, make_pdf("ALICE invoice total 111")).json()["session_id"]
    b = upload(client, make_pdf("BOB invoice total 222")).json()["session_id"]

    client.post("/ask", json={"question": "total?", "session_id": a})
    client.post("/ask", json={"question": "total?", "session_id": b})

    assert "ALICE" in seen[0] and "BOB" not in seen[0]
    assert "BOB" in seen[1] and "ALICE" not in seen[1]


def test_ask_returns_answer(client, monkeypatch):
    monkeypatch.setattr(app_module, "ask_gemini", lambda text, q: "The total is 250.00 USD")
    sid = upload(client, make_pdf()).json()["session_id"]
    response = client.post("/ask", json={"question": "  What is the total? ", "session_id": sid})
    assert response.status_code == 200
    assert response.json() == {"question": "What is the total?", "answer": "The total is 250.00 USD"}


def test_ask_rate_limit(client, monkeypatch):
    monkeypatch.setattr(app_module, "ASKS_PER_10_MIN", 2)
    monkeypatch.setattr(app_module, "ask_gemini", lambda text, q: "ok")
    sid = upload(client, make_pdf()).json()["session_id"]
    codes = [client.post("/ask", json={"question": "hi", "session_id": sid}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_gemini_error_is_shown_as_clean_message(client, monkeypatch):
    def boom(text, question):
        raise gemini_service.GeminiError("The AI service is busy right now.", 503)

    monkeypatch.setattr(app_module, "ask_gemini", boom)
    sid = upload(client, make_pdf()).json()["session_id"]
    response = client.post("/ask", json={"question": "hi", "session_id": sid})
    assert response.status_code == 503
    assert response.json()["detail"] == "The AI service is busy right now."


def test_cors_only_allows_configured_origin(client):
    ok = client.options(
        "/ask",
        headers={
            "Origin": "https://invoai.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert ok.headers.get("access-control-allow-origin") == "https://invoai.example.com"

    bad = client.options(
        "/ask",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in bad.headers


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


# ---- Gemini service: model fallback and error handling (no network) ----

class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        result = self.behaviour(model)
        if isinstance(result, Exception):
            raise result
        return FakeResponse(result)


class FakeClient:
    def __init__(self, behaviour):
        self.models = FakeModels(behaviour)


def api_error(code):
    cls = errors.ClientError if code < 500 else errors.ServerError
    return cls(code, {"error": {"code": code, "message": "x", "status": "X"}})


def test_falls_back_when_model_is_missing(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "old-model,new-model")
    fake = FakeClient(lambda m: api_error(404) if m == "old-model" else "answer from new")
    monkeypatch.setattr(gemini_service, "_client", fake)

    assert gemini_service.ask_gemini("invoice", "q") == "answer from new"
    assert fake.models.calls == ["old-model", "new-model"]

    # the working model is remembered
    gemini_service.ask_gemini("invoice", "q")
    assert fake.models.calls[-1] == "new-model"


def test_quota_error_is_503(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "m1")
    monkeypatch.setattr(gemini_service, "_client", FakeClient(lambda m: api_error(429)))
    with pytest.raises(gemini_service.GeminiError) as info:
        gemini_service.ask_gemini("invoice", "q")
    assert info.value.status_code == 503


def test_all_models_missing_gives_helpful_error(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "m1,m2")
    monkeypatch.setattr(gemini_service, "_client", FakeClient(lambda m: api_error(404)))
    with pytest.raises(gemini_service.GeminiError) as info:
        gemini_service.ask_gemini("invoice", "q")
    assert "GEMINI_MODEL" in info.value.message


def test_invalid_api_key_is_reported_clearly(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "m1,m2")
    bad_key = errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.", "status": "INVALID_ARGUMENT"}})
    fake = FakeClient(lambda m: bad_key)
    monkeypatch.setattr(gemini_service, "_client", fake)
    with pytest.raises(gemini_service.GeminiError) as info:
        gemini_service.ask_gemini("invoice", "q")
    assert "API key was rejected" in info.value.message
    assert fake.models.calls == ["m1"]  # no point trying other models


def test_overloaded_model_falls_back_then_reports_unavailable(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "m1,m2")
    fake = FakeClient(lambda m: api_error(503))
    monkeypatch.setattr(gemini_service, "_client", fake)
    with pytest.raises(gemini_service.GeminiError) as info:
        gemini_service.ask_gemini("invoice", "q")
    assert fake.models.calls == ["m1", "m2"]
    assert "temporarily unavailable" in info.value.message


def test_rejecting_model_does_not_block_a_working_one(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "picky-model,good-model")
    err = errors.ClientError(400, {"error": {"code": 400, "message": "Unsupported setting", "status": "INVALID_ARGUMENT"}})
    fake = FakeClient(lambda m: err if m == "picky-model" else "fine")
    monkeypatch.setattr(gemini_service, "_client", fake)
    assert gemini_service.ask_gemini("invoice", "q") == "fine"
    assert fake.models.calls == ["picky-model", "good-model"]


def test_default_chain_starts_with_gemini_25_flash(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert gemini_service._models()[0] == "gemini-2.5-flash"
    assert len(gemini_service._models()) >= 3


def test_other_bad_request_shows_google_reason(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "m1")
    err = errors.ClientError(400, {"error": {"code": 400, "message": "Unsupported parameter foo", "status": "INVALID_ARGUMENT"}})
    monkeypatch.setattr(gemini_service, "_client", FakeClient(lambda m: err))
    with pytest.raises(gemini_service.GeminiError) as info:
        gemini_service.ask_gemini("invoice", "q")
    assert "Unsupported parameter foo" in info.value.message


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(gemini_service.GeminiError) as info:
        gemini_service.ask_gemini("invoice", "q")
    assert info.value.status_code == 503


def test_empty_model_answer_is_handled(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "m1")
    monkeypatch.setattr(gemini_service, "_client", FakeClient(lambda m: ""))
    assert "rephras" in gemini_service.ask_gemini("invoice", "q")


# ---- store helpers ----

def test_sessions_expire_and_are_bounded():
    store = SessionStore(ttl_seconds=0, max_sessions=3)
    sid = store.create("a.pdf", "text")
    import time
    time.sleep(0.01)
    assert store.get(sid) is None

    store = SessionStore(ttl_seconds=3600, max_sessions=3)
    for i in range(10):
        store.create(f"{i}.pdf", "t")
    assert store.count() <= 3


def test_rate_limiter_window():
    limiter = RateLimiter()
    assert limiter.check("k", 2, 60) == 0
    assert limiter.check("k", 2, 60) == 0
    assert limiter.check("k", 2, 60) > 0
    assert limiter.check("other", 2, 60) == 0
