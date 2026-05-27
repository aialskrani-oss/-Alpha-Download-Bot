"""
main.py - بوت تليجرام لتحميل الفيديوهات والصور
Telegram Bot for downloading videos and images from social media

المنصات المدعومة / Supported Platforms:
- YouTube
- Instagram (منشورات عامة، ريلز) — yt-dlp بدون تسجيل دخول
- TikTok
- Twitter/X
- Facebook (عام أو مع كوكيز اختيارية)
- وأكثر من 100 موقع آخر عبر yt-dlp

المتطلبات / Requirements:
- TELEGRAM_BOT_TOKEN: توكن البوت من @BotFather
"""

import os
import re
import asyncio
import logging
import tempfile
import shutil
import time
from pathlib import Path

import requests
import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from keep_alive import keep_alive

# User-Agent يحاكي متصفح حديث على الهاتف / Modern mobile browser UA
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)
DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ===== إعدادات السجل / Logging Setup =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===== الثوابت / Constants =====
MAX_FILE_SIZE_MB = 50  # الحد الأقصى لحجم الملف بالميجابايت (حد تليجرام)
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# وقت بدء تشغيل البوت / Bot start time for uptime tracking
BOT_START_TIME = time.time()

# الرابط الداخلي لـ ping (يُقرأ من البيئة) / Internal URL for self-ping
SELF_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
if not SELF_URL:
    SELF_URL = os.environ.get("REPLIT_URL", "")
KEEP_ALIVE_PORT = int(os.environ.get("KEEP_ALIVE_PORT", 5001))

# أنماط روابط المنصات المدعومة / Supported platform URL patterns
URL_PATTERN = re.compile(
    r"https?://(?:[\w\-]+\.)?"
    r"(?:youtube\.com|youtu\.be|"
    r"instagram\.com|"
    r"tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|"
    r"twitter\.com|x\.com|t\.co|"
    r"facebook\.com|fb\.watch|fb\.com|"
    r"snapchat\.com|snap\.com|"
    r"pinterest\.com|pin\.it|"
    r"reddit\.com|redd\.it|"
    r"dailymotion\.com|dai\.ly|"
    r"twitch\.tv|"
    r"vimeo\.com)"
    r"[^\s]*",
    re.IGNORECASE,
)

# ===== رسائل البوت / Bot Messages =====
WELCOME_MESSAGE = """
⚡ *مرحباً بك في Alpha Downloader!*
_بوت منصة الفا | Alpha Platform_

أقوى بوت لتحميل الفيديوهات والصور من جميع منصات التواصل الاجتماعي.

📌 *المنصات المدعومة:*
• YouTube 🎬
• Instagram (منشورات عامة، ريلز) 📸
• TikTok 🎵
• Twitter/X 🐦
• Facebook 📘
• وأكثر من 1000 موقع آخر!

📤 *طريقة الاستخدام:*
فقط أرسل لي رابط الفيديو أو الصورة وسأقوم بتحميلها لك فوراً!

⚠️ *ملاحظة:* الحد الأقصى لحجم الملف هو 50 ميجابايت.

اكتب /help لمزيد من المساعدة.
"""

HELP_MESSAGE = """
📖 *دليل استخدام Alpha Downloader*

*الأوامر المتاحة:*
• /start - بدء استخدام البوت
• /help - عرض هذه المساعدة
• /about - معلومات عن Alpha Downloader

*كيفية التحميل:*
1️⃣ انسخ رابط الفيديو أو الصورة
2️⃣ أرسله مباشرة للبوت
3️⃣ انتظر قليلاً وسيصلك الملف

*المنصات المدعومة:*
• ✅ YouTube — يعمل بالكامل
• ✅ TikTok — يعمل بالكامل
• ✅ Instagram — يعمل للمنشورات والريلز العامة (بدون حساب)
• ✅ Twitter/X — يعمل للتغريدات التي تحوي فيديو
• ⚙️ Facebook — يعمل للمقاطع العامة؛ للمقاطع الخاصة راجع إعداد الكوكيز أدناه

*إعداد كوكيز Facebook (اختياري):*
لتحميل مقاطع Facebook الخاصة أو التي تتطلب تسجيل دخول:
1️⃣ ثبّت إضافة "Get cookies.txt LOCALLY" على Chrome أو Firefox
2️⃣ سجّل دخولك على facebook.com
3️⃣ صدّر الكوكيز بصيغة Netscape واحفظها
4️⃣ أضف محتوى الملف كمتغير بيئة FACEBOOK_COOKIES

⚠️ *قيود:*
• الحد الأقصى لحجم الملف: 50 ميجابايت
• المحتوى الخاص لا يمكن تحميله بدون كوكيز

⚡ *Alpha Downloader* | منصة الفا
"""

