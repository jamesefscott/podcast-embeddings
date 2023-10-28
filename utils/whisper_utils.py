import io
import logging
import requests

import librosa
from transformers import pipeline

logger = logging.getLogger("main-logger")


class Transcriber:
    def __init__(self, model_name):
        self.pipe = pipeline("automatic-speech-recognition", model=model_name)

    def load_mp3_from_url(self, url, sample_rate=16000):
        logger.info(f"Getting mp3 content from {url}")
        mp3_content = requests.get(url).content

        logger.info("Reading samples from mp3")
        mp3_io = io.BytesIO(mp3_content)
        audio_samples, _ = librosa.load(mp3_io, sr=sample_rate)

        logger.info(f"mp3 processing complete. {len(audio_samples)} samples total.")
        return audio_samples

    def transcribe_file_from_url(self, url):
        audio_samples = self.load_mp3_from_url(url)
        logger.info("Transcribing mp3.")
        transcribed_data = self.pipe(
            audio_samples,
            return_timestamps=True,
            chunk_length_s=30,
            # stride_length_s=(0.2, 0.2),
            # batch_size=5,
        )
        logger.info(
            f"Transcription complete. {len(transcribed_data['chunks'])} chunks."
        )
        return transcribed_data
