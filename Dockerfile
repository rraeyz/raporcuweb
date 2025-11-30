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
    libgdk-pixbuf2.0-0 \
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

CMD ["gunicorn", "run:app", "--workers", "2", "--threads", "4", "--timeout", "120", "--bind", "0.0.0.0:5000"]
