-- Al Munadi -- Conky Lua helpers
-- Reads ~/.config/AlMunadi/cache.json (written by al_munadi_linux.py) and exposes
-- conky_* functions used from the conkyrc templates. No network calls.

local HOME = os.getenv("HOME") or ""
local XDG = os.getenv("XDG_CONFIG_HOME")
local CONFIG_DIR = (XDG and #XDG > 0) and (XDG .. "/AlMunadi") or (HOME .. "/.config/AlMunadi")
local CACHE_FILE = CONFIG_DIR .. "/cache.json"
local SETTINGS_FILE = CONFIG_DIR .. "/settings.json"

local PRAYER_KEYS = { "Fajr", "Dhuhr", "Asr", "Maghrib", "Isha" }

local TRANSLATIONS = {
    en = { Fajr = "Fajr", Dhuhr = "Dhuhr", Asr = "Asr", Maghrib = "Maghrib", Isha = "Isha", Jumuah = "Jumuah", Shuruq = "Shuruq", Iqama = "Iqama", Qibla = "Qibla", now = "now", no_data = "No prayer data" },
    nl = { Fajr = "Fadjr", Dhuhr = "Dhuhr", Asr = "Asr", Maghrib = "Maghrib", Isha = "Isha", Jumuah = "Joemoe'a", Shuruq = "Zonsopgang", Iqama = "Iqama", Qibla = "Qibla", now = "nu", no_data = "Geen gebedstijden" },
    ar = { Fajr = "الفجر", Dhuhr = "الظهر", Asr = "العصر", Maghrib = "المغرب", Isha = "العشاء", Jumuah = "الجمعة", Shuruq = "الشروق", Iqama = "الإقامة", Qibla = "القبلة", now = "الآن", no_data = "لا توجد بيانات" },
    fr = { Fajr = "Fajr", Dhuhr = "Dhouhr", Asr = "Asr", Maghrib = "Maghrib", Isha = "Icha", Jumuah = "Joumouâ", Shuruq = "Shourouq", Iqama = "Iqama", Qibla = "Qibla", now = "maintenant", no_data = "Pas de données" },
    tr = { Fajr = "İmsak", Dhuhr = "Öğle", Asr = "İkindi", Maghrib = "Akşam", Isha = "Yatsı", Jumuah = "Cuma", Shuruq = "Güneş", Iqama = "İkamet", Qibla = "Kıble", now = "şimdi", no_data = "Veri yok" },
}

-- ---- Minimal JSON parser (handles cache.json + settings.json schema) -------
-- Not a general-purpose parser. Supports objects, arrays, strings, numbers,
-- booleans, null. Sufficient for the small, well-known files we read.
local json = {}

local function skip_ws(s, i)
    while i <= #s do
        local c = s:sub(i, i)
        if c ~= " " and c ~= "\t" and c ~= "\n" and c ~= "\r" then return i end
        i = i + 1
    end
    return i
end

local parse_value

local function parse_string(s, i)
    if s:sub(i, i) ~= '"' then return nil, i end
    i = i + 1
    local out = {}
    while i <= #s do
        local c = s:sub(i, i)
        if c == '"' then return table.concat(out), i + 1 end
        if c == "\\" then
            local nxt = s:sub(i + 1, i + 1)
            if nxt == "n" then out[#out + 1] = "\n"
            elseif nxt == "t" then out[#out + 1] = "\t"
            elseif nxt == "r" then out[#out + 1] = "\r"
            elseif nxt == '"' then out[#out + 1] = '"'
            elseif nxt == "\\" then out[#out + 1] = "\\"
            elseif nxt == "/" then out[#out + 1] = "/"
            elseif nxt == "u" then
                local hex = s:sub(i + 2, i + 5)
                local cp = tonumber(hex, 16) or 0
                if cp < 0x80 then
                    out[#out + 1] = string.char(cp)
                elseif cp < 0x800 then
                    out[#out + 1] = string.char(0xC0 + math.floor(cp / 0x40), 0x80 + (cp % 0x40))
                else
                    out[#out + 1] = string.char(
                        0xE0 + math.floor(cp / 0x1000),
                        0x80 + (math.floor(cp / 0x40) % 0x40),
                        0x80 + (cp % 0x40)
                    )
                end
                i = i + 4
            else
                out[#out + 1] = nxt
            end
            i = i + 2
        else
            out[#out + 1] = c
            i = i + 1
        end
    end
    return nil, i
end

local function parse_number(s, i)
    local start = i
    if s:sub(i, i) == "-" then i = i + 1 end
    while i <= #s do
        local c = s:sub(i, i)
        if c:match("[0-9eE%+%-%.]") then i = i + 1 else break end
    end
    return tonumber(s:sub(start, i - 1)), i
end

local function parse_array(s, i)
    i = i + 1
    local arr = {}
    i = skip_ws(s, i)
    if s:sub(i, i) == "]" then return arr, i + 1 end
    while i <= #s do
        local v
        v, i = parse_value(s, i)
        arr[#arr + 1] = v
        i = skip_ws(s, i)
        local c = s:sub(i, i)
        if c == "]" then return arr, i + 1 end
        if c == "," then i = skip_ws(s, i + 1) else return arr, i end
    end
    return arr, i
end

local function parse_object(s, i)
    i = i + 1
    local obj = {}
    i = skip_ws(s, i)
    if s:sub(i, i) == "}" then return obj, i + 1 end
    while i <= #s do
        i = skip_ws(s, i)
        local key
        key, i = parse_string(s, i)
        i = skip_ws(s, i)
        if s:sub(i, i) == ":" then i = skip_ws(s, i + 1) end
        local v
        v, i = parse_value(s, i)
        if key then obj[key] = v end
        i = skip_ws(s, i)
        local c = s:sub(i, i)
        if c == "}" then return obj, i + 1 end
        if c == "," then i = i + 1 else return obj, i end
    end
    return obj, i
end

parse_value = function(s, i)
    i = skip_ws(s, i)
    local c = s:sub(i, i)
    if c == '"' then return parse_string(s, i) end
    if c == "{" then return parse_object(s, i) end
    if c == "[" then return parse_array(s, i) end
    if c == "t" then return true, i + 4 end
    if c == "f" then return false, i + 5 end
    if c == "n" then return nil, i + 4 end
    return parse_number(s, i)
end

function json.decode(s)
    if not s or #s == 0 then return nil end
    local ok, v = pcall(function() return (parse_value(s, 1)) end)
    if not ok then return nil end
    return v
end

-- ---- File loading with mtime cache ----------------------------------------

local function file_mtime(path)
    local f = io.popen('stat -c %Y "' .. path .. '" 2>/dev/null')
    if not f then return 0 end
    local s = f:read("*l")
    f:close()
    return tonumber(s) or 0
end

local function read_file(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local s = f:read("*a")
    f:close()
    return s
end

local cache_data = nil
local cache_mtime = 0
local settings_data = nil
local settings_mtime = 0

local function load_cache()
    local mt = file_mtime(CACHE_FILE)
    if mt > cache_mtime or cache_data == nil then
        local s = read_file(CACHE_FILE)
        cache_data = s and json.decode(s) or nil
        cache_mtime = mt
    end
    return cache_data
end

local function load_settings()
    local mt = file_mtime(SETTINGS_FILE)
    if mt > settings_mtime or settings_data == nil then
        local s = read_file(SETTINGS_FILE)
        settings_data = s and json.decode(s) or {}
        settings_mtime = mt
    end
    return settings_data
end

local function language()
    local s = load_settings()
    local lang = s and s.language or "en"
    if not TRANSLATIONS[lang] then lang = "en" end
    return lang
end

local function t(key)
    local tr = TRANSLATIONS[language()] or TRANSLATIONS.en
    return tr[key] or key
end

-- ---- Prayer-time logic (mirrors core.al_munadi_core) ----------------------

local function to_minutes(time_str)
    if not time_str or #time_str < 4 then return nil end
    local h, m = time_str:match("^(%d+):(%d+)")
    if not h then return nil end
    return tonumber(h) * 60 + tonumber(m)
end

local function from_minutes(total)
    total = total % 1440
    if total < 0 then total = total + 1440 end
    return string.format("%02d:%02d", math.floor(total / 60), total % 60)
end

local function apply_offset(time_str, off)
    off = off or 0
    if off == 0 then return time_str end
    local m = to_minutes(time_str)
    if not m then return time_str end
    return from_minutes(m + off)
end

local function adjusted_times()
    local c = load_cache()
    if not c or not c.times then return nil, nil end
    local times = {}
    local offsets = (load_settings() or {}).prayer_offsets or {}
    -- Jumuah swap on Fridays (Linux locale weekday: Sunday=1..Saturday=7 in os.date "%w" -> "5" = Friday)
    local is_friday = os.date("*t").wday == 6
    local display_names = {}
    for i, time_str in ipairs(c.times) do
        local key = PRAYER_KEYS[i]
        local off = tonumber(offsets[key] or 0) or 0
        local effective = time_str
        local name = t(key)
        if i == 2 and is_friday and c.jumua and #c.jumua > 0 then
            effective = c.jumua
            name = t("Jumuah")
        end
        times[i] = apply_offset(effective, off)
        display_names[i] = name
    end
    return times, display_names
end

-- Returns list of {idx, dt} where dt is os.time() of the prayer.
local function prayer_events()
    local times = adjusted_times()
    if not times then return {} end
    local now = os.time()
    local today = os.date("*t", now)
    local events = {}
    local prev_abs = nil
    local day_offset = 0
    local minute_values = {}
    for i, ts in ipairs(times) do minute_values[i] = to_minutes(ts) end
    if #minute_values >= 2 and minute_values[1] > minute_values[2] then
        day_offset = -1
    end
    for i, mv in ipairs(minute_values) do
        if i > 1 then
            if day_offset < 0 then day_offset = 0 end
            while prev_abs and (mv + day_offset * 1440) <= prev_abs do
                day_offset = day_offset + 1
            end
        end
        prev_abs = mv + day_offset * 1440
        local dt = os.time({
            year = today.year, month = today.month, day = today.day + day_offset,
            hour = math.floor(mv / 60), min = mv % 60, sec = 0,
        })
        events[#events + 1] = { idx = i, dt = dt }
    end
    return events
end

local function next_prayer()
    local events = prayer_events()
    if #events == 0 then return nil end
    local now = os.time()
    for _, ev in ipairs(events) do
        if ev.dt > now then return ev end
    end
    -- wrap to tomorrow's first
    return { idx = events[1].idx, dt = events[1].dt + 86400 }
end

local function format_countdown(secs)
    if secs <= 0 then return t("now") end
    local mins = math.floor(secs / 60)
    local h = math.floor(mins / 60)
    local m = mins % 60
    local fmt = (load_settings() or {}).countdown_format or "compact"
    if h > 0 then
        if fmt == "full" then return string.format("-%dh %02dm", h, m) end
        return string.format("-%dh%02dm", h, m)
    end
    return string.format("-%dm", m)
end

-- ---- conky_* exported functions -------------------------------------------

function conky_mosque_name()
    local c = load_cache()
    return (c and c.name) or t("no_data")
end

function conky_next_name()
    local ev = next_prayer()
    if not ev then return "" end
    local _, names = adjusted_times()
    return (names and names[ev.idx]) or t(PRAYER_KEYS[ev.idx])
end

function conky_next_time()
    local ev = next_prayer()
    if not ev then return "--:--" end
    local times = adjusted_times()
    return (times and times[ev.idx]) or "--:--"
end

function conky_countdown()
    local ev = next_prayer()
    if not ev then return "" end
    return format_countdown(ev.dt - os.time())
end

function conky_prayer_name(idx)
    local i = tonumber(idx)
    local _, names = adjusted_times()
    return (names and names[i]) or (PRAYER_KEYS[i] or "")
end

function conky_prayer_time(idx)
    local i = tonumber(idx)
    local times = adjusted_times()
    return (times and times[i]) or "--:--"
end

function conky_iqama(idx)
    local i = tonumber(idx)
    local c = load_cache()
    if not c or not c.iqama_enabled or not c.iqama then return "" end
    local v = c.iqama[i]
    if not v then return "" end
    local s = tostring(v):gsub("^%s+", ""):gsub("%s+$", "")
    if s == "" or s == "0" or s == "+0" then return "" end
    if s:find(":") then return s end
    local stripped = s:gsub("^%+", "")
    local off = tonumber(stripped)
    if not off or off <= 0 then return "" end
    local base = (adjusted_times() or {})[i]
    local m = base and to_minutes(base) or nil
    if not m then return "" end
    return from_minutes(m + off)
end

function conky_is_next(idx)
    local ev = next_prayer()
    return (ev and ev.idx == tonumber(idx)) and "1" or "0"
end

function conky_shuruq()
    local c = load_cache()
    return (c and c.shuruq) or ""
end

function conky_hijri()
    local c = load_cache()
    return (c and c.hijri_date) or ""
end

function conky_qibla()
    local c = load_cache()
    if not c or not c.qibla_direction then return "" end
    local deg = tonumber(tostring(c.qibla_direction):match("(%-?%d+%.?%d*)"))
    if not deg then return tostring(c.qibla_direction) end
    local arrows = { "↑", "↗", "→", "↘", "↓", "↙", "←", "↖" }
    local octant = math.floor(((deg + 22.5) % 360) / 45) + 1
    return string.format("%s %d°", arrows[octant], math.floor(deg + 0.5))
end

function conky_label(key)
    return t(tostring(key))
end
