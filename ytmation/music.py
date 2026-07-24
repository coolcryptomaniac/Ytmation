"""Step 2: turn the lyrics into a real song with Suno.

Uses the unofficial SunoAI client, which authenticates with your suno.com
browser cookie (SUNO_COOKIE secret). Cookies expire every few weeks - if
this step starts failing with auth errors, refresh the secret.
"""

import os

import requests

from . import config


def generate_song(concept: dict) -> str:
    """Generate the song and return the path to the downloaded MP3."""
    if not config.SUNO_COOKIE:
        raise RuntimeError("SUNO_COOKIE is not set - cannot create the song.")

    from suno import ModelVersions, Suno

    client = Suno(cookie=config.SUNO_COOKIE, model_version=ModelVersions.CHIRP_V3_5)

    # In custom mode Suno treats `prompt` as the lyrics and `tags` as the style.
    clips = client.generate(
        prompt=concept["lyrics"],
        is_custom=True,
        tags=f"{concept['genre']}, {concept['mood']}",
        title=concept["title"],
        wait_audio=True,
    )
    if not clips:
        raise RuntimeError("Suno returned no clips.")

    audio_url = clips[0].audio_url
    path = os.path.join(config.OUTPUT_DIR, "song.mp3")
    response = requests.get(audio_url, timeout=300)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)
    print(f"   Song saved to {path} ({os.path.getsize(path) // 1024} KB)")
    return path
