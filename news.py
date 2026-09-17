import random
import feedparser
import requests

from bs4 import BeautifulSoup

from config import RSS_FEEDS, USED_FILE

from utils import (
    clean_text,
    translate_batch,
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
        "Chrome/128.0 Safari/537.36"
    )
}


MAX_CANDIDATES = 5


# ============================================================
# IMAGE URL
# ============================================================

def upgrade_image_url(url):

    if not url:
        return None

    replacements = [
        "240",
        "320",
        "480",
        "624",
        "800",
    ]

    for size in replacements:

        url = url.replace(
            f"/{size}/",
            "/1024/"
        )

    return url


# ============================================================
# RSS IMAGE
# ============================================================

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

                link_type = link.get(
                    "type",
                    ""
                )

                if "image" in link_type:

                    return upgrade_image_url(
                        link.get("href")
                    )

    except Exception as e:

        log(
            f"Feed image error: {e}"
        )

    return None


# ============================================================
# ARTICLE IMAGE
# ============================================================

def get_article_image(article_url):

    if not article_url:
        return None

    try:

        response = requests.get(
            article_url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
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

            if (
                item
                and item.get("content")
            ):

                image = (
                    upgrade_image_url(
                        item.get("content")
                    )
                )

                if image:
                    return image

    except Exception as e:

        log(
            f"Article image error: {e}"
        )

    return None


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_news():

    used = load_used(
        USED_FILE
    )

    news_list = []

    feeds = list(
        RSS_FEEDS
    )

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

                    "source": source,

                })

        except Exception as e:

            log(
                f"Feed error: {e}"
            )

    return news_list


# ============================================================
# TRANSLATE NEWS
# ============================================================

def translate_news(news):

    title = shorten(
        news.get("title", ""),
        1200
    )

    summary = shorten(
        news.get("summary", ""),
        1200
    )

    # Translate both in one controlled function.
    translations = translate_batch(
        [
            title,
            summary
        ]
    )

    if not translations:
        return None

    title_si = translations[0]

    summary_si = translations[1]

    if not title_si:

        log(
            "Title translation failed."
        )

        return None

    if not summary_si:

        log(
            "Summary translation failed."
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


# ============================================================
# SELECT BEST NEWS
# ============================================================

def get_best_news():

    news_list = collect_news()

    if not news_list:

        log(
            "No news found."
        )

        return None

    random.shuffle(
        news_list
    )

    with_image = [
        news
        for news in news_list
        if news.get("image")
    ]

    if with_image:

        candidates = with_image[
            :MAX_CANDIDATES
        ]

    else:

        candidates = news_list[
            :MAX_CANDIDATES
        ]

    log(
        f"Found {len(news_list)} "
        "unused articles."
    )

    log(
        f"Trying up to {len(candidates)} "
        "candidate articles."
    )

    for news in candidates:

        try:

            if not news.get("image"):

                article_image = (
                    get_article_image(
                        news["link"]
                    )
                )

                if article_image:

                    news["image"] = (
                        article_image
                    )

            translated = (
                translate_news(news)
            )

            if not translated:

                log(
                    "Skipping article "
                    "because translation "
                    "failed."
                )

                continue

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

            return translated

        except Exception as e:

            log(
                "Article processing error: "
                f"{e}"
            )

    log(
        "All candidate articles "
        "failed."
    )

    return None


# ============================================================
# VIDEO SCRIPT
# ============================================================

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

    script = (
        f"{title}. "
        f"{summary}. "
        "තවත් ලෝක පුවත් සඳහා "
        "අපගේ චැනලය Follow කරන්න."
    )

    return script


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    news = get_best_news()

    if news:

        print(
            "=" * 60
        )

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
            "No News Found"
        )
