import json
import math
import re
from datetime import date, datetime, timedelta

import requests

APP_NAME = "Al Munadi"
APP_VERSION = "1.0.7"
TAG_PREFIX = "v"
RELEASES_URL = "https://api.github.com/repos/Chanclatoen/almunadi/releases"
REPO_RELEASES_PAGE = "https://github.com/Chanclatoen/almunadi/releases"
PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
API_BASE = "https://mawaqit.net/api/2.0/mosque"

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
        "loading": "Loading...",
        "no_mosque": "No mosque set",
        "no_data": "No data loaded",
        "refresh": "Refresh",
        "settings": "Settings",
        "quit": "Quit",
        "notifications": "Prayer notifications",
        "notification_title": "{name} - {time}",
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
        "display_mode": "Display mode",
        "display_mode_countdown": "Countdown",
        "display_mode_time": "Time",
        "display_mode_name": "Name only",
        "display_mode_compact": "Compact",
        "display_mode_icon": "Icon only",
        "display_mode_since": "Since last prayer",
        "per_prayer_notifications": "Per-prayer notifications",
        "prayer_reminder": "Reminder (min before)",
        "prayer_offset": "Time offset (minutes)",
        "manual_offsets": "Manual time adjustments",
        "adhan_per_prayer": "Adhan",
        "language": "Language",
        "now": "now",
        "paste_url": "Or Paste URL Directly",
        "paste_url_hint": "Go to mawaqit.net, find your mosque, and paste the URL",
        "connected_mosque": "Connected Mosque",
        "mosques": "Mosques",
        "search_failed": "Search failed",
        "no_prayer_times": "No prayer times loaded",
        "update_available": "Update available",
        "hijri_date": "Hijri date",
        "qibla": "Qibla",
        "since_last_prayer": "Since {name}",
        "dnd_bypass": "Break through Do Not Disturb",
        "dnd_bypass_per_prayer": "DND bypass",
    },
    "nl": {
        "prayer_fajr": "Fajr",
        "prayer_dhuhr": "Dhuhr",
        "prayer_asr": "Asr",
        "prayer_maghrib": "Maghrib",
        "prayer_isha": "Isha",
        "prayer_shuruq": "Shuruq",
        "prayer_jumuah": "Jumuah",
        "prayer_jumuah2": "Jumuah 2",
        "next_prayer": "Volgend gebed",
        "loading": "Laden...",
        "no_mosque": "Geen moskee ingesteld",
        "no_data": "Geen gegevens geladen",
        "refresh": "Vernieuwen",
        "settings": "Instellingen",
        "quit": "Afsluiten",
        "notifications": "Gebedsmeldingen",
        "notification_title": "{name} - {time}",
        "notification_body": "Het is tijd voor het {name}-gebed",
        "cached_data": "Gegevens uit cache",
        "fetch_error": "Kon tijden niet ophalen",
        "search": "Zoeken",
        "save": "Opslaan",
        "mosque_url": "Mawaqit URL",
        "find_mosque": "Vind je moskee",
        "search_hint": "Zoek op moskeenaam of stad",
        "no_results": "Geen moskeeen gevonden",
        "configure_mosque": "Moskee instellen",
        "launch_at_login": "Starten bij inloggen",
        "iqama": "Iqama",
        "show_prayer_times": "Gebedstijden tonen",
        "saved_mosques": "Opgeslagen moskeeen",
        "add_mosque": "Huidige toevoegen",
        "remove_mosque": "Verwijderen",
        "switch_mosque": "Wisselen",
        "active": "Actief",
        "adhan": "Adhan",
        "adhan_enabled": "Adhan-audio afspelen",
        "adhan_path": "Adhan-audiobestand",
        "adhan_browse": "Bladeren",
        "countdown_format": "Aftelformaat",
        "countdown_compact": "Compact",
        "countdown_full": "Volledig",
        "display_mode": "Weergavemodus",
        "display_mode_countdown": "Aftellen",
        "display_mode_time": "Tijd",
        "display_mode_name": "Alleen naam",
        "display_mode_compact": "Compact",
        "display_mode_icon": "Alleen icoon",
        "display_mode_since": "Sinds vorig gebed",
        "per_prayer_notifications": "Meldingen per gebed",
        "prayer_reminder": "Herinnering (min ervoor)",
        "prayer_offset": "Tijdcorrectie (minuten)",
        "manual_offsets": "Handmatige tijdcorrecties",
        "adhan_per_prayer": "Adhan",
        "language": "Taal",
        "now": "nu",
        "paste_url": "Of plak de URL direct",
        "paste_url_hint": "Ga naar mawaqit.net, vind je moskee en plak de URL",
        "connected_mosque": "Verbonden moskee",
        "mosques": "Moskeeen",
        "search_failed": "Zoeken mislukt",
        "no_prayer_times": "Geen gebedstijden geladen",
        "update_available": "Update beschikbaar",
        "hijri_date": "Hijri-datum",
        "qibla": "Qibla",
        "since_last_prayer": "Sinds {name}",
        "dnd_bypass": "Niet storen doorbreken",
        "dnd_bypass_per_prayer": "Niet storen",
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
        "loading": "جاري التحميل...",
        "no_mosque": "لم يتم تحديد مسجد",
        "no_data": "لا توجد بيانات",
        "refresh": "تحديث",
        "settings": "إعدادات",
        "quit": "خروج",
        "notifications": "إشعارات الصلاة",
        "notification_title": "{name} - {time}",
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
        "dnd_bypass": "تجاوز وضع عدم الإزعاج",
        "dnd_bypass_per_prayer": "تجاوز عدم الإزعاج",
        "hijri_date": "التاريخ الهجري",
        "qibla": "القبلة",
        "since_last_prayer": "منذ {name}",
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
        "next_prayer": "Prochaine priere",
        "loading": "Chargement...",
        "no_mosque": "Aucune mosquee configuree",
        "no_data": "Aucune donnee chargee",
        "refresh": "Actualiser",
        "settings": "Parametres",
        "quit": "Quitter",
        "notifications": "Notifications de priere",
        "notification_title": "{name} - {time}",
        "notification_body": "C'est l'heure de la priere de {name}",
        "cached_data": "Donnees en cache",
        "fetch_error": "Impossible de recuperer les horaires",
        "search": "Rechercher",
        "save": "Enregistrer",
        "mosque_url": "URL Mawaqit",
        "find_mosque": "Trouver votre mosquee",
        "search_hint": "Rechercher par nom ou ville",
        "no_results": "Aucune mosquee trouvee",
        "configure_mosque": "Configurer la mosquee",
        "launch_at_login": "Lancer au demarrage",
        "iqama": "Iqama",
        "show_prayer_times": "Afficher les horaires",
        "saved_mosques": "Mosquees enregistrees",
        "add_mosque": "Ajouter",
        "remove_mosque": "Supprimer",
        "switch_mosque": "Changer",
        "active": "Actif",
        "adhan": "Adhan",
        "adhan_enabled": "Jouer l'adhan",
        "adhan_path": "Fichier audio de l'adhan",
        "adhan_browse": "Parcourir",
        "countdown_format": "Format du compte a rebours",
        "countdown_compact": "Compact",
        "countdown_full": "Complet",
        "language": "Langue",
        "now": "maintenant",
        "paste_url": "Ou collez l'URL directement",
        "paste_url_hint": "Allez sur mawaqit.net, trouvez votre mosquee et collez l'URL",
        "connected_mosque": "Mosquee connectee",
        "mosques": "Mosquees",
        "search_failed": "La recherche a echoue",
        "no_prayer_times": "Aucun horaire de priere charge",
        "update_available": "Mise a jour disponible",
        "dnd_bypass": "Passer le mode Ne pas deranger",
        "dnd_bypass_per_prayer": "Ne pas deranger",
        "hijri_date": "Date hegirienne",
        "qibla": "Qibla",
        "since_last_prayer": "Depuis {name}",
    },
    "tr": {
        "prayer_fajr": "Sabah",
        "prayer_dhuhr": "Ogle",
        "prayer_asr": "Ikindi",
        "prayer_maghrib": "Aksam",
        "prayer_isha": "Yatsi",
        "prayer_shuruq": "Gunes",
        "prayer_jumuah": "Cuma",
        "prayer_jumuah2": "Cuma 2",
        "next_prayer": "Sonraki Namaz",
        "loading": "Yukleniyor...",
        "no_mosque": "Cami ayarlanmadi",
        "no_data": "Veri yuklenmedi",
        "refresh": "Yenile",
        "settings": "Ayarlar",
        "quit": "Cikis",
        "notifications": "Namaz bildirimleri",
        "notification_title": "{name} - {time}",
        "notification_body": "{name} namazi vakti geldi",
        "cached_data": "Onbellekten veri",
        "fetch_error": "Vakitler alinamadi",
        "search": "Ara",
        "save": "Kaydet",
        "mosque_url": "Mawaqit URL",
        "find_mosque": "Caminizi Bulun",
        "search_hint": "Cami adi veya sehir ile arayin",
        "no_results": "Cami bulunamadi",
        "configure_mosque": "Cami ayarla",
        "launch_at_login": "Giriste baslat",
        "iqama": "Kamet",
        "show_prayer_times": "Namaz Vakitlerini Goster",
        "saved_mosques": "Kayitli Camiler",
        "add_mosque": "Ekle",
        "remove_mosque": "Kaldir",
        "switch_mosque": "Degistir",
        "active": "Aktif",
        "adhan": "Ezan",
        "adhan_enabled": "Ezan sesini cal",
        "adhan_path": "Ezan ses dosyasi",
        "adhan_browse": "Gozat",
        "countdown_format": "Geri sayim bicimi",
        "countdown_compact": "Kisa",
        "countdown_full": "Tam",
        "language": "Dil",
        "now": "simdi",
        "paste_url": "Veya URL'yi yapistirin",
        "paste_url_hint": "mawaqit.net'e gidin, caminizi bulun ve URL'yi yapistirin",
        "connected_mosque": "Bagli Cami",
        "mosques": "Camiler",
        "search_failed": "Arama basarisiz",
        "no_prayer_times": "Namaz vakti yuklenmedi",
        "update_available": "Guncelleme mevcut",
        "dnd_bypass": "Rahatsiz Etmeyin modunu as",
        "dnd_bypass_per_prayer": "Rahatsiz Etmeyin",
        "hijri_date": "Hicri tarih",
        "qibla": "Kible",
        "since_last_prayer": "{name}'dan beri",
    },
}

