"""Ytmation daily pipeline.

Concept (Claude/ChatGPT) -> Suno song -> cover art -> video + Short
-> YouTube upload -> distribution-ready release package.

Run:  python script.py            (full run)
      SKIP_UPLOAD=1 python script.py   (everything except YouTube)
"""

import json
import os
import sys

from ytmation import artwork, concept, config, distribute, music, upload, video


def main():
    config.ensure_dirs()

    print("1/6 Generating song concept (script + prompts) ...")
    idea = concept.generate_concept()
    print(f"    Title: {idea['title']}  |  Genre: {idea['genre']}")
    with open(os.path.join(config.OUTPUT_DIR, "concept.json"), "w") as f:
        json.dump(idea, f, indent=2)

    print("2/6 Creating song with Suno ...")
    song_path = music.generate_song(idea)

    print("3/6 Generating album cover ...")
    cover_path = artwork.generate_cover(idea)

    print("4/6 Assembling main video (16:9) and Short (9:16) ...")
    video_path = video.create_main_video(song_path, cover_path, idea)
    short_path = video.create_short(song_path, cover_path, idea)

    links = {}
    if config.SKIP_UPLOAD:
        print("5/6 SKIP_UPLOAD=1 - skipping YouTube upload")
    else:
        print("5/6 Uploading to YouTube ...")
        links = upload.upload_all(video_path, short_path, cover_path, idea)

    print("6/6 Packaging release for distribution ...")
    distribute.package_release(song_path, cover_path, idea, links)

    print("Done!")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        raise
