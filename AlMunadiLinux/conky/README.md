# Al Munadi -- Conky desktop widget

Ambient desktop overlay showing the next prayer (and optionally all five, iqama, Hijri date and Qibla direction). Works on **any Linux desktop environment** (KDE Plasma, XFCE, Cinnamon, MATE, LXQt, Budgie). GNOME users should use the [GNOME Shell extension](../../) from this repo instead.

The widget reads the cache that `al_munadi_linux.py` already writes to `~/.config/AlMunadi/cache.json`. **The main app must be running** -- it stays the sole Mawaqit consumer; the widget only reads.

## Install

1. Install Conky (the embedded Lua JSON parser means no `lua-dkjson` dependency):

   **Debian / Ubuntu / Mint:** `sudo apt install conky-all`  
   **Fedora:** `sudo dnf install conky`  
   **Arch:** `sudo pacman -S conky`  
   **openSUSE:** `sudo zypper install conky`

2. Copy this folder to your config dir:

   ```bash
   mkdir -p ~/.config/AlMunadi/conky
   cp AlMunadiLinux/conky/almunadi.lua ~/.config/AlMunadi/conky/
   cp AlMunadiLinux/conky/almunadi-*.conkyrc ~/.config/AlMunadi/conky/
   ```

3. Make sure the Al Munadi tray app is running so the cache exists.

4. Pick a size and launch:

   ```bash
   conky -c ~/.config/AlMunadi/conky/almunadi-small.conkyrc &
   # or
   conky -c ~/.config/AlMunadi/conky/almunadi-medium.conkyrc &
   # or
   conky -c ~/.config/AlMunadi/conky/almunadi-large.conkyrc &
   ```

## Sizes

| Size | Shows | Footprint |
|---|---|---|
| **Small** | Next prayer name + time + countdown | 220 × 90 |
| **Medium** | Mosque name, countdown, all 5 prayers (next highlighted) | 280 × 280 |
| **Large** | Medium + iqama times + Shuruq + Qibla arrow + Hijri date | 340 × 440 |

Edit `alignment`, `gap_x`, `gap_y` at the top of the `.conkyrc` to reposition. Common values: `top_right`, `top_left`, `bottom_right`, `bottom_left`, `middle_right`, etc.

## Auto-start at login

Add this to your DE's autostart (KDE: System Settings → Autostart, XFCE: Session and Startup, etc.) **after** the Al Munadi tray app:

```
conky -c /home/YOU/.config/AlMunadi/conky/almunadi-medium.conkyrc
```

Or drop a `.desktop` file in `~/.config/autostart/`:

```ini
[Desktop Entry]
Type=Application
Name=Al Munadi (Conky widget)
Exec=conky -c %h/.config/AlMunadi/conky/almunadi-medium.conkyrc
X-GNOME-Autostart-Delay=5
```

## How it works

- `almunadi.lua` reads `~/.config/AlMunadi/cache.json` (rewritten by `al_munadi_linux.py` after every successful Mawaqit fetch) and `~/.config/AlMunadi/settings.json` (for language, prayer offsets, countdown format).
- It mirrors the same next-prayer / Jumuah-swap / offset / iqama logic as the main app (`core/al_munadi_core.py`), so the displayed values match the tray icon.
- Conky re-evaluates the `${lua ...}` calls every `update_interval` seconds (1s by default for a live countdown). File mtime is checked each tick so mosque changes from the main app propagate immediately.
- No network calls. No Mawaqit fetches. No extra config.

## Customizing

Each `.conkyrc` is plain text and self-contained. Tweak fonts, colors, alignment, transparency (`own_window_argb_value` 0–255) to taste. Available Lua helpers exposed for your own layouts:

| Helper | Returns |
|---|---|
| `${lua conky_mosque_name}` | Mosque name |
| `${lua conky_next_name}` | Localized name of next prayer |
| `${lua conky_next_time}` | `HH:MM` of next prayer |
| `${lua conky_countdown}` | e.g. `-1h23m`, or `now` |
| `${lua conky_prayer_name N}` | Name for prayer N (1..5) |
| `${lua conky_prayer_time N}` | Time for prayer N |
| `${lua conky_iqama N}` | Iqama time for prayer N (empty if disabled) |
| `${lua conky_is_next N}` | `"1"` if N is the next prayer, else `"0"` |
| `${lua conky_shuruq}` | Sunrise time |
| `${lua conky_hijri}` | Hijri date string |
| `${lua conky_qibla}` | Qibla arrow + degrees, e.g. `↗ 117°` |
| `${lua conky_label KEY}` | Localized label (`Shuruq`, `Iqama`, `Qibla`) |

## Troubleshooting

**Conky shows `--:--` or empty fields.**  Run the main app at least once to populate `~/.config/AlMunadi/cache.json`. Check `cat ~/.config/AlMunadi/cache.json` to confirm.

**Countdown doesn't tick.**  Verify `update_interval = 1.0` in the `.conkyrc`. Some DE compositors throttle background windows -- try `own_window_type = 'normal'` instead of `'desktop'`.

**Widget is invisible / behind wallpaper.**  Compositor differences. Try changing `own_window_hints` -- remove `below` to bring it forward, or switch `own_window_type` between `'desktop'`, `'normal'`, `'override'`.

**Wrong language.**  The widget reads `language` from `~/.config/AlMunadi/settings.json`. Change it in the tray app's settings; the widget picks it up within a second.
