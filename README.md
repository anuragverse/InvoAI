# InvoAI

InvoAI is an AI-powered invoice analysis web application that allows users to upload invoice PDFs, extract invoice details, and ask natural language questions about the uploaded invoice using Google's Gemini AI.

The application combines a FastAPI backend with a React frontend to provide a clean, interactive interface for invoice analysis.

---

## Features

* Upload invoice PDF documents
* Extract text from uploaded invoices
* Display extracted invoice details
* Ask questions about the uploaded invoice
* AI-powered responses using Gemini API
* Modern and responsive user interface
* FastAPI REST API backend
* React + Vite frontend

---

## Technologies Used

### Frontend

* React.js
* Vite
* Axios
* CSS3

### Backend

* FastAPI
* Python
* Uvicorn
* PyMuPDF (PDF text extraction)
* Google Gemini API

---

## Project Structure

```
InvoAI/
│
├── backend/
│   ├── app.py
│   ├── gemini_service.py
│   ├── pdf_reader.py
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone 
cd InvoAI
```

---

### 2. Backend Setup

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn app:app --reload
```

---

### 3. Frontend Setup

Open a new terminal.

```bash
cd frontend

npm install

npm run dev
```

---

## Environment Variables

Create a `.env` file inside the `backend` folder.

```
GEMINI_API_KEY=YOUR_API_KEY
```

---

## API Endpoints

| Method | Endpoint  | Description                               |
| ------ | --------- | ----------------------------------------- |
| GET    | `/`       | Backend status                            |
| POST   | `/upload` | Upload an invoice PDF                     |
| POST   | `/ask`    | Ask a question about the uploaded invoice |

## Future Improvements

* Support multiple invoice formats
* Invoice history
* Download analysis reports
* User authentication
* OCR support for scanned invoices
* Dark mode
* Invoice summary dashboard
