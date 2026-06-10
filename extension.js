import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Soup from 'gi://Soup?version=3.0';
import St from 'gi://St';
import Clutter from 'gi://Clutter';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as MessageTray from 'resource:///org/gnome/shell/ui/messageTray.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const _VERSION = '1.0.8';
const _TAG_PREFIX = 'v';
const _RELEASES_URL = 'https://api.github.com/repos/Chanclatoen/almunadi/releases';
const _REPO_RELEASES_PAGE = 'https://github.com/Chanclatoen/almunadi/releases';

const PRAYER_NAMES = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
const PRAYER_ICONS = [
    'daytime-sunrise-symbolic',
    'weather-clear-symbolic',
    'weather-few-clouds-symbolic',
    'daytime-sunset-symbolic',
    'weather-clear-night-symbolic',
];
const SHURUQ_ICON = 'daytime-sunrise-symbolic';
const API_BASE = 'https://mawaqit.net/api/2.0/mosque';
const KAABA_LATITUDE = 21.422487;
const KAABA_LONGITUDE = 39.826206;
const HIJRI_MONTHS = [
    'Muharram', 'Safar', 'Rabi al-awwal', 'Rabi al-thani',
    'Jumada al-awwal', 'Jumada al-thani', 'Rajab', 'Shaban',
    'Ramadan', 'Shawwal', 'Dhu al-Qadah', 'Dhu al-Hijjah',
];

const TRANSLATIONS = {
    en: {
        prayers: ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'],
        shuruq: 'Shuruq',
        jumuah: 'Jumuah',
        jumuah2: 'Jumuah 2',
        configure: 'Configure mosque',
        refresh: 'Refresh',
        loading: 'Loading…',
        noMosque: 'No mosque set',
        parseError: 'Parse error',
        error: 'Error',
        notifTitle: (name, time) => `${name} - ${time}`,
        notifBody: (name) => `It's time for ${name} prayer`,
        couldNotReach: 'Could not reach mawaqit.net',
        couldNotParse: 'Could not parse prayer data',
        invalidUrl: 'Invalid URL',
        usingCached: (err) => `Using cached data. ${err}`,
        clickRetry: (err) => `${err} — click to retry`,
        mosques: 'Mosques',
        saveCurrent: 'Save current mosque',
        updateAvailable: 'Update available',
        hijriDate: 'Hijri date',
        qibla: 'Qibla',
        sinceLastPrayer: (name) => `Since ${name}`,
        dnd_bypass: 'Break through Do Not Disturb',
    },
    nl: {
        prayers: ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'],
        shuruq: 'Shuruq',
        jumuah: 'Jumuah',
        jumuah2: 'Jumuah 2',
        configure: 'Moskee instellen',
        refresh: 'Vernieuwen',
        loading: 'Laden...',
        noMosque: 'Geen moskee ingesteld',
        parseError: 'Parsefout',
        error: 'Fout',
        notifTitle: (name, time) => `${name} - ${time}`,
        notifBody: (name) => `Het is tijd voor het ${name}-gebed`,
        couldNotReach: 'Kon mawaqit.net niet bereiken',
        couldNotParse: 'Kon gebedsgegevens niet lezen',
        invalidUrl: 'Ongeldige URL',
        usingCached: (err) => `Gegevens uit cache. ${err}`,
        clickRetry: (err) => `${err} - klik om opnieuw te proberen`,
        mosques: 'Moskeeen',
        saveCurrent: 'Huidige moskee opslaan',
        updateAvailable: 'Update beschikbaar',
        hijriDate: 'Hijri-datum',
        qibla: 'Qibla',
        sinceLastPrayer: (name) => `Sinds ${name}`,
        dnd_bypass: 'Niet storen doorbreken',
    },
    ar: {
        prayers: ['فجر', 'ظهر', 'عصر', 'مغرب', 'عشاء'],
        shuruq: 'شروق',
        jumuah: 'جمعة',
        jumuah2: 'جمعة 2',
        configure: 'إعداد المسجد',
        refresh: 'تحديث',
        loading: 'جارٍ التحميل…',
        noMosque: 'لم يتم تعيين مسجد',
        parseError: 'خطأ في التحليل',
        error: 'خطأ',
        notifTitle: (name, time) => `${name} - ${time}`,
        notifBody: (name) => `حان وقت صلاة ${name}`,
        couldNotReach: 'تعذر الاتصال بمواقيت',
        couldNotParse: 'تعذر تحليل بيانات الصلاة',
        invalidUrl: 'رابط غير صالح',
        usingCached: (err) => `بيانات مخزنة. ${err}`,
        clickRetry: (err) => `${err} — اضغط للمحاولة`,
        mosques: 'المساجد',
        saveCurrent: 'حفظ المسجد الحالي',
        updateAvailable: 'تحديث متاح',
        dnd_bypass: 'تجاوز وضع عدم الإزعاج',
        hijriDate: 'التاريخ الهجري',
        qibla: 'القبلة',
        sinceLastPrayer: (name) => `منذ ${name}`,
    },
    fr: {
        prayers: ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'],
        shuruq: 'Shuruq',
        jumuah: "Joumou'a",
        jumuah2: "Joumou'a 2",
        configure: 'Configurer la mosquée',
        refresh: 'Actualiser',
        loading: 'Chargement…',
        noMosque: 'Aucune mosquée configurée',
        parseError: 'Erreur d’analyse',
        error: 'Erreur',
        notifTitle: (name, time) => `${name} - ${time}`,
        notifBody: (name) => `C'est l'heure de la prière de ${name}`,
        couldNotReach: 'Impossible de joindre mawaqit.net',
        couldNotParse: 'Impossible d’analyser les données',
        invalidUrl: 'URL invalide',
        usingCached: (err) => `Données en cache. ${err}`,
        clickRetry: (err) => `${err} — cliquez pour réessayer`,
        mosques: 'Mosquées',
        saveCurrent: 'Sauvegarder la mosquée actuelle',
        updateAvailable: 'Mise à jour disponible',
        dnd_bypass: 'Passer le mode Ne pas deranger',
        hijriDate: 'Date hégirienne',
        qibla: 'Qibla',
        sinceLastPrayer: (name) => `Depuis ${name}`,
    },
    tr: {
        prayers: ['Sabah', 'Öğle', 'İkindi', 'Akşam', 'Yatsı'],
        shuruq: 'Güneş',
        jumuah: 'Cuma',
        jumuah2: 'Cuma 2',
        configure: 'Cami yapılandır',
        refresh: 'Yenile',
        loading: 'Yükleniyor…',
        noMosque: 'Cami ayarlanmadı',
        parseError: 'Ayrıştırma hatası',
        error: 'Hata',
        notifTitle: (name, time) => `${name} - ${time}`,
        notifBody: (name) => `${name} namazı vakti geldi`,
        couldNotReach: 'mawaqit.net\'e ulaşılamıyor',
        couldNotParse: 'Namaz verileri ayrıştırılamadı',
        invalidUrl: 'Geçersiz URL',
        usingCached: (err) => `Önbellekten yüklendi. ${err}`,
        clickRetry: (err) => `${err} — tekrar denemek için tıklayın`,
        mosques: 'Camiler',
        saveCurrent: 'Mevcut camiyi kaydet',
        updateAvailable: 'Güncelleme mevcut',
        dnd_bypass: 'Rahatsiz Etmeyin modunu as',
        hijriDate: 'Hicri tarih',
        qibla: 'Kıble',
        sinceLastPrayer: (name) => `${name}'dan beri`,
    },
};

