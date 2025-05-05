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
