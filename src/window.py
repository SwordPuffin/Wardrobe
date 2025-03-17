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

import xml.etree.ElementTree as ET, gi, webbrowser, shutil, random, subprocess, ast, zipfile, tarfile

gi.require_version('WebKit', '6.0')
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")

from gi.repository import Gtk, GLib, Gio, Gdk, Adw, WebKit, Soup, Pango
from .utils import _get_valid_shell_themes, _get_valid_icon_themes, _get_valid_gtk_themes, _get_valid_cursor_themes, _get_valid_wallpapers, wallpaper_paths, css

@Gtk.Template(resource_path='/io/github/swordpuffin/wardrobe/window.ui')
class WardrobeWindow(Adw.ApplicationWindow):
    
    notebook = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    menus = Gtk.Template.Child()
    folders = {
        0: f"{shutil.os.path.expanduser('~')}/.themes/",
        1: f"{shutil.os.path.expanduser('~')}/.icons/",
        2: f"{shutil.os.path.expanduser('~')}/.themes/",
        3: f"{shutil.os.path.expanduser('~')}/.icons/",
        4: f"{shutil.os.path.expanduser('~')}/Pictures/",
        5: f"{GLib.get_user_data_dir()}"
    }
    __gtype_name__ = 'WardrobeWindow'
    selected = "down"
    dropdown = None
    user_theme_downloaded = True
    
    #This system with the txt file is really rigid, and I will probably replace it at some point.
    #Saves a python dictionary inside a plain text file with the file paths for downloaded themes. Made for easy installation and deletion.
    #Stored at ~/.var/app/io.github.swordpuffin.wardrobe/data/downloaded.txt
    try:
        downloaded = dict(ast.literal_eval(open(f"{folders[5]}/downloaded.txt", "r").read())) 
    except Exception:
        downloaded = dict()
    current_page = 0
    
    try:
        active_gtk_theme = subprocess.run(["flatpak-spawn", "--host", "gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"], check=True, text=True, stdout=subprocess.PIPE).stdout.strip()
        active_icon_theme = subprocess.run(["flatpak-spawn", "--host", "gsettings", "get", "org.gnome.desktop.interface", "icon-theme"], check=True, text=True, stdout=subprocess.PIPE).stdout.strip()
        active_cursor_theme = subprocess.run(["flatpak-spawn", "--host", "gsettings", "get", "org.gnome.desktop.interface", "cursor-theme"], check=True, text=True, stdout=subprocess.PIPE).stdout.strip()
        active_wallpaper = "'"+shutil.os.path.basename(subprocess.run(["flatpak-spawn", "--host", "gsettings", "get", "org.gnome.desktop.background", "picture-uri"], check=True, text=True, stdout=subprocess.PIPE).stdout.strip())
        active_shell_theme = subprocess.run(["flatpak-spawn", "--host", "gsettings", "get", "org.gnome.shell.extensions.user-theme", "name"], check=True, text=True, stdout=subprocess.PIPE).stdout.strip()
    except Exception:
        active_shell_theme = ""
        user_theme_downloaded = False
    active_themes = {
        0: active_shell_theme,
        1: active_icon_theme,
        2: active_gtk_theme,
        3: active_cursor_theme,
        4: active_wallpaper
    }

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
        self.notebook.remove_css_class("frame")
        self.set_default_size(600, 600)
        
        for category in self.categories:
            category_box = Gtk.ListBox(margin_top=10, margin_bottom=10, margin_start=15, margin_end=15, selection_mode=Gtk.SelectionMode.NONE)
            category_box.add_css_class("boxed-list")
            scrollbox = Gtk.ScrolledWindow(vexpand=True, child=category_box)
            self.notebook.append_page(scrollbox, Gtk.Label(label=category["name"]))
            category['box'] = category_box
            
        self.menus.connect('notify::selected-item', self.on_type_changed)
        items = Gtk.StringList()
        for item in ["Downloaded", "Alphabetical", "Highest Rated", "New"]:
            items.append(item)
        self.menus.set_model(items)
        self.current_page = 0
        
        self.add_search_and_tweak_pages()
        self.notebook.connect("switch-page", self.on_tab_changed)
    
    def error_dialog(self):
        dialog = Gtk.Dialog(
            title='Warning',
            transient_for=self,
            modal=True
        )
        dialog.add_css_class("warning")
            
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        head = Gtk.Label(xalign=0.5, label="Changing the shell theme requires the\nuser-theme package for your distribution", margin_top=8)
        head.add_css_class("heading")
        box.append(head)
        listbox = Gtk.ListBox(margin_top=12, margin_bottom=12, margin_start=12, margin_end=12); listbox.add_css_class("boxed-list")
        box.append(listbox)
        commands = ["sudo dnf install gnome-shell-extension-user-theme", "sudo apt install gnome-shell-extensions", "sudo pacman -S gnome-shell-extensions"]
        for item in commands:
            label = Gtk.Label(label=item, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8, wrap=True, xalign=0, selectable=True)
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
            case(366 | 135):
                return(2)
            case(107):
                return(3)
            case(261 | 299):
                return(4)
            case(_):
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
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)

        search_entry = Gtk.SearchEntry(placeholder_text="Search...")
        search_entry.connect("activate", self.on_search)
        search_box.append(search_entry)

        self.search_results = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.search_results.add_css_class("boxed-list")
        scrollbox = Gtk.ScrolledWindow(child=self.search_results)
        search_box.append(scrollbox)

        self.notebook.append_page(search_box, Gtk.Label(label="Search"))
        if(self.user_theme_downloaded):
            self.theme_list = Gtk.ListBox(vexpand=True)
            self.theme_list.add_css_class("boxed-list"); self.theme_list.add_css_class("title-4")
            item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
            scrollbox = Gtk.ScrolledWindow(child=self.theme_list)

            items = ["Shell Themes", "Icon Themes", "Gtk3/4 Themes", "Cursors", "Wallpaper"]
            string_list = Gtk.StringList()
            for item in items:
                string_list.append(item)
            self.dropdown = Gtk.DropDown.new_from_strings(items); self.dropdown.set_halign(Gtk.Align.START)
            self.dropdown.connect("notify::selected", self.on_selection_changed)
            self.on_selection_changed(self.dropdown, _)

            item_box.append(self.dropdown)
            item_box.append(scrollbox)
            self.notebook.append_page(item_box, Gtk.Label(label="Tweaks"))
        else:
            self.error_dialog()
  
    first_check_button = None
    def on_selection_changed(self, dropdown, param):
        while(self.theme_list.get_first_child() is not None):
            self.theme_list.remove(self.theme_list.get_first_child())
        
        match(self.dropdown.get_selected()):
            case(0):
                items = _get_valid_shell_themes()
            case(1):
                items = _get_valid_icon_themes()
            case(2):
                items = _get_valid_gtk_themes()
            case(3):
                items = _get_valid_cursor_themes()
            case(4):
                items = _get_valid_wallpapers()

        for file_name in sorted(items): 
            row = Gtk.ListBoxRow(vexpand=True, height_request=50) 
            row_box = Gtk.Box()
            check_button = Gtk.CheckButton(label=file_name, hexpand=True, margin_start=10, halign=Gtk.Align.START)
            check_button.get_last_child().set_wrap(True) 
            check_button.get_last_child().set_wrap_mode(Pango.WrapMode.CHAR)
            check_button.get_last_child().set_size_request(300, -1)
            check_button.get_last_child().set_margin_start(8)
            row_box.append(check_button)
            if(self.dropdown.get_selected() == 4): 
                image_file = Gio.File.new_for_path((f"{shutil.os.path.join(wallpaper_paths[file_name], file_name)}")) 
                image = Gtk.Picture(hexpand=True, halign=Gtk.Align.END, height_request=70, margin_top=10, margin_bottom=10, margin_end=5, file=image_file)
                row_box.append(image)
            if(self.active_themes[self.dropdown.get_selected()] == f"'{file_name}'"):
                check_button.set_active(True)
            if(self.first_check_button is None):
                self.first_check_button = check_button
            else:
                check_button.set_group(self.first_check_button)
            check_button.connect("toggled", self.change_theme, self.dropdown.get_selected(), shutil.os.path.join(wallpaper_paths[file_name], file_name) if file_name in wallpaper_paths.keys() else None)
            row.set_child(row_box)  
            self.theme_list.append(row)  

    def change_theme(self, button, index, wallpaper_path):
        # TODO: This is an unsafe way to set the theme, will NEED revision

        match(index):
            case(0): #Shell themes
                subprocess.run(["flatpak-spawn", "--host", "gsettings", "set", "org.gnome.shell.extensions.user-theme", "name", button.get_parent().get_first_child().get_label()], check=True)
            case(1): #Icon themes
                subprocess.run(["flatpak-spawn", "--host", "gsettings", "set", "org.gnome.desktop.interface", "icon-theme", button.get_parent().get_first_child().get_label()], check=True)
            case(2): #Gtk3/4 themes
                subprocess.run(["flatpak-spawn", "--host", "gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", button.get_parent().get_first_child().get_label()], check=True)
            case(3): #Cursors
                subprocess.run(["flatpak-spawn", "--host", "gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", button.get_parent().get_first_child().get_label()], check=True)
            case(4): #Wallpapers
                subprocess.run(["flatpak-spawn", "--host", "gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"'{wallpaper_path}'"], check=True)
                subprocess.run(["flatpak-spawn", "--host", "gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"'{wallpaper_path}'"], check=True)
        
    def on_search(self, search_entry):
        self.query = search_entry.get_text().strip()
        if(self.query):
            self.menus.set_sensitive(False)
            print(f"Search for: {self.query}")
            self.search_results.set_vexpand(True)
            self.current_page = 0
            
            while(self.search_results.get_first_child() is not None):
                self.search_results.remove(self.search_results.get_first_child())
                
            url = f"https://www.opendesktop.org/ocs/v1/content/data/?search={self.query}&page=0&categories=134x386x366x107x261"
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
        response = self.soup_get(api_url)
        root = ET.fromstring(response)
        num_added = 0
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
            for i in range(1, 11):  # Maximum of 10 download links
                download_link = item.find(f"downloadlink{i}")
                download_name = item.find(f"downloadname{i}")
                if(download_link is not None and download_link.text):
                    download_links.append(download_link.text)
                    download_names.append(download_name.text)
            num_added += 1
            self.add_theme_to_list(title, thumbnail_url, creator, category_box, downloads, theme_url, download_links, download_names, description, self.category_index(typeid), rating)
        if(num_added < 10):
            return
        self.next_page_button = Gtk.Button(label="Next Page", vexpand=True, margin_top=10, visible=False)
        category_box.append(self.next_page_button)
        self.next_page_button.connect("clicked", self.on_next_page_clicked, category_box)
        
    def on_next_page_clicked(self, button, category_box):
        self.current_page += 1
        if(self.notebook.get_current_page() != 5):
            self.fetch_themes(self.notebook.get_current_page(), self.current_page, "_")
        else:
            url = f"https://www.opendesktop.org/ocs/v1/content/data/?search={self.query}&page={self.current_page}&categories=134x386x366x107x261"
            self.grab_theme_params(url, self.search_results)
        button.set_sensitive(False); category_box.remove(button.get_parent())
        
    def add_theme_to_list(self, title, thumbnail_url, creator, category_box, downloads, theme_url, download_links, download_names, description, index, rating):
        row = Adw.ExpanderRow(visible=False)
        category_box.append(row)

        label = Gtk.Label(label=title, xalign=0, wrap=True, width_request=320, margin_start=12)
        label.add_css_class("title-2")
        creator_label = Gtk.Label(label=creator + "\nDownloads: " + downloads, xalign=0, margin_start=12)
        creator_label.add_css_class("creator-title")
        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=10)
        label_box.append(label)
        label_box.append(creator_label)
        row.add_prefix(label_box)

        if(thumbnail_url):
            self.get_image_from_url(thumbnail_url, row)

        nested_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        button_box.add_css_class("title-4")

        rating_box = Gtk.Button(child=Gtk.Label(label=str(rating) + " ★"))
        if(rating >= 8):
            rating_box.add_css_class("success")
        elif(rating >= 6 and rating < 8):
            rating_box.add_css_class("warning")
        elif(rating < 6):
            rating_box.add_css_class("destructive-action")
        
        download_button = Gtk.Button(label="Download or Delete")
        download_button.connect("clicked", self.download_item, download_links, download_names, index)
        download_button.add_css_class(random.choice(["linear-1", "linear-2", "linear-3", "linear-4", "linear-5"]))
        
        browser_button = Gtk.Button(label="View in Browser")
        browser_button.add_css_class("suggested-action")
        browser_button.connect("clicked", self.on_view_button_clicked, theme_url)

        button_box.append(rating_box); button_box.append(download_button); button_box.append(browser_button)

        description_label = WebKit.WebView(hexpand=True)
        description_label.load_html(description)
        rounded_frame = Gtk.Frame(child=description_label)
        nested_box.append(button_box)
        nested_box.append(rounded_frame)
        row.add_row(child=nested_box)

    def on_image_recieved(self, session, result, message, row):
        bytes = session.send_and_read_finish(result)
        if(message.get_status() != Soup.Status.OK):
            raise Exception(f"Got {message.get_status()}, {message.get_reason_phrase()}")
        thumbnail_image = Gtk.Image.new_from_paintable(Gdk.Texture.new_from_bytes(bytes))
        thumbnail_image.set_pixel_size(150)
        thumbnail_image_frame = Gtk.Frame(child=thumbnail_image, margin_top=10, margin_bottom=10, margin_end=10)
        thumbnail_image_frame.add_css_class("rounded")
        row.add_suffix(thumbnail_image_frame)
        row.set_visible(True)
        self.next_page_button.set_visible(True)
        self.loading(False)

    def get_image_from_url(self, url, row):
        session = Soup.Session()
        message = Soup.Message(
            method="GET",
            uri=GLib.Uri.parse(url, GLib.UriFlags.NONE),
        )
        session.send_and_read_async(
            message, GLib.PRIORITY_DEFAULT, None, self.on_image_recieved, message, row
        )

    def loading(self, activate):
        self.spinner.set_spinning(activate)

    def download_item(self, button, download_links, download_names, index):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, buttons=Gtk.ButtonsType.CLOSE, title="Select Download Link")
        dialog.set_default_size(600, 600)
        label = Gtk.Label(label="*Larger files may cause temporary freezes, just wait until the download completes", wrap=True)
        label.add_css_class("warning")
        dialog.get_content_area().append(label)

        listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        scroll = Gtk.ScrolledWindow(vexpand=True, child=listbox)
        dialog.get_content_area().append(scroll)

        count = 0
        for link in download_links:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            label = Gtk.Label(label=download_names[count], xalign=0, margin_start=10)
            label.add_css_class("title-4")

            if(label.get_label() in self.downloaded.keys()):
                button = Gtk.Button(label="Delete", halign=Gtk.Align.END, hexpand=True)
                button.add_css_class("destructive-action")
                button.connect("clicked", self.delete_item, label.get_label(), link, self.category_index(index))
            else:
                button = Gtk.Button(label="Download", halign=Gtk.Align.END, hexpand=True)
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
                shutil.os.remove(file_path)
                print(f'ZIP file extracted successfully to {folder_path}')
            elif(tarfile.is_tarfile(file_path)):
                with tarfile.open(file_path, 'r') as tar_ref:
                    tar_ref.extractall(folder_path)
                    for member in tar_ref.getnames():
                        # Get the head folder or file
                        head_folder = member.split('/')[0]
                        head_folders.add(shutil.os.path.join(folder_path, head_folder))
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
            case("Downloaded"):
                self.selected = "down"
            case("Alphabetical"):
                self.selected = "alpha"
            case("Highest Rated"):
                self.selected = "high"
            case("New"):
                self.selected = "new"
        self.fetch_themes(self.notebook.get_current_page(), 0, "clear")

    def on_tab_changed(self, notebook, page, page_num):
        if(page_num != 5 and page_num != 6):
            self.menus.set_sensitive(True)
            self.fetch_themes(page_num, 0, "clear")
        else:
            if(page_num == 6):
                self.on_selection_changed(self.dropdown, _)
            self.menus.set_sensitive(False)

    def on_view_button_clicked(self, button, theme_url):
        webbrowser.open(theme_url)

