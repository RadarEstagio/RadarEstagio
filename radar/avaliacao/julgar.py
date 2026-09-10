import logging
import random
from collections.abc import Iterator
from uuid import UUID

from radar.domain.models import EntregaJulgada, EntregaParaJulgar, ResultadoDoJulgamento
from radar.domain.ports import JuizDeRecomendacoes
from radar.matching.errors import ErroDeAvaliacao

logger = logging.getLogger(__name__)

TAMANHO_DO_LOTE = 8


def julgar_entregas(
    entregas: list[EntregaParaJulgar],
    juiz: JuizDeRecomendacoes,
    amostra: int,
    semente: int,
    modelo: str,
    dias: int,
) -> ResultadoDoJulgamento:
    escolhidas = amostrar(entregas, amostra, semente)
    resultado = ResultadoDoJulgamento(
        modelo=modelo, dias=dias, entregas_no_periodo=len(entregas), amostradas=len(escolhidas)
    )
    for grupo in agrupar_por_perfil(escolhidas).values():
        for lote in lotes(grupo, TAMANHO_DO_LOTE):
            try:
                julgamentos = juiz.julgar(lote[0].perfil, [entrega.vaga for entrega in lote])
            except ErroDeAvaliacao as erro:
                logger.warning("lote de %d entregas ficou sem julgamento: %s", len(lote), erro)
                resultado.sem_julgamento += len(lote)
                resultado.ultimo_erro = str(erro)
                continue
            por_id = {julgamento.id_vaga: julgamento for julgamento in julgamentos}
            for entrega in lote:
                julgamento = por_id.get(entrega.vaga.identidade())
                if julgamento is None:
                    resultado.sem_julgamento += 1
                    continue
                resultado.julgadas.append(EntregaJulgada(entrega=entrega, julgamento=julgamento))
    return resultado


def amostrar(
    entregas: list[EntregaParaJulgar], amostra: int, semente: int
) -> list[EntregaParaJulgar]:
    if amostra >= len(entregas):
        return list(entregas)
    return random.Random(semente).sample(entregas, amostra)


def agrupar_por_perfil(
    entregas: list[EntregaParaJulgar],
) -> dict[UUID, list[EntregaParaJulgar]]:
    grupos: dict[UUID, list[EntregaParaJulgar]] = {}
    for entrega in entregas:
        grupos.setdefault(entrega.perfil_id, []).append(entrega)
    return grupos


def lotes(entregas: list[EntregaParaJulgar], tamanho: int) -> Iterator[list[EntregaParaJulgar]]:
    for inicio in range(0, len(entregas), tamanho):
        yield entregas[inicio : inicio + tamanho]
