import boto3


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
