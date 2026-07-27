import os

# ==============================
# PROJECT SETTINGS
# ==============================

APP_NAME = "AutoNewsBot"

OUTPUT_DIR = "output"
ASSET_DIR = "assets"
USED_FILE = "used.json"

# Video
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Languages
TRANSLATE_TO = "si"
VOICE_LANGUAGE = "si"

# News
MAX_TITLE = 180
MAX_SUMMARY = 650

# Telegram
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

# Facebook
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "")

GRAPH_VERSION = "v22.0"

# RSS Feeds
RSS_FEEDS = [
    "https://www.bbc.com/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.skynews.com/feeds/rss/world.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
    "https://feeds.npr.org/1004/rss.xml",
    "https://www.france24.com/en/rss",
    "https://www.cbc.ca/cmlink/rss-world",
    "https://www.thehindu.com/news/international/feeder/default.rss",
]
