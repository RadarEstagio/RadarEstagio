from google import genai

from radar.avaliacao.agy import JuizAgy
from radar.avaliacao.gemini import JuizGemini
from radar.domain.ports import JuizDeRecomendacoes
from radar.settings import Settings


def criar_juiz(settings: Settings) -> JuizDeRecomendacoes:
    if settings.avaliador == "agy":
        return JuizAgy(settings)
    return JuizGemini(settings, genai.Client(api_key=settings.gemini_api_key))
