import gi, random
from gi.repository import Gtk, Adw, Soup, GLib, Gdk
from .install_page import InstallPage

class ThemeCell(Gtk.Box):
    session = Soup.Session()
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, height_request=350)
        self.add_css_class("card")

    def set_thumbnail_image(self, session, result):
        bytes = self.session.send_and_read_finish(result)
        texture = Gdk.Texture.new_from_bytes(bytes)
        foreground = Gtk.Picture.new_for_paintable(texture)
        foreground.set_content_fit(Gtk.ContentFit.CONTAIN)

        foreground.set_margin_bottom(6)
        foreground.set_margin_top(6)
        foreground.set_margin_start(12)
        foreground.set_margin_end(12)

        background = Gtk.Picture.new_for_paintable(texture)
        background.add_css_class("blur")
        background.set_content_fit(Gtk.ContentFit.COVER)
        background.set_valign(Gtk.Align.FILL)
        background.set_halign(Gtk.Align.FILL)

        overlay = Gtk.Overlay(hexpand=True, vexpand=True, height_request=280, margin_bottom=6)
        overlay.set_child(Gtk.Frame(child=background))
        overlay.add_overlay(foreground)

        self.append(overlay)
        self.append(self.make_bottom_box())

    def make_bottom_box(self):
        def on_get_button_clicked(button):
            install_page = InstallPage(self)
            self.page.add(install_page)
            self.page.push(install_page)

        bottom_box = Gtk.Box(hexpand=True, valign=Gtk.Align.CENTER)
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, margin_start=12, spacing=2, margin_bottom=8)

        title_label = Gtk.Label(label=self.title, xalign=0.0, wrap=True)
        title_label.add_css_class("title-4")

        dev_label = Gtk.Label(label=_("By: ") + self.dev, xalign=0.0)
        dev_label.add_css_class("dimmed")

        download_label = Gtk.Label(label=_("Downloads: ") + self.downloads, xalign=0.0)
        download_label.add_css_class("dimmed")

        text_box.append(title_label)
        text_box.append(dev_label)
        text_box.append(download_label)

        get_button = Gtk.Button(label=_("Get"), hexpand=True, vexpand=True, margin_end=12, valign=Gtk.Align.CENTER, halign=Gtk.Align.END)
        get_button.set_css_classes(["pill", "suggested-action"])
        get_button.connect("clicked", on_get_button_clicked)

        bottom_box.append(text_box)
        bottom_box.append(get_button)

        return bottom_box

    def build_cell(self):
        url = self.image_urls[0]
        message = Soup.Message(method="GET", uri=GLib.Uri.parse(url, GLib.UriFlags.NONE))
        self.session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, None, self.set_thumbnail_image)








