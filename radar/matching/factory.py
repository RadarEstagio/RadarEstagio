from google import genai

from radar.domain.ports import ExtratorDeVagas
from radar.matching.agy import ExtratorAgy
from radar.matching.gemini import ExtratorGemini
from radar.matching.prompt import VERSAO_DA_EXTRACAO
from radar.settings import Settings


def criar_extrator(settings: Settings) -> ExtratorDeVagas:
    if settings.avaliador == "agy":
        return ExtratorAgy(settings)
    cliente = genai.Client(api_key=settings.gemini_api_key)
    return ExtratorGemini(settings, cliente)


def nome_do_modelo(settings: Settings) -> str:
    if settings.avaliador == "agy":
        return settings.agy_modelo
    return settings.gemini_modelo


def identidade_da_extracao(settings: Settings) -> str:
    return f"{nome_do_modelo(settings)}#{VERSAO_DA_EXTRACAO}"
