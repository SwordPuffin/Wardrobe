import gi
from gi.repository import Gtk, Adw
from .utils import soup_get, parse_json
from .theme_cell_flowbox import ThemeCellFlowbox

category_map = {
        134: 0, 386: 1, 199: 1, 132: 1, 366: 2, 135: 2, 136: 2,
        107: 3, 300: 4, 312: 4, 261: 4, 299: 4, 283: 4, 360: 4
    }

class SearchPage(Adw.NavigationPage):
    def __init__(self):
        super().__init__(tag="search_page")
        content_box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=18)
        search_box = Gtk.Box()
        search_bar = Gtk.SearchEntry(placeholder_text=_("Search themes"), hexpand=True, margin_start=5, margin_end=5)
        search_bar.connect("activate", self.search)
        filter_button = Gtk.Button(icon_name="filter-symbolic", valign=Gtk.Align.CENTER)
        filter_button.add_css_class("circular")

        self.filter_popover = Gtk.Popover()
        self.filter_popover.set_has_arrow(True)
        self.filter_popover.set_autohide(True)
        self.filter_popover.set_parent(filter_button)
        self.make_filter()
        filter_button.connect("clicked", self.toggle_filter_popover)

        search_box.append(search_bar); search_box.append(filter_button)
        content_box.append(Adw.Clamp(maximum_size=520, child=search_box))
        content_box.append(Gtk.Separator())

        self.search_flowbox = ThemeCellFlowbox()
        self.search_flowbox.page = self
        self.search_icon = Gtk.Image(icon_name="search-symbolic", pixel_size=160, valign=Gtk.Align.END, vexpand=True)
        self.search_icon.add_css_class("dimmed")
        scroller = Gtk.ScrolledWindow(child=self.search_flowbox, vexpand=True, hexpand=True)
        content_box.append(self.search_icon)
        content_box.append(scroller)
        self.set_child(content_box)

    def toggle_filter_popover(self, button):
        if(self.filter_popover.get_visible()):
            self.filter_popover.popdown()
        else:
            self.filter_popover.popup()

    def make_filter(self):
        def on_filter_changed(button):
            if(button.id in self.active_filters):
                self.active_filters.remove(button.id)
                button.remove_css_class("suggested-action")
            else:
                self.active_filters.add(button.id)
                button.add_css_class("suggested-action")
        activated = {134, 386, 366, 107, 261}

        filter_flowbox = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            max_children_per_line=2,
            column_spacing=6,
            row_spacing=6,
            margin_top=6,
            margin_bottom=6,
            margin_start=6,
            margin_end=6
        )

        for category, id in zip(
            [_("Gnome Shell"), _("Icons"), _("GTK3/4"), _("Cursors"), _("Wallpapers")],
            activated
        ):
            button = Gtk.Button(label=category)
            button.id = id
            button.add_css_class("pill")
            button.connect("clicked", on_filter_changed)
            filter_flowbox.append(button)

        self.filter_popover.set_child(filter_flowbox)

    def search(self, entry):
        url = f"https://api.opendesktop.org/ocs/v1/content/data/?format=json&search={entry.get_text()}&page=0&pagesize=10&categories=134x386x366x107x261"
        self.search_icon.set_visible(False)
        self.search_flowbox.remove_all()
        soup_get(url, self.list_search_items)

    def list_search_items(self, reponse):
        parse_json(reponse, self.search_flowbox)



