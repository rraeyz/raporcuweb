FROM python:3.11-slim

# Sistem paketlerini kur
RUN apt-get update && apt-get install -y \
    texlive-xetex \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-recommended \
    texlive-latex-extra \
    lmodern \
    cm-super \
    pandoc \
    ffmpeg \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    fonts-dejavu-core \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads temp instance

EXPOSE 5000

CMD ["gunicorn", "run:app", "--workers", "4", "--threads", "2", "--worker-class", "gthread", "--worker-connections", "1000", "--timeout", "180", "--graceful-timeout", "30", "--keep-alive", "5", "--max-requests", "1000", "--max-requests-jitter", "100", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-"]
