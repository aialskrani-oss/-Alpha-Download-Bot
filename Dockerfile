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

  CMD ["python", "main.py"]
  