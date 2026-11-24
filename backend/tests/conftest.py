import os
import sys

# Make `import app` work when pytest runs from the backend folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("CLIENT_URL", "https://invoai.example.com")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
