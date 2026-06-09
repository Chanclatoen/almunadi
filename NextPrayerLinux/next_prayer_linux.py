import os
import re
import json
import threading
import time
import subprocess
import shutil
from datetime import datetime, timedelta, date

import requests
import pystray
from PIL import Image, ImageDraw, ImageFont

APP_NAME = "Next Prayer (Mawaqit)"
APP_VERSION = "1.0.0"
TAG_PREFIX = "linux-v"
RELEASES_URL = "https://api.github.com/repos/Chanclatoen/next-prayer-mawaqit/releases"
REPO_RELEASES_PAGE = "https://github.com/Chanclatoen/next-prayer-mawaqit/releases"
PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
PRAYER_ICONS = {
    "Fajr": "☀",
    "Dhuhr": "☀",
    "Jumuah": "☀",
    "Asr": "⛅",
    "Maghrib": "\U0001f305",
    "Isha": "☾",
}
API_BASE = "https://mawaqit.net/api/2.0/mosque"

# XDG-compliant config directory
_XDG_CONFIG = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
APP_DATA_DIR = os.path.join(_XDG_CONFIG, "NextPrayer")
os.makedirs(APP_DATA_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "settings.json")
CACHE_FILE = os.path.join(APP_DATA_DIR, "cache.json")

PRAYER_COLORS = {
    "Fajr": "#FFB74D",
    "Dhuhr": "#FFEB3B",
    "Jumuah": "#FFEB3B",
    "Asr": "#FFA726",
    "Maghrib": "#EF6C00",
    "Isha": "#648CC8",
}

PRAYER_COLORS_RGB = {
    "Fajr": (255, 183, 77),
    "Dhuhr": (255, 235, 59),
    "Jumuah": (255, 235, 59),
    "Asr": (255, 167, 38),
    "Maghrib": (239, 108, 0),
    "Isha": (100, 140, 200),
}

BG_COLOR = "#1a1a2e"
CARD_COLOR = "#16213e"
CARD_HOVER = "#1a2744"
ACCENT = "#4a90d9"
TEXT_PRIMARY = "#e8e8e8"
TEXT_SECONDARY = "#8899aa"
TEXT_DIM = "#556677"
HIGHLIGHT_BG = "#1e3a5f"
FONT_FAMILY = "DejaVu Sans"


