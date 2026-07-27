import os
import requests

# ==========================================
# Telegram Settings
# ==========================================

BOT_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")
# ==========================================
# Upload Video
# ==========================================

def upload_video(video_path, caption=""):

    if not BOT_TOKEN or not CHAT_ID:

        print("Telegram Token Missing")

        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"

    try:

        with open(video_path, "rb") as video:

            files = {

                "video": video

            }

            data = {

                "chat_id": CHAT_ID,

                "caption": caption,

                "supports_streaming": True,

                "parse_mode": "HTML"

            }

            r = requests.post(

                url,

                data=data,

                files=files,

                timeout=600

            )

        print(r.text)

        return r.status_code == 200

    except Exception as e:

        print(e)
      # ==========================================
# Build Caption
# ==========================================

def make_caption(news):

    caption = f"""

<b>{news['title_si']}</b>

{news['summary_si']}

🌍 World News in Sinhala

📢 Follow for more daily news.

"""

    return caption
  # ==========================================
# Upload News
# ==========================================

def upload_news(video_path, news):

    caption = make_caption(news)

    return upload_video(

        video_path,

        caption

    )
  # ==========================================
# Test
# ==========================================

if __name__ == "__main__":

    test_news = {

        "title_si":"පරීක්ෂණ පුවත",

        "summary_si":"මෙය Telegram Upload Test එකකි."

    }

    ok = upload_news(

        "output/video.mp4",

        test_news

    )

    print(ok)

        return False
