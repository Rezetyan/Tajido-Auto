import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime")
SCREENSHOT_DIR = os.path.join(RUNTIME_DIR, "screenshots")
LOG_FILE = os.path.join(RUNTIME_DIR, "tajido.log")

TARGET_URL = "https://www.tajiduo.com/bbs/index.html#/home?id=2"
CREATE_POST_URL = "https://www.tajiduo.com/bbs/index.html#/create"
CONTENT_CENTER_URL = "https://www.tajiduo.com/bbs/index.html#/content?index=0"
REPLY_URL = os.getenv("TAJIDO_REPLY_URL", CONTENT_CENTER_URL)
POST_URL_TEMPLATE = "https://www.tajiduo.com/bbs/index.html#/post?postId={post_id}"

DRY_RUN = os.getenv("TAJIDO_DRY_RUN", "0").lower() in {"1", "true", "yes", "on"}

# Delay configurations (seconds)
DELAY_MIN = 1.5
DELAY_MAX = 4.5
