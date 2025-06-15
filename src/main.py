# main.py
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

import sys, gi, json

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib
from .window import WardrobeWindow

class WardrobeApplication(Adw.Application):
    """The main application singleton class."""
    def __init__(self):
        super().__init__(application_id='io.github.swordpuffin.wardrobe',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = WardrobeWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        about = Adw.AboutDialog(application_name='Wardrobe',
                                application_icon='io.github.swordpuffin.wardrobe',
                                developer_name='Nathan Perlman',
                                version='1.0.9',
                                developers=['Nathan Perlman'],
                                copyright='© 2025 Nathan Perlman')
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        dialog = Gtk.MessageDialog(modal=True, transient_for=self.props.active_window, buttons=Gtk.ButtonsType.CLOSE)
        dialog.set_default_size(500, 200)

        carousel_adjustment = Gtk.Adjustment(value=WardrobeWindow.carousel_image_count, lower=0, upper=5, step_increment=1)
        carousel_spinner = Gtk.SpinButton(adjustment=carousel_adjustment)
        cell_adjustment = Gtk.Adjustment(value=WardrobeWindow.cell_count, lower=2, upper=10, step_increment=1)
        cell_spinner = Gtk.SpinButton(adjustment=cell_adjustment)

        content = dialog.get_content_area()
        content.set_spacing(12)
        content.set_margin_top(30)
        content.set_margin_bottom(10)
        content.set_margin_start(25)
        content.set_margin_end(25)
        frame = Gtk.Frame(child=Gtk.Label(label="Less items will load faster, and take up less system resources.\nBut you may have less context about downloaded content."))
        frame.add_css_class("card")
        content.prepend(frame)

        carousel_label = Gtk.Label(label="Number of carousel images to show for each theme:", margin_top=15)
        content.append(carousel_label)
        content.append(carousel_spinner)

        cell_label = Gtk.Label(label="Number of themes to present on one page:", margin_top=30)
        content.append(cell_label)
        content.append(cell_spinner)

        title = Gtk.Label(label="Preferences", margin_bottom=30)
        title.add_css_class("title-3")
        content.prepend(title)

        dialog.connect(
            "response",
            lambda d, r: self.preferences_save(d, cell_spinner.get_value_as_int(), carousel_spinner.get_value_as_int())
        )
        dialog.show()

    def preferences_save(self, dlg, cell, carousel):
        with open(f"{GLib.get_user_data_dir()}/prefs.json", "w") as file:
            json.dump({"cell_count": cell, "carousel_image_count": carousel}, file, indent=4)
            WardrobeWindow.cell_count = cell
            WardrobeWindow.carousel_image_count = carousel
        dlg.destroy()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = WardrobeApplication()
    return app.run(sys.argv)
