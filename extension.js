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

const PRAYER_NAMES = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
const PRAYER_ICONS = [
    'daytime-sunrise-symbolic',
    'weather-clear-symbolic',
    'weather-few-clouds-symbolic',
    'daytime-sunset-symbolic',
    'weather-clear-night-symbolic',
];
const SHURUQ_ICON = 'daytime-sunrise-symbolic';

export default class NextPrayerExtension extends Extension {
    _indicator = null;
    _settings = null;
    _updateTimer = null;
    _fetchTimer = null;
    _session = null;
    _times = null;
    _shuruq = null;
    _mosqueName = null;
    _settingsChangedId = null;
    _notificationTimers = [];

    enable() {
        this._settings = this.getSettings();
        this._session = new Soup.Session();

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

        this._fetchTimes();
        this._startUpdateTimer();
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
        this._clearNotificationTimers();
        this._indicator?.destroy();
        this._indicator = null;
        this._session = null;
        this._settings = null;
        this._times = null;
    }

    _buildMenu() {
        this._mosqueLabel = new PopupMenu.PopupMenuItem('', {reactive: false});
        this._mosqueLabel.label.style_class = 'next-prayer-mosque-name';
        this._indicator.menu.addMenuItem(this._mosqueLabel);

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this._menuItems = {};
        for (let i = 0; i < PRAYER_NAMES.length; i++) {
            const item = new PopupMenu.PopupImageMenuItem(
                PRAYER_NAMES[i], PRAYER_ICONS[i]);
            item.setSensitive(false);

            const timeLabel = new St.Label({
                text: '--:--',
                y_align: Clutter.ActorAlign.CENTER,
                style_class: 'next-prayer-menu-time',
            });
            item.add_child(timeLabel);

            this._indicator.menu.addMenuItem(item);
            this._menuItems[PRAYER_NAMES[i]] = {item, timeLabel};
        }

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const shuruqItem = new PopupMenu.PopupImageMenuItem('Shuruq', SHURUQ_ICON);
        shuruqItem.setSensitive(false);
        this._shuruqTimeLabel = new St.Label({
            text: '--:--',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'next-prayer-menu-time',
        });
        shuruqItem.add_child(this._shuruqTimeLabel);
        this._indicator.menu.addMenuItem(shuruqItem);

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const settingsItem = new PopupMenu.PopupImageMenuItem(
            'Configure mosque', 'emblem-system-symbolic');
        settingsItem.connect('activate', () => this.openPreferences());
        this._indicator.menu.addMenuItem(settingsItem);

        const refreshItem = new PopupMenu.PopupImageMenuItem(
            'Refresh', 'view-refresh-symbolic');
        refreshItem.connect('activate', () => this._fetchTimes());
        this._indicator.menu.addMenuItem(refreshItem);
    }

