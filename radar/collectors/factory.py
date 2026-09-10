from collections.abc import Iterable
from datetime import datetime, timedelta

import httpx

from radar.collectors.adzuna import ColetorAdzuna
from radar.collectors.composto import ColetorComposto
from radar.collectors.gupy import ColetorGupy
from radar.collectors.jooble import ColetorJooble
from radar.domain.areas import area_do_curso, termos_de_busca
from radar.domain.models import Modalidade, Usuario
from radar.domain.ports import ColetorDeVagas
from radar.domain.regioes import polo_da_regiao
from radar.settings import Settings

MODALIDADES_QUE_DEPENDEM_DA_CIDADE = frozenset({Modalidade.PRESENCIAL, Modalidade.HIBRIDO})


def criar_coletor(
    settings: Settings,
    cliente_http: httpx.Client,
    agora: datetime,
    cidades: Iterable[str] = (),
    termos: Iterable[str] = (),
    busca_geral: bool = False,
) -> ColetorDeVagas:
    publicadas_desde = agora - timedelta(days=settings.dias_recentes)
    cidades_de_busca = tuple(cidades)
    termos_de_interesse = tuple(termos)
    coletores_disponiveis: dict[str, ColetorDeVagas] = {
        "adzuna": ColetorAdzuna(
            settings,
            cliente_http,
            cidades_de_busca,
            termos=termos_de_interesse,
            busca_geral=busca_geral,
        ),
        "gupy": ColetorGupy(cliente_http, publicadas_desde, cidades_de_busca),
        "jooble": ColetorJooble(
            settings.jooble_api_key,
            cliente_http,
            publicadas_desde,
            cidades_de_busca,
            termos=termos_de_interesse,
            busca_geral=busca_geral,
        ),
    }
    return ColetorComposto(
        {fonte: coletores_disponiveis[fonte] for fonte in settings.fontes_selecionadas()}
    )


def cidades_de_interesse(usuarios: Iterable[Usuario]) -> list[str]:
    perfis = [
        usuario.perfil
        for usuario in usuarios
        if usuario.perfil.modalidade in MODALIDADES_QUE_DEPENDEM_DA_CIDADE
    ]
    cidades = {perfil.nome_da_cidade() for perfil in perfis}
    polos = {polo for perfil in perfis if (polo := polo_da_regiao(perfil.cidade))}
    return sorted(cidades | polos)


def areas_de_interesse(usuarios: Iterable[Usuario]) -> set[str]:
    areas = {area_do_curso(usuario.perfil.curso) for usuario in usuarios}
    return {area for area in areas if area is not None}


def termos_de_interesse(usuarios: Iterable[Usuario]) -> tuple[str, ...]:
    return termos_de_busca(areas_de_interesse(usuarios))


def ha_curso_desconhecido(usuarios: Iterable[Usuario]) -> bool:
    return any(area_do_curso(usuario.perfil.curso) is None for usuario in usuarios)