LANGUAGE_LABELS = {
    "en": "English",
    "nl": "Nederlands",
    "ar": "العربية",
    "fr": "Français",
    "tr": "Türkçe",
}

_current_language = "en"


def _set_language(lang):
    global _current_language
    if lang in TRANSLATIONS:
        _current_language = lang


def t(key, **kwargs):
    text = TRANSLATIONS.get(_current_language, {}).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


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
    key = _PRAYER_KEY_MAP.get(name)
    if key:
        return t(key)
    return name


PRAYER_OFFSET_KEYS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
NOTIFICATION_PRAYER_KEYS = PRAYER_OFFSET_KEYS + ["Jumuah"]
KAABA_LATITUDE = 21.422487
KAABA_LONGITUDE = 39.826206
HIJRI_MONTHS = [
    "Muharram",
    "Safar",
    "Rabi al-awwal",
    "Rabi al-thani",
    "Jumada al-awwal",
    "Jumada al-thani",
    "Rajab",
    "Shaban",
    "Ramadan",
    "Shawwal",
    "Dhu al-Qadah",
    "Dhu al-Hijjah",
]

SETTINGS_DEFAULTS = {
    "mosque_url": "",
    "notifications_enabled": True,
    "language": "en",
    "adhan_enabled": False,
    "adhan_path": "",
    "display_mode": "countdown",
    "countdown_format": "compact",
    "dnd_bypass": True,
        "saved_mosques": [],
    }


