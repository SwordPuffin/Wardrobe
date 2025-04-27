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

import xml.etree.ElementTree as ET, gi, webbrowser, shutil, random, ast, zipfile, tarfile, re

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")
#Remember to add libportal when trying to use xdp
# gi.require_version("Xdp", "1.0")
# gi.require_version("XdpGtk4", "1.0")
# from gi.repository import Xdp, XdpGtk4

from gi.repository import Gtk, GLib, Gio, Gdk, Adw, Soup, Pango
from .utils import _get_valid_shell_themes, _get_valid_icon_themes, _get_valid_gtk_themes, _get_valid_cursor_themes, _get_valid_wallpapers, arrange_folders, wallpaper_paths, css

@Gtk.Template(resource_path='/io/github/swordpuffin/wardrobe/window.ui')
class WardrobeWindow(Adw.ApplicationWindow):
    
    stack = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    menus = Gtk.Template.Child()
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
    __gtype_name__ = 'WardrobeWindow'
    selected = "down"
    dropdown = None
    user_theme_downloaded = True
    search_theme_grid = Gtk.FlowBox(row_spacing=12, column_spacing=12, homogeneous=True, max_children_per_line=5, selection_mode=Gtk.SelectionMode.NONE)
    error_label = Gtk.Label(label=_("No results found :("))
    error_label.add_css_class("error"); error_label.add_css_class("title-4")
    # shell_settings = Gio.Settings(schema_id="org.gnome.shell.extensions.user-theme")
    # interface_settings = Gio.Settings(schema_id="org.gnome.desktop.interface")
    
    #This system with the txt file is really rigid, and I will probably replace it at some point.
    #Saves a python dictionary inside a plain text file with the file paths for downloaded themes. Made for easy installation and deletion.
    #Stored at ~/.var/app/io.github.swordpuffin.wardrobe/data/downloaded.txt
    try:
        downloaded = dict(ast.literal_eval(open(f"{folders[5]}/downloaded.txt", "r").read())) 
    except Exception:
        downloaded = dict()
    current_page = 0
    # try:
    #     active_gtk_theme = interface_settings.get("gtk-theme")
    #     active_icon_theme = interface_settings.get("icon-theme")
    #     active_cursor_theme = interface_settings.get("cursor-theme")
    #     active_wallpaper = interface_settings.get("picture-uri")
        # active_shell_theme = interface_settings.get("name")
    #     active_shell_theme = ""
    # except Exception:
    #     active_shell_theme = ""
    #     active_icon_theme = ""
    #     active_wallpaper = ""
    #     active_cursor_theme = ""
    #     active_gtk_theme = ""


        # user_theme_downloaded = False
    # active_themes = {
    #     0: active_shell_theme,
    #     1: active_icon_theme,
    #     2: active_gtk_theme,
    #     3: active_cursor_theme,
    #     4: active_wallpaper
    # }

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

        self.set_title("")
        self.set_default_size(600, 600)
        
        count = 0
        for category in self.categories:
            category_box = Gtk.Box(margin_top=10, margin_bottom=10, margin_start=15, margin_end=15, orientation=Gtk.Orientation.VERTICAL)
            scrollbox = Gtk.ScrolledWindow(vexpand=True, child=category_box)
            self.stack.get_child_by_name(str(count)).get_first_child().get_first_child().get_first_child().set_vexpand(True)
            self.stack.get_child_by_name(str(count)).get_first_child().get_first_child().get_first_child().set_valign(Gtk.Align.FILL)
            self.stack.get_child_by_name(str(count)).set_child(scrollbox); count += 1
            category['box'] = category_box
        self.menus.connect('notify::selected-item', self.on_type_changed)
        items = Gtk.StringList()
        for item in ["Most Downloaded", "Alphabetical", "Highest Rated", "New"]:
            items.append(item)
        self.menus.set_model(items)
        self.current_page = 0
        
        self.add_search_and_tweak_pages()
        self.stack.connect("notify::visible-child", self.on_tab_changed)

    def error_dialog(self):
        dialog = Gtk.Dialog(
            title='Warning',
            transient_for=self,
            modal=True
        )
        dialog.add_css_class("warning")
            
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        head = Gtk.Label(xalign=0.5, label=_("Changing the shell theme requires the\nuser-theme package for your distribution"), margin_top=8)
        head.add_css_class("heading")
        box.append(head)
        listbox = Gtk.ListBox(margin_top=12, margin_bottom=12, margin_start=12, margin_end=12); listbox.add_css_class("boxed-list")
        box.append(listbox)
        commands = ["sudo dnf install gnome-shell-extension-user-theme", "sudo apt install gnome-shell-extensions", "sudo pacman -S gnome-shell-extensions"]
        for item in commands:
            label = Gtk.Label(label=_(item), margin_top=8, margin_bottom=8, margin_start=8, margin_end=8, wrap=True, xalign=0, selectable=True)
            label.add_css_class("heading")
            row = Gtk.ListBoxRow(selectable=False, child=label)
            listbox.append(row)
        dialog.set_child(box)
        dialog.present()
    
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

    def add_search_and_tweak_pages(self):
        self.search_results = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        scrollbox = Gtk.ScrolledWindow(child=self.search_results)

        search_entry = Gtk.SearchEntry(placeholder_text="Search...")
        search_entry.connect("activate", self.on_search)
        self.search_results.append(search_entry)
        self.stack.get_child_by_name("5").set_child(scrollbox)
        self.stack.get_child_by_name("5").get_first_child().get_first_child().get_first_child().set_vexpand(True)
        self.stack.get_child_by_name("5").get_first_child().get_first_child().get_first_child().set_valign(Gtk.Align.FILL)

        # if(self.user_theme_downloaded):
        #     self.theme_list = Gtk.ListBox(vexpand=True)
        #     self.theme_list.add_css_class("boxed-list"); self.theme_list.add_css_class("title-4")
        #     item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        #     scrollbox = Gtk.ScrolledWindow(child=self.theme_list)

        #     items = ["Shell Themes", "Icon Themes", "Gtk3/4 Themes", "Cursors", "Wallpaper"]
        #     string_list = Gtk.StringList()
        #     for item in items:
        #         string_list.append(item)
        #     self.dropdown = Gtk.DropDown.new_from_strings(items); self.dropdown.set_halign(Gtk.Align.START)
        #     self.dropdown.connect("notify::selected", self.on_selection_changed)
        #     self.on_selection_changed(self.dropdown, _)

        #     item_box.append(self.dropdown)
        #     item_box.append(scrollbox)
        #     self.notebook.append_page(item_box, Gtk.Label(label="_(Tweaks")))
        # else:
            # self.error_dialog()
  
    # first_check_button = None
    # def on_selection_changed(self, dropdown, param):
    #     while(self.theme_list.get_first_child() is not None):
    #         self.theme_list.remove(self.theme_list.get_first_child())
        
    #     match(self.dropdown.get_selected()):
    #         case(0):
    #             items = _get_valid_shell_themes()
    #         case(1):
    #             items = _get_valid_icon_themes()
    #         case(2):
    #             items = _get_valid_gtk_themes()
    #         case(3):
    #             items = _get_valid_cursor_themes()
    #         case(4):
    #             items = _get_valid_wallpapers()

    #     for file_name in sorted(items):
    #         row = Gtk.ListBoxRow(vexpand=True, height_request=50)
    #         row_box = Gtk.Box()
    #         check_button = Gtk.CheckButton(label=_(file_name), hexpand=True, margin_start=10, halign=Gtk.Align.START)
    #         check_button.get_last_child().set_wrap(True)
    #         check_button.get_last_child().set_wrap_mode(Pango.WrapMode.CHAR)
    #         check_button.get_last_child().set_size_request(300, -1)
    #         check_button.get_last_child().set_margin_start(16)
    #         row_box.append(check_button)
    #         if(self.dropdown.get_selected() == 4):
    #             image_file = Gio.File.new_for_path((f"{shutil.os.path.join(wallpaper_paths[file_name], file_name)}"))
    #             image = Gtk.Picture(hexpand=True, halign=Gtk.Align.END, height_request=70, margin_top=10, margin_bottom=10, margin_end=5, file=image_file)
    #             row_box.append(image)
    #         if(self.active_themes[self.dropdown.get_selected()] == f"'{file_name}'"):
    #             check_button.set_active(True)
    #         if(self.first_check_button is None):
    #             self.first_check_button = check_button
    #         else:
    #             check_button.set_group(self.first_check_button)
    #         check_button.connect("toggled", self.change_theme, self.dropdown.get_selected(), shutil.os.path.join(wallpaper_paths[file_name], file_name) if file_name in wallpaper_paths.keys() else None)
    #         row.set_child(row_box)
    #         self.theme_list.append(row)

    # def change_theme(self, button, index, wallpaper_path):
        # TODO: This is an unsafe way to set the theme, will NEED revision
    #     if(button.get_active()):
    #         match(index):
    #             case(0): #Shell themes
                    #shell_settings.set_string("name", button.get_parent().get_first_child().get_label())
    #                 pass
    #             case(1): #Icon themes
    #                 self.interface_settings.set_string("icon-theme", button.get_parent().get_first_child().get_label())
    #             case(2): #Gtk3/4 themes
    #                 self.interface_settings.set_string("gtk-theme", button.get_parent().get_first_child().get_label())
    #             case(3): #Cursors
    #                 self.interface_settings.set_string("cursor-theme", button.get_parent().get_first_child().get_label())
    #             case(4): #Wallpapers
    #                 portal = Xdp.Portal()
    #                 parent = XdpGtk4.parent_new_gtk(self)
    #                 print(wallpaper_path)
    #                 file = f"file://{wallpaper_path}"
    #                 portal.set_wallpaper(
    #                     parent,
    #                     file,
    #                     Xdp.WallpaperFlags.PREVIEW
    #                     | Xdp.WallpaperFlags.BACKGROUND
    #                     | Xdp.WallpaperFlags.LOCKSCREEN,
    #                     None,
    #                     self.on_wallpaper_set
    #                 )
    # def on_wallpaper_set(self, _portal, result):
    #     success = _portal.set_wallpaper_finish(result)
    #     if success:
    #         print("Wallpaper set successfully")
    #     else:
    #         print("Could not set wallpaper")
    def on_search(self, search_entry):
        self.query = search_entry.get_text().strip()
        if(self.query):
            self.menus.set_sensitive(False)
            print(f"Search for: {self.query}")
            self.search_results.set_vexpand(True)
            self.current_page = 0
            if(self.search_theme_grid.get_parent()):
                self.search_theme_grid.get_parent().remove(self.search_theme_grid)
            while(self.search_theme_grid.get_first_child() is not None):
                self.search_theme_grid.remove(self.search_theme_grid.get_first_child())
                
            url = f"https://www.opendesktop.org/ocs/v1/content/data/?search={self.query}&page=0&categories=134x386x366x107x261"
            self.loading(True)
            self.search_results.append(self.search_theme_grid)
            self.grab_theme_params(url, self.search_results)

    def fetch_themes(self, index, page, action):
        category = self.categories[self.category_index(index)]
        api_url = f"{category['url']}{self.selected}&page={page}"
        category_box = category['box']
        if(action == "clear"):
            self.current_page = 0
            while(category_box.get_first_child() is not None):
                category_box.remove(category_box.get_first_child())
        self.grab_theme_params(api_url, category_box)

    def grab_theme_params(self, api_url, category_box):
        self.loading(True)
        print("start loading xml")
        response = self.soup_get(api_url)
        print("finished loading xml")

        flowbox_in_theme_grid = False
        for child in category_box:
            if(str(type(child)) == "<class 'gi.repository.Gtk.FlowBox'>"):
                theme_grid = child
                flowbox_in_theme_grid = True
            elif(str(type(child)) == "<class 'gi.repository.Gtk.Button'>" or str(type(child)) == "<class 'gi.repository.Gtk.Label'>"):
                category_box.remove(child)
        if(not flowbox_in_theme_grid):
            theme_grid = Gtk.FlowBox(row_spacing=12, column_spacing=12, homogeneous=True, max_children_per_line=5, selection_mode=Gtk.SelectionMode.NONE)
            category_box.append(theme_grid)

        root = ET.fromstring(response)
        if(int(root.findall(".//meta")[0].find("itemsperpage").text) == 0):
            self.no_results_found(category_box)
            return
        for item in root.findall(".//content"):
            title = item.find("name").text if item.find("name") is not None else "Unknown"
            thumbnail_url = item.find("previewpic1").text if item.find("previewpic1") is not None else ""
            theme_url = item.find("detailpage").text if item.find("detailpage") is not None else ""
            creator = item.find("personid").text if item.find("personid") is not None else "Unknown"
            #I don't know why but I can't get downloads to always work unless I overbuild the security
            if(item.find("downloads") is not None): 
                downloads = item.find("downloads").text if item.find("downloads").text is not None else "0"
            else: 
                downloads = "0"
            description = item.find("description").text if item.find("description") is not None else ""
            rating = int(item.find("score").text) / 10 if item.find("score") is not None else 0
            typeid = item.find("typeid").text if item.find("typeid") is not None else 0 #Some items don't have typeids for some reason???
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
            for z in range(1, 6):
                if(item.find(f"previewpic{z}") is not None):
                    image_links.append(item.find(f"previewpic{z}").text)
                else:
                    break
            self.add_theme_to_list(theme_grid, title, creator, downloads, theme_url, download_links, download_names, description, self.category_index(typeid), rating, image_links)
        if(int(root.findall(".//meta")[0].find("itemsperpage").text) < 10):
            self.loading(False)
            return
        self.next_page_button = Gtk.Button(label=_("Next Page"), vexpand=True, margin_top=10, visible=False)
        category_box.append(self.next_page_button)
        self.next_page_button.connect("clicked", self.on_next_page_clicked, category_box)

    def no_results_found(self, box):
        self.loading(False)
        box.append(self.error_label)
        
    def on_next_page_clicked(self, button, category_box):
        button.set_visible(False)
        self.current_page += 1
        vadj = category_box.get_parent().get_parent().get_vadjustment()
        if(int(self.stack.get_visible_child_name()) != 5):
            self.fetch_themes(int(self.stack.get_visible_child_name()), self.current_page, "_")
        else:
            url = f"https://www.opendesktop.org/ocs/v1/content/data/?search={self.query}&page={self.current_page}&categories=134x386x366x107x261"
            self.grab_theme_params(url, self.search_results)
        GLib.idle_add(self.scroll_to_original_pos, category_box.get_parent().get_parent(), vadj.get_value()) #For vertical position in scrolled window to not reset
        
    def scroll_to_original_pos(self, scrolled_window, vadj):
        scrolled_window.get_vadjustment().set_value(vadj)

    def add_theme_to_list(self, theme_grid, title, creator, downloads, theme_url, download_links, download_names, description, index, rating, image_links):
        theme_box = Gtk.Box(hexpand=True, vexpand=True, orientation=Gtk.Orientation.VERTICAL, visible=False)

        label = Gtk.Label(label=_(title), justify=Gtk.Justification.CENTER, wrap=True, width_request=150)
        label.add_css_class("title-2")
        creator_label = Gtk.Label(label=_(creator) + "\nDownloads: " + downloads, justify=Gtk.Justification.CENTER, margin_bottom=12)
        creator_label.add_css_class("creator-title")

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=10)
        label_box.append(label)
        label_box.append(creator_label)
        theme_box.append(label_box)

        carousel = Adw.Carousel(hexpand=True, halign=Gtk.Align.CENTER, margin_top=8, allow_scroll_wheel=False)
        for image in image_links:
            self.get_image_from_url(image, _, carousel, theme_box)

        navigation_box = Gtk.Box()
        navigation_box.append(carousel)

        indicators = Adw.CarouselIndicatorDots(carousel=carousel, halign=Gtk.Align.CENTER)
        carousel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
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
        carousel.prepend(image)
        self.loading(False)
        self.next_page_button.set_visible(True)
        theme_box.set_visible(True)

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

            if(label.get_label() in self.downloaded.keys()):
                button = Gtk.Button(label=_("Delete"), halign=Gtk.Align.END, hexpand=True)
                button.add_css_class("destructive-action")
                button.connect("clicked", self.delete_item, label.get_label(), link, self.category_index(index))
            else:
                button = Gtk.Button(label=_("Download"), halign=Gtk.Align.END, hexpand=True)
                button.add_css_class("suggested-action")
                button.connect("clicked", self.on_download_button_clicked, link, self.category_index(index), download_names[count])
            row.append(label)
            row.append(button)
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
            file.write(response)
        print(f'File downloaded successfully to {file_path}')

        try:
            head_folders = set() 
            if(zipfile.is_zipfile(file_path)):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(folder_path)
                    for member in zip_ref.namelist():
                        # Get the head folder or file
                        head_folder = member.split('/')[0]
                        head_folders.add(shutil.os.path.join(folder_path, head_folder))
                    for item in head_folders:
                        arrange_folders(shutil.os.path.join(folder_path, item), folder_path, index, item)
                shutil.os.remove(file_path)
                print(f'ZIP file extracted successfully to {folder_path}')
            elif(tarfile.is_tarfile(file_path)):
                with tarfile.open(file_path, 'r') as tar_ref:
                    tar_ref.extractall(folder_path)
                    for member in tar_ref.getnames():
                        # Get the head folder or file
                        head_folder = member.split('/')[0]
                        head_folders.add(shutil.os.path.join(folder_path, head_folder))
                    for item in head_folders:
                        arrange_folders(shutil.os.path.join(folder_path, item), folder_path, index, item)
                shutil.os.remove(file_path)
                print(f'TAR file extracted successfully to {folder_path}')
            elif(any(ext in file_path for ext in [".png", ".jpg", ".svg", ".jpeg"])):
                print("Download is an image, no need to extract")
                head_folders.add(file_path)
            else:
                head_folders.add(file_path)
                print("Base file downloaded")
            writer = open(f"{self.folders[5]}/downloaded.txt", "w")
            # Update self.downloaded with only head folders
            self.downloaded[name] = list(head_folders)
            writer.write(f"{self.downloaded}")
            writer.close()

        except Exception as e:
            print(f'Failed to extract archive: {e}')

        self.update_button_to_delete(button, name, link, index)

    def update_button_to_delete(self, button, name, link, index):
        button.set_label("Delete")
        button.remove_css_class("suggested-action")
        button.add_css_class("destructive-action")
        button.disconnect_by_func(self.on_download_button_clicked)
        button.connect("clicked", self.delete_item, name, link, index)

    def delete_item(self, button, name, link, index):
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
        self.fetch_themes(int(self.stack.get_visible_child_name()), 0, "clear")


    def on_tab_changed(self, stack, param_spec):

        if(int(stack.get_visible_child_name()) != 5 and int(stack.get_visible_child_name()) != 6):
            self.menus.set_sensitive(True)
            self.fetch_themes(int(stack.get_visible_child_name()), 0, "clear")
        else:
            if(int(stack.get_visible_child_name()) == 6):
                self.on_selection_changed(self.dropdown, _)
            self.menus.set_sensitive(False)

    def on_view_button_clicked(self, button, theme_url):
        webbrowser.open(theme_url)
