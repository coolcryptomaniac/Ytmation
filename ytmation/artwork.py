"""Step 3: album cover art.

Tries OpenAI image generation first (if OPENAI_API_KEY is set), then falls
back to the free Pollinations endpoint which needs no API key.
"""

import base64
import os
import urllib.parse

import requests

from . import config

COVER_SIZE = 1024


def _openai_cover(prompt: str, path: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=f"{COVER_SIZE}x{COVER_SIZE}",
    )
    image = result.data[0]
    if getattr(image, "b64_json", None):
        data = base64.b64decode(image.b64_json)
    else:
        data = requests.get(image.url, timeout=120).content
    with open(path, "wb") as f:
        f.write(data)
    return path


def _pollinations_cover(prompt: str, path: str) -> str:
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt)
        + f"?width={COVER_SIZE}&height={COVER_SIZE}&nologo=true"
    )
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)
    return path


def generate_cover(concept: dict) -> str:
    """Generate the album cover and return the JPEG/PNG path."""
    prompt = (
        f"{concept['cover_prompt']}. Album cover art, square composition, "
        "high detail, no text, no words, no lettering."
    )
    path = os.path.join(config.OUTPUT_DIR, "cover.jpg")

    if config.OPENAI_API_KEY:
        try:
            _openai_cover(prompt, path)
            print("   Cover generated with OpenAI gpt-image-1")
            return path
        except Exception as exc:  # fall back to the free generator
            print(f"   OpenAI image failed ({exc}); falling back to Pollinations")

    _pollinations_cover(prompt, path)
    print("   Cover generated with Pollinations (free)")
    return path