def normalize_settings(data):
    if not isinstance(data, dict):
        data = {}
    for key, default in SETTINGS_DEFAULTS.items():
        if key not in data:
            data[key] = default
    if "prayer_notification_settings" not in data:
        data["prayer_notification_settings"] = default_prayer_notification_settings()
    else:
        data["prayer_notification_settings"] = merge_prayer_notification_settings(
            data.get("prayer_notification_settings")
        )
    if "prayer_offsets" not in data:
        data["prayer_offsets"] = default_prayer_offsets()
    else:
        data["prayer_offsets"] = merge_prayer_offsets(data.get("prayer_offsets"))
    return data


def build_cache_payload(data):
    return {
        "times": data["times"],
        "shuruq": data.get("shuruq"),
        "name": data.get("name", ""),
        "iqama": data.get("iqama"),
        "iqama_enabled": data.get("iqama_enabled", False),
        "jumua": data.get("jumua"),
        "jumua2": data.get("jumua2"),
        "hijri_date": data.get("hijri_date"),
        "qibla_direction": data.get("qibla_direction"),
        "date": date.today().isoformat(),
    }


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def qibla_bearing(latitude, longitude):
    lat = _as_float(latitude)
    lon = _as_float(longitude)
    if lat is None or lon is None:
        return None

    lat1 = math.radians(lat)
    lat2 = math.radians(KAABA_LATITUDE)
    delta_lon = math.radians(KAABA_LONGITUDE - lon)
    y = math.sin(delta_lon)
    x = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(delta_lon)
    bearing = math.degrees(math.atan2(y, x))
    return round((bearing + 360) % 360)


