import logging
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pytest_httpx import HTTPXMock

from radar.domain.models import Vaga
from radar.matching.enriquecimento import EnriquecedorDeDescricoes

CAMINHO_DA_PAGINA = Path(__file__).parent / "fixtures" / "adzuna_detalhe.html"


def vaga_truncada() -> Vaga:
    return Vaga(
        id_externo="5862521726",
        fonte="adzuna",
        titulo="Estágio Ti Desenvolvimento",
        empresa="Trinks",
        localizacao="Rio de Janeiro",
        descricao="Atuar com um time e contar com o auxílio de profi".ljust(499, " ") + "…",
        url="https://www.adzuna.com.br/details/5862521726",
        publicada_em=datetime(2026, 8, 31, tzinfo=UTC),
        descricao_completa=False,
    )


def test_devolve_a_vaga_com_descricao_completa_da_pagina_da_adzuna(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_truncada()])

    assert all(
        tecnologia in enriquecidas[0].descricao for tecnologia in ("C#", "JavaScript", "SQL Server")
    )
    assert enriquecidas[0].descricao_completa


def test_busca_a_pagina_da_mesma_vaga_uma_vez_por_execucao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)

        enriquecedor.enriquecer([vaga_truncada()])
        enriquecedor.enriquecer([vaga_truncada()])

    assert len(httpx_mock.get_requests()) == 1


def test_nao_abre_pagina_de_vaga_que_nao_e_resumo_truncado(httpx_mock: HTTPXMock):
    completa = vaga_truncada().model_copy(
        update={"fonte": "gupy", "descricao": "Descrição completa da vaga"}
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([completa])

    assert enriquecidas[0].descricao == "Descrição completa da vaga"
    assert httpx_mock.get_requests() == []


def anuncio_da_adzuna(id_externo: str, url: str) -> Vaga:
    return vaga_truncada().model_copy(update={"id_externo": id_externo, "url": url})


def test_nao_pede_a_pagina_de_anuncio_land_ad_que_a_adzuna_sempre_recusa(
    httpx_mock: HTTPXMock, caplog
):
    anuncio = anuncio_da_adzuna(
        "5880177309",
        "https://www.adzuna.com.br/land/ad/5880177309?se=abc&utm_medium=api&v=1",
    )
    caplog.set_level(logging.INFO, logger="radar.matching.enriquecimento")
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([anuncio, anuncio])

    assert httpx_mock.get_requests() == []
    assert enriquecidas == [anuncio, anuncio]
    assert not enriquecidas[0].descricao_completa
    assert not [registro for registro in caplog.records if registro.levelno >= logging.WARNING]


def test_pula_so_o_anuncio_land_ad_e_informa_quantos_ficaram_de_fora(httpx_mock: HTTPXMock, caplog):
    pagina = CAMINHO_DA_PAGINA.read_text(encoding="utf-8")
    httpx_mock.add_response(url="https://www.adzuna.com.br/details/5862521726", text=pagina)
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5880188747?ref=/land/ad/5880188747", text=pagina
    )
    detalhe = vaga_truncada()
    detalhe_com_land_ad_na_consulta = anuncio_da_adzuna(
        "5880188747", "https://www.adzuna.com.br/details/5880188747?ref=/land/ad/5880188747"
    )
    anuncios = [
        anuncio_da_adzuna(numero, f"https://www.adzuna.com.br/land/ad/{numero}?se=x")
        for numero in ("5880177309", "5880176423")
    ]
    caplog.set_level(logging.INFO, logger="radar.matching.enriquecimento")
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer(
            [anuncios[0], detalhe, anuncios[1], detalhe_com_land_ad_na_consulta]
        )

    assert [str(pedido.url) for pedido in httpx_mock.get_requests()] == [
        "https://www.adzuna.com.br/details/5862521726",
        "https://www.adzuna.com.br/details/5880188747?ref=/land/ad/5880188747",
    ]
    assert [vaga.descricao_completa for vaga in enriquecidas] == [False, True, False, True]
    informativos = [
        registro.getMessage() for registro in caplog.records if registro.levelno == logging.INFO
    ]
    assert informativos == [
        "2 vagas da Adzuna com anúncio /land/ad/ ficaram com a descrição da API"
    ]


def test_reconhece_land_ad_sem_diferenciar_caixa_nem_barra_dupla(httpx_mock: HTTPXMock):
    variantes = [
        anuncio_da_adzuna(numero, url)
        for numero, url in [
            ("5880177309", "https://www.adzuna.com.br/LAND/AD/5880177309?se=x"),
            ("5880176423", "https://www.adzuna.com.br//land/ad/5880176423?se=x"),
            ("5880188747", "https://www.adzuna.com.br/Land//Ad/5880188747"),
        ]
    ]
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer(variantes)

    assert httpx_mock.get_requests() == []
    assert enriquecidas == variantes


def test_mantem_descricao_marcada_como_incompleta_quando_pagina_falha(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        status_code=503,
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_truncada()])

    assert not enriquecidas[0].descricao_completa


def test_url_que_o_urlsplit_recusa_nao_derruba_o_enriquecimento(httpx_mock: HTTPXMock):
    sem_caminho_legivel = vaga_truncada().model_copy(update={"url": "https://[oops/details/1"})
    httpx_mock.add_response(text="<html></html>")

    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([sem_caminho_legivel])

    assert not enriquecidas[0].descricao_completa


def test_url_que_o_httpx_recusa_mantem_a_descricao_da_api(httpx_mock: HTTPXMock, caplog):
    sem_porta_valida = vaga_truncada().model_copy(
        update={"url": "https://www.adzuna.com.br:porta/details/1"}
    )

    with httpx.Client() as cliente, caplog.at_level(logging.WARNING):
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([sem_porta_valida])

    assert httpx_mock.get_requests() == []
    assert not enriquecidas[0].descricao_completa
    assert "InvalidURL" in caplog.text


def test_descricao_lida_da_pagina_chega_sem_nul(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text='<section class="adp-body">Vaga\x00 com C# e SQL</section>',
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_truncada()])

    assert enriquecidas[0].descricao == "Vaga com C# e SQL"
    assert enriquecidas[0].descricao_completa
