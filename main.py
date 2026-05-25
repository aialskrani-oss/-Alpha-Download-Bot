"""
main.py - بوت تليجرام لتحميل الفيديوهات والصور
Telegram Bot for downloading videos and images from social media

المنصات المدعومة / Supported Platforms:
- YouTube
- Instagram (منشورات، ريلز، قصص)
- TikTok
- Twitter/X
- Facebook
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
from pathlib import Path

import requests
import yt_dlp
import instaloader
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
• Instagram (منشورات، ريلز، قصص) 📸
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
• ⚙️ Instagram — يتطلب إعداد حساب (راجع أدناه)
• ✅ Twitter/X — يعمل للتغريدات التي تحوي فيديو
• ⚙️ Facebook — يتطلب كوكيز (راجع أدناه)

*إعداد Instagram:*
أضف `INSTAGRAM_USERNAME` و `INSTAGRAM_PASSWORD` كـ Secrets
في Replit لتفعيل التحميل التلقائي من إنستغرام.

⚠️ *قيود:*
• الحد الأقصى لحجم الملف: 50 ميجابايت
• المحتوى الخاص لا يمكن تحميله

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

📊 *الإصدار:* 1.0.0

_جميع الحقوق محفوظة لمنصة الفا © Alpha Platform_
"""


# ===== دوال المساعدة / Helper Functions =====

