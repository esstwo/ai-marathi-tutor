"""Google Cloud Text-to-Speech wrapper for Marathi audio."""

import os
import json
from google.cloud import texttospeech
from google.oauth2 import service_account

_cache: dict[str, bytes] = {}


def _get_client() -> texttospeech.TextToSpeechClient:
    creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(info)
        return texttospeech.TextToSpeechClient(credentials=credentials)
    return texttospeech.TextToSpeechClient()


client = _get_client()


def synthesize_marathi(text: str) -> bytes:
    if text in _cache:
        return _cache[text]

    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code="mr-IN",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        ),
    )

    _cache[text] = response.audio_content
    return response.audio_content
