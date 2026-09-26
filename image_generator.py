"""
Milestone 2 / Activity 2.1 — Generate Comic Illustrations from Prompts
Uses Hugging Face Diffusers (Stable Diffusion) to turn an image prompt into
a comic-style panel illustration.

Loading the real Stable Diffusion pipeline needs a GPU (or a lot of patience
on CPU) and downloads several GB of weights the first time it runs, so this
module loads it lazily — the app still starts instantly, and only pays that
cost the first time /generate (or /test-image) is actually called.

If diffusers/torch aren't installed, or no GPU/HF token is available, it
falls back to drawing a simple placeholder panel with Pillow so the rest of
the pipeline (layout + PDF export) can still be exercised end to end.
"""
import logging
import os
import re
import textwrap
import uuid
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "panels"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

HF_API_KEY = os.getenv("HF_API_KEY")

_pipe = None
logger = logging.getLogger(__name__)


def _sanitize_filename(prompt: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt.strip().lower())[:40].strip("_")
    return f"{slug or 'panel'}_{uuid.uuid4().hex[:8]}.png"


def _load_pipeline():
    """Lazily import torch/diffusers and build the Stable Diffusion pipeline."""
    global _pipe
    if _pipe is not None:
        return _pipe

    import torch
    from diffusers import DDIMScheduler, StableDiffusionPipeline

    model_id = "runwayml/stable-diffusion-v1-5"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    pipe = StableDiffusionPipeline.from_pretrained(
        model_id, torch_dtype=dtype, use_auth_token=HF_API_KEY
    )
    pipe = pipe.to(device)
    if device == "cpu":
        pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
    _pipe = pipe
    return _pipe


def _placeholder_image(prompt: str, out_path: Path) -> None:
    """Draws a simple placeholder panel when Stable Diffusion isn't available."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (512, 512), color=(235, 235, 245))
    draw = ImageDraw.Draw(img)
    wrapped = textwrap.fill(prompt, width=36)
    draw.rectangle([8, 8, 503, 503], outline=(60, 60, 90), width=4)
    draw.text((24, 24), "Placeholder panel\n(Stable Diffusion not configured)",
              fill=(40, 40, 60))
    draw.text((24, 90), wrapped, fill=(20, 20, 30))
    img.save(out_path)


def generate_image(image_prompt: str) -> str:
    """
    Generates one comic panel image from a text prompt.
    Returns a path relative to /static, e.g. "panels/xxx.png", for use in
    <img src="/static/{path}"> and in the PDF exporter.
    """
    filename = _sanitize_filename(image_prompt)
    out_path = STATIC_DIR / filename

    try:
        import torch

        cpu_generation_enabled = os.getenv(
            "ENABLE_CPU_IMAGE_GENERATION", "false"
        ).lower() in {"1", "true", "yes"}
        if not torch.cuda.is_available() and not cpu_generation_enabled:
            logger.info(
                "Using placeholder image because CUDA is unavailable. "
                "Set ENABLE_CPU_IMAGE_GENERATION=true to enable slow CPU rendering."
            )
            _placeholder_image(image_prompt, out_path)
            return f"panels/{filename}"

        pipe = _load_pipeline()
        steps = int(os.getenv("IMAGE_STEPS", "30" if pipe.device.type == "cuda" else "2"))
        image = pipe(image_prompt, num_inference_steps=steps, guidance_scale=7.5).images[0]
        image.save(out_path)
    except Exception:
        # No GPU, no internet to fetch weights, diffusers missing, etc.
        logger.exception("Stable Diffusion failed for image prompt: %s", image_prompt)
        _placeholder_image(image_prompt, out_path)

    return f"panels/{filename}"
