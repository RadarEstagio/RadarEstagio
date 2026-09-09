import subprocess

from radar.avaliacao.prompt import JulgamentosDeEntregas, apenas_das_vagas, montar_prompt_do_juiz
from radar.domain.models import Julgamento, Perfil, Vaga
from radar.matching.agy import Executor, pedir_saida_estruturada
from radar.settings import Settings


class JuizAgy:
    def __init__(self, settings: Settings, executor: Executor = subprocess.run) -> None:
        self._modelo = settings.juiz_modelo
        self._timeout_segundos = settings.agy_timeout_segundos
        self._executor = executor

    def julgar(self, perfil: Perfil, vagas: list[Vaga]) -> list[Julgamento]:
        if not vagas:
            return []
        resposta = pedir_saida_estruturada(
            montar_prompt_do_juiz(perfil, vagas),
            JulgamentosDeEntregas,
            self._modelo,
            self._timeout_segundos,
            self._executor,
        )
        return apenas_das_vagas(resposta.julgamentos, vagas)
