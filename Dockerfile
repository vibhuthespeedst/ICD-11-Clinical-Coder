FROM python:3.13-slim@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps -r requirements.txt && pip check
COPY coder ./coder
COPY data ./data
RUN python -m coder.prebuild
ENTRYPOINT ["python", "-m", "coder"]
