from google import genai

from radar.avaliacao.prompt import JulgamentosDeEntregas, apenas_das_vagas, montar_prompt_do_juiz
from radar.domain.models import Julgamento, Perfil, Vaga
from radar.matching.gemini import gerar_json
from radar.settings import Settings


class JuizGemini:
    def __init__(self, settings: Settings, cliente: genai.Client) -> None:
        self._modelo = settings.juiz_modelo
        self._timeout_segundos = settings.gemini_timeout_segundos
        self._cliente = cliente

    def julgar(self, perfil: Perfil, vagas: list[Vaga]) -> list[Julgamento]:
        if not vagas:
            return []
        resposta = gerar_json(
            self._cliente,
            self._modelo,
            montar_prompt_do_juiz(perfil, vagas),
            JulgamentosDeEntregas,
            self._timeout_segundos,
        )
        return apenas_das_vagas(resposta.julgamentos, vagas)
