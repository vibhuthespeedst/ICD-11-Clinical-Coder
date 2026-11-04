FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY coder ./coder
COPY data/mms-2026-01.json ./data/mms-2026-01.json
ENTRYPOINT ["python", "-m", "coder"]
