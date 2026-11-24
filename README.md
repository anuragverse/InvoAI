# InvoAI

InvoAI is an AI-powered invoice analysis application that allows users to upload invoice PDFs, extract invoice information, and ask questions about their invoices using Google Gemini AI.

---

## Tech Stack

### Frontend

* React.js
* Vite
* JavaScript
* CSS

### Backend

* Python
* FastAPI
* Uvicorn
* PyPDF2
* Google Gemini API (`google-genai` SDK)
* PyMuPDF for PDF text extraction


---

## Project Structure

```text
InvoAI/
│
├── backend/
│   ├── app.py
│   ├── gemini_service.py
│   ├── pdf_reader.py
│   ├── store.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env            (you create this)
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
└── README.md
```

---

# Prerequisites

Before running InvoAI, make sure the following software is installed on your system:

* Python
* Node.js
* npm
* Git


---

# Installation and Setup

## 1. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/anuragverse/InvoAI.git
```

Move into the project directory:

```bash
cd InvoAI
```

---

# Backend Setup

## 2. Open the Backend Folder

```bash
cd backend
```

## 3. Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv venv
```

## 4. Activate the Virtual Environment

### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

After activation, `(venv)` should appear at the beginning of your terminal prompt.

---

## 5. Install Backend Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

## 6. Configure the Gemini API Key

InvoAI uses Google Gemini AI to analyze invoice information and answer questions.

Create a `.env` file inside the `backend` folder.

The backend directory should look similar to:

```text
backend/
├── app.py
├── gemini_service.py
├── pdf_reader.py
├── store.py
├── requirements.txt
└── .env
```

Add the following to the `.env` file:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Replace `YOUR_GEMINI_API_KEY` with your actual Google Gemini API key.

---

## 7. Start the Backend

Make sure you are inside the `backend` directory and the virtual environment is activated.

Run:

```bash
python -m uvicorn app:app --reload
```

The backend starts at `http://127.0.0.1:8000`. Interactive API docs are at `http://127.0.0.1:8000/docs`.

---

# Frontend Setup

## 8. Open a New Terminal

Keep the backend terminal running.

Open a second terminal and navigate to the frontend directory:

```bash
cd InvoAI/frontend
```

---

## 9. Install Frontend Dependencies

Install the required Node.js packages:

```bash
npm install
```

---

## 10. Start the Frontend

Run the development server:

```bash
npm run dev
```

The frontend will normally start at:

```text
http://localhost:5173
```

Open this URL in your browser.


# How to Use

1. Open:

   ```text
   http://localhost:5173
   ```

2. Upload an invoice PDF.

3. Wait for InvoAI to process and extract the invoice information.

4. Enter a question related to the uploaded invoice.

5. Submit the question.

6. InvoAI processes the invoice information and sends the relevant data to Google Gemini.

7. Gemini analyzes the information and generates an answer.

8. The generated answer is displayed in the application.

---

---
# Author

**Anurag**

GitHub:
https://github.com/anuragverse

Project Repository:
https://github.com/anuragverse/InvoAI
