import gi, random
from gi.repository import Gtk, Adw
from .utils import soup_get, parse_json
from .search_page import SearchPage
from .theme_page import ThemePage

class CategoryBox(Gtk.FlowBox):
    def __init__(self, view):
        super().__init__(margin_start=12, margin_end=12, selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=3, row_spacing=3, column_spacing=3, valign=Gtk.Align.START, homogeneous=True)
        self.view = view
        self.theme_page = ThemePage(view)

        icons = [
            "shell-symbolic",
            "icon-symbolic",
            "interface-symbolic",
            "cursor-symbolic",
            "wallpaper-symbolic",
            "search-symbolic",
        ]

        categories = [
            "GNOME Shell",
            "Icons",
            "GTK3/4",
            "Cursors",
            "Wallpapers",
            "Search",
        ]

        for category, icon_name in zip(categories, icons):
            self.insert(self.make_category(category, icon_name), -1)

    def make_category(self, label_text, icon_name):
        box = Gtk.Box(
            spacing=10,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
            halign=Gtk.Align.CENTER
        )

        icon = Gtk.Image(icon_name=icon_name, pixel_size=20)

        label = Gtk.Label(label=_(label_text), wrap=True, justify=Gtk.Justification.CENTER)
        label.add_css_class("title-4")

        box.append(icon)
        box.append(label)

        button = Gtk.Button(child=box, hexpand=True, vexpand=True)
        button.connect("clicked", self.on_category_clicked, label_text)
        button.add_css_class(icon_name)
        return button

    def on_category_clicked(self, button, category):
        if(category == "Search"):
            search_page = SearchPage()
            self.view.add(search_page)
            self.view.push(search_page)
        else:
            self.theme_page.category = category
            self.theme_page.make_new_page()
            self.view.push(self.theme_page)

class MainPage(Adw.NavigationPage):
    def __init__(self, view):
        super().__init__(tag="main_page")
        content_box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=18, margin_bottom=25)
        content_box.append(Adw.Clamp(maximum_size=840, child=CategoryBox(view)))

        for topic in ["Curated", "New & Updated"]:
            content_box.append(Gtk.Separator())
            title = Gtk.Label(label=_(topic), halign=Gtk.Align.START, margin_start=25)
            title.add_css_class("title-2")
            content_box.append(title)

            if(topic == "Curated"):
                curated_ids = ["2299211", "1681315", "1477945", "1166289", "1359276", "1598493", "1197198", "1366182", "1499429"]
                self.curated_flowbox = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True, column_spacing=12, min_children_per_line=9, max_children_per_line=9)
                self.curated_flowbox.page = view
                side_scroll_box = Gtk.ScrolledWindow(child=self.curated_flowbox, height_request=420)
                side_scroll_box.add_css_class("view")
                content_box.append(side_scroll_box)
                for item in curated_ids:
                    soup_get(self.get_url(item), self.make_curated)
            if(topic == "New & Updated"):
                url = "https://api.opendesktop.org/ocs/v1/content/data/?format=json&page=0&pagesize=10&categories=134x386x366x107x261&sortmode=new"
                self.new_flowbox = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True, column_spacing=12, min_children_per_line=9, max_children_per_line=9)
                self.new_flowbox.page = view
                side_scroll_box = Gtk.ScrolledWindow(child=self.new_flowbox, height_request=420)
                side_scroll_box.add_css_class("view")
                content_box.append(side_scroll_box)
                soup_get(url, self.make_new)

        scroller = Gtk.ScrolledWindow(child=content_box, vexpand=True, hexpand=True)
        self.set_child(scroller)

    def make_curated(self, response):
        parse_json(response, self.curated_flowbox)

    def make_new(self, response):
        parse_json(response, self.new_flowbox)

    def get_url(self, id):
        return f"https://api.opendesktop.org/ocs/v1/content/data/{id}?format=json"




