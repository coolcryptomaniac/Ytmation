# Ytmation 🎵

Fully automated daily AI music channel. Every day a GitHub Action:

1. **Writes the song** — Claude (or ChatGPT) generates the title, lyrics,
   Suno style tags, album-cover prompt, video prompt, Shorts hook, and all
   YouTube metadata in one shot.
2. **Creates the music** — Suno turns the lyrics into a real 2–3 minute song.
3. **Designs the album cover** — OpenAI `gpt-image-1` if you have a key,
   otherwise the free Pollinations generator.
4. **Builds two videos** — a 1920×1080 music video and a vertical 1080×1920
   **YouTube Short**. If a `GEMINI_API_KEY` is set, the Short's background is
   an AI clip generated with **Google Veo** (the model behind Flow), looped to
   the music; otherwise the cover art is used.
5. **Uploads both to YouTube** via the YouTube Data API.
6. **Packages the release for distribution** — `song.mp3`, `cover.jpg`,
   `metadata.json`, and a copy-paste `RELEASE.md` are bundled into `dist/`
   and attached to the workflow run as an artifact. Music distributors
   (MusicStudio, DistroKid, TuneCore, …) don't offer public upload APIs, so
   this gives you a one-tap download with everything the release form asks for.

## Setup

Add these in **Settings → Secrets and variables → Actions**:

| Secret | Required | What it is |
|---|---|---|
| `ANTHROPIC_API_KEY` | one of these two | Claude API key ([console.anthropic.com](https://console.anthropic.com)) — used for the concept if present |
| `OPENAI_API_KEY` | ↑ | OpenAI key — concept fallback + album covers |
| `SUNO_COOKIE` | ✅ | Your `suno.com` browser cookie (DevTools → Network → any request → `Cookie` header). Expires every few weeks — refresh it when the Suno step starts failing |
| `YOUTUBE_CLIENT_ID` | ✅ | OAuth client from a Google Cloud project with the **YouTube Data API v3** enabled |
| `YOUTUBE_CLIENT_SECRET` | ✅ | OAuth client secret |
| `YOUTUBE_REFRESH_TOKEN` | ✅ | Refresh token authorized with the `youtube.upload` scope for your channel |
| `GEMINI_API_KEY` | optional | Enables AI video backgrounds for Shorts via Veo ([aistudio.google.com](https://aistudio.google.com)) |

And optionally a repository **variable** `ARTIST_NAME` (defaults to "AI Artist").

### Getting the YouTube refresh token

1. In Google Cloud Console create an OAuth client (type: *Desktop app*) and
   enable **YouTube Data API v3**.
2. Run the [OAuth playground](https://developers.google.com/oauthplayground)
   with your own client credentials, authorize scope
   `https://www.googleapis.com/auth/youtube.upload`, and exchange for tokens.
3. Save the refresh token as the `YOUTUBE_REFRESH_TOKEN` secret.

## Running

- **Automatic:** every day at 08:00 UTC (edit the cron in
  `.github/workflows/daily.yml`).
- **Manual:** Actions tab → *Daily Song Video* → *Run workflow* (works from
  the GitHub mobile app too).
- **Local test without uploading:**

  ```bash
  pip install -r requirements.txt
  SKIP_UPLOAD=1 python script.py
  ```

## Layout

```
script.py               # orchestrator
ytmation/
  concept.py            # step 1: Claude/ChatGPT — lyrics + all prompts + metadata
  music.py              # step 2: Suno song generation
  artwork.py            # step 3: album cover (OpenAI → Pollinations fallback)
  video.py              # step 4: main video + Short (optional Veo background)
  upload.py             # step 5: YouTube upload (video + Short + thumbnail)
  distribute.py         # step 6: release package for your music distributor
  config.py             # all env/config in one place
.github/workflows/daily.yml
```
