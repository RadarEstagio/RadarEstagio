import logging
from datetime import date, datetime, timedelta

from radar.collectors.adzuna import LIMITE_DE_PAGINAS_POR_REGIAO, CotaDaAdzuna, saldo_da_adzuna
from radar.collectors.factory import (
    cidades_de_interesse,
    ha_curso_desconhecido,
    termos_de_interesse,
)
from radar.domain.models import Usuario, Vaga
from radar.domain.ports import ColetorDeVagas, RepositorioDeAvaliacoes
from radar.storage.errors import ErroDeArmazenamento

FONTE_ADZUNA = "adzuna"
FONTE_DO_DIARIO = "adzuna:diario"
DIAS_DA_JANELA_SEMANAL = 7

logger = logging.getLogger(__name__)


def abrir_cota_da_adzuna(
    repositorio: RepositorioDeAvaliacoes, agora: datetime, reserva: int = 0
) -> CotaDaAdzuna:
    hoje = agora.date()
    try:
        usado_hoje = repositorio.requisicoes_da_fonte_desde(FONTE_ADZUNA, hoje)
        usado_na_semana = repositorio.requisicoes_da_fonte_desde(
            FONTE_ADZUNA, hoje - timedelta(days=DIAS_DA_JANELA_SEMANAL - 1)
        )
        usado_no_mes = repositorio.requisicoes_da_fonte_desde(FONTE_ADZUNA, hoje.replace(day=1))
    except ErroDeArmazenamento as erro:
        logger.warning("Uso da Adzuna não pôde ser lido; a coleta segue sem saldo: %s", erro)
        return CotaDaAdzuna()
    reserva_do_dia = 0 if not reserva or diario_ja_rodou(repositorio, hoje) else reserva
    return CotaDaAdzuna(
        saldo=saldo_da_adzuna(
            hoje=usado_hoje + reserva_do_dia,
            semana=usado_na_semana + reserva,
            mes=usado_no_mes + reserva,
        )
    )


def diario_ja_rodou(repositorio: RepositorioDeAvaliacoes, dia: date) -> bool:
    try:
        return repositorio.fonte_tem_registro_no_dia(FONTE_DO_DIARIO, dia)
    except ErroDeArmazenamento as erro:
        logger.warning("Registro do diário não pôde ser lido; a reserva do dia continua: %s", erro)
        return False


def reserva_do_diario(usuarios: list[Usuario]) -> int:
    regioes = 1 + len(cidades_de_interesse(usuarios))
    buscas = 2 if termos_de_interesse(usuarios) and ha_curso_desconhecido(usuarios) else 1
    return LIMITE_DE_PAGINAS_POR_REGIAO * regioes * buscas


def registrar_uso_da_adzuna(
    repositorio: RepositorioDeAvaliacoes, requisicoes: int, agora: datetime
) -> None:
    if not requisicoes:
        return
    try:
        repositorio.registrar_requisicoes_da_fonte(FONTE_ADZUNA, agora.date(), requisicoes)
    except ErroDeArmazenamento as erro:
        logger.warning("Uso da Adzuna não foi gravado (%d requisições): %s", requisicoes, erro)


def registrar_diario_da_adzuna(
    repositorio: RepositorioDeAvaliacoes, requisicoes: int, agora: datetime
) -> None:
    try:
        repositorio.registrar_requisicoes_da_fonte(FONTE_DO_DIARIO, agora.date(), requisicoes)
    except ErroDeArmazenamento as erro:
        logger.warning("O registro de que o diário rodou não foi gravado: %s", erro)


class ColetorComRegistroDeUso:
    def __init__(
        self,
        coletor: ColetorDeVagas,
        repositorio: RepositorioDeAvaliacoes,
        cota: CotaDaAdzuna,
        agora: datetime,
    ) -> None:
        self._coletor = coletor
        self._repositorio = repositorio
        self._cota = cota
        self._agora = agora

    def coletar(self) -> list[Vaga]:
        antes = self._cota.requisicoes
        try:
            return self._coletor.coletar()
        finally:
            registrar_uso_da_adzuna(self._repositorio, self._cota.requisicoes - antes, self._agora)


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
