import random
import feedparser
import requests
from bs4 import BeautifulSoup

from config import RSS_FEEDS, USED_FILE
from utils import (
    clean_text,
    translate,
    shorten,
    load_used,
    save_used,
    news_hash,
    log,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def upgrade_image_url(url):
    if not url:
        return None

    replacements = [
        "240",
        "320",
        "480",
        "624",
        "800"
    ]

    for size in replacements:
        url = url.replace(f"/{size}/", "/1024/")

    return url


def get_feed_image(entry):

    if "media_content" in entry:
        for media in entry.media_content:
            if media.get("url"):
                return upgrade_image_url(media["url"])

    if "media_thumbnail" in entry:
        for media in entry.media_thumbnail:
            if media.get("url"):
                return upgrade_image_url(media["url"])

    if "links" in entry:
        for link in entry.links:

            if "image" in link.get("type",""):
                return upgrade_image_url(link["href"])

    return None


def get_article_image(article_url):

    try:

        r = requests.get(
            article_url,
            headers=HEADERS,
            timeout=15
        )

        soup = BeautifulSoup(r.text,"html.parser")

        tags = [

            ("meta",{"property":"og:image"}),

            ("meta",{"name":"twitter:image"}),

            ("meta",{"property":"twitter:image"}),

        ]

        for tag,attr in tags:

            item = soup.find(tag,attr)

            if item and item.get("content"):
                return upgrade_image_url(item["content"])

    except Exception as e:

        log(e)

    return None
