"""Step 5: upload the main video and the Short to YouTube."""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from . import config


def _client():
    for name in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"):
        if not getattr(config, name):
            raise RuntimeError(f"{name} is not set - cannot upload to YouTube.")
    credentials = Credentials(
        None,
        refresh_token=config.YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YOUTUBE_CLIENT_ID,
        client_secret=config.YOUTUBE_CLIENT_SECRET,
    )
    return build("youtube", "v3", credentials=credentials)


def _upload(youtube, video_path: str, title: str, description: str, tags: list) -> str:
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:30],
            "categoryId": "10",  # Music
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]


def upload_all(video_path: str, short_path: str, cover_path: str, concept: dict) -> dict:
    youtube = _client()
    links = {}

    video_id = _upload(
        youtube, video_path,
        f"{concept['title']} - {config.ARTIST_NAME} (Official AI Music Video)",
        concept["description"] + "\n\nCreated end-to-end with AI.",
        list(concept["tags"]),
    )
    links["video"] = f"https://youtu.be/{video_id}"
    print(f"   Main video: {links['video']}")

    try:  # custom thumbnail needs a verified channel; best-effort only
        youtube.thumbnails().set(
            videoId=video_id, media_body=MediaFileUpload(cover_path)
        ).execute()
    except Exception as exc:
        print(f"   Thumbnail not set ({exc})")

    short_id = _upload(
        youtube, short_path,
        f"{concept['shorts_hook']} #Shorts"[:100],
        f"{concept['title']} - {config.ARTIST_NAME}\n\n"
        f"Full video: {links['video']}\n\n{concept['description']}\n#Shorts",
        list(concept["tags"]) + ["shorts"],
    )
    links["short"] = f"https://youtu.be/{short_id}"
    print(f"   Short: {links['short']}")
    return links
