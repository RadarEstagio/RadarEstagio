import logging
from datetime import datetime, timedelta

from radar.collectors.adzuna import CotaDaAdzuna, saldo_da_adzuna
from radar.domain.ports import RepositorioDeAvaliacoes
from radar.storage.errors import ErroDeArmazenamento

FONTE_ADZUNA = "adzuna"
DIAS_DA_JANELA_SEMANAL = 7

logger = logging.getLogger(__name__)


def abrir_cota_da_adzuna(repositorio: RepositorioDeAvaliacoes, agora: datetime) -> CotaDaAdzuna:
    hoje = agora.date()
    try:
        saldo = saldo_da_adzuna(
            hoje=repositorio.requisicoes_da_fonte_desde(FONTE_ADZUNA, hoje),
            semana=repositorio.requisicoes_da_fonte_desde(
                FONTE_ADZUNA, hoje - timedelta(days=DIAS_DA_JANELA_SEMANAL - 1)
            ),
            mes=repositorio.requisicoes_da_fonte_desde(FONTE_ADZUNA, hoje.replace(day=1)),
        )
    except ErroDeArmazenamento as erro:
        logger.warning("Uso da Adzuna não pôde ser lido; a coleta segue sem saldo: %s", erro)
        return CotaDaAdzuna()
    return CotaDaAdzuna(saldo=saldo)


def registrar_uso_da_adzuna(
    repositorio: RepositorioDeAvaliacoes, cota: CotaDaAdzuna, agora: datetime
) -> None:
    if not cota.requisicoes:
        return
    try:
        repositorio.registrar_requisicoes_da_fonte(FONTE_ADZUNA, agora.date(), cota.requisicoes)
    except ErroDeArmazenamento as erro:
        logger.warning("Uso da Adzuna não foi gravado (%d requisições): %s", cota.requisicoes, erro)


def uso_da_adzuna(repositorio: RepositorioDeAvaliacoes, agora: datetime) -> tuple[int, int] | None:
    hoje = agora.date()
    try:
        return (
            repositorio.requisicoes_da_fonte_desde(FONTE_ADZUNA, hoje),
            repositorio.requisicoes_da_fonte_desde(FONTE_ADZUNA, hoje.replace(day=1)),
        )
    except ErroDeArmazenamento as erro:
        logger.warning("Uso da Adzuna não pôde ser lido para o resumo: %s", erro)
        return None
