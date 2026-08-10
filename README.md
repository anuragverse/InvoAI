# InvoAI

InvoAI is an AI-powered invoice analysis application that allows users to upload invoice PDFs, extract invoice information, and ask questions about their invoices using Google Gemini AI.

## Features

- Upload invoice PDFs
- Extract invoice information
- Ask questions about invoices
- AI-powered answers using Google Gemini
- React frontend
- FastAPI backend
- PDF text extraction using PyMuPDF

## Tech Stack

### Frontend
- React.js
- Vite
- Axios
- CSS

### Backend
- Python
- FastAPI
- Uvicorn
- PyMuPDF
- Google Gemini API

---

# Installation

Follow these steps to run InvoAI on your computer.

## Requirements

Install these before starting:

- Python
- Node.js
- Git
- Google Gemini API Key

---

## 1. Clone the Project

Open a terminal and run:

```bash
git clone https://github.com/anuragverse/InvoAI.git

Then:

cd InvoAI
Backend Setup
2. Open the Backend Folder
cd backend
3. Create a Virtual Environment
python -m venv venv
4. Activate the Virtual Environment
Windows PowerShell
.\venv\Scripts\Activate.ps1
Windows CMD
venv\Scripts\activate
macOS / Linux
source venv/bin/activate

You should see (venv) in your terminal after activation.

5. Install Dependencies
pip install -r requirements.txt
6. Add Your Gemini API Key

Create a file named:

.env

inside the backend folder.

Add:

GEMINI_API_KEY=YOUR_GEMINI_API_KEY

Replace YOUR_GEMINI_API_KEY with your actual Gemini API key.

Do not upload your .env file to GitHub.

7. Start the Backend

Run:

python -m uvicorn app:app --reload

The backend will run at:

http://127.0.0.1:8000
Frontend Setup
8. Open a New Terminal

Keep the backend running.

Open another terminal and go to the project folder:

cd InvoAI/frontend
9. Install Frontend Dependencies
npm install
10. Start the Frontend
npm run dev

The frontend will run at:

http://localhost:5173
Run InvoAI

You need two terminals running at the same time.

Terminal 1 - Backend
cd InvoAI/backend

Activate the virtual environment:

.\venv\Scripts\Activate.ps1

Start the backend:

python -m uvicorn app:app --reload
Terminal 2 - Frontend
cd InvoAI/frontend

Start the frontend:

npm run dev

Then open:

http://localhost:5173

How to Use
Open InvoAI in your browser.
Upload an invoice PDF.
Wait for the invoice information to be extracted.
Ask a question about the invoice.
InvoAI uses Gemini AI to generate the answer.

Project Structure
InvoAI/
│
├── backend/
│   ├── app.py
│   ├── gemini_service.py
│   ├── pdf_reader.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md