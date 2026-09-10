import logging
import time
from collections.abc import Callable

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.domain.ports import ExtratorDeVagas
from radar.matching.errors import ErroDeAvaliacao, ErroTemporarioDeAvaliacao

logger = logging.getLogger(__name__)

ESPERA_PADRAO_EM_SEGUNDOS = 60
ESPERA_MAXIMA_EM_SEGUNDOS = 120
MARGEM_DE_ESPERA_EM_SEGUNDOS = 1
TENTATIVAS_APOS_COTA_EXCEDIDA = 3


class ExtratorEmLotes:
    def __init__(
        self,
        extrator: ExtratorDeVagas,
        tamanho_do_lote: int,
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        if tamanho_do_lote < 1:
            raise ValueError("tamanho_do_lote deve ser pelo menos 1")
        self._extrator = extrator
        self._tamanho_do_lote = tamanho_do_lote
        self._esperar = esperar
        self.requisicoes = 0

    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        resultados: list[ExtracaoDaVaga] = []
        for inicio in range(0, len(vagas), self._tamanho_do_lote):
            lote = vagas[inicio : inicio + self._tamanho_do_lote]
            try:
                self._extrair_lote(lote, resultados)
            except ErroTemporarioDeAvaliacao as erro:
                logger.warning(
                    "Avaliador indisponível ou cota excedida; "
                    "%d de %d vagas ficaram sem extração: %s",
                    len(vagas_sem_resultado(vagas, resultados)),
                    len(vagas),
                    erro,
                )
                break
        return resultados

    def _extrair_lote(self, lote: list[Vaga], resultados: list[ExtracaoDaVaga]) -> None:
        try:
            extraidas = self._chamar_esperando_a_cota(lote)
        except ErroTemporarioDeAvaliacao:
            raise
        except ErroDeAvaliacao as erro:
            self._dividir_e_tentar_de_novo(lote, erro, resultados)
            return
        resultados.extend(extraidas)
        faltantes = vagas_sem_resultado(lote, extraidas)
        if faltantes and len(lote) > 1:
            logger.info("%d vagas sem extração no lote; extraindo uma a uma", len(faltantes))
            for vaga in faltantes:
                self._extrair_lote([vaga], resultados)
        elif faltantes:
            logger.warning("Vaga %s ignorada: extrator não a devolveu", lote[0].identidade())

    def _chamar_esperando_a_cota(self, lote: list[Vaga]) -> list[ExtracaoDaVaga]:
        for tentativa in range(1, TENTATIVAS_APOS_COTA_EXCEDIDA + 1):
            try:
                return self._chamar(lote)
            except ErroTemporarioDeAvaliacao as erro:
                espera = erro.aguardar_segundos or ESPERA_PADRAO_EM_SEGUNDOS
                if espera > ESPERA_MAXIMA_EM_SEGUNDOS:
                    raise
                logger.info(
                    "Cota por minuto atingida; aguardando %.0f s (tentativa %d de %d)",
                    espera,
                    tentativa,
                    TENTATIVAS_APOS_COTA_EXCEDIDA,
                )
                self._esperar(espera + MARGEM_DE_ESPERA_EM_SEGUNDOS)
        return self._chamar(lote)

    def _chamar(self, lote: list[Vaga]) -> list[ExtracaoDaVaga]:
        self.requisicoes += 1
        return self._extrator.extrair(lote)

    def _dividir_e_tentar_de_novo(
        self, lote: list[Vaga], erro: ErroDeAvaliacao, resultados: list[ExtracaoDaVaga]
    ) -> None:
        if len(lote) == 1:
            logger.warning("Vaga %s ignorada: %s", lote[0].identidade(), erro)
            return
        metade = len(lote) // 2
        logger.info("Lote de %d vagas falhou (%s); dividindo em dois", len(lote), erro)
        self._extrair_lote(lote[:metade], resultados)
        self._extrair_lote(lote[metade:], resultados)


def vagas_sem_resultado(vagas: list[Vaga], extracoes: list[ExtracaoDaVaga]) -> list[Vaga]:
    extraidas = {extracao.id_vaga for extracao in extracoes}
    return [vaga for vaga in vagas if vaga.identidade() not in extraidas]