# ---------------------------------------------------------------------------
# Translations (i18n)
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "en": {
        "prayer_fajr": "Fajr",
        "prayer_dhuhr": "Dhuhr",
        "prayer_asr": "Asr",
        "prayer_maghrib": "Maghrib",
        "prayer_isha": "Isha",
        "prayer_shuruq": "Shuruq",
        "prayer_jumuah": "Jumuah",
        "prayer_jumuah2": "Jumuah 2",
        "next_prayer": "Next Prayer",
        "loading": "Loading…",
        "no_mosque": "No mosque set",
        "no_data": "No data loaded",
        "refresh": "Refresh",
        "settings": "Settings",
        "quit": "Quit",
        "notifications": "Prayer notifications",
        "notification_title": "{name} — {time}",
        "notification_body": "It's time for {name} prayer",
        "cached_data": "Using cached data",
        "fetch_error": "Could not fetch times",
        "search": "Search",
        "save": "Save",
        "mosque_url": "Mawaqit URL",
        "find_mosque": "Find Your Mosque",
        "search_hint": "Search by mosque name or city",
        "no_results": "No mosques found",
        "configure_mosque": "Configure mosque",
        "launch_at_login": "Launch at login",
        "iqama": "Iqama",
        "show_prayer_times": "Show Prayer Times",
        "saved_mosques": "Saved Mosques",
        "add_mosque": "Add Current",
        "remove_mosque": "Remove",
        "switch_mosque": "Switch",
        "active": "Active",
        "adhan": "Adhan",
        "adhan_enabled": "Play adhan audio",
        "adhan_path": "Adhan audio file",
        "adhan_browse": "Browse",
        "countdown_format": "Countdown format",
        "countdown_compact": "Compact",
        "countdown_full": "Full",
        "language": "Language",
        "now": "now",
        "paste_url": "Or Paste URL Directly",
        "paste_url_hint": "Go to mawaqit.net, find your mosque, and paste the URL",
        "connected_mosque": "Connected Mosque",
        "mosques": "Mosques",
        "search_failed": "Search failed",
        "no_prayer_times": "No prayer times loaded",
        "update_available": "Update available",
    },
    "ar": {
        "prayer_fajr": "فجر",
        "prayer_dhuhr": "ظهر",
        "prayer_asr": "عصر",
        "prayer_maghrib": "مغرب",
        "prayer_isha": "عشاء",
        "prayer_shuruq": "شروق",
        "prayer_jumuah": "جمعة",
        "prayer_jumuah2": "جمعة 2",
        "next_prayer": "الصلاة القادمة",
        "loading": "جاري التحميل…",
        "no_mosque": "لم يتم تحديد مسجد",
        "no_data": "لا توجد بيانات",
        "refresh": "تحديث",
        "settings": "إعدادات",
        "quit": "خروج",
        "notifications": "إشعارات الصلاة",
        "notification_title": "{name} — {time}",
        "notification_body": "حان وقت صلاة {name}",
        "cached_data": "بيانات مخزنة",
        "fetch_error": "تعذر جلب الأوقات",
        "search": "بحث",
        "save": "حفظ",
        "mosque_url": "رابط مواقيت",
        "find_mosque": "ابحث عن مسجدك",
        "search_hint": "ابحث باسم المسجد أو المدينة",
        "no_results": "لم يتم العثور على مساجد",
        "configure_mosque": "إعداد المسجد",
        "launch_at_login": "بدء عند تسجيل الدخول",
        "iqama": "إقامة",
        "show_prayer_times": "عرض أوقات الصلاة",
        "saved_mosques": "المساجد المحفوظة",
        "add_mosque": "إضافة",
        "remove_mosque": "حذف",
        "switch_mosque": "تبديل",
        "active": "نشط",
        "adhan": "أذان",
        "adhan_enabled": "تشغيل صوت الأذان",
        "adhan_path": "ملف صوت الأذان",
        "adhan_browse": "تصفح",
        "countdown_format": "شكل العد التنازلي",
        "countdown_compact": "مختصر",
        "countdown_full": "كامل",
        "language": "اللغة",
        "now": "الآن",
        "paste_url": "أو الصق الرابط مباشرة",
        "paste_url_hint": "اذهب إلى mawaqit.net وابحث عن مسجدك والصق الرابط",
        "connected_mosque": "المسجد المتصل",
        "mosques": "المساجد",
        "search_failed": "فشل البحث",
        "no_prayer_times": "لا توجد أوقات صلاة",
        "update_available": "تحديث متاح",
    },
    "fr": {
        "prayer_fajr": "Fajr",
        "prayer_dhuhr": "Dhuhr",
        "prayer_asr": "Asr",
        "prayer_maghrib": "Maghrib",
        "prayer_isha": "Isha",
        "prayer_shuruq": "Shuruq",
        "prayer_jumuah": "Joumou'a",
        "prayer_jumuah2": "Joumou'a 2",
        "next_prayer": "Prochaine prière",
        "loading": "Chargement…",
        "no_mosque": "Aucune mosquée configurée",
        "no_data": "Aucune donnée chargée",
        "refresh": "Actualiser",
        "settings": "Paramètres",
        "quit": "Quitter",
        "notifications": "Notifications de prière",
        "notification_title": "{name} — {time}",
        "notification_body": "C'est l'heure de la prière de {name}",
        "cached_data": "Données en cache",
        "fetch_error": "Impossible de récupérer les horaires",
        "search": "Rechercher",
        "save": "Enregistrer",
        "mosque_url": "URL Mawaqit",
        "find_mosque": "Trouver votre mosquée",
        "search_hint": "Rechercher par nom ou ville",
        "no_results": "Aucune mosquée trouvée",
        "configure_mosque": "Configurer la mosquée",
        "launch_at_login": "Lancer au démarrage",
        "iqama": "Iqama",
        "show_prayer_times": "Afficher les horaires",
        "saved_mosques": "Mosquées enregistrées",
        "add_mosque": "Ajouter",
        "remove_mosque": "Supprimer",
        "switch_mosque": "Changer",
        "active": "Actif",
        "adhan": "Adhan",
        "adhan_enabled": "Jouer l'adhan",
        "adhan_path": "Fichier audio de l'adhan",
        "adhan_browse": "Parcourir",
        "countdown_format": "Format du compte à rebours",
        "countdown_compact": "Compact",
        "countdown_full": "Complet",
        "language": "Langue",
        "now": "maintenant",
        "paste_url": "Ou collez l'URL directement",
        "paste_url_hint": "Allez sur mawaqit.net, trouvez votre mosquée et collez l'URL",
        "connected_mosque": "Mosquée connectée",
        "mosques": "Mosquées",
        "search_failed": "La recherche a échoué",
        "no_prayer_times": "Aucun horaire de prière chargé",
        "update_available": "Mise à jour disponible",
    },
    "tr": {
        "prayer_fajr": "Sabah",
        "prayer_dhuhr": "Öğle",
        "prayer_asr": "İkindi",
        "prayer_maghrib": "Akşam",
        "prayer_isha": "Yatsı",
        "prayer_shuruq": "Güneş",
        "prayer_jumuah": "Cuma",
        "prayer_jumuah2": "Cuma 2",
        "next_prayer": "Sonraki Namaz",
        "loading": "Yükleniyor…",
        "no_mosque": "Cami ayarlanmadı",
        "no_data": "Veri yüklenmedi",
        "refresh": "Yenile",
        "settings": "Ayarlar",
        "quit": "Çıkış",
        "notifications": "Namaz bildirimleri",
        "notification_title": "{name} — {time}",
        "notification_body": "{name} namazı vakti geldi",
        "cached_data": "Önbellekten veri",
        "fetch_error": "Vakitler alınamadı",
        "search": "Ara",
        "save": "Kaydet",
        "mosque_url": "Mawaqit URL",
        "find_mosque": "Caminizi Bulun",
        "search_hint": "Cami adı veya şehir ile arayın",
        "no_results": "Cami bulunamadı",
        "configure_mosque": "Cami ayarla",
        "launch_at_login": "Girişte başlat",
        "iqama": "Kamet",
        "show_prayer_times": "Namaz Vakitlerini Göster",
        "saved_mosques": "Kayıtlı Camiler",
        "add_mosque": "Ekle",
        "remove_mosque": "Kaldır",
        "switch_mosque": "Değiştir",
        "active": "Aktif",
        "adhan": "Ezan",
        "adhan_enabled": "Ezan sesini çal",
        "adhan_path": "Ezan ses dosyası",
        "adhan_browse": "Gözat",
        "countdown_format": "Geri sayım biçimi",
        "countdown_compact": "Kısa",
        "countdown_full": "Tam",
        "language": "Dil",
        "now": "şimdi",
        "paste_url": "Veya URL'yi yapıştırın",
        "paste_url_hint": "mawaqit.net'e gidin, caminizi bulun ve URL'yi yapıştırın",
        "connected_mosque": "Bağlı Cami",
        "mosques": "Camiler",
        "search_failed": "Arama başarısız",
        "no_prayer_times": "Namaz vakti yüklenmedi",
        "update_available": "Güncelleme mevcut",
    },
}

LANGUAGE_LABELS = {
    "en": "English",
    "ar": "العربية",
    "fr": "Français",
    "tr": "Türkçe",
}

# The current language code, set from settings at startup and when changed.
_current_language = "en"


def _set_language(lang):
    """Set the active language for translations."""
    global _current_language
    if lang in TRANSLATIONS:
        _current_language = lang


def t(key, **kwargs):
    """Return the translated string for *key* in the current language.

    Supports ``{placeholder}`` substitution via keyword arguments.
    Falls back to English, then to the raw key.
    """
    text = TRANSLATIONS.get(_current_language, {}).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


# Mapping from internal prayer name to translation key.
_PRAYER_KEY_MAP = {
    "Fajr": "prayer_fajr",
    "Dhuhr": "prayer_dhuhr",
    "Asr": "prayer_asr",
    "Maghrib": "prayer_maghrib",
    "Isha": "prayer_isha",
    "Shuruq": "prayer_shuruq",
    "Jumuah": "prayer_jumuah",
}


def _translate_prayer(name):
    """Translate an internal prayer name (e.g. 'Fajr') to the current language."""
    key = _PRAYER_KEY_MAP.get(name)
    if key:
        return t(key)
    return name


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

