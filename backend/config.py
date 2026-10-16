import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = "../pdfs"
MAX_FILE_SIZE_MB = 5
ALLOWED_EXTENSIONS = [".pdf"]

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

os.makedirs(UPLOAD_DIR, exist_ok=True)