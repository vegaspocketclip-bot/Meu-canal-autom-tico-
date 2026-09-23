# PIPELINE AUTOMATIZADO DE CANAL "FACELESS" (sem aparecer)

import os
import sys
import json
import random
import asyncio

from config import (
    GROQ_API_KEY, PEXELS_API_KEY,
    NICHE, VIDEO_LENGTH_SECONDS
)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

KNOWN_FACTS = """
CONFIRMED REAL FACTS about GTA 6 (as of September 2026, use ONLY these,
do not invent additional plot details, missions, or rumors not listed here):
- Official release date: November 19, 2026 (for PS5 and Xbox Series X/S)
- The game was previously delayed from an earlier planned date of May 26, 2026
- No PC release date has been officially confirmed yet
- Setting: a fictionalized version of Florida called "Leonida"
- Protagonists: Jason and Lucia (confirmed via official trailers)
- Developer: Rockstar Games. Publisher: Take-Two Interactive
"""

MIAMI_VIBE_KEYWORDS = [
    "Miami South Beach art deco neon night",
    "Ocean Drive Miami night palm trees",
    "Florida Everglades swamp alligator",
    "Florida Keys ocean drone aerial",
    "Miami downtown skyline sunset drone",
    "luxury mansion pool palm trees Florida",
    "speedboat ocean Florida coast",
]


def generate_script():
    import requests

    prompt = f"""You are a scriptwriter for short-form faceless YouTube/TikTok videos
in the niche: "{NICHE}".

{KNOWN_FACTS}

Write ONE video script for a video lasting about {VIDEO_LENGTH_SECONDS} seconds
(roughly {VIDEO_LENGTH_SECONDS * 2.5:.0f} words at natural speaking pace).

Requirements:
- Base the script ONLY on the confirmed facts above. Do not invent a
  release date, mission, or leak that isn't in the facts list.
- You may mention that fans are speculating about X or Y, but must
  clearly frame it as unconfirmed fan speculation, not fact.
- IMPORTANT: in the "script" field (the spoken narration), always
  write the game's name in full as "Grand Theft Auto 6" or
  "Grand Theft Auto", never as the abbreviation "GTA".
- Hook in the first sentence (must stop the scroll)
- Simple, punchy sentences, no complex words
- End the script with a direct QUESTION to the viewer, designed to
  generate comments (not a generic "follow and comment"). Example
  style: "Will you be playing on console on day one, or waiting for
  the PC release? Let me know below."
- The narration itself must be 100% in English.
- Additionally, provide a Brazilian Portuguese translation of that
  same script, ONLY so the creator can understand what is being said.
- Output STRICT JSON only, no markdown, in this format:
{{
  "title": "short catchy YouTube title, max 90 chars",
  "description": "1-2 sentence YouTube description with 3 hashtags",
  "script": "the full narration text in English, plain sentences separated by periods",
  "script_pt": "a traducao completa do script em portugues do Brasil, so para referencia"
}}
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 2000,
        "temperature": 0.9,
        "reasoning_effort": "low",
    }

    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"].strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print("A IA nao retornou JSON valido. Resposta bruta:")
        print(text)
        sys.exit(1)

    with open(f"{OUTPUT_DIR}/script.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"TITULO: {data['title']}")
    print("=" * 60)
    print("O QUE FOI FALADO NO VIDEO (traduzido, so pra voce entender):")
    print(data.get("script_pt", "(traducao nao disponivel)"))
    print("=" * 60)

    return data


def generate_voiceover(script_text):
    import edge_tts

    audio_path = f"{OUTPUT_DIR}/voiceover.mp3"
    words = []

    async def _run():
        communicate = edge_tts.Communicate(script_text, voice="en-US-GuyNeural")
        with open(audio_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append({
                        "text": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,
                        "duration": chunk["duration"] / 10_000_000,
                    })

    asyncio.run(_run())
    print(f"Narracao gerada com edge-tts (gratis) - {len(words)} palavras cronometradas pelo sistema")

    return audio_path, words


def fetch_stock_clips(count=6):
    import requests

    clips = []
    headers = {"Authorization": PEXELS_API_KEY}

    for kw in MIAMI_VIBE_KEYWORDS:
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page=3&orientation=portrait"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            continue
        data = r.json()
        for video in data.get("videos", []):
            files = sorted(video["video_files"], key=lambda f: f.get("width", 0))
            for f in files:
                if f.get("width", 0) >= 720:
                    clips.append(f["link"])
                    break

    if not clips:
        print("Nenhum clipe encontrado no Pexels. Verifique a API key.")
        sys.exit(1)

    random.shuffle(clips)
    downloaded = []
    for i, url in enumerate(clips[:count]):
        path = f"{OUTPUT_DIR}/clip_{i}.mp4"
        r = requests.get(url, stream=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        downloaded.append(path)

    print(f"{len(downloaded)} clipes baixados (locais reais estilo Leonida)")
    return downloaded


def build_caption_clips(word_timings, total_duration, script_text):
    """Cria uma legenda por palavra. Se a cronometragem exata da voz
    falhar por qualquer motivo, calcula um tempo aproximado sozinho,
    garantindo que a legenda SEMPRE apareca no video."""
    from moviepy.editor import TextClip

    if not word_timings:
        print("AVISO: cronometragem exata falhou, usando tempo estimado")
        words_list = script_text.split()
        n = len(words_list)
        if n == 0:
            return []
        dur_each = total_duration / n
        word_timings = [
            {"text": w, "start": i * dur_each, "duration": dur_each}
            for i, w in enumerate(words_list)
        ]

    clips = []
    for w in word_timings:
        start = w["start"]
        if start >= total_duration:
            break
        dur = max(w["duration"], 0.15)
        end = min(start + dur, total_duration)

        txt = w["text"].upper().strip()
        if not txt:
            continue

        clip = (TextClip(txt, fontsize=100, color="yellow", font="Arial-Bold",
                          stroke_color="black", stroke_width=6, method="label")
                .set_position("center")
                .set_start(start)
                .set_end(end))
        clips.append(clip)

    print(f"{len(clips)} legendas criadas")
    return clips


def assemble_video(audio_path, clip_paths, word_timings, script_text):
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, concatenate_videoclips,
        CompositeVideoClip
    )

    audio = AudioFileClip(audio_path)
    total_duration = audio.duration

    clips = []
    time_used = 0
    while time_used < total_duration:
        for path in clip_paths:
            if time_used >= total_duration:
                break
            c = VideoFileClip(path).without_audio()
            c = c.subclip(0, min(c.duration, 5))
            c = c.resize(height=1920)
            if c.w < 1080:
                c = c.resize(width=1080)
            c = c.crop(x_center=c.w / 2, width=1080)
            clips.append(c)
            time_used += c.duration

    video = concatenate_videoclips(clips, method="compose").set_duration(total_duration)
    video = video.set_audio(audio)

    caption_clips = build_caption_clips(word_timings, total_duration, script_text)

    final = CompositeVideoClip([video] + caption_clips)
    output_path = f"{OUTPUT_DIR}/final_video.mp4"
    final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")

    print(f"Video final montado: {output_path}")
    return output_path


if __name__ == "__main__":
    data = generate_script()
    audio_path, word_timings = generate_voiceover(data["script"])
    clips = fetch_stock_clips()
    video_path = assemble_video(audio_path, clips, word_timings, data["script"])

    print("\nVideo pronto em output/final_video.mp4")
