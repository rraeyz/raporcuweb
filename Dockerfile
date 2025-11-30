FROM python:3.11-slim

# Sistem paketlerini güncelle
RUN apt-get update && apt-get install -y \
    # LaTeX ve Pandoc
    texlive-xetex \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-recommended \
    texlive-latex-extra \
    lmodern \
    cm-super \
    pandoc \
    # WeasyPrint ve diğer bağımlılıklar
    ffmpeg \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    fonts-dejavu-core \
    # Genel araçlar
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Python bağımlılıklarını kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# XeLaTeX kurulumunu doğrula
RUN which xelatex && echo "XeLaTeX kuruldu!" || echo "HATA: XeLaTeX bulunamadı!"

# Flask migration
RUN flask db upgrade || echo "Migration henüz hazır değil"

# Port
EXPOSE 10000

# Gunicorn ile başlat
CMD ["gunicorn", "run:app", "--workers", "1", "--threads", "2", "--timeout", "120", "--max-requests", "100", "--max-requests-jitter", "10", "--bind", "0.0.0.0:10000"]
