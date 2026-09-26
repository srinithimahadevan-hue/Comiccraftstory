"""
Milestone 2 / Activity 2.1 — Export Comic Panel and Story into PDF
Compiles the full comic layout into a multi-page PDF using FPDF.
"""
import datetime
import os
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
EXPORTS_DIR = STATIC_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _configure_font(pdf: FPDF) -> tuple[str, bool]:
    """Use an embedded Unicode font when one is available on the host."""
    font_dir = Path(os.getenv("COMIC_FONT_DIR", r"C:\Windows\Fonts"))
    font_files = {
        "": font_dir / "segoeui.ttf",
        "B": font_dir / "segoeuib.ttf",
        "I": font_dir / "segoeuii.ttf",
    }
    if all(path.exists() for path in font_files.values()):
        for style, path in font_files.items():
            pdf.add_font("ComicCraft", style, str(path))
        return "ComicCraft", True
    return "Helvetica", False


def _pdf_text(value: str, unicode_font: bool) -> str:
    if unicode_font:
        return value
    replacements = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"}
    return value.translate(str.maketrans(replacements))


def save_pdf(layout: list[dict], title: str = "ComicCraft Story") -> str:
    """
    Writes one page per panel (image + narration text) and saves the PDF
    with a timestamped filename under static/exports/.
    Returns the path relative to /static, e.g. "exports/comic_20260924.pdf".
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    font_family, unicode_font = _configure_font(pdf)

    for panel in layout:
        pdf.add_page()
        pdf.set_font(font_family, "B", 16)
        pdf.multi_cell(0, 10, _pdf_text(f"Panel {panel['panel_number']}: {panel['title']}", unicode_font),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        image_path = STATIC_DIR / panel["image_path"] if panel["image_path"] else None
        if image_path and image_path.exists():
            pdf.image(str(image_path), x=15, w=180)
            pdf.set_x(pdf.l_margin)
            pdf.ln(4)

        pdf.set_font(font_family, "I", 11)
        if panel.get("scene_description"):
            pdf.multi_cell(0, 7, _pdf_text(panel["scene_description"], unicode_font),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

        pdf.set_font(font_family, "", 11)
        if panel.get("caption"):
            pdf.multi_cell(0, 7, _pdf_text(f"Caption: {panel['caption']}", unicode_font),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if panel.get("narration"):
            pdf.multi_cell(0, 7, _pdf_text(f"Narration: {panel['narration']}", unicode_font),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    out_path = EXPORTS_DIR / filename
    pdf.output(str(out_path))

    return f"exports/{filename}"
