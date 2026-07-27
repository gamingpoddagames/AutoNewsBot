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
