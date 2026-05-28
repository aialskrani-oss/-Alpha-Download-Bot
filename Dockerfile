FROM python:3.11-slim

  # تثبيت ffmpeg وأدوات النظام الضرورية
  # Install ffmpeg and required system tools
  RUN apt-get update && apt-get install -y \
      ffmpeg \
      curl \
      && rm -rf /var/lib/apt/lists/*

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  ENV PYTHONUNBUFFERED=1
  ENV PYTHONDONTWRITEBYTECODE=1

  # Render يحقن PORT تلقائياً — لا نثبّت منفذاً هنا
  # Render injects PORT automatically — we don't hardcode it
  EXPOSE 10000

  # فحص صحة الحاوية يستخدم المنفذ الديناميكي من Render
  # Container health check uses Render's dynamic PORT (default 10000)
  HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
      CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

  # إنشاء مستخدم عادي (غير root) لتشغيل الحاوية بأمان
  # Create non-root user for secure container execution
  RUN adduser --disabled-password --gecos "" --uid 1001 botuser
  USER botuser

  # إعادة التشغيل التلقائي عند توقف البوت / Auto-restart on crash
  CMD ["sh", "-c", "while true; do python main.py; echo 'Bot exited, restarting in 5s...'; sleep 5; done"]
  