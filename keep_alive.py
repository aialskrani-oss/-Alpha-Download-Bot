"""
keep_alive.py
خادم Flask متكامل يعمل على thread منفصل تماماً لإبقاء البوت حياً 24/7
Full Flask server running on a completely separate thread for 24/7 uptime

نقاط النهاية / Endpoints:
- /         : الصفحة الرئيسية
- /health   : فحص صحة الخادم (لـ UptimeRobot و Render)
- /ping     : نقطة ping بسيطة للمراقبة الخارجية
- /stats    : إحصائيات البوت (وقت التشغيل)

الاستخدام مع UptimeRobot / Usage with UptimeRobot:
1. أنشئ monitor من نوع HTTP(s) على https://your-app.onrender.com/health
2. اضبط الفترة على 5 دقائق (الحد المجاني)
3. البوت سيبقى يعمل 24/7 مجاناً
"""

import os
import time
import threading
from flask import Flask, jsonify

app = Flask(__name__)

# وقت بدء التشغيل / Server start time
_start_time = time.time()


@app.route("/")
def home():
    """الصفحة الرئيسية / Home page"""
    return (
        "<h2>⚡ Alpha Downloader Bot</h2>"
        "<p>🤖 البوت يعمل بشكل طبيعي! / Bot is running!</p>"
        "<p><a href='/health'>Health Check</a> | <a href='/stats'>Stats</a></p>"
    )


@app.route("/health")
def health():
    """
    نقطة فحص الصحة — تُستخدم من UptimeRobot و Render و healthCheckPath
    Health check endpoint — used by UptimeRobot, Render, and external monitors
    """
    uptime_seconds = int(time.time() - _start_time)
    return jsonify({
        "status": "ok",
        "message": "Bot is alive and running",
        "uptime_seconds": uptime_seconds,
        "uptime_human": _format_uptime(uptime_seconds),
    }), 200


@app.route("/ping")
def ping():
    """نقطة ping بسيطة / Simple ping endpoint"""
    return jsonify({"ping": "pong", "ts": int(time.time())}), 200


@app.route("/stats")
def stats():
    """
    إحصائيات البوت — وقت التشغيل وحالة الخادم
    Bot stats — uptime and server status
    """
    uptime_seconds = int(time.time() - _start_time)
    return jsonify({
        "bot": "Alpha Downloader",
        "platform": "Alpha Platform",
        "version": "1.1.0",
        "status": "running",
        "uptime_seconds": uptime_seconds,
        "uptime_human": _format_uptime(uptime_seconds),
    }), 200


def _format_uptime(seconds: int) -> str:
    """تحويل الثواني إلى صيغة مقروءة / Convert seconds to human-readable uptime"""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def _run_server():
    """
    تشغيل خادم Flask على المنفذ المحدد
    Run Flask server on the configured port
    """
    port = int(os.environ.get("KEEP_ALIVE_PORT", 5001))
    # تعطيل سجلات Flask الافتراضية لتجنب الضوضاء / Suppress Flask default logs
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.WARNING)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def keep_alive():
    """
    تشغيل خادم Flask في خيط daemon منفصل حتى لا يعطل عمل البوت.
    يموت الخيط تلقائياً عند إغلاق العملية الرئيسية.
    
    Run Flask server in a separate daemon thread so it never blocks the bot.
    The thread dies automatically when the main process exits.
    """
    t = threading.Thread(target=_run_server, name="keep-alive-server")
    t.daemon = True  # موت تلقائي مع العملية / Auto-die with main process
    t.start()
    
    port = int(os.environ.get("KEEP_ALIVE_PORT", 5001))
    print(f"[keep_alive] Server started on port {port}")
    print(f"[keep_alive] Health check: http://localhost:{port}/health")
