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

import xml.etree.ElementTree as ET, gi, webbrowser, shutil, ast, json, re

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")
gi.require_version("Xdp", "1.0")
gi.require_version("XdpGtk4", "1.0")
from gi.repository import Gtk, GLib, Gio, Gdk, Adw, Soup, Xdp, XdpGtk4
from .utils import css, arrange_folders

@Gtk.Template(resource_path='/io/github/swordpuffin/wardrobe/window.ui')
class WardrobeWindow(Adw.ApplicationWindow):
    
    __gtype_name__ = 'WardrobeWindow'
    page = Gtk.Template.Child()
    tab_buttons = Gtk.Template.Child()
    menus = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    if(GLib.getenv("HOST_XDG_DATA_HOME") == None):
        GLib.setenv("HOST_XDG_DATA_HOME", shutil.os.path.join(GLib.getenv("HOME"), ".local", "share"), True)
    data_dir = GLib.getenv("HOST_XDG_DATA_HOME") #Should be ~/.local/share
    picture_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES) #Typically ~/Pictures
    folders = {
        0: f"{data_dir}/themes/",
        1: f"{data_dir}/icons/",
        2: f"{data_dir}/themes/",
        3: f"{data_dir}/icons/",
        4: f"{picture_dir}/",
        5: f"{GLib.get_user_data_dir()}"
    }
    selected = "down"
    activated = None
    category_box = None
    search_url = None
    error_label = Gtk.Label(label=_("No results found :("))
    error_label.add_css_class("error"); error_label.add_css_class("title-4")

    #This system with the txt file is really rigid, and I will probably replace it at some point.
    #Saves a python dictionary inside a plain text file with the file paths for downloaded themes. Made for easy installation and deletion.
    #Stored at ~/.var/app/io.github.swordpuffin.wardrobe/data/downloaded.txt
    try:
        downloaded = dict(ast.literal_eval(open(f"{folders[5]}/downloaded.txt", "r").read())) 
    except Exception:
        downloaded = dict()

    if(not shutil.os.path.exists(f"{folders[5]}/prefs.json")):
        with open(f"{folders[5]}/prefs.json", "w") as file:
            json.dump({"cell_count": 8, "carousel_image_count": 3}, file, indent=4)

    with open(f"{folders[5]}/prefs.json", "r") as file:
        data = json.load(file)

    cell_count = data["cell_count"]
    carousel_image_count = data["carousel_image_count"]

    current_page = 0
    categories = [
        {"name": "Shell Themes", "url": "https://www.opendesktop.org/ocs/v1/content/data/?categories=134&sortmode="},
        {"name": "Icon Themes", "url": "https://www.opendesktop.org/ocs/v1/content/data/?categories=386&sortmode="},
        {"name": "Gtk3/4 Themes", "url": "https://www.opendesktop.org/ocs/v1/content/data/?categories=366&sortmode="},
        {"name": "Cursors", "url": "https://www.opendesktop.org/ocs/v1/content/data/?categories=107&sortmode="},
        {"name": "Wallpapers", "url": "https://www.opendesktop.org/ocs/v1/content/data/?categories=261&sortmode="}
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8')) #fetches the css from utils.py.
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self.set_default_size(800, 600)
        self.set_title("")
        icons = ["shell-symbolic", "app-symbolic", "interface-symbolic", "cursor-symbolic", "wallpaper-symbolic", "search-symbolic"]
        for i, label in zip(range(6), ["Shell", "Icon", "Interface", "Cursor", "Wallpaper", "Search"]):
            row = Adw.ActionRow(title=label, height_request=65, activatable=True)
            icon = Gtk.Image(pixel_size=22).new_from_icon_name(icons[i])
            if(i == 0):
                self.activated = row
                row.add_css_class("accent")
            elif(i == 5):
                search = Adw.EntryRow(title="Search", show_apply_button=False, name=str(i))
                self.tab_buttons.append(search)
                search.connect("entry-activated", self.on_search)
                continue
            row.add_suffix(icon)
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
        index = int(index)
        match(index):
            case(134):
                return(0)
            case(386 | 132):
                return(1)
            case(366 | 135 | 136):
                return(2)
            case(107):
                return(3)
            case(261 | 299 | 360):
                return(4)
            case(_):
                print("missing index: " + str(index))
                return(index)
    
    def soup_get(self, api_url):
        session = Soup.Session()
        message = Soup.Message.new("GET", api_url)   
        response_bytes = session.send_and_read(message)
        try:
            response_text = response_bytes.get_data().decode()
        except(Exception):
            response_text = response_bytes.get_data()
        return response_text 

    def on_search(self, search_entry):
        self.query = search_entry.get_text().strip()
        if(self.query):
            self.menus.set_sensitive(False)
            print(f"Search for: {self.query}")
            self.current_page = 0
            self.search_url = f"https://www.opendesktop.org/ocs/v1/content/data/?search={self.query}&page=0&pagesize={self.cell_count}&categories=134x386x366x107x261"
            self.on_tab_changed(search_entry)

    def fetch_themes(self, index, page, action):
        if(index != 5):
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
        response = self.soup_get(api_url)
        print("finished loading xml")

        flowbox_in_theme_grid = False
        for child in self.category_box:
            if(str(type(child)) == "<class 'gi.repository.Gtk.FlowBox'>"):
                theme_grid = child
                flowbox_in_theme_grid = True
            elif(str(type(child)) == "<class 'gi.repository.Gtk.Button'>" or str(type(child)) == "<class 'gi.repository.Gtk.Label'>"):
                self.category_box.remove(child)
        if(not flowbox_in_theme_grid):
            theme_grid = Gtk.FlowBox(row_spacing=12, column_spacing=12, homogeneous=True, max_children_per_line=5, selection_mode=Gtk.SelectionMode.NONE)
            self.category_box.append(theme_grid)
            scrollbox = Gtk.ScrolledWindow(vexpand=True, child=self.category_box)
            self.page.set_content(scrollbox)

        root = ET.fromstring(response)
        if(int(root.findall(".//meta")[0].find("itemsperpage").text) == 0):
            self.no_results_found(self.category_box)
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
            description = item.find("description").text if item.find("description") is not None else ""
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
            self.add_theme_to_list(theme_grid, title, creator, downloads, theme_url, download_links, download_names, description, self.category_index(typeid), rating, image_links)
        if(int(root.findall(".//meta")[0].find("itemsperpage").text) < self.cell_count):
            self.loading(False)
            return
        next_page_button = Gtk.Button(label=_("Next Page"), vexpand=True, margin_top=10)
        self.category_box.append(next_page_button)
        next_page_button.connect("clicked", self.on_next_page_clicked)

    def no_results_found(self, box):
        self.loading(False)
        box.append(self.error_label)
        
    def on_next_page_clicked(self, button):
        button.set_visible(False)
        self.current_page += 1
        vadj = self.category_box.get_parent().get_parent().get_vadjustment()
        if(int(self.activated.get_name()) != 5):
            self.fetch_themes(int(self.activated.get_name()), self.current_page, "_")
        else:
            url = f"https://www.opendesktop.org/ocs/v1/content/data/?search={self.query}&page={self.current_page}&pagesize={self.cell_count}&categories=134x386x366x107x261"
            self.grab_theme_params(url)
        GLib.idle_add(self.scroll_to_original_pos, self.category_box.get_parent().get_parent(), vadj.get_value()) #For vertical position in scrolled window to not reset

    def scroll_to_original_pos(self, scrolled_window, vadj):
        scrolled_window.get_vadjustment().set_value(vadj)

    def add_theme_to_list(self, theme_grid, title, creator, downloads, theme_url, download_links, download_names, description, index, rating, image_links):
        theme_box = Gtk.Box(hexpand=True, vexpand=True, orientation=Gtk.Orientation.VERTICAL)

        label = Gtk.Label(label=_(title), justify=Gtk.Justification.CENTER, wrap=True)
        label.add_css_class("title-2")
        creator_label = Gtk.Label(label=_(creator) + "\nDownloads: " + downloads, justify=Gtk.Justification.CENTER, margin_bottom=12)
        creator_label.add_css_class("creator-title")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=10)
        label_box.append(label)
        label_box.append(creator_label)
        theme_box.append(label_box)

        carousel = Adw.Carousel(halign=Gtk.Align.CENTER, margin_top=8, allow_scroll_wheel=False)
        for image in image_links:
            self.get_image_from_url(image, _, carousel, theme_box)

        navigation_box = Gtk.Box(halign=Gtk.Align.CENTER, visible=False)
        navigation_box.append(carousel)

        indicators = Adw.CarouselIndicatorDots(carousel=carousel, halign=Gtk.Align.CENTER)
        carousel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.CENTER)
        carousel_box.append(navigation_box); carousel_box.append(indicators)
        carousel.add_css_class("rounded")

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.CENTER, spacing=10, margin_bottom=5)
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
        
        browser_button = Gtk.Button(label=_("View in Browser"))
        browser_button.add_css_class("suggested-action")
        browser_button.connect("clicked", self.on_view_button_clicked, theme_url)
        button_box.append(rating_box); button_box.append(download_button); button_box.append(browser_button)

        description_label = Gtk.Label(label=re.sub(r'<.*?>', '', description), selectable=True, wrap=True)
        if(len(image_links) > 1):
            prev_button = Gtk.Button(label="<", valign=Gtk.Align.CENTER, halign=Gtk.Align.END, hexpand=True, margin_end=12, margin_start=12); navigation_box.prepend(prev_button)
            prev_button.add_css_class("circular")
            next_button = Gtk.Button(label=">", valign=Gtk.Align.CENTER, halign=Gtk.Align.START, hexpand=True, margin_start=12, margin_end=12); navigation_box.append(next_button)
            next_button.add_css_class("circular")
            prev_button.connect("clicked", self.on_prev_clicked, carousel)
            next_button.connect("clicked", self.on_next_clicked, carousel)
        description_scrolled_window = Gtk.ScrolledWindow(child=description_label, margin_top=8, margin_bottom=5, margin_start=12, margin_end=12, height_request=150)
        theme_box.append(button_box)
        theme_box.append(description_scrolled_window)
        theme_box.prepend(carousel_box)
        cell = Gtk.Frame(child=theme_box); cell.add_css_class("card")
        theme_grid.insert(cell, -1)

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

    def get_carousel_images(self, session, result, message, carousel, theme_box):
        bytes = session.send_and_read_finish(result)
        if(message.get_status() != Soup.Status.OK):
            raise Exception(f"Got {message.get_status()}, {message.get_reason_phrase()}")
        image = Gtk.Image.new_from_paintable(Gdk.Texture.new_from_bytes(bytes))
        image.set_pixel_size(260)
        carousel.append(image)
        carousel.get_parent().set_visible(True)
        self.loading(False)

    def get_image_from_url(self, url, row, carousel, theme_box):
        session = Soup.Session()
        message = Soup.Message(method="GET", uri=GLib.Uri.parse(url, GLib.UriFlags.NONE))
        session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, None, self.get_carousel_images, message, carousel, theme_box)

    def loading(self, activate):
        self.spinner.set_spinning(activate)

    def download_item(self, button, download_links, download_names, index):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, buttons=Gtk.ButtonsType.CLOSE, title="Select Download Link")
        dialog.set_default_size(600, 600)
        label = Gtk.Label(label=_("*Larger files may cause temporary freezes, just wait until the download completes"), wrap=True)
        label.add_css_class("warning")
        info_label = Gtk.Label(label=_(f"<b>Downloads will be sent to:  {self.folders[self.category_index(index)]}</b>"), use_markup=True)
        dialog.get_content_area().append(label); dialog.get_content_area().append(info_label)

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
                button = Gtk.Button(label=_("Delete"), halign=Gtk.Align.END, hexpand=True)
                button.add_css_class("destructive-action")
                button.connect("clicked", self.delete_item, label.get_label(), link, self.category_index(index))
                use_button = Gtk.Button(label=(_("Use")), margin_start=8, halign=Gtk.Align.END)
                use_button.connect("clicked", self.set_theme, index, self.downloaded[label.get_label()])
            else:
                button = Gtk.Button(label=_("Download"), halign=Gtk.Align.END, hexpand=True)
                button.add_css_class("suggested-action")
                button.connect("clicked", self.on_download_button_clicked, link, self.category_index(index), download_names[count])
            row.append(button)
            if(use_button is not None):
                row.append(use_button)
            row.prepend(label)
            listbox.append(row)
            count += 1

        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()

    def on_download_button_clicked(self, button, link, index, name):
        folder_path = self.folders.get(index, "Downloads")
        if(not shutil.os.path.exists(folder_path)):
            shutil.os.makedirs(folder_path, exist_ok=True)

        file_path = shutil.os.path.join(folder_path, name)

        response = self.soup_get(link)
        with open(file_path, 'wb') as file:
            print(link)
            file.write(response)
        print(f'File downloaded successfully to {file_path}')

        if(any(ext in file_path for ext in [".png", ".jpg", ".svg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"])):
            head_folders = [ file_path ]
        else:
            head_folders = arrange_folders(file_path, folder_path, index)
            shutil.os.remove(file_path)
        self.downloaded[name] = list(head_folders)
        writer = open(f"{self.folders[5]}/downloaded.txt", "w")
        writer.write(f"{self.downloaded}")
        writer.close()
        self.update_button_to_delete(button, name, link, index, list(head_folders))

    def update_button_to_delete(self, button, name, link, index, installed_folders):
        button.set_label("Delete")
        button.remove_css_class("suggested-action")
        button.add_css_class("destructive-action")
        button.disconnect_by_func(self.on_download_button_clicked)
        button.connect("clicked", self.delete_item, name, link, index)

        use_button = Gtk.Button(label=(_("Use")), margin_start=8)
        use_button.connect("clicked", self.set_theme, index, installed_folders)
        button.get_parent().append(use_button)

    def set_theme(self, button, index, installed_folders):
        interface_settings = Gio.Settings(schema_id="org.gnome.desktop.interface")
        match(index):
            case(0):
                shell_settings = Gio.Settings(schema_id="org.gnome.shell.extensions.user-theme")
                shell_settings.set_string("name", shutil.os.path.basename(installed_folders[0]))
            case(1):
                interface_settings.set_string("icon-theme", shutil.os.path.basename(installed_folders[0]))
            case(2):
                interface_settings.set_string("gtk-theme", shutil.os.path.basename(installed_folders[0]))
            case(3):
                interface_settings.set_string("cursor-theme", shutil.os.path.basename(installed_folders[0]))
            case(4):
                print(installed_folders[0])
                if(shutil.os.path.isdir(installed_folders[0])):
                    for root, dirs, files in shutil.os.walk(installed_folders[0]):
                        for file in files:
                            if any(ext in file for ext in [".png", ".jpg", ".svg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"]):
                                image = shutil.os.path.join(root, file)
                else:
                    image = installed_folders[0]
                portal = Xdp.Portal()
                parent = XdpGtk4.parent_new_gtk(self)
                portal.set_wallpaper(
                    parent,
                    f"file://{image}",
                    Xdp.WallpaperFlags.PREVIEW | Xdp.WallpaperFlags.BACKGROUND | Xdp.WallpaperFlags.LOCKSCREEN
                )

    def delete_item(self, button, name, link, index):
        button.get_parent().remove(button.get_parent().get_last_child())
        self.downloaded = dict(ast.literal_eval(open(f"{self.folders[5]}/downloaded.txt", "r").read())) 
        for path in self.downloaded[name]:
            try:
                if(shutil.os.path.isdir(path)):
                    shutil.rmtree(path)
                else:
                    shutil.os.remove(path)
            except FileNotFoundError:
                continue
        writer = open(f"{self.folders[5]}/downloaded.txt", "w")
        self.downloaded.pop(name)
        writer.write(str(self.downloaded)); writer.close()
        self.update_button_to_download(button, name, link, index)
        
    def update_button_to_download(self, button, name, link, index):
        button.set_label("Download")
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
        self.activated.remove_css_class("accent")
        row.add_css_class("accent")
        self.activated = row
        print(row.get_name())
        if(int(row.get_name()) != 5):
            self.menus.set_sensitive(True)
        else:
            self.menus.set_sensitive(False)
        self.fetch_themes(int(row.get_name()), 0, "clear")

    def on_view_button_clicked(self, button, theme_url):
        webbrowser.open(theme_url)
