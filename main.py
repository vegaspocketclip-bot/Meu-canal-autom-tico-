# PIPELINE AUTOMATIZADO DE CANAL "FACELESS" (sem aparecer)

import os
import sys
import json
import random
import textwrap

from config import (
    GROQ_API_KEY, PEXELS_API_KEY,
    NICHE, VIDEO_LENGTH_SECONDS
)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_script():
    import requests

    prompt = f"""You are a scriptwriter for short-form faceless YouTube/TikTok videos
in the niche: "{NICHE}".

Write ONE video script for a video lasting about {VIDEO_LENGTH_SECONDS} seconds
(roughly {VIDEO_LENGTH_SECONDS * 2.5:.0f} words at natural speaking pace).

Requirements:
- Hook in the first sentence (must stop the scroll)
- Simple, punchy sentences, no complex words
- End with a call to action (follow/comment)
- Output STRICT JSON only, no markdown, in this format:
{{
  "title": "short catchy YouTube title, max 90 chars",
  "description": "1-2 sentence YouTube description with 3 hashtags",
  "script": "the full narration text, plain sentences separated by periods",
  "visual_keywords": ["keyword1", "keyword2", "keyword3"]
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
        "max_tokens": 1000,
        "temperature": 0.9,
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

    print(f"Roteiro gerado: {data['title']}")
    return data


def generate_voiceover(script_text):
    audio_path = f"{OUTPUT_DIR}/voiceover.mp3"

    from gtts import gTTS
    tts = gTTS(text=script_text, lang="en")
    tts.save(audio_path)
    print("Narracao gerada com gTTS (gratis)")

    return audio_path


def fetch_stock_clips(keywords, count=5):
    import requests

    clips = []
    headers = {"Authorization": PEXELS_API_KEY}

    for kw in keywords:
        url = f"https://api.pexels.com/videos/search?query={kw}&per_page={count}&orientation=portrait"
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
        print("Nenhum clipe encontrado no Pexels. Verifique as keywords/API key.")
        sys.exit(1)

    random.shuffle(clips)
    downloaded = []
    for i, url in enumerate(clips[:count]):
        path = f"{OUTPUT_DIR}/clip_{i}.mp4"
        import requests as req
        r = req.get(url, stream=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        downloaded.append(path)

    print(f"{len(downloaded)} clipes baixados")
    return downloaded


def assemble_video(audio_path, clip_paths, script_text):
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, concatenate_videoclips,
        CompositeVideoClip, TextClip
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
            c = c.resize(height=1920).crop(x_center=c.w / 2, width=1080)
            clips.append(c)
            time_used += c.duration

    video = concatenate_videoclips(clips, method="compose").set_duration(total_duration)
    video = video.set_audio(audio)

    hook = textwrap.shorten(script_text.split(".")[0], width=60)
    txt_clip = (TextClip(hook, fontsize=60, color="white", font="Arial-Bold",
                          size=(1000, None), method="caption")
                .set_position(("center", 150))
                .set_duration(min(4, total_duration)))

    final = CompositeVideoClip([video, txt_clip])
    output_path = f"{OUTPUT_DIR}/final_video.mp4"
    final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")

    print(f"Video final montado: {output_path}")
    return output_path


if __name__ == "__main__":
    data = generate_script()
    audio_path = generate_voiceover(data["script"])
    clips = fetch_stock_clips(data["visual_keywords"])
    video_path = assemble_video(audio_path, clips, data["script"])

    print("\nVideo pronto em output/final_video.mp4")
