# install_page.py
#
# Copyright 2026 Nathan Perlman
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

import gi, os, shutil, webbrowser, json, gc
from html.parser import HTMLParser
gi.require_version('WebKit', '6.0')
gi.require_version('Xdp', '1.0')
gi.require_version('XdpGtk4', '1.0')
from gi.repository import Gtk, Gdk, Adw, Gio, GLib, WebKit, Soup, Xdp, XdpGtk4
from .utils import match_theme_type, soup_get, resolve_issues, strip_html
from datetime import datetime, timezone

data_home = os.path.join(GLib.getenv("HOME"), '.local', 'share')
picture_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)

folders = {
    0: f"{os.path.join(data_home, 'themes', 'wardrobe-installs')}",
    1: f"{os.path.join(data_home, 'icons', 'wardrobe-installs')}",
    2: f"{os.path.join(data_home, 'themes', 'wardrobe-installs')}",
    3: f"{os.path.join(data_home, 'icons', 'wardrobe-installs')}",
    4: f"{picture_dir}/",
    5: f"{GLib.get_user_data_dir()}"
}

json_path = os.path.join(folders[5], "installed.json")

def get_installed_themes():
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except:
        with open(json_path, "w") as f:
            json.dump(dict(), f, indent=2)
            return dict()

def add_theme(name, delete_paths, theme_paths):
    data = get_installed_themes()
    data[name] = (list(delete_paths), list(theme_paths))
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

def pop_theme(key):
    data = get_installed_themes()
    del data[key]
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

def make_break(title, box):
    title_label = Gtk.Label(label=_(title))
    title_label.add_css_class("title-2")
    separator = Gtk.Separator()
    box.append(separator)
    box.append(title_label)

