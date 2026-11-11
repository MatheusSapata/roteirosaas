FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev certbot \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from rembg import new_session; new_session('u2netp')"
# Bibliotecas do Chromium para a raspagem de páginas externas (import-url do assistente de
# IA). Não usa "playwright install --with-deps": essa lista embutida do Playwright ainda
# pede pacotes que a imagem base (Debian trixie) não tem mais (ttf-unifont,
# ttf-ubuntu-font-family), e a instalação falha. Lista testada à mão nesta imagem.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates fonts-liberation fonts-unifont \
       libasound2t64 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 \
       libdbus-1-3 libdrm2 libgbm1 libglib2.0-0t64 libnspr4 libnss3 \
       libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 \
       libxfixes3 libxkbcommon0 libxrandr2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*
RUN playwright install chromium

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