ABOUT_MESSAGE = """
ℹ️ *معلومات عن Alpha Downloader*

⚡ *الاسم:* Alpha Downloader
🏢 *المنصة:* Alpha Platform | منصة الفا

🛠️ *التقنيات المستخدمة:*
• Python 3.11
• python-telegram-bot v20+
• yt-dlp (يدعم أكثر من 1000 موقع!)
• Flask (للإبقاء على البوت حياً 24/7)

📊 *الإصدار:* 1.1.0

_جميع الحقوق محفوظة لمنصة الفا © Alpha Platform_
"""

# ===== رسائل الخطأ لكل منصة / Per-platform error messages =====
PLATFORM_ERROR_MESSAGES = {
    "youtube": "❌ فشل تحميل فيديو YouTube\n\nأسباب محتملة:\n• الرابط غير صحيح\n• الفيديو محمي بحقوق ملكية\n• الفيديو مقيّد في منطقتك",
    "tiktok": "❌ فشل تحميل فيديو TikTok\n\nأسباب محتملة:\n• الحساب خاص\n• الرابط منتهي الصلاحية\n• جرّب نسخ الرابط مرة أخرى",
    "instagram": "❌ فشل تحميل محتوى Instagram\n\nأسباب محتملة:\n• الحساب خاص\n• المنشور محذوف\n• يدعم البوت المنشورات العامة فقط",
    "twitter": "❌ فشل تحميل تغريدة Twitter/X\n\nأسباب محتملة:\n• التغريدة لا تحتوي على فيديو\n• الحساب خاص أو محذوف",
    "facebook": "❌ فشل تحميل فيديو Facebook\n\nفيديو Facebook يتطلب إعداد الكوكيز للمحتوى الخاص.\n\nاكتب /help واتبع خطوات إعداد كوكيز Facebook.",
    "other": "❌ فشل تحميل المحتوى\n\nتأكد من صحة الرابط وأن المحتوى متاح للعموم.",
}


# ===== دوال المساعدة / Helper Functions =====

def is_valid_url(url: str) -> bool:
    """
    التحقق من صحة الرابط قبل محاولة التحميل
    Validate URL before attempting download
    """
    try:
        result = requests.utils.urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def resolve_short_url(url: str) -> str:
    """
    حل الروابط المختصرة — يأخذ أول Location header (قبل أن تكتشف المنصة البوت)
    Resolve shortened URLs by reading the first redirect Location header only.
    Handles: vt.tiktok.com, vm.tiktok.com, t.co, fb.watch, etc.
    """
    short_domains = (
        "vt.tiktok.com", "vm.tiktok.com",
        "t.co", "fb.watch", "bit.ly",
        "tinyurl.com", "ow.ly", "is.gd",
        "pin.it", "redd.it", "dai.ly",
    )
    needs_resolve = any(d in url for d in short_domains)
    if not needs_resolve:
        return url

    headers = {
        "User-Agent": MOBILE_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.tiktok.com/",
    }

    try:
        resp = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        location = resp.headers.get("Location", "")
        logger.info(f"Short URL first redirect: {url} -> {location or '(none)'}")

        if location and "tiktok.com" in location and "/video/" in location:
            return location

        resp2 = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        final = resp2.url
        logger.info(f"Resolved {url} -> {final}")

        BAD_PATHS = ("/in/about", "/login", "/signup", "/explore")
        if any(p in final for p in BAD_PATHS):
            logger.warning(f"Redirect landed on bad page: {final}. Using original URL.")
            return url

        return final

    except Exception as e:
        logger.warning(f"Could not resolve short URL {url}: {e}")
        return url


