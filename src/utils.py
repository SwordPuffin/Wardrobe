#Some of the code in this file is taken from the official Gnome-Tweaks app with some minor adaptations 
#https://gitlab.gnome.org/GNOME/gnome-tweaks

import os, logging, subprocess
from gi.repository import Gtk

wallpaper_paths = dict()
def _get_valid_shell_themes():
    valid = []
    for dirs in [f"{os.path.expanduser('~')}/.themes/", f"/run/host/usr/share/themes"]:
        valid += walk_directories(dirs, lambda d: "/gnome-shell " in d)
    return set(valid)

def _get_valid_gtk_themes():
    """ Only shows themes that have variations for gtk3"""
    valid = ['Adwaita', 'HighContrast', 'HighContrastInverse']
    for dirs in [f"{os.path.expanduser('~')}/.themes/", f"/run/host/usr/share/themes"]:
        valid += walk_directories(dirs, lambda d: "gtk-3." in d)
    return set(valid)
    
def _get_valid_icon_themes():
    valid = []
    for dirs in [f"{os.path.expanduser('~')}/.icons/", f"/run/host/usr/share/icons"]:
        valid += walk_directories(dirs, lambda d: "index.theme " in d)
    return set(valid)

def _get_valid_cursor_themes():
    valid = []
    for dirs in [f"{os.path.expanduser('~')}/.icons/", f"/run/host/usr/share/icons"]:
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
        logging.critical("Error parsing directories", exc_info=True)
    return valid

css = """
    .linear-1 {
      background-image: linear-gradient(90deg
        var(--red-1),
        var(--blue-1)
      );
    }
    .linear-2 {
      background-image: linear-gradient(90deg
        var(--red-2),
        var(--purple-2),
        var(--blue-2)
      );
    }
    .linear-3 {
      background-image: linear-gradient(90deg
        var(--yellow-2),
        var(--orange-3),
        var(--red-1)
      );
    }
    .linear-4 {
      background-image: linear-gradient(90deg
        var(--green-4),
        var(--blue-4),
        var(--purple-2)
      );
    }
    .linear-5 {
      background-image: linear-gradient(90deg
        var(--green-5),
        var(--yellow-2)
      );
    }
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
"""
