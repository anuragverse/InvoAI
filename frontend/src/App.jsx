import { useEffect, useRef, useState } from "react";
import "./App.css";
import invoaiMark from "./assets/invoai-mark.png";
import { api, errorMessage, MAX_UPLOAD_MB } from "./api";

const SUGGESTIONS = [
  "What is the total amount?",
  "Who is this invoice from?",
  "When is it due?",
  "List the line items.",
];

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function App() {
  // -----------------------------
  // State
  // -----------------------------
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  // The uploaded invoice: { sessionId, filename, pages, truncated, text }
  const [invoice, setInvoice] = useState(null);

  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState([]); // [{ question, answer, isError }]

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState("");

  // { type: "error" | "success", text }
  const [notice, setNotice] = useState(null);

  const fileInputRef = useRef(null);
  const transcriptRef = useRef(null);

  // Keep the newest message in view
  useEffect(() => {
    const el = transcriptRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [history, asking]);

  // -----------------------------
  // File selection (browse or drag & drop)
  // -----------------------------
  const chooseFile = (file) => {
    if (!file) return;

    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setNotice({ type: "error", text: "Please choose a PDF file." });
      return;
    }

    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setNotice({ type: "error", text: `That file is too large. The limit is ${MAX_UPLOAD_MB} MB.` });
      return;
    }

    setNotice(null);
    setSelectedFile(file);
  };

  const handleFileChange = (event) => {
    chooseFile(event.target.files[0]);
    // allow choosing the same file again later
    event.target.value = "";
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    chooseFile(event.dataTransfer.files[0]);
  };

  // -----------------------------
  // Upload invoice
  // -----------------------------
  const handleUpload = async () => {
    if (!selectedFile) {
      setNotice({ type: "error", text: "Please select a PDF file first." });
      return;
    }

    setUploading(true);
    setNotice(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const { data } = await api.post("/upload", formData);

      setInvoice({
        sessionId: data.session_id,
        filename: data.filename,
        pages: data.pages,
        truncated: data.truncated,
        text: data.text,
      });
      setHistory([]);
      setQuestion("");
      setNotice({ type: "success", text: "Invoice uploaded. You can now ask questions about it." });
    } catch (error) {
      setNotice({ type: "error", text: errorMessage(error, "Unable to upload the invoice.") });
    } finally {
      setUploading(false);
    }
  };

  // -----------------------------
  // Ask a question
  // -----------------------------
  const handleAskQuestion = async (preset) => {
    const text = (typeof preset === "string" ? preset : question).trim();

    if (!invoice) {
      setNotice({ type: "error", text: "Upload an invoice first." });
      return;
    }

    if (!text) {
      setNotice({ type: "error", text: "Please enter a question." });
      return;
    }

    setAsking(true);
    setPendingQuestion(text);
    setNotice(null);

    try {
      const { data } = await api.post("/ask", {
        question: text,
        session_id: invoice.sessionId,
      });

      setHistory((previous) => [...previous, { question: text, answer: data.answer, isError: false }]);
      setQuestion("");
    } catch (error) {
      if (error?.response?.status === 404) {
        // The server forgot this invoice (restart or timeout)
        setInvoice(null);
        setNotice({ type: "error", text: errorMessage(error) });
      } else {
        setHistory((previous) => [
          ...previous,
          { question: text, answer: errorMessage(error, "Unable to get an answer."), isError: true },
        ]);
      }
    } finally {
      setAsking(false);
    }
  };

  const handleQuestionKeyDown = (event) => {
    if (event.key === "Enter" && !asking) {
      event.preventDefault();
      handleAskQuestion();
    }
  };

  const handleStartOver = () => {
    setInvoice(null);
    setSelectedFile(null);
    setHistory([]);
    setQuestion("");
    setNotice(null);
  };

  const pageLabel = invoice ? `${invoice.pages} ${invoice.pages === 1 ? "page" : "pages"}` : "";

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <img src={invoaiMark} alt="" className="brand-mark" width="42" height="43" />
          <span className="brand-name">
            Invo<span>AI</span>
          </span>
        </div>
        <p className="tagline">Ask questions about any invoice PDF</p>
      </header>

      {notice && (
        <div className={`notice notice-${notice.type}`} role={notice.type === "error" ? "alert" : "status"}>
          <span>{notice.text}</span>
          <button className="notice-close" onClick={() => setNotice(null)} aria-label="Dismiss message">
            <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
              <path d="M3.5 3.5l9 9m0-9l-9 9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      )}

      <main className="workbench">
        {/* Left: the invoice */}
        <section className="panel desk" aria-label="Invoice">
          <div className="panel-head">
            <h2>Invoice</h2>
            {invoice && (
              <button className="text-btn" onClick={handleStartOver}>
                Start over
              </button>
            )}
          </div>

          {invoice ? (
            <div className="desk-body">
              <div className="file-meta">
                <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
                  <path
                    d="M5 2.5h6.5L15 6v11.5H5z M11.5 2.5V6H15"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                  />
                </svg>
                <span className="file-name" title={invoice.filename}>
                  {invoice.filename}
                </span>
                <span className="file-pages">{pageLabel}</span>
              </div>

              {invoice.truncated && (
                <p className="callout">This invoice is long, so only the first part of it was read.</p>
              )}

              <div className={`sheet${asking ? " scanning" : ""}`}>
                <pre className="invoice-preview">{invoice.text}</pre>
              </div>
            </div>
          ) : (
            <div className="desk-body">
              <div
                className={`dropzone${dragOver ? " drag-over" : ""}${selectedFile ? " has-file" : ""}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  id="fileInput"
                  accept=".pdf,application/pdf"
                  hidden
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />

                <svg className="drop-icon" viewBox="0 0 48 48" width="44" height="44" aria-hidden="true">
                  <path
                    d="M13 5h16l8 8v30H13z M29 5v8h8"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinejoin="round"
                  />
                  <path d="M24 35V22m0 0l-5 5m5-5l5 5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>

                {selectedFile ? (
                  <>
                    <p className="drop-title selected-file">{selectedFile.name}</p>
                    <p className="drop-sub">{formatSize(selectedFile.size)}</p>
                  </>
                ) : (
                  <>
                    <p className="drop-title">Drop your invoice PDF here</p>
                    <p className="drop-sub">
                      or{" "}
                      <label htmlFor="fileInput" className="browse-link">
                        browse files
                      </label>
                    </p>
                  </>
                )}

                <div className="drop-actions">
                  <button className="btn primary upload-btn" onClick={handleUpload} disabled={uploading || !selectedFile}>
                    {uploading ? "Reading invoice..." : "Upload invoice"}
                  </button>
                  {selectedFile && !uploading && (
                    <label htmlFor="fileInput" className="btn ghost">
                      Choose another
                    </label>
                  )}
                </div>

                <p className="hint">PDF only, up to {MAX_UPLOAD_MB} MB. Text-based invoices work best.</p>
                {uploading && (
                  <p className="hint">The first request can take up to a minute if the server was asleep.</p>
                )}
              </div>
            </div>
          )}
        </section>

        {/* Right: the conversation */}
        <section className="panel chat" aria-label="Questions">
          <div className="panel-head">
            <h2>Questions</h2>
          </div>

          <div className="transcript" ref={transcriptRef} aria-live="polite">
            {history.length === 0 && !asking ? (
              <div className="empty">
                <p className="empty-title">
                  {invoice ? "Your invoice is ready." : "Upload an invoice to get started."}
                </p>
                <p className="empty-sub">Ask about totals, dates, vendors or line items.</p>
                <div className="chips">
                  {SUGGESTIONS.map((text) => (
                    <button
                      key={text}
                      className="chip"
                      disabled={!invoice || asking}
                      onClick={() => handleAskQuestion(text)}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {history.map((item, index) => (
                  <div key={index} className="qa">
                    <p className="qa-question">{item.question}</p>
                    <div className={`answer${item.isError ? " response-error" : ""}`}>
                      <p className="answer-text">{item.answer}</p>
                    </div>
                  </div>
                ))}
                {asking && (
                  <div className="qa" role="status">
                    <p className="qa-question">{pendingQuestion}</p>
                    <div className="answer pending">
                      <span className="dots" aria-hidden="true">
                        <i />
                        <i />
                        <i />
                      </span>
                      <span>Reading the invoice...</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="composer">
            <input
              type="text"
              placeholder={invoice ? "Ask about this invoice..." : "Upload an invoice first"}
              value={question}
              maxLength={500}
              disabled={!invoice}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleQuestionKeyDown}
              aria-label="Your question about the invoice"
            />
            <button className="btn primary ask-btn" onClick={() => handleAskQuestion()} disabled={asking || !invoice || !question.trim()}>
              {asking ? "Asking..." : "Ask"}
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