_SETTINGS_DEFAULTS = {
    "mosque_url": "",
    "notifications_enabled": True,
    "language": "en",
    "adhan_enabled": False,
    "adhan_path": "",
    "countdown_format": "compact",
    "saved_mosques": [],
}


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    # Migrate: ensure all default keys exist
    for key, default in _SETTINGS_DEFAULTS.items():
        if key not in data:
            data[key] = default
    return data


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_cache(data):
    cache = {
        "times": data["times"],
        "shuruq": data.get("shuruq"),
        "name": data.get("name", ""),
        "iqama": data.get("iqama"),
        "iqama_enabled": data.get("iqama_enabled", False),
        "jumua": data.get("jumua"),
        "jumua2": data.get("jumua2"),
        "date": date.today().isoformat(),
    }
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def extract_slug(url):
    match = re.search(r"mawaqit\.net/\w+/(?:w/)?(.+?)/?$", url)
    return match.group(1) if match else None


def fetch_times_api(slug):
    resp = requests.get(
        f"{API_BASE}/search?word={slug}",
        headers={"Accept": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError("No mosque found via API")

    mosque = results[0]
    api_times = mosque.get("times", [])
    if len(api_times) < 6:
        raise ValueError("Unexpected API times format")

    times = [api_times[0], api_times[2], api_times[3], api_times[4], api_times[5]]
    return {
        "times": times,
        "shuruq": api_times[1],
        "name": mosque.get("name") or mosque.get("label", ""),
        "iqama": mosque.get("iqama"),
        "iqama_enabled": mosque.get("iqamaEnabled", False),
        "jumua": mosque.get("jumua"),
        "jumua2": mosque.get("jumua2"),
    }


def fetch_times_html(url):
    slug = extract_slug(url)
    fetch_url = url
    if "/w/" not in fetch_url and slug:
        fetch_url = f"https://mawaqit.net/en/w/{slug}"

    resp = requests.get(fetch_url, timeout=15)
    resp.raise_for_status()

    match = re.search(r"confData\s*=\s*(\{.*?\});", resp.text, re.DOTALL)
    if not match:
        raise ValueError("Could not find confData in page")

    data = json.loads(match.group(1))
    return {
        "times": data["times"],
        "shuruq": data.get("shuruq"),
        "name": data.get("name") or data.get("label", ""),
    }


def fetch_times(url):
    slug = extract_slug(url)
    if slug:
        try:
            return fetch_times_api(slug)
        except Exception:
            pass
    return fetch_times_html(url)


def search_mosques(query):
    resp = requests.get(
        f"{API_BASE}/search?word={query}",
        headers={"Accept": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    return [
        {
            "name": m.get("name", ""),
            "slug": m.get("slug", ""),
            "localisation": m.get("localisation", ""),
        }
        for m in resp.json()
    ]


def resolve_iqama(prayer_time_str, iqama_value):
    if not iqama_value:
        return None
    val = str(iqama_value).strip()
    if val in ("0", "+0", ""):
        return None
    if val.startswith("+"):
        val = val[1:]
    if ":" in val:
        return val
    try:
        offset = int(val)
        if offset <= 0:
            return None
        dt = parse_time(prayer_time_str) + timedelta(minutes=offset)
        return dt.strftime("%H:%M")
    except ValueError:
        return None


def parse_time(time_str):
    h, m = map(int, time_str.split(":"))
    now = datetime.now()
    return now.replace(hour=h, minute=m, second=0, microsecond=0)


def get_next_prayer(times):
    now = datetime.now()
    for i, t_str in enumerate(times):
        dt = parse_time(t_str)
        if dt > now:
            return i, dt
    fajr = parse_time(times[0]) + timedelta(days=1)
    return 0, fajr


def format_countdown(dt, settings=None):
    remaining = int((dt - datetime.now()).total_seconds() / 60)
    if remaining <= 0:
        return t("now")
    h, m = divmod(remaining, 60)
    fmt = "compact"
    if settings:
        fmt = settings.get("countdown_format", "compact")
    if fmt == "full":
        if h > 0:
            return f"-{h}h {m:02d}m"
        return f"-{m}m"
    # compact (default)
    if h > 0:
        return f"-{h}h{m:02d}m"
    return f"-{m}m"


# ---------------------------------------------------------------------------
# Update checker
# ---------------------------------------------------------------------------


def check_for_update(current_version, tag_prefix):
    """Check GitHub releases for a newer version matching *tag_prefix*.

    Returns ``(latest_version, html_url)`` when a newer release exists,
    otherwise ``None``.  Network or parse errors are **not** propagated.
    """
    resp = requests.get(RELEASES_URL, timeout=10)
    resp.raise_for_status()
    releases = resp.json()
    for release in releases:
        tag = release.get("tag_name", "")
        if tag.startswith(tag_prefix):
            latest = tag[len(tag_prefix):]
            current_tuple = tuple(int(x) for x in current_version.split("."))
            latest_tuple = tuple(int(x) for x in latest.split("."))
            if latest_tuple > current_tuple:
                html_url = release.get("html_url", REPO_RELEASES_PAGE)
                return (latest, html_url)
            return None
    return None


# ---------------------------------------------------------------------------
# Tray icon rendering
# ---------------------------------------------------------------------------

def _find_font(size):
    """Try to locate a TrueType font available on Linux."""
    font_names = [
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Regular.ttf",
        "NotoSans-Regular.ttf",
        "FreeSans.ttf",
        "Ubuntu-R.ttf",
    ]
    font_dirs = [
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/truetype/freefont",
        "/usr/share/fonts/truetype/ubuntu",
        "/usr/share/fonts/TTF",
        "/usr/share/fonts",
    ]
    for d in font_dirs:
        for name in font_names:
            path = os.path.join(d, name)
            if os.path.isfile(path):
                try:
                    return ImageFont.truetype(path, size)
                except OSError:
                    continue
    return ImageFont.load_default()


def create_icon_image(prayer_name):
    color = PRAYER_COLORS_RGB.get(prayer_name, (200, 200, 200))
    size = 128
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse([8, 8, size - 8, size - 8], fill=color)

    letter = prayer_name[0]
    font = _find_font(56)

    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]
    draw.text((tx, ty), letter, fill=(255, 255, 255), font=font)

    return img.resize((64, 64), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Linux notification & audio
# ---------------------------------------------------------------------------

def send_notification(prayer_name, time_str):
    """Send a desktop notification using notify-send."""
    translated_name = _translate_prayer(prayer_name)
    title = t("notification_title", name=translated_name, time=time_str)
    body = t("notification_body", name=translated_name)
    try:
        subprocess.run(
            ["notify-send", "--app-name", APP_NAME, title, body],
            timeout=10,
        )
    except FileNotFoundError:
        # notify-send not installed; silently ignore
        pass
    except Exception:
        pass


# Track the currently playing adhan process so we can avoid overlapping playback.
_adhan_process = None


def _play_adhan(path):
    """Play an adhan audio file using available Linux audio players."""
    global _adhan_process
    if not path or not os.path.isfile(path):
        return
    # Kill any previous adhan playback
    if _adhan_process and _adhan_process.poll() is None:
        try:
            _adhan_process.terminate()
        except Exception:
            pass
    # Try paplay (PulseAudio), then mpv, then aplay (ALSA)
    players = [
        ["paplay", path],
        ["mpv", "--no-video", path],
        ["aplay", path],
    ]
    for cmd in players:
        if shutil.which(cmd[0]):
            try:
                _adhan_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                continue


# ---------------------------------------------------------------------------
# Prayer Times Popup Window
# ---------------------------------------------------------------------------

class PrayerTimesWindow:
    def __init__(self, app):
        import tkinter as tk

        self.app = app
        self.win = tk.Toplevel() if hasattr(app, '_tk_root') and app._tk_root else tk.Tk()
        self.win.title(t("next_prayer"))
        self.win.configure(bg=BG_COLOR)
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self._center_window(340, 480)
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()

    def _center_window(self, w, h):
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = sw - w - 20
        y = sh - h - 80
        self.win.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        import tkinter as tk

        pad = 16

        # Mosque name header
        if self.app.mosque_name:
            header = tk.Label(
                self.win,
                text=self.app.mosque_name,
                font=(FONT_FAMILY, 13, "bold"),
                fg=TEXT_PRIMARY,
                bg=BG_COLOR,
                anchor="w",
            )
            header.pack(fill="x", padx=pad, pady=(pad, 4))

        # Update available banner
        if self.app.update_info:
            update_ver, update_url = self.app.update_info
            update_frame = tk.Frame(self.win, bg="#1a3050", padx=10, pady=6)
            update_frame.pack(fill="x", padx=pad, pady=(4, 4))
            update_label = tk.Label(
                update_frame,
                text=f"⬆ {t('update_available')} — v{update_ver}",
                font=(FONT_FAMILY, 10, "bold"),
                fg=ACCENT,
                bg="#1a3050",
                cursor="hand2",
            )
            update_label.pack(fill="x")
            update_label.bind(
                "<Button-1>",
                lambda e, u=update_url: subprocess.Popen(["xdg-open", u]),
            )

        # Divider
        tk.Frame(self.win, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(4, 8))

        display_times = self.app._display_times()
        display_names = self.app._display_names()
        iqama_times = self.app._resolved_iqama()

        if display_times:
            idx, _ = get_next_prayer(display_times)

            for i, name in enumerate(display_names):
                t_str = display_times[i] if i < len(display_times) else "--:--"
                is_next = i == idx and parse_time(t_str) > datetime.now()
                is_past = parse_time(t_str) <= datetime.now()
                iq = iqama_times[i] if i < len(iqama_times) else None

                self._build_prayer_row(name, t_str, iq, is_next, is_past, i)

            if self.app._is_friday() and self.app.jumua2:
                tk.Frame(self.win, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=2)
                self._build_simple_row(t("prayer_jumuah2"), self.app.jumua2)

        else:
            tk.Label(
                self.win,
                text=t("no_prayer_times"),
                font=(FONT_FAMILY, 11),
                fg=TEXT_SECONDARY,
                bg=BG_COLOR,
            ).pack(pady=20)

        # Shuruq
        if self.app.shuruq:
            tk.Frame(self.win, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(8, 4))
            self._build_simple_row(t("prayer_shuruq"), self.app.shuruq)

        # Status / error
        if self.app.last_error:
            tk.Frame(self.win, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(8, 4))
            msg = self.app.last_error
            if self.app.is_cached:
                msg = f"{t('cached_data')}. {msg}"
            tk.Label(
                self.win,
                text=msg,
                font=(FONT_FAMILY, 9),
                fg="#cc7744",
                bg=BG_COLOR,
                anchor="w",
                wraplength=300,
            ).pack(fill="x", padx=pad, pady=2)

        # Bottom buttons
        spacer = tk.Frame(self.win, bg=BG_COLOR)
        spacer.pack(fill="both", expand=True)

        tk.Frame(self.win, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(4, 8))

        btn_frame = tk.Frame(self.win, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=pad, pady=(0, pad))

        self._make_button(btn_frame, t("refresh"), self._on_refresh).pack(side="left")
        self._make_button(btn_frame, t("settings"), self._on_settings).pack(side="left", padx=(8, 0))
        self._make_button(btn_frame, t("quit"), self._on_quit).pack(side="right")

    def _build_prayer_row(self, name, time_str, iqama, is_next, is_past, index):
        import tkinter as tk

        # Translate the prayer name for display
        display_name = _translate_prayer(name)

        bg = HIGHLIGHT_BG if is_next else BG_COLOR
        fg = ACCENT if is_next else TEXT_DIM if is_past else TEXT_PRIMARY
        color = PRAYER_COLORS.get(name, "#888888")

        row = tk.Frame(self.win, bg=bg, padx=16, pady=8)
        row.pack(fill="x")

        dot = tk.Canvas(row, width=12, height=12, bg=bg, highlightthickness=0)
        dot.create_oval(1, 1, 11, 11, fill=color, outline="")
        dot.pack(side="left", padx=(0, 10))

        name_frame = tk.Frame(row, bg=bg)
        name_frame.pack(side="left", fill="x", expand=True)

        weight = "bold" if is_next else "normal"
        tk.Label(
            name_frame,
            text=display_name,
            font=(FONT_FAMILY, 11, weight),
            fg=fg,
            bg=bg,
            anchor="w",
        ).pack(anchor="w")

        if iqama:
            tk.Label(
                name_frame,
                text=f"{t('iqama')} {iqama}",
                font=(FONT_FAMILY, 9),
                fg=TEXT_SECONDARY if is_next else TEXT_DIM,
                bg=bg,
                anchor="w",
            ).pack(anchor="w")

        right_frame = tk.Frame(row, bg=bg)
        right_frame.pack(side="right")

        if is_next:
            countdown = format_countdown(parse_time(time_str), self.app.settings)
            tk.Label(
                right_frame,
                text=countdown,
                font=(FONT_FAMILY, 9),
                fg=TEXT_SECONDARY,
                bg=bg,
            ).pack(anchor="e")

        tk.Label(
            right_frame,
            text=time_str,
            font=(FONT_FAMILY, 12, weight),
            fg=fg,
            bg=bg,
        ).pack(anchor="e")

    def _build_simple_row(self, name, time_str):
        import tkinter as tk

        row = tk.Frame(self.win, bg=BG_COLOR, padx=16, pady=4)
        row.pack(fill="x")

        tk.Label(
            row, text=name, font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY, bg=BG_COLOR, anchor="w",
        ).pack(side="left")
        tk.Label(
            row, text=time_str, font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY, bg=BG_COLOR,
        ).pack(side="right")

    def _make_button(self, parent, text, command):
        import tkinter as tk

        btn = tk.Label(
            parent,
            text=text,
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=CARD_COLOR,
            padx=12,
            pady=5,
            cursor="hand2",
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=CARD_HOVER, fg=TEXT_PRIMARY))
        btn.bind("<Leave>", lambda e: btn.configure(bg=CARD_COLOR, fg=TEXT_SECONDARY))
        return btn

    def _on_refresh(self):
        self.win.destroy()
        self.app.refresh()

    def _on_settings(self):
        self.win.destroy()
        self.app.show_settings()

    def _on_quit(self):
        self.win.destroy()
        self.app.quit()

    def _close(self):
        self.win.destroy()

    def show(self):
        self.win.mainloop()


# ---------------------------------------------------------------------------
# Settings Window
# ---------------------------------------------------------------------------

class SettingsWindow:
    def __init__(self, app):
        import tkinter as tk
        from tkinter import ttk

        self.app = app
        self.win = tk.Tk()
        self.win.title(f"{t('next_prayer')} — {t('settings')}")
        self.win.configure(bg=BG_COLOR)
        self.win.resizable(False, False)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w, h = 520, 820
        self.win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        style = ttk.Style(self.win)
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=BG_COLOR)
        style.configure("Dark.TLabel", background=BG_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 10))
        style.configure("Header.TLabel", background=BG_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 13, "bold"))
        style.configure("Dim.TLabel", background=BG_COLOR, foreground=TEXT_SECONDARY, font=(FONT_FAMILY, 9))
        style.configure("Dark.TEntry", fieldbackground=CARD_COLOR, foreground=TEXT_PRIMARY, insertcolor=TEXT_PRIMARY)
        style.configure("Dark.TButton", background=CARD_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 10), padding=(12, 6))
        style.map("Dark.TButton", background=[("active", CARD_HOVER)])
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", font=(FONT_FAMILY, 10, "bold"), padding=(12, 6))
        style.map("Accent.TButton", background=[("active", "#5aa0e9")])
        style.configure("Dark.TCheckbutton", background=BG_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 10))
        style.configure("Treeview", background=CARD_COLOR, foreground=TEXT_PRIMARY, fieldbackground=CARD_COLOR, font=(FONT_FAMILY, 10), rowheight=30)
        style.configure("Treeview.Heading", background=BG_COLOR, foreground=TEXT_SECONDARY, font=(FONT_FAMILY, 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])
        style.configure("Dark.TCombobox", fieldbackground=CARD_COLOR, foreground=TEXT_PRIMARY, background=CARD_COLOR, font=(FONT_FAMILY, 10))
        style.map("Dark.TCombobox", fieldbackground=[("readonly", CARD_COLOR)])

        pad = 20

        # Scrollable canvas
        canvas = tk.Canvas(self.win, bg=BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        main = ttk.Frame(canvas, style="Dark.TFrame")
        canvas_window = canvas.create_window((0, 0), window=main, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        main.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse wheel scrolling (Linux uses Button-4 / Button-5)
        def _on_mousewheel_up(event):
            canvas.yview_scroll(-3, "units")

        def _on_mousewheel_down(event):
            canvas.yview_scroll(3, "units")

        canvas.bind_all("<Button-4>", _on_mousewheel_up)
        canvas.bind_all("<Button-5>", _on_mousewheel_down)
        self._canvas = canvas

        inner_pad = pad

        # --- Language selector ---
        ttk.Label(main, text=t("language"), style="Header.TLabel").pack(anchor="w", padx=inner_pad, pady=(inner_pad, 4))

        lang_frame = ttk.Frame(main, style="Dark.TFrame")
        lang_frame.pack(fill="x", padx=inner_pad, pady=(0, 12))

        self.lang_var = tk.StringVar(value=app.settings.get("language", "en"))
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=list(LANGUAGE_LABELS.keys()),
            state="readonly",
            style="Dark.TCombobox",
            width=10,
        )
        lang_combo.pack(side="left")

        # Show the human-readable label next to the dropdown
        self._lang_label_var = tk.StringVar(value=LANGUAGE_LABELS.get(self.lang_var.get(), ""))
        lang_label = ttk.Label(lang_frame, textvariable=self._lang_label_var, style="Dim.TLabel")
        lang_label.pack(side="left", padx=(8, 0))

        def _on_lang_change(event):
            self._lang_label_var.set(LANGUAGE_LABELS.get(self.lang_var.get(), ""))

        lang_combo.bind("<<ComboboxSelected>>", _on_lang_change)

        # Divider
        tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=(0, 12))

        # --- Search section ---
        ttk.Label(main, text=t("find_mosque"), style="Header.TLabel").pack(anchor="w", padx=inner_pad)
        ttk.Label(main, text=t("search_hint"), style="Dim.TLabel").pack(anchor="w", padx=inner_pad, pady=(0, 8))

        search_frame = ttk.Frame(main, style="Dark.TFrame")
        search_frame.pack(fill="x", padx=inner_pad, pady=(0, 8))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=(FONT_FAMILY, 11), bg=CARD_COLOR, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY, relief="flat", bd=0,
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=TEXT_DIM,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        ttk.Button(search_frame, text=t("search"), style="Accent.TButton", command=self._do_search).pack(side="right", padx=(8, 0))

        self.results_tree = ttk.Treeview(main, columns=("location",), show="tree", height=4, selectmode="browse")
        self.results_tree.column("#0", width=200)
        self.results_tree.column("location", width=260)
        self.results_tree.pack(fill="x", padx=inner_pad, pady=(0, 12))
        self.results_tree.bind("<Double-1>", self._on_result_select)
        self.search_results = []

        # Divider
        tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=(0, 12))

        # --- URL section ---
        ttk.Label(main, text=t("paste_url"), style="Header.TLabel").pack(anchor="w", padx=inner_pad)
        ttk.Label(main, text=t("paste_url_hint"), style="Dim.TLabel").pack(anchor="w", padx=inner_pad, pady=(0, 8))

        url_frame = ttk.Frame(main, style="Dark.TFrame")
        url_frame.pack(fill="x", padx=inner_pad, pady=(0, 12))

        self.url_var = tk.StringVar(value=app.settings.get("mosque_url", ""))
        self.url_entry = tk.Entry(
            url_frame, textvariable=self.url_var,
            font=(FONT_FAMILY, 11), bg=CARD_COLOR, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY, relief="flat", bd=0,
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=TEXT_DIM,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=6)

        ttk.Button(url_frame, text=t("save"), style="Accent.TButton", command=self._save_url).pack(side="right", padx=(8, 0))

        # --- Connected mosque ---
        if app.mosque_name:
            tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=(0, 12))
            ttk.Label(main, text=f"{t('connected_mosque')}: {app.mosque_name}", style="Dim.TLabel").pack(anchor="w", padx=inner_pad)

        # --- Notifications toggle ---
        tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=12)
        self.notif_var = tk.BooleanVar(value=app.settings.get("notifications_enabled", True))
        notif_cb = tk.Checkbutton(
            main,
            text=f"  {t('notifications')}",
            variable=self.notif_var,
            command=self._toggle_notifications,
            font=(FONT_FAMILY, 11),
            fg=TEXT_PRIMARY,
            bg=BG_COLOR,
            selectcolor=CARD_COLOR,
            activebackground=BG_COLOR,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            highlightthickness=0,
        )
        notif_cb.pack(anchor="w", padx=inner_pad)

        # --- Adhan section ---
        tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=12)
        ttk.Label(main, text=t("adhan"), style="Header.TLabel").pack(anchor="w", padx=inner_pad, pady=(0, 4))

        self.adhan_var = tk.BooleanVar(value=app.settings.get("adhan_enabled", False))
        adhan_cb = tk.Checkbutton(
            main,
            text=f"  {t('adhan_enabled')}",
            variable=self.adhan_var,
            command=self._toggle_adhan,
            font=(FONT_FAMILY, 11),
            fg=TEXT_PRIMARY,
            bg=BG_COLOR,
            selectcolor=CARD_COLOR,
            activebackground=BG_COLOR,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            highlightthickness=0,
        )
        adhan_cb.pack(anchor="w", padx=inner_pad, pady=(0, 4))

        adhan_path_frame = ttk.Frame(main, style="Dark.TFrame")
        adhan_path_frame.pack(fill="x", padx=inner_pad, pady=(0, 4))

        ttk.Label(adhan_path_frame, text=t("adhan_path"), style="Dim.TLabel").pack(side="left")

        self.adhan_path_var = tk.StringVar(value=app.settings.get("adhan_path", ""))
        adhan_path_entry = tk.Entry(
            adhan_path_frame, textvariable=self.adhan_path_var,
            font=(FONT_FAMILY, 9), bg=CARD_COLOR, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY, relief="flat", bd=0,
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=TEXT_DIM,
            state="readonly",
        )
        adhan_path_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)

        ttk.Button(adhan_path_frame, text=t("adhan_browse"), style="Dark.TButton", command=self._browse_adhan).pack(side="right", padx=(8, 0))

        # --- Countdown format ---
        tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=12)
        ttk.Label(main, text=t("countdown_format"), style="Header.TLabel").pack(anchor="w", padx=inner_pad, pady=(0, 4))

        cd_frame = ttk.Frame(main, style="Dark.TFrame")
        cd_frame.pack(fill="x", padx=inner_pad, pady=(0, 12))

        self.countdown_var = tk.StringVar(value=app.settings.get("countdown_format", "compact"))
        cd_combo = ttk.Combobox(
            cd_frame,
            textvariable=self.countdown_var,
            values=["compact", "full"],
            state="readonly",
            style="Dark.TCombobox",
            width=12,
        )
        cd_combo.pack(side="left")

        self._cd_label_var = tk.StringVar(value=self._countdown_label(self.countdown_var.get()))
        cd_label = ttk.Label(cd_frame, textvariable=self._cd_label_var, style="Dim.TLabel")
        cd_label.pack(side="left", padx=(8, 0))

        def _on_cd_change(event):
            self._cd_label_var.set(self._countdown_label(self.countdown_var.get()))

        cd_combo.bind("<<ComboboxSelected>>", _on_cd_change)

        # --- Saved Mosques section ---
        tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=12)
        ttk.Label(main, text=t("saved_mosques"), style="Header.TLabel").pack(anchor="w", padx=inner_pad, pady=(0, 4))

        self.mosque_tree = ttk.Treeview(
            main, columns=("url",), show="headings", height=4, selectmode="browse",
        )
        self.mosque_tree.heading("url", text="URL")
        self.mosque_tree.column("url", width=460)
        self.mosque_tree.pack(fill="x", padx=inner_pad, pady=(0, 4))
        self.mosque_tree.bind("<Double-1>", self._on_mosque_double_click)

        mosque_btn_frame = ttk.Frame(main, style="Dark.TFrame")
        mosque_btn_frame.pack(fill="x", padx=inner_pad, pady=(0, 12))

        ttk.Button(mosque_btn_frame, text=t("add_mosque"), style="Dark.TButton", command=self._add_current_mosque).pack(side="left")
        ttk.Button(mosque_btn_frame, text=t("switch_mosque"), style="Accent.TButton", command=self._switch_mosque).pack(side="left", padx=(8, 0))
        ttk.Button(mosque_btn_frame, text=t("remove_mosque"), style="Dark.TButton", command=self._remove_mosque).pack(side="left", padx=(8, 0))

        self._populate_mosque_tree()

        # --- Save All button at the bottom ---
        tk.Frame(main, bg=TEXT_DIM, height=1).pack(fill="x", padx=inner_pad, pady=(12, 8))
        ttk.Button(main, text=t("save"), style="Accent.TButton", command=self._save_all).pack(anchor="e", padx=inner_pad, pady=(0, inner_pad))

        self.search_entry.focus_set()

    def _countdown_label(self, value):
        if value == "compact":
            return f"{t('countdown_compact')} (-2h15m)"
        return f"{t('countdown_full')} (-2h 15m)"

    # --- Search ---

    def _do_search(self):
        query = self.search_var.get().strip()
        if not query:
            return

        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.search_results = []

        try:
            results = search_mosques(query)
            self.search_results = results
            if not results:
                self.results_tree.insert("", "end", text=t("no_results"), values=("",))
                return
            for m in results:
                loc = m["localisation"]
                if len(loc) > 50:
                    loc = loc[:47] + "..."
                self.results_tree.insert("", "end", text=m["name"], values=(loc,))
        except Exception as e:
            self.results_tree.insert("", "end", text=f"{t('search_failed')}: {e}", values=("",))

    def _on_result_select(self, event):
        sel = self.results_tree.selection()
        if not sel:
            return
        idx = self.results_tree.index(sel[0])
        if idx < len(self.search_results):
            mosque = self.search_results[idx]
            url = f"https://mawaqit.net/en/w/{mosque['slug']}"
            self.url_var.set(url)
            self._save_url()

    def _save_url(self):
        url = self.url_var.get().strip()
        if url:
            self.app.settings["mosque_url"] = url
            save_settings(self.app.settings)
            self.win.destroy()
            self._unbind_mousewheel()
            self.app.refresh()

    # --- Notifications ---

    def _toggle_notifications(self):
        enabled = self.notif_var.get()
        self.app.settings["notifications_enabled"] = enabled
        save_settings(self.app.settings)
        if enabled:
            self.app._schedule_notifications()
        else:
            self.app._cancel_notification_timers()

    # --- Adhan ---

    def _toggle_adhan(self):
        self.app.settings["adhan_enabled"] = self.adhan_var.get()
        save_settings(self.app.settings)

    def _browse_adhan(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title=t("adhan_path"),
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.ogg *.opus *.flac *.m4a"),
                ("All files", "*.*"),
            ],
            parent=self.win,
        )
        if path:
            self.adhan_path_var.set(path)
            self.app.settings["adhan_path"] = path
            save_settings(self.app.settings)

    # --- Saved Mosques ---

    def _populate_mosque_tree(self):
        for item in self.mosque_tree.get_children():
            self.mosque_tree.delete(item)
        saved = self.app.settings.get("saved_mosques", [])
        active_url = self.app.settings.get("mosque_url", "")
        for m in saved:
            name = m.get("name", "")
            url = m.get("url", "")
            marker = f"[{t('active')}] " if url == active_url else ""
            display = f"{marker}{name}" if name else url
            self.mosque_tree.insert("", "end", values=(display,))

    def _add_current_mosque(self):
        url = self.app.settings.get("mosque_url", "")
        name = self.app.mosque_name or ""
        if not url:
            return
        saved = self.app.settings.get("saved_mosques", [])
        # Avoid duplicates
        for m in saved:
            if m.get("url") == url:
                return
        saved.append({"url": url, "name": name})
        self.app.settings["saved_mosques"] = saved
        save_settings(self.app.settings)
        self._populate_mosque_tree()

    def _switch_mosque(self):
        sel = self.mosque_tree.selection()
        if not sel:
            return
        idx = self.mosque_tree.index(sel[0])
        saved = self.app.settings.get("saved_mosques", [])
        if idx < len(saved):
            mosque = saved[idx]
            self.app.settings["mosque_url"] = mosque["url"]
            save_settings(self.app.settings)
            self.win.destroy()
            self._unbind_mousewheel()
            self.app.refresh()

    def _on_mosque_double_click(self, event):
        self._switch_mosque()

    def _remove_mosque(self):
        sel = self.mosque_tree.selection()
        if not sel:
            return
        idx = self.mosque_tree.index(sel[0])
        saved = self.app.settings.get("saved_mosques", [])
        if idx < len(saved):
            saved.pop(idx)
            self.app.settings["saved_mosques"] = saved
            save_settings(self.app.settings)
            self._populate_mosque_tree()

    # --- Save All settings ---

    def _save_all(self):
        """Save language, countdown format, adhan settings all at once."""
        lang = self.lang_var.get()
        self.app.settings["language"] = lang
        _set_language(lang)

        self.app.settings["countdown_format"] = self.countdown_var.get()
        self.app.settings["adhan_enabled"] = self.adhan_var.get()
        self.app.settings["adhan_path"] = self.adhan_path_var.get()
        self.app.settings["notifications_enabled"] = self.notif_var.get()

        save_settings(self.app.settings)

        # Rebuild the tray menu / title with the new language
        self.app.update_icon()

        self.win.destroy()
        self._unbind_mousewheel()

    def _unbind_mousewheel(self):
        try:
            self._canvas.unbind_all("<Button-4>")
            self._canvas.unbind_all("<Button-5>")
        except Exception:
            pass

    def _close(self):
        self._unbind_mousewheel()
        self.win.destroy()

    def show(self):
        self.win.mainloop()


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class NextPrayerApp:
    def __init__(self):
        self.settings = load_settings()
        # Apply language from settings
        _set_language(self.settings.get("language", "en"))

        self.times = None
        self.shuruq = None
        self.mosque_name = ""
        self.iqama = None
        self.iqama_enabled = False
        self.jumua = None
        self.jumua2 = None
        self.icon = None
        self.running = True
        self.last_error = None
        self.is_cached = False
        self.notification_timers = []
        self.update_info = None

    def _is_friday(self):
        return datetime.now().weekday() == 4

    def _display_names(self):
        names = list(PRAYER_NAMES)
        if self._is_friday() and self.jumua:
            names[1] = "Jumuah"
        return names

    def _display_times(self):
        if not self.times:
            return None
        times = list(self.times)
        if self._is_friday() and self.jumua:
            times[1] = self.jumua
        return times

    def _resolved_iqama(self):
        if not self.iqama_enabled or not self.iqama or not self.times:
            return [None] * 5
        result = []
        for i in range(5):
            prayer_time = self.times[i]
            iq_val = self.iqama[i] if i < len(self.iqama) else None
            result.append(resolve_iqama(prayer_time, iq_val))
        return result

    def _cancel_notification_timers(self):
        for timer in self.notification_timers:
            timer.cancel()
        self.notification_timers.clear()

    def _schedule_notifications(self):
        self._cancel_notification_timers()
        if not self.times:
            return
        if not self.settings.get("notifications_enabled", True):
            return
        now = datetime.now()
        display_times = self._display_times()
        display_names = self._display_names()
        for i, t_str in enumerate(display_times):
            dt = parse_time(t_str)
            delay = (dt - now).total_seconds()
            if delay > 0:
                timer = threading.Timer(
                    delay, self._fire_notification, args=(display_names[i], t_str)
                )
                timer.daemon = True
                timer.start()
                self.notification_timers.append(timer)

    def _fire_notification(self, name, time_str):
        adhan_enabled = self.settings.get("adhan_enabled", False)
        adhan_path = self.settings.get("adhan_path", "")
        if adhan_enabled and adhan_path and os.path.isfile(adhan_path):
            _play_adhan(adhan_path)
        else:
            send_notification(name, time_str)
        self.update_icon()

    def _check_update(self):
        """Check for a newer release on GitHub (silent on failure)."""
        try:
            result = check_for_update(APP_VERSION, TAG_PREFIX)
            if result:
                self.update_info = result
                self.update_icon()
        except Exception:
            pass

    def _apply_data(self, data, from_cache=False):
        self.times = data["times"]
        self.shuruq = data.get("shuruq")
        self.mosque_name = data.get("name", "")
        self.iqama = data.get("iqama")
        self.iqama_enabled = data.get("iqama_enabled", False)
        self.jumua = data.get("jumua")
        self.jumua2 = data.get("jumua2")
        self.is_cached = from_cache
        if not from_cache:
            self.last_error = None
            save_cache(data)
        self._schedule_notifications()

    def _load_cache(self):
        cached = load_cache()
        if not cached or "times" not in cached:
            return False
        self._apply_data(cached, from_cache=True)
        return True

    def build_menu(self):
        display_times = self._display_times()
        display_names = self._display_names()

        items = []
        items.append(pystray.MenuItem(
            t("show_prayer_times"),
            lambda: self.show_prayer_times(),
            default=True,
        ))

        if self.update_info:
            ver, url = self.update_info
            items.append(pystray.MenuItem(
                f"⬆ {t('update_available')} (v{ver})",
                (lambda u: lambda: subprocess.Popen(["xdg-open", u]))(url),
            ))

        items.append(pystray.Menu.SEPARATOR)

        if display_times:
            idx, _ = get_next_prayer(display_times)
            for i, name in enumerate(display_names):
                t_str = display_times[i] if i < len(display_times) else "--:--"
                marker = "▶ " if i == idx and parse_time(t_str) > datetime.now() else "  "
                translated = _translate_prayer(name)
                items.append(
                    pystray.MenuItem(f"{marker}{translated}  {t_str}", None, enabled=False)
                )
        else:
            items.append(pystray.MenuItem(t("no_data"), None, enabled=False))

        items.append(pystray.Menu.SEPARATOR)

        # Mosques submenu
        saved = self.settings.get("saved_mosques", [])
        if saved:
            mosque_items = []
            for m in saved:
                m_name = m.get("name") or m.get("url", "")
                m_url = m.get("url", "")
                active_url = self.settings.get("mosque_url", "")
                prefix = "✓ " if m_url == active_url else "  "
                # Capture m_url in default arg to avoid closure issue
                mosque_items.append(
                    pystray.MenuItem(
                        f"{prefix}{m_name}",
                        (lambda url: lambda: self._switch_mosque_from_tray(url))(m_url),
                    )
                )
            items.append(pystray.MenuItem(
                t("mosques"),
                pystray.Menu(*mosque_items),
            ))

        items.append(pystray.MenuItem(
            t("notifications"),
            lambda: self.toggle_notifications(),
            checked=lambda _: self.settings.get("notifications_enabled", True),
        ))
        items.append(pystray.MenuItem(t("settings"), lambda: self.show_settings()))
        items.append(pystray.MenuItem(t("refresh"), lambda: self.refresh()))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem(t("quit"), lambda: self.quit()))

        return pystray.Menu(*items)

    def _switch_mosque_from_tray(self, url):
        """Switch to a saved mosque from the tray submenu."""
        self.settings["mosque_url"] = url
        save_settings(self.settings)
        self.refresh()

    def get_title(self):
        display_times = self._display_times()
        if not display_times:
            return t("next_prayer")
        idx, next_dt = get_next_prayer(display_times)
        name = _translate_prayer(self._display_names()[idx])
        t_str = display_times[idx]
        countdown = format_countdown(next_dt, self.settings)
        suffix = f" ({t('cached_data')})" if self.is_cached else ""
        return f"{name}  {t_str}  {countdown}{suffix}"

    def refresh(self):
        url = self.settings.get("mosque_url", "")
        if not url:
            return

        try:
            data = fetch_times(url)
            self._apply_data(data)
            self.update_icon()
        except Exception as e:
            self.last_error = f"{t('fetch_error')}: {e}"
            if not self.times:
                self._load_cache()
            self.update_icon()

    def update_icon(self):
        if not self.icon:
            return
        display_times = self._display_times()
        if not display_times:
            return

        idx, _ = get_next_prayer(display_times)
        name = self._display_names()[idx]
        self.icon.icon = create_icon_image(name)
        self.icon.title = self.get_title()
        self.icon.menu = self.build_menu()

    def toggle_notifications(self):
        current = self.settings.get("notifications_enabled", True)
        self.settings["notifications_enabled"] = not current
        save_settings(self.settings)
        if not current:
            self._schedule_notifications()
        else:
            self._cancel_notification_timers()
        self.update_icon()

    def show_prayer_times(self):
        threading.Thread(target=self._open_prayer_window, daemon=True).start()

    def _open_prayer_window(self):
        try:
            PrayerTimesWindow(self).show()
        except Exception:
            pass

    def show_settings(self):
        threading.Thread(target=self._open_settings_window, daemon=True).start()

    def _open_settings_window(self):
        try:
            SettingsWindow(self).show()
        except Exception:
            pass

    def quit(self):
        self.running = False
        self._cancel_notification_timers()
        if self.icon:
            self.icon.stop()

    def background_loop(self):
        self.refresh()
        self._check_update()
        last_date = datetime.now().date()
        update_counter = 0  # minutes since last update check

        while self.running:
            time.sleep(60)
            if not self.running:
                break

            today = datetime.now().date()
            if today != last_date:
                last_date = today
                self.refresh()

            update_counter += 1
            if update_counter >= 1440:  # 24 hours
                update_counter = 0
                self._check_update()

            self.update_icon()

    def run(self):
        img = create_icon_image("Fajr")
        self.icon = pystray.Icon(
            APP_NAME,
            img,
            title=f"{t('next_prayer')} - {t('loading')}",
            menu=self.build_menu(),
        )

        bg = threading.Thread(target=self.background_loop, daemon=True)
        bg.start()

        self.icon.run()


if __name__ == "__main__":
    app = NextPrayerApp()
    app.run()
