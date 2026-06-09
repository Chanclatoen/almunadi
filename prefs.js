import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';
import GObject from 'gi://GObject';
import Soup from 'gi://Soup?version=3.0';
import GLib from 'gi://GLib';
import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

const API_BASE = 'https://mawaqit.net/api/2.0/mosque';

export default class NextPrayerPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        const session = new Soup.Session();

        const page = new Adw.PreferencesPage({
            title: 'Next Prayer',
            icon_name: 'preferences-system-time-symbolic',
        });

        // --- Search group ---
        const searchGroup = new Adw.PreferencesGroup({
            title: 'Find Your Mosque',
            description: 'Search by mosque name or city',
        });

        const searchRow = new Adw.EntryRow({
            title: 'Search',
            show_apply_button: true,
        });

        const resultsGroup = new Adw.PreferencesGroup();
        let resultRows = [];

        const clearResults = () => {
            for (const r of resultRows)
                resultsGroup.remove(r);
            resultRows = [];
        };

        searchRow.connect('apply', () => {
            const query = searchRow.get_text().trim();
            if (!query) return;

            clearResults();

            const message = Soup.Message.new('GET', `${API_BASE}/search?word=${encodeURIComponent(query)}`);
            if (!message) return;
            message.get_request_headers().append('Accept', 'application/json');

            session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, null, (s, result) => {
                try {
                    const bytes = s.send_and_read_finish(result);
                    if (message.get_status() !== Soup.Status.OK) return;

                    const json = new TextDecoder().decode(bytes.get_data());
                    const mosques = JSON.parse(json);

                    clearResults();

                    if (!mosques.length) {
                        const noResult = new Adw.ActionRow({title: 'No mosques found'});
                        resultsGroup.add(noResult);
                        resultRows.push(noResult);
                        return;
                    }

                    for (const mosque of mosques.slice(0, 10)) {
                        const row = new Adw.ActionRow({
                            title: mosque.name || mosque.label || 'Unknown',
                            subtitle: mosque.localisation || '',
                            activatable: true,
                        });
                        row.add_suffix(new Gtk.Image({icon_name: 'go-next-symbolic'}));
                        row.connect('activated', () => {
                            const url = `https://mawaqit.net/en/w/${mosque.slug}`;
                            settings.set_string('mosque-url', url);
                            urlRow.set_text(url);
                            clearResults();
                        });
                        resultsGroup.add(row);
                        resultRows.push(row);
                    }
                } catch (e) {
                    logError(e, 'NextPrayer: search error');
                }
            });
        });

        searchGroup.add(searchRow);
        page.add(searchGroup);
        page.add(resultsGroup);

        // --- URL group ---
        const group = new Adw.PreferencesGroup({
            title: 'Mosque Configuration',
            description: 'Or paste your mosque\'s Mawaqit URL directly',
        });

        const urlRow = new Adw.EntryRow({
            title: 'Mawaqit URL',
            text: settings.get_string('mosque-url'),
            show_apply_button: true,
        });

        urlRow.connect('apply', () => {
            settings.set_string('mosque-url', urlRow.get_text());
        });

        settings.connect('changed::mosque-url', () => {
            urlRow.set_text(settings.get_string('mosque-url'));
        });

        group.add(urlRow);
        page.add(group);

        // --- Notifications group ---
        const notifGroup = new Adw.PreferencesGroup({
            title: 'Notifications',
        });

        const notifRow = new Adw.SwitchRow({
            title: 'Prayer notifications',
            subtitle: 'Show a notification when each prayer time arrives',
        });
        settings.bind('notifications-enabled', notifRow, 'active',
            Gio.SettingsBindFlags.DEFAULT);
        notifGroup.add(notifRow);
        page.add(notifGroup);

        // --- Language group ---
        const langGroup = new Adw.PreferencesGroup({
            title: 'Language',
            description: 'Display language for prayer names and UI',
        });

        const langModel = new Gtk.StringList();
        langModel.append('English');
        langModel.append('العربية');
        langModel.append('Français');
        langModel.append('Türkçe');

        const langCodes = ['en', 'ar', 'fr', 'tr'];

        const langRow = new Adw.ComboRow({
            title: 'Language',
            subtitle: 'Prayer names, notifications, and menu items',
            model: langModel,
        });

        const currentLang = settings.get_string('language') || 'en';
        const langIdx = langCodes.indexOf(currentLang);
        langRow.set_selected(langIdx >= 0 ? langIdx : 0);

        langRow.connect('notify::selected', () => {
            const idx = langRow.get_selected();
            if (idx >= 0 && idx < langCodes.length)
                settings.set_string('language', langCodes[idx]);
        });

        settings.connect('changed::language', () => {
            const lang = settings.get_string('language');
            const idx = langCodes.indexOf(lang);
            if (idx >= 0)
                langRow.set_selected(idx);
        });

        langGroup.add(langRow);
        page.add(langGroup);

        // --- Adhan group ---
        const adhanGroup = new Adw.PreferencesGroup({
            title: 'Adhan',
            description: 'Play adhan audio at prayer time',
        });

        const adhanEnabledRow = new Adw.SwitchRow({
            title: 'Enable adhan',
            subtitle: 'Play audio file when prayer time arrives',
        });
        settings.bind('adhan-enabled', adhanEnabledRow, 'active',
            Gio.SettingsBindFlags.DEFAULT);
        adhanGroup.add(adhanEnabledRow);

        const adhanPathRow = new Adw.EntryRow({
            title: 'Audio file path',
            text: settings.get_string('adhan-path'),
            show_apply_button: true,
        });

        adhanPathRow.connect('apply', () => {
            settings.set_string('adhan-path', adhanPathRow.get_text());
        });

        settings.connect('changed::adhan-path', () => {
            adhanPathRow.set_text(settings.get_string('adhan-path'));
        });

        adhanGroup.add(adhanPathRow);
        page.add(adhanGroup);

        // --- Countdown format group ---
        const countdownGroup = new Adw.PreferencesGroup({
            title: 'Display',
        });

        const countdownModel = new Gtk.StringList();
        countdownModel.append('Compact (-2h15m)');
        countdownModel.append('Full (-2h 15m)');

        const countdownCodes = ['compact', 'full'];

        const countdownRow = new Adw.ComboRow({
            title: 'Countdown format',
            subtitle: 'How remaining time is displayed in the panel',
            model: countdownModel,
        });

        const currentFormat = settings.get_string('countdown-format') || 'compact';
        const fmtIdx = countdownCodes.indexOf(currentFormat);
        countdownRow.set_selected(fmtIdx >= 0 ? fmtIdx : 0);

        countdownRow.connect('notify::selected', () => {
            const idx = countdownRow.get_selected();
            if (idx >= 0 && idx < countdownCodes.length)
                settings.set_string('countdown-format', countdownCodes[idx]);
        });

        settings.connect('changed::countdown-format', () => {
            const fmt = settings.get_string('countdown-format');
            const idx = countdownCodes.indexOf(fmt);
            if (idx >= 0)
                countdownRow.set_selected(idx);
        });

        countdownGroup.add(countdownRow);
        page.add(countdownGroup);

        // --- Saved Mosques group ---
        const savedGroup = new Adw.PreferencesGroup({
            title: 'Saved Mosques',
            description: 'Quick-switch between your mosques',
        });

        let savedRows = [];

        const rebuildSavedMosques = () => {
            for (const r of savedRows)
                savedGroup.remove(r);
            savedRows = [];

            let mosques = [];
            try {
                mosques = JSON.parse(settings.get_string('saved-mosques') || '[]');
            } catch {
                mosques = [];
            }

            for (const mosque of mosques) {
                const row = new Adw.ActionRow({
                    title: mosque.name || mosque.url,
                    subtitle: mosque.url,
                });

                const deleteBtn = new Gtk.Button({
                    icon_name: 'user-trash-symbolic',
                    valign: Gtk.Align.CENTER,
                    css_classes: ['flat'],
                });
                deleteBtn.connect('clicked', () => {
                    let current = [];
                    try {
                        current = JSON.parse(settings.get_string('saved-mosques') || '[]');
                    } catch {
                        current = [];
                    }
                    const filtered = current.filter(m => m.url !== mosque.url);
                    settings.set_string('saved-mosques', JSON.stringify(filtered));
                });

                const selectBtn = new Gtk.Button({
                    icon_name: 'go-next-symbolic',
                    valign: Gtk.Align.CENTER,
                    css_classes: ['flat'],
                    tooltip_text: 'Set as active mosque',
                });
                selectBtn.connect('clicked', () => {
                    settings.set_string('mosque-url', mosque.url);
                });

                row.add_suffix(selectBtn);
                row.add_suffix(deleteBtn);
                savedGroup.add(row);
                savedRows.push(row);
            }

            // Add current mosque button
            const addBtn = new Adw.ActionRow({
                title: 'Add Current Mosque',
                subtitle: 'Save the currently connected mosque for quick switching',
                activatable: true,
            });
            addBtn.add_prefix(new Gtk.Image({icon_name: 'list-add-symbolic'}));
            addBtn.connect('activated', () => {
                const currentUrl = settings.get_string('mosque-url');
                if (!currentUrl) return;

                let current = [];
                try {
                    current = JSON.parse(settings.get_string('saved-mosques') || '[]');
                } catch {
                    current = [];
                }

                // Don't add duplicates
                if (current.some(m => m.url === currentUrl)) return;

                // Try to get a name from cached data
                let name = currentUrl;
                try {
                    const cached = JSON.parse(settings.get_string('cached-data') || '{}');
                    if (cached.name)
                        name = cached.name;
                } catch {
                    // use URL as name
                }

                current.push({url: currentUrl, name});
                settings.set_string('saved-mosques', JSON.stringify(current));
            });
            savedGroup.add(addBtn);
            savedRows.push(addBtn);
        };

        rebuildSavedMosques();

        settings.connect('changed::saved-mosques', () => {
            rebuildSavedMosques();
        });

        page.add(savedGroup);

        // --- Help group ---
        const helpGroup = new Adw.PreferencesGroup({
            title: 'Help',
            description: 'Go to mawaqit.net, find your mosque, and paste the full URL here.\nExample: https://mawaqit.net/en/w/arrahmaan-dordrecht',
        });
        page.add(helpGroup);

        window.add(page);
    }
}
