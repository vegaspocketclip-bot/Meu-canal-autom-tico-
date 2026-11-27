import os
import json
import random
import asyncio
import glob
import edge_tts
import google.generativeai as genai
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

OUTPUT_DIR = "output"
CLIPS_DIR = "gta_clips"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_script():
    if not GEMINI_API_KEY:
        raise ValueError("Variável de ambiente GEMINI_API_KEY não configurada.")
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = (
        "Crie um roteiro curto, envolvente e dinâmico de 45 a 60 segundos para TikTok/Shorts "
        "sobre curiosidades, fatos ocultos ou mistérios do universo GTA. "
        "Retorne APENAS um JSON válido no formato: "
        '{"title": "Título", "script": "Texto narrado direto ao ponto, sem marcações de cena."}'
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    return json.loads(raw_text.strip())

async def _tts_with_timings(text, audio_path, voice="pt-BR-AntonioNeural"):
    communicate = edge_tts.Communicate(text, voice)
    word_timings = []
    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_sec = chunk["offset"] / 10_000_000
                dur_sec = chunk["duration"] / 10_000_000
                word_timings.append({
                    "text": chunk["text"],
                    "start": start_sec,
                    "duration": dur_sec,
                })
    return word_timings

def generate_voiceover(script_text):
    audio_path = os.path.join(OUTPUT_DIR, "voiceover.mp3")
    word_timings = asyncio.run(_tts_with_timings(script_text, audio_path))
    return audio_path, word_timings

def get_local_gameplay_clips(clips_dir=CLIPS_DIR):
    valid_extensions = ("*.mp4", "*.mov", "*.mkv", "*.avi", "*.webm")
    clip_paths = []
    for ext in valid_extensions:
        clip_paths.extend(glob.glob(os.path.join(clips_dir, ext)))
        clip_paths.extend(glob.glob(os.path.join(clips_dir, ext.upper())))
    clip_paths = list(set(clip_paths))
    if not clip_paths:
        raise FileNotFoundError(f"Nenhum vídeo encontrado na pasta '{clips_dir}'. Adicione clipes .mp4.")
    random.shuffle(clip_paths)
    return clip_paths

def build_caption_clips(word_timings, total_duration, script_text):
    if not word_timings:
        words_list = script_text.split()
        n = len(words_list)
        if n == 0: return []
        dur_each = total_duration / n
        word_timings = [{"text": w, "start": i * dur_each, "duration": dur_each} for i, w in enumerate(words_list)]
    clips = []
    for w in word_timings:
        start = w["start"]
        if start >= total_duration: break
        dur = max(w["duration"], 0.15)
        end = min(start + dur, total_duration)
        txt = w["text"].upper().strip()
        if not txt: continue
        clip = (TextClip(txt, fontsize=100, color="yellow", font="Arial-Bold", stroke_color="black", stroke_width=6, method="label")
                .set_position("center")
                .set_start(start)
                .set_end(end))
        clips.append(clip)
    return clips

def assemble_video(audio_path, clip_paths, word_timings, script_text):
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    clips = []
    time_used = 0
    while time_used < total_duration:
        random.shuffle(clip_paths)
        for path in clip_paths:
            if time_used >= total_duration: break
            c = VideoFileClip(path).without_audio()
            max_sub = min(c.duration, 5)
            if c.duration > 5:
                max_start = c.duration - 5
                start_cut = random.uniform(0, max_start)
                c = c.subclip(start_cut, start_cut + 5)
            else:
                c = c.subclip(0, max_sub)
            c = c.resize(height=1920)
            if c.w < 1080: c = c.resize(width=1080)
            c = c.crop(x_center=c.w/2, width=1080, height=1920)
            clips.append(c)
            time_used += c.duration
    video = concatenate_videoclips(clips, method="compose").set_duration(total_duration)
    video = video.set_audio(audio)
    caption_clips = build_caption_clips(word_timings, total_duration, script_text)
    final = CompositeVideoClip([video] + caption_clips)
    output_path = f"{OUTPUT_DIR}/final_video.mp4"
    final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")
    return output_path

if __name__ == "__main__":
    data = generate_script()
    audio_path, word_timings = generate_voiceover(data["script"])
    clips = get_local_gameplay_clips(CLIPS_DIR)
    video_path = assemble_video(audio_path, clips, word_timings, data["script"])