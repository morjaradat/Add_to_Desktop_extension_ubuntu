import os
from gi.repository import Nautilus, GObject, Gio, GLib

class AddToDesktopExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()

    def get_file_items(self, files):
        if not files:
            return

        item = Nautilus.MenuItem(
            name="AddToDesktopExtension::Add",
            label="Add to Desktop",
            tip="Add a symbolic link to the desktop",
        )
        item.connect("activate", self.on_activate, files)

        return [item]

    def on_activate(self, menu, files):
        uris = [f.get_uri() for f in files]
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            bus.call_sync(
                "org.my.desktop_linker",
                "/org/my/desktop_linker",
                "org.my.desktop_linker",
                "CreateLinks",
                GLib.Variant("(as)", [uris]),
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error as e:
            print(f"D-Bus call failed: {e.message}")
