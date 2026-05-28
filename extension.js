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

export default class NextPrayerExtension extends Extension {
    _indicator = null;
    _label = null;
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

        this._label = new St.Label({
            text: 'Prayer …',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'next-prayer-label',
        });
        this._indicator.add_child(this._label);

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
        this._label = null;
        this._session = null;
        this._settings = null;
        this._times = null;
    }

    _buildMenu() {
        this._menuItems = {};
        for (const name of PRAYER_NAMES) {
            const item = new PopupMenu.PopupMenuItem(`${name}: --:--`);
            item.setSensitive(false);
            this._indicator.menu.addMenuItem(item);
            this._menuItems[name] = item;
        }

        this._shuruqItem = new PopupMenu.PopupMenuItem('Shuruq: --:--');
        this._shuruqItem.setSensitive(false);
        this._indicator.menu.addMenuItem(this._shuruqItem);

        this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const settingsItem = new PopupMenu.PopupMenuItem('Configure mosque…');
        settingsItem.connect('activate', () => {
            this.openPreferences();
        });
        this._indicator.menu.addMenuItem(settingsItem);

        const refreshItem = new PopupMenu.PopupMenuItem('Refresh');
        refreshItem.connect('activate', () => {
            this._fetchTimes();
        });
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
            this._label.set_text('No mosque set');
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
            this._label.set_text('Invalid URL');
            return;
        }

        this._label.set_text('Loading…');

        this._session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (session, result) => {
            try {
                const bytes = session.send_and_read_finish(result);
                if (message.get_status() !== Soup.Status.OK) {
                    this._label.set_text('Fetch error');
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
                this._label.set_text('Error');
                this._scheduleFetchRetry();
            }
        });
    }

    _parseConfData(html) {
        const match = html.match(/confData\s*=\s*(\{.*?\});/s);
        if (!match) {
            this._label.set_text('Parse error');
            return;
        }

        try {
            const data = JSON.parse(match[1]);
            this._times = data.times;
            this._shuruq = data.shuruq || null;
            this._mosqueName = data.name || data.label || '';
        } catch (e) {
            logError(e, 'NextPrayer: JSON parse error');
            this._label.set_text('Parse error');
        }
    }

    _updateMenu() {
        if (!this._times) return;

        for (let i = 0; i < PRAYER_NAMES.length; i++) {
            const name = PRAYER_NAMES[i];
            const time = this._times[i] || '--:--';
            this._menuItems[name]?.label.set_text(`${name}: ${time}`);
        }

        if (this._shuruq)
            this._shuruqItem.label.set_text(`Shuruq: ${this._shuruq}`);
    }

    _toMinutes(timeStr) {
        const parts = timeStr.split(':');
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }

    _updateLabel() {
        if (!this._times || this._times.length < 5) return;

        const now = GLib.DateTime.new_now_local();
        const nowMinutes = now.get_hour() * 60 + now.get_minute();

        let nextIdx = -1;
        let nextMinutes = -1;

        for (let i = 0; i < this._times.length; i++) {
            const m = this._toMinutes(this._times[i]);
            if (m > nowMinutes) {
                nextIdx = i;
                nextMinutes = m;
                break;
            }
        }

        if (nextIdx === -1) {
            const fajrMinutes = this._toMinutes(this._times[0]);
            const remaining = (24 * 60 - nowMinutes) + fajrMinutes;
            const h = Math.floor(remaining / 60);
            const min = remaining % 60;
            this._label.set_text(`Fajr  ${this._times[0]}  (-${h}h${min.toString().padStart(2, '0')})`);
        } else {
            const remaining = nextMinutes - nowMinutes;
            const h = Math.floor(remaining / 60);
            const min = remaining % 60;
            const name = PRAYER_NAMES[nextIdx];
            this._label.set_text(`${name}  ${this._times[nextIdx]}  (-${h}h${min.toString().padStart(2, '0')})`);
        }
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
        const tomorrow = now.add_hours(24 - now.get_hour()).add_minutes(-now.get_minute());
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
