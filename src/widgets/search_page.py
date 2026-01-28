import gi
from gi.repository import Gtk, Adw
from .utils import soup_get, parse_xml

class SearchPage(Adw.NavigationPage):
    def __init__(self):
        super().__init__(tag="search_page")
        print("hi")
        content_box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=18)
        search_bar = Gtk.Entry(placeholder_text=_("Search Themes..."), hexpand=True, margin_end=60, margin_start=60, margin_top=20)
        search_bar.connect("activate", self.search)
        content_box.append(search_bar)
        separator = Gtk.Separator()
        content_box.append(separator)
        self.search_flowbox = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, hexpand=True, halign=Gtk.Align.CENTER, vexpand=True, homogeneous=True, column_spacing=12, row_spacing=24, max_children_per_line=3)
        self.search_flowbox.page = self
        self.search_icon = Gtk.Image(icon_name="search-symbolic", pixel_size=160, valign=Gtk.Align.END, vexpand=True)
        self.search_icon.add_css_class("dimmed")
        scroller = Gtk.ScrolledWindow(child=self.search_flowbox, vexpand=True, hexpand=True)
        content_box.append(self.search_icon)
        content_box.append(scroller)
        self.set_child(content_box)

    def search(self, entry):
        url = f"https://api.opendesktop.org/ocs/v1/content/data/?search={entry.get_text()}&page=0&pagesize=10&categories=134x386x366x107x261"
        self.search_icon.set_visible(False)
        self.search_flowbox.remove_all()
        soup_get(url, self.list_search_items)

    def list_search_items(self, reponse):
        parse_xml(reponse, self.search_flowbox)



