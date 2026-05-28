import re
import json
import threading
import time
from datetime import datetime, timedelta
from io import BytesIO

import requests
import pystray
from PIL import Image, ImageDraw, ImageFont
from winotify import Notification, audio

APP_NAME = "Next Prayer (Mawaqit)"
PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
SETTINGS_FILE = "next_prayer_settings.json"

PRAYER_COLORS = {
    "Fajr": (255, 183, 77),
    "Dhuhr": (255, 235, 59),
    "Asr": (255, 167, 38),
    "Maghrib": (239, 108, 0),
    "Isha": (100, 140, 200),
}


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"mosque_url": ""}


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def extract_slug(url):
    match = re.search(r"mawaqit\.net/\w+/(?:w/)?(.+?)/?$", url)
    return match.group(1) if match else None


def fetch_times(url):
    fetch_url = url
    if "/w/" not in fetch_url:
        slug = extract_slug(fetch_url)
        if slug:
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


def parse_time(time_str):
    h, m = map(int, time_str.split(":"))
    now = datetime.now()
    return now.replace(hour=h, minute=m, second=0, microsecond=0)


def get_next_prayer(times):
    now = datetime.now()
    for i, t in enumerate(times):
        dt = parse_time(t)
        if dt > now:
            return i, dt
    fajr = parse_time(times[0]) + timedelta(days=1)
    return 0, fajr


def format_countdown(dt):
    remaining = int((dt - datetime.now()).total_seconds() / 60)
    if remaining <= 0:
        return "now"
    h, m = divmod(remaining, 60)
    if h > 0:
        return f"-{h}h{m:02d}m"
    return f"-{m}m"


def create_icon_image(prayer_name):
    color = PRAYER_COLORS.get(prayer_name, (200, 200, 200))
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img


def send_notification(prayer_name, time_str):
    toast = Notification(
        app_id=APP_NAME,
        title=f"{prayer_name} - {time_str}",
        msg=f"It's time for {prayer_name} prayer",
    )
    toast.set_audio(audio.Default, loop=False)
    toast.show()


class NextPrayerApp:
    def __init__(self):
        self.settings = load_settings()
        self.times = None
        self.shuruq = None
        self.mosque_name = ""
        self.icon = None
        self.running = True
        self.notified = set()

    def build_menu(self):
        items = []

        if self.mosque_name:
            items.append(pystray.MenuItem(self.mosque_name, None, enabled=False))
            items.append(pystray.Menu.SEPARATOR)

        if self.times:
            for i, name in enumerate(PRAYER_NAMES):
                t = self.times[i] if i < len(self.times) else "--:--"
                idx, next_dt = get_next_prayer(self.times)
                prefix = "▶ " if i == idx and parse_time(t) > datetime.now() else "   "
                items.append(
                    pystray.MenuItem(f"{prefix}{name:<12}{t}", None, enabled=False)
                )

            if self.shuruq:
                items.append(pystray.Menu.SEPARATOR)
                items.append(
                    pystray.MenuItem(f"   Shuruq      {self.shuruq}", None, enabled=False)
                )
        else:
            items.append(pystray.MenuItem("No data loaded", None, enabled=False))

        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Refresh", lambda: self.refresh()))
        items.append(pystray.MenuItem("Set Mosque URL", lambda: self.prompt_url()))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Quit", lambda: self.quit()))

        return pystray.Menu(*items)

    def get_title(self):
        if not self.times:
            return "Next Prayer"
        idx, next_dt = get_next_prayer(self.times)
        name = PRAYER_NAMES[idx]
        t = self.times[idx]
        countdown = format_countdown(next_dt)
        return f"{name}  {t}  {countdown}"

    def refresh(self):
        url = self.settings.get("mosque_url", "")
        if not url:
            return

        try:
            data = fetch_times(url)
            self.times = data["times"]
            self.shuruq = data.get("shuruq")
            self.mosque_name = data.get("name", "")
            self.notified.clear()
            self.update_icon()
        except Exception as e:
            print(f"Fetch error: {e}")

    def update_icon(self):
        if not self.icon or not self.times:
            return

        idx, _ = get_next_prayer(self.times)
        name = PRAYER_NAMES[idx]
        self.icon.icon = create_icon_image(name)
        self.icon.title = self.get_title()
        self.icon.menu = self.build_menu()

    def check_notifications(self):
        if not self.times:
            return
        now = datetime.now()
        for i, t in enumerate(self.times):
            dt = parse_time(t)
            diff = (now - dt).total_seconds()
            if 0 <= diff < 60 and i not in self.notified:
                self.notified.add(i)
                send_notification(PRAYER_NAMES[i], t)

    def prompt_url(self):
        try:
            import tkinter as tk
            from tkinter import simpledialog

            root = tk.Tk()
            root.withdraw()
            url = simpledialog.askstring(
                "Mosque URL",
                "Enter your Mawaqit mosque URL:",
                initialvalue=self.settings.get("mosque_url", ""),
                parent=root,
            )
            root.destroy()
            if url:
                self.settings["mosque_url"] = url
                save_settings(self.settings)
                self.refresh()
        except Exception as e:
            print(f"Dialog error: {e}")

    def quit(self):
        self.running = False
        if self.icon:
            self.icon.stop()

    def background_loop(self):
        self.refresh()
        last_date = datetime.now().date()
        while self.running:
            time.sleep(30)
            if not self.running:
                break

            today = datetime.now().date()
            if today != last_date:
                last_date = today
                self.notified.clear()
                self.refresh()

            self.check_notifications()
            self.update_icon()

    def run(self):
        img = create_icon_image("Fajr")
        self.icon = pystray.Icon(
            APP_NAME,
            img,
            title="Next Prayer - Loading...",
            menu=self.build_menu(),
        )

        bg = threading.Thread(target=self.background_loop, daemon=True)
        bg.start()

        self.icon.run()


if __name__ == "__main__":
    app = NextPrayerApp()
    app.run()
