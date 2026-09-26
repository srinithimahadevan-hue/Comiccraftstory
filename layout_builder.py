"""
Milestone 2 / Activity 2.1 — Organize Comic Panels into Layout Structure
Combines outline + story + generated images into one ordered list ready for
the frontend template and the PDF exporter.
"""


def build_comic_layout(panels: list[dict], story_by_panel: dict,
                        image_paths: dict) -> list[dict]:
    """
    panels:         output of gemini_flash.generate_outline()
    story_by_panel: output of gemini_pro.generate_story() -> {panel_number: {...}}
    image_paths:    {panel_number: "panels/xxx.png"}

    Returns a list of dicts, one per panel, each containing everything the
    templates and PDF exporter need:
        panel_number, title, scene_description, image_prompt,
        image_path, caption, narration
    """
    layout = []
    for panel in sorted(panels, key=lambda p: p["panel_number"]):
        num = panel["panel_number"]
        story = story_by_panel.get(num, {"caption": "", "narration": ""})
        layout.append(
            {
                "panel_number": num,
                "title": panel.get("title", f"Panel {num}"),
                "scene_description": panel.get("scene_description", ""),
                "image_prompt": panel.get("image_prompt", ""),
                "image_path": image_paths.get(num, ""),
                "caption": story.get("caption", ""),
                "narration": story.get("narration", ""),
            }
        )
    return layout
