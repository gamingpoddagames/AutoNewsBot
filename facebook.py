import os
import requests

GRAPH_VERSION = "v22.0"

PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
# ==========================================
# Create Caption
# ==========================================

def make_caption(news):

    caption = f"""

{news["title_si"]}

{news["summary_si"]}

🌍 World News in Sinhala

{news["link"]}

"""

    return caption
  # ==========================================
# Upload Video
# ==========================================

def upload_video(video_path, caption):

    if not PAGE_ID or not PAGE_TOKEN:

        print("Facebook settings missing")

        return False

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PAGE_ID}/videos"

    data = {

        "description": caption,

        "access_token": PAGE_TOKEN

    }

    try:

        with open(video_path,"rb") as video:

            files = {

                "source": video

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
# Upload News
# ==========================================

def upload_news(video_path, news):

    caption = make_caption(news)

    return upload_video(

        video_path,

        caption

    )
  if __name__ == "__main__":

    news = {

        "title_si":"Test",

        "summary_si":"Facebook Upload Test",

        "link":"https://google.com"

    }

    upload_news(

        "output/video.mp4",

        news

    )

        return False
