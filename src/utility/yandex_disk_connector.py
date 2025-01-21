# yandex_disk_connector.py
import os
import json
import yadisk
from datetime import datetime
from src.config import YANDEX_TOKEN, SHOPS

def download_new_videos(
    yandex_folder: str = "Varvikas Video",
    local_folder: str = "data/incoming",
    last_check_time: datetime = None
):
    y = yadisk.YaDisk(token=YANDEX_TOKEN)
    os.makedirs(local_folder, exist_ok=True)

    items = y.listdir(yandex_folder)
    all_new_files = []

    for item in items:
        if item['type'] == 'dir':
            shop_name = item['name']
            shop_path = f"{yandex_folder}/{shop_name}"
            shop_local_folder = os.path.join(local_folder, shop_name)
            os.makedirs(shop_local_folder, exist_ok=True)

            shop_files = y.listdir(shop_path)
            for file_info in shop_files:
                if (file_info['type'] == 'file' and
                    file_info["name"].lower().endswith((".mp4", ".avi", ".mkv"))):

                    # file_info["modified"] is already a datetime object
                    file_mod_time = file_info["modified"]

                    if last_check_time is None or file_mod_time > last_check_time:
                        filename = file_info["name"]
                        local_path = os.path.join(shop_local_folder, filename)
                        print(f"Downloading {filename} from '{shop_path}' to '{local_path}'...")
                        y.download(f"{shop_path}/{filename}", local_path)
                        all_new_files.append(local_path)
    
    return all_new_files

def ensure_shops_on_ydisk(yandex_folder="Varvikas Video"):
    """
    Ensures each shop listed in shops_file has a corresponding folder under 'yandex_folder'.
    Creates missing folders automatically.
    
    :param yandex_folder: The main folder on Yandex.Disk (e.g. "Varvikas Video").
    :param shops_file: JSON file with structure: { "shops": ["ShopA", "ShopB", ...] }
    """
    y = yadisk.YaDisk(token=YANDEX_TOKEN)


    existing_items = y.listdir(yandex_folder)
    existing_folders = [item["name"] for item in existing_items if item["type"] == "dir"]


    for shop in SHOPS:
        if shop not in existing_folders:
            new_folder_path = f"{yandex_folder}/{shop}"
            print(f"Creating folder on Yandex Disk: {new_folder_path} ...")
            y.mkdir(new_folder_path)

    print("All shops ensured on Yandex Disk.")
