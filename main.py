# PIPELINE AUTOMATIZADO DE CANAL "FACELESS" (sem aparecer)

import os
import sys
import json
import random
import textwrap
import asyncio

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
(roughly {VIDEO_LENGTH_SECO