def detect_platform(url: str) -> str:
    """كشف المنصة من الرابط / Detect platform from URL"""
    url_lower = url.lower()
    if "tiktok.com" in url_lower:
        return "tiktok"
    if "instagram.com" in url_lower:
        return "instagram"
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    if "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "facebook"
    return "other"


def extract_url(text: str) -> str | None:
    """
    استخراج الرابط من النص
    Extract URL from text, handles shortened URLs too
    """
    match = URL_PATTERN.search(text)
    if match:
        return match.group(0)

    general_url = re.search(r"https?://[^\s]+", text)
    if general_url:
        return general_url.group(0)

    return None


def human_size(size_bytes: int) -> str:
    """تحويل الحجم إلى صيغة مقروءة / Convert bytes to human-readable size"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_ydl_opts(output_path: str, platform: str = "other", cookies_file: str | None = None) -> dict:
    """
    إعدادات yt-dlp للتحميل مع headers مخصصة لكل منصة
    yt-dlp download options with platform-specific headers
    """
    common_headers = {
        "User-Agent": MOBILE_UA if platform in ("tiktok", "instagram") else DESKTOP_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }

    base_opts = {
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "writesubtitles": False,
        "writethumbnail": False,
        "http_headers": common_headers,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
    }

    if cookies_file:
        base_opts["cookiefile"] = cookies_file

    if platform == "tiktok":
        base_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best",
            "http_headers": {
                "User-Agent": (
                    "com.zhiliaoapp.musically/2022600030 "
                    "(Linux; U; Android 10; en_US; Pixel 4; "
                    "Build/QQ3A.200805.001; Cronet/58.0.2991.0)"
                ),
            },
            "extractor_args": {
                "tiktok": {
                    "webpage_download": ["0"],
                    "api_hostname": ["api22-normal-c-useast2a.tiktokv.com"],
                }
            },
        })
    elif platform == "instagram":
        # --- تعديل Instagram: استخدام yt-dlp بدلاً من instaloader ---
        # Instagram public content via yt-dlp without login credentials
        base_opts.update({
            "format": "best[height<=720]/best",
            "extractor_args": {
                "instagram": {
                    "username": ["__bypass"],
                },
            },
        })
    elif platform == "twitter":
        base_opts.update({
            "format": (
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                "bestvideo[ext=mp4]+bestaudio/"
                "best[ext=mp4]/best"
            ),
        })
    else:
        base_opts.update({
            "format": (
                "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/"
                "bestvideo[height<=720]+bestaudio/"
                "best[height<=720]/"
                "best[filesize<50M]/"
                "best"
            ),
        })

    return base_opts


# ===== تحميل Instagram عبر yt-dlp (بدون instaloader) =====
# Download Instagram public content using yt-dlp — no login required

def _download_instagram_ytdlp(url: str, tmp_dir: str) -> str | None:
    """
    تحميل محتوى Instagram العام باستخدام yt-dlp بدون بيانات دخول.
    Download public Instagram content using yt-dlp without login.
    يعمل مع: منشورات، ريلز، IGTV / Works with: posts, reels, IGTV
    """
    output_path = os.path.join(tmp_dir, "%(id)s.%(ext)s")
    ydl_opts = get_ydl_opts(output_path, platform="instagram")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None
            # البحث عن الملف المُحمَّل / Find the downloaded file
            downloaded = list(Path(tmp_dir).glob("*"))
            if downloaded:
                return str(max(downloaded, key=lambda f: f.stat().st_size))
    except Exception as e:
        logger.warning(f"Instagram yt-dlp failed: {e}")

    return None


# ===== تحميل TikTok عبر API المباشر =====

def _download_tiktok_api(url: str, tmp_dir: str) -> str | None:
    """
    تحميل TikTok عبر tikwm.com API (أكثر موثوقية من yt-dlp للتيك توك)
    Download TikTok via tikwm.com API — more reliable than yt-dlp
    """
    try:
        api_url = "https://www.tikwm.com/api/"
        resp = requests.post(
            api_url,
            data={"url": url, "hd": 1},
            headers={"User-Agent": DESKTOP_UA},
            timeout=15,
        )
        data = resp.json()
        if data.get("code") != 0:
            logger.warning(f"tikwm API error: {data}")
            return None

        play_url = data["data"].get("hdplay") or data["data"].get("play")
        if not play_url:
            return None

        output_file = os.path.join(tmp_dir, "tiktok_video.mp4")
        video_resp = requests.get(
            play_url,
            headers={"User-Agent": DESKTOP_UA, "Referer": "https://www.tiktok.com/"},
            stream=True,
            timeout=60,
        )
        with open(output_file, "wb") as f:
            for chunk in video_resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        if os.path.getsize(output_file) > 0:
            return output_file

    except Exception as e:
        logger.warning(f"tikwm API failed: {e}")

    return None


# ===== تحميل Facebook مع محاولة بدون كوكيز أولاً =====
# Facebook download: try without cookies first, then with cookies

def _download_facebook(url: str, tmp_dir: str) -> str | None:
    """
    محاولة تحميل Facebook:
    1. بدون كوكيز أولاً (للمحتوى العام)
    2. مع كوكيز FACEBOOK_COOKIES إذا فشلت الخطوة 1
    
    Facebook download strategy:
    1. Try without cookies first (public content)
    2. Try with FACEBOOK_COOKIES env var if step 1 fails
    """
    output_path = os.path.join(tmp_dir, "%(id)s.%(ext)s")

    # --- المحاولة 1: بدون كوكيز / Attempt 1: No cookies ---
    logger.info("Facebook: trying without cookies first...")
    ydl_opts_no_cookies = get_ydl_opts(output_path, platform="other")
    try:
        with yt_dlp.YoutubeDL(ydl_opts_no_cookies) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                files = list(Path(tmp_dir).glob("*"))
                if files:
                    result = str(max(files, key=lambda f: f.stat().st_size))
                    logger.info("Facebook: downloaded without cookies")
                    return result
    except Exception as e:
        logger.warning(f"Facebook no-cookies attempt failed: {e}")

    # --- المحاولة 2: مع كوكيز / Attempt 2: With cookies ---
    fb_cookies = os.environ.get("FACEBOOK_COOKIES", "").strip()
    if fb_cookies:
        logger.info("Facebook: retrying with FACEBOOK_COOKIES...")
        cookies_file = os.path.join(tmp_dir, "fb_cookies.txt")
        with open(cookies_file, "w", encoding="utf-8") as f:
            f.write(fb_cookies)

        ydl_opts_with_cookies = get_ydl_opts(output_path, platform="other", cookies_file=cookies_file)
        try:
            with yt_dlp.YoutubeDL(ydl_opts_with_cookies) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    files = list(Path(tmp_dir).glob("*"))
                    non_cookie = [f for f in files if f.name != "fb_cookies.txt"]
                    if non_cookie:
                        result = str(max(non_cookie, key=lambda f: f.stat().st_size))
                        logger.info("Facebook: downloaded with cookies")
                        return result
        except Exception as e:
            logger.warning(f"Facebook with-cookies attempt failed: {e}")

    return None


# ===== دالة التحميل العامة عبر yt-dlp =====

def _download_with_ytdlp(url: str, tmp_dir: str, platform: str) -> str | None:
    """
    تحميل عام باستخدام yt-dlp مع إعادة محاولة تلقائية مرة واحدة عند الفشل
    Generic yt-dlp download with one automatic retry on transient failure
    """
    output_path = os.path.join(tmp_dir, "%(id)s.%(ext)s")
    ydl_opts = get_ydl_opts(output_path, platform=platform)

    for attempt in range(1, 3):  # محاولتان / two attempts
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    continue
                files = list(Path(tmp_dir).glob("*"))
                if files:
                    return str(max(files, key=lambda f: f.stat().st_size))
        except yt_dlp.utils.DownloadError as e:
            logger.warning(f"yt-dlp attempt {attempt} failed for {platform}: {e}")
            if attempt < 2:
                time.sleep(2)  # انتظر ثانيتين قبل إعادة المحاولة
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}: {e}")
            break

    return None


# ===== دالة self-ping لمنع النوم (asyncio) =====
# Self-ping function to prevent platform sleep using asyncio

async def ping_self():
    """
    ترسل طلب داخلي كل 3 دقائق لنفسها لمنع النوم على المنصات المجانية.
    Sends an internal HTTP ping to itself every 3 minutes to prevent sleep
    on free-tier hosting platforms (Render, Railway, etc.).
    """
    if not SELF_URL:
        logger.info("ping_self: SELF_URL not set, self-ping disabled.")
        return

    ping_url = f"{SELF_URL.rstrip('/')}/health"
    logger.info(f"ping_self: will ping {ping_url} every 3 minutes")

    while True:
        await asyncio.sleep(180)  # 3 دقائق / 3 minutes
        try:
            resp = requests.get(ping_url, timeout=10)
            logger.info(f"ping_self: {resp.status_code} from {ping_url}")
        except Exception as e:
            logger.warning(f"ping_self failed: {e}")


# ===== معالجات الأوامر / Command Handlers =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /help"""
    await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.MARKDOWN)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /about"""
    await update.message.reply_text(ABOUT_MESSAGE, parse_mode=ParseMode.MARKDOWN)


# ===== معالج الرسائل الرئيسي / Main Message Handler =====

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    المعالج الرئيسي للرسائل - يستقبل الروابط ويحمّلها
    Main message handler - receives URLs and downloads them
    """
    message = update.message
    text = message.text.strip()

    # --- استخراج والتحقق من الرابط / Extract and validate URL ---
    url = extract_url(text)

    if not url:
        await message.reply_text(
            "⚠️ لم أتمكن من العثور على رابط صالح في رسالتك.\n"
            "الرجاء إرسال رابط مباشر من YouTube أو Instagram أو TikTok أو Twitter أو Facebook.\n\n"
            "اكتب /help للمساعدة.",
        )
        return

    # التحقق من صحة الرابط / Validate URL format
    if not is_valid_url(url):
        await message.reply_text(
            "⚠️ الرابط الذي أرسلته يبدو غير صالح. يرجى التحقق منه والمحاولة مجدداً.",
        )
        return

    status_msg = await message.reply_text(
        "⏳ *جارٍ معالجة الرابط...*",
        parse_mode=ParseMode.MARKDOWN,
    )

    # إنشاء مجلد مؤقت — يُنظَّف دائماً حتى عند الخطأ / Temp dir cleaned up with try/finally
    tmp_dir = tempfile.mkdtemp(prefix="tgbot_dl_")

    try:
        loop = asyncio.get_running_loop()

        # حل الروابط المختصرة / Resolve shortened URLs
        resolved_url = await loop.run_in_executor(None, resolve_short_url, url)
        platform = detect_platform(resolved_url)
        logger.info(f"URL: {resolved_url} | Platform: {platform}")

        await status_msg.edit_text(
            "📥 *جارٍ التحميل...*\n\n⏳ يرجى الانتظار...",
            parse_mode=ParseMode.MARKDOWN,
        )

        downloaded_file = None

        # ====== TikTok: tikwm API أولاً ثم yt-dlp ======
        if platform == "tiktok":
            downloaded_file = await loop.run_in_executor(
                None, _download_tiktok_api, resolved_url, tmp_dir
            )
            if not downloaded_file:
                downloaded_file = await loop.run_in_executor(
                    None, _download_with_ytdlp, resolved_url, tmp_dir, platform
                )

        # ====== Instagram: yt-dlp بدون instaloader ======
        elif platform == "instagram":
            downloaded_file = await loop.run_in_executor(
                None, _download_instagram_ytdlp, resolved_url, tmp_dir
            )
            # إعادة محاولة بـ yt-dlp العام إذا فشل المحاولة الأولى
            if not downloaded_file:
                downloaded_file = await loop.run_in_executor(
                    None, _download_with_ytdlp, resolved_url, tmp_dir, platform
                )

        # ====== Facebook: بدون كوكيز أولاً ثم مع كوكيز ======
        elif platform == "facebook":
            downloaded_file = await loop.run_in_executor(
                None, _download_facebook, resolved_url, tmp_dir
            )

        # ====== بقية المنصات / Other platforms ======
        else:
            downloaded_file = await loop.run_in_executor(
                None, _download_with_ytdlp, resolved_url, tmp_dir, platform
            )

        # --- التحقق من الملف المُحمَّل / Verify downloaded file ---
        if not downloaded_file or not os.path.exists(downloaded_file):
            error_msg = PLATFORM_ERROR_MESSAGES.get(platform, PLATFORM_ERROR_MESSAGES["other"])
            await status_msg.edit_text(error_msg)
            return

        file_size = os.path.getsize(downloaded_file)

        if file_size > MAX_FILE_SIZE_BYTES:
            await status_msg.edit_text(
                f"⚠️ حجم الملف ({human_size(file_size)}) يتجاوز الحد الأقصى المسموح به في تيليجرام (50 MB).\n"
                "جرّب رابطاً لفيديو بجودة أقل."
            )
            return

        # --- إرسال الملف / Send file ---
        await status_msg.edit_text("📤 *جارٍ الإرسال...*", parse_mode=ParseMode.MARKDOWN)

        file_ext = Path(downloaded_file).suffix.lower()
        caption = f"⚡ *Alpha Downloader* | منصة الفا\n📦 الحجم: {human_size(file_size)}"

        with open(downloaded_file, "rb") as f:
            if file_ext in (".jpg", ".jpeg", ".png", ".webp"):
                await message.reply_photo(photo=f, caption=caption, parse_mode=ParseMode.MARKDOWN)
            elif file_ext == ".mp3":
                await message.reply_audio(audio=f, caption=caption, parse_mode=ParseMode.MARKDOWN)
            else:
                await message.reply_video(
                    video=f,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    supports_streaming=True,
                )

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Unhandled error for {url}: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ حدث خطأ غير متوقع أثناء معالجة طلبك.\n"
            "يرجى المحاولة مرة أخرى بعد قليل.\n\n"
            "اكتب /help للمساعدة."
        )

    finally:
        # --- تنظيف الملفات المؤقتة دائماً حتى عند الخطأ / Always clean temp files ---
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            logger.info(f"Cleaned up tmp_dir: {tmp_dir}")
        except Exception as cleanup_err:
            logger.warning(f"Could not clean tmp_dir {tmp_dir}: {cleanup_err}")


# ===== نقطة الدخول الرئيسية / Main Entry Point =====

def main() -> None:
    """إعداد وتشغيل البوت / Set up and run the bot"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set!")

    # تشغيل خادم keep-alive في خيط منفصل / Start keep-alive server in background thread
    keep_alive()
    logger.info("Keep-alive server started.")

    application = Application.builder().token(token).build()

    # تسجيل معالجات الأوامر / Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))

    # معالج الرسائل النصية / Text message handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Alpha Downloader Bot is starting...")

    # تشغيل self-ping بشكل غير متزامن مع البوت / Run self-ping alongside the bot
    async def post_init(app):
        asyncio.create_task(ping_self())

    application.post_init = post_init

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
