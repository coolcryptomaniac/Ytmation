"""Step 6: package the release for music distribution.

Music distributors (MusicStudio, DistroKid, TuneCore, ...) have no public
upload API, so this step assembles everything a release form asks for into
dist/<date>-<slug>/ - the GitHub Action attaches it as a downloadable
artifact so you can submit it to your distributor in one sitting:

  song.mp3        the master audio from Suno
  cover.jpg       3000px-ready square artwork
  metadata.json   title, artist, genre, lyrics, YouTube links
  RELEASE.md      human-readable copy-paste sheet
"""

import datetime
import json
import os
import re
import shutil

from . import config


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "release"


def package_release(song_path: str, cover_path: str, concept: dict, links: dict) -> str:
    today = datetime.date.today().isoformat()
    folder = os.path.join(config.DIST_DIR, f"{today}-{_slug(concept['title'])}")
    os.makedirs(folder, exist_ok=True)

    shutil.copy(song_path, os.path.join(folder, "song.mp3"))
    shutil.copy(cover_path, os.path.join(folder, "cover.jpg"))

    metadata = {
        "title": concept["title"],
        "artist": config.ARTIST_NAME,
        "genre": concept["genre"],
        "mood": concept["mood"],
        "release_date": today,
        "lyrics": concept["lyrics"],
        "explicit": False,
        "language": "en",
        "youtube": links,
    }
    with open(os.path.join(folder, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(folder, "RELEASE.md"), "w") as f:
        f.write(
            f"# {concept['title']}\n\n"
            f"- **Artist:** {config.ARTIST_NAME}\n"
            f"- **Genre:** {concept['genre']}\n"
            f"- **Release date:** {today}\n"
            f"- **YouTube:** {links.get('video', 'n/a')}\n"
            f"- **Short:** {links.get('short', 'n/a')}\n\n"
            "## Distributor checklist\n\n"
            "1. Log in to your distributor (MusicStudio / DistroKid / TuneCore).\n"
            "2. Upload `song.mp3` and `cover.jpg`.\n"
            "3. Copy the metadata below into the release form.\n\n"
            f"## Lyrics\n\n```\n{concept['lyrics']}\n```\n"
        )

    print(f"   Release package ready: {folder}")
    return folder
