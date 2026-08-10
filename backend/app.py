from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from pdf_reader import extract_text_from_pdf
from gemini_service import ask_gemini

app = FastAPI(title="InvoAI API")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

invoice_text = ""


@app.get("/")
def home():
    return {
    "message": "InvoAI Backend is Running!"
}


@app.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    global invoice_text
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text from the uploaded PDF
    text = extract_text_from_pdf(file_path)
    invoice_text = text

    if not text.strip():
        return {
            "message": "No text found in this PDF."
        }

    # Upload successful
    return {
        "message": "File uploaded successfully!",
        "filename": file.filename,
        "text": text
    }

@app.post("/ask")
async def ask_invoice(question: str = Body(..., embed=True)):
    global invoice_text

    if invoice_text == "":
        return {
            "message": "Please upload an invoice first."
        }

    answer = ask_gemini(invoice_text, question)

    return {
        "question": question,
        "answer": answer
    }