export default class NextPrayerExtension extends Extension {
    _indicator = null;
    _settings = null;
    _updateTimer = null;
    _fetchTimer = null;
    _session = null;
    _times = null;
    _shuruq = null;
    _mosqueName = null;
    _iqama = null;
    _iqamaEnabled = false;
    _jumua = null;
    _jumua2 = null;
    _hijriDate = null;
    _qiblaDirection = null;
    _settingsChangedId = null;
    _notificationTimers = [];
    _notificationsChangedId = null;
    _languageChangedId = null;
    _adhanEnabledChangedId = null;
    _adhanPathChangedId = null;
    _countdownFormatChangedId = null;
    _displayModeChangedId = null;
    _prayerNotificationSettingsChangedId = null;
    _prayerOffsetsChangedId = null;
    _savedMosquesChangedId = null;
    _lastError = null;
    _isCached = false;
    _gstPipeline = null;
    _gstAvailable = false;
    _gstModule = null;
    _updateInfo = null;
    _updateCheckTimer = null;

    enable() {
        this._settings = this.getSettings();
        this._session = new Soup.Session();

        // Initialize GStreamer if available (async, non-blocking)
        this._initGstreamer();

        this._indicator = new PanelMenu.Button(0.0, this.metadata.name, false);

        const box = new St.BoxLayout({style_class: 'next-prayer-box'});

        this._icon = new St.Icon({
            icon_name: 'preferences-system-time-symbolic',
            style_class: 'system-status-icon next-prayer-icon',
        });
        box.add_child(this._icon);

        this._prayerLabel = new St.Label({
            text: '…',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'next-prayer-name',
        });
        box.add_child(this._prayerLabel);

        this._timeLabel = new St.Label({
            text: '',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'next-prayer-time',
        });
        box.add_child(this._timeLabel);

        this._countdownLabel = new St.Label({
            text: '',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'next-prayer-countdown',
        });
        box.add_child(this._countdownLabel);

        this._indicator.add_child(box);

        this._buildMenu();

        Main.panel.addToStatusArea(this.uuid, this._indicator);

        this._settingsChangedId = this._settings.connect('changed::mosque-url', () => {
            this._fetchTimes();
        });
        this._notificationsChangedId = this._settings.connect('changed::notifications-enabled', () => {
            if (this._settings.get_boolean('notifications-enabled'))
                this._scheduleNotifications();
            else
                this._clearNotificationTimers();
        });
        this._languageChangedId = this._settings.connect('changed::language', () => {
            this._rebuildMenu();
            this._updateLabel();
        });
        this._adhanEnabledChangedId = this._settings.connect('changed::adhan-enabled', () => {
            this._scheduleNotifications();
        });
        this._adhanPathChangedId = this._settings.connect('changed::adhan-path', () => {
            // No action needed until next prayer time
        });
        this._countdownFormatChangedId = this._settings.connect('changed::countdown-format', () => {
            this._updateLabel();
        });
        this._displayModeChangedId = this._settings.connect('changed::display-mode', () => {
            this._updateLabel();
        });
        this._prayerNotificationSettingsChangedId = this._settings.connect('changed::prayer-notification-settings', () => {
            this._scheduleNotifications();
        });
        this._prayerOffsetsChangedId = this._settings.connect('changed::prayer-offsets', () => {
            this._updateLabel();
            this._scheduleNotifications();
        });
        this._savedMosquesChangedId = this._settings.connect('changed::saved-mosques', () => {
            this._updateMosquesSubmenu();
        });

        this._loadCache();
        this._fetchTimes();
        this._startUpdateTimer();
        this._checkForUpdate();
        this._updateCheckTimer = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT, 86400, () => {
                this._checkForUpdate();
                return GLib.SOURCE_CONTINUE;
            });
    }

    disable() {
        if (this._updateTimer) {
            GLib.source_remove(this._updateTimer);
            this._updateTimer = null;
        }
        if (this._fetchTimer) {
            GLib.source_remove(this._fetchTimer);
            this._fetchTimer = null;
        }
        if (this._settingsChangedId) {
            this._settings.disconnect(this._settingsChangedId);
            this._settingsChangedId = null;
        }
        if (this._notificationsChangedId) {
            this._settings.disconnect(this._notificationsChangedId);
            this._notificationsChangedId = null;
        }
        if (this._languageChangedId) {
            this._settings.disconnect(this._languageChangedId);
            this._languageChangedId = null;
        }
        if (this._adhanEnabledChangedId) {
            this._settings.disconnect(this._adhanEnabledChangedId);
            this._adhanEnabledChangedId = null;
        }
        if (this._adhanPathChangedId) {
            this._settings.disconnect(this._adhanPathChangedId);
            this._adhanPathChangedId = null;
        }
        if (this._countdownFormatChangedId) {
            this._settings.disconnect(this._countdownFormatChangedId);
            this._countdownFormatChangedId = null;
        }
        if (this._displayModeChangedId) {
            this._settings.disconnect(this._displayModeChangedId);
            this._displayModeChangedId = null;
        }
        if (this._prayerNotificationSettingsChangedId) {
            this._settings.disconnect(this._prayerNotificationSettingsChangedId);
            this._prayerNotificationSettingsChangedId = null;
        }
        if (this._prayerOffsetsChangedId) {
            this._settings.disconnect(this._prayerOffsetsChangedId);
            this._prayerOffsetsChangedId = null;
        }
        if (this._savedMosquesChangedId) {
            this._settings.disconnect(this._savedMosquesChangedId);
            this._savedMosquesChangedId = null;
        }
        if (this._updateCheckTimer) {
            GLib.source_remove(this._updateCheckTimer);
            this._updateCheckTimer = null;
        }
        this._updateInfo = null;
        this._clearNotificationTimers();
        this._stopAdhan();
        this._indicator?.destroy();
        this._indicator = null;
        this._session = null;
        this._settings = null;
        this._times = null;
    }

    async _initGstreamer() {
        try {
            const gstModule = (await import('gi://Gst')).default;
            gstModule.init(null);
            this._gstModule = gstModule;
            this._gstAvailable = true;
        } catch {
            this._gstModule = null;
            this._gstAvailable = false;
        }
    }

    _t(key) {
        const lang = this._settings.get_string('language') || 'en';
        const table = TRANSLATIONS[lang] || TRANSLATIONS.en;
        return table[key] !== undefined ? table[key] : (TRANSLATIONS.en[key] || key);
    }

    _rebuildMenu() {
        this._indicator.menu.removeAll();
        this._buildMenu();
        this._updateMenu();
    }

    _buildMenu() {
        this._mosqueLabel = new PopupMenu.PopupMenuItem('', {reactive: false});
        this._mosqueLabel.label.style_class = 'next-prayer-mosque-name';
        this._indicator.menu.addMenuItem(this._mosqueLabel);

        this._errorItem = new PopupMenu.PopupImageMenuItem('', 'dialog-warning-symbolic');
        this._errorItem.connect('activate', () => this._fetchTimes());
        this._errorItem.visible = false;
        this._indicator.menu.addMenuItem(this._errorItem);

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this._menuItems = {};
        for (let i = 0; i < PRAYER_NAMES.length; i++) {
            const item = new PopupMenu.PopupImageMenuItem(
                this._t('prayers')[i], PRAYER_ICONS[i]);
            item.setSensitive(false);

            const timeLabel = new St.Label({
                text: '--:--',
                y_align: Clutter.ActorAlign.CENTER,
                style_class: 'next-prayer-menu-time',
            });
            item.add_child(timeLabel);

            const iqamaLabel = new St.Label({
                text: '',
                y_align: Clutter.ActorAlign.CENTER,
                style_class: 'next-prayer-menu-iqama',
            });
            item.add_child(iqamaLabel);

            this._indicator.menu.addMenuItem(item);
            this._menuItems[PRAYER_NAMES[i]] = {item, timeLabel, iqamaLabel};
        }

        this._jumuaSeparator = new PopupMenu.PopupSeparatorMenuItem();
        this._jumuaSeparator.visible = false;
        this._indicator.menu.addMenuItem(this._jumuaSeparator);

        this._jumua2Item = new PopupMenu.PopupImageMenuItem(this._t('jumuah2'), 'weather-clear-symbolic');
        this._jumua2Item.setSensitive(false);
        this._jumua2TimeLabel = new St.Label({
            text: '',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'next-prayer-menu-time',
        });
        this._jumua2Item.add_child(this._jumua2TimeLabel);
        this._jumua2Item.visible = false;
        this._indicator.menu.addMenuItem(this._jumua2Item);

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this._shuruqItem = new PopupMenu.PopupImageMenuItem(this._t('shuruq'), SHURUQ_ICON);
        this._shuruqItem.setSensitive(false);
        this._shuruqTimeLabel = new St.Label({
            text: '--:--',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'next-prayer-menu-time',
        });
        this._shuruqItem.add_child(this._shuruqTimeLabel);
        this._indicator.menu.addMenuItem(this._shuruqItem);

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this._hijriItem = new PopupMenu.PopupImageMenuItem(this._t('hijriDate'), 'x-office-calendar-symbolic');
        this._hijriItem.setSensitive(false);
        this._hijriItem.visible = false;
        this._indicator.menu.addMenuItem(this._hijriItem);

        this._qiblaItem = new PopupMenu.PopupImageMenuItem(this._t('qibla'), 'go-next-symbolic');
        this._qiblaItem.setSensitive(false);
        this._qiblaItem.visible = false;
        this._indicator.menu.addMenuItem(this._qiblaItem);

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Mosques submenu
        this._mosquesSubmenu = new PopupMenu.PopupSubMenuMenuItem(this._t('mosques'));
        this._indicator.menu.addMenuItem(this._mosquesSubmenu);
        this._updateMosquesSubmenu();

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const settingsItem = new PopupMenu.PopupImageMenuItem(
            this._t('configure'), 'emblem-system-symbolic');
        settingsItem.connect('activate', () => this.openPreferences());
        this._indicator.menu.addMenuItem(settingsItem);

        const refreshItem = new PopupMenu.PopupImageMenuItem(
            this._t('refresh'), 'view-refresh-symbolic');
        refreshItem.connect('activate', () => this._fetchTimes());
        this._indicator.menu.addMenuItem(refreshItem);

        if (this._updateInfo) {
            this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
            const updateItem = new PopupMenu.PopupImageMenuItem(
                `${this._t('updateAvailable')} (v${this._updateInfo.version})`,
                'software-update-available-symbolic');
            updateItem.connect('activate', () => {
                Gio.AppInfo.launch_default_for_uri(this._updateInfo.url, null);
            });
            this._indicator.menu.addMenuItem(updateItem);
        }
    }

    _updateMosquesSubmenu() {
        this._mosquesSubmenu.menu.removeAll();

        const savedMosques = this._getSavedMosques();

        for (const mosque of savedMosques) {
            const mosqueItem = new PopupMenu.PopupMenuItem(mosque.name || mosque.url);
            mosqueItem.connect('activate', () => {
                this._settings.set_string('mosque-url', mosque.url);
            });
            this._mosquesSubmenu.menu.addMenuItem(mosqueItem);
        }

        if (savedMosques.length > 0)
            this._mosquesSubmenu.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const saveItem = new PopupMenu.PopupMenuItem(this._t('saveCurrent'));
        saveItem.connect('activate', () => {
            this._saveCurrentMosque();
        });
        this._mosquesSubmenu.menu.addMenuItem(saveItem);
    }

    _getSavedMosques() {
        try {
            return JSON.parse(this._settings.get_string('saved-mosques') || '[]');
        } catch {
            return [];
        }
    }

    _saveCurrentMosque() {
        const url = this._settings.get_string('mosque-url');
        if (!url) return;

        const name = this._mosqueName || url;
        const mosques = this._getSavedMosques();

        // Don't add duplicates
        if (mosques.some(m => m.url === url)) return;

        mosques.push({url, name});
        this._settings.set_string('saved-mosques', JSON.stringify(mosques));
    }

    _startUpdateTimer() {
        if (this._updateTimer)
            GLib.source_remove(this._updateTimer);

        this._updateTimer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 60, () => {
            this._updateLabel();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _checkForUpdate() {
        const message = Soup.Message.new('GET', _RELEASES_URL);
        if (!message) return;

        this._session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (session, result) => {
            try {
                const bytes = session.send_and_read_finish(result);
                if (message.get_status() !== Soup.Status.OK) return;

                const json = new TextDecoder().decode(bytes.get_data());
                const releases = JSON.parse(json);
                if (!Array.isArray(releases)) return;

                for (const release of releases) {
                    const tag = release.tag_name || '';
                    if (!tag.startsWith(_TAG_PREFIX)) continue;

                    const latest = tag.slice(_TAG_PREFIX.length);
                    const currentParts = _VERSION.split('.').map(Number);
                    const latestParts = latest.split('.').map(Number);

                    let newer = false;
                    for (let i = 0; i < Math.max(currentParts.length, latestParts.length); i++) {
                        const c = currentParts[i] || 0;
                        const l = latestParts[i] || 0;
                        if (l > c) { newer = true; break; }
                        if (l < c) break;
                    }

                    if (newer) {
                        this._updateInfo = {
                            version: latest,
                            url: release.html_url || _REPO_RELEASES_PAGE,
                        };
                        this._rebuildMenu();
                    }
                    return; // Only check the first matching release
                }
            } catch {
                // Silently ignore update check errors
            }
        });
    }

    _slugFromUrl(url) {
        if (!url) return null;
        const match = url.match(/mawaqit\.net\/\w+\/(?:w\/)?(.+?)\/?$/);
        return match ? match[1] : null;
    }

    _isFriday() {
        return GLib.DateTime.new_now_local().get_day_of_week() === 5;
    }

    _displayNames() {
        const prayerNames = this._t('prayers');
        const names = [...prayerNames];
        if (this._isFriday() && this._jumua)
            names[1] = this._t('jumuah');
        return names;
    }

    _fromMinutes(total) {
        const normalized = ((total % 1440) + 1440) % 1440;
        const h = Math.floor(normalized / 60);
        const m = normalized % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    }

    _applyOffset(timeStr, offsetMinutes) {
        if (!offsetMinutes) return timeStr;
        return this._fromMinutes(this._toMinutes(timeStr) + offsetMinutes);
    }

    _prayerEvents(displayTimes = this._displayTimes()) {
        if (!displayTimes) return [];
        const minutes = displayTimes.map(time => this._toMinutes(time));
        const events = [];
        let dayOffset = minutes.length > 1 && minutes[0] > minutes[1] ? -1 : 0;
        let previousAbsolute = null;

        for (let i = 0; i < minutes.length; i++) {
            if (i > 0) {
                if (dayOffset < 0)
                    dayOffset = 0;
                while (previousAbsolute !== null && minutes[i] + dayOffset * 1440 <= previousAbsolute)
                    dayOffset++;
            }

            const absoluteMinutes = minutes[i] + dayOffset * 1440;
            previousAbsolute = absoluteMinutes;
            events.push({index: i, time: displayTimes[i], absoluteMinutes});
        }

        return events;
    }

    _findNextPrayerEvent(nowMinutes) {
        const events = this._prayerEvents();
        if (!events.length) return null;
        const next = events.find(event => event.absoluteMinutes > nowMinutes);
        if (next) return next;
        const first = events[0];
        return {...first, absoluteMinutes: first.absoluteMinutes + 1440};
    }

    _getPrayerOffsets() {
        const defaults = {Fajr: 0, Dhuhr: 0, Asr: 0, Maghrib: 0, Isha: 0};
        try {
            const stored = JSON.parse(this._settings.get_string('prayer-offsets') || '{}');
            for (const key of Object.keys(defaults)) {
                if (stored[key] !== undefined) {
                    const val = parseInt(stored[key]) || 0;
                    defaults[key] = Math.max(-60, Math.min(60, val));
                }
            }
        } catch {
            // use defaults
        }
        return defaults;
    }

    _getPrayerNotificationSettings() {
        const keys = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha', 'Jumuah'];
        const settings = {};
        for (const key of keys)
            settings[key] = {enabled: true, reminder_minutes: 0, adhan_enabled: null, dnd_bypass: null};
        try {
            const stored = JSON.parse(this._settings.get_string('prayer-notification-settings') || '{}');
            for (const key of keys) {
                if (stored[key]) {
                    settings[key] = {
                        enabled: stored[key].enabled !== false,
                        reminder_minutes: Math.max(0, parseInt(stored[key].reminder_minutes) || 0),
                        adhan_enabled: stored[key].adhan_enabled ?? null,
                        dnd_bypass: stored[key].dnd_bypass ?? null,
                    };
                }
            }
        } catch {
            // use defaults
        }
        return settings;
    }

    _notificationKeyForIndex(index) {
        if (index === 1 && this._isFriday() && this._jumua)
            return 'Jumuah';
        return PRAYER_NAMES[index];
    }

    _shouldPlayAdhan(prayerSetting) {
        if (prayerSetting?.adhan_enabled === true) return true;
        if (prayerSetting?.adhan_enabled === false) return false;
        return this._settings.get_boolean('adhan-enabled');
    }

    _shouldBypassDnd(prayerSetting) {
        if (prayerSetting?.dnd_bypass === true) return true;
        if (prayerSetting?.dnd_bypass === false) return false;
        return this._settings.get_boolean('dnd-bypass');
    }

    _formatQiblaDirection(latitude, longitude) {
        const lat = Number(latitude);
        const lon = Number(longitude);
        if (!Number.isFinite(lat) || !Number.isFinite(lon))
            return null;
        const lat1 = lat * Math.PI / 180;
        const lat2 = KAABA_LATITUDE * Math.PI / 180;
        const deltaLon = (KAABA_LONGITUDE - lon) * Math.PI / 180;
        const y = Math.sin(deltaLon);
        const x = Math.cos(lat1) * Math.tan(lat2) - Math.sin(lat1) * Math.cos(deltaLon);
        return `${Math.round((Math.atan2(y, x) * 180 / Math.PI + 360) % 360)}°`;
    }

    _gregorianToJdn(year, month, day) {
        const a = Math.floor((14 - month) / 12);
        const y = year + 4800 - a;
        const m = month + 12 * a - 3;
        return day + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4)
            - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
    }

    _islamicToJdn(year, month, day) {
        return day + Math.ceil(29.5 * (month - 1)) + (year - 1) * 354
            + Math.floor((3 + 11 * year) / 30) + 1948439 - 1;
    }

    _formatHijriDate(adjustment = 0) {
        const now = GLib.DateTime.new_now_local();
        const jdn = this._gregorianToJdn(now.get_year(), now.get_month(), now.get_day_of_month())
            + (parseInt(adjustment) || 0);
        const year = Math.floor((30 * (jdn - 1948439) + 10646) / 10631);
        const month = Math.min(12, Math.ceil((jdn - (29 + this._islamicToJdn(year, 1, 1))) / 29.5) + 1);
        const day = jdn - this._islamicToJdn(year, month, 1) + 1;
        return `${day} ${HIJRI_MONTHS[month - 1]} ${year} AH`;
    }

    _displayTimes() {
        if (!this._times) return null;
        const times = [...this._times];
        if (this._isFriday() && this._jumua)
            times[1] = this._jumua;
        const offsets = this._getPrayerOffsets();
        return times.map((time, i) => this._applyOffset(time, offsets[PRAYER_NAMES[i]] || 0));
    }

    _resolveIqama(prayerTime, iqamaValue) {
        if (!iqamaValue) return null;
        const val = String(iqamaValue).trim();
        if (val === '0' || val === '+0' || val === '') return null;
        if (val.includes(':')) return val;
        const offset = parseInt(val.replace('+', ''));
        if (isNaN(offset) || offset <= 0) return null;
        const total = this._toMinutes(prayerTime) + offset;
        const h = Math.floor(total / 60) % 24;
        const m = total % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    }

    _fetchTimes() {
        const url = this._settings.get_string('mosque-url');
        if (!url) {
            this._prayerLabel.set_text(this._t('noMosque'));
            this._timeLabel.set_text('');
            this._countdownLabel.set_text('');
            return;
        }

        const slug = this._slugFromUrl(url);
        if (slug) {
            this._fetchTimesApi(slug, () => {
                this._fetchTimesHtml(url);
            });
        } else {
            this._fetchTimesHtml(url);
        }
    }

    _fetchTimesApi(slug, fallback) {
        const apiUrl = `${API_BASE}/search?word=${slug}`;
        const message = Soup.Message.new('GET', apiUrl);
        if (!message) {
            fallback();
            return;
        }
        message.get_request_headers().append('Accept', 'application/json');

        this._prayerLabel.set_text(this._t('loading'));
        this._timeLabel.set_text('');
        this._countdownLabel.set_text('');

        this._session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (session, result) => {
            try {
                const bytes = session.send_and_read_finish(result);
                if (message.get_status() !== Soup.Status.OK) {
                    fallback();
                    return;
                }

                const json = new TextDecoder().decode(bytes.get_data());
                const results = JSON.parse(json);
                if (!Array.isArray(results) || results.length === 0) {
                    fallback();
                    return;
                }

                const mosque = results[0];
                const apiTimes = mosque.times;
                if (!apiTimes || apiTimes.length < 6) {
                    fallback();
                    return;
                }

                this._times = [apiTimes[0], apiTimes[2], apiTimes[3], apiTimes[4], apiTimes[5]];
                this._shuruq = apiTimes[1] || null;
                this._mosqueName = mosque.name || mosque.label || '';
                this._iqama = mosque.iqama || null;
                this._iqamaEnabled = mosque.iqamaEnabled || false;
                this._jumua = mosque.jumua || null;
                this._jumua2 = mosque.jumua2 || null;
                this._hijriDate = this._formatHijriDate(mosque.hijriAdjustment || 0);
                this._qiblaDirection = this._formatQiblaDirection(mosque.latitude, mosque.longitude);

                this._isCached = false;
                this._lastError = null;
                this._saveCache();
                this._scheduleNotifications();
                this._updateLabel();
                this._updateMenu();
                this._scheduleDailyRefresh();
            } catch (e) {
                logError(e, 'NextPrayer: API fetch error, falling back to HTML');
                fallback();
            }
        });
    }

    _fetchTimesHtml(url) {
        let fetchUrl = url;
        if (!fetchUrl.includes('/w/')) {
            const slug = this._slugFromUrl(fetchUrl);
            if (slug)
                fetchUrl = `https://mawaqit.net/en/w/${slug}`;
        }

        const message = Soup.Message.new('GET', fetchUrl);
        if (!message) {
            this._handleFetchError(this._t('invalidUrl'));
            return;
        }

        this._prayerLabel.set_text(this._t('loading'));
        this._timeLabel.set_text('');
        this._countdownLabel.set_text('');

        this._session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (session, result) => {
            try {
                const bytes = session.send_and_read_finish(result);
                if (message.get_status() !== Soup.Status.OK) {
                    this._handleFetchError(this._t('couldNotReach'));
                    return;
                }

                const html = new TextDecoder().decode(bytes.get_data());
                this._parseConfData(html);
                this._isCached = false;
                this._lastError = null;
                this._saveCache();
                this._scheduleNotifications();
                this._updateLabel();
                this._updateMenu();
                this._scheduleDailyRefresh();
            } catch (e) {
                logError(e, 'NextPrayer: HTML fetch error');
                this._handleFetchError(this._t('couldNotParse'));
            }
        });
    }

    _parseConfData(html) {
        const match = html.match(/confData\s*=\s*(\{.*?\});/s);
        if (!match) {
            this._prayerLabel.set_text(this._t('parseError'));
            return;
        }

        try {
            const data = JSON.parse(match[1]);
            this._times = data.times;
            this._shuruq = data.shuruq || null;
            this._mosqueName = data.name || data.label || '';
            this._iqama = data.iqama || null;
            this._iqamaEnabled = data.iqamaEnabled || false;
            this._jumua = data.jumua || null;
            this._jumua2 = data.jumua2 || null;
            this._hijriDate = this._formatHijriDate(data.hijriAdjustment || 0);
            this._qiblaDirection = this._formatQiblaDirection(data.latitude, data.longitude);
        } catch (e) {
            logError(e, 'NextPrayer: JSON parse error');
            this._prayerLabel.set_text(this._t('parseError'));
        }
    }

    _updateMenu() {
        if (!this._times) return;

        if (this._mosqueName)
            this._mosqueLabel.label.set_text(this._mosqueName);

        if (this._lastError) {
            const msg = this._isCached
                ? this._t('usingCached')(this._lastError)
                : this._t('clickRetry')(this._lastError);
            this._errorItem.label.set_text(msg);
            this._errorItem.visible = true;
        } else {
            this._errorItem.visible = false;
        }

        const now = GLib.DateTime.new_now_local();
        const nowMinutes = now.get_hour() * 60 + now.get_minute();
        const displayTimes = this._displayTimes();
        const displayNames = this._displayNames();

        for (let i = 0; i < PRAYER_NAMES.length; i++) {
            const entry = this._menuItems[PRAYER_NAMES[i]];
            if (!entry) continue;

            const displayTime = displayTimes ? displayTimes[i] : '--:--';
            entry.timeLabel.set_text(displayTime || '--:--');
            entry.item.label.set_text(displayNames[i]);

            if (this._iqamaEnabled && this._iqama && i < this._iqama.length) {
                const iqTime = this._resolveIqama(this._times[i], this._iqama[i]);
                entry.iqamaLabel.set_text(iqTime ? `Iq ${iqTime}` : '');
            } else {
                entry.iqamaLabel.set_text('');
            }

            const m = this._toMinutes(displayTime || '00:00');
            const isNext = this._findNextPrayerIndex(nowMinutes) === i;
            const isPast = m <= nowMinutes;

            if (isNext) {
                entry.item.style_class = 'popup-menu-item next-prayer-menu-active';
            } else if (isPast) {
                entry.item.style_class = 'popup-menu-item next-prayer-menu-past';
            } else {
                entry.item.style_class = 'popup-menu-item';
            }
        }

        const showJumua2 = this._isFriday() && this._jumua2;
        this._jumua2Item.visible = showJumua2;
        this._jumuaSeparator.visible = showJumua2;
        if (showJumua2) {
            this._jumua2Item.label.set_text(this._t('jumuah2'));
            this._jumua2TimeLabel.set_text(this._jumua2);
        }

        // Update shuruq label text for language
        this._shuruqItem.label.set_text(this._t('shuruq'));
        if (this._shuruq)
            this._shuruqTimeLabel.set_text(this._shuruq);

        this._hijriItem.visible = Boolean(this._hijriDate);
        if (this._hijriDate)
            this._hijriItem.label.set_text(`${this._t('hijriDate')}: ${this._hijriDate}`);

        this._qiblaItem.visible = Boolean(this._qiblaDirection);
        if (this._qiblaDirection)
            this._qiblaItem.label.set_text(`${this._t('qibla')}: ${this._qiblaDirection}`);
    }

    _toMinutes(timeStr) {
        const parts = timeStr.split(':');
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }

    _findNextPrayerIndex(nowMinutes) {
        const events = this._prayerEvents();
        const next = events.find(event => event.absoluteMinutes > nowMinutes);
        if (next) return next.index;
        const first = events[0];
        if (first && first.absoluteMinutes < 0 && first.absoluteMinutes + 1440 > nowMinutes)
            return first.index;
        return -1;
    }

    _formatCountdown(remaining) {
        const format = this._settings.get_string('countdown-format') || 'compact';
        const h = Math.floor(remaining / 60);
        const min = remaining % 60;
        if (format === 'full') {
            if (h > 0)
                return `-${h}h ${min.toString().padStart(2, '0')}m`;
            return `-${min}m`;
        }
        // compact (default)
        if (h > 0)
            return `-${h}h${min.toString().padStart(2, '0')}m`;
        return `-${min}m`;
    }

    _formatElapsed(elapsed) {
        const format = this._settings.get_string('countdown-format') || 'compact';
        const h = Math.floor(elapsed / 60);
        const min = elapsed % 60;
        if (format === 'full') {
            if (h > 0)
                return `+${h}h ${min.toString().padStart(2, '0')}m`;
            return `+${min}m`;
        }
        if (h > 0)
            return `+${h}h${min.toString().padStart(2, '0')}m`;
        return `+${min}m`;
    }

    _updateLabel() {
        if (!this._times || this._times.length < 5) return;

        const now = GLib.DateTime.new_now_local();
        const nowMinutes = now.get_hour() * 60 + now.get_minute();
        const nextEvent = this._findNextPrayerEvent(nowMinutes);
        const displayTimes = this._displayTimes();
        const displayNames = this._displayNames();
        const displayMode = this._settings.get_string('display-mode') || 'countdown';

        let name, time, remaining, iconIdx;

        if (!nextEvent) {
            name = displayNames[0];
            time = displayTimes[0];
            remaining = (24 * 60 - nowMinutes) + this._toMinutes(displayTimes[0]);
            iconIdx = 0;
        } else {
            name = displayNames[nextEvent.index];
            time = displayTimes[nextEvent.index];
            remaining = nextEvent.absoluteMinutes - nowMinutes;
            iconIdx = nextEvent.index;
        }

        if (displayMode === 'since') {
            const events = this._prayerEvents(displayTimes);
            let lastEvent = null;
            for (const event of events) {
                if (event.absoluteMinutes <= nowMinutes)
                    lastEvent = event;
            }
            if (!lastEvent && events.length)
                lastEvent = {...events[events.length - 1], absoluteMinutes: events[events.length - 1].absoluteMinutes - 1440};
            if (lastEvent) {
                name = this._t('sinceLastPrayer')(displayNames[lastEvent.index]);
                time = displayTimes[lastEvent.index];
                remaining = nowMinutes - lastEvent.absoluteMinutes;
                iconIdx = lastEvent.index;
            }
        }

        this._icon.icon_name = PRAYER_ICONS[iconIdx];
        this._icon.visible = displayMode !== 'icon' || true;

        let showName = true;
        let showTime = true;
        let showCountdown = true;

        switch (displayMode) {
        case 'since':
            showTime = false;
            break;
        case 'time':
            showCountdown = false;
            break;
        case 'name':
            showTime = false;
            showCountdown = false;
            break;
        case 'compact':
            showTime = false;
            break;
        case 'icon':
            showName = false;
            showTime = false;
            showCountdown = false;
            break;
        default:
            break;
        }

        this._prayerLabel.set_text(showName ? name : '');
        this._timeLabel.set_text(showTime ? time : '');
        this._countdownLabel.set_text(showCountdown ? (displayMode === 'since' ? this._formatElapsed(remaining) : this._formatCountdown(remaining)) : '');
        this._prayerLabel.visible = showName;
        this._timeLabel.visible = showTime;
        this._countdownLabel.visible = showCountdown;

        this._updateMenu();
    }

    _clearNotificationTimers() {
        for (const id of this._notificationTimers)
            GLib.source_remove(id);
        this._notificationTimers = [];
    }

    _scheduleNotifications() {
        this._clearNotificationTimers();
        if (!this._times) return;
        if (!this._settings.get_boolean('notifications-enabled')) return;

        const now = GLib.DateTime.new_now_local();
        const nowSeconds = now.get_hour() * 3600 + now.get_minute() * 60 + now.get_second();
        const displayNames = this._displayNames();
        const prayerSettings = this._getPrayerNotificationSettings();
        const events = this._prayerEvents();
        if (events.length && events[0].absoluteMinutes <= nowSeconds / 60)
            events.push({...events[0], absoluteMinutes: events[0].absoluteMinutes + 1440});

        for (const event of events) {
            const i = event.index;
            const notifKey = this._notificationKeyForIndex(i);
            const setting = prayerSettings[notifKey];
            if (!setting?.enabled) continue;

            const name = displayNames[i];
            const time = event.time;
            const prayerSeconds = event.absoluteMinutes * 60;

            const bypassDnd = this._shouldBypassDnd(setting);

            const reminderMinutes = setting.reminder_minutes || 0;
            if (reminderMinutes > 0) {
                const reminderDelay = prayerSeconds - (reminderMinutes * 60) - nowSeconds;
                if (reminderDelay > 0) {
                    const reminderId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, reminderDelay, () => {
                        this._sendReminderNotification(name, reminderMinutes, bypassDnd);
                        return GLib.SOURCE_REMOVE;
                    });
                    this._notificationTimers.push(reminderId);
                }
            }

            const delay = prayerSeconds - nowSeconds;
            if (delay <= 0) continue;

            const id = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, delay, () => {
                this._sendNotification(name, time, bypassDnd);
                if (this._shouldPlayAdhan(setting))
                    this._maybePlayAdhan(true);
                this._updateLabel();
                return GLib.SOURCE_REMOVE;
            });
            this._notificationTimers.push(id);
        }
    }

    _sendReminderNotification(prayerName, minutes, bypassDnd = false) {
        const title = this._t('notifTitle')(prayerName, `${minutes}m`);
        const body = `${prayerName} in ${minutes} minutes`;
        const source = MessageTray.getSystemSource();
        const notification = new MessageTray.Notification({
            source,
            title,
            body,
            iconName: 'preferences-system-time-symbolic',
        });
        notification.urgency = bypassDnd
            ? MessageTray.Urgency.CRITICAL
            : MessageTray.Urgency.NORMAL;
        source.addNotification(notification);
    }

    _sendNotification(prayerName, time, bypassDnd = false) {
        const title = this._t('notifTitle')(prayerName, time);
        const body = this._t('notifBody')(prayerName);
        const source = MessageTray.getSystemSource();
        const notification = new MessageTray.Notification({
            source,
            title,
            body,
            iconName: 'preferences-system-time-symbolic',
        });
        notification.urgency = bypassDnd
            ? MessageTray.Urgency.CRITICAL
            : MessageTray.Urgency.HIGH;
        source.addNotification(notification);
    }

    _maybePlayAdhan(force = false) {
        if (!this._gstAvailable) return;
        if (!force && !this._settings.get_boolean('adhan-enabled')) return;
        const path = this._settings.get_string('adhan-path');
        if (!path) return;

        const file = Gio.File.new_for_path(path);
        if (!file.query_exists(null)) return;

        this._playAdhan(path);
    }

    _playAdhan(filePath) {
        this._stopAdhan();

        const Gst = this._gstModule;
        if (!Gst) return;

        try {
            this._gstPipeline = Gst.ElementFactory.make('playbin', 'adhan-player');
            if (!this._gstPipeline) return;

            const fileUri = Gio.File.new_for_path(filePath).get_uri();
            this._gstPipeline.set_property('uri', fileUri);

            const bus = this._gstPipeline.get_bus();
            bus.add_signal_watch();
            this._gstBusWatchId = bus.connect('message', (_bus, msg) => {
                if (msg.type === Gst.MessageType.EOS || msg.type === Gst.MessageType.ERROR) {
                    this._stopAdhan();
                }
            });

            this._gstPipeline.set_state(Gst.State.PLAYING);
        } catch (e) {
            logError(e, 'NextPrayer: Failed to play adhan');
            this._stopAdhan();
        }
    }

    _stopAdhan() {
        if (this._gstPipeline) {
            const Gst = this._gstModule;
            try {
                const bus = this._gstPipeline.get_bus();
                if (bus && this._gstBusWatchId) {
                    bus.disconnect(this._gstBusWatchId);
                    bus.remove_signal_watch();
                }
                if (Gst)
                    this._gstPipeline.set_state(Gst.State.NULL);
            } catch {
                // Ignore cleanup errors
            }
            this._gstPipeline = null;
            this._gstBusWatchId = null;
        }
    }

    _scheduleDailyRefresh() {
        if (this._fetchTimer)
            GLib.source_remove(this._fetchTimer);

        const now = GLib.DateTime.new_now_local();
        const secondsUntilMidnight = Math.max(
            (24 - now.get_hour()) * 3600 - now.get_minute() * 60 - now.get_second() + 60,
            3600
        );

        this._fetchTimer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, secondsUntilMidnight, () => {
            this._fetchTimes();
            return GLib.SOURCE_REMOVE;
        });
    }

    _saveCache() {
        if (!this._times) return;
        const cache = JSON.stringify({
            times: this._times,
            shuruq: this._shuruq,
            name: this._mosqueName,
            iqama: this._iqama,
            iqamaEnabled: this._iqamaEnabled,
            jumua: this._jumua,
            jumua2: this._jumua2,
            hijriDate: this._hijriDate,
            qiblaDirection: this._qiblaDirection,
            date: new Date().toISOString().split('T')[0],
        });
        this._settings.set_string('cached-data', cache);
    }

    _loadCache() {
        const raw = this._settings.get_string('cached-data');
        if (!raw) return false;
        try {
            const data = JSON.parse(raw);
            if (!data.times || !data.times.length) return false;
            this._times = data.times;
            this._shuruq = data.shuruq || null;
            this._mosqueName = data.name || '';
            this._iqama = data.iqama || null;
            this._iqamaEnabled = data.iqamaEnabled || false;
            this._jumua = data.jumua || null;
            this._jumua2 = data.jumua2 || null;
            this._hijriDate = data.hijriDate || null;
            this._qiblaDirection = data.qiblaDirection || null;
            this._isCached = true;
            this._updateLabel();
            this._updateMenu();
            this._scheduleNotifications();
            return true;
        } catch {
            return false;
        }
    }

    _handleFetchError(message) {
        this._lastError = message;
        if (!this._times)
            this._loadCache();
        if (this._times) {
            this._updateLabel();
        } else {
            this._prayerLabel.set_text(this._t('error'));
            this._timeLabel.set_text('');
            this._countdownLabel.set_text('');
        }
        this._updateMenu();
        this._scheduleFetchRetry();
    }

    _scheduleFetchRetry() {
        if (this._fetchTimer)
            GLib.source_remove(this._fetchTimer);

        this._fetchTimer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 300, () => {
            this._fetchTimes();
            return GLib.SOURCE_REMOVE;
        });
    }
}
