import os
import subprocess
import wave

from pyttsx3.engine import Engine


from src.config import FEMALE_VOICE, MALE_VOICES, SPEECHES_DIR


def text_to_speach(text: str, lecture_id: int):
    engine = Engine(driverName="nsss")
    engine.setProperty('rate', 150)
    voices = engine.getProperty('voices')

    res = {}
    folder = SPEECHES_DIR + "/lecture" + str(lecture_id)
    os.makedirs(folder, exist_ok=True)

    for voice in voices:
        if voice.id in MALE_VOICES:
            engine.setProperty("voice", voice.id)
            engine.save_to_file(text=text, filename=f"{folder}/{voice.name.lower()}.mp3")
            res.update({f"path{voice.name}": f"{folder}/{voice.name.lower()}.mp3"})

        elif voice.id in FEMALE_VOICE:
            engine.setProperty("voice", voice.id)
            engine.save_to_file(text=text, filename=f"{folder}/{voice.name.lower()}.mp3")
            res.update({f"path{voice.name}": f"{folder}/{voice.name.lower()}.mp3"})

    engine.runAndWait()

    for k, v in res.items():
        new_v = convert_to_wav(v)
        res[k] = new_v

    return res


def convert_to_wav(mp3_path: str):
    wav_path = mp3_path.replace(".mp3", ".wav")
    subprocess.run(["ffmpeg", "-i", mp3_path, wav_path])

    with wave.open(wav_path, "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()

        with wave.open(mp3_path, "wb") as mp3_file:
            mp3_file.setnchannels(channels)
            mp3_file.setsampwidth(sample_width)
            mp3_file.setframerate(frame_rate)
            mp3_file.writeframes(frames)

    return wav_path


def create_lecture_text(attrs):
    lecture_text = ""

    for attr in attrs:
        title = attr.title.strip()
        text = attr.text.strip() if attr.text else None

        if title and title[-1] not in [".", "?", "!"]:
            title += '.'

        if text and text[-1] not in [".", "?", "!"]:
            text += '.'

        lecture_text += f"{title}\n{text}\n"
    return lecture_text


