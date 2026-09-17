import os
import re
import json
import time
import hashlib
import requests

from bs4 import BeautifulSoup


# ============================================================
# TRANSLATION CONFIGURATION
# ============================================================

# Set this in GitHub Actions Secrets/Variables if you use
# your own LibreTranslate-compatible server.
#
# Example:
# TRANSLATE_API_URL=https://your-server.example/translate
#
# The program also accepts the common LibreTranslate format.
TRANSLATE_API_URL = os.environ.get(
    "TRANSLATE_API_URL",
    ""
).strip()

TRANSLATE_API_KEY = os.environ.get(
    "TRANSLATE_API_KEY",
    ""
).strip()

TRANSLATE_SOURCE = "en"
TRANSLATE_TARGET = "si"

TRANSLATE_TIMEOUT = 30
TRANSLATE_RETRIES = 2

# Small delay so that if your translation endpoint has limits,
# we do not hammer it.
TRANSLATE_DELAY = 1.0

_last_translation_time = 0.0


# ============================================================
# FILES
# ============================================================

TRANSLATION_CACHE_FILE = os.path.join(
    "data",
    "translation_cache.json"
)


# ============================================================
# CLEAN TEXT
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
# SHORTEN TEXT
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

def translation_cache_key(text):

    raw = (
        TRANSLATE_SOURCE
        + "|"
        + TRANSLATE_TARGET
        + "|"
        + text
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


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


# ============================================================
# RATE CONTROL
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


# ============================================================
# LIBRETRANSLATE REQUEST
# ============================================================

def libretranslate_request(text):

    if not TRANSLATE_API_URL:

        print(
            "Translation API is not configured."
        )

        print(
            "Set TRANSLATE_API_URL "
            "in GitHub Actions."
        )

        return ""

    payload = {
        "q": text,
        "source": TRANSLATE_SOURCE,
        "target": TRANSLATE_TARGET,
        "format": "text",
    }

    if TRANSLATE_API_KEY:
        payload["api_key"] = TRANSLATE_API_KEY

    headers = {
        "User-Agent": (
            "AutoNewsBot/1.0"
        ),
        "Accept": "application/json",
        "Content-Type": (
            "application/json"
        ),
    }

    for attempt in range(
        TRANSLATE_RETRIES + 1
    ):

        try:

            wait_for_translation_slot()

            response = requests.post(
                TRANSLATE_API_URL,
                json=payload,
                headers=headers,
                timeout=TRANSLATE_TIMEOUT,
            )

            if response.status_code == 200:

                data = response.json()

                translated = data.get(
                    "translatedText",
                    ""
                )

                translated = clean_text(
                    translated
                )

                if has_sinhala(
                    translated
                ):
                    return translated

                print(
                    "Translation endpoint "
                    "returned invalid Sinhala text."
                )

                return ""

            print(
                "Translation API HTTP "
                f"{response.status_code}: "
                f"{response.text[:300]}"
            )

        except Exception as e:

            print(
                "Translation request error "
                f"(attempt {attempt + 1}):",
                e
            )

        if attempt < TRANSLATE_RETRIES:

            time.sleep(
                3 * (attempt + 1)
            )

    return ""


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

    key = translation_cache_key(
        text
    )

    cached = cache.get(key)

    if cached and has_sinhala(
        cached
    ):

        print(
            "Translation cache hit."
        )

        return cached

    result = libretranslate_request(
        text
    )

    if result:

        cache[key] = result

        save_translation_cache(
            cache
        )

        return result

    return ""


# ============================================================
# TRANSLATE BATCH
# ============================================================

def translate_batch(texts):

    if not texts:
        return []

    results = []

    for text in texts:

        results.append(
            translate(text)
        )

    return results


# ============================================================
# DOWNLOAD
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
                "Download error "
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
# NEWS HASH
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