def format_qibla_direction(latitude, longitude):
    bearing = qibla_bearing(latitude, longitude)
    if bearing is None:
        return None
    return f"{bearing}°"


def _gregorian_to_jdn(year, month, day):
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _islamic_to_jdn(year, month, day):
    return (
        day
        + math.ceil(29.5 * (month - 1))
        + (year - 1) * 354
        + math.floor((3 + 11 * year) / 30)
        + 1948439
        - 1
    )


def gregorian_to_hijri(gregorian_date=None, adjustment=0):
    current = gregorian_date or date.today()
    if isinstance(current, datetime):
        current = current.date()
    jdn = _gregorian_to_jdn(current.year, current.month, current.day) + int(adjustment or 0)
    year = math.floor((30 * (jdn - 1948439) + 10646) / 10631)
    month = min(12, math.ceil((jdn - (29 + _islamic_to_jdn(year, 1, 1))) / 29.5) + 1)
    day = int(jdn - _islamic_to_jdn(year, month, 1) + 1)
    return int(year), int(month), day


def format_hijri_date(gregorian_date=None, adjustment=0):
    year, month, day = gregorian_to_hijri(gregorian_date, adjustment)
    return f"{day} {HIJRI_MONTHS[month - 1]} {year} AH"


def mosque_metadata(mosque):
    adjustment = mosque.get("hijriAdjustment", 0) if isinstance(mosque, dict) else 0
    latitude = mosque.get("latitude") if isinstance(mosque, dict) else None
    longitude = mosque.get("longitude") if isinstance(mosque, dict) else None
    return {
        "hijri_date": format_hijri_date(adjustment=adjustment),
        "qibla_direction": format_qibla_direction(latitude, longitude),
    }


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
        **mosque_metadata(mosque),
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
        "iqama": data.get("iqama"),
        "iqama_enabled": data.get("iqamaEnabled", False),
        "jumua": data.get("jumua"),
        "jumua2": data.get("jumua2"),
        **mosque_metadata(data),
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


def prayer_datetime_events(times, base=None):
    base = base or datetime.now()
    minute_values = []
    for time_str in times:
        h, m = map(int, time_str.split(":"))
        minute_values.append(h * 60 + m)
    if not minute_values:
        return []

    events = []
    day_offset = -1 if len(minute_values) > 1 and minute_values[0] > minute_values[1] else 0
    previous_absolute = None

    for i, minute_value in enumerate(minute_values):
        if i > 0:
            if day_offset < 0:
                day_offset = 0
            while previous_absolute is not None and minute_value + day_offset * 1440 <= previous_absolute:
                day_offset += 1

        absolute_minutes = minute_value + day_offset * 1440
        previous_absolute = absolute_minutes
        h, m = divmod(minute_value, 60)
        dt = base.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=day_offset)
        events.append((i, dt))

    return events


