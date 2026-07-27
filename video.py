import numpy as np

from PIL import (
    Image,
    ImageDraw,
    ImageFilter
)

from moviepy import (
    VideoClip,
    AudioFileClip
)

from image import (
    cover_resize,
    create_background,
    get_font
)

from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT
)


HEADER_HEIGHT = 170
# ==========================================
# Rounded Rectangle
# ==========================================

def rounded(draw, xy, radius, fill):

    draw.rounded_rectangle(

        xy,

        radius=radius,

        fill=fill

    )


# ==========================================
# Draw Header
# ==========================================

def draw_header(draw):

    rounded(

        draw,

        (0,0,VIDEO_WIDTH,HEADER_HEIGHT),

        0,

        (8,18,45)

    )

    font = get_font(46,True)

    draw.text(

        (40,50),

        "WORLD NEWS IN SINHALA",

        font=font,

        fill="white"

    )
  # ==========================================
# Breaking Banner
# ==========================================

def draw_breaking(draw):

    rounded(

        draw,

        (40,200,1040,310),

        30,

        (210,20,30)

    )

    font = get_font(42,True)

    draw.text(

        (90,235),

        "BREAKING NEWS",

        font=font,

        fill="white"

    )

    live = get_font(32,True)

    draw.text(

        (920,238),

        "LIVE",

        font=live,

        fill="white"

    )
    # ==========================================
# Draw Main News Image
# ==========================================

def draw_news_image(canvas, image_path, progress):

    original = Image.open(image_path).convert("RGB")

    # Smooth zoom animation
    zoom = 1.0 + progress * 0.04

    crop_w = int(original.width / zoom)
    crop_h = int(original.height / zoom)

    left = (original.width - crop_w) // 2
    top = (original.height - crop_h) // 2

    original = original.crop((
        left,
        top,
        left + crop_w,
        top + crop_h
    ))

    photo = cover_resize(
        original,
        (980,700)
    )

    mask = Image.new("L",(980,700),0)

    mdraw = ImageDraw.Draw(mask)

    mdraw.rounded_rectangle(
        (0,0,980,700),
        radius=40,
        fill=255
    )

    canvas.paste(
        photo,
        (50,360),
        mask
    )

    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle(
        (50,360,1030,1060),
        radius=40,
        outline="white",
        width=4
    )

    return canvas
    # ==========================================
# Draw Text Panel
# ==========================================

def draw_panel(canvas):

    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle(

        (40,1110,1040,1860),

        radius=40,

        fill=(5,12,30)

    )

    return canvas
    # ==========================================
# Draw News Title
# ==========================================

def draw_title(canvas,title):

    draw = ImageDraw.Draw(canvas)

    font = get_font(50,True)

    draw.text(

        (80,1160),

        title,

        font=font,

        fill="white"

    )

    return canvas
    # ==========================================
# Wrap Text
# ==========================================

def wrap_text(draw, text, font, max_width):

    words = text.split()

    lines = []

    current = ""

    for word in words:

        test = current + " " + word if current else word

        width = draw.textlength(test, font=font)

        if width <= max_width:

            current = test

        else:

            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines
    # ==========================================
# Draw Summary
# ==========================================

def draw_summary(canvas, summary):

    draw = ImageDraw.Draw(canvas)

    font = get_font(32)

    lines = wrap_text(

        draw,

        summary,

        font,

        900

    )

    y = 1320

    for line in lines[:9]:

        draw.text(

            (80, y),

            line,

            font=font,

            fill=(235,235,235)

        )

        y += 46

    return canvas
    # ==========================================
# Footer
# ==========================================

def draw_footer(canvas):

    draw = ImageDraw.Draw(canvas)

    font = get_font(26)

    draw.text(

        (80,1830),

        "Follow for more world news",

        font=font,

        fill=(200,200,200)

    )

    return canvas
    # ==========================================
# Create Frame
# ==========================================

def create_frame(

    image_path,

    title,

    summary,

    progress

):

    bg = create_background(image_path)

    bg = draw_news_image(

        bg,

        image_path,

        progress

    )

    draw = ImageDraw.Draw(bg)

    draw_header(draw)

    draw_breaking(draw)

    bg = draw_panel(bg)

    bg = draw_title(bg,title)

    bg = draw_summary(bg,summary)

    bg = draw_footer(bg)

    return bg
    # ==========================================
# Render Video
# ==========================================

def create_video(

    image_path,

    audio_path,

    title,

    summary,

    output_path

):

    audio = AudioFileClip(audio_path)

    duration = audio.duration


    def make_frame(t):

        progress = min(
            1.0,
            t / duration
        )

        frame = create_frame(

            image_path,

            title,

            summary,

            progress

        )

        return np.array(frame)


    video = VideoClip(

        make_frame,

        duration=duration

    )

    video = video.with_audio(audio)

    video.write_videofile(

        output_path,

        fps=30,

        codec="libx264",

        audio_codec="aac",

        preset="medium",

        threads=2

    )

    audio.close()

    video.close()
    # ==========================================
# Test
# ==========================================

if __name__ == "__main__":

    create_video(

        "assets/news.jpg",

        "assets/voice.mp3",

        "ලෝකයේ නවතම පුවත",

        "මෙය පරීක්ෂණයක් සඳහා පමණි.",

        "output/video.mp4"

    )
