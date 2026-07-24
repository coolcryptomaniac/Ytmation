import os

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "out")
DIST_DIR = os.environ.get("DIST_DIR", "dist")

ARTIST_NAME = os.environ.get("ARTIST_NAME", "AI Artist")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SUNO_COOKIE = os.environ.get("SUNO_COOKIE", "")

YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
VEO_MODEL = os.environ.get("VEO_MODEL", "veo-3.0-generate-001")

# Set SKIP_UPLOAD=1 to run the whole pipeline without touching YouTube.
SKIP_UPLOAD = os.environ.get("SKIP_UPLOAD", "") == "1"

# Max length of the Short in seconds (YouTube Shorts limit is 60s).
SHORT_MAX_SECONDS = int(os.environ.get("SHORT_MAX_SECONDS", "58"))


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
