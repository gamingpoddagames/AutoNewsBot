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
    # ==========================================
# Get News From RSS
# ==========================================

def collect_news():

    used = load_used(USED_FILE)

    news_list = []

    feeds = RSS_FEEDS.copy()

    random.shuffle(feeds)

    for feed_url in feeds:

        try:

            log(f"Checking : {feed_url}")

            feed = feedparser.parse(feed_url)

            source = feed.feed.get("title", "Unknown")

            for entry in feed.entries[:10]:

                title = clean_text(
                    entry.get("title", "")
                )

                summary = clean_text(
                    entry.get("summary", "")
                )

                link = entry.get("link", "")

                if not title or not link:
                    continue

                news_id = news_hash(link)

                if news_id in used:
                    continue

                image = get_feed_image(entry)

                news_list.append({

                    "id": news_id,

                    "title": title,

                    "summary": summary,

                    "link": link,

                    "image": image,

                    "source": source

                })

        except Exception as e:

            log(e)

    return news_list


# ==========================================
# Translate News
# ==========================================

def translate_news(news):

    title_si = translate(
        news["title"]
    )

    summary_si = translate(
        news["summary"]
    )

    if not title_si:
        return None

    if not summary_si:
        summary_si = title_si

    news["title_si"] = shorten(title_si,180)

    news["summary_si"] = shorten(summary_si,650)

    return news
    # ==========================================
# Select Best News
# ==========================================

def get_best_news():

    news_list = collect_news()

    if not news_list:

        log("No news found.")

        return None

    random.shuffle(news_list)

    # Prefer articles with images
    with_image = [
        n for n in news_list
        if n["image"]
    ]

    if with_image:
        news = random.choice(with_image)
    else:
        news = random.choice(news_list)

    # Try getting better image from article page
    article_image = get_article_image(
        news["link"]
    )

    if article_image:
        news["image"] = article_image

    # Translate
    news = translate_news(news)

    if not news:

        log("Translation failed.")

        return None

    # Save used news
    used = load_used(USED_FILE)

    used.append(news["id"])

    save_used(USED_FILE, used)

    log("News Selected")

    log(news["title"])

    return news


# ==========================================
# Create Voice Script
# ==========================================

def make_script(news):

    title = shorten(
        news["title_si"],
        180
    )

    summary = shorten(
        news["summary_si"],
        700
    )

    script = (
        f"{title}. "
        f"{summary}. "
        "තවත් ලෝක පුවත් සඳහා අපගේ චැනලය Follow කරන්න."
    )

    return script


# ==========================================
# Test
# ==========================================

if __name__ == "__main__":

    news = get_best_news()

    if news:

        print("=" * 60)

        print(news["title"])

        print()

        print(news["title_si"])

        print()

        print(news["summary_si"])

        print()

        print(news["image"])

        print()

        print(make_script(news))
