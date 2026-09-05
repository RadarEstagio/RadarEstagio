from datetime import UTC, datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.collectors.errors import ErroDeColeta
from radar.collectors.jooble import (
    LIMITE_DE_PAGINAS_POR_BUSCA,
    TERMOS_DE_BUSCA,
    URL_BUSCA,
    ColetorJooble,
)

PUBLICADAS_DESDE = datetime(2026, 9, 1, tzinfo=UTC)
CHAVE = "chave-de-teste"


def item(numero: int, updated: str | None = "2026-09-04T00:00:00") -> dict:
    return {
        "id": numero,
        "title": "Estágio em <b>TI</b>",
        "location": "Rio de Janeiro, RJ",
        "snippet": "Apoiar o time de <b>desenvolvimento</b>&nbsp;web.",
        "source": "infojobs.com.br",
        "link": f"https://br.jooble.org/desc/{numero}",
        "company": "Empresa Exemplo",
        "updated": updated,
    }


def resposta(*itens: dict) -> dict:
    return {"totalCount": len(itens), "jobs": list(itens)}


@pytest.fixture
def coletor():
    with httpx.Client() as cliente_http:
        yield ColetorJooble(CHAVE, cliente_http, PUBLICADAS_DESDE, esperar=lambda _: None)


def test_converte_resposta_do_jooble_em_vagas(httpx_mock: HTTPXMock, coletor: ColetorJooble):
    httpx_mock.add_response(json=resposta(item(1)))
    httpx_mock.add_response(json=resposta(), is_reusable=True)

    vagas = coletor.coletar()

    assert len(vagas) == 1
    vaga = vagas[0]
    assert vaga.id_externo == "1"
    assert vaga.fonte == "jooble"
    assert vaga.titulo == "Estágio em TI"
    assert vaga.empresa == "Empresa Exemplo"
    assert vaga.localizacao == "Rio de Janeiro, RJ"
    assert vaga.descricao == "Apoiar o time de desenvolvimento web."
    assert vaga.url == "https://br.jooble.org/desc/1"
    assert vaga.publicada_em == datetime(2026, 9, 4, tzinfo=UTC)
    assert not vaga.descricao_completa


def test_envia_chave_termos_e_cidades(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=resposta(), is_reusable=True)
    with httpx.Client() as cliente_http:
        ColetorJooble(
            CHAVE, cliente_http, PUBLICADAS_DESDE, ["Rio de Janeiro"], esperar=lambda _: None
        ).coletar()

    requisicoes = httpx_mock.get_requests()
    assert all(str(r.url) == f"{URL_BUSCA}/{CHAVE}" for r in requisicoes)
    corpos = [r.read().decode() for r in requisicoes]
    assert len(requisicoes) == 2 * len(TERMOS_DE_BUSCA)
    assert sum('"location": ""' in corpo or '"location":""' in corpo for corpo in corpos) == len(
        TERMOS_DE_BUSCA
    )


def test_descarta_vaga_antiga_ou_sem_data(httpx_mock: HTTPXMock, coletor: ColetorJooble):
    httpx_mock.add_response(
        json=resposta(item(1), item(2, updated="2026-08-20T00:00:00"), item(3, updated=None))
    )
    httpx_mock.add_response(json=resposta(), is_reusable=True)

    assert [vaga.id_externo for vaga in coletor.coletar()] == ["1"]


def test_pagina_cheia_busca_a_proxima_ate_o_limite(httpx_mock: HTTPXMock, coletor: ColetorJooble):
    pagina_cheia = resposta(*[item(numero) for numero in range(1, 21)])
    for _ in range(LIMITE_DE_PAGINAS_POR_BUSCA):
        httpx_mock.add_response(json=pagina_cheia)
    httpx_mock.add_response(json=resposta(), is_reusable=True)

    coletor.coletar()

    corpos = [r.read().decode() for r in httpx_mock.get_requests()[:3]]
    assert ['"page": "1"' in corpos[0], '"page": "2"' in corpos[1], '"page": "3"' in corpos[2]]


def test_mesma_vaga_em_dois_termos_aparece_uma_vez(httpx_mock: HTTPXMock, coletor: ColetorJooble):
    httpx_mock.add_response(json=resposta(item(1)))
    httpx_mock.add_response(json=resposta(item(1)))
    httpx_mock.add_response(json=resposta(), is_reusable=True)

    assert len(coletor.coletar()) == 1


def test_erro_transitorio_e_tentado_de_novo(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503, text="indisponível")
    httpx_mock.add_response(json=resposta(item(1)))
    httpx_mock.add_response(json=resposta(), is_reusable=True)
    esperas: list[float] = []
    with httpx.Client() as cliente_http:
        vagas = ColetorJooble(
            CHAVE, cliente_http, PUBLICADAS_DESDE, esperar=esperas.append
        ).coletar()

    assert len(vagas) == 1
    assert esperas == [2]


def test_erro_de_chave_nao_e_tentado_de_novo(httpx_mock: HTTPXMock, coletor: ColetorJooble):
    httpx_mock.add_response(status_code=403, text="proibido")

    with pytest.raises(ErroDeColeta, match="403"):
        coletor.coletar()
