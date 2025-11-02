# Option A: Skip Duplicates (Smart Behavior - Recommended)

This implementation prevents duplicate shortcuts by checking if a symlink to the same target file already exists on the desktop.

## Features:
- ✅ Prevents duplicate shortcuts to the same file
- ✅ Keeps desktop clean and organized
- ✅ Detects existing shortcuts even if renamed
- ✅ Shows notification when shortcuts already exist
- ✅ More intelligent than Windows behavior

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

    def shortcut_already_exists(self, source_path, desktop_path):
        """Check if a symlink to this exact file already exists on desktop"""
        # Get absolute path of source
        source_abs = os.path.abspath(source_path)
        
        # Check all files on desktop
        try:
            for item in os.listdir(desktop_path):
                item_path = os.path.join(desktop_path, item)
                
                # Check if it's a symlink
                if os.path.islink(item_path):
                    # Get what the symlink points to
                    link_target = os.readlink(item_path)
                    
                    # Convert to absolute path if it's relative
                    if not os.path.isabs(link_target):
                        link_target = os.path.abspath(os.path.join(desktop_path, link_target))
                    
                    # Compare with source
                    if os.path.abspath(link_target) == source_abs:
                        return True, item_path
        except Exception as e:
            print(f"Error checking existing shortcuts: {e}")
        
        return False, None

    def create_link_for_file(self, source_file, desktop_path):
        source_path = source_file.get_path()
        
        # Check if shortcut already exists
        exists, existing_path = self.shortcut_already_exists(source_path, desktop_path)
        if exists:
            print(f"Shortcut already exists: {existing_path}")
            return None  # Return None to indicate it was skipped
        
        basename = source_file.get_basename()
        dest_path = os.path.join(desktop_path, basename)
        counter = 0

        while True:
            try:
                # Use os.symlink instead of Gio
                os.symlink(source_path, dest_path)
                return dest_path
            except FileExistsError:
                counter += 1
                name_parts = basename.rsplit('.', 1)
                stem = name_parts[0]
                ext = f".{name_parts[1]}" if len(name_parts) > 1 else ""

                if counter > 1:
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
        skipped_count = 0
        self.last_created_links = []
        
        for uri in uris:
            try:
                source_file = Gio.File.new_for_uri(uri)
                result = self.create_link_for_file(source_file, desktop_dir)
                
                if result is None:
                    # Shortcut already exists, skip it
                    skipped_count += 1
                else:
                    success_count += 1
                    self.last_created_links.append(result)
            except Exception as e:
                error_count += 1
                print(f"Error creating link: {e}")

        # Send appropriate notifications
        if success_count > 0:
            self.send_success_notification(success_count)
        
        if skipped_count > 0:
            self.send_skipped_notification(skipped_count)
        
        if error_count > 0:
            self.send_error_notification(f"{error_count} links failed.")

    def send_success_notification(self, count):
        notification = Gio.Notification.new(f"{count} items added to Desktop")
        notification.add_button("Undo", "app.undo")
        self.send_notification("links-created", notification)

    def send_skipped_notification(self, count):
        message = f"{count} item{'s' if count > 1 else ''} already on Desktop"
        notification = Gio.Notification.new(message)
        notification.set_body("Shortcut already exists")
        self.send_notification("links-skipped", notification)

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

### Example 1: Same file added twice
```
1. Right-click "document.pdf" → Add to Desktop
   Result: Creates "document.pdf" shortcut ✅

2. Right-click same "document.pdf" → Add to Desktop
   Result: Shows "1 item already on Desktop" ⚠️ (Skipped)
```

### Example 2: Renamed shortcut
```
1. Desktop has "important.pdf" → points to /home/mor/docs/report.pdf
2. Right-click /home/mor/docs/report.pdf → Add to Desktop
   Result: Shows "1 item already on Desktop" ⚠️ (Detects renamed shortcut)
```

### Example 3: Different files with same name
```
1. Desktop has shortcut to /home/mor/docs/file.txt
2. Right-click /home/mor/downloads/file.txt → Add to Desktop
   Result: Creates "file (1).txt" ✅ (Different file, different shortcut)
```

### Example 4: Real file exists with same name
```
1. Desktop has real file "photo.jpg"
2. Right-click /home/mor/pictures/photo.jpg → Add to Desktop
   Result: Creates "photo (1).jpg" shortcut ✅
```

## Advantages:
- 🎯 Prevents accidental duplicates
- 🧹 Keeps desktop clean
- 🧠 Intelligent duplicate detection
- 📢 Clear user feedback via notifications
- ⚡ Efficient - only creates what's needed

## Testing:

Test all scenarios:
```bash
# Test 1: Add same file twice
# Should skip on second attempt

# Test 2: Rename shortcut then add original again
# Should detect and skip

# Test 3: Add two different files with same name
# Should create both with numbering
```
```