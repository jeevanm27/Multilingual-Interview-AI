# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 – Dependency builder
# Using a slim Python image to keep the final image small.
# Think of this like a multi-stage Maven/Gradle build in Spring Boot Docker setups.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /install

# System deps needed by some Python packages (gTTS needs no extras,
# but aiofiles/uvicorn might need build tools on some platforms)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install/deps --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 – Runtime image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY main.py .
COPY static/ ./static/

# Create the directory where gTTS audio files are written at runtime
RUN mkdir -p static/audio

# Non-root user for security  (like running as a non-root user in Spring Boot containers)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# uvicorn is the ASGI server – analogous to Tomcat/Jetty for Spring Boot,
# or the built-in HTTP server in Node.js
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
