"""
ComicCraft - AI Comic Story Creator using Gemini Models
Application entry point.

Run with:
    uvicorn app.main:app --reload
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()  # loads GEMINI_API_KEY / HF_API_KEY from a .env file if present

from app.routes import router  # noqa: E402  (import after load_dotenv on purpose)

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="ComicCraft",
    description="AI Comic Story Creator using Gemini Models + Stable Diffusion",
    version="1.0.0",
)

# Serve generated panel images / exported PDFs
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# All page + API routes live in routes.py
app.include_router(router)
