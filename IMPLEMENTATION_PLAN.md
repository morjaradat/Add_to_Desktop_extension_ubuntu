### Implementation Plan: Nautilus "Add to Desktop" Extension

This plan outlines the steps to create a robust and feature-rich Nautilus extension for adding files to the desktop.

#### Part 1: Foundational Architecture

- [x] **Project Setup**:
    - [x] Create the directory structure for the project.
    - [x] Initialize a `git` repository.
- [x] **Frontend: `nautilus-python` Extension**:
    - [x] Create the `add-to-desktop.py` extension file.
    - [x] Implement the `Nautilus.MenuProvider` interface.
    - [x] Implement `get_file_items` to add the "Add to Desktop" menu item, ensuring it's non-blocking.
    - [x] Implement the `on_activate` callback to send file URIs to the background service via D-Bus.
- [x] **Backend: D-Bus Service**:
    - [x] Create the `linker-service.py` for the background service.
    - [x] Implement a `Gio.Application` to manage the service lifecycle.
    - [x] Define and expose a D-Bus method to receive file URIs from the frontend.

#### Part 2: Core Logic and File Operations

- [x] **Symbolic Link Creation**:
    - [x] Implement the core logic to create symbolic links using `Gio.File.make_symbolic_link_async` for asynchronous, non-blocking I/O.
- [x] **Edge Case Handling**:
    - [x] **Desktop Path**: Dynamically get the user's desktop directory using `GLib.get_user_special_dir`.
    - [x] **Name Conflicts**: Implement a race-free loop to handle existing filenames by appending a counter (e.g., `file (1).txt`).
    - [x] **Permissions**: Use a `try...except` block to catch `GLib.Error` for permission-denied errors (EAFP).
    - [x] **Complex Paths**: Ensure full Unicode support by using `Gio.File` and `GLib.build_filenamev`.

#### Part 3: Performance and User Experience

- [x] **Concurrency**:
    - [x] Use `asyncio.gather` to handle multiple file selections concurrently, processing them in parallel.
- [x] **User Notifications**:
    - [x] Use `Gio.Application.send_notification` to provide feedback to the user.
    - [x] Send notifications for success, partial success, and failure scenarios.
- [x] **"Undo" Functionality**:
    - [x] Store the paths of newly created links in the background service.
    - [x] Add an "Undo" button to the success notification using `notification.add_button`.
    - [x] Implement the "undo" action to delete the created links and withdraw the notification.
- [x] **Internationalization (i18n)**:
    - [x] Wrap all user-facing strings in `gettext` calls (`_()`).
    - [x] Set up the necessary files for translation (`.pot`, `.po`).

#### Part 4: Packaging and Distribution

- [x] **Installation Script**:
    - [x] Create a `Makefile` or `setup.py` to install all components to the correct system directories.
- [x] **Service Files**:
    - [x] Create the `org.my.desktop_linker.desktop` file for the `Gio.Application`.
    - [x] Create the `org.my.desktop_linker.service` file for D-Bus activation.
- [x] **Documentation**:
    - [x] Create a `README.md` with installation and usage instructions.