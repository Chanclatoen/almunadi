UUID = almunadi@almunadi.net
INSTALL_DIR = $(HOME)/.local/share/gnome-shell/extensions/$(UUID)

.PHONY: build install uninstall

build:
	glib-compile-schemas schemas/

install: build
	mkdir -p $(INSTALL_DIR)
	cp -r extension.js prefs.js metadata.json stylesheet.css schemas $(INSTALL_DIR)/
	@echo "Installed. Log out and back in, then run: gnome-extensions enable $(UUID)"

uninstall:
	rm -rf $(INSTALL_DIR)
	@echo "Uninstalled. Log out and back in to complete removal."
