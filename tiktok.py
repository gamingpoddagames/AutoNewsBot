import os
import time
import requests


# ==========================================
# TikTok API
# ==========================================

API_BASE = "https://open.tiktokapis.com/v2"


# ==========================================
# Environment Variables
# ==========================================

TIKTOK_ACCESS_TOKEN = os.getenv(
    "TIKTOK_ACCESS_TOKEN"
)


# ==========================================
# Headers
# ==========================================

def get_headers():

    return {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


# ==========================================
# Check TikTok Configuration
# ==========================================

def check_config():

    if not TIKTOK_ACCESS_TOKEN:

        print(
            "ERROR: TIKTOK_ACCESS_TOKEN is not configured."
        )

        return False

    return True


# ==========================================
# Get Creator Information
# ==========================================

def get_creator_info():

    url = (
        f"{API_BASE}/post/publish/"
        "creator_info/query/"
    )

    try:

        response = requests.post(
            url,
            headers=get_headers(),
            timeout=30
        )

        print(
            "TikTok Creator Info:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "TikTok Creator Info Error:",
                response.text
            )

            return None

        data = response.json()

        if data.get("error", {}).get("code") not in (
            None,
            "ok"
        ):

            print(
                "TikTok API Error:",
                data
            )

            return None

        return data.get("data")

    except Exception as e:

        print(
            f"TikTok Creator Info Exception: {e}"
        )

        return None


# ==========================================
# Choose Privacy Level
# ==========================================

def choose_privacy_level(creator_info):

    options = creator_info.get(
        "privacy_level_options",
        []
    )

    if not options:

        print(
            "ERROR: TikTok did not return privacy options."
        )

        return None

    # Prefer public posting when TikTok allows it.
    if "PUBLIC_TO_EVERYONE" in options:

        return "PUBLIC_TO_EVERYONE"

    # Otherwise use the first option returned
    # by TikTok.
    return options[0]


# ==========================================
# Initialize TikTok Video Post
# ==========================================

def initialize_post(
    video_size,
    privacy_level
):

    # 10 MB chunks
    chunk_size = 10 * 1024 * 1024

    total_chunks = (
        video_size + chunk_size - 1
    ) // chunk_size

    url = (
        f"{API_BASE}/post/publish/"
        "video/init/"
    )

    payload = {

        "post_info": {

            "title": "Sinhala World News",

            "privacy_level": privacy_level,

            "disable_duet": False,

            "disable_comment": False,

            "disable_stitch": False,

            "video_cover_timestamp_ms": 1000

        },

        "source_info": {

            "source": "FILE_UPLOAD",

            "video_size": video_size,

            "chunk_size": chunk_size,

            "total_chunk_count": total_chunks

        }

    }

    try:

        response = requests.post(
            url,
            headers=get_headers(),
            json=payload,
            timeout=30
        )

        print(
            "TikTok Init:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "TikTok Init Error:",
                response.text
            )

            return None

        data = response.json()

        error = data.get(
            "error",
            {}
        )

        if error.get("code") not in (
            None,
            "ok"
        ):

            print(
                "TikTok API Error:",
                data
            )

            return None

        return data.get("data")

    except Exception as e:

        print(
            f"TikTok Init Exception: {e}"
        )

        return None


# ==========================================
# Upload Video
# ==========================================

def upload_video(
    video_file,
    upload_url
):

    file_size = os.path.getsize(
        video_file
    )

    chunk_size = 10 * 1024 * 1024

    print(
        f"TikTok video size: "
        f"{file_size / (1024 * 1024):.2f} MB"
    )

    try:

        with open(
            video_file,
            "rb"
        ) as video:

            start = 0

            while start < file_size:

                end = min(
                    start + chunk_size,
                    file_size
                ) - 1

                current_size = (
                    end - start + 1
                )

                video.seek(start)

                chunk = video.read(
                    current_size
                )

                headers = {

                    "Content-Type":
                        "video/mp4",

                    "Content-Length":
                        str(current_size),

                    "Content-Range":
                        f"bytes {start}-{end}/{file_size}"

                }

                print(
                    f"Uploading TikTok "
                    f"bytes {start}-{end}..."
                )

                response = requests.put(
                    upload_url,
                    headers=headers,
                    data=chunk,
                    timeout=120
                )

                if response.status_code not in (
                    200,
                    201,
                    206
                ):

                    print(
                        "TikTok Upload Error:",
                        response.status_code,
                        response.text
                    )

                    return False

                start = end + 1

        print(
            "TikTok video upload completed."
        )

        return True

    except Exception as e:

        print(
            f"TikTok Upload Exception: {e}"
        )

        return False


# ==========================================
# Check Publish Status
# ==========================================

def check_publish_status(
    publish_id
):

    url = (
        f"{API_BASE}/post/publish/"
        "status/fetch/"
    )

    payload = {
        "publish_id": publish_id
    }

    try:

        response = requests.post(
            url,
            headers=get_headers(),
            json=payload,
            timeout=30
        )

        if response.status_code != 200:

            print(
                "TikTok Status Error:",
                response.text
            )

            return None

        data = response.json()

        return data.get("data")

    except Exception as e:

        print(
            f"TikTok Status Exception: {e}"
        )

        return None


# ==========================================
# Wait For TikTok Processing
# ==========================================

def wait_for_publish(
    publish_id
):

    print(
        "Waiting for TikTok to process video..."
    )

    for attempt in range(6):

        time.sleep(10)

        status = check_publish_status(
            publish_id
        )

        if not status:

            continue

        print(
            "TikTok Status:",
            status
        )

        publish_status = status.get(
            "status"
        )

        if publish_status == "PUBLISH_COMPLETE":

            print(
                "TikTok Publish Complete"
            )

            return True

        if publish_status in (
            "FAILED",
            "ERROR"
        ):

            print(
                "TikTok Publish Failed:",
                status
            )

            return False

    print(
        "TikTok is still processing the video."
    )

    return True


# ==========================================
# Upload News
# ==========================================

def upload_news(
    video_file,
    news
):

    print(
        "Starting TikTok upload..."
    )

    # --------------------------------------
    # Configuration
    # --------------------------------------

    if not check_config():

        return False

    # --------------------------------------
    # Check Video
    # --------------------------------------

    if not os.path.exists(video_file):

        print(
            f"TikTok video not found: {video_file}"
        )

        return False

    video_size = os.path.getsize(
        video_file
    )

    if video_size <= 0:

        print(
            "TikTok video is empty."
        )

        return False

    # --------------------------------------
    # Creator Info
    # --------------------------------------

    creator_info = get_creator_info()

    if not creator_info:

        return False

    print(
        "TikTok Creator:",
        creator_info.get("display_name", "Unknown")
    )

    # --------------------------------------
    # Privacy
    # --------------------------------------

    privacy_level = choose_privacy_level(
        creator_info
    )

    if not privacy_level:

        return False

    print(
        "TikTok Privacy:",
        privacy_level
    )

    # --------------------------------------
    # Initialize
    # --------------------------------------

    post_data = initialize_post(
        video_size,
        privacy_level
    )

    if not post_data:

        return False

    publish_id = post_data.get(
        "publish_id"
    )

    upload_url = post_data.get(
        "upload_url"
    )

    if not publish_id:

        print(
            "ERROR: TikTok did not return publish_id."
        )

        return False

    if not upload_url:

        print(
            "ERROR: TikTok did not return upload_url."
        )

        return False

    print(
        "TikTok Publish ID:",
        publish_id
    )

    # --------------------------------------
    # Upload MP4
    # --------------------------------------

    uploaded = upload_video(
        video_file,
        upload_url
    )

    if not uploaded:

        return False

    # --------------------------------------
    # Wait For Processing
    # --------------------------------------

    result = wait_for_publish(
        publish_id
    )

    return result
