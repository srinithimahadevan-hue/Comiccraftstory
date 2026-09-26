"""
Milestone 2 / Activity 2.1 — Generate Structured Comic Panel Outline
Uses Gemini Flash (fast, structured output) to break a story prompt into
a 5-panel comic outline.
"""
import json
import os
import re

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


def _extract_json(text: str):
    """Gemini sometimes wraps JSON in ```json fences — strip them."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)


def _fallback_outline(story_prompt: str, character_name: str, setting: str,
                      tone: str, art_style: str, num_panels: int) -> list[dict]:
    fallback_scenes = [
        f"{character_name} begins the adventure in {setting}, following a clue connected to the story.",
        f"A new obstacle appears, and {character_name} must decide how to move forward.",
        f"{character_name} discovers an important detail that changes the direction of the adventure.",
        f"The main challenge reaches its peak as {character_name} uses courage and creativity.",
        f"{character_name} resolves the conflict and returns to {setting} with a hopeful new beginning.",
    ]
    return [
        {
            "panel_number": i + 1,
            "title": f"Panel {i + 1}",
            "scene_description": fallback_scenes[i % len(fallback_scenes)],
            "image_prompt": f"{art_style} style illustration, {setting}, "
                             f"{character_name}, {fallback_scenes[i % len(fallback_scenes)]}, {tone} mood",
        }
        for i in range(num_panels)
    ]


def generate_outline(story_prompt: str, character_name: str, setting: str,
                      tone: str, art_style: str, num_panels: int = 5) -> list[dict]:
    """
    Returns a list of dicts, one per panel:
        {"panel_number": int, "title": str, "scene_description": str,
         "image_prompt": str}
    """
    prompt = f"""
You are a comic book editor. Break the following idea into exactly {num_panels}
comic panels. Respond ONLY with a JSON array (no markdown, no commentary).

Each array item must be an object with keys:
- "panel_number" (integer, starting at 1)
- "title" (short punchy panel title)
- "scene_description" (1-2 sentences describing what happens)
- "image_prompt" (a detailed visual prompt suitable for an image generator,
   written in the "{art_style}" art style)

Story prompt: {story_prompt}
Main character: {character_name}
Setting: {setting}
Tone: {tone}
Art style: {art_style}
"""
    try:
        response = _get_model().generate_content(prompt)
    except ResourceExhausted:
        return _fallback_outline(
            story_prompt, character_name, setting, tone, art_style, num_panels
        )

    try:
        panels = _extract_json(response.text)
    except (json.JSONDecodeError, AttributeError, ValueError):
        panels = _fallback_outline(
            story_prompt, character_name, setting, tone, art_style, num_panels
        )
    return panels