def resolve_short_url(url: str) -> str:
    """
    حل الروابط المختصرة — يأخذ أول Location header (قبل أن تكتشف المنصة البوت)
    Resolve shortened URLs by reading the first redirect Location header only.
    This avoids bot-detection pages like tiktok.com/in/about.
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
        # الخطوة 1: احصل على أول redirect فقط (قبل أي صفحة كشف بوت)
        resp = requests.get(
            url, headers=headers,
            allow_redirects=False,   # لا تتبع — نريد Location header الأولى فقط
            timeout=10,
        )
        location = resp.headers.get("Location", "")
        logger.info(f"Short URL first redirect: {url} -> {location or '(none)'}")

        # إذا حصلنا على رابط تيك توك حقيقي (يحتوي /video/) استخدمه
        if location and "tiktok.com" in location and "/video/" in location:
            return location

        # الخطوة 2: إذا لم ينجح، اتبع جميع التوجيهات
        resp2 = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        final = resp2.url
        logger.info(f"Resolved {url} -> {final}")

        # تجنّب صفحات الكشف مثل /in/about
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

    # البحث عن أي رابط في النص / Look for any URL in text
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


def get_ydl_opts(output_path: str, platform: str = "other", is_audio_only: bool = False) -> dict:
    """
    إعدادات yt-dlp للتحميل مع headers مخصصة لكل منصة
    yt-dlp download options with platform-specific headers
    """
    # Headers مشتركة تحاكي متصفح حقيقي / Common headers mimicking real browser
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
        # إعادة المحاولة عند الفشل / Retry on failure
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
    }

    if is_audio_only:
        base_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }],
        })
        return base_opts

    # إعدادات خاصة بكل منصة / Platform-specific settings
    if platform == "tiktok":
        # استخدام API المباشر بدلاً من صفحة الويب لتجاوز حماية البوت
        base_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best",
            "http_headers": {
                # User-Agent لتطبيق TikTok Android — يجاوز الحماية
                "User-Agent": (
                    "com.zhiliaoapp.musically/2022600030 "
                    "(Linux; U; Android 10; en_US; Pixel 4; "
                    "Build/QQ3A.200805.001; Cronet/58.0.2991.0)"
                ),
            },
            "extractor_args": {
                "tiktok": {
                    "webpage_download": ["0"],  # تجاوز صفحة الويب واستخدام API
                    "api_hostname": ["api22-normal-c-useast2a.tiktokv.com"],
                }
            },
        })
    elif platform == "instagram":
        base_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best",
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


# ===== معالجات الأوامر / Command Handlers =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /help"""
    await update.message.reply_text(
        HELP_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /about"""
    await update.message.reply_text(
        ABOUT_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
    )


# ===== معالج الرسائل الرئيسي / Main Message Handler =====

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    المعالج الرئيسي للرسائل - يستقبل الروابط ويحمّلها
    Main message handler - receives URLs and downloads them
    """
    message = update.message
    text = message.text.strip()

    # استخراج الرابط من الرسالة
    url = extract_url(text)

    if not url:
        await message.reply_text(
            "⚠️ لم أتمكن من العثور على رابط صالح في رسالتك.\n"
            "الرجاء إرسال رابط مباشر من YouTube أو Instagram أو TikTok أو Twitter أو Facebook.\n\n"
            "اكتب /help للمساعدة.",
        )
        return

    # إرسال رسالة انتظار
    status_msg = await message.reply_text(
        "⏳ *جارٍ معالجة الرابط...*",
        parse_mode=ParseMode.MARKDOWN,
    )

    # إنشاء مجلد مؤقت للتحميل
    tmp_dir = tempfile.mkdtemp(prefix="tgbot_dl_")

    try:
        loop = asyncio.get_running_loop()

        # حل الروابط المختصرة أولاً (vt.tiktok.com, t.co, ...)
        resolved_url = await loop.run_in_executor(
            None, resolve_short_url, url
        )
        platform = detect_platform(resolved_url)
        logger.info(f"URL: {resolved_url} | Platform: {platform}")

        # تحميل المحتوى مباشرة (بدون خطوة جلب المعلومات المنفصلة)
        await status_msg.edit_text(
            "📥 *جارٍ التحميل...*\n\n"
            "⏳ يرجى الانتظار...",
            parse_mode=ParseMode.MARKDOWN,
        )

        output_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")
        ydl_opts = get_ydl_opts(output_template, platform=platform)

        downloaded_file = None

        # ====== TikTok: استخدم tikwm API المباشر (أكثر موثوقية) ======
        if platform == "tiktok":
            downloaded_file = await loop.run_in_executor(
                None, _download_tiktok_api, resolved_url, tmp_dir
            )
            if not downloaded_file:
                await status_msg.edit_text(
                    "❌ *فشل في تحميل فيديو TikTok.*\n\n"
                    "• تأكد أن الفيديو عام وليس خاصاً\n"
                    "• حاول مرة أخرى لاحقاً",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

        # ====== Instagram: جرّب yt-dlp ثم instaloader ======
        elif platform == "instagram":
            try:
                downloaded_file = await loop.run_in_executor(
                    None, _download, resolved_url, ydl_opts, tmp_dir
                )
            except yt_dlp.utils.DownloadError:
                logger.info("yt-dlp failed for Instagram, trying instaloader...")
                await status_msg.edit_text(
                    "🔄 *جارٍ المحاولة بطريقة أخرى...*",
                    parse_mode=ParseMode.MARKDOWN,
                )
                downloaded_file = await loop.run_in_executor(
                    None, _download_instagram, resolved_url, tmp_dir
                )
            if not downloaded_file:
                ig_user = os.environ.get("INSTAGRAM_USERNAME", "").strip()
                if ig_user:
                    ig_note = f"⚠️ تم تسجيل الدخول بحساب `{ig_user}` لكن التحميل فشل.\nربما الفيديو خاص أو محذوف."
                else:
                    ig_note = (
                        "💡 *نصيحة للمشرف:* أضف `INSTAGRAM_USERNAME` و `INSTAGRAM_PASSWORD`\n"
                        "كـ Secrets في Replit لتفعيل التحميل تلقائياً."
                    )
                await status_msg.edit_text(
                    "🔐 *Instagram يتطلب تسجيل دخول*\n\n"
                    "إنستغرام قيّد التحميل المباشر بشكل صارم.\n\n"
                    f"{ig_note}\n\n"
                    "جرّب هذه البدائل:\n"
                    "• [snapinsta.app](https://snapinsta.app)\n"
                    "• [igram.world](https://igram.world)\n"
                    "• [ssinstagram.com](https://ssinstagram.com)",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
                return

        # ====== Facebook: جرّب yt-dlp (مع كوكيز اختيارية) ======
        elif platform == "facebook":
            downloaded_file = await loop.run_in_executor(
                None, _download_facebook, resolved_url, tmp_dir
            )
            if not downloaded_file:
                await status_msg.edit_text(
                    "📘 *تعذّر تحميل فيديو Facebook*\n\n"
                    "Facebook قيّد التحميل المباشر.\n\n"
                    "جرّب هذه البدائل:\n"
                    "• [fdown.net](https://fdown.net)\n"
                    "• [savefrom.net](https://en.savefrom.net)\n"
                    "• [getfvid.com](https://www.getfvid.com)",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
                return

        # ====== باقي المنصات: yt-dlp ======
        else:
            downloaded_file = await loop.run_in_executor(
                None, _download, resolved_url, ydl_opts, tmp_dir
            )

        if not downloaded_file:
            await status_msg.edit_text(
                "❌ *فشل في تحميل المحتوى.*\n\n"
                "حاول مرة أخرى لاحقاً أو تأكد من صحة الرابط.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # التحقق من حجم الملف
        file_size = os.path.getsize(downloaded_file)

        if file_size > MAX_FILE_SIZE_BYTES:
            await status_msg.edit_text(
                f"⚠️ *الملف كبير جداً!*\n\n"
                f"• حجم الملف: {human_size(file_size)}\n"
                f"• الحد الأقصى المسموح: {MAX_FILE_SIZE_MB} ميجابايت\n\n"
                f"تليجرام لا يسمح برفع ملفات أكبر من {MAX_FILE_SIZE_MB} ميجابايت.\n"
                f"جرب رابطاً لفيديو أقصر أو بجودة أقل.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # استخدام اسم الملف كعنوان
        title = Path(downloaded_file).stem[:50] or "Alpha Downloader"

        # إرسال الملف
        await status_msg.edit_text(
            "📤 *جارٍ الإرسال...*",
            parse_mode=ParseMode.MARKDOWN,
        )

        ext = Path(downloaded_file).suffix.lower()

        if ext in (".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v"):
            await _send_video(message, downloaded_file, title, file_size)
        elif ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            await _send_photo(message, downloaded_file, title)
        elif ext in (".mp3", ".m4a", ".ogg", ".wav", ".flac"):
            await _send_audio(message, downloaded_file, title)
        else:
            await _send_document(message, downloaded_file, title, file_size)

        # حذف رسالة الانتظار بعد الإرسال
        await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        final_url = locals().get("resolved_url", url)
        logger.error(f"yt-dlp DownloadError for {final_url}: {error_msg}")
        await status_msg.edit_text(
            _format_download_error(error_msg),
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ *حدث خطأ غير متوقع.*\n\n"
            "الرجاء المحاولة مرة أخرى لاحقاً.",
            parse_mode=ParseMode.MARKDOWN,
        )

    finally:
        # تنظيف الملفات المؤقتة / Clean up temp files
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


# ===== دوال التنفيذ المتزامن / Sync Execution Functions =====


def _download(url: str, ydl_opts: dict, tmp_dir: str) -> str | None:
    """
    تحميل المحتوى (تنفيذ متزامن) مع دعم إعادة المحاولة
    Download content (sync execution) with retry support
    """
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # البحث عن الملف المحمّل في المجلد المؤقت (تجاهل ملفات .part غير المكتملة)
        files = [
            f for f in Path(tmp_dir).iterdir()
            if f.is_file() and f.suffix != ".part"
        ]
        if not files:
            return None

        return str(max(files, key=lambda f: f.stat().st_size))

    except yt_dlp.utils.DownloadError:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None


def _download_tiktok_api(url: str, tmp_dir: str) -> str | None:
    """
    تحميل فيديو TikTok مباشرة عبر tikwm.com API (مجاني، بدون مفتاح)
    Download TikTok video via tikwm.com API - no auth needed, works reliably.
    """
    try:
        logger.info(f"Trying tikwm.com API for: {url}")
        resp = requests.post(
            "https://www.tikwm.com/api/",
            data={"url": url, "hd": "1"},
            timeout=20,
        )
        data = resp.json()

        if data.get("code") != 0:
            logger.error(f"tikwm API error: {data.get('msg')}")
            return None

        video_data = data.get("data", {})
        # تفضيل الجودة العالية، ثم الاحتياطية
        download_url = video_data.get("hdplay") or video_data.get("play")

        if not download_url:
            logger.error("tikwm API: no video URL in response")
            return None

        # تحميل الفيديو مباشرة
        video_resp = requests.get(
            download_url,
            stream=True,
            timeout=60,
            headers={
                "User-Agent": MOBILE_UA,
                "Referer": "https://www.tiktok.com/",
            },
        )
        video_resp.raise_for_status()

        out_path = os.path.join(tmp_dir, "tiktok_video.mp4")
        with open(out_path, "wb") as f:
            for chunk in video_resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

        size = os.path.getsize(out_path)
        if size > 0:
            logger.info(f"tikwm download success: {size} bytes")
            return out_path

        return None

    except Exception as e:
        logger.error(f"tikwm API error: {e}")
        return None


def _get_instaloader_with_session() -> "instaloader.Instaloader":
    """
    ينشئ Instaloader ويسجّل الدخول إذا كانت بيانات الاعتماد متوفرة.
    يحفظ الجلسة في ملف لتجنب تسجيل الدخول في كل مرة.
    """
    SESSION_FILE = "/tmp/instaloader_session"

    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern="",
        quiet=True,
    )

    ig_user = os.environ.get("INSTAGRAM_USERNAME", "").strip()
    ig_pass = os.environ.get("INSTAGRAM_PASSWORD", "").strip()

    if not ig_user or not ig_pass:
        return L  # بدون بيانات اعتماد، رجّع Instaloader بدون دخول

    # حاول تحميل الجلسة المحفوظة أولاً (أسرع وأأمن)
    try:
        L.load_session_from_file(ig_user, SESSION_FILE)
        logger.info("Instagram: loaded saved session")
        return L
    except Exception:
        pass  # لا يوجد ملف جلسة — سنسجل الدخول من جديد

    # سجّل الدخول بالبيانات وحفظ الجلسة
    try:
        L.login(ig_user, ig_pass)
        L.save_session_to_file(SESSION_FILE)
        logger.info(f"Instagram: logged in as {ig_user}")
    except instaloader.exceptions.BadCredentialsException:
        logger.error("Instagram: bad credentials (wrong username/password)")
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        logger.error("Instagram: 2FA required — disable 2FA or use app password")
    except Exception as e:
        logger.error(f"Instagram login error: {e}")

    return L


def _download_instagram(url: str, tmp_dir: str) -> str | None:
    """
    تحميل من Instagram باستخدام instaloader.
    يدعم تسجيل الدخول التلقائي إذا كانت INSTAGRAM_USERNAME/PASSWORD متوفرة.
    """
    import re as _re

    match = _re.search(r"/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
    if not match:
        logger.error(f"Could not extract Instagram shortcode from {url}")
        return None

    shortcode = match.group(1)
    logger.info(f"Trying instaloader for shortcode: {shortcode}")

    try:
        L = _get_instaloader_with_session()
        L.dirname_pattern = tmp_dir
        L.filename_pattern = "{shortcode}"

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=Path(tmp_dir))

        files = [
            f for f in Path(tmp_dir).rglob("*")
            if f.is_file() and f.suffix in (".mp4", ".jpg", ".jpeg", ".png")
        ]
        if not files:
            return None
        return str(max(files, key=lambda f: f.stat().st_size))

    except instaloader.exceptions.LoginRequiredException:
        logger.warning("Instagram: login required")
        return None
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        logger.warning("Instagram: private profile")
        return None
    except Exception as e:
        logger.error(f"instaloader error: {e}")
        return None


def _download_facebook(url: str, tmp_dir: str) -> str | None:
    """
    تحميل من Facebook باستخدام yt-dlp مع كوكيز اختيارية.
    إذا توفرت FACEBOOK_COOKIES كمتغير بيئة (Netscape format) تُستخدم تلقائياً.
    """
    cookie_file = None

    fb_cookies = os.environ.get("FACEBOOK_COOKIES", "").strip()
    if fb_cookies:
        cookie_file = os.path.join(tmp_dir, "fb_cookies.txt")
        with open(cookie_file, "w") as f:
            f.write(fb_cookies)
        logger.info("Facebook: using cookies from env")

    opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "http_headers": {
            "User-Agent": DESKTOP_UA,
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    if cookie_file:
        opts["cookiefile"] = cookie_file

    try:
        logger.info(f"Trying yt-dlp for Facebook: {url}")
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        files = [
            f for f in Path(tmp_dir).iterdir()
            if f.is_file() and f.suffix != ".part" and f.name != "fb_cookies.txt"
        ]
        if not files:
            return None
        return str(max(files, key=lambda f: f.stat().st_size))

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Facebook yt-dlp error: {e}")
        return None
    except Exception as e:
        logger.error(f"Facebook download error: {e}")
        return None



def _format_download_error(error_msg: str) -> str:
    """
    تحويل رسائل خطأ yt-dlp إلى رسائل مفهومة للمستخدم
    Convert yt-dlp error messages to user-friendly messages
    """
    error_lower = error_msg.lower()

    if "private" in error_lower:
        return "🔒 *المحتوى خاص*\n\nهذا المحتوى خاص ولا يمكن تحميله."
    elif "unavailable" in error_lower or "not available" in error_lower:
        return "🚫 *المحتوى غير متاح*\n\nالفيديو محذوف أو غير متاح في منطقتك."
    elif "copyright" in error_lower:
        return "⚖️ *محتوى محمي بحقوق النشر*\n\nلا يمكن تحميل هذا المحتوى بسبب قيود حقوق النشر."
    elif "login" in error_lower or "sign in" in error_lower or "rate-limit" in error_lower or "rate limit" in error_lower:
        return (
            "🔐 *المحتوى يتطلب تسجيل دخول*\n\n"
            "هذه المنصة قيّدت التحميل المباشر.\n"
            "جرّب:\n"
            "• نسخ الفيديو من التطبيق مباشرة\n"
            "• التأكد من أن المحتوى عام وليس خاصاً\n"
            "• المحاولة مرة أخرى لاحقاً"
        )
    elif "geo" in error_lower or "region" in error_lower:
        return "🌍 *محظور في منطقتك*\n\nهذا المحتوى غير متاح في منطقتنا."
    elif "http error 404" in error_lower:
        return "❌ *الرابط غير موجود*\n\nتأكد من صحة الرابط وحاول مرة أخرى."
    elif "unsupported url" in error_lower:
        return (
            "❌ *الرابط غير مدعوم*\n\n"
            "هذا الموقع غير مدعوم حالياً.\n"
            "المنصات المدعومة: YouTube، Instagram، TikTok، Twitter، Facebook"
        )
    else:
        return (
            "❌ *فشل في التحميل*\n\n"
            "• تأكد من صحة الرابط\n"
            "• قد يكون المحتوى محذوف أو خاص\n"
            "• حاول مرة أخرى لاحقاً"
        )


# ===== دوال الإرسال / Sending Functions =====

async def _send_video(message, file_path: str, title: str, file_size: int) -> None:
    """إرسال الفيديو للمستخدم"""
    caption = (
        f"🎬 *{title}*\n"
        f"📦 الحجم: {human_size(file_size)}"
    )
    with open(file_path, "rb") as f:
        await message.reply_video(
            video=f,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            supports_streaming=True,
            read_timeout=120,
            write_timeout=120,
            connect_timeout=30,
        )


async def _send_photo(message, file_path: str, title: str) -> None:
    """إرسال الصورة للمستخدم بجودة عالية"""
    caption = f"🖼️ *{title}*"
    try:
        with open(file_path, "rb") as f:
            await message.reply_photo(
                photo=f,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                read_timeout=60,
                write_timeout=60,
            )
    except Exception:
        # إذا فشل إرسال الصورة، أرسلها كملف للحفاظ على الجودة
        with open(file_path, "rb") as f:
            await message.reply_document(
                document=f,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
            )


async def _send_audio(message, file_path: str, title: str) -> None:
    """إرسال الصوت للمستخدم"""
    caption = f"🎵 *{title}*"
    with open(file_path, "rb") as f:
        await message.reply_audio(
            audio=f,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            read_timeout=120,
            write_timeout=120,
        )


async def _send_document(message, file_path: str, title: str, file_size: int) -> None:
    """إرسال الملف كمستند"""
    caption = (
        f"📄 *{title}*\n"
        f"📦 الحجم: {human_size(file_size)}"
    )
    with open(file_path, "rb") as f:
        await message.reply_document(
            document=f,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            read_timeout=120,
            write_timeout=120,
        )


# ===== معالج الأخطاء / Error Handler =====

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء العامة"""
    logger.error("Exception while handling an update:", exc_info=context.error)


# ===== الدالة الرئيسية / Main Function =====

def main() -> None:
    """تشغيل البوت"""
    # التحقق من وجود التوكن
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error(
            "خطأ: متغير البيئة TELEGRAM_BOT_TOKEN غير موجود!\n"
            "احصل على التوكن من @BotFather على تليجرام"
        )
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

    # تشغيل خادم keep_alive لإبقاء البوت حياً 24/7
    keep_alive()
    logger.info("✅ خادم keep_alive يعمل على المنفذ 8080")

    # إنشاء تطبيق البوت
    app = Application.builder().token(token).build()

    # تسجيل معالجات الأوامر
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))

    # تسجيل معالج الرسائل (لأي نص يُرسل للبوت)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # تسجيل معالج الأخطاء
    app.add_error_handler(error_handler)

    logger.info("🤖 البوت يعمل الآن... اضغط Ctrl+C للإيقاف")
    logger.info("Bot is running... Press Ctrl+C to stop")

    # تشغيل البوت
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
