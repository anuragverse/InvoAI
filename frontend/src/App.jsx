import { useState } from "react";
import axios from "axios";
import "./App.css";
import invoaiLogo from "./assets/invoai-logo.png";

function App() {
  // -----------------------------
  // State Variables
  // -----------------------------
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const [invoiceText, setInvoiceText] = useState("");

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);

  // -----------------------------
  // Handle File Selection
  // -----------------------------
  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (file) {
      setSelectedFile(file);
      setFileName(file.name);
    }
  };

  // -----------------------------
  // Upload Invoice
  // -----------------------------
  const handleUpload = async () => {
    if (!selectedFile) {
      alert("Please select a PDF file first.");
      return;
    }

    setUploading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/upload",
        formData
      );

      setInvoiceText(response.data.text);

      setUploading(false);

      alert("Invoice uploaded successfully!");
    } catch (error) {
      console.error(error);

      setUploading(false);

      alert(
        "Unable to upload the invoice.\n\nPlease make sure the backend is running."
      );
    }
  };

  // -----------------------------
  // Ask Question
  // -----------------------------
  const handleAskQuestion = async () => {
    if (question.trim() === "") {
      alert("Please enter a question.");
      return;
    }

    setAsking(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/ask",
        {
          question: question,
        }
      );

      setAnswer(response.data.answer);

      setAsking(false);
    } catch (error) {
      console.error(error);

      setAsking(false);

      setAnswer(
        "⚠️ Unable to connect to the server.\n\nPlease make sure the backend is running and try again."
      );
    }
  };

  return (
    <div className="container">

      {/* Header */}
<div className="header">
  <img
    src={invoaiLogo}
    alt="InvoAI - AI-Powered Invoice Analysis"
    className="brand-logo"
  />
</div>

      {/* Upload Card */}
      <div className="card">

        <h2>Upload Invoice</h2>

        <div className="upload-box">

          <p>📄 Drag & Drop your Invoice PDF</p>

          <p>or</p>

          <input
            type="file"
            id="fileInput"
            accept=".pdf"
            hidden
            onChange={handleFileChange}
          />

          <label
            htmlFor="fileInput"
            className="browse-btn"
          >
            Browse Files
          </label>

          {fileName && (
            <p className="selected-file">
              Selected File:
              <br />
              <strong>{fileName}</strong>
            </p>
          )}

        </div>

        <button
          className="upload-btn"
          onClick={handleUpload}
          disabled={uploading}
        >
          {uploading ? "Uploading..." : "Upload Invoice"}
        </button>

      </div>

      {/* Invoice Details */}
      <div className="card">

        <h2>Invoice Details</h2>

        {invoiceText ? (
          <div className="invoice-preview">
            <pre>{invoiceText}</pre>
          </div>
        ) : (
          <p>Upload an invoice to view its details.</p>
        )}

      </div>

      {/* Ask Question */}
      <div className="card">

        <h2>Ask a Question</h2>

        <input
          type="text"
          placeholder="Ask a question about this invoice..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <button
          className="upload-btn"
          onClick={handleAskQuestion}
          disabled={asking}
        >
          {asking ? "Getting Answer..." : "Get Answer"}
        </button>

      </div>

      {/* Response */}
      <div className="card">

        <h2>💬 Response</h2>

        <div className="response-box">

          {answer ? (
            <p>{answer}</p>
          ) : (
            <p>Ask a question to see the response.</p>
          )}

        </div>

      </div>

    </div>
  );
}

export default App;