import os
import re
import json
import time
import hashlib
import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

MYMEMORY_URL = "https://api.mymemory.translated.net/get"

# Optional email.
# Leave empty if you do not want to provide one.
MYMEMORY_EMAIL = os.environ.get("MYMEMORY_EMAIL", "").strip()

# Local translation cache
TRANSLATION_CACHE_FILE = os.environ.get(
    "TRANSLATION_CACHE_FILE",
    "data/translation_cache.json"
)

# MyMemory allows max 500 bytes per request.
# Keep safely below that limit.
TRANSLATION_MAX_CHARS = 350

# Wait between translation requests.
# This prevents rapid-fire requests.
TRANSLATION_DELAY = 2.0

HEADERS = {
    "User-Agent": (
        "AutoNewsBot/1.0 "
        "(https://github.com/gamingpoddagames/AutoNewsBot)"
    )
}


# ============================================================
# LOGGING
# ============================================================

def log(text):
    print("[AutoNewsBot]", text)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = BeautifulSoup(str(text), "html.parser").get_text(" ")

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def shorten(text, limit):
    text = clean_text(text)

    if len(text) <= limit:
        return text

    shortened = text[:limit].rsplit(" ", 1)[0]

    return shortened + "..."


# ============================================================
# SINHALA CHECK
# ============================================================

def has_sinhala(text):
    if not text:
        return False

    return bool(re.search(r"[\u0D80-\u0DFF]", text))


# ============================================================
# TRANSLATION CACHE
# ============================================================

def load_translation_cache():
    if not os.path.exists(TRANSLATION_CACHE_FILE):
        return {}

    try:
        with open(
            TRANSLATION_CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception as e:
        log(f"Translation cache error: {e}")

    return {}


def save_translation_cache(cache):
    try:
        directory = os.path.dirname(TRANSLATION_CACHE_FILE)

        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(
            TRANSLATION_CACHE_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                cache,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:
        log(f"Could not save translation cache: {e}")


def translation_cache_key(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ============================================================
# MYMEMORY TRANSLATION
# ============================================================

def mymemory_translate(text):
    text = clean_text(text)

    if not text:
        return ""

    # Check cache first
    cache = load_translation_cache()

    cache_key = translation_cache_key(text)

    if cache_key in cache:
        cached = cache[cache_key]

        if has_sinhala(cached):
            log("Translation loaded from cache.")
            return cached

    # MyMemory has a 500-byte request limit.
    # We use a smaller limit for safety.
    text = shorten(text, TRANSLATION_MAX_CHARS)

    params = {
        "q": text,
        "langpair": "en|si",
        "mt": "1",
    }

    if MYMEMORY_EMAIL:
        params["de"] = MYMEMORY_EMAIL

    for attempt in range(1, 4):

        try:

            log(
                f"MyMemory translation "
                f"attempt {attempt}/3..."
            )

            response = requests.get(
                MYMEMORY_URL,
                params=params,
                headers=HEADERS,
                timeout=30
            )

            if response.status_code != 200:
                log(
                    f"MyMemory HTTP error: "
                    f"{response.status_code}"
                )

                time.sleep(3)
                continue

            data = response.json()

            response_data = data.get(
                "responseData",
                {}
            )

            translated = response_data.get(
                "translatedText",
                ""
            )

            translated = clean_text(translated)

            if not translated:
                log("MyMemory returned empty translation.")
                time.sleep(3)
                continue

            # Make sure the result is actually Sinhala.
            if not has_sinhala(translated):

                log(
                    "MyMemory returned text without "
                    "Sinhala characters."
                )

                time.sleep(3)
                continue

            # Save to cache
            cache[cache_key] = translated

            # Keep cache reasonably sized.
            if len(cache) > 2000:
                items = list(cache.items())[-1500:]
                cache = dict(items)

            save_translation_cache(cache)

            log("Translation successful.")

            return translated

        except requests.RequestException as e:

            log(
                f"MyMemory request error: {e}"
            )

            time.sleep(3)

        except Exception as e:

            log(
                f"MyMemory translation error: {e}"
            )

            time.sleep(3)

    return ""


# ============================================================
# PUBLIC TRANSLATION FUNCTION
# ============================================================

def translate(text):
    text = clean_text(text)

    if not text:
        return ""

    return mymemory_translate(text)


# ============================================================
# TRANSLATE MULTIPLE TEXTS
# ============================================================

def translate_batch(texts):

    results = []

    for index, text in enumerate(texts):

        text = clean_text(text)

        if not text:
            results.append("")
            continue

        result = translate(text)

        results.append(result)

        # Don't wait after the final request.
        if index < len(texts) - 1:
            time.sleep(TRANSLATION_DELAY)

    return results


# ============================================================
# DOWNLOAD
# ============================================================

def download(url, path, retry=3):

    if not url:
        return False

    for attempt in range(1, retry + 1):

        try:

            response = requests.get(
                url,
                timeout=30,
                headers=HEADERS
            )

            if response.status_code == 200:

                with open(path, "wb") as f:
                    f.write(response.content)

                return True

            log(
                f"Download HTTP error "
                f"{response.status_code}"
            )

        except Exception as e:

            log(
                f"Download error "
                f"{attempt}/{retry}: {e}"
            )

        time.sleep(2)

    return False


# ============================================================
# USED NEWS
# ============================================================

def load_used(file):

    if os.path.exists(file):

        try:

            with open(
                file,
                "r",
                encoding="utf8"
            ) as f:

                data = json.load(f)

                if isinstance(data, list):
                    return data

        except Exception:

            print(
                "used.json damaged. "
                "Resetting..."
            )

    return []


def save_used(file, data):

    directory = os.path.dirname(file)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )

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


# ============================================================
# NEWS HASH
# ============================================================

def news_hash(link):

    return hashlib.md5(
        link.encode("utf8")
    ).hexdigest()
