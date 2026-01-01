FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Variables pour l'IA
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV HF_HOME=/root/.cache/huggingface
ENV TORCH_HOME=/root/.cache/torch

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Créer les répertoires de cache
RUN mkdir -p /root/.cache/huggingface \
    && mkdir -p /root/.cache/torch

# Copier les requirements
COPY requirements.txt .

# Installer TOUT en une seule commande (évite les conflits de versions)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir \
    -r requirements.txt \
    profanity-check==1.0.3 \
    scikit-learn==1.3.2 \
    joblib==1.3.0

# Copier l'application
COPY . .

# Configurer l'utilisateur
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app /root/.cache

USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "talentForge.wsgi:application"]