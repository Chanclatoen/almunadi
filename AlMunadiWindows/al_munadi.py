import os
import json
import shutil
import subprocess
import threading
import time
import ctypes
import winsound
from datetime import datetime, timedelta

import pystray
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from winotify import Notification, audio

PRAYER_ICONS = {
    "Fajr": "☀",
    "Dhuhr": "☀",
    "Jumuah": "☀",
    "Asr": "⛅",
    "Maghrib": "\U0001f305",
    "Isha": "☾",
}

_APPDATA_ROOT = os.environ.get("APPDATA", os.path.expanduser("~"))
APP_DATA_DIR = os.path.join(_APPDATA_ROOT, "AlMunadi")
# One-time migration from the pre-rebrand "NextPrayer" data directory.
_LEGACY_DATA_DIR = os.path.join(_APPDATA_ROOT, "NextPrayer")
if os.path.isdir(_LEGACY_DATA_DIR) and not os.path.isdir(APP_DATA_DIR):
    try:
        shutil.copytree(_LEGACY_DATA_DIR, APP_DATA_DIR)
    except Exception:
        pass
os.makedirs(APP_DATA_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "settings.json")
CACHE_FILE = os.path.join(APP_DATA_DIR, "cache.json")

_OLD_SETTINGS = "next_prayer_settings.json"
if os.path.exists(_OLD_SETTINGS) and not os.path.exists(SETTINGS_FILE):
    try:
        import shutil
        shutil.copy2(_OLD_SETTINGS, SETTINGS_FILE)
    except Exception:
        pass

# Al Munadi visual identity: deep charcoal surfaces, emerald primary, saffron
# accent, refined prayer hues. Matches the website and GNOME/macOS styling.
PRAYER_COLORS = {
    "Fajr": "#D9A05B",
    "Dhuhr": "#E3B15A",
    "Jumuah": "#E3B15A",
    "Asr": "#BC8A52",
    "Maghrib": "#C96B4A",
    "Isha": "#7D93C4",
}

PRAYER_COLORS_RGB = {
    "Fajr": (217, 160, 91),
    "Dhuhr": (227, 177, 90),
    "Jumuah": (227, 177, 90),
    "Asr": (188, 138, 82),
    "Maghrib": (201, 107, 74),
    "Isha": (125, 147, 196),
}

BG_COLOR = "#14130F"
CARD_COLOR = "#1F1D17"
CARD_HOVER = "#27241C"
CARD_ALT = "#26231B"
ACCENT = "#46C79E"
ACCENT_HOVER = "#5ED2AC"
ON_ACCENT = "#0C1A14"
TEXT_PRIMARY = "#F1EDE2"
TEXT_SECONDARY = "#AAB0A3"
TEXT_DIM = "#6E7466"
HIGHLIGHT_BG = "#1B2E26"
SHURUQ_ACCENT = "#E3B15A"
ERROR_BG = "#332A18"
ERROR_BORDER = "#C2913B"
ERROR_TEXT = "#E0B36A"
IQAMA_DOT = "#46C79E"
BORDER_COLOR = "#2D2B23"
DIVIDER_COLOR = "#2D2B23"
FONT_FAMILY = "Segoe UI"


# ---------------------------------------------------------------------------
# Shared Python core
# ---------------------------------------------------------------------------

from pathlib import Path
import sys

_CORE_ROOT = Path(__file__).resolve().parent.parent
if str(_CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CORE_ROOT))

from core.al_munadi_core import (
    APP_NAME,
    APP_VERSION,
    TAG_PREFIX,
    RELEASES_URL,
    REPO_RELEASES_PAGE,
    PRAYER_NAMES,
    API_BASE,
    LANGUAGE_LABELS,
    TRANSLATIONS,
    _set_language,
    t,
    _translate_prayer,
    normalize_settings,
    build_cache_payload,
    extract_slug,
    fetch_times_api,
    fetch_times_html,
    fetch_times,
    search_mosques,
    qibla_bearing,
    format_hijri_date,
    resolve_iqama,
    parse_time,
    prayer_datetime_events,
    get_next_prayer,
    get_last_prayer,
    format_countdown,
    format_elapsed_since,
    from_minutes,
    apply_offset,
    default_prayer_notification_settings,
    default_prayer_offsets,
    merge_prayer_notification_settings,
    merge_prayer_offsets,
    notification_key_for_index,
    should_play_adhan,
    should_bypass_dnd,
    apply_prayer_offsets,
    format_tray_title,
    check_for_update,
)

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    return normalize_settings(data)


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
    cache = build_cache_payload(data)
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tray icon rendering
# ---------------------------------------------------------------------------

