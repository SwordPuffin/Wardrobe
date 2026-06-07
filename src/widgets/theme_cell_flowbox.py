import gi, json
from gi.repository import Gtk, GLib, Adw
from .utils import soup_get, parse_json

class ThemeCellFlowbox(Gtk.FlowBox):
    def __init__(self):
        super().__init__(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True, column_spacing=12, row_spacing=12, halign=Gtk.Align.CENTER, margin_bottom=12)
        
    def add_themes(self, response):
        if(isinstance(response, str)):
            data = json.loads(response)
        else:
            data = response
                
        parse_json(response, self)
        self.next_page_button.set_visible(True)
        self.next_page_button.set_sensitive(True)
        self.next_page_button.set_label(_("Next Page"))
        if(hasattr(self, "is_search_flowbox") and len(data.get("data", [])) < 10):
            self.next_page_button.set_visible(False)
            self.search_icon.set_visible(True)
            self.search_icon.set_from_icon_name("list-remove-symbolic")

    def build_cells(self, url):
        soup_get(url, self.add_themes)
        
    def remove_all(self):
        for button in self:
            button.get_first_child().get_first_child().destroy_cell()
        super().remove_all()


