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

import os, shutil
#Some theme developers do not package the folders in their theme in the correct order
#arrange_folders moves everything into the right order
folders = {
    0: ["gnome-shell"],
    2: ["gtk-2.0", "gnome-shell", "gtk-3.0", "gtk-4.0", "cinnamon", "xfwm4", "index.theme"],
    3: ["cursors", "cursors_scalable", "index.theme"]
}

def arrange_folders(download_dir, theme_dir, index, name):
    try:
        print(folders[index])
    except Exception:
        return # Does not verify icon themes and wallpapers
    print(download_dir)
    os.mkdir(name + "-wardrobe_install"); new_path = name + "-wardrobe_install"
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
                    #There should not be a preexisting folder with the same name unless the creator has packaged the theme REALLY weirdly
                    try:
                        shutil.move(found_path, os.path.join(new_path, folder_name))
                    except Exception:
                        continue
    shutil.rmtree(name)
    os.rename(new_path, new_path.replace("-wardrobe_install", ""))

def extract_folders(archive_path, extract_to):
    before = set(os.listdir(extract_to)) if os.path.exists(extract_to) else set()

    # os.chdir(extract_to)
    # libarchive.extract_file(archive_path)

    shutil.unpack_archive(archive_path, extract_to)

    # Get the directory contents after extraction
    after = set(os.listdir(extract_to))
    added = after - before

    head_folders = set()
    for item in added:
        item_path = os.path.join(extract_to, item)
        if(os.path.isdir(item_path)):
            print(f"Extracted folder: {item_path}")
            head_folders.add(item_path)
    return head_folders

wallpaper_paths = dict()
def _get_valid_shell_themes():
    valid = []
    for dirs in [f"{os.path.expanduser('~')}/.themes/", f"/run/host/usr/share/themes", f"{os.path.expanduser('~')}/.local/share/themes"]:
        valid += walk_directories(dirs, lambda d: "/gnome-shell " in d)
    return set(valid)

def _get_valid_gtk_themes():
    """ Only shows themes that have variations for gtk3"""
    valid = ['Adwaita', 'HighContrast', 'HighContrastInverse']
    for dirs in [f"{os.path.expanduser('~')}/.themes/", f"/run/host/usr/share/themes", f"{os.path.expanduser('~')}/.local/share/themes"]:
        valid += walk_directories(dirs, lambda d: "gtk-3." in d)
    return set(valid)

def _get_valid_icon_themes():
    valid = []
    for dirs in [f"{os.path.expanduser('~')}/.icons/", f"/run/host/usr/share/icons", f"{os.path.expanduser('~')}/.local/share/icons"]:
        valid += walk_directories(dirs, lambda d: "index.theme " in d)
    return set(valid)

def _get_valid_cursor_themes():
    valid = []
    for dirs in [f"{os.path.expanduser('~')}/.icons/", f"/run/host/usr/share/icons", f"{os.path.expanduser('~')}/.local/share/icons"]:
        valid += walk_directories((dirs), lambda d: "cursors " in d)
    return set(valid)

def _get_valid_wallpapers():
    valid = []
    for dirname, _, filenames in os.walk(f"{os.path.expanduser('~')}/Pictures/"):
        for file in filenames:
            if any(ext in file for ext in [".png", ".jpg", ".svg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"]):
                valid.append(file)
                wallpaper_paths[file] = dirname
    return valid

def walk_directories(dirs, filter_func):
    valid = []
    try:
        if os.path.exists(dirs):
            for thdir in os.listdir(dirs):
                full_thdir = os.path.join(dirs, thdir)
                if os.path.isdir(full_thdir):
                    for t in os.listdir(full_thdir):
                        full_t = os.path.join(full_thdir, t + " ")
                        if filter_func(full_t):
                            valid.append(thdir)
    except:
        print("Error parsing directories", exc_info=True)
    return valid

css = """
    .rounded {
        border-radius: 30px;
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

