import os

from news import (
    get_best_news,
    make_script
)

from image import (
    download_image,
    create_fallback
)

from voice import (
    create_voice
)

from video import (
    create_video
)

from telegram import (
    upload_news as telegram_upload
)

from facebook import (
    upload_news as facebook_upload
)

from config import (
    OUTPUT_DIR,
    ASSET_DIR
)
# ==========================================
# Create Folders
# ==========================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

os.makedirs(
    ASSET_DIR,
    exist_ok=True
)

IMAGE_FILE = os.path.join(
    ASSET_DIR,
    "news.jpg"
)

VOICE_FILE = os.path.join(
    ASSET_DIR,
    "voice.mp3"
)

VIDEO_FILE = os.path.join(
    OUTPUT_DIR,
    "news.mp4"
)
# ==========================================
# Get News
# ==========================================

print("Getting News...")

news = get_best_news()

if news is None:

    print("No News Found")

    quit()

print(news["title_si"])

print("Downloading Image...")

ok = download_image(

    news["image"],

    IMAGE_FILE

)

if not ok:

    print("Using fallback image")

    create_fallback(

        IMAGE_FILE

    )
  # ==========================================
# Create Voice
# ==========================================

print("Creating Voice...")

script = make_script(news)

voice = create_voice(

    script,

    VOICE_FILE

)

if not voice:

    print("Voice Failed")

    quit()

print("Creating Video...")

create_video(

    IMAGE_FILE,

    VOICE_FILE,

    news["title_si"],

    news["summary_si"],

    VIDEO_FILE
)
# ==========================================
# Telegram Upload
# ==========================================

print("Uploading Telegram...")

telegram_ok = telegram_upload(

    VIDEO_FILE,

    news

)

if telegram_ok:

    print("Telegram Success")

else:

    print("Telegram Failed")


# ==========================================
# Facebook Upload
# ==========================================

print("Uploading Facebook...")

facebook_ok = facebook_upload(

    VIDEO_FILE,

    news

)

if facebook_ok:

    print("Facebook Success")

else:

    print("Facebook Failed")


print("Finished")
