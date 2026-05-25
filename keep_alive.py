"""
keep_alive.py
خادم Flask بسيط لإبقاء البوت حياً 24/7
Simple Flask server to keep the bot alive 24/7

الاستخدام مع UptimeRobot / Monitority:
1. انسخ رابط Replit الخاص بك (مثال: https://your-repl.username.repl.co)
2. أضفه في UptimeRobot كـ HTTP monitor كل 5 دقائق
3. البوت سيبقى يعمل بشكل دائم مجاناً
"""

import os
from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route("/")
def home():
    """الصفحة الرئيسية - Health check endpoint"""
    return "🤖 البوت يعمل بشكل طبيعي! / Bot is running!"


@app.route("/health")
def health():
    """نقطة فحص صحة الخادم للمراقبة الخارجية"""
    return {"status": "ok", "message": "Bot is alive and running"}, 200


def run():
    """تشغيل خادم Flask على المنفذ 5001 (keep-alive ping endpoint)"""
    port = int(os.environ.get("KEEP_ALIVE_PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)


def keep_alive():
    """
    تشغيل الخادم في خيط منفصل حتى لا يعطل عمل البوت
    Run the server in a separate thread so it doesn't block the bot
    """
    t = Thread(target=run)
    t.daemon = True
    t.start()
