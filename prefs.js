import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';
import GObject from 'gi://GObject';
import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

export default class NextPrayerPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();

        const page = new Adw.PreferencesPage({
            title: 'Next Prayer',
            icon_name: 'preferences-system-time-symbolic',
        });

        const group = new Adw.PreferencesGroup({
            title: 'Mosque Configuration',
            description: 'Enter your mosque\'s Mawaqit URL to display prayer times',
        });

        const row = new Adw.EntryRow({
            title: 'Mawaqit URL',
            text: settings.get_string('mosque-url'),
            show_apply_button: true,
        });

        row.connect('apply', () => {
            settings.set_string('mosque-url', row.get_text());
        });

        settings.connect('changed::mosque-url', () => {
            row.set_text(settings.get_string('mosque-url'));
        });

        group.add(row);
        page.add(group);

        const helpGroup = new Adw.PreferencesGroup({
            title: 'Help',
            description: 'Go to mawaqit.net, find your mosque, and paste the full URL here.\nExample: https://mawaqit.net/en/w/arrahmaan-dordrecht',
        });
        page.add(helpGroup);

        window.add(page);
    }
}
