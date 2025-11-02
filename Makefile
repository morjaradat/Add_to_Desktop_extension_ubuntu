VENV_PYTHON = $(shell pwd)/.venv/bin/python3
INSTALL_DIR_NAUTILUS = $(HOME)/.local/share/nautilus-python/extensions
INSTALL_DIR_DBUS = $(HOME)/.local/share/dbus-1/services
INSTALL_DIR_DESKTOP = $(HOME)/.local/share/applications
INSTALL_DIR_BIN = $(HOME)/.local/bin

SERVICE_SCRIPT_NAME = add-to-desktop-service
SERVICE_SCRIPT_PATH = $(INSTALL_DIR_BIN)/$(SERVICE_SCRIPT_NAME)

.PHONY: install uninstall

install:
	# Create executable service script
	@echo "Creating service script..."
	@mkdir -p $(INSTALL_DIR_BIN)
	@echo "#!$(VENV_PYTHON)" > $(SERVICE_SCRIPT_PATH)
	@echo "" >> $(SERVICE_SCRIPT_PATH)
	@cat src/linker-service.py >> $(SERVICE_SCRIPT_PATH)
	@chmod +x $(SERVICE_SCRIPT_PATH)

	# Install the Nautilus extension
	@mkdir -p $(INSTALL_DIR_NAUTILUS)
	@cp src/add-to-desktop.py $(INSTALL_DIR_NAUTILUS)/
	@echo "Installed Nautilus extension"
	
	# Install D-Bus service file (update Exec path before copying)
	@mkdir -p $(INSTALL_DIR_DBUS)
	@sed "s|Exec=.*|Exec=$(SERVICE_SCRIPT_PATH)|" data/org.my.desktop_linker.service > $(INSTALL_DIR_DBUS)/org.my.desktop_linker.service
	@echo "Installed D-Bus service file to $(INSTALL_DIR_DBUS)"
	
	# Install .desktop file (update Exec path before copying)
	@mkdir -p $(INSTALL_DIR_DESKTOP)
	@sed "s|Exec=.*|Exec=$(SERVICE_SCRIPT_PATH)|" data/org.my.desktop_linker.desktop > $(INSTALL_DIR_DESKTOP)/org.my.desktop_linker.desktop
	@echo "Installed .desktop file"
	@echo "Installation complete. Please restart Nautilus with 'nautilus -q'"

uninstall:
	@rm -f $(INSTALL_DIR_NAUTILUS)/add-to-desktop.py
	@rm -f $(INSTALL_DIR_DBUS)/org.my.desktop_linker.service
	@rm -f $(INSTALL_DIR_DESKTOP)/org.my.desktop_linker.desktop
	@rm -f $(SERVICE_SCRIPT_PATH)
	@echo "Uninstallation complete."
