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

from tiktok import (
    upload_news as tiktok_upload
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


# ==========================================
# File Paths
# ==========================================

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

print("=" * 50)
print("STARTING NEWS BOT")
print("=" * 50)

print("\nGetting News...")

news = get_best_news()

if news is None:
    print("No News Found")
    quit()

print("\nNews Found:")
print(news.get("title_si", "No Sinhala title"))


# ==========================================
# Download Image
# ==========================================

print("\nDownloading Image...")

image_url = news.get("image")

if image_url:

    ok = download_image(
        image_url,
        IMAGE_FILE
    )

else:

    ok = False


# ==========================================
# Fallback Image
# ==========================================

if not ok:

    print("Image download failed.")
    print("Using fallback image...")

    create_fallback(
        IMAGE_FILE
    )


# ==========================================
# Create Sinhala Voice
# ==========================================

print("\nCreating Voice...")

script = make_script(
    news
)

if not script:

    print("Script creation failed.")
    quit()


voice_ok = create_voice(
    script,
    VOICE_FILE
)

if not voice_ok:

    print("Voice Failed")
    quit()

print("Voice Created Successfully")


# ==========================================
# Create Video
# ==========================================

print("\nCreating Video...")

video_ok = create_video(
    IMAGE_FILE,
    VOICE_FILE,
    news.get("title_si", ""),
    news.get("summary_si", ""),
    VIDEO_FILE
)

if not video_ok:

    # Some existing video.py versions don't return True/False.
    # Therefore check whether the MP4 was actually created.
    if not os.path.exists(VIDEO_FILE):

        print("Video Creation Failed")
        quit()

else:

    print("Video Created Successfully")


# ==========================================
# Verify Video
# ==========================================

if not os.path.exists(VIDEO_FILE):

    print("ERROR: Video file does not exist.")

    quit()


video_size = os.path.getsize(
    VIDEO_FILE
)

if video_size <= 0:

    print("ERROR: Video file is empty.")

    quit()


print(
    f"Video Ready: {VIDEO_FILE}"
)

print(
    f"Video Size: {video_size / (1024 * 1024):.2f} MB"
)


# ==========================================
# Telegram Upload
# ==========================================

print("\n" + "=" * 50)
print("Uploading Telegram...")
print("=" * 50)

try:

    telegram_ok = telegram_upload(
        VIDEO_FILE,
        news
    )

    if telegram_ok:

        print("Telegram Success")

    else:

        print("Telegram Failed")

except Exception as e:

    print(
        f"Telegram Error: {e}"
    )


# ==========================================
# Facebook Upload
# ==========================================

print("\n" + "=" * 50)
print("Uploading Facebook...")
print("=" * 50)

try:

    facebook_ok = facebook_upload(
        VIDEO_FILE,
        news
    )

    if facebook_ok:

        print("Facebook Success")

    else:

        print("Facebook Failed")

except Exception as e:

    print(
        f"Facebook Error: {e}"
    )


# ==========================================
# TikTok Upload
# ==========================================

print("\n" + "=" * 50)
print("Uploading TikTok...")
print("=" * 50)

try:

    tiktok_ok = tiktok_upload(
        VIDEO_FILE,
        news
    )

    if tiktok_ok:

        print("TikTok Success")

    else:

        print("TikTok Failed")

except Exception as e:

    print(
        f"TikTok Error: {e}"
    )


# ==========================================
# Finished
# ==========================================

print("\n" + "=" * 50)
print("NEWS BOT FINISHED")
print("=" * 50)
