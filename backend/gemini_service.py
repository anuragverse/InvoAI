import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def ask_gemini(text, question):
    prompt = f"""
You are an AI Invoice Assistant.

Answer ONLY using the information present in the invoice.

If the answer is not available in the invoice,
reply with:

"Information not found in the uploaded invoice."

Invoice Content:

{text}

User Question:

{question}

Give a clear and concise answer.
"""

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:

     error = str(e)

    if "429" in error:
        return (
            "⚠️ AI service is temporarily unavailable.\n\n"
            "The Gemini API quota has been exceeded.\n"
            "Please try again later or use another API key."
        )

    return (
        "⚠️ Unable to process your request at the moment.\n"
        "Please try again later."
    )