    _startUpdateTimer() {
        if (this._updateTimer)
            GLib.source_remove(this._updateTimer);

        this._updateTimer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 60, () => {
            this._updateLabel();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _slugFromUrl(url) {
        if (!url) return null;
        const match = url.match(/mawaqit\.net\/\w+\/(?:w\/)?(.+?)\/?$/);
        return match ? match[1] : null;
    }

    _fetchTimes() {
        const url = this._settings.get_string('mosque-url');
        if (!url) {
            this._prayerLabel.set_text('No mosque set');
            this._timeLabel.set_text('');
            this._countdownLabel.set_text('');
            return;
        }

        let fetchUrl = url;
        if (!fetchUrl.includes('/w/')) {
            const slug = this._slugFromUrl(fetchUrl);
            if (slug)
                fetchUrl = `https://mawaqit.net/en/w/${slug}`;
        }

        const message = Soup.Message.new('GET', fetchUrl);
        if (!message) {
            this._prayerLabel.set_text('Invalid URL');
            return;
        }

        this._prayerLabel.set_text('Loading…');
        this._timeLabel.set_text('');
        this._countdownLabel.set_text('');

        this._session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (session, result) => {
            try {
                const bytes = session.send_and_read_finish(result);
                if (message.get_status() !== Soup.Status.OK) {
                    this._prayerLabel.set_text('Fetch error');
                    this._scheduleFetchRetry();
                    return;
                }

                const html = new TextDecoder().decode(bytes.get_data());
                this._parseConfData(html);
                this._scheduleNotifications();
                this._updateLabel();
                this._updateMenu();
                this._scheduleDailyRefresh();
            } catch (e) {
                logError(e, 'NextPrayer: fetch error');
                this._prayerLabel.set_text('Error');
                this._scheduleFetchRetry();
            }
        });
    }

    _parseConfData(html) {
        const match = html.match(/confData\s*=\s*(\{.*?\});/s);
        if (!match) {
            this._prayerLabel.set_text('Parse error');
            return;
        }

        try {
            const data = JSON.parse(match[1]);
            this._times = data.times;
            this._shuruq = data.shuruq || null;
            this._mosqueName = data.name || data.label || '';
        } catch (e) {
            logError(e, 'NextPrayer: JSON parse error');
            this._prayerLabel.set_text('Parse error');
        }
    }

    _updateMenu() {
        if (!this._times) return;

        if (this._mosqueName)
            this._mosqueLabel.label.set_text(this._mosqueName);

        const now = GLib.DateTime.new_now_local();
        const nowMinutes = now.get_hour() * 60 + now.get_minute();

        for (let i = 0; i < PRAYER_NAMES.length; i++) {
            const name = PRAYER_NAMES[i];
            const entry = this._menuItems[name];
            if (!entry) continue;

            entry.timeLabel.set_text(this._times[i] || '--:--');

            const m = this._toMinutes(this._times[i]);
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

        if (this._shuruq)
            this._shuruqTimeLabel.set_text(this._shuruq);
    }

    _toMinutes(timeStr) {
        const parts = timeStr.split(':');
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }

    _findNextPrayerIndex(nowMinutes) {
        for (let i = 0; i < this._times.length; i++) {
            if (this._toMinutes(this._times[i]) > nowMinutes)
                return i;
        }
        return -1;
    }

    _formatCountdown(remaining) {
        const h = Math.floor(remaining / 60);
        const min = remaining % 60;
        if (h > 0)
            return `-${h}h ${min.toString().padStart(2, '0')}m`;
        return `-${min}m`;
    }

    _updateLabel() {
        if (!this._times || this._times.length < 5) return;

        const now = GLib.DateTime.new_now_local();
        const nowMinutes = now.get_hour() * 60 + now.get_minute();
        const nextIdx = this._findNextPrayerIndex(nowMinutes);

        let name, time, remaining;

        if (nextIdx === -1) {
            name = PRAYER_NAMES[0];
            time = this._times[0];
            remaining = (24 * 60 - nowMinutes) + this._toMinutes(this._times[0]);
            this._icon.icon_name = PRAYER_ICONS[0];
        } else {
            name = PRAYER_NAMES[nextIdx];
            time = this._times[nextIdx];
            remaining = this._toMinutes(this._times[nextIdx]) - nowMinutes;
            this._icon.icon_name = PRAYER_ICONS[nextIdx];
        }

        this._prayerLabel.set_text(name);
        this._timeLabel.set_text(time);
        this._countdownLabel.set_text(this._formatCountdown(remaining));

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

        const now = GLib.DateTime.new_now_local();
        const nowSeconds = now.get_hour() * 3600 + now.get_minute() * 60 + now.get_second();

        for (let i = 0; i < this._times.length; i++) {
            const prayerSeconds = this._toMinutes(this._times[i]) * 60;
            const delay = prayerSeconds - nowSeconds;
            if (delay <= 0) continue;

            const name = PRAYER_NAMES[i];
            const time = this._times[i];
            const id = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, delay, () => {
                this._sendNotification(name, time);
                this._updateLabel();
                return GLib.SOURCE_REMOVE;
            });
            this._notificationTimers.push(id);
        }
    }

    _sendNotification(prayerName, time) {
        const source = MessageTray.getSystemSource();
        const notification = new MessageTray.Notification({
            source,
            title: `${prayerName} - ${time}`,
            body: `It's time for ${prayerName} prayer`,
            iconName: 'preferences-system-time-symbolic',
        });
        notification.urgency = MessageTray.Urgency.HIGH;
        source.addNotification(notification);
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

    _scheduleFetchRetry() {
        if (this._fetchTimer)
            GLib.source_remove(this._fetchTimer);

        this._fetchTimer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 300, () => {
            this._fetchTimes();
            return GLib.SOURCE_REMOVE;
        });
    }
}
