# window.py
#
# Copyright 2025 Nathan Perlman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import xml.etree.ElementTree as ET, gi, webbrowser, shutil, os, ast, json, re, copy

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")
gi.require_version("Xdp", "1.0")
gi.require_version("XdpGtk4", "1.0")
from gi.repository import Gtk, GLib, Gio, Gdk, Adw, Soup, Xdp, XdpGtk4
from datetime import datetime
from .utils import css, arrange_folders

@Gtk.Template(resource_path='/io/github/swordpuffin/wardrobe/window.ui')
class WardrobeWindow(Adw.ApplicationWindow):

    __gtype_name__ = 'WardrobeWindow'
    page = Gtk.Template.Child()
    split_view = Gtk.Template.Child()
    tab_buttons = Gtk.Template.Child()
    menus = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    search_box = Gtk.Template.Child()
    session = Soup.Session()
    if(GLib.getenv("HOST_XDG_DATA_HOME") == None):
        GLib.setenv("HOST_XDG_DATA_HOME", os.path.join(GLib.getenv("HOME"), ".local", "share"), True)
    data_dir = GLib.getenv("HOST_XDG_DATA_HOME") #Should be ~/.local/share
    picture_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES) #Typically ~/Pictures
    folders = {
        0: f"{data_dir}/themes/wardrobe-installs",
        1: f"{data_dir}/icons/wardrobe-installs",
        2: f"{data_dir}/themes/wardrobe-installs",
        3: f"{data_dir}/icons/wardrobe-installs",
        4: f"{picture_dir}/",
        5: f"{GLib.get_user_data_dir()}"
    }
    selected = "down"
    activated = None
    category_box = None
    search_url = None
    save_function = None
    currently_loading = False
    error_label = Gtk.Label(label=_("No results found :("), hexpand=True, halign=Gtk.Align.CENTER)
    error_label.add_css_class("error"); error_label.add_css_class("title-4")

    #Stored at ~/.var/app/io.github.swordpuffin.wardrobe/data/downloaded.txt
    try:
        downloaded = dict(ast.literal_eval(open(f"{folders[5]}/downloaded.txt", "r").read()))
    except Exception:
        downloaded = dict()

    if(not os.path.exists(f"{folders[5]}/prefs.json")):
        with open(f"{folders[5]}/prefs.json", "w") as file:
            json.dump({"cell_count": 8, "carousel_image_count": 3}, file, indent=4)

    with open(f"{folders[5]}/prefs.json", "r") as file:
        data = json.load(file)

    cell_count = data["cell_count"]
    carousel_image_count = data["carousel_image_count"]

    current_page = 0
    categories = [
        {"name": "Shell Themes", "url": "https://api.opendesktop.org/ocs/v1/content/data/?categories=134&sortmode="},
        {"name": "Icon Themes", "url": "https://api.opendesktop.org/ocs/v1/content/data/?categories=386&sortmode="},
        {"name": "Gtk3/4 Themes", "url": "https://api.opendesktop.org/ocs/v1/content/data/?categories=366&sortmode="},
        {"name": "Cursors", "url": "https://api.opendesktop.org/ocs/v1/content/data/?categories=107&sortmode="},
        {"name": "Wallpapers", "url": "https://api.opendesktop.org/ocs/v1/content/data/?categories=261&sortmode="}
    ]
    # shell_settings = Gio.Settings(schema_id="org.gnome.shell.extensions.user-theme")
    # print(shell_settings.get_string("name"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8')) #fetches the css from utils.py.
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self.set_default_size(800, 600)
        icons = ["shell-symbolic", "app-symbolic", "interface-symbolic", "cursor-symbolic", "wallpaper-symbolic", "search-symbolic"]
        for i, label in zip(range(7), ["GNOME Shell", "Icon", "Interface", "Cursor", "Wallpaper", "Search"]):
            row = Adw.ActionRow(title=(_(label)), activatable=True)
            icon = Gtk.Image(pixel_size=22).new_from_icon_name(icons[i])
            if(i == 0):
                self.activated = row
            elif(i == 5):
                search = Adw.EntryRow(title="Search", show_apply_button=False, name=str(i), margin_start=12, margin_end=12)
                search.add_css_class("card")
                self.search_box.append(search)
                search.connect("entry-activated", self.on_search)
                continue
            row.add_prefix(icon)
            row.set_name(str(i))
            row.connect("activated", self.on_tab_changed)
            self.tab_buttons.append(row)

        self.menus.connect('notify::selected-item', self.on_type_changed)
        items = Gtk.StringList()
        for item in ["Most Downloaded", "Alphabetical", "Highest Rated", "New"]:
            items.append(item)
        self.menus.set_model(items)
        self.current_page = 0

    def category_index(self, index):
        category_map = {
            134: 0, 386: 1, 132: 1, 366: 2, 135: 2, 136: 2,
            107: 3, 261: 4, 299: 4, 360: 4
        }
        return category_map.get(int(index), int(index))

    def soup_get(self, api_url, func):
        session = Soup.Session()
        message = Soup.Message.new("GET", api_url)
        session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, None, self.on_response, func)

    def on_response(self, session, result, func):
        response_bytes = session.send_and_read_finish(result)
        try:
            response_text = response_bytes.get_data().decode()
        except(Exception):
            response_text = response_bytes.get_data()
        func(response_text)

    def on_search(self, search_entry):
        self.query = search_entry.get_text().strip()
        if(self.query):
            self.menus.set_sensitive(False)
            print(f"Search for: {self.query}")
            self.current_page = 0
            self.search_url = f"https://api.opendesktop.org/ocs/v1/content/data/?search={self.query}&page=0&pagesize={self.cell_count}&categories=134x386x366x107x261"
            self.on_tab_changed(search_entry)

    def fetch_themes(self, index, page, action):
        if(index < 5):
            category = self.categories[self.category_index(index)]
            api_url = f"{category['url']}{self.selected}&pagesize={self.cell_count}&page={page}"
        else:
            api_url = self.search_url
        if(action == "clear"):
            self.category_box = Gtk.Box(margin_top=10, margin_bottom=10, margin_start=15, margin_end=15, orientation=Gtk.Orientation.VERTICAL)
            self.current_page = 0
            while(self.category_box.get_first_child() is not None):
                self.category_box.remove(self.category_box.get_first_child())
        self.grab_theme_params(api_url)

    def grab_theme_params(self, api_url):
        if(self.carousel_image_count > 0):
            self.loading(True)
        print("start loading xml")
        self.soup_get(api_url, self.grab_theme_params_finish)
        print("finished loading xml")

    def grab_theme_params_finish(self, response):
        flowbox_in_theme_grid = False
        scrollbox = Gtk.ScrolledWindow(vexpand=True)
        for child in self.category_box:
            if(str(type(child)) == "<class 'gi.repository.Gtk.FlowBox'>"):
                theme_grid = child
                flowbox_in_theme_grid = True
            elif(str(type(child)) == "<class 'gi.repository.Gtk.Button'>" or str(type(child)) == "<class 'gi.repository.Gtk.Label'>"):
                self.category_box.remove(child)
        if(not flowbox_in_theme_grid):
            theme_grid = Gtk.FlowBox(row_spacing=12, max_children_per_line=5, selection_mode=Gtk.SelectionMode.NONE)
            scrollbox.set_child(self.category_box)
            self.category_box.append(theme_grid)
            if(self.page.get_first_child() is not None):
                self.page.remove(self.page.get_first_child())
            self.page.append(scrollbox)

        root = ET.fromstring(response)
        meta = root.findall(".//meta")
        if(int(meta[0].find("itemsperpage").text) == 0 and theme_grid.get_first_child() is None):
            self.no_results_found(self.category_box)
            return
        elif(int(meta[0].find("itemsperpage").text) == 0 and theme_grid.get_first_child() is not None):
            self.loading(False)
            return
        for item in root.findall(".//content"):
            title = item.find("name").text if item.find("name") is not None else "Unknown"
            theme_url = item.find("detailpage").text if item.find("detailpage") is not None else ""
            creator = item.find("personid").text if item.find("personid") is not None else "Unknown"
            #I don't know why but I can't get downloads to always work unless I overbuild the security
            if(item.find("downloads") is not None):
                downloads = item.find("downloads").text if item.find("downloads").text is not None else "0"
            else:
                downloads = "0"
            downloads = "{:,}".format(int(downloads))
            description = item.find("description").text if item.find("description") is not None else ""
            last_update = item.find("changed").text if item.find("changed") is not None else ""
            rating = int(item.find("score").text) / 10 if item.find("score") is not None else 0
            typeid = item.find("typeid").text if item.find("typeid") is not None else 0 #Some items don't have typeids for some reason
            download_links = []
            download_names = []
            for i in range(1, 25):  # Maximum of 24 download links
                if(item.find(f"downloadlink{i}") is None):
                    break
                download_link = item.find(f"downloadlink{i}")
                download_name = item.find(f"downloadname{i}")
                if(download_link.text):
                    download_links.append(download_link.text)
                    download_names.append(download_name.text)
            image_links = []
            for z in range(1, self.carousel_image_count + 1):
                if(item.find(f"previewpic{z}") is not None):
                    image_links.append(item.find(f"previewpic{z}").text)
                else:
                    break
            self.add_theme_to_list(theme_grid, title, creator, downloads, theme_url, download_links, download_names, description, self.category_index(typeid), rating, image_links, last_update)
        if(int(meta[0].find("itemsperpage").text) < self.cell_count):
            self.loading(False)
            return

        adjustment = scrollbox.get_vadjustment()
        adjustment.connect("value-changed", self.scroll_to_bottom, scrollbox)

    def no_results_found(self, box):
        self.loading(False)
        if(self.page.get_first_child() is not None):
            self.page.remove(self.page.get_first_child())
        self.page.append(self.error_label)

    def scroll_to_bottom(self, adjustment, scrollbox):
        if(self.currently_loading):
            return
        scroll_value = adjustment.get_value()
        page_size = adjustment.get_page_size()
        upper = adjustment.get_upper()

        if(scroll_value + page_size >= upper - 1):
            self.current_page += 1
            vadj = self.category_box.get_parent().get_parent().get_vadjustment()
            if(int(self.activated.get_name()) != 5):
                self.fetch_themes(int(self.activated.get_name()), self.current_page, "_")
            else:
                url = f"https://api.opendesktop.org/ocs/v1/content/data/?search={self.query}&page={self.current_page}&pagesize={self.cell_count}&categories=134x386x366x107x261"
                self.grab_theme_params(url)
            GLib.idle_add(self.scroll_to_original_pos, self.category_box.get_parent().get_parent(), vadj.get_value()) #For vertical position in scrolled window to not reset

    def scroll_to_original_pos(self, scrolled_window, vadj):
        scrolled_window.get_vadjustment().set_value(vadj)

    def add_theme_to_list(self, theme_grid, title, creator, downloads, theme_url, download_links, download_names, description, index, rating, image_links, last_update):
        theme_box = Gtk.Box(hexpand=True, vexpand=True, orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.CENTER)

        label = Gtk.Label(label=_(title), justify=Gtk.Justification.LEFT, wrap=True, margin_start=12, margin_end=12)
        label.add_css_class("title-2")
        creator_label = Gtk.Label(label=(_("By: ")) + creator, justify=Gtk.Justification.LEFT, margin_bottom=12)
        creator_label.add_css_class("creator-title")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.START, spacing=10)
        label_box.append(label)
        label_box.append(creator_label)

        carousel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, visible=False)
        carousel = Adw.Carousel(height_request=315, allow_scroll_wheel=False, hexpand=True)
        carousel_container = Gtk.Box()
        carousel_container.append(carousel)
        carousel_box.prepend(carousel_container)
        indicator_box = Gtk.Box(margin_top=10, margin_bottom=10, spacing=12)
        for image in image_links:
            self.get_image_from_url(image, _, carousel, carousel_box)

        indicators = Adw.CarouselIndicatorDots(carousel=carousel, halign=Gtk.Align.CENTER)
        indicator_box.append(indicators)
        carousel_box.append(indicator_box)

        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.CENTER, spacing=10, margin_start=8, margin_end=8, margin_bottom=8)
        button_box.add_css_class("title-4")

        rating_box = Gtk.Button(child=Gtk.Label(label=_(str(rating)) + " ★"))
        if(rating >= 8):
            rating_box.add_css_class("success")
        elif(rating >= 6 and rating < 8):
            rating_box.add_css_class("warning")
        elif(rating < 6):
            rating_box.add_css_class("destructive-action")
        download_button = Gtk.Button(label=_("Download or Delete"))
        download_button.connect("clicked", self.download_item, download_links, download_names, index)
        download_button.add_css_class("accent")

        browser_button = Gtk.Button(label=_("View in Browser"), icon_name="web-browser-symbolic")
        browser_button.connect("clicked", self.on_view_button_clicked, theme_url)
        browser_button.add_css_class("suggested-action")
        top_box = Gtk.Box(spacing=10, hexpand=True, halign=Gtk.Align.CENTER)
        top_box.append(rating_box)
        top_box.append(download_button)
        top_box.append(browser_button)
        bottom_box = Gtk.Frame(halign=Gtk.Align.CENTER, hexpand=True, child=Gtk.Label(label=(_("Last updated: ")) + str(datetime.fromisoformat(last_update).date()) + (_("       Installs: ")) + downloads))
        bottom_box.add_css_class("extra-padding")
        button_box.append(top_box); button_box.append(bottom_box)

        if(len(re.sub(r'<.*?>', '', description)) > 100):
            text = re.sub(r'<.*?>', '', description)[:100] + (_("... (Click for more)"))
        else:
            text = re.sub(r'<.*?>', '', description)

        lines = text.splitlines()
        non_blank_lines = [line for line in lines if line.strip() != '']
        text = '\n'.join(non_blank_lines)

        description_label = Gtk.Button(margin_start=12, margin_end=12, margin_bottom=12, vexpand=True)
        description_label.set_child(Gtk.Label(label=text, wrap=True))
        description_label.connect("clicked", self.on_description_clicked,  re.sub(r'<.*?>', '', description))

        if(len(image_links) > 1):
            prev_button = Gtk.Button(icon_name="arrow-left-symbolic", valign=Gtk.Align.CENTER, halign=Gtk.Align.END, hexpand=True, margin_end=12, margin_start=12)
            prev_button.add_css_class("circular")
            next_button = Gtk.Button(icon_name="arrow-right-symbolic", valign=Gtk.Align.CENTER, halign=Gtk.Align.START, hexpand=True, margin_start=12, margin_end=12)
            next_button.add_css_class("circular")
            prev_button.connect("clicked", self.on_prev_clicked, carousel)
            next_button.connect("clicked", self.on_next_clicked, carousel)
            indicator_box.prepend(prev_button)
            indicator_box.append(next_button)
        elif(len(image_links) == 0):
            carousel.set_size_request(0, 0)
            label.set_size_request(-1, 125)
        if(self.carousel_image_count == 0):
            carousel_box.set_visible(True)

        carousel_box.append(label_box)
        carousel_box.append(button_box)
        carousel_box.append(description_label)
        theme_box.prepend(carousel_box)
        cell = Gtk.Frame(child=theme_box, valign=Gtk.Align.START); cell.add_css_class("card")
        clamp = Adw.Clamp(maximum_size=400, tightening_threshold=250, child=cell)
        theme_grid.insert(clamp, -1)

    def on_description_clicked(self, button, text):
        dialog = Gtk.MessageDialog(modal=True, transient_for=self, buttons=Gtk.ButtonsType.CLOSE)
        dialog.set_default_size(600, 600)
        scrolled_window=Gtk.ScrolledWindow(child=Gtk.Label(label=text, wrap=True, selectable=True), vexpand=True, hexpand=True, margin_start=8, margin_end=8)
        dialog.get_content_area().append(scrolled_window)
        dialog.connect("response", lambda d, r: dialog.destroy())
        dialog.show()

    def on_prev_clicked(self, button, carousel):
        index = carousel.get_position()
        if(index == 0):
            index = carousel.get_n_pages()
        carousel.scroll_to(carousel.get_nth_page(index - 1), 250)

    def on_next_clicked(self, button, carousel):
        index = carousel.get_position()
        if(index < carousel.get_n_pages() - 1):
            carousel.scroll_to(carousel.get_nth_page(index + 1), 250)
        else:
            index = 0
            carousel.scroll_to(carousel.get_nth_page(0), 250)

    def on_picture_clicked(self, gesture, n_press, x, y, image):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, buttons=Gtk.ButtonsType.CLOSE, title="")
        dialog.connect("response", lambda d, r: d.destroy())
        image_copy = Gtk.Picture.new_for_paintable(image.get_paintable())
        image_copy.set_vexpand(True)
        image_copy.set_hexpand(True)
        dialog.get_content_area().append(image_copy)
        dialog.show()

    def get_carousel_images(self, session, result, message, carousel, main_box):
        bytes = session.send_and_read_finish(result)
        if message.get_status() != Soup.Status.OK:
            raise Exception(f"Got {message.get_status()}, {message.get_reason_phrase()}")

        texture = Gdk.Texture.new_from_bytes(bytes)
        foreground = Gtk.Picture.new_for_paintable(texture)
        foreground.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
        foreground.set_hexpand(True)
        foreground.set_vexpand(True)

        click = Gtk.GestureClick.new()
        click.connect("pressed", self.on_picture_clicked, foreground)

        icon = Gtk.Image(icon_name="zoom-in-symbolic", pixel_size=30)
        icon.set_visible(False)

        background = Gtk.Picture.new_for_paintable(texture)
        background.add_css_class("blur")
        background.set_content_fit(Gtk.ContentFit.COVER)
        background.set_valign(Gtk.Align.FILL)
        background.set_halign(Gtk.Align.FILL)

        overlay = Gtk.Overlay(hexpand=True)
        overlay.set_child(background)
        overlay.add_overlay(foreground)
        overlay.add_overlay(icon)

        motion = Gtk.EventControllerMotion.new()
        motion.connect("enter", lambda m, x, y: (icon.set_visible(True), foreground.add_css_class("dark"), background.add_css_class("background-dark")))
        motion.connect("leave", lambda m: (icon.set_visible(False), foreground.remove_css_class("dark"), background.remove_css_class("background-dark")))
        overlay.add_controller(motion)
        overlay.add_controller(click)

        carousel.append(overlay)
        main_box.set_visible(True)
        self.loading(False)

    def get_image_from_url(self, url, row, carousel, main_box):
        message = Soup.Message(method="GET", uri=GLib.Uri.parse(url, GLib.UriFlags.NONE))
        self.session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, None, self.get_carousel_images, message, carousel, main_box)

    def loading(self, activate):
        self.currently_loading = activate
        self.spinner.set_spinning(activate)

    def download_item(self, button, download_links, download_names, index):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, buttons=Gtk.ButtonsType.CLOSE, title="Select Download Link")
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.set_default_size(700, 600)
        info_label = Gtk.Label(label=_(f"<b>Downloads will be sent to: {self.folders[self.category_index(index)]} </b>"), use_markup=True)
        dialog.get_content_area().append(info_label)

        listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow(vexpand=True, child=listbox)
        dialog.get_content_area().append(scroll)

        count = 0
        for link in download_links:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            label = Gtk.Label(label=_(download_names[count]), xalign=0, margin_start=10)
            label.add_css_class("title-4")

            use_button = None
            if(label.get_label() in self.downloaded.keys()):
                button = Gtk.Button(icon_name="user-trash-symbolic", halign=Gtk.Align.END, hexpand=True)
                button.add_css_class("destructive-action")
                button.connect("clicked", self.delete_item, label.get_label(), link, self.category_index(index))
                if(index != 0):
                    use_button = self.set_use_menu_button(self.downloaded[label.get_label()][1], index)
            else:
                button = Gtk.Button(icon_name="download-symbolic", halign=Gtk.Align.END, hexpand=True)
                button.add_css_class("suggested-action")
                button.connect("clicked", self.on_download_button_clicked, link, self.category_index(index), download_names[count])
            row.append(button)
            if(use_button is not None):
                row.append(use_button)
            row.prepend(label)
            listbox.append(row)
            count += 1

        dialog.show()

    def set_use_menu_button(self, themes, index):
        use_button = Gtk.MenuButton(label=(_("Use")), margin_start=8, halign=Gtk.Align.END)
        items = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        popover = Gtk.Popover()
        popover.set_child(items)
        for item in themes:
            if(index != 4):
                theme = Gtk.Button(label=os.path.basename(item))
            else:
                theme = Gtk.Button(label=item)
            theme.connect("clicked", self.set_theme, index)
            items.append(theme)
        use_button.set_popover(popover)
        return use_button

    def on_download_button_clicked(self, button, link, index, name):
        folder_path = self.folders.get(index, "Downloads")
        spinner = Gtk.Spinner(spinning=True)
        button.set_child(spinner)
        if(not os.path.exists(folder_path)):
            os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, name)

        def save_download(head_folders, installed_folders):
            self.downloaded[name] = [list(head_folders), installed_folders]
            writer = open(f"{self.folders[5]}/downloaded.txt", "w")
            writer.write(f"{self.downloaded}")
            writer.close()
            self.update_button_to_delete(button, name, link, index, installed_folders)

        def download_and_extract_file(response):
            with open(file_path, 'wb') as file:
                file.write(response)
            print(f'File downloaded successfully to {file_path}')
            if(any(ext in file_path for ext in [".png", ".jpg", ".svg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"])):
                save_download([file_path], [file_path])
            else:
                arrange_folders(file_path, folder_path, index, save_download)

        self.soup_get(link, download_and_extract_file)

    def update_button_to_delete(self, button, name, link, index, installed_folders):
        button.set_icon_name("user-trash-symbolic")
        button.remove_css_class("suggested-action")
        button.add_css_class("destructive-action")
        button.disconnect_by_func(self.on_download_button_clicked)
        button.connect("clicked", self.delete_item, name, link, index)

        if(index != 0):
            use_button = self.set_use_menu_button(installed_folders, index)
            button.get_parent().append(use_button)

    def set_theme(self, button, index):
        interface_settings = Gio.Settings(schema_id="org.gnome.desktop.interface")
        chosen_item = button.get_label()
        print(chosen_item)
        match(index):
            case(0):
                print("feature currently unavailable")
                # shell_settings = Gio.Settings(schema_id="org.gnome.shell.extensions.user-theme")
                # shell_settings.set_string("name", os.path.basename(installed_folders[0]))
            case(1):
                interface_settings.set_string("icon-theme", os.path.basename(chosen_item))
            case(2):
                interface_settings.set_string("gtk-theme", os.path.basename(chosen_item))
            case(3):
                interface_settings.set_string("cursor-theme", os.path.basename(chosen_item))
            case(4):
                portal = Xdp.Portal()
                parent = XdpGtk4.parent_new_gtk(self)
                portal.set_wallpaper(
                    parent,
                    f"file://{chosen_item}",
                    Xdp.WallpaperFlags.PREVIEW | Xdp.WallpaperFlags.BACKGROUND | Xdp.WallpaperFlags.LOCKSCREEN
                )

    def delete_item(self, button, name, link, index):
        if(index != 0):
            button.get_parent().remove(button.get_parent().get_last_child())
        self.downloaded = dict(ast.literal_eval(open(f"{self.folders[5]}/downloaded.txt", "r").read()))
        for path in self.downloaded[name][0]:
            try:
                if(os.path.isdir(path)):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except:
                continue
        writer = open(f"{self.folders[5]}/downloaded.txt", "w")
        self.downloaded.pop(name)
        writer.write(str(self.downloaded)); writer.close()
        self.update_button_to_download(button, name, link, index)

    def update_button_to_download(self, button, name, link, index):
        button.set_icon_name("download-symbolic")
        button.add_css_class("suggested-action")
        button.remove_css_class("destructive-action")
        button.disconnect_by_func(self.delete_item)
        button.connect("clicked", self.on_download_button_clicked, link, index, name)

    def on_type_changed(self, dropdown, _pspec):
        chosen_type = dropdown.props.selected_item.get_string()
        match(chosen_type):
            case("Most Downloaded"):
                self.selected = "down"
            case("Alphabetical"):
                self.selected = "alpha"
            case("Highest Rated"):
                self.selected = "high"
            case("New"):
                self.selected = "new"
        self.fetch_themes(int(self.activated.get_name()), 0, "clear")

    def on_tab_changed(self, row):
        self.activated = row
        if(int(row.get_name()) < 5):
            self.menus.set_sensitive(True)
        else:
            self.menus.set_sensitive(False)
        self.split_view.set_show_content(True)
        self.fetch_themes(int(row.get_name()), 0, "clear")

    def on_view_button_clicked(self, button, theme_url):
        webbrowser.open(theme_url)
