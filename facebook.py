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
{news['title_si']}

{news['summary_si']}

🌍 world news in sinhala
"""

    return caption



# ==========================================
# Upload Video To Facebook Page
# ==========================================

def upload_video(video_path, caption):

    if not PAGE_ID or not PAGE_TOKEN:

        print("Facebook settings missing")

        return False


    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/"
        f"{PAGE_ID}/videos"
    )


    try:

        with open(video_path, "rb") as video:

            files = {
                "source": video
            }


            data = {

                "description": caption,

                "access_token": PAGE_TOKEN

            }


            response = requests.post(

                url,

                files=files,

                data=data,

                timeout=600

            )


        print(response.text)


        if response.status_code == 200:

            return True


        return False


    except Exception as e:

        print("Facebook Error:", e)

        return False



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

        "title_si": "Test News",

        "summary_si": "Facebook upload test"

    }


    print(

        upload_news(

            "output/news.mp4",

            test_news

        )

    )
