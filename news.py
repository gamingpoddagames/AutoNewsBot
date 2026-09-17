```python
import random
import time

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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

# ==========================================================
# Translation Settings
# ==========================================================

TRANSLATION_DELAY = 2.0
TRANSLATION_RETRIES = 3

# ==========================================================
# Image URL
# ==========================================================

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
        url = url.replace(
            f"/{size}/",
            "/1024/"
        )

    return url


# ==========================================================
# Get Image From RSS Entry
# ==========================================================

def get_feed_image(entry):

    try:

        if "media_content" in entry:

            for media in entry.media_content:

                if media.get("url"):
                    return upgrade_image_url(
                        media["url"]
                    )

        if "media_thumbnail" in entry:

            for media in entry.media_thumbnail:

                if media.get("url"):
                    return upgrade_image_url(
                        media["url"]
                    )

        if "links" in entry:

            for link in entry.links:

                if "image" in link.get("type", ""):

                    return upgrade_image_url(
                        link["href"]
                    )

    except Exception as e:

        log(
            f"Feed image error: {e}"
        )

    return None


# ==========================================================
# Get Image From Article
# ==========================================================

def get_article_image(article_url):

    try:

        r = requests.get(
            article_url,
            headers=HEADERS,
            timeout=15
        )

        if r.status_code != 200:

            return None

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        tags = [

            (
                "meta",
                {"property": "og:image"}
            ),

            (
                "meta",
                {"name": "twitter:image"}
            ),

            (
                "meta",
                {"property": "twitter:image"}
            ),

        ]

        for tag, attr in tags:

            item = soup.find(
                tag,
                attr
            )

            if item and item.get("content"):

                return upgrade_image_url(
                    item["content"]
                )

    except Exception as e:

        log(
            f"Article image error: {e}"
        )

    return None


# ==========================================================
# Collect News
# ==========================================================

def collect_news():

    used = load_used(
        USED_FILE
    )

    news_list = []

    feeds = RSS_FEEDS.copy()

    random.shuffle(
        feeds
    )

    for feed_url in feeds:

        try:

            log(
                f"Checking : {feed_url}"
            )

            feed = feedparser.parse(
                feed_url
            )

            if not feed.entries:

                log(
                    "No entries found."
                )

                continue

            source = feed.feed.get(
                "title",
                "Unknown"
            )

            for entry in feed.entries[:10]:

                title = clean_text(
                    entry.get(
                        "title",
                        ""
                    )
                )

                summary = clean_text(
                    entry.get(
                        "summary",
                        ""
                    )
                )

                link = entry.get(
                    "link",
                    ""
                )

                if not title or not link:

                    continue

                news_id = news_hash(
                    link
                )

                if news_id in used:

                    continue

                image = get_feed_image(
                    entry
                )

                news_list.append({

                    "id": news_id,

                    "title": title,

                    "summary": summary,

                    "link": link,

                    "image": image,

                    "source": source

                })

        except Exception as e:

            log(
                f"Feed error: {e}"
            )

    return news_list


# ==========================================================
# Safe Translation
# ==========================================================

def safe_translate(text, label="text"):

    if not text:

        return ""

    text = clean_text(
        text
    )

    if not text:

        return ""

    for attempt in range(
        1,
        TRANSLATION_RETRIES + 1
    ):

        try:

            log(
                f"Translating {label} "
                f"(attempt {attempt}/{TRANSLATION_RETRIES})"
            )

            result = translate(
                text
            )

            if result:

                # Small delay after successful request
                time.sleep(
                    TRANSLATION_DELAY
                )

                return result

            log(
                f"Translation returned empty result for {label}"
            )

        except Exception as e:

            log(
                f"Translation error ({label}): {e}"
            )

        if attempt < TRANSLATION_RETRIES:

            wait_time = (
                TRANSLATION_DELAY
                * attempt
                * 2
            )

            log(
                f"Waiting {wait_time:.1f} seconds before retry..."
            )

            time.sleep(
                wait_time
            )

    return ""


# ==========================================================
# Translate News
# ==========================================================

def translate_news(news):

    # ------------------------------------------------------
    # Translate title
    # ------------------------------------------------------

    title_si = safe_translate(
        news.get("title", ""),
        "title"
    )

    if not title_si:

        log(
            "Title translation failed."
        )

        return None

    # ------------------------------------------------------
    # Translate summary
    # ------------------------------------------------------

    summary = news.get(
        "summary",
        ""
    )

    summary_si = ""

    if summary:

        summary_si = safe_translate(
            summary,
            "summary"
        )

    # ------------------------------------------------------
    # If summary fails, use title
    # ------------------------------------------------------

    if not summary_si:

        log(
            "Summary translation failed."
        )

        log(
            "Using translated title as summary."
        )

        summary_si = title_si

    news["title_si"] = shorten(
        title_si,
        180
    )

    news["summary_si"] = shorten(
        summary_si,
        650
    )

    return news


# ==========================================================
# Select Best News
# ==========================================================

def get_best_news():

    news_list = collect_news()

    if not news_list:

        log(
            "No unused news articles found."
        )

        return None

    log(
        f"Found {len(news_list)} unused articles."
    )

    # Randomize articles
    random.shuffle(
        news_list
    )

    # Prefer articles that already contain images
    with_image = [
        n
        for n in news_list
        if n.get("image")
    ]

    without_image = [
        n
        for n in news_list
        if not n.get("image")
    ]

    # Try image articles first
    candidates = (
        with_image
        + without_image
    )

    # Limit attempts so the bot does not translate
    # hundreds of articles in one run.
    max_attempts = min(
        len(candidates),
        5
    )

    for index in range(
        max_attempts
    ):

        news = candidates[index]

        log(
            f"Trying article "
            f"{index + 1}/{max_attempts}"
        )

        log(
            f"Title: {news['title']}"
        )

        # --------------------------------------------------
        # Try better image from article page
        # --------------------------------------------------

        if not news.get("image"):

            article_image = get_article_image(
                news["link"]
            )

            if article_image:

                news["image"] = article_image

        else:

            # Sometimes the RSS image is bad.
            # Try the article image as an upgrade.
            article_image = get_article_image(
                news["link"]
            )

            if article_image:

                news["image"] = article_image

        # --------------------------------------------------
        # Translate
        # --------------------------------------------------

        translated = translate_news(
            news
        )

        if not translated:

            log(
                "Translation failed."
            )

            log(
                "Trying another article..."
            )

            # Extra delay before next article
            time.sleep(
                TRANSLATION_DELAY
            )

            continue

        # --------------------------------------------------
        # Translation succeeded
        # --------------------------------------------------

        news = translated

        # --------------------------------------------------
        # Save as used ONLY after success
        # --------------------------------------------------

        used = load_used(
            USED_FILE
        )

        if news["id"] not in used:

            used.append(
                news["id"]
            )

            save_used(
                USED_FILE,
                used
            )

        log(
            "News Selected"
        )

        log(
            news["title"]
        )

        return news

    # ------------------------------------------------------
    # Nothing worked
    # ------------------------------------------------------

    log(
        "All candidate articles failed translation."
    )

    return None


# ==========================================================
# Create Voice Script
# ==========================================================

def make_script(news):

    title = shorten(
        news.get(
            "title_si",
            ""
        ),
        180
    )

    summary = shorten(
        news.get(
            "summary_si",
            ""
        ),
        700
    )

    if not title:

        return None

    if not summary:

        summary = title

    script = (
        f"{title}. "
        f"{summary}. "
        "තවත් ලෝක පුවත් සඳහා අපගේ චැනලය Follow කරන්න."
    )

    return script


# ==========================================================
# Test
# ==========================================================

if __name__ == "__main__":

    news = get_best_news()

    if news:

        print("=" * 60)

        print(
            news["title"]
        )

        print()

        print(
            news["title_si"]
        )

        print()

        print(
            news["summary_si"]
        )

        print()

        print(
            news["image"]
        )

        print()

        print(
            make_script(news)
        )

    else:

        print(
            "No usable news article found."
        )
```
