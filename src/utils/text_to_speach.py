import os
import subprocess
import tempfile
import wave

from src.config import SPEECHES_DIR


def convert_to_wav(mp3_path: str):
    wav_path = mp3_path.replace(".mp3", ".wav")
    subprocess.run(["ffmpeg", "-i", mp3_path, wav_path], check=True)

    with wave.open(wav_path, "rb") as wav_file:
        wav_file.readframes(wav_file.getnframes())
        wav_file.getnchannels()
        wav_file.getsampwidth()
        wav_file.getframerate()

    return wav_path


def text_to_speach(text: str, lecture_id: int):
    folder = os.path.join(SPEECHES_DIR, f"lecture{lecture_id}")
    os.makedirs(folder, exist_ok=True)

    voices = {
        "male1": "en",
        "male2": "en-sc",
        "male3": "en-us"
    }

    res = []

    for voice_name, lang in voices.items():
        mp3_path = os.path.join(folder, f"{voice_name}.mp3")

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(text.encode('utf-8'))
            temp_file_path = temp_file.name

        command = f"espeak -v {lang} -s 100 -a 200 -f {temp_file_path} --stdout > {mp3_path}"

        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при создании MP3 файла для {voice_name}: {e}")
            continue
        finally:
            os.remove(temp_file_path)

        if not os.path.exists(mp3_path):
            print(f"Файл MP3 не был создан: {mp3_path}")
            continue

        try:
            wav_path = convert_to_wav(mp3_path)
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при конвертации MP3 в WAV с использованием ffmpeg для {voice_name}: {e}")
            continue

        res.append(wav_path)

    return res


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


# from pyttsx3.engine import Engine
# from src.config import FEMALE_VOICE, MALE_VOICES, SPEECHES_DIR


# def text_to_speach(text: str, lecture_id: int):
#     engine = Engine(driverName="nsss")
#     engine.setProperty('rate', 150)
#     voices = engine.getProperty('voices')
#
#     res = {}
#     folder = SPEECHES_DIR + "/lecture" + str(lecture_id)
#     os.makedirs(folder, exist_ok=True)
#
#     for voice in voices:
#         if voice.id in MALE_VOICES:
#             engine.setProperty("voice", voice.id)
#             engine.save_to_file(text=text, filename=f"{folder}/{voice.name.lower()}.mp3")
#             res.update({f"path{voice.name}": f"{folder}/{voice.name.lower()}.mp3"})
#
#         elif voice.id in FEMALE_VOICE:
#             engine.setProperty("voice", voice.id)
#             engine.save_to_file(text=text, filename=f"{folder}/{voice.name.lower()}.mp3")
#             res.update({f"path{voice.name}": f"{folder}/{voice.name.lower()}.mp3"})
#
#     engine.runAndWait()
#
#     for k, v in res.items():
#         new_v = convert_to_wav(v)
#         res[k] = new_v
#
#     return res
#
#

# with wave.open(mp3_path, "wb") as mp3_file:
#     mp3_file.setnchannels(channels)
#     mp3_file.setsampwidth(sample_width)
#     mp3_file.setframerate(frame_rate)
#     mp3_file.writeframes(frames)
