```python
import os
import re
import json
import time
import hashlib

import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator


# ==========================================================
# Translation Settings
# ==========================================================

# Minimum time between Google Translate requests.
# This helps avoid hitting the request-rate limit.
TRANSLATE_DELAY = 2.5

# Number of attempts for temporary translation failures.
TRANSLATE_RETRIES = 4

# Cache file so identical text is not translated again.
TRANSLATION_CACHE_FILE = "translation_cache.json"


# ==========================================================
# Global Translation State
# ==========================================================

_last_translate_time = 0.0

_translator = GoogleTranslator(
    source="auto",
    target="si"
)


# ==========================================================
# Clean HTML/Text
# ==========================================================

def clean_text(text):

    if not text:
        return ""

    try:

        text = BeautifulSoup(
            str(text),
            "html.parser"
        ).get_text(" ")

    except Exception:

        text = str(text)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================================
# Limit Text
# ==========================================================

def shorten(text, limit):

    text = clean_text(
        text
    )

    if len(text) <= limit:

        return text

    shortened = text[:limit]

    # Avoid cutting a word in half.
    if " " in shortened:

        shortened = shortened.rsplit(
            " ",
            1
        )[0]

    return shortened + "..."


# ==========================================================
# Sinhala Check
# ==========================================================

def has_sinhala(text):

    if not text:

        return False

    return bool(
        re.search(
            r"[\u0D80-\u0DFF]",
            text
        )
    )


# ==========================================================
# Translation Cache
# ==========================================================

def load_translation_cache():

    if not os.path.exists(
        TRANSLATION_CACHE_FILE
    ):

        return {}

    try:

        with open(
            TRANSLATION_CACHE_FILE,
            "r",
            encoding="utf8"
        ) as f:

            data = json.load(f)

            if isinstance(data, dict):

                return data

    except Exception as e:

        print(
            "Translation cache error:",
            e
        )

    return {}


def save_translation_cache(cache):

    try:

        # Keep the cache from becoming enormous.
        if len(cache) > 2000:

            items = list(
                cache.items()
            )[-2000:]

            cache = dict(
                items
            )

        with open(
            TRANSLATION_CACHE_FILE,
            "w",
            encoding="utf8"
        ) as f:

            json.dump(
                cache,
                f,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            "Translation cache save error:",
            e
        )


def translation_cache_key(text):

    return hashlib.sha256(
        text.encode(
            "utf-8"
        )
    ).hexdigest()


# ==========================================================
# Wait Before Translation
# ==========================================================

def wait_for_translation_slot():

    global _last_translate_time

    now = time.monotonic()

    elapsed = (
        now - _last_translate_time
    )

    if elapsed < TRANSLATE_DELAY:

        wait_time = (
            TRANSLATE_DELAY
            - elapsed
        )

        print(
            f"Translation cooldown: "
            f"waiting {wait_time:.1f}s"
        )

        time.sleep(
            wait_time
        )


# ==========================================================
# Translate
# ==========================================================

def translate(text):

    global _last_translate_time

    text = clean_text(
        text
    )

    # Keep requests reasonably small.
    text = shorten(
        text,
        1200
    )

    if not text:

        return ""

    # ------------------------------------------------------
    # Check cache first
    # ------------------------------------------------------

    cache = load_translation_cache()

    cache_key = translation_cache_key(
        text
    )

    if cache_key in cache:

        cached = cache[
            cache_key
        ]

        if cached and has_sinhala(cached):

            print(
                "Translation cache hit."
            )

            return cached

    # ------------------------------------------------------
    # Translation attempts
    # ------------------------------------------------------

    for attempt in range(
        1,
        TRANSLATE_RETRIES + 1
    ):

        try:

            # Respect request spacing.
            wait_for_translation_slot()

            print(
                f"Translating "
                f"(attempt {attempt}/{TRANSLATE_RETRIES})..."
            )

            result = _translator.translate(
                text
            )

            # Record request time.
            _last_translate_time = (
                time.monotonic()
            )

            result = clean_text(
                result
            )

            # --------------------------------------------------
            # Validate result
            # --------------------------------------------------

            if result and has_sinhala(result):

                cache[
                    cache_key
                ] = result

                save_translation_cache(
                    cache
                )

                return result

            print(
                "Translation returned "
                "no valid Sinhala text."
            )

        except Exception as e:

            _last_translate_time = (
                time.monotonic()
            )

            error_text = str(
                e
            )

            print(
                "Translate Error:",
                error_text
            )

            # --------------------------------------------------
            # Rate limit / temporary server error
            # --------------------------------------------------

            lower_error = (
                error_text.lower()
            )

            rate_limited = (
                "too many requests"
                in lower_error
                or "429"
                in lower_error
                or "rate limit"
                in lower_error
                or "server error"
                in lower_error
            )

            if rate_limited:

                # Increasing backoff:
                #
                # attempt 1 -> 5 sec
                # attempt 2 -> 10 sec
                # attempt 3 -> 20 sec
                #
                wait_time = (
                    5 * (2 ** (attempt - 1))
                )

                print(
                    "Google Translate "
                    "rate limit detected."
                )

                print(
                    f"Waiting {wait_time} seconds "
                    "before retry..."
                )

                time.sleep(
                    wait_time
                )

            else:

                # Other temporary errors.
                wait_time = (
                    2 * attempt
                )

                print(
                    f"Waiting {wait_time} seconds "
                    "before retry..."
                )

                time.sleep(
                    wait_time
                )

    # ------------------------------------------------------
    # All attempts failed
    # ------------------------------------------------------

    print(
        "Translation failed after "
        f"{TRANSLATE_RETRIES} attempts."
    )

    return ""


# ==========================================================
# Retry Download
# ==========================================================

def download(
    url,
    path,
    retry=3
):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        )
    }

    for i in range(
        retry
    ):

        try:

            r = requests.get(
                url,
                timeout=30,
                headers=headers
            )

            if r.status_code == 200:

                with open(
                    path,
                    "wb"
                ) as f:

                    f.write(
                        r.content
                    )

                return True

        except Exception as e:

            print(
                f"Download attempt "
                f"{i + 1} failed:",
                e
            )

        if i < retry - 1:

            time.sleep(
                2
            )

    return False


# ==========================================================
# Used News
# ==========================================================

def load_used(file):

    if os.path.exists(
        file
    ):

        try:

            with open(
                file,
                "r",
                encoding="utf8"
            ) as f:

                data = json.load(
                    f
                )

                if isinstance(
                    data,
                    list
                ):

                    return data

        except Exception:

            print(
                "used.json damaged. "
                "Resetting..."
            )

    return []


def save_used(
    file,
    data
):

    try:

        with open(
            file,
            "w",
            encoding="utf8"
        ) as f:

            json.dump(
                list(data)[-1000:],
                f,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            "Could not save used news:",
            e
        )


# ==========================================================
# News ID
# ==========================================================

def news_hash(link):

    return hashlib.md5(
        link.encode(
            "utf8"
        )
    ).hexdigest()


# ==========================================================
# Logger
# ==========================================================

def log(text):

    print(
        "[AutoNewsBot]",
        text
    )
```
