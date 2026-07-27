import os
from gtts import gTTS
from utils import clean_text

VOICE_LANG = "si"


def create_voice(script, output_file):
    script = clean_text(script)

    if not script:
        return False

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        tts = gTTS(
            text=script,
            lang=VOICE_LANG,
            slow=False
        )

        tts.save(output_file)
        return True

    except Exception as e:
        print("Voice Error:", e)
        return False


def test_voice():
    text = "ලෝකයේ නවතම පුවත් සඳහා අප සමඟ රැඳී සිටින්න."

    ok = create_voice(text, "output/test.mp3")

    if ok:
        print("Voice Created")
    else:
        print("Voice Failed")


if __name__ == "__main__":
    test_voice()
