FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app/staticfiles /app/media

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command (will be overridden by docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "talentForge.wsgi:application"]