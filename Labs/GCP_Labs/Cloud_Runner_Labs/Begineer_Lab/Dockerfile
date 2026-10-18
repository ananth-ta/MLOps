FROM python:3.13-slim

# Don't write .pyc files; flush logs straight to Cloud Logging.
# pip runs as root only at build time (the app itself runs as appuser), so skip its root warning.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PORT=8080

WORKDIR /app

# Install dependencies first so this layer is cached when only app code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Run as an unprivileged user instead of root
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8080

# Cloud Run sends traffic to the port in $PORT, so bind to it rather than hard-coding 8080.
# Shell form is needed for $PORT to expand; exec makes gunicorn PID 1 so it receives SIGTERM.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 app:app