def create_icon_image(prayer_name):
    color = PRAYER_COLORS_RGB.get(prayer_name, (200, 200, 200))
    # Render at high resolution for smooth anti-aliasing
    render_size = 256
    img = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = render_size // 16  # 16px at 256

    # Draw a subtle drop shadow behind the main circle
    shadow_offset = render_size // 40  # ~6px at 256
    shadow_color = (0, 0, 0, 80)
    draw.ellipse(
        [margin + shadow_offset, margin + shadow_offset,
         render_size - margin + shadow_offset, render_size - margin + shadow_offset],
        fill=shadow_color,
    )

    # Main colored circle
    draw.ellipse(
        [margin, margin, render_size - margin, render_size - margin],
        fill=color,
    )

    letter = prayer_name[0]
    # Try bold font first, then regular
    font_size = render_size * 56 // 128  # scaled proportionally (~112 at 256)
    font = None
    for font_name in ("segoeuib.ttf", "segoeui.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Precise centering using text bounding box
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (render_size - tw) // 2 - bbox[0]
    ty = (render_size - th) // 2 - bbox[1]
    draw.text((tx, ty), letter, fill=(255, 255, 255), font=font)

    # Downscale from 256 to 64 for crisp anti-aliased result
    return img.resize((64, 64), Image.LANCZOS)


def send_notification(prayer_name, time_str, bypass_dnd=False):
    if bypass_dnd:
        _send_toast_bypass_dnd(prayer_name, time_str)
        return
    translated_name = _translate_prayer(prayer_name)
    toast = Notification(
        app_id=APP_NAME,
        title=t("notification_title", name=translated_name, time=time_str),
        msg=t("notification_body", name=translated_name),
    )
    toast.set_audio(audio.Default, loop=False)
    toast.show()


def _send_toast_bypass_dnd(prayer_name, time_str):
    translated_name = _translate_prayer(prayer_name)
    title = t("notification_title", name=translated_name, time=time_str)
    body = t("notification_body", name=translated_name)
    ps_script = (
        '[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null\n'
        '[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null\n'
        '$xml = New-Object Windows.Data.Xml.Dom.XmlDocument\n'
        '$xml.LoadXml(@"\n'
        '<toast scenario=""alarm"" duration=""short"">\n'
        '  <visual><binding template=""ToastGeneric"">\n'
        '    <text><![CDATA[' + title + ']]></text>\n'
        '    <text><![CDATA[' + body + ']]></text>\n'
        '  </binding></visual>\n'
        '  <audio src=""ms-winsoundevent:Notification.Default"" loop=""false"" />\n'
        '</toast>\n'
        '"@)\n'
        '$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("' + APP_NAME + '")\n'
        '$notifier.Show([Windows.UI.Notifications.ToastNotification]::new($xml))'
    )
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=si,
        )
    except Exception:
        pass


