"""
Milestone 2 / Activity 2.1 — Generate Comic Story Narration and Dialogue
Uses Gemini Pro (creative, detailed) to expand a panel outline into full
narration + character dialogue.
"""
import os

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel("models/gemini-3.6-flash")
    return _model


def generate_story(panels: list[dict], character_name: str, tone: str) -> dict:
    """
    Expands each panel's scene_description into narration + dialogue.
    Returns a dict keyed by panel_number:
        {1: {"caption": str, "narration": str}, 2: {...}, ...}
    """
    outline_text = "\n".join(
        f"Panel {p['panel_number']}: {p['title']} — {p['scene_description']}"
        for p in panels
    )

    prompt = f"""
You are a comic book writer. The main character is {character_name} and the
story's tone is {tone}. For each panel below, write:
1. A short "Caption" (ambient description of environment/background)
2. A "Narration" (the character's actions, emotions, or dialogue)

Format your answer exactly like this for every panel, one block per panel:

Panel <number>
Caption: <text>
Narration: <text>

Panels:
{outline_text}
"""
    try:
        response = _get_model().generate_content(prompt)
    except ResourceExhausted:
        return _fallback_story(panels)

    text = response.text if hasattr(response, "text") else ""
    return _parse_story(text, panels)


def _fallback_story(panels: list[dict]) -> dict:
    return {
        p["panel_number"]: {
            "caption": p["scene_description"],
            "narration": "",
        }
        for p in panels
    }


def _parse_story(text: str, panels: list[dict]) -> dict:
    story_by_panel = {}
    current_panel = None
    caption, narration = "", ""

    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith("panel"):
            if current_panel is not None:
                story_by_panel[current_panel] = {"caption": caption, "narration": narration}
            digits = "".join(ch for ch in line if ch.isdigit())
            current_panel = int(digits) if digits else None
            caption, narration = "", ""
        elif line.lower().startswith("caption"):
            caption = line.split(":", 1)[-1].strip()
        elif line.lower().startswith("narration"):
            narration = line.split(":", 1)[-1].strip()

    if current_panel is not None:
        story_by_panel[current_panel] = {"caption": caption, "narration": narration}

    # Fallback for any panel Gemini didn't cover
    for p in panels:
        story_by_panel.setdefault(
            p["panel_number"],
            {"caption": p["scene_description"], "narration": ""},
        )

    return story_by_panel
