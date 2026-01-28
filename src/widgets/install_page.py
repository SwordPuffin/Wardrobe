import gi, os, shutil, webbrowser, json
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, Gdk, Adw, Gio, GLib, WebKit, Soup
from .utils import match_theme_type, soup_get, resolve_issues
from datetime import datetime, timezone

data_dir = os.path.join(GLib.getenv("HOME"), ".local", "share") #Should be ~/.local/share
picture_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES) #Typically ~/Pictures

folders = {
    0: f"{data_dir}/themes/wardrobe-installs",
    1: f"{data_dir}/icons/wardrobe-installs",
    2: f"{data_dir}/themes/wardrobe-installs",
    3: f"{data_dir}/icons/wardrobe-installs",
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

def get_theme_path(key):
    data = get_installed_themes()
    return data[key]

def add_theme(name, paths):
    data = get_installed_themes()
    data[name] = list(paths)
    print("Data: " + str(data))
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

        links = theme_button.download_links
        names = theme_button.download_names
        images = theme_button.image_urls
        description = theme_button.description
        content_box = Gtk.Box(vexpand=True, hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=36)
        scroll = Gtk.ScrolledWindow(child=content_box)
        self.theme_type = match_theme_type(theme_button.theme_type)
        self.set_tag("install_page")

        title = Gtk.Label(label=theme_button.title, wrap=True)
        title.add_css_class("title-1")
        content_box.append(title)

        info_box = Gtk.FlowBox(
            hexpand=True,
            margin_start=12,
            margin_end=12,
            selection_mode=Gtk.SelectionMode.NONE,
            can_target=False,
            max_children_per_line=2,
            row_spacing=12
        )

        info_box.add_css_class("info-row")
        content_box.append(Adw.Clamp(child=info_box, maximum_size=750))

        dev = theme_button.dev
        download = theme_button.downloads
        score = f"{theme_button.rating}/10 ★"
        changed = datetime.fromisoformat(theme_button.last_update).strftime("%b %d, %Y")

        now = datetime.now(timezone.utc)
        delta = now - datetime.fromisoformat(theme_button.last_update)
        days_since = delta.days

        items = [
            ("Creator", dev),
            ("Downloads", download),
            ("Rating", score),
            ("Last updated", changed),
        ]

        for i, (tag, info) in enumerate(items):
            part = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, spacing=2, height_request=50)

            info_label = Gtk.Label(label=str(info), xalign=0.5, hexpand=True, vexpand=True)
            info_label.add_css_class("title-4")

            tag_label = Gtk.Label(label=_(tag), xalign=0.5, yalign=0.3, vexpand=True)
            tag_label.add_css_class("dim-label")

            part.append(info_label)
            part.append(tag_label)

            top_level = Gtk.Button(child=part)
            if(tag == "Creator"):
                top_level.add_css_class("accent")
            elif(tag == "Downloads" and int(theme_button.downloads) < 1000):
                top_level.add_css_class("destructive-action")
            elif(tag == "Downloads" and int(theme_button.downloads) >= 1000):
                top_level.add_css_class("success")
            elif(tag == "Rating" and theme_button.rating <= 5.0):
                top_level.add_css_class("destructive-action")
            elif(tag == "Rating" and theme_button.rating > 5.0 and theme_button.rating <= 7.0):
                top_level.add_css_class("warning")
            elif(tag == "Rating" and theme_button.rating > 7.0):
                top_level.add_css_class("success")
            elif(tag == "Last updated" and days_since >= 365):
                top_level.add_css_class("destructive-action")
            elif(tag == "Last updated" and days_since < 365):
                top_level.add_css_class("success")

            info_box.insert(top_level, -1)

        make_break("Screenshots", content_box)

        carousel = Adw.Carousel(
            allow_scroll_wheel=False,
            height_request=280
        )
        carousel.add_css_class("card")

        self.make_carousel_images(images, carousel)

        overlay = Gtk.Overlay()
        overlay.set_child(carousel)

        left_button = Gtk.Button(icon_name="go-previous-symbolic")
        left_button.add_css_class("circular")
        left_button.add_css_class("osd")
        left_button.set_valign(Gtk.Align.CENTER)
        left_button.set_halign(Gtk.Align.START)
        left_button.set_margin_start(12)

        right_button = Gtk.Button(icon_name="go-next-symbolic")
        right_button.add_css_class("circular")
        right_button.add_css_class("osd")
        right_button.set_valign(Gtk.Align.CENTER)
        right_button.set_halign(Gtk.Align.END)
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

        left_button.connect("clicked", scroll_to, -1)
        right_button.connect("clicked", scroll_to, 1)

        make_break("Description", content_box)

        description_box = WebKit.WebView(height_request=250)
        description_box.get_settings().set_enable_javascript(False)
        description_box.connect("decide-policy", self.on_decide_policy)
        # description += f"\n\n<style>html, body {{background-color: {get_default_colors(content_box)[0]}; color: {get_default_colors(content_box)[1]};}}</style>"
        description_box.load_html(description)
        content_box.append(Gtk.Frame(child=description_box, margin_start=24, margin_end=24))

        make_break("Download/Delete Theme", content_box)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        label = Gtk.Label(label=_("Save Folder"))
        icon = Gtk.Image.new_from_icon_name("folder-open-symbolic")
        box.append(label); box.append(icon)
        open_folder_button = Gtk.Button(child=box, halign=Gtk.Align.CENTER)
        open_folder_button.set_css_classes(["suggested-action", "pill"])
        folder = Gio.File.new_for_path(folders[self.theme_type])
        open_folder_button.connect("clicked", lambda d : Gio.AppInfo.launch_default_for_uri(folder.get_uri(), None))
        content_box.append(open_folder_button)

        download_list = Gtk.ListBox(hexpand=True, margin_start=24, margin_end=24, margin_bottom=24)
        download_list.add_css_class("boxed-list")

        link_row = Gtk.ListBoxRow()
        link_row.set_child(Gtk.LinkButton(label=_("Become a supporter"), uri="https://www.pling.com/support"))
        download_list.append(link_row)
        installed = get_installed_themes()
        for name, link in zip(names, links):
            if('.' not in name):
                continue
            row = Adw.ActionRow(title=name)
            if(name in installed.keys()):
                suffix_button = Gtk.Button(icon_name="delete-symbolic")
                suffix_button.add_css_class("destructive-action")
                suffix_button.connect("clicked", self.delete_theme, installed[name])
            else:
                suffix_button = Gtk.Button(icon_name="download-symbolic")
                suffix_button.add_css_class("suggested-action")
                suffix_button.connect("clicked", self.install_theme, link, name, self.theme_type)
            suffix_button.add_css_class("circular")
            suffix_button.link = link; suffix_button.name = name
            suffix_button.set_valign(Gtk.Align.CENTER)
            row.add_suffix(suffix_button)
            download_list.append(row)

        content_box.append(Adw.Clamp(child=download_list, maximum_size=500))
        self.set_child(scroll)

    def on_decide_policy(self, webview, decision, decision_type):
        if(decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION):
            nav = decision.get_navigation_action()
            if(nav.get_navigation_type() == WebKit.NavigationType.LINK_CLICKED):
                request = nav.get_request()
                uri = request.get_uri()
                webbrowser.open(uri)

        if(decision_type == 2):
            decision.ignore()

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
        button.connect("clicked", self.install_theme, button.link, button.name, self.theme_type)

    def install_theme(self, button, url, name, typeid):
        def change_button_to_delete(delete_paths):
            button.disconnect_by_func(self.install_theme)
            button.remove_css_class("suggested-action")
            button.add_css_class("destructive-action")
            button.set_icon_name("delete-symbolic")
            button.connect("clicked", self.delete_theme, delete_paths)
            add_theme(button.name, delete_paths)

        def on_download(response):
            download_path = os.path.join(folders[self.theme_type], name)
            os.makedirs(folders[self.theme_type], exist_ok=True)
            with open(download_path, "wb") as file:
                file.write(response)
            resolve_issues(download_path, typeid, change_button_to_delete)
        button.set_child(Gtk.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, spinning=True))
        soup_get(url, on_download)

    def delete_theme(self, button, theme_paths):
        self.change_button_to_download(button)
        pop_theme(button.name)
        for item in theme_paths:
            if(os.path.isdir(item)):
                shutil.rmtree(item)
            else:
                os.remove(item)



