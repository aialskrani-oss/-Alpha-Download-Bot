# ⚡ Alpha Downloader Bot
### بوت منصة الفا | Alpha Platform

بوت تيليجرام متكامل لتحميل الفيديوهات والصور من منصات التواصل الاجتماعي.

---

## 📌 المنصات المدعومة

| المنصة | الحالة | الطريقة |
|--------|--------|---------|
| YouTube | ✅ يعمل بالكامل | yt-dlp |
| TikTok | ✅ يعمل بالكامل | tikwm.com API |
| Twitter/X | ✅ يعمل للتغريدات التي تحوي فيديو | yt-dlp |
| Instagram | ⚙️ يتطلب بيانات دخول | instaloader |
| Facebook | ⚙️ يتطلب كوكيز | yt-dlp + cookies |

---

## 🚀 النشر السريع

### على Render.com
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. افتح [render.com](https://render.com) وسجّل دخولك
2. New → Web Service → اربط GitHub repo
3. أضف المتغيرات البيئية (انظر أدناه)
4. انقر Deploy

### على Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. افتح [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. أضف المتغيرات البيئية
4. انشر

### بـ Docker محلياً
```bash
git clone <your-repo>
cd telegram-bot
cp .env.example .env
# عدّل .env وأضف قيمك
docker-compose up -d
```

---

## ⚙️ متغيرات البيئة

| المتغير | مطلوب | الوصف |
|---------|-------|-------|
| `TELEGRAM_BOT_TOKEN` | ✅ نعم | توكن البوت من @BotFather |
| `INSTAGRAM_USERNAME` | اختياري | اسم مستخدم حساب إنستغرام |
| `INSTAGRAM_PASSWORD` | اختياري | كلمة مرور حساب إنستغرام |
| `FACEBOOK_COOKIES` | اختياري | كوكيز فيسبوك بصيغة Netscape |
| `KEEP_ALIVE_PORT` | اختياري | منفذ خادم keep-alive (افتراضي: 5001) |

---

## 🛠️ التثبيت المحلي

```bash
# 1. نسخ المشروع
git clone <your-repo>
cd telegram-bot

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. إعداد المتغيرات البيئية
cp .env.example .env
# افتح .env وأضف TELEGRAM_BOT_TOKEN

# 4. تشغيل البوت
python main.py
```

**المتطلبات:**
- Python 3.10+
- ffmpeg مثبّت على النظام

---

## 🔒 إعداد Instagram

لتفعيل تحميل Instagram:
1. أنشئ حساباً ثانوياً على إنستغرام (لا تستخدم حسابك الشخصي)
2. أضف `INSTAGRAM_USERNAME` و `INSTAGRAM_PASSWORD` كمتغيرات بيئة
3. أعد تشغيل البوت — سيحفظ الجلسة تلقائياً

---

## 💡 الإبقاء على البوت حياً 24/7

البوت يشغّل خادم Flask بسيط على المنفذ 5001.
استخدم **UptimeRobot** (مجاني) لعمل ping كل 5 دقائق:

1. افتح [uptimerobot.com](https://uptimerobot.com) وسجّل دخولك
2. New Monitor → HTTP(s)
3. أضف رابط بوتك: `https://your-app.onrender.com/health`
4. الفترة: كل 5 دقائق

---

## 📁 هيكل المشروع

```
telegram-bot/
├── main.py           # الكود الرئيسي للبوت (974 سطر)
├── keep_alive.py     # خادم Flask للـ ping
├── requirements.txt  # مكتبات Python
├── Dockerfile        # لنشر Docker
├── docker-compose.yml
├── render.yaml       # إعداد Render.com
├── .env.example      # مثال متغيرات البيئة
├── .gitignore
└── README.md
```

---

## 📊 الإصدار

**v1.1.0** — Alpha Platform © 2024