def get_next_prayer(times):
    now = datetime.now()
    events = prayer_datetime_events(times, now)
    for i, dt in events:
        if dt > now:
            return i, dt
    if events:
        i, dt = events[0]
        return i, dt + timedelta(days=1)
    return 0, now


def get_last_prayer(times):
    now = datetime.now()
    events = prayer_datetime_events(times, now)
    last_event = None
    for i, dt in events:
        if dt <= now:
            last_event = (i, dt)
    if last_event:
        return last_event
    if events:
        i, dt = events[-1]
        return i, dt - timedelta(days=1)
    return 0, now


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
    if h > 0:
        return f"-{h}h{m:02d}m"
    return f"-{m}m"


def format_elapsed_since(dt, settings=None):
    elapsed = int((datetime.now() - dt).total_seconds() / 60)
    if elapsed <= 0:
        return t("now")
    h, m = divmod(elapsed, 60)
    fmt = (settings or {}).get("countdown_format", "compact")
    if fmt == "full":
        if h > 0:
            return f"+{h}h {m:02d}m"
        return f"+{m}m"
    if h > 0:
        return f"+{h}h{m:02d}m"
    return f"+{m}m"


def from_minutes(total):
    normalized = total % 1440
    if normalized < 0:
        normalized += 1440
    h, m = divmod(normalized, 60)
    return f"{h:02d}:{m:02d}"


def apply_offset(time_str, offset_minutes):
    if not offset_minutes:
        return time_str
    h, m = map(int, time_str.split(":"))
    return from_minutes(h * 60 + m + offset_minutes)


def default_prayer_notification_settings():
    return {
        key: {"enabled": True, "reminder_minutes": 0, "adhan_enabled": None, "dnd_bypass": None}
        for key in NOTIFICATION_PRAYER_KEYS
    }


def default_prayer_offsets():
    return {key: 0 for key in PRAYER_OFFSET_KEYS}


def merge_prayer_notification_settings(stored):
    merged = default_prayer_notification_settings()
    if not isinstance(stored, dict):
        return merged
    for key in NOTIFICATION_PRAYER_KEYS:
        if key in stored and isinstance(stored[key], dict):
            entry = stored[key]
            merged[key] = {
                "enabled": entry.get("enabled", True) is not False,
                "reminder_minutes": max(0, int(entry.get("reminder_minutes") or 0)),
                "adhan_enabled": entry.get("adhan_enabled"),
                "dnd_bypass": entry.get("dnd_bypass"),
            }
    return merged


def merge_prayer_offsets(stored):
    merged = default_prayer_offsets()
    if not isinstance(stored, dict):
        return merged
    for key in PRAYER_OFFSET_KEYS:
        if key in stored:
            val = int(stored[key] or 0)
            merged[key] = max(-60, min(60, val))
    return merged


def notification_key_for_index(index, is_friday, has_jumua):
    if index == 1 and is_friday and has_jumua:
        return "Jumuah"
    return PRAYER_NAMES[index]


def should_play_adhan(prayer_setting, global_adhan_enabled):
    if prayer_setting.get("adhan_enabled") is True:
        return True
    if prayer_setting.get("adhan_enabled") is False:
        return False
    return bool(global_adhan_enabled)


def should_bypass_dnd(prayer_setting, global_dnd_bypass):
    if prayer_setting.get("dnd_bypass") is True:
        return True
    if prayer_setting.get("dnd_bypass") is False:
        return False
    return bool(global_dnd_bypass)


def apply_prayer_offsets(times, offsets):
    return [
        apply_offset(time_str, offsets.get(PRAYER_NAMES[i], 0))
        for i, time_str in enumerate(times)
    ]


def format_tray_title(name, time_str, countdown, display_mode, settings=None):
    if display_mode == "icon":
        return name or t("next_prayer")
    if display_mode == "since":
        return f"{name}  {countdown}" if countdown else name or t("next_prayer")
    parts = []
    if display_mode in ("countdown", "time", "name", "compact"):
        parts.append(name)
    if display_mode in ("countdown", "time"):
        parts.append(time_str)
    if display_mode in ("countdown", "compact") and countdown:
        parts.append(countdown)
    return "  ".join(parts) if parts else name or t("next_prayer")


def check_for_update(current_version, tag_prefix):
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
