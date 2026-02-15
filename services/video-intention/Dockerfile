FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SUPABASE_URL=""
ENV SUPABASE_KEY=""
ENV OPENAI_API_KEY=""
ENV TWELVE_LABS_API_KEY=""

CMD ["python", "src/consumer/main.py"]
