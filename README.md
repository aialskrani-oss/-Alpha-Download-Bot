# ⚡ Alpha Downloader Bot
  ### بوت منصة الفا | Alpha Platform

  [![Build & Push Docker Image](https://github.com/aialskrani-oss/-Alpha-Download-Bot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/aialskrani-oss/-Alpha-Download-Bot/actions)

  بوت تيليجرام متكامل لتحميل الفيديوهات والصور من منصات التواصل الاجتماعي.

  ---

  ## 📌 المنصات المدعومة

  | المنصة | الحالة | الطريقة |
  |--------|--------|---------|
  | YouTube | ✅ يعمل بالكامل | yt-dlp |
  | TikTok | ✅ يعمل بالكامل | tikwm.com API + yt-dlp |
  | Twitter/X | ✅ يعمل للتغريدات التي تحوي فيديو | yt-dlp |
  | Instagram | ✅ يعمل للمنشورات العامة والريلز | yt-dlp (بدون حساب) |
  | Facebook | ✅ عام / ⚙️ خاص بكوكيز | yt-dlp + cookies اختياري |

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
  git clone https://github.com/aialskrani-oss/-Alpha-Download-Bot
  cd -Alpha-Download-Bot
  cp .env.example .env
  # عدّل .env وأضف TELEGRAM_BOT_TOKEN
  docker-compose up -d
  ```

  ---

  ## ⚙️ متغيرات البيئة

  | المتغير | مطلوب | الوصف |
  |---------|-------|-------|
  | `TELEGRAM_BOT_TOKEN` | ✅ نعم | توكن البوت من @BotFather |
  | `FACEBOOK_COOKIES` | اختياري | كوكيز فيسبوك بصيغة Netscape للمقاطع الخاصة |
  | `KEEP_ALIVE_PORT` | اختياري | منفذ خادم keep-alive (افتراضي: 5001) |
  | `RENDER_EXTERNAL_URL` | اختياري | رابط التطبيق الخارجي لـ self-ping |

  > **ملاحظة:** لا يوجد INSTAGRAM_USERNAME أو INSTAGRAM_PASSWORD — Instagram يعمل بدون حساب للمحتوى العام.

  ---

  ## 🛠️ التثبيت المحلي

  ```bash
  # 1. نسخ المشروع
  git clone https://github.com/aialskrani-oss/-Alpha-Download-Bot

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

  ## 🍪 كيفية إعداد Facebook Cookies (اختياري)

  لتحميل مقاطع Facebook الخاصة أو التي تتطلب تسجيل دخول:

  1. ثبّت إضافة **"Get cookies.txt LOCALLY"** على Chrome أو Firefox
  2. سجّل دخولك على [facebook.com](https://facebook.com)
  3. انقر على أيقونة الإضافة واختر "Export" → Netscape format
  4. انسخ المحتوى الكامل للملف
  5. أضفه كمتغير بيئة باسم `FACEBOOK_COOKIES`

  > **للمحتوى العام:** البوت يحاول التحميل بدون كوكيز أولاً تلقائياً.

  ---

  ## 💡 الإبقاء على البوت حياً 24/7

  البوت يشغّل خادم Flask على المنفذ 5001 مع self-ping كل 3 دقائق.

  **استخدم UptimeRobot** (مجاني) لضمان عدم نوم البوت:

  1. افتح [uptimerobot.com](https://uptimerobot.com) وسجّل دخولك
  2. New Monitor → HTTP(s)
  3. أضف رابط بوتك: `https://your-app.onrender.com/health`
  4. الفترة: كل 5 دقائق

  نقاط النهاية المتاحة:
  - `/health` — فحص الصحة (JSON)
  - `/ping` — ping بسيط
  - `/stats` — إحصائيات وقت التشغيل

  ---

  ## 📁 هيكل المشروع

  ```
  ├── main.py                     # الكود الرئيسي للبوت
  ├── keep_alive.py               # خادم Flask للـ ping والصحة
  ├── requirements.txt            # مكتبات Python
  ├── Dockerfile                  # Docker مع HEALTHCHECK
  ├── docker-compose.yml
  ├── render.yaml                 # إعداد Render.com مع healthCheckPath
  ├── .env.example                # مثال متغيرات البيئة
  ├── github-actions-workflow.yml # نموذج GitHub Actions
  └── README.md
  ```

  ---

  ## 📊 الإصدار

  **v1.1.0** — Alpha Platform © 2024
  