"""Step 4: assemble the videos.

- Main video: 1920x1080 - blurred cover backdrop, centered cover, title text.
- Short: 1080x1920 vertical, first ~58s of the song, hook text overlay.
  If GEMINI_API_KEY is set, an AI background clip is generated with Google
  Veo (the model behind Flow) and looped behind the Short; otherwise the
  Short uses the cover art.

All text is drawn with Pillow so ImageMagick is not required.
"""

import os
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import config

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _font(size: int):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_text(draw: ImageDraw.ImageDraw, xy, text: str, font, max_width: int):
    """Draw centered, outlined text, wrapping if it exceeds max_width."""
    words, lines, current = text.split(), [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    x, y = xy
    line_height = int(font.size * 1.25)
    for i, line in enumerate(lines):
        width = draw.textlength(line, font=font)
        pos = (x - width / 2, y + i * line_height)
        draw.text(pos, line, font=font, fill="white",
                  stroke_width=max(2, font.size // 15), stroke_fill="black")


def _frame_landscape(cover_path: str, title: str, artist: str, path: str):
    """1920x1080 frame: blurred cover backdrop + centered cover + title."""
    W, H = 1920, 1080
    cover = Image.open(cover_path).convert("RGB")

    backdrop = cover.resize((W, W)).crop((0, (W - H) // 2, W, (W - H) // 2 + H))
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(30))
    backdrop = Image.eval(backdrop, lambda px: int(px * 0.5))

    art = cover.resize((720, 720))
    backdrop.paste(art, ((W - 720) // 2, 100))

    draw = ImageDraw.Draw(backdrop)
    _draw_text(draw, (W // 2, 860), title, _font(64), W - 300)
    _draw_text(draw, (W // 2, 960), artist, _font(40), W - 300)
    backdrop.save(path, quality=92)
    return path


def _frame_portrait(cover_path: str, hook: str, title: str, path: str):
    """1080x1920 frame for the Short."""
    W, H = 1080, 1920
    cover = Image.open(cover_path).convert("RGB")

    backdrop = cover.resize((H, H)).crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(30))
    backdrop = Image.eval(backdrop, lambda px: int(px * 0.5))

    art = cover.resize((900, 900))
    backdrop.paste(art, ((W - 900) // 2, (H - 900) // 2))

    draw = ImageDraw.Draw(backdrop)
    _draw_text(draw, (W // 2, 220), hook, _font(72), W - 120)
    _draw_text(draw, (W // 2, 1560), title, _font(52), W - 120)
    backdrop.save(path, quality=92)
    return path


def _veo_clip(prompt: str, path: str, aspect_ratio: str) -> str | None:
    """Generate a background clip with Google Veo. Returns None on any failure."""
    if not config.GEMINI_API_KEY:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        operation = client.models.generate_videos(
            model=config.VEO_MODEL,
            prompt=prompt,
            config=types.GenerateVideosConfig(aspect_ratio=aspect_ratio),
        )
        deadline = time.time() + 480
        while not operation.done:
            if time.time() > deadline:
                raise TimeoutError("Veo generation timed out")
            time.sleep(15)
            operation = client.operations.get(operation)

        video = operation.response.generated_videos[0]
        client.files.download(file=video.video)
        video.video.save(path)
        print(f"   Veo background clip saved to {path}")
        return path
    except Exception as exc:
        print(f"   Veo unavailable ({exc}); using cover art instead")
        return None


def create_main_video(audio_path: str, cover_path: str, concept: dict) -> str:
    from moviepy import AudioFileClip, ImageClip

    frame = _frame_landscape(
        cover_path, concept["title"], config.ARTIST_NAME,
        os.path.join(config.OUTPUT_DIR, "frame_main.jpg"),
    )
    audio = AudioFileClip(audio_path)
    clip = ImageClip(frame).with_duration(audio.duration).with_audio(audio)

    path = os.path.join(config.OUTPUT_DIR, "video.mp4")
    clip.write_videofile(path, fps=24, codec="libx264", audio_codec="aac", logger=None)
    audio.close()
    return path


def create_short(audio_path: str, cover_path: str, concept: dict) -> str:
    from moviepy import (AudioFileClip, CompositeVideoClip, ImageClip,
                         VideoFileClip, vfx)

    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, config.SHORT_MAX_SECONDS)
    audio_cut = audio.subclipped(0, duration)

    veo_path = _veo_clip(
        f"{concept['video_prompt']}, vertical 9:16 format, seamless loop",
        os.path.join(config.OUTPUT_DIR, "veo_clip.mp4"),
        aspect_ratio="9:16",
    )

    if veo_path and os.path.exists(veo_path):
        base = VideoFileClip(veo_path).with_effects([vfx.Loop(duration=duration)])
        # Overlay the hook text on a transparent-backed still.
        overlay_png = os.path.join(config.OUTPUT_DIR, "short_overlay.png")
        _hook_overlay(concept["shorts_hook"], concept["title"], overlay_png,
                      base.size[0], base.size[1])
        overlay = ImageClip(overlay_png).with_duration(duration)
        clip = CompositeVideoClip([base, overlay]).with_audio(audio_cut)
    else:
        frame = _frame_portrait(
            cover_path, concept["shorts_hook"], concept["title"],
            os.path.join(config.OUTPUT_DIR, "frame_short.jpg"),
        )
        clip = ImageClip(frame).with_duration(duration).with_audio(audio_cut)

    path = os.path.join(config.OUTPUT_DIR, "short.mp4")
    clip.write_videofile(path, fps=24, codec="libx264", audio_codec="aac", logger=None)
    audio.close()
    return path


def _hook_overlay(hook: str, title: str, path: str, width: int, height: int):
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = width / 1080
    _draw_text(draw, (width // 2, int(220 * scale)), hook,
               _font(int(72 * scale)), width - int(120 * scale))
    _draw_text(draw, (width // 2, int(height * 0.82)), title,
               _font(int(52 * scale)), width - int(120 * scale))
    image.save(path)
