import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
AUTH_FILE = os.path.join(BASE_DIR, "auth.json")
TARGET_URL = "https://www.tajiduo.com/bbs/index.html#/home?id=2"

# Delay configurations (seconds)
DELAY_MIN = 1.5
DELAY_MAX = 4.5
