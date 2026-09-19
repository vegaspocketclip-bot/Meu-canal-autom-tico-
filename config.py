"""
CONFIGURAÇÃO — VERSÃO 100% GRATUITA
====================================
As chaves ja estao configuradas como GitHub Secrets
(GROQ_API_KEY e PEXELS_API_KEY) e sao lidas automaticamente
pelo os.getenv abaixo. Nao precisa editar nada aqui pra isso funcionar.
"""

import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "COLOQUE_SUA_CHAVE_AQUI")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "COLOQUE_SUA_CHAVE_AQUI")

# Nicho do canal — GTA 6 (noticias, teorias, curiosidades sobre o jogo).
# Importante: o roteiro e gerado do zero pela IA (nao copia texto de
# ninguem) e os videos de fundo vem do banco do Pexels (carros, cidade
# a noite, etc) — nunca usar trecho de trailer oficial da Rockstar
# como fundo, pra nao correr risco de Content ID/direitos autorais.
NICHE = "GTA 6 news, release updates, and fan theories (no copyrighted game footage, just narration over generic city/car background)"

VIDEO_LENGTH_SECONDS = 40  # ideal para Shorts/Reels/TikTok
