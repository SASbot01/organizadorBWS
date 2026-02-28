import os
import tempfile
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Se carga una sola vez al importar (modelo "base" - rapido y bueno para español)
_model = None


def _get_model():
    global _model
    if _model is None:
        logger.info("Cargando modelo Whisper (base)... primera vez tarda un poco")
        _model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Modelo Whisper cargado")
    return _model


async def transcribir_audio(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    """Transcribe audio bytes a texto usando Whisper local."""
    suffix = os.path.splitext(filename)[1] or ".ogg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()

        model = _get_model()
        segments, info = model.transcribe(tmp.name, language="es")
        texto = " ".join(seg.text.strip() for seg in segments)

    logger.info(f"Transcripcion ({info.language}, {info.duration:.1f}s): {texto}")
    return texto