class InstallPage(Adw.NavigationPage):
    def __init__(self, theme_button):
        super().__init__(vexpand=True, hexpand=True)
        self.signal_ids = []

        links = theme_button.download_links
        names = theme_button.download_names
        images = theme_button.image_urls
        description = theme_button.description
        content_box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=36)
        scroll = Gtk.ScrolledWindow(child=content_box)
        self.theme_type = match_theme_type(theme_button.theme_type)
        self.set_tag("install_page")

        top_box = Gtk.Box(hexpand=True, halign=Gtk.Align.CENTER, spacing=125)
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=12, spacing=8)
        title = Gtk.Label(margin_start=24, label=theme_button.title, wrap=True, halign=Gtk.Align.START)
        title.add_css_class("featured-title")
        dev_label = Gtk.Label(margin_start=24, label=_("By: ") + theme_button.dev, halign=Gtk.Align.START)
        dev_label.set_css_classes(["title-4", "dimmed"])
        web_button = Gtk.Button(icon_name="web-symbolic", valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, margin_end=24)
        web_button.set_size_request(45, 45)
        web_button.set_css_classes(["circular", "suggested-action"])
        self.connect_button(web_button, "clicked", lambda x: webbrowser.open(theme_button.home_page))

        title_box.append(title)
        title_box.append(dev_label)
        top_box.append(title_box)
        top_box.append(web_button)
        content_box.append(top_box)
        info_box = Gtk.Box(hexpand=True, margin_start=6, margin_end=6)
        info_box.set_css_classes(["card"])
        content_box.append(Adw.Clamp(child=info_box, maximum_size=750))

        download = theme_button.downloads
        score = f"{theme_button.rating}/10"
        changed = datetime.fromisoformat(theme_button.last_update).strftime("%m/%d/%Y")
        now = datetime.now(timezone.utc)
        delta = now - datetime.fromisoformat(theme_button.last_update)
        days_since = delta.days

        items = [("Downloads", download, "⤓"), ("Rating", score, "★"), ("Last Updated", changed, "⟳")]

        for tag, info, icon_name in items:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, valign=Gtk.Align.CENTER)

            icon = Gtk.Label(label=icon_name, margin_top=8)
            icon.add_css_class("title-4")

            info_label = Gtk.Label(label=str(info), xalign=0.5, hexpand=True)
            info_label.add_css_class("bold")

            tag_label = Gtk.Label(label=_(tag), xalign=0.5, margin_bottom=8)
            tag_label.add_css_class("dimmed")
            
            card.append(icon)
            card.append(info_label)
            card.append(tag_label)

            if(tag == "Downloads"):
                info_label.add_css_class("success" if int(theme_button.downloads) >= 1000 else "error")
            elif(tag == "Rating"):
                if(theme_button.rating > 7.0):
                    info_label.add_css_class("success")
                elif(theme_button.rating > 5.0):
                    info_label.add_css_class("warning")
                else:
                    info_label.add_css_class("error")
            elif(tag == "Last Updated"):
                info_label.add_css_class("error" if days_since >= 365 else "success")

            info_box.append(card)
            if(tag != "Last Updated"):
                info_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL, margin_top=8, margin_bottom=8))

        make_break("Screenshots", content_box)

        carousel = Adw.Carousel(allow_scroll_wheel=False, height_request=280)
        carousel.add_css_class("card")
        self.make_carousel_images(images, carousel)

        overlay = Gtk.Overlay()
        overlay.set_child(carousel)

        left_button = Gtk.Button(icon_name="go-previous-symbolic", valign=Gtk.Align.CENTER, halign=Gtk.Align.START, margin_start=12)
        left_button.set_css_classes(["circular", "osd"])
        left_button.set_margin_start(12)

        right_button = Gtk.Button(icon_name="go-next-symbolic", valign=Gtk.Align.CENTER, halign=Gtk.Align.START, margin_start=12)
        right_button.set_css_classes(["circular", "osd"])
        right_button.set_margin_end(12)

        overlay.add_overlay(left_button)
        overlay.add_overlay(right_button)
        content_box.append(overlay)

        def scroll_to(button, direction):
            try:
                carousel.scroll_to(carousel.get_nth_page(carousel.get_position() + direction), True)
            except:
                if(carousel.get_position() + direction < 0):
                    carousel.scroll_to(carousel.get_nth_page(carousel.get_n_pages() - 1), True)
                else:
                    carousel.scroll_to(carousel.get_nth_page(0), True)

        self.connect_button(left_button, "clicked", scroll_to, -1)
        self.connect_button(right_button, "clicked", scroll_to, 1)

        content_box.append(Gtk.Separator())
        description_label = Gtk.Label(label=strip_html(description), wrap=True, selectable=True)
        description_label.set_css_classes(["description-label", "view"])
        content_box.append(description_label)

        make_break("Install Theme", content_box)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        label = Gtk.Label(label=_("Save Folder"))
        icon = Gtk.Image.new_from_icon_name("folder-open-symbolic")
        box.append(label); box.append(icon)
        open_folder_button = Gtk.Button(child=box, halign=Gtk.Align.CENTER)
        open_folder_button.set_css_classes(["suggested-action", "pill"])
        folder = Gio.File.new_for_path(folders[self.theme_type])
        self.connect_button(open_folder_button, "clicked", lambda d: Gio.AppInfo.launch_default_for_uri(folder.get_uri(), None))
        content_box.append(open_folder_button)

        download_list = Gtk.ListBox(hexpand=True, margin_start=24, margin_end=24, margin_bottom=24)
        download_list.add_css_class("boxed-list")

        link_row = Gtk.ListBoxRow()
        link_row.set_child(Gtk.LinkButton(label=_("Become a supporter"), uri="https://www.pling.com/support"))
        download_list.append(link_row)

        installed = get_installed_themes()
        for name, link in zip(names, links):
            row = Adw.ActionRow(title=name)
            suffix_box = Gtk.Box()
            if(name in installed.keys()):
                suffix_button = Gtk.Button(icon_name="delete-symbolic")
                suffix_button.add_css_class("destructive-action")
                self.connect_button(suffix_button, "clicked", self.delete_theme, installed[name][0])
                use_button = self.set_use_menu_button(installed[name][1])
                suffix_box.append(use_button)
            else:
                suffix_button = Gtk.Button(icon_name="download-symbolic")
                suffix_button.add_css_class("suggested-action")
                self.connect_button(suffix_button, "clicked", self.install_theme, link, name, self.theme_type)
            suffix_box.append(suffix_button)
            suffix_button.add_css_class("circular")
            suffix_button.link = link
            suffix_button.name = name
            suffix_button.set_valign(Gtk.Align.CENTER)
            row.add_suffix(suffix_box)
            download_list.append(row)
        content_box.append(Adw.Clamp(child=download_list, maximum_size=500))
        self.set_child(scroll)

    def connect_button(self, widget, signal, handler, *args):
        signal_id = widget.connect(signal, handler, *args)
        self.signal_ids.append((widget, signal_id))
        return signal_id

    def clean(self):
        for widget, signal_id in self.signal_ids:
            widget.disconnect(signal_id)
        self.signal_ids.clear()
        gc.collect()

    def make_carousel_images(self, images, carousel):
        carousel.add_css_class("view")
        def on_receive_bytes(session, result, message):
            bytes = session.send_and_read_finish(result)
            if(message.get_status() != Soup.Status.OK):
                raise Exception(f"Got {message.get_status()}, {message.get_reason_phrase()}")
            texture = Gdk.Texture.new_from_bytes(bytes)
            picture = Gtk.Picture.new_for_paintable(texture)
            picture.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
            picture.set_margin_top(12)
            picture.set_margin_bottom(12)
            picture.set_margin_start(12)
            picture.set_margin_end(12)
            carousel.append(picture)

        def get_image_bytes(url):
            session = Soup.Session()
            message = Soup.Message(
                method="GET",
                uri=GLib.Uri.parse(url, GLib.UriFlags.NONE),
            )
            session.send_and_read_async(
                message, GLib.PRIORITY_DEFAULT, None, on_receive_bytes, message
            )

        for image in images:
            get_image_bytes(image)

    def change_button_to_download(self, button):
        button.disconnect_by_func(self.delete_theme)
        button.remove_css_class("destructive-action")
        button.add_css_class("suggested-action")
        button.set_icon_name("download-symbolic")
        self.connect_button(button, "clicked", self.install_theme, button.link, button.name, self.theme_type)

        first_child = button.get_parent().get_first_child()
        if(first_child != button):
            button.get_parent().remove(first_child)

    def set_theme(self, button):
        interface_settings = Gio.Settings(schema_id="org.gnome.desktop.interface")
        chosen_item = button.get_label()
        match self.theme_type:
            case 0:
                print("feature currently unavailable")
            case 1:
                interface_settings.set_string("icon-theme", os.path.basename(chosen_item))
            case 2:
                interface_settings.set_string("gtk-theme", os.path.basename(chosen_item))
            case 3:
                interface_settings.set_string("cursor-theme", os.path.basename(chosen_item))
            case 4:
                portal = Xdp.Portal()
                parent = XdpGtk4.parent_new_gtk(self)
                portal.set_wallpaper(
                    parent,
                    f"file://{chosen_item}",
                    Xdp.WallpaperFlags.PREVIEW | Xdp.WallpaperFlags.BACKGROUND | Xdp.WallpaperFlags.LOCKSCREEN
                )

    def set_use_menu_button(self, themes):
        use_button = Gtk.MenuButton(label=(_("Use")), margin_end=8, halign=Gtk.Align.END, valign=Gtk.Align.CENTER)
        items = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        popover = Gtk.Popover()
        popover.set_child(items)
        for item in themes:
            if(self.theme_type != 4):
                theme = Gtk.Button(label=os.path.basename(item))
            else:
                theme = Gtk.Button(label=item)
            theme.add_css_class("flat")
            self.connect_button(theme, "clicked", self.set_theme)
            items.append(theme)
        use_button.set_popover(popover)
        return use_button

    def install_theme(self, button, url, name, typeid):
        def change_button_to_delete(delete_paths, theme_paths):
            button.disconnect_by_func(self.install_theme)
            button.remove_css_class("suggested-action")
            button.add_css_class("destructive-action")
            button.set_icon_name("delete-symbolic")
            self.connect_button(button, "clicked", self.delete_theme, delete_paths)

            use_button = self.set_use_menu_button(theme_paths)
            button.get_parent().prepend(use_button)
            add_theme(button.name, delete_paths, theme_paths)

        def on_download(response):
            download_path = os.path.join(folders[self.theme_type], name)
            os.makedirs(folders[self.theme_type], exist_ok=True)
            with open(download_path, "wb") as file:
                file.write(response)
            resolve_issues(download_path, typeid, change_button_to_delete)

        button.set_child(Gtk.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, spinning=True))
        soup_get(url, on_download)

    def delete_theme(self, button, delete_paths):
        self.change_button_to_download(button)
        pop_theme(button.name)
        for item in delete_paths:
            if(os.path.isdir(item)):
                shutil.rmtree(item)
            else:
                os.remove(item)
