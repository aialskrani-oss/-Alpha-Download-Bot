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

  # منفذ خادم keep-alive / Keep-alive server port
  EXPOSE 5001

  # فحص صحة الحاوية — يتحقق من /health كل 30 ثانية
  # Container health check — verifies /health every 30 seconds
  HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
      CMD curl -f http://localhost:5001/health || exit 1

  # إنشاء مستخدم عادي (غير root) لتشغيل الحاوية بأمان
  # Create non-root user for secure container execution
  RUN adduser --disabled-password --gecos "" --uid 1001 botuser
  USER botuser

  # إعادة التشغيل التلقائي عند توقف البوت / Auto-restart on crash
  CMD ["sh", "-c", "while true; do python main.py; echo 'Bot exited, restarting in 5s...'; sleep 5; done"]
  