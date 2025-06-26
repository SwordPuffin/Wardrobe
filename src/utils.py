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

def search_for_images(folders):
    return_val = []
    for folder in folders:
        if(shutil.os.path.isdir(folder)):
            for root, dirs, files in shutil.os.walk(folder):
                for file in files:
                    if(any(ext in file for ext in [".png", ".jpg", ".svg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".jxl"])):
                        print(shutil.os.path.join(root, file))
                        return_val.append(shutil.os.path.join(root, file))
        else:
            return_val.append(folder)
    return return_val

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
        folders = {
            0: ["gnome-shell"],
            1: ["index.theme"],
            2: ["gtk-2.0", "gnome-shell", "gtk-3.0", "gtk-4.0", "cinnamon", "xfwm4", "index.theme"],
            3: ["cursors", "cursors_scalable", "index.theme"]
        }

        after = set(os.listdir(theme_dir))
        added = list(after - before)
        head_folders = set()

        for item in added:
            item_path = os.path.join(theme_dir, item)
            if(os.path.isdir(item_path)):
                print(f"Extracted folder: {item_path}")
                head_folders.add(item_path)

        if(index == 4):
            save_function(list(head_folders), search_for_images(list(head_folders)))
            return
        important_paths = set()
        before = set(os.listdir(check_path)) if os.path.exists(check_path) else set()
        for download_dir in head_folders:
            for root, dirs, files in os.walk(download_dir, topdown=False):
                for folder_name in folders[index]:
                    if(folder_name == "index.theme"):
                        search = files
                    else:
                        search = dirs
                    for item in search:
                        if(item == folder_name):
                            print("Found: " + item)
                            important_paths.add(os.path.dirname(os.path.join(root, item)))
        print(important_paths)
        if(index == 0 or index == 2 or index == 3):
            for path in important_paths:
                try:
                    os.symlink(path, f"{os.path.dirname(theme_dir)}/" + f"{os.path.basename(path)}")
                except:
                    continue
        elif(index == 1):
            for path in important_paths:
                extension = ""
                folder = os.path.basename(path)
                if('dark' in folder.lower()):
                  extension = '-dark'
                elif('light' in folder.lower()):
                  extension = '-light'
                parent_name = os.path.basename(os.path.dirname(path)).lower()
                correct_folder_name = folder.lower().replace(extension, '')
                if(parent_name in correct_folder_name):
                    new_folder_name = correct_folder_name + extension
                elif(correct_folder_name in parent_name):
                    new_folder_name = parent_name + extension
                else:
                    new_folder_name = folder + '-' + str(random.getrandbits(8))
                os.symlink(path, f"{os.path.dirname(theme_dir)}/" + f"{os.path.basename(new_folder_name)}")
        after = set(os.listdir(check_path))
        added = list(after - before)
        for pos, item in zip(range(len(added)), added):
            added[pos] = shutil.os.path.join(check_path, item)

        save_function(list(head_folders), added)

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
