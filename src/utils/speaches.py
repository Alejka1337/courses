import os
import boto3
from pydub import AudioSegment



def initial_boto() -> boto3.client:
    polly = boto3.client('polly')
    return polly


def synthesize_female_speech(text: str, file_path: str, polly: boto3.client) -> None:
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        LanguageCode='en-GB',
        VoiceId='Joanna',
        Engine='neural'
    )

    with open(file_path, "wb") as file:
        file.write(response['AudioStream'].read())


def synthesize_male_speech(text: str, file_path: str, polly: boto3.client) -> None:
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        LanguageCode='en-GB',
        VoiceId='Gregory',
        Engine='neural'
    )

    with open(file_path, "wb") as file:
        file.write(response['AudioStream'].read())

def split_text(text: str, max_length: int = 1500) -> list[str]:
    """
    Разделяет текст на части, каждая из которых не превышает max_length символов.
    Разделение происходит по завершенным предложениям (точкам).
    """
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def combine_audio(audio_files: list[str], output_path: str) -> None:
    """
    Объединяет несколько аудиофайлов в один и сохраняет результат.
    """
    combined_audio = AudioSegment.empty()

    for file in audio_files:
        audio = AudioSegment.from_file(file, format="mp3")
        combined_audio += audio

    combined_audio.export(output_path, format="mp3")


def generate_female_audio_from_text(full_text: str, output_path: str, polly: boto3.client) -> None:
    """
    Генерирует аудио для полного текста, разбивая его на части, и сохраняет результат.
    """
    # 1. Разбиваем текст на части
    text_chunks = split_text(full_text)

    # 2. Генерируем аудио для каждой части
    audio_files = []
    for i, chunk in enumerate(text_chunks):
        temp_file = f"temp_part_{i}.mp3"
        synthesize_female_speech(chunk, temp_file, polly)
        audio_files.append(temp_file)

    # 3. Объединяем аудио в один файл
    combine_audio(audio_files, output_path)

    # 4. Удаляем временные файлы
    for file in audio_files:
        os.remove(file)



def generate_male_audio_from_text(full_text: str, output_path: str, polly: boto3.client) -> None:
    """
    Генерирует аудио для полного текста, разбивая его на части, и сохраняет результат.
    """
    # 1. Разбиваем текст на части
    text_chunks = split_text(full_text)

    # 2. Генерируем аудио для каждой части
    audio_files = []
    for i, chunk in enumerate(text_chunks):
        temp_file = f"temp_part_{i}.mp3"
        synthesize_male_speech(chunk, temp_file, polly)
        audio_files.append(temp_file)

    # 3. Объединяем аудио в один файл
    combine_audio(audio_files, output_path)

    # 4. Удаляем временные файлы
    for file in audio_files:
        os.remove(file)
