"""
Milestone 3 — routes.py Development
All ComicCraft routes: page rendering, comic generation (form + JSON), and
export/test utilities.
"""
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.schemas import PromptRequest

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


def _run_pipeline(story_prompt: str, character_name: str, setting: str,
                   tone: str, art_style: str) -> list[dict]:
    """Shared pipeline used by both the form route and the JSON API route."""
    panels = generate_outline(story_prompt, character_name, setting, tone, art_style)
    story_by_panel = generate_story(panels, character_name, tone)

    image_paths = {}
    for panel in panels:
        image_paths[panel["panel_number"]] = generate_image(panel["image_prompt"])

    layout = build_comic_layout(panels, story_by_panel, image_paths)
    return layout


@router.get("/")
def homepage(request: Request):
    """Loads the homepage where users submit their story details."""
    return templates.TemplateResponse(request, "index.html")


@router.api_route("/generate", methods=["GET", "POST"])
def generate_comic_form(
    request: Request,
    story_prompt: str = Form(default=""),
    character_name: str = Form(default=""),
    setting: str = Form(default=""),
    tone: str = Form(default=""),
    art_style: str = Form(default=""),
):
    """Handles the HTML form page load and the comic preview generation POST."""
    if request.method == "GET":
        return templates.TemplateResponse(request, "index.html")

    if not story_prompt or not character_name:
        raise HTTPException(status_code=400, detail="Story prompt and character name are required.")

    try:
        layout = _run_pipeline(story_prompt, character_name, setting, tone, art_style)
        pdf_path = save_pdf(layout, title=story_prompt)
    except Exception as exc:  # pragma: no cover - defensive, surfaced to user
        raise HTTPException(status_code=500, detail=f"Comic generation failed: {exc}")

    return templates.TemplateResponse(
        request,
        "comic_preview.html",
        {"layout": layout, "pdf_path": pdf_path},
    )


@router.post("/generate-comic/json")
def generate_comic_json(payload: PromptRequest):
    """API route: accepts JSON, returns layout data + generated PDF path."""
    try:
        layout = _run_pipeline(
            payload.story_prompt,
            payload.character_name,
            payload.setting,
            payload.tone,
            payload.art_style,
        )
        pdf_path = save_pdf(layout, title=payload.story_prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Comic generation failed: {exc}")

    return JSONResponse({"layout": layout, "pdf_path": pdf_path})


@router.get("/export-success")
def export_success(request: Request, pdf_path: str = ""):
    """Displays a success confirmation page after the comic is downloaded."""
    return templates.TemplateResponse(
        request, "export_success.html", {"pdf_path": pdf_path}
    )


@router.post("/test-image")
def test_image(prompt: str = Form(...)):
    """Developer utility: test image generation from a direct prompt."""
    image_path = generate_image(prompt)
    return JSONResponse({"image_path": image_path})
