import os
import re
import json
import time
import hashlib
import requests

from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator


# ============================================================
# TRANSLATION SETTINGS
# ============================================================

TRANSLATE_DELAY = 2.5
TRANSLATE_RETRIES = 4

TRANSLATION_CACHE_FILE = os.path.join(
    "data",
    "translation_cache.json"
)

_last_translation_time = 0.0


# ============================================================
# CLEAN HTML / TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = BeautifulSoup(
        str(text),
        "html.parser"
    ).get_text(" ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# LIMIT TEXT
# ============================================================

def shorten(text, limit):

    text = clean_text(text)

    if len(text) <= limit:
        return text

    shortened = text[:limit].rsplit(
        " ",
        1
    )[0]

    return shortened + "..."


# ============================================================
# SINHALA CHECK
# ============================================================

def has_sinhala(text):

    if not text:
        return False

    return bool(
        re.search(
            r"[\u0D80-\u0DFF]",
            text
        )
    )


# ============================================================
# TRANSLATION CACHE
# ============================================================

def load_translation_cache():

    try:

        folder = os.path.dirname(
            TRANSLATION_CACHE_FILE
        )

        if folder:
            os.makedirs(
                folder,
                exist_ok=True
            )

        if not os.path.exists(
            TRANSLATION_CACHE_FILE
        ):
            return {}

        with open(
            TRANSLATION_CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as e:

        print(
            "Translation cache read error:",
            e
        )

    return {}


def save_translation_cache(cache):

    try:

        folder = os.path.dirname(
            TRANSLATION_CACHE_FILE
        )

        if folder:
            os.makedirs(
                folder,
                exist_ok=True
            )

        with open(
            TRANSLATION_CACHE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                cache,
                file,
                indent=2,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            "Translation cache save error:",
            e
        )


def translation_cache_key(text):

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ============================================================
# TRANSLATION RATE CONTROL
# ============================================================

def wait_for_translation_slot():

    global _last_translation_time

    now = time.time()

    elapsed = (
        now -
        _last_translation_time
    )

    if elapsed < TRANSLATE_DELAY:

        time.sleep(
            TRANSLATE_DELAY - elapsed
        )

    _last_translation_time = time.time()


def is_rate_limit_error(error):

    message = str(error).lower()

    keywords = [
        "too many requests",
        "429",
        "rate limit",
        "server error",
        "quota",
        "blocked",
    ]

    return any(
        keyword in message
        for keyword in keywords
    )


# ============================================================
# TRANSLATE ONE TEXT
# ============================================================

def translate(text):

    text = shorten(
        text,
        1200
    )

    if not text:
        return ""

    cache = load_translation_cache()

    key = translation_cache_key(text)

    cached = cache.get(key)

    if cached and has_sinhala(cached):
        return cached

    last_error = None

    for attempt in range(
        TRANSLATE_RETRIES
    ):

        try:

            wait_for_translation_slot()

            translator = GoogleTranslator(
                source="auto",
                target="si"
            )

            result = translator.translate(
                text
            )

            result = clean_text(result)

            if has_sinhala(result):

                cache[key] = result

                save_translation_cache(
                    cache
                )

                return result

            last_error = Exception(
                "Translation returned "
                "no Sinhala text."
            )

        except Exception as e:

            last_error = e

            print(
                "Translate Error "
                f"(attempt {attempt + 1}/"
                f"{TRANSLATE_RETRIES}):",
                e
            )

            if is_rate_limit_error(e):

                wait_seconds = (
                    8 * (attempt + 1)
                )

            else:

                wait_seconds = (
                    3 * (attempt + 1)
                )

            if (
                attempt
                < TRANSLATE_RETRIES - 1
            ):

                time.sleep(
                    wait_seconds
                )

    if last_error:

        print(
            "Translation failed "
            "after retries:",
            last_error
        )

    return ""


# ============================================================
# TRANSLATE BATCH
# ============================================================

def translate_batch(texts):

    if not texts:
        return []

    cleaned = [
        shorten(text, 1200)
        for text in texts
    ]

    cache = load_translation_cache()

    results = [
        ""
        for _ in cleaned
    ]

    pending = []
    pending_indexes = []

    for index, text in enumerate(
        cleaned
    ):

        if not text:
            continue

        key = translation_cache_key(
            text
        )

        cached = cache.get(key)

        if cached and has_sinhala(
            cached
        ):

            results[index] = cached

        else:

            pending.append(text)
            pending_indexes.append(index)

    if not pending:
        return results

    last_error = None

    for attempt in range(
        TRANSLATE_RETRIES
    ):

        try:

            wait_for_translation_slot()

            translator = GoogleTranslator(
                source="auto",
                target="si"
            )

            translated = (
                translator.translate_batch(
                    pending
                )
            )

            if not isinstance(
                translated,
                list
            ):

                translated = list(
                    translated
                )

            for (
                index,
                original,
                result
            ) in zip(
                pending_indexes,
                pending,
                translated
            ):

                result = clean_text(
                    result
                )

                if has_sinhala(result):

                    results[index] = result

                    cache[
                        translation_cache_key(
                            original
                        )
                    ] = result

            save_translation_cache(
                cache
            )

            return results

        except Exception as e:

            last_error = e

            print(
                "Batch Translate Error "
                f"(attempt {attempt + 1}/"
                f"{TRANSLATE_RETRIES}):",
                e
            )

            if is_rate_limit_error(e):

                wait_seconds = (
                    10 * (attempt + 1)
                )

            else:

                wait_seconds = (
                    4 * (attempt + 1)
                )

            if (
                attempt
                < TRANSLATE_RETRIES - 1
            ):

                time.sleep(
                    wait_seconds
                )

    print(
        "Batch translation failed "
        "after retries:",
        last_error
    )

    # Individual translation fallback.
    for index, text in zip(
        pending_indexes,
        pending
    ):

        if results[index]:
            continue

        results[index] = translate(
            text
        )

    return results


# ============================================================
# DOWNLOAD FILE
# ============================================================

def download(
    url,
    path,
    retry=3
):

    if not url:
        return False

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/128.0 Safari/537.36"
        )
    }

    for attempt in range(retry):

        try:

            response = requests.get(
                url,
                timeout=30,
                headers=headers
            )

            if (
                response.status_code == 200
                and response.content
            ):

                folder = os.path.dirname(
                    path
                )

                if folder:

                    os.makedirs(
                        folder,
                        exist_ok=True
                    )

                with open(
                    path,
                    "wb"
                ) as file:

                    file.write(
                        response.content
                    )

                return True

        except Exception as e:

            print(
                "Download Error "
                f"(attempt {attempt + 1}/"
                f"{retry}):",
                e
            )

        if attempt < retry - 1:

            time.sleep(
                2 * (attempt + 1)
            )

    return False


# ============================================================
# USED NEWS
# ============================================================

def load_used(file):

    try:

        if os.path.exists(file):

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            if isinstance(
                data,
                list
            ):

                return data

    except Exception as e:

        print(
            "used.json damaged. "
            "Resetting:",
            e
        )

    return []


def save_used(
    file,
    data
):

    folder = os.path.dirname(
        file
    )

    if folder:

        os.makedirs(
            folder,
            exist_ok=True
        )

    with open(
        file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            list(data)[-1000:],
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# NEWS ID
# ============================================================

def news_hash(link):

    return hashlib.md5(
        link.encode("utf-8")
    ).hexdigest()


# ============================================================
# LOGGER
# ============================================================

def log(text):

    print(
        "[AutoNewsBot]",
        text
    )