def _play_adhan(path):
    """Play an adhan WAV file asynchronously via winsound."""
    try:
        if path and os.path.isfile(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass


def _stop_adhan():
    """Stop any adhan audio currently playing through winsound."""
    try:
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Prayer Times Popup Window
# ---------------------------------------------------------------------------

class PrayerTimesWindow:
    def __init__(self, app):
        import tkinter as tk

        self.app = app
        self.win = tk.Toplevel() if hasattr(app, '_tk_root') and app._tk_root else tk.Tk()
        self.win.title(t("next_prayer"))
        self.win.overrideredirect(True)  # Remove window decorations for clean edge
        self.win.configure(bg=BORDER_COLOR)  # Outer border color
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)

        # Inner frame provides the 1px accent border effect
        self._inner = tk.Frame(self.win, bg=BG_COLOR, padx=0, pady=0)
        self._inner.pack(fill="both", expand=True, padx=1, pady=1)

        self._position_near_tray(344, 490)
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        # Close when clicking outside the window
        self.win.bind("<FocusOut>", lambda e: self._close())

        self._build_ui()

    def _position_near_tray(self, w, h):
        """Position the window near the system tray (bottom-right corner)."""
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = sw - w - 12
        y = sh - h - 50
        self.win.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        import tkinter as tk

        container = self._inner
        pad = 16

        # Mosque name header with mosque icon
        if self.app.mosque_name:
            header_frame = tk.Frame(container, bg=BG_COLOR)
            header_frame.pack(fill="x", padx=pad, pady=(pad, 4))

            tk.Label(
                header_frame,
                text="\U0001f54c",
                font=(FONT_FAMILY, 13),
                fg=TEXT_PRIMARY,
                bg=BG_COLOR,
            ).pack(side="left", padx=(0, 6))

            tk.Label(
                header_frame,
                text=self.app.mosque_name,
                font=(FONT_FAMILY, 13, "bold"),
                fg=TEXT_PRIMARY,
                bg=BG_COLOR,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        if self.app.hijri_date or self.app.qibla_direction:
            meta_parts = []
            if self.app.hijri_date:
                meta_parts.append(f"{t('hijri_date')}: {self.app.hijri_date}")
            if self.app.qibla_direction:
                meta_parts.append(f"{t('qibla')}: {self.app.qibla_direction}")
            tk.Label(
                container,
                text="  |  ".join(meta_parts),
                font=(FONT_FAMILY, 9),
                fg=TEXT_SECONDARY,
                bg=BG_COLOR,
                anchor="w",
            ).pack(fill="x", padx=pad, pady=(0, 4))

        # Update available banner
        if self.app.update_info:
            import webbrowser
            update_ver, update_url = self.app.update_info
            update_frame = tk.Frame(container, bg=HIGHLIGHT_BG, padx=10, pady=6)
            update_frame.pack(fill="x", padx=pad, pady=(4, 4))
            update_label = tk.Label(
                update_frame,
                text=f"⬆ {t('update_available')} — v{update_ver}",
                font=(FONT_FAMILY, 10, "bold"),
                fg=ACCENT,
                bg=HIGHLIGHT_BG,
                cursor="hand2",
            )
            update_label.pack(fill="x")
            update_label.bind("<Button-1>", lambda e, u=update_url: webbrowser.open(u))

        # Divider
        tk.Frame(container, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(4, 8))

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

                self._build_prayer_row(container, name, t_str, iq, is_next, is_past, i)

            if self.app._is_friday() and self.app.jumua2:
                tk.Frame(container, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=2)
                self._build_simple_row(container, t("prayer_jumuah2"), self.app.jumua2)

        elif not self.app.settings.get("mosque_url"):
            self._build_first_run_state(container)
        else:
            tk.Label(
                container,
                text=t("no_prayer_times"),
                font=(FONT_FAMILY, 11),
                fg=TEXT_SECONDARY,
                bg=BG_COLOR,
            ).pack(pady=20)

        # Shuruq with warm amber accent
        if self.app.shuruq:
            tk.Frame(container, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(8, 4))
            self._build_shuruq_row(container, t("prayer_shuruq"), self.app.shuruq)

        # Status / error banner
        if self.app.last_error:
            tk.Frame(container, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(8, 4))
            msg = self.app.last_error
            if self.app.is_cached:
                msg = f"{t('cached_data')}. {msg}"
            # Styled error banner with amber/orange background
            error_frame = tk.Frame(container, bg=ERROR_BG, padx=10, pady=6)
            error_frame.pack(fill="x", padx=pad, pady=2)
            # Left accent strip on error banner
            tk.Frame(error_frame, bg=ERROR_BORDER, width=3).pack(side="left", fill="y", padx=(0, 8))
            tk.Label(
                error_frame,
                text=msg,
                font=(FONT_FAMILY, 9),
                fg=ERROR_TEXT,
                bg=ERROR_BG,
                anchor="w",
                wraplength=280,
            ).pack(fill="x", side="left")

        # Bottom buttons
        spacer = tk.Frame(container, bg=BG_COLOR)
        spacer.pack(fill="both", expand=True)

        tk.Frame(container, bg=TEXT_DIM, height=1).pack(fill="x", padx=pad, pady=(4, 8))

        btn_frame = tk.Frame(container, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=pad, pady=(0, pad))

        self._make_pill_button(btn_frame, t("refresh"), self._on_refresh).pack(side="left")
        self._make_pill_button(btn_frame, t("settings"), self._on_settings).pack(side="left", padx=(8, 0))
        self._make_pill_button(btn_frame, t("quit"), self._on_quit).pack(side="right")

    def _build_prayer_row(self, parent, name, time_str, iqama, is_next, is_past, index):
        import tkinter as tk

        # Translate the prayer name for display
        display_name = _translate_prayer(name)

        bg = HIGHLIGHT_BG if is_next else BG_COLOR
        fg = ACCENT if is_next else TEXT_DIM if is_past else TEXT_PRIMARY
        color = PRAYER_COLORS.get(name, "#888888")

        # Outer wrapper for the left accent border on next prayer
        if is_next:
            outer = tk.Frame(parent, bg=ACCENT)
            outer.pack(fill="x")
            row = tk.Frame(outer, bg=bg, padx=12, pady=8)
            row.pack(fill="x", padx=(4, 0))  # 4px blue left accent strip
        else:
            outer = None
            row = tk.Frame(parent, bg=bg, padx=16, pady=8)
            row.pack(fill="x")

        # Hover effect bindings
        def _on_enter(e):
            if not is_next:
                row.configure(bg=CARD_HOVER)
                for child in row.winfo_children():
                    try:
                        child.configure(bg=CARD_HOVER)
                    except Exception:
                        pass
                    # Also update children of sub-frames
                    if hasattr(child, 'winfo_children'):
                        for sub in child.winfo_children():
                            try:
                                sub.configure(bg=CARD_HOVER)
                            except Exception:
                                pass

        def _on_leave(e):
            if not is_next:
                row.configure(bg=BG_COLOR)
                for child in row.winfo_children():
                    try:
                        child.configure(bg=BG_COLOR)
                    except Exception:
                        pass
                    if hasattr(child, 'winfo_children'):
                        for sub in child.winfo_children():
                            try:
                                sub.configure(bg=BG_COLOR)
                            except Exception:
                                pass

        row.bind("<Enter>", _on_enter)
        row.bind("<Leave>", _on_leave)

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
            iq_frame = tk.Frame(name_frame, bg=bg)
            iq_frame.pack(anchor="w")
            # Small colored dot badge before iqama time
            iq_dot = tk.Canvas(iq_frame, width=8, height=8, bg=bg, highlightthickness=0)
            iq_dot.create_oval(1, 1, 7, 7, fill=IQAMA_DOT, outline="")
            iq_dot.pack(side="left", padx=(0, 4), pady=2)
            tk.Label(
                iq_frame,
                text=f"{t('iqama')} {iqama}",
                font=(FONT_FAMILY, 9),
                fg=TEXT_SECONDARY if is_next else TEXT_DIM,
                bg=bg,
                anchor="w",
            ).pack(side="left", anchor="w")

        right_frame = tk.Frame(row, bg=bg)
        right_frame.pack(side="right")

        if is_next:
            countdown = format_countdown(parse_time(time_str), self.app.settings)
            tk.Label(
                right_frame,
                text=countdown,
                font=(FONT_FAMILY, 10, "bold"),
                fg=ACCENT,
                bg=bg,
            ).pack(anchor="e")

        tk.Label(
            right_frame,
            text=time_str,
            font=(FONT_FAMILY, 12, weight),
            fg=fg,
            bg=bg,
        ).pack(anchor="e")

    def _build_first_run_state(self, parent):
        """Friendly empty state shown before any mosque is configured."""
        import tkinter as tk

        box = tk.Frame(parent, bg=BG_COLOR)
        box.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(
            box, text="المُنادي", font=(FONT_FAMILY, 20),
            fg=SHURUQ_ACCENT, bg=BG_COLOR,
        ).pack(pady=(12, 2))
        tk.Label(
            box, text=t("first_run_title"), font=(FONT_FAMILY, 13, "bold"),
            fg=TEXT_PRIMARY, bg=BG_COLOR,
        ).pack(pady=(0, 6))
        tk.Label(
            box, text=t("first_run_body"), font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY, bg=BG_COLOR, wraplength=270, justify="center",
        ).pack(pady=(0, 14))

        cta = tk.Label(
            box, text=t("find_mosque"), font=(FONT_FAMILY, 11, "bold"),
            fg=ON_ACCENT, bg=ACCENT, padx=18, pady=8, cursor="hand2",
        )
        cta.pack()
        cta.bind("<Button-1>", lambda e: self._on_settings())
        cta.bind("<Enter>", lambda e: cta.configure(bg=ACCENT_HOVER))
        cta.bind("<Leave>", lambda e: cta.configure(bg=ACCENT))

    def _build_simple_row(self, parent, name, time_str):
        import tkinter as tk

        row = tk.Frame(parent, bg=BG_COLOR, padx=16, pady=4)
        row.pack(fill="x")

        tk.Label(
            row, text=name, font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY, bg=BG_COLOR, anchor="w",
        ).pack(side="left")
        tk.Label(
            row, text=time_str, font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY, bg=BG_COLOR,
        ).pack(side="right")

    def _build_shuruq_row(self, parent, name, time_str):
        """Build the Shuruq row with a warm amber/sunrise accent."""
        import tkinter as tk

        row = tk.Frame(parent, bg=BG_COLOR, padx=16, pady=6)
        row.pack(fill="x")

        # Small amber sunrise dot
        sun_dot = tk.Canvas(row, width=10, height=10, bg=BG_COLOR, highlightthickness=0)
        sun_dot.create_oval(1, 1, 9, 9, fill=SHURUQ_ACCENT, outline="")
        sun_dot.pack(side="left", padx=(0, 8))

        tk.Label(
            row, text=name, font=(FONT_FAMILY, 10),
            fg=SHURUQ_ACCENT, bg=BG_COLOR, anchor="w",
        ).pack(side="left")
        tk.Label(
            row, text=time_str, font=(FONT_FAMILY, 10, "bold"),
            fg=SHURUQ_ACCENT, bg=BG_COLOR,
        ).pack(side="right")

    def _make_pill_button(self, parent, text, command):
        """Create a rounded-pill styled button using a frame with padding."""
        import tkinter as tk

        pill = tk.Frame(parent, bg=CARD_COLOR, padx=1, pady=1)

        btn = tk.Label(
            pill,
            text=text,
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=CARD_COLOR,
            padx=14,
            pady=6,
            borderwidth=0,
            cursor="hand2",
        )
        btn.pack()

        def _enter(e):
            btn.configure(bg=CARD_HOVER, fg=TEXT_PRIMARY)
            pill.configure(bg=CARD_HOVER)

        def _leave(e):
            btn.configure(bg=CARD_COLOR, fg=TEXT_SECONDARY)
            pill.configure(bg=CARD_COLOR)

        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)
        pill.bind("<Button-1>", lambda e: command())
        pill.bind("<Enter>", _enter)
        pill.bind("<Leave>", _leave)
        return pill

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
        self.win.title(f"{APP_NAME} — {t('settings')}")
        self.win.configure(bg=BG_COLOR)
        self.win.resizable(False, False)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        # Never grow taller than the screen; the content scrolls anyway.
        w, h = 540, min(sh - 80, 800)
        self.win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        style = ttk.Style(self.win)
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=BG_COLOR)
        style.configure("Dark.TLabel", background=BG_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 10))
        style.configure("Header.TLabel", background=BG_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 14, "bold"))
        style.configure("Dim.TLabel", background=BG_COLOR, foreground=TEXT_SECONDARY, font=(FONT_FAMILY, 9))
        style.configure("Dark.TEntry", fieldbackground=CARD_COLOR, foreground=TEXT_PRIMARY, insertcolor=TEXT_PRIMARY)
        style.configure("Dark.TButton", background=CARD_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 10), padding=(12, 6), borderwidth=0)
        style.map("Dark.TButton", background=[("active", CARD_HOVER)])
        style.configure("Accent.TButton", background=ACCENT, foreground=ON_ACCENT, font=(FONT_FAMILY, 10, "bold"), padding=(14, 7), borderwidth=0)
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])
        style.configure("Dark.TCheckbutton", background=BG_COLOR, foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 10))
        style.configure("Treeview", background=CARD_COLOR, foreground=TEXT_PRIMARY, fieldbackground=CARD_COLOR, font=(FONT_FAMILY, 10), rowheight=40)
        style.configure("Treeview.Heading", background=BG_COLOR, foreground=TEXT_SECONDARY, font=(FONT_FAMILY, 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])
        style.configure("Dark.TCombobox", fieldbackground=CARD_COLOR, foreground=TEXT_PRIMARY, background=CARD_COLOR, font=(FONT_FAMILY, 10))
        style.map("Dark.TCombobox", fieldbackground=[("readonly", CARD_COLOR)])

        # Treeview alternating row colors via tags
        self._tree_tag_colors = {
            "oddrow": CARD_COLOR,
            "evenrow": CARD_ALT,
        }

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

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self._canvas = canvas

        inner_pad = pad

        # --- Language selector ---
        self._build_section_header(main, t("language"), inner_pad, top_pad=inner_pad)

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
        self._build_divider(main, inner_pad)

        # --- Search section ---
        self._build_section_header(main, t("find_mosque"), inner_pad)
        ttk.Label(main, text=t("search_hint"), style="Dim.TLabel").pack(anchor="w", padx=inner_pad, pady=(0, 8))

        search_frame = ttk.Frame(main, style="Dark.TFrame")
        search_frame.pack(fill="x", padx=inner_pad, pady=(0, 8))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=(FONT_FAMILY, 11), bg=CARD_COLOR, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY, relief="flat", bd=0,
            highlightthickness=2, highlightcolor=ACCENT, highlightbackground=TEXT_DIM,
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

        # Configure alternating row tags for results tree
        self.results_tree.tag_configure("oddrow", background=CARD_COLOR)
        self.results_tree.tag_configure("evenrow", background=CARD_ALT)

        # Divider
        self._build_divider(main, inner_pad)

        # --- URL section ---
        self._build_section_header(main, t("paste_url"), inner_pad)
        ttk.Label(main, text=t("paste_url_hint"), style="Dim.TLabel").pack(anchor="w", padx=inner_pad, pady=(0, 8))

        url_frame = ttk.Frame(main, style="Dark.TFrame")
        url_frame.pack(fill="x", padx=inner_pad, pady=(0, 12))

        self.url_var = tk.StringVar(value=app.settings.get("mosque_url", ""))
        self.url_entry = tk.Entry(
            url_frame, textvariable=self.url_var,
            font=(FONT_FAMILY, 11), bg=CARD_COLOR, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY, relief="flat", bd=0,
            highlightthickness=2, highlightcolor=ACCENT, highlightbackground=TEXT_DIM,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=6)

        ttk.Button(url_frame, text=t("save"), style="Accent.TButton", command=self._save_url).pack(side="right", padx=(8, 0))

        # --- Connected mosque ---
        if app.mosque_name:
            self._build_divider(main, inner_pad)
            ttk.Label(main, text=f"{t('connected_mosque')}: {app.mosque_name}", style="Dim.TLabel").pack(anchor="w", padx=inner_pad)

        # --- Notifications toggle ---
        self._build_divider(main, inner_pad)
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

        self.dnd_bypass_var = tk.BooleanVar(value=app.settings.get("dnd_bypass", True))
        dnd_cb = tk.Checkbutton(
            main,
            text=f"  {t('dnd_bypass')}",
            variable=self.dnd_bypass_var,
            font=(FONT_FAMILY, 11),
            fg=TEXT_PRIMARY,
            bg=BG_COLOR,
            selectcolor=CARD_COLOR,
            activebackground=BG_COLOR,
            activeforeground=TEXT_PRIMARY,
            bd=0,
            highlightthickness=0,
        )
        dnd_cb.pack(anchor="w", padx=inner_pad)

        # --- Adhan section ---
        self._build_divider(main, inner_pad)
        self._build_section_header(main, t("adhan"), inner_pad)

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

        adhan_btn_frame = ttk.Frame(main, style="Dark.TFrame")
        adhan_btn_frame.pack(fill="x", padx=inner_pad, pady=(4, 4))
        ttk.Button(adhan_btn_frame, text=t("test_adhan"), style="Dark.TButton", command=self._test_adhan).pack(side="left")
        ttk.Button(adhan_btn_frame, text=t("stop_adhan"), style="Dark.TButton", command=self._stop_adhan_clicked).pack(side="left", padx=(8, 0))
        self._adhan_status_var = tk.StringVar(value="")
        ttk.Label(adhan_btn_frame, textvariable=self._adhan_status_var, style="Dim.TLabel").pack(side="left", padx=(10, 0))

        # --- Display mode ---
        self._build_divider(main, inner_pad)
        self._build_section_header(main, t("display_mode"), inner_pad)

        dm_frame = ttk.Frame(main, style="Dark.TFrame")
        dm_frame.pack(fill="x", padx=inner_pad, pady=(0, 4))

        self.display_mode_var = tk.StringVar(value=app.settings.get("display_mode", "countdown"))
        dm_combo = ttk.Combobox(
            dm_frame,
            textvariable=self.display_mode_var,
            values=["countdown", "since", "time", "name", "compact", "icon"],
            state="readonly",
            style="Dark.TCombobox",
            width=12,
        )
        dm_combo.pack(side="left")

        # --- Countdown format ---
        self._build_divider(main, inner_pad)
        self._build_section_header(main, t("countdown_format"), inner_pad)

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

        # --- Per-prayer notifications ---
        self._build_divider(main, inner_pad)
        self._build_section_header(main, t("per_prayer_notifications"), inner_pad)

        self._prayer_notif_vars = {}
        notif_settings = app.settings.get(
            "prayer_notification_settings", default_prayer_notification_settings()
        )
        for key in NOTIFICATION_PRAYER_KEYS:
            row = ttk.Frame(main, style="Dark.TFrame")
            row.pack(fill="x", padx=inner_pad, pady=2)
            ttk.Label(row, text=key, style="Dark.TLabel", width=8).pack(side="left")

            enabled_var = tk.BooleanVar(value=notif_settings.get(key, {}).get("enabled", True))
            ttk.Checkbutton(row, variable=enabled_var, style="Dark.TCheckbutton").pack(side="left")

            ttk.Label(row, text=t("prayer_reminder"), style="Dim.TLabel").pack(side="left", padx=(8, 4))
            reminder_var = tk.IntVar(value=notif_settings.get(key, {}).get("reminder_minutes", 0))
            tk.Spinbox(
                row, from_=0, to=120, textvariable=reminder_var, width=4,
                bg=CARD_COLOR, fg=TEXT_PRIMARY, buttonbackground=CARD_COLOR,
            ).pack(side="left")

            adhan_val = notif_settings.get(key, {}).get("adhan_enabled")
            adhan_var = tk.StringVar(value="global" if adhan_val is None else ("on" if adhan_val else "off"))
            ttk.Combobox(
                row, textvariable=adhan_var, values=["global", "on", "off"],
                state="readonly", style="Dark.TCombobox", width=8,
            ).pack(side="left", padx=(8, 0))

            dnd_val = notif_settings.get(key, {}).get("dnd_bypass")
            dnd_var = tk.StringVar(value="global" if dnd_val is None else ("on" if dnd_val else "off"))
            ttk.Combobox(
                row, textvariable=dnd_var, values=["global", "on", "off"],
                state="readonly", style="Dark.TCombobox", width=8,
            ).pack(side="left", padx=(8, 0))

            self._prayer_notif_vars[key] = {
                "enabled": enabled_var,
                "reminder": reminder_var,
                "adhan": adhan_var,
                "dnd_bypass": dnd_var,
            }

        # --- Manual offsets ---
        self._build_divider(main, inner_pad)
        self._build_section_header(main, t("manual_offsets"), inner_pad)
        ttk.Label(main, text=t("offsets_hint"), style="Dim.TLabel", wraplength=470, justify="left").pack(anchor="w", padx=inner_pad, pady=(0, 6))

        self._offset_vars = {}
        offsets = app.settings.get("prayer_offsets", default_prayer_offsets())
        for key in PRAYER_OFFSET_KEYS:
            row = ttk.Frame(main, style="Dark.TFrame")
            row.pack(fill="x", padx=inner_pad, pady=2)
            ttk.Label(row, text=f"{key} {t('prayer_offset')}", style="Dark.TLabel", width=24).pack(side="left")
            var = tk.IntVar(value=offsets.get(key, 0))
            tk.Spinbox(
                row, from_=-60, to=60, textvariable=var, width=5,
                bg=CARD_COLOR, fg=TEXT_PRIMARY, buttonbackground=CARD_COLOR,
            ).pack(side="left")
            self._offset_vars[key] = var

        ttk.Button(main, text=t("reset_offsets"), style="Dark.TButton", command=self._reset_offsets).pack(anchor="w", padx=inner_pad, pady=(6, 0))

        # --- Saved Mosques section ---
        self._build_divider(main, inner_pad)
        self._build_section_header(main, t("saved_mosques"), inner_pad)

        self.mosque_tree = ttk.Treeview(
            main, columns=("url",), show="headings", height=4, selectmode="browse",
        )
        self.mosque_tree.heading("url", text="URL")
        self.mosque_tree.column("url", width=460)
        self.mosque_tree.pack(fill="x", padx=inner_pad, pady=(0, 4))
        self.mosque_tree.bind("<Double-1>", self._on_mosque_double_click)

        # Configure alternating row tags for mosque tree
        self.mosque_tree.tag_configure("oddrow", background=CARD_COLOR)
        self.mosque_tree.tag_configure("evenrow", background=CARD_ALT)

        mosque_btn_frame = ttk.Frame(main, style="Dark.TFrame")
        mosque_btn_frame.pack(fill="x", padx=inner_pad, pady=(0, 12))

        ttk.Button(mosque_btn_frame, text=t("add_mosque"), style="Dark.TButton", command=self._add_current_mosque).pack(side="left")
        ttk.Button(mosque_btn_frame, text=t("switch_mosque"), style="Accent.TButton", command=self._switch_mosque).pack(side="left", padx=(8, 0))
        ttk.Button(mosque_btn_frame, text=t("remove_mosque"), style="Dark.TButton", command=self._remove_mosque).pack(side="left", padx=(8, 0))

        self._populate_mosque_tree()

        # --- Save All button at the bottom ---
        self._build_divider(main, inner_pad, top=12, bottom=8)
        ttk.Button(main, text=t("save"), style="Accent.TButton", command=self._save_all).pack(anchor="e", padx=inner_pad, pady=(0, inner_pad))

        self.search_entry.focus_set()

    def _build_section_header(self, parent, text, pad, top_pad=0):
        """Build a section header with accent underline."""
        import tkinter as tk

        header_container = tk.Frame(parent, bg=BG_COLOR)
        header_container.pack(fill="x", padx=pad, pady=(top_pad, 4))

        tk.Label(
            header_container,
            text=text,
            font=(FONT_FAMILY, 14, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_COLOR,
            anchor="w",
        ).pack(anchor="w")

        # Accent underline
        tk.Frame(header_container, bg=ACCENT, height=2, width=40).pack(anchor="w", pady=(2, 0))

    def _build_divider(self, parent, pad, top=0, bottom=12):
        """Build a visible section divider."""
        import tkinter as tk
        tk.Frame(parent, bg=DIVIDER_COLOR, height=1).pack(fill="x", padx=pad, pady=(top, bottom))

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
        self.results_tree.insert("", "end", text=t("searching"), values=("",))

        # Run the network search off the UI thread so the window stays responsive.
        def worker():
            try:
                results = search_mosques(query)
            except Exception:
                results = None
            try:
                self.win.after(0, lambda: self._apply_search_results(results))
            except Exception:
                pass  # window was closed while searching

        threading.Thread(target=worker, daemon=True).start()

    def _apply_search_results(self, results):
        try:
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            if results is None:
                self.results_tree.insert("", "end", text=t("search_failed"), values=("",))
                return
            self.search_results = results
            if not results:
                self.results_tree.insert("", "end", text=t("no_results"), values=("",))
                return
            for i, m in enumerate(results):
                loc = m["localisation"]
                if len(loc) > 50:
                    loc = loc[:47] + "..."
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.results_tree.insert("", "end", text=m["name"], values=(loc,), tags=(tag,))
        except Exception:
            pass  # window was closed while searching

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
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
            parent=self.win,
        )
        if path:
            self.adhan_path_var.set(path)
            self.app.settings["adhan_path"] = path
            save_settings(self.app.settings)

    def _test_adhan(self):
        path = self.adhan_path_var.get()
        if not path or not os.path.isfile(path):
            self._adhan_status_var.set(t("adhan_file_missing"))
            return
        self._adhan_status_var.set("")
        _play_adhan(path)

    def _stop_adhan_clicked(self):
        _stop_adhan()

    def _reset_offsets(self):
        for var in self._offset_vars.values():
            var.set(0)

    # --- Saved Mosques ---

    def _populate_mosque_tree(self):
        for item in self.mosque_tree.get_children():
            self.mosque_tree.delete(item)
        saved = self.app.settings.get("saved_mosques", [])
        active_url = self.app.settings.get("mosque_url", "")
        for i, m in enumerate(saved):
            name = m.get("name", "")
            url = m.get("url", "")
            marker = f"[{t('active')}] " if url == active_url else ""
            display = f"{marker}{name}" if name else url
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.mosque_tree.insert("", "end", values=(display,), tags=(tag,))

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
        """Save language, display, countdown format, adhan, and prayer settings."""
        lang = self.lang_var.get()
        self.app.settings["language"] = lang
        _set_language(lang)

        self.app.settings["display_mode"] = self.display_mode_var.get()
        self.app.settings["countdown_format"] = self.countdown_var.get()
        self.app.settings["adhan_enabled"] = self.adhan_var.get()
        self.app.settings["adhan_path"] = self.adhan_path_var.get()
        self.app.settings["notifications_enabled"] = self.notif_var.get()
        self.app.settings["dnd_bypass"] = self.dnd_bypass_var.get()

        def safe_int(var, default=0):
            # IntVar.get() raises TclError when the user typed junk in a Spinbox.
            try:
                return int(var.get())
            except Exception:
                return default

        notif_settings = {}
        for key, vars_dict in self._prayer_notif_vars.items():
            adhan_sel = vars_dict["adhan"].get()
            adhan_enabled = None if adhan_sel == "global" else adhan_sel == "on"
            dnd_sel = vars_dict["dnd_bypass"].get()
            dnd_enabled = None if dnd_sel == "global" else dnd_sel == "on"
            notif_settings[key] = {
                "enabled": vars_dict["enabled"].get(),
                "reminder_minutes": safe_int(vars_dict["reminder"]),
                "adhan_enabled": adhan_enabled,
                "dnd_bypass": dnd_enabled,
            }
        self.app.settings["prayer_notification_settings"] = merge_prayer_notification_settings(notif_settings)

        offsets = {key: safe_int(var) for key, var in self._offset_vars.items()}
        self.app.settings["prayer_offsets"] = merge_prayer_offsets(offsets)

        save_settings(self.app.settings)

        # Rebuild the tray menu / title with the new language
        self.app.update_icon()
        if self.app.settings.get("notifications_enabled", True):
            self.app._schedule_notifications()
        else:
            self.app._cancel_notification_timers()

        self.win.destroy()
        self._unbind_mousewheel()

    def _unbind_mousewheel(self):
        try:
            self._canvas.unbind_all("<MouseWheel>")
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
        self.hijri_date = None
        self.qibla_direction = None
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
        offsets = self.settings.get("prayer_offsets", default_prayer_offsets())
        return apply_prayer_offsets(times, offsets)

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
        prayer_settings = self.settings.get(
            "prayer_notification_settings", default_prayer_notification_settings()
        )
        global_adhan = self.settings.get("adhan_enabled", False)
        global_dnd = self.settings.get("dnd_bypass", True)
        adhan_path = self.settings.get("adhan_path", "")

        events = prayer_datetime_events(display_times, now)
        if events and events[0][1] <= now:
            i, dt = events[0]
            events.append((i, dt + timedelta(days=1)))

        for i, dt in events:
            t_str = display_times[i]
            notif_key = notification_key_for_index(i, self._is_friday(), bool(self.jumua))
            setting = prayer_settings.get(notif_key, {"enabled": True, "reminder_minutes": 0})
            if not setting.get("enabled", True):
                continue

            name = display_names[i]

            play_adhan = should_play_adhan(setting, global_adhan)
            bypass_dnd = should_bypass_dnd(setting, global_dnd)

            reminder_minutes = setting.get("reminder_minutes", 0) or 0
            if reminder_minutes > 0:
                reminder_dt = dt - timedelta(minutes=reminder_minutes)
                reminder_delay = (reminder_dt - now).total_seconds()
                if reminder_delay > 0:
                    timer = threading.Timer(
                        reminder_delay,
                        self._fire_reminder_notification,
                        args=(name, reminder_minutes, bypass_dnd),
                    )
                    timer.daemon = True
                    timer.start()
                    self.notification_timers.append(timer)

            delay = (dt - now).total_seconds()
            if delay > 0:
                timer = threading.Timer(
                    delay,
                    self._fire_notification,
                    args=(name, t_str, play_adhan, adhan_path, bypass_dnd),
                )
                timer.daemon = True
                timer.start()
                self.notification_timers.append(timer)

    def _fire_reminder_notification(self, name, minutes, bypass_dnd=False):
        if bypass_dnd:
            _send_toast_bypass_dnd(name, f"{minutes}m")
            return
        translated = _translate_prayer(name)
        toast = Notification(
            app_id=APP_NAME,
            title=translated,
            msg=t("reminder_body", name=translated, minutes=minutes),
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()

    def _fire_notification(self, name, time_str, play_adhan=False, adhan_path="", bypass_dnd=False):
        if play_adhan and adhan_path and os.path.isfile(adhan_path):
            _play_adhan(adhan_path)
        else:
            send_notification(name, time_str, bypass_dnd=bypass_dnd)
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
        self.hijri_date = data.get("hijri_date")
        self.qibla_direction = data.get("qibla_direction")
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
        import webbrowser
        display_times = self._display_times()
        display_names = self._display_names()

        items = []
        if not self.settings.get("mosque_url"):
            # First run: the default action takes the user straight to setup.
            items.append(pystray.MenuItem(
                t("configure_mosque"),
                lambda: self.show_settings(),
                default=True,
            ))
        else:
            items.append(pystray.MenuItem(
                t("show_prayer_times"),
                lambda: self.show_prayer_times(),
                default=True,
            ))

        if self.update_info:
            ver, url = self.update_info
            items.append(pystray.MenuItem(
                f"⬆ {t('update_available')} (v{ver})",
                (lambda u: lambda: webbrowser.open(u))(url),
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

        if self.hijri_date or self.qibla_direction:
            items.append(pystray.Menu.SEPARATOR)
            if self.hijri_date:
                items.append(pystray.MenuItem(
                    f"{t('hijri_date')}: {self.hijri_date}",
                    None,
                    enabled=False,
                ))
            if self.qibla_direction:
                items.append(pystray.MenuItem(
                    f"{t('qibla')}: {self.qibla_direction}",
                    None,
                    enabled=False,
                ))

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
        if not self.settings.get("mosque_url"):
            return t("set_mosque")
        display_times = self._display_times()
        if not display_times:
            return t("next_prayer")
        idx, next_dt = get_next_prayer(display_times)
        display_mode = self.settings.get("display_mode", "countdown")
        if display_mode == "since":
            last_idx, last_dt = get_last_prayer(display_times)
            name = t("since_last_prayer", name=_translate_prayer(self._display_names()[last_idx]))
            t_str = display_times[last_idx]
            countdown = format_elapsed_since(last_dt, self.settings)
        else:
            name = _translate_prayer(self._display_names()[idx])
            t_str = display_times[idx]
            countdown = format_countdown(next_dt, self.settings)
        title = format_tray_title(name, t_str, countdown, display_mode, self.settings)
        suffix = f" ({t('cached_data')})" if self.is_cached else ""
        return f"{title}{suffix}"

    def refresh(self):
        url = self.settings.get("mosque_url", "")
        if not url:
            return

        try:
            data = fetch_times(url)
            self._apply_data(data)
            self.update_icon()
        except Exception:
            # Keep the UI message calm; details are intentionally not shown.
            self.last_error = t("fetch_error")
            if not self.times:
                self._load_cache()
            self.update_icon()

    def update_icon(self):
        if not self.icon:
            return
        display_times = self._display_times()
        if not display_times:
            # First run / no data yet: keep the menu and title meaningful.
            self.icon.title = self.get_title()
            self.icon.menu = self.build_menu()
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
            _enable_dpi_awareness()
            PrayerTimesWindow(self).show()
        except Exception:
            pass

    def show_settings(self):
        threading.Thread(target=self._open_settings_window, daemon=True).start()

    def _open_settings_window(self):
        try:
            _enable_dpi_awareness()
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
        _enable_dpi_awareness()
        img = create_icon_image("Fajr")
        initial_title = self.get_title() if not self.settings.get("mosque_url") else f"{t('next_prayer')} - {t('loading')}"
        self.icon = pystray.Icon(
            APP_NAME,
            img,
            title=initial_title,
            menu=self.build_menu(),
        )

        bg = threading.Thread(target=self.background_loop, daemon=True)
        bg.start()

        self.icon.run()


def _enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


if __name__ == "__main__":
    app = NextPrayerApp()
    app.run()
