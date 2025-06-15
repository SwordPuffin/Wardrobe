# utils.py
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

import os, shutil, gi, random

gi.require_version('GnomeAutoar', '0.1')
from gi.repository import GnomeAutoar, Gio, GLib, Gdk, Gtk, GdkPixbuf

#Some theme developers do not package the folders in their theme in the correct order
#arrange_folders moves everything into the right order
def arrange_folders(archive_path, theme_dir, index, save_function):
    check_path = os.path.dirname(theme_dir)
    for item in os.listdir(check_path): #removes null symlinks
        if(os.path.islink(os.path.join(check_path, item))):
            if(not os.path.exists(os.readlink(os.path.join(check_path, item)))):
                os.unlink(os.path.join(check_path, item))

    before = set(os.listdir(theme_dir)) if os.path.exists(theme_dir) else set()
    archive_file = Gio.File.new_for_path(archive_path)
    destination_dir = Gio.File.new_for_path(theme_dir)
    extractor = GnomeAutoar.Extractor.new(archive_file, destination_dir)
    extractor.set_delete_after_extraction(True)

    def resolve_conflicts(extractor, before, archive_path, theme_dir, index, save_function):
        # Get the directory contents after extraction
        after = set(os.listdir(theme_dir))
        added = after - before

        head_folders = set()
        for item in added:
            item_path = os.path.join(theme_dir, item)
            if(os.path.isdir(item_path)):
                print(f"Extracted folder: {item_path}")
                head_folders.add(item_path)

        folders = {
            0: ["gnome-shell"],
            2: ["gtk-2.0", "gnome-shell", "gtk-3.0", "gtk-4.0", "cinnamon", "xfwm4", "index.theme"],
            3: ["cursors", "cursors_scalable", "index.theme"]
        }

        for download_dir in head_folders:
            if(index == 4):
                save_function(head_folders) # Does not verify wallpapers
                return
            elif(index == 1):
                icon_folders = os.listdir(download_dir)
                added = {}
                before = set(os.listdir(check_path)) if os.path.exists(check_path) else set()
                if('index.theme' not in icon_folders):
                    for folder in os.listdir(download_dir): #This is all to prevent file conflicts
                        extension = ""
                        if('dark' in folder.lower()):
                          extension = '-dark'
                        elif('light' in folder.lower()):
                          extension = '-light'
                        parent_name = os.path.basename(download_dir).lower()
                        correct_folder_name = folder.lower().replace(extension, '')
                        if(parent_name in correct_folder_name):
                            new_folder_name = correct_folder_name + extension
                        elif(correct_folder_name in parent_name):
                            new_folder_name = parent_name + extension
                        else:
                            new_folder_name = folder + '-' + str(random.getrandbits(8))
                        os.symlink(os.path.join(download_dir, folder), f"{os.path.dirname(theme_dir)}/" + f"{os.path.basename(new_folder_name)}")
                    for index, item in zip(range(len(added)), added):
                        added[index] = shutil.os.path.join(theme_dir, item)
                else:
                    os.symlink(download_dir, f"{os.path.dirname(theme_dir)}/" + f"{os.path.basename(download_dir)}")
                after = set(os.listdir(check_path))
                added = list(after - before)
                save_function(list(head_folders.union(set(added))))
                return
            os.mkdir(download_dir + "-wardrobe_install"); new_path = download_dir + "-wardrobe_install"
            for folder_name in folders[index]:
                for root, dirs, files in os.walk(download_dir, topdown=False):
                    if(folder_name == "index.theme"):
                        search = files
                    else:
                        search = dirs
                    for d in search:
                        if(d == folder_name):
                            found_path = os.path.join(root, d)
                            print(f"Found {folder_name} at: {found_path}")
                            print(f"Moving to: {new_path}")
                            try:
                                shutil.move(found_path, os.path.join(new_path, folder_name))
                            except Exception:
                                continue
            shutil.rmtree(download_dir)
            os.rename(new_path, new_path.replace("-wardrobe_install", ""))
            os.symlink(new_path.replace("-wardrobe_install", ""), f"{os.path.dirname(theme_dir)}/" + f"{os.path.basename(new_path.replace('-wardrobe_install', ''))}")
            head_folders.add(os.path.basename(new_path.replace('-wardrobe_install', '')))
            save_function(head_folders)
            return

    extractor.start_async()
    extractor.connect("completed", resolve_conflicts, before, archive_path, theme_dir, index, save_function)

css = """
    .rounded {
      border-radius: 25px;
      border: 0px solid;
    }
    .creator-title {
        opacity: 0.65;
        font-size: 12pt;
        font-weight: 600;
    }
    .browser_button {
        background-color: var(--green-1);
        color: var(--dark-5);
    }
    .card {
        border: 0px solid;
    }
"""
