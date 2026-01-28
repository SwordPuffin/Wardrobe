import gi, asyncio
from gi.repository import Gtk, GLib, Adw
from .utils import soup_get, parse_xml

class ThemeCellFlowbox(Gtk.FlowBox):
    def __init__(self):
        super().__init__(selection_mode=Gtk.SelectionMode.NONE, hexpand=True, vexpand=True, homogeneous=True, column_spacing=12, row_spacing=12, halign=Gtk.Align.CENTER)

    def add_themes(self, response):
        parse_xml(response, self)

    def build_cells(self, url):
        soup_get(url, self.add_themes)


