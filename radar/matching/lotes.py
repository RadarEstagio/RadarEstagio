import logging
import math
import time
from collections.abc import Callable

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.domain.ports import ExtratorDeVagas
from radar.matching.errors import (
    ErroDeAvaliacao,
    ErroTemporarioDeAvaliacao,
    FalhaInternaDoAvaliador,
)

logger = logging.getLogger(__name__)

ESPERA_PADRAO_EM_SEGUNDOS = 60
ESPERA_MAXIMA_EM_SEGUNDOS = 120
MARGEM_DE_ESPERA_EM_SEGUNDOS = 1
TENTATIVAS_APOS_COTA_EXCEDIDA = 3
ESPERA_APOS_FALHA_INTERNA_EM_SEGUNDOS = 10
REPETICOES_DE_FALHA_INTERNA_POR_LOTE = 1


class PrazoDaExtracaoEsgotado(Exception):
    pass


class ExtratorEmLotes:
    def __init__(
        self,
        extrator: ExtratorDeVagas,
        tamanho_do_lote: int,
        esperar: Callable[[float], None] = time.sleep,
        prazo_em_segundos: float = math.inf,
        timeout_da_chamada_em_segundos: float = 0,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        if tamanho_do_lote < 1:
            raise ValueError("tamanho_do_lote deve ser pelo menos 1")
        self._extrator = extrator
        self._tamanho_do_lote = tamanho_do_lote
        self._esperar = esperar
        self._prazo_em_segundos = prazo_em_segundos
        self._timeout_da_chamada = timeout_da_chamada_em_segundos
        self._relogio = relogio
        self._limite = math.inf
        self._repeticoes_de_falha_interna = REPETICOES_DE_FALHA_INTERNA_POR_LOTE
        self.requisicoes = 0

    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        resultados: list[ExtracaoDaVaga] = []
        self._limite = self._relogio() + self._prazo_em_segundos
        for inicio in range(0, len(vagas), self._tamanho_do_lote):
            lote = vagas[inicio : inicio + self._tamanho_do_lote]
            self._repeticoes_de_falha_interna = REPETICOES_DE_FALHA_INTERNA_POR_LOTE
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
            except PrazoDaExtracaoEsgotado as prazo:
                logger.warning(
                    "Prazo da extração de %.0f s esgotado%s; %d de %d vagas ficaram sem extração",
                    self._prazo_em_segundos,
                    f" enquanto {prazo}" if str(prazo) else "",
                    len(vagas_sem_resultado(vagas, resultados)),
                    len(vagas),
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
        if not faltantes:
            return
        if len(lote) == 1:
            logger.warning("Vaga %s ignorada: extrator não a devolveu", lote[0].identidade())
            return
        registrar_resposta_incompleta("Lote", lote, extraidas, faltantes)
        if 1 < len(faltantes) < len(lote) and ids_confiaveis(lote, extraidas):
            self._pedir_juntas_as_que_faltaram(faltantes, resultados)
        else:
            self._extrair_uma_a_uma(faltantes, resultados)

    def _pedir_juntas_as_que_faltaram(
        self, faltantes: list[Vaga], resultados: list[ExtracaoDaVaga]
    ) -> None:
        try:
            extraidas = self._chamar_esperando_a_cota(faltantes)
        except ErroTemporarioDeAvaliacao:
            raise
        except ErroDeAvaliacao as erro:
            logger.info(
                "Repetição de %d vagas falhou (%s); seguindo uma a uma", len(faltantes), erro
            )
            self._extrair_uma_a_uma(faltantes, resultados)
            return
        if not ids_confiaveis(faltantes, extraidas):
            logger.warning(
                "Repetição de %d vagas descartada; ids sem vaga %s; ids repetidos %s",
                len(faltantes),
                ids_sem_vaga(faltantes, extraidas),
                ids_repetidos(extraidas),
            )
            self._extrair_uma_a_uma(faltantes, resultados)
            return
        resultados.extend(extraidas)
        ainda_faltam = vagas_sem_resultado(faltantes, extraidas)
        if ainda_faltam:
            registrar_resposta_incompleta("Repetição", faltantes, extraidas, ainda_faltam)
        self._extrair_uma_a_uma(ainda_faltam, resultados)

    def _extrair_uma_a_uma(self, vagas: list[Vaga], resultados: list[ExtracaoDaVaga]) -> None:
        for vaga in vagas:
            self._extrair_lote([vaga], resultados)

    def _chamar_esperando_a_cota(self, lote: list[Vaga]) -> list[ExtracaoDaVaga]:
        for tentativa in range(1, TENTATIVAS_APOS_COTA_EXCEDIDA + 1):
            try:
                return self._chamar_repetindo_falha_interna(lote)
            except ErroTemporarioDeAvaliacao as erro:
                espera = erro.aguardar_segundos or ESPERA_PADRAO_EM_SEGUNDOS
                if espera > ESPERA_MAXIMA_EM_SEGUNDOS:
                    raise
                self._garantir_que_cabe_no_prazo(
                    espera + MARGEM_DE_ESPERA_EM_SEGUNDOS, f"esperava a cota ({erro})"
                )
                logger.info(
                    "Cota por minuto atingida; aguardando %.0f s (tentativa %d de %d)",
                    espera,
                    tentativa,
                    TENTATIVAS_APOS_COTA_EXCEDIDA,
                )
                self._esperar(espera + MARGEM_DE_ESPERA_EM_SEGUNDOS)
        return self._chamar_repetindo_falha_interna(lote)

    def _chamar_repetindo_falha_interna(self, lote: list[Vaga]) -> list[ExtracaoDaVaga]:
        try:
            return self._chamar(lote)
        except FalhaInternaDoAvaliador as erro:
            if self._repeticoes_de_falha_interna < 1:
                raise ErroDeAvaliacao(f"{erro} (persistiu depois de repetir)") from None
            self._repeticoes_de_falha_interna -= 1
            self._garantir_que_cabe_no_prazo(
                ESPERA_APOS_FALHA_INTERNA_EM_SEGUNDOS, f"esperava para repetir ({erro})"
            )
            logger.info(
                "Falha interna do avaliador; aguardando %.0f s para repetir o lote de %d vagas",
                ESPERA_APOS_FALHA_INTERNA_EM_SEGUNDOS,
                len(lote),
            )
            self._esperar(ESPERA_APOS_FALHA_INTERNA_EM_SEGUNDOS)
        return self._chamar_repetindo_falha_interna(lote)

    def _chamar(self, lote: list[Vaga]) -> list[ExtracaoDaVaga]:
        self._garantir_que_cabe_no_prazo(self._timeout_da_chamada)
        self.requisicoes += 1
        return self._extrator.extrair(lote)

    def _garantir_que_cabe_no_prazo(self, segundos_a_mais: float, motivo: str = "") -> None:
        if self._relogio() + segundos_a_mais > self._limite:
            raise PrazoDaExtracaoEsgotado(motivo)

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


def ids_sem_vaga(lote: list[Vaga], extraidas: list[ExtracaoDaVaga]) -> list[str]:
    esperados = {vaga.identidade() for vaga in lote}
    return sorted({extracao.id_vaga for extracao in extraidas} - esperados)


def ids_repetidos(extraidas: list[ExtracaoDaVaga]) -> list[str]:
    devolvidos = [extracao.id_vaga for extracao in extraidas]
    return sorted({id_vaga for id_vaga in devolvidos if devolvidos.count(id_vaga) > 1})


def ids_confiaveis(lote: list[Vaga], extraidas: list[ExtracaoDaVaga]) -> bool:
    return not ids_sem_vaga(lote, extraidas) and not ids_repetidos(extraidas)


def registrar_resposta_incompleta(
    chamada: str, vagas: list[Vaga], extraidas: list[ExtracaoDaVaga], faltantes: list[Vaga]
) -> None:
    logger.warning(
        "%s de %d vagas voltou com %d extrações; faltaram %s; ids sem vaga %s; ids repetidos %s",
        chamada,
        len(vagas),
        len(extraidas),
        [vaga.identidade() for vaga in faltantes],
        ids_sem_vaga(vagas, extraidas),
        ids_repetidos(extraidas),
    )
