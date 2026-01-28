import gi
from gi.repository import Gtk, Adw
from .theme_cell_flowbox import ThemeCellFlowbox

categories = {
    "GNOME Shell": "https://api.opendesktop.org/ocs/v1/content/data/?categories=134&sortmode=",
    "Icons": "https://api.opendesktop.org/ocs/v1/content/data/?categories=386&sortmode=",
    "GTK3/4": "https://api.opendesktop.org/ocs/v1/content/data/?categories=366&sortmode=",
    "Cursors": "https://api.opendesktop.org/ocs/v1/content/data/?categories=107&sortmode=",
    "Wallpapers": "https://api.opendesktop.org/ocs/v1/content/data/?categories=261&sortmode="
}

class ThemePage(Adw.NavigationPage):
    current_page = 0

    def __init__(self, view):
        super().__init__()
        content_box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=18)
        button_box = Adw.ToggleGroup(hexpand=True, halign=Gtk.Align.CENTER)
        button_box.connect("notify::active", self.on_type_changed)
        content_box.append(button_box)

        for sortmode in ["Most Downloaded", "Alphabetical", "Highest Rated", "Recently Updated"]:
            button = Adw.Toggle(label=_(sortmode), name=sortmode)
            button_box.add(button)

        self.theme_flowbox = ThemeCellFlowbox()
        self.theme_flowbox.page = view
        next_button = Gtk.Button(label=_("Next Page"), hexpand=True, halign=Gtk.Align.CENTER, width_request=350, margin_top=24, margin_bottom=24)
        next_button.connect("clicked", self.next_page)
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        theme_box.append(self.theme_flowbox)
        theme_box.append(next_button)
        scroller = Gtk.ScrolledWindow(child=theme_box, hexpand=True, vexpand=True)
        content_box.append(scroller)
        self.set_child(content_box)

    def next_page(self, button):
        self.current_page += 1
        self.theme_action("add_page", categories[self.category] + self.selected + f"&page={self.current_page}");

    def make_new_page(self):
        self.theme_action("new_page", categories[self.category] + "down")

    def theme_action(self, action, url):
        if(action == "new_page"):
            self.current_page = 0
            self.theme_flowbox.remove_all()
        self.theme_flowbox.build_cells(url)

    def on_type_changed(self, group, button):
        label = group.get_active_name()
        match(label):
            case("Most Downloaded"):
                self.selected = "down"
            case("Alphabetical"):
                self.selected = "alpha"
            case("Highest Rated"):
                self.selected = "high"
            case("Recently Updated"):
                self.selected = "new"
        self.theme_action("new_page", categories[self.category] + self.selected)



