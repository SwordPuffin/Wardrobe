import gi, os, random, xml.etree.ElementTree as ET
gi.require_version('GnomeAutoar', '0.1')
from gi.repository import GnomeAutoar, Soup, GLib, Gtk, Gdk, Gio, Adw
from pathlib import Path

def clear_broken_symlinks(directory):
    for entry in Path(directory).iterdir():
        if(entry.is_symlink() and not entry.exists()):
            entry.unlink()

def soup_get(url, response_func):
    def on_response(session, result):
        response_bytes = session.send_and_read_finish(result)
        try:
            response_text = response_bytes.get_data().decode()
        except:
            response_text = response_bytes.get_data()
        response_func(response_text)
    session = Soup.Session()
    message = Soup.Message.new("GET", url)
    session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, None, on_response)

def match_theme_type(typeid):
    category_map = {
        134: 0, 386: 1, 199: 1, 132: 1, 366: 2, 135: 2, 136: 2,
        107: 3, 300: 4, 261: 4, 299: 4, 360: 4
    }
    return category_map.get(int(typeid), int(typeid))

def resolve_issues(archive_path, typeid, change_func):
    archive_file = Gio.File.new_for_path(archive_path)
    output = os.path.dirname(archive_file)
    theme_dir = os.path.dirname(output)
    gio_output = Gio.File.new_for_path(output)
    before = set(os.listdir(output))
    def arrange_folders(extractor):
        folders = {
            0: ["gnome-shell"],
            1: ["index.theme"],
            2: ["gtk-2.0", "gnome-shell", "gtk-3.0", "gtk-4.0", "cinnamon", "xfwm4", "index.theme"],
            3: ["cursors", "cursors_scalable", "index.theme"]
        }

        if(typeid == 4):
            return
        else:
            important_items = folders.get(typeid)

        # I can't tell if this code is very good or very bad
        after = set(os.listdir(output))
        added = set()
        for item in after - before:
            item_path = os.path.join(output, item)
            if(os.path.isdir(item_path)):
                added.add(item_path)
        important_paths = set()
        for folder in added:
            for root, dirs, files in os.walk(folder, topdown=False):
                for folder_name in important_items:
                    if(folder_name == "index.theme"):
                        search = files
                    else:
                        search = dirs
                    for item in search:
                        if(item == folder_name):
                            important_paths.add(os.path.dirname(os.path.join(root, item)))
        if(typeid != 1):
            for path in important_paths:
                try:
                    os.symlink(path, os.path.join(theme_dir, os.path.basename(path)))
                except:
                    continue
        else:
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
                    new_folder_name = folder + '-' + str(random.randint(1, 1000))
                os.symlink(path, os.path.join(theme_dir, os.path.basename(new_folder_name)))
        change_func(added)

    clear_broken_symlinks(theme_dir)
    extractor = GnomeAutoar.Extractor.new(archive_file, gio_output)
    extractor.set_delete_after_extraction(True)

    extractor.start_async()
    extractor.connect("completed", arrange_folders)

def parse_xml(xml, flowbox):
    from .theme_cell import ThemeCell
    root = ET.fromstring(xml)
    content = root.findall(".//content")

    for item in content:
        cell = ThemeCell()
        cell.page = flowbox.page
        cell.title = item.find("name").text if item.find("name") is not None else "Unknown"
        cell.home_page = item.find("detailpage").text if item.find("detailpage") is not None else ""
        cell.dev = item.find("personid").text if item.find("personid") is not None else "Unknown"
        cell.rating = int(item.find("score").text) / 10 if item.find("score") is not None else 0
        cell.last_update = item.find("changed").text if item.find("changed") is not None else ""
        cell.description = item.find("description").text if item.find("description") is not None else ""
        cell.downloads = item.find("downloads").text if item.find("downloads").text is not None else "0"
        cell.theme_type =  item.find("typeid").text if item.find("typeid") is not None else 0

        # Get download links
        cell.download_links = []
        cell.download_names = []

        i = 1
        while(True):
            if(item.find(f"downloadlink{i}") is None):
                break
            download_link = item.find(f"downloadlink{i}")
            download_name = item.find(f"downloadname{i}")
            if(download_link.text):
                cell.download_links.append(download_link.text)
                cell.download_names.append(download_name.text)
            i += 1

        # Get image links
        cell.image_urls = []
        z = 1
        while(True):
            if(item.find(f"previewpic{z}") is None):
                break
            cell.image_urls.append(item.find(f"previewpic{z}").text)
            z += 1

        cell.build_cell()
        flowbox.insert(Adw.Clamp(child=cell, maximum_size=375), -1)

# def get_default_colors(widget):
#     style_context = widget.get_style_context()
#     color = Gdk.RGBA()

#     bg = style_context.lookup_color("view_bg_color")[1]
#     fg = style_context.lookup_color("window_fg_color")[1]
#     bg_color = f"rgba({bg.red * 255}, {bg.green * 255}, {bg.blue * 255}, {bg.alpha})"
#     fg_color = f"rgba({fg.red * 255}, {fg.green * 255}, {fg.blue * 255}, {fg.alpha})"
#     return (bg_color, fg_color)
