FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" jinja2 httpx python-multipart python-docx pypdf
COPY app/ ./app/
COPY seed/ ./seed/
# State lives in a persistent volume mounted here (Coolify storage at /data).
RUN mkdir -p /data
ENV PYTHONUNBUFFERED=1 APERTURE_DATA_DIR=/data PORT=8770
EXPOSE 8770
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8770\")}/health', timeout=3)" || exit 1
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8770}"]
