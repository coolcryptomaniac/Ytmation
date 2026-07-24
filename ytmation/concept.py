"""Step 1: generate the full creative concept with Claude (preferred) or ChatGPT.

One LLM call produces everything downstream steps need: lyrics, Suno style
tags, the album-cover image prompt, the Veo video prompt, YouTube metadata
and the Shorts hook line.
"""

import json
import re

from . import config

CONCEPT_PROMPT = """You are a hit songwriter and music-video creative director.
Invent today's release for an AI music channel and answer with a single JSON
object (no markdown fences, no commentary) with exactly these keys:

- "title": catchy song title, max 60 characters
- "genre": short style description usable as Suno style tags,
  e.g. "dreamy synthwave, female vocals, 110 bpm"
- "mood": 2-4 words describing the mood
- "lyrics": full lyrics with [Verse], [Chorus], [Bridge] section tags,
  under 2500 characters, structured for a 2-3 minute song
- "cover_prompt": a rich text-to-image prompt for the album cover
  (subject, style, lighting, color palette; no text or lettering in the image)
- "video_prompt": a cinematic text-to-video prompt for a looping background
  visual matching the song (describe motion, camera, atmosphere)
- "shorts_hook": one punchy line (max 50 chars) to overlay on a YouTube Short
- "description": YouTube video description, 2-4 sentences plus 3-5 hashtags
- "tags": array of 8-12 YouTube tag strings

Make the song genuinely catchy and current. Vary genres day to day."""


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in LLM response: {text[:200]}")
    return json.loads(text[start : end + 1])


def _concept_claude() -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": CONCEPT_PROMPT}],
    )
    return _parse_json(message.content[0].text)


def _concept_chatgpt() -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": CONCEPT_PROMPT}],
        response_format={"type": "json_object"},
        max_tokens=3000,
    )
    return _parse_json(response.choices[0].message.content)


REQUIRED_KEYS = [
    "title", "genre", "mood", "lyrics", "cover_prompt",
    "video_prompt", "shorts_hook", "description", "tags",
]


def generate_concept() -> dict:
    if config.ANTHROPIC_API_KEY:
        concept = _concept_claude()
    elif config.OPENAI_API_KEY:
        concept = _concept_chatgpt()
    else:
        raise RuntimeError(
            "Set ANTHROPIC_API_KEY (Claude) or OPENAI_API_KEY (ChatGPT) "
            "to generate the song concept."
        )

    missing = [k for k in REQUIRED_KEYS if not concept.get(k)]
    if missing:
        raise ValueError(f"Concept is missing keys: {missing}")
    if isinstance(concept["tags"], str):
        concept["tags"] = [t.strip() for t in concept["tags"].split(",") if t.strip()]
    return concept
