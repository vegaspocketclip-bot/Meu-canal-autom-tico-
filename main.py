"""
PIPELINE AUTOMATIZADO DE CANAL "FACELESS" (sem aparecer)
==========================================================
"""

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
    text = r.json()["choices"][0]["me
