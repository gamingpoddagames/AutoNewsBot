import os
import re
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# -----------------------------
# Clean HTML/Text
# -----------------------------
def clean_text(text):
    if not text:
        return ""

    text = BeautifulSoup(text, "html.parser").get_text(" ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -----------------------------
# Limit text
# -----------------------------
def shorten(text, limit):
    text = clean_text(text)

    if len(text) <= limit:
        return text

    return text[:limit].rsplit(" ", 1)[0] + "..."


# -----------------------------
# Sinhala check
# -----------------------------
def has_sinhala(text):
    return bool(re.search(r"[\u0D80-\u0DFF]", text))


# -----------------------------
# Translate
# -----------------------------
def translate(text):

    text = shorten(text, 1200)

    if not text:
        return ""

    try:

        result = GoogleTranslator(
            source="auto",
            target="si"
        ).translate(text)

        result = clean_text(result)

        if has_sinhala(result):
            return result

        return ""

    except Exception as e:
        print("Translate Error:", e)
        return ""


# -----------------------------
# Retry download
# -----------------------------
def download(url, path, retry=3):

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    for i in range(retry):

        try:

            r = requests.get(
                url,
                timeout=30,
                headers=headers
            )

            if r.status_code == 200:

                with open(path, "wb") as f:
                    f.write(r.content)

                return True

        except Exception:
            pass

    return False


# -----------------------------
# Used News
# -----------------------------
def load_used(file):

    if os.path.exists(file):

        try:

            with open(file, "r", encoding="utf8") as f:

                data = json.load(f)

                if isinstance(data, list):
                    return data

        except Exception:

            print("used.json damaged. Resetting...")

    return []


def save_used(file, data):

    with open(file, "w", encoding="utf8") as f:

        json.dump(
            data[-1000:],
            f,
            indent=4,
            ensure_ascii=False
        )


# -----------------------------
# News ID
# -----------------------------
def news_hash(link):

    return hashlib.md5(
        link.encode("utf8")
    ).hexdigest()


# -----------------------------
# Logger
# -----------------------------
def log(text):

    print("[AutoNewsBot]", text)
