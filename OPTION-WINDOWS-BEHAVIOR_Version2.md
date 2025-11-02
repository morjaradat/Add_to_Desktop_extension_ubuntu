# Windows Behavior: Always Create Shortcuts (Allow Duplicates)

This implementation mimics Windows "Send to Desktop" behavior by always creating shortcuts, even if one already exists for the same file.

## Features:
- ✅ Always creates shortcuts when requested
- ✅ Allows multiple shortcuts to the same file
- ✅ Simple and predictable behavior
- ✅ Handles filename conflicts with numbering
- ⚠️ Can create duplicate shortcuts (like Windows)

## Installation:

Replace your `src/linker-service.py` with this code:

```python
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib
import sys
import os

dbus_interface = """
<node>
    <interface name='org.my.desktop_linker'>
        <method name='CreateLinks'>
            <arg type='as' name='uris' direction='in'/>
        </method>
    </interface>
</node>
"""

class LinkerService(Gio.Application):
    def __init__(self):
        super().__init__(application_id='org.my.desktop_linker',
                         flags=Gio.ApplicationFlags.IS_SERVICE)
        self.connect('activate', self.on_activate)
        self.hold()
        self.last_created_links = []

    def on_activate(self, *args, **kwargs):
        print("Linker service activated")

    def do_dbus_register(self, connection, object_path):
        interface_info = Gio.DBusNodeInfo.new_for_xml(dbus_interface).interfaces[0]
        connection.register_object(object_path, interface_info, self.dbus_method_call, None, None)
        return True

    def dbus_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        if method_name == 'CreateLinks':
            uris = parameters.get_child_value(0).get_strv()
            self.create_links(uris)
            invocation.return_value(None)

    def get_desktop_dir(self):
        return GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)

    def create_link_for_file(self, source_file, desktop_path):
        source_path = source_file.get_path()
        basename = source_file.get_basename()
        dest_path = os.path.join(desktop_path, basename)
        counter = 0

        while True:
            try:
                # Always try to create symlink (no duplicate checking)
                os.symlink(source_path, dest_path)
                return dest_path
            except FileExistsError:
                # File or shortcut with this name exists, add numbering
                counter += 1
                name_parts = basename.rsplit('.', 1)
                stem = name_parts[0]
                ext = f".{name_parts[1]}" if len(name_parts) > 1 else ""

                if counter > 1:
                    # Remove previous counter to avoid "file (1) (2).txt"
                    stem = stem.rsplit(' (', 1)[0]

                new_name = f"{stem} ({counter}){ext}"
                dest_path = os.path.join(desktop_path, new_name)
            except Exception as err:
                raise err

    def create_links(self, uris):
        desktop_dir = self.get_desktop_dir()
        if not desktop_dir:
            self.send_error_notification("Could not find desktop directory")
            return

        success_count = 0
        error_count = 0
        self.last_created_links = []
        
        for uri in uris:
            try:
                source_file = Gio.File.new_for_uri(uri)
                result = self.create_link_for_file(source_file, desktop_dir)
                success_count += 1
                self.last_created_links.append(result)
            except Exception as e:
                error_count += 1
                print(f"Error creating link: {e}")

        # Send appropriate notifications
        if success_count > 0:
            self.send_success_notification(success_count)
        
        if error_count > 0:
            self.send_error_notification(f"{error_count} links failed.")

    def send_success_notification(self, count):
        notification = Gio.Notification.new(f"{count} items added to Desktop")
        notification.add_button("Undo", "app.undo")
        self.send_notification("links-created", notification)

    def send_error_notification(self, message):
        notification = Gio.Notification.new("Error Creating Shortcuts")
        notification.set_body(message)
        notification.set_priority(Gio.NotificationPriority.HIGH)
        self.send_notification("links-error", notification)

    def on_undo_activate(self, action, param):
        if not self.last_created_links:
            return

        for path in self.last_created_links:
            try:
                os.unlink(path)
            except Exception as e:
                print(f"Error deleting link {path}: {e}")

        self.last_created_links = []
        self.withdraw_notification("links-created")

if __name__ == '__main__':
    service = LinkerService()
    action = Gio.SimpleAction.new("undo", None)
    action.connect("activate", service.on_undo_activate)
    service.add_action(action)
    service.run(sys.argv)
```

## How to apply:

```bash
cd ~/Desktop/add-to-desktop-extension
make uninstall
make install
nautilus -q
```

## Behavior Examples:

### Example 1: Same file added multiple times
```
1. Right-click "document.pdf" → Add to Desktop
   Result: Creates "document.pdf" ✅

2. Right-click same "document.pdf" → Add to Desktop
   Result: Creates "document (1).pdf" ✅

3. Right-click same "document.pdf" → Add to Desktop
   Result: Creates "document (2).pdf" ✅
```

### Example 2: Renamed shortcut
```
1. Desktop has "important.pdf" → points to /home/mor/docs/report.pdf
2. Right-click /home/mor/docs/report.pdf → Add to Desktop
   Result: Creates "report.pdf" ✅ (Doesn't detect the renamed one)
```

### Example 3: Different files with same name
```
1. Desktop has shortcut to /home/mor/docs/file.txt
2. Right-click /home/mor/downloads/file.txt → Add to Desktop
   Result: Creates "file (1).txt" ✅
```

### Example 4: Real file exists with same name
```
1. Desktop has real file "photo.jpg"
2. Right-click /home/mor/pictures/photo.jpg → Add to Desktop
   Result: Creates "photo (1).jpg" ✅
```

### Example 5: Accidental double-click
```
User accidentally clicks "Add to Desktop" twice quickly
Result: Creates 2 shortcuts ⚠️
- "document.pdf"
- "document (1).pdf"
```

## Key Differences from Option A:

| Scenario | Option A (Smart) | Windows Behavior |
|----------|-----------------|------------------|
| Add same file twice | Skips, shows notification | Creates duplicate with (1) |
| Renamed shortcut exists | Detects and skips | Creates another one |
| Accidental double-click | Protected, creates only 1 | Creates duplicates |
| Desktop cleanliness | Very clean | Can get cluttered |

## Advantages:
- ✅ Simple and predictable
- ✅ Matches Windows user expectations
- ✅ User has full control (can create as many as they want)
- ✅ No "smart" behavior to confuse users

## Disadvantages:
- ⚠️ Can create many duplicate shortcuts
- ⚠️ Desktop can get cluttered
- ⚠️ No protection against accidental clicks
- ⚠️ Wastes space with redundant shortcuts

## Testing:

Test the behavior:
```bash
# Test 1: Add same file 3 times
# Should create: file.pdf, file (1).pdf, file (2).pdf

# Test 2: Rename first shortcut, add again
# Should create new shortcut with original name

# Test 3: Quick double-click
# Should create 2 shortcuts
```

## When to use this:

Choose this option if:
- You want to match Windows behavior exactly
- Your users are coming from Windows
- You want simple, predictable behavior
- You don't mind potential desktop clutter
- You prefer user control over automation

## Recommendation:

While this matches Windows behavior, **Option A is recommended** for Linux users because:
- Linux users value efficiency and clean desktops
- Prevents common mistakes
- More intelligent behavior
- Better user experience overall
```