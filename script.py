
import os
import json
import requests
from moviepy.editor import *
import openai
from suno import Suno, ModelVersions
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ─── 1. Song idea (OpenAI) ──────────────────────────
def generate_idea():
    openai.api_key = os.environ["OPENAI_API_KEY"]
    prompt = """You are a creative song‑writing AI.
    Output a JSON object with keys:
    "title", "genre", "mood", and "lyrics" (the full song text).
    Make it a catchy pop/electronic song, 2-3 minutes long."""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=800
    )
    return json.loads(response.choices[0].message.content)

# ─── 2. Suno music ──────────────────────────────────
def generate_music(lyrics, genre):
    client = Suno(
        cookie=os.environ["SUNO_COOKIE"],
        model_version=ModelVersions.CHIRP_V3_5
    )
    jobs = client.generate(
        prompt=f"{genre} song",
        lyrics=lyrics,
        is_custom=True,
        wait_audio=True
    )
    audio_url = jobs[0].audio_url
    r = requests.get(audio_url)
    with open("song.mp3", "wb") as f:
        f.write(r.content)
    return "song.mp3"

# ─── 3. Cover image (free, no key) ──────────────────
def generate_image(prompt_text):
    url = f"https://image.pollinations.ai/prompt/{prompt_text}?width=1024&height=1024&nologo=true"
    r = requests.get(url)
    with open("cover.jpg", "wb") as f:
        f.write(r.content)
    return "cover.jpg"

# ─── 4. Video assembly ─────────────────────────────
def create_video(audio_path, image_path, lyrics):
    audio = AudioFileClip(audio_path)
    img = ImageClip(image_path).set_duration(audio.duration).resize(height=720)

    # Simple text overlay – first line of lyrics
    first_line = lyrics.strip().split("\n")[0]
    txt = TextClip(first_line, fontsize=45, color='white',
                   stroke_color='black', stroke_width=3)
    txt = txt.set_position(('center', 0.8), relative=True).set_duration(audio.duration)

    final = CompositeVideoClip([img, txt]).set_audio(audio)
    final.write_videofile("output.mp4", fps=24, codec='libx264', audio_codec='aac', logger=None)
    return "output.mp4"

# ─── 5. YouTube upload ─────────────────────────────
def upload_youtube(video_path, title, description, tags):
    creds = Credentials(
        None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"]
    )
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "10"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()

# ─── Main pipeline ─────────────────────────────────
def main():
    print("1/5 Generating song idea ...")
    song = generate_idea()
    print(f"   Title: {song['title']}")

    print("2/5 Creating music with Suno ...")
    audio = generate_music(song["lyrics"], song["genre"])

    print("3/5 Generating cover art ...")
    image = generate_image(f"{song['mood']} digital art, vibrant, abstract")

    print("4/5 Assembling video ...")
    video = create_video(audio, image, song["lyrics"])

    description = (
        f"Daily AI song: {song['title']}\n\n"
        f"Genre: {song['genre']}\n"
        f"Mood: {song['mood']}\n\n"
        f"#AIMusic #SunoAI"
    )
    print("5/5 Uploading to YouTube ...")
    upload_youtube(
        video,
        f"{song['title']} (AI Music Video)",
        description,
        ["AI music", "Suno", song["genre"]]
    )
    print("Done! Check your YouTube channel.")

if __name__ == "__main__":
    main()
