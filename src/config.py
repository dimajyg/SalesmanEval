import json
import os

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
    _config_data = json.load(f)

YANDEX_TOKEN = _config_data["YANDEX_TOKEN"]


SHOPS_FILE_PATH = os.path.join(os.path.dirname(__file__), "shops.json")

with open(SHOPS_FILE_PATH, "r", encoding="utf-8") as f:
    _shops_data = json.load(f)

SHOPS = _shops_data["shops"]

SHEETS_TOKEN = os.path.join(os.path.dirname(__file__), "sheets_token.json")