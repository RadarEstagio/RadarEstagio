import logging
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.domain.models import OrigemDoAnuncio, Vaga
from radar.matching.enriquecimento import EnriquecedorDeDescricoes

CAMINHO_DA_PAGINA = Path(__file__).parent / "fixtures" / "adzuna_detalhe.html"
CAMINHO_DA_PAGINA_COM_PARCEIRO = (
    Path(__file__).parent / "fixtures" / "adzuna_detalhe_com_parceiro.html"
)
URL_DA_PAGINA_COM_PARCEIRO = "https://www.adzuna.com.br/details/5967239538"


def pagina_com_parceiro() -> str:
    return CAMINHO_DA_PAGINA_COM_PARCEIRO.read_text(encoding="utf-8")


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


def test_nao_abre_pagina_de_vaga_que_nao_veio_da_adzuna(httpx_mock: HTTPXMock):
    completa = vaga_truncada().model_copy(
        update={"fonte": "gupy", "descricao": "Descrição completa da vaga"}
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([completa])

    assert enriquecidas[0].descricao == "Descrição completa da vaga"
    assert httpx_mock.get_requests() == []


def test_nunca_pede_a_pagina_da_vaga_no_site_da_jooble(httpx_mock: HTTPXMock):
    da_jooble = vaga_truncada().model_copy(
        update={
            "fonte": "jooble",
            "descricao": "...Apoiar o time de desenvolvimento web...",
            "url": "https://br.jooble.org/jdp/1000000000000000001",
            "origem": OrigemDoAnuncio(dominio="empregos.com.br"),
        }
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([da_jooble])

    assert enriquecidas == [da_jooble]
    assert not enriquecidas[0].descricao_completa
    assert httpx_mock.get_requests() == []


def anuncio_da_adzuna(id_externo: str, url: str) -> Vaga:
    return vaga_truncada().model_copy(update={"id_externo": id_externo, "url": url})


def test_anuncio_land_ad_e_lido_na_pagina_de_detalhe_da_mesma_vaga(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5967239538", text=pagina_com_parceiro()
    )
    anuncio = anuncio_da_adzuna(
        "5967239538",
        "https://www.adzuna.com.br/land/ad/5967239538?se=abc&utm_medium=api&v=1",
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([anuncio, anuncio])

    assert [str(pedido.url) for pedido in httpx_mock.get_requests()] == [
        "https://www.adzuna.com.br/details/5967239538"
    ]
    assert enriquecidas[0].descricao_completa
    assert "Python e SQL" in enriquecidas[0].descricao
    assert enriquecidas[0].origem == OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="79986")
    assert enriquecidas[0].url == anuncio.url


def test_so_o_anuncio_land_ad_troca_de_endereco(httpx_mock: HTTPXMock):
    pagina = CAMINHO_DA_PAGINA.read_text(encoding="utf-8")
    for endereco in (
        "https://www.adzuna.com.br/details/5880177309",
        "https://www.adzuna.com.br/details/5862521726",
        "https://www.adzuna.com.br/details/5880188747?ref=/land/ad/5880188747",
    ):
        httpx_mock.add_response(url=endereco, text=pagina)
    detalhe_com_land_ad_na_consulta = anuncio_da_adzuna(
        "5880188747", "https://www.adzuna.com.br/details/5880188747?ref=/land/ad/5880188747"
    )
    land_ad = anuncio_da_adzuna("5880177309", "https://www.adzuna.com.br/land/ad/5880177309?se=x")
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer(
            [land_ad, vaga_truncada(), detalhe_com_land_ad_na_consulta]
        )

    assert [str(pedido.url) for pedido in httpx_mock.get_requests()] == [
        "https://www.adzuna.com.br/details/5880177309",
        "https://www.adzuna.com.br/details/5862521726",
        "https://www.adzuna.com.br/details/5880188747?ref=/land/ad/5880188747",
    ]
    assert all(vaga.descricao_completa for vaga in enriquecidas)


def test_reconhece_land_ad_sem_diferenciar_caixa_nem_barra_dupla(httpx_mock: HTTPXMock):
    variantes = [
        anuncio_da_adzuna(numero, url)
        for numero, url in [
            ("5880177309", "https://www.adzuna.com.br/LAND/AD/5880177309?se=x"),
            ("5880176423", "https://www.adzuna.com.br//land/ad/5880176423?se=x"),
            ("5880188747", "https://www.adzuna.com.br/Land//Ad/5880188747"),
        ]
    ]
    httpx_mock.add_response(text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"), is_reusable=True)
    with httpx.Client() as cliente:
        EnriquecedorDeDescricoes(cliente).enriquecer(variantes)

    assert [str(pedido.url) for pedido in httpx_mock.get_requests()] == [
        "https://www.adzuna.com.br/details/5880177309",
        "https://www.adzuna.com.br/details/5880176423",
        "https://www.adzuna.com.br/details/5880188747",
    ]


def test_identificador_do_anuncio_land_ad_entra_escapado_no_endereco(httpx_mock: HTTPXMock):
    estranho = anuncio_da_adzuna("../1?x=2", "https://www.adzuna.com.br/land/ad/1")
    httpx_mock.add_response(text="<html></html>")
    with httpx.Client() as cliente:
        EnriquecedorDeDescricoes(cliente).enriquecer([estranho])

    assert [pedido.url.raw_path for pedido in httpx_mock.get_requests()] == [
        b"/details/..%2F1%3Fx%3D2"
    ]


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


def vaga_do_parceiro() -> Vaga:
    return anuncio_da_adzuna("5967239538", URL_DA_PAGINA_COM_PARCEIRO)


def origem_lida_de(pagina: str, httpx_mock: HTTPXMock) -> OrigemDoAnuncio | None:
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, text=pagina)
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_do_parceiro()])
    return enriquecidas[0].origem


def test_guarda_na_vaga_o_parceiro_e_o_identificador_que_a_pagina_informa(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, text=pagina_com_parceiro())
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_do_parceiro()])

    assert enriquecidas[0].origem == OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="79986")
    assert enriquecidas[0].descricao_completa
    assert "Python e SQL" in enriquecidas[0].descricao


def test_le_outro_parceiro_com_o_logo_em_outro_caminho(httpx_mock: HTTPXMock):
    pagina = (
        pagina_com_parceiro()
        .replace(
            'src="//zunastatic-abf.kxcdn.com/images/br/jobs/partners/logo_emprego.png" '
            'alt="Emprego"',
            'src="//zunastatic-abf.kxcdn.com/images/BR/partners/et17fTACZn_d7RSBLqbl6boew5M.png" '
            'alt="SourceStack"',
        )
        .replace('"source_id" : "79986"', '"source_id" : "506674"')
    )

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio(
        parceiro="SourceStack", id_do_parceiro="506674"
    )


def test_pagina_lida_sem_logo_nem_identificador_fica_sem_origem_identificada(
    httpx_mock: HTTPXMock,
):
    origem = origem_lida_de(CAMINHO_DA_PAGINA.read_text(encoding="utf-8"), httpx_mock)

    assert origem == OrigemDoAnuncio()
    assert not origem.identificada()


def test_logo_sem_alt_deixa_so_o_identificador(httpx_mock: HTTPXMock):
    pagina = pagina_com_parceiro().replace(' alt="Emprego"', "")

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio(id_do_parceiro="79986")


def test_logo_com_alt_em_branco_deixa_so_o_identificador(httpx_mock: HTTPXMock):
    pagina = pagina_com_parceiro().replace('alt="Emprego"', 'alt="  "')

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio(id_do_parceiro="79986")


def test_pagina_so_com_o_identificador_guarda_o_identificador(httpx_mock: HTTPXMock):
    pagina = '<section class="adp-body">Vaga</section><script>{"source_id" : "79986"}</script>'

    origem = origem_lida_de(pagina, httpx_mock)

    assert origem == OrigemDoAnuncio(id_do_parceiro="79986")
    assert origem.identificada()


def test_pagina_so_com_o_logo_guarda_o_nome_do_parceiro(httpx_mock: HTTPXMock):
    pagina = (
        '<img src="//zunastatic-abf.kxcdn.com/images/br/jobs/partners/logo_emprego.png" '
        'alt=" Emprego "><section class="adp-body">Vaga</section>'
    )

    origem = origem_lida_de(pagina, httpx_mock)

    assert origem == OrigemDoAnuncio(parceiro="Emprego")
    assert origem.identificada()


def test_imagem_fora_da_pasta_de_parceiros_nao_e_lida_como_parceiro(httpx_mock: HTTPXMock):
    pagina = (
        '<img src="//zunastatic-abf.kxcdn.com/images/global/jobs/logo.png" alt="Adzuna">'
        '<section class="adp-body">Vaga</section>'
    )

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio()


LOGO_DO_EMPREGO_PT = (
    '<img src="//zunastatic-abf.kxcdn.com/images/br/jobs/partners/logo_emprego.png" alt="Emprego">'
)
LOGO_DO_SOURCESTACK = (
    '<img src="//zunastatic-abf.kxcdn.com/images/BR/partners/logo.png" alt="SourceStack">'
)
LOGO_SEM_NOME = '<img src="//zunastatic-abf.kxcdn.com/images/BR/partners/logo.png">'
DADOS_DO_EMPREGO_PT = '<script>{"source_id" : "79986"}</script>'
DADOS_DO_SOURCESTACK = '<script>{"source_id" : "506674"}</script>'
CORPO_DO_ANUNCIO = '<section class="adp-body">Vaga</section>'


def test_com_dois_logos_e_dois_identificadores_vale_o_primeiro_de_cada(httpx_mock: HTTPXMock):
    pagina = (
        LOGO_DO_SOURCESTACK
        + DADOS_DO_SOURCESTACK
        + CORPO_DO_ANUNCIO
        + LOGO_DO_EMPREGO_PT
        + DADOS_DO_EMPREGO_PT
    )

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio(
        parceiro="SourceStack", id_do_parceiro="506674"
    )


def test_anuncio_do_emprego_pt_seguido_de_outro_parceiro_continua_sendo_do_emprego_pt(
    httpx_mock: HTTPXMock,
):
    pagina = (
        LOGO_DO_EMPREGO_PT
        + DADOS_DO_EMPREGO_PT
        + CORPO_DO_ANUNCIO
        + LOGO_DO_SOURCESTACK
        + DADOS_DO_SOURCESTACK
    )

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio(
        parceiro="Emprego", id_do_parceiro="79986"
    )


def test_primeiro_logo_sem_nome_nao_cede_o_lugar_ao_logo_seguinte(httpx_mock: HTTPXMock):
    pagina = LOGO_SEM_NOME + CORPO_DO_ANUNCIO + LOGO_DO_EMPREGO_PT

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio()


def test_dois_identificadores_no_mesmo_script_vale_o_primeiro(httpx_mock: HTTPXMock):
    pagina = CORPO_DO_ANUNCIO + (
        '<script>{"source_id" : "506674", "parecidos": [{"source_id" : "79986"}]}</script>'
    )

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio(id_do_parceiro="506674")


def test_identificador_escrito_no_texto_do_anuncio_nao_e_lido_como_origem(httpx_mock: HTTPXMock):
    pagina = '<section class="adp-body">Vaga com "source_id" : "79986" no texto</section>'

    assert origem_lida_de(pagina, httpx_mock) == OrigemDoAnuncio()


def test_pagina_lida_sem_descricao_ainda_guarda_a_origem(httpx_mock: HTTPXMock):
    pagina = (
        '<img src="//zunastatic-abf.kxcdn.com/images/br/jobs/partners/logo_emprego.png" '
        'alt="Emprego"><script>{"source_id" : "79986"}</script>'
    )
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, text=pagina)
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_do_parceiro()])

    assert enriquecidas[0].origem == OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="79986")
    assert not enriquecidas[0].descricao_completa
    assert enriquecidas[0].descricao == vaga_do_parceiro().descricao


@pytest.mark.parametrize("status", [403, 404, 410, 503])
def test_pagina_que_nao_foi_lida_deixa_a_vaga_sem_origem(httpx_mock: HTTPXMock, status: int):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, status_code=status)
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_do_parceiro()])

    assert enriquecidas[0].origem is None


def test_vaga_com_descricao_curta_tambem_tem_a_pagina_lida_para_achar_a_origem(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, text=pagina_com_parceiro())
    curta = vaga_do_parceiro().model_copy(
        update={"descricao": "Descrição curta que a API já dá inteira", "descricao_completa": True}
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([curta])

    assert enriquecidas[0].origem == OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="79986")
    assert enriquecidas[0].descricao_completa
    assert "Python e SQL" in enriquecidas[0].descricao


def test_vaga_com_descricao_curta_cuja_pagina_falha_fica_como_veio(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, status_code=403)
    curta = vaga_do_parceiro().model_copy(
        update={"descricao": "Descrição curta que a API já dá inteira", "descricao_completa": True}
    )
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)
        enriquecidas = enriquecedor.enriquecer([curta])

    assert enriquecidas == [curta]
    assert enriquecedor.paginas_nao_lidas == 1


def test_ler_a_origem_nao_acrescenta_requisicao_a_pagina(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, text=pagina_com_parceiro())
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)

        enriquecedor.enriquecer([vaga_do_parceiro()])
        enriquecedor.enriquecer([vaga_do_parceiro()])

    assert len(httpx_mock.get_requests()) == 1


def test_enriquecedor_novo_nao_tem_pagina_nao_lida():
    with httpx.Client() as cliente:
        assert EnriquecedorDeDescricoes(cliente).paginas_nao_lidas == 0


@pytest.mark.parametrize("status", [403, 404, 503])
def test_conta_a_pagina_que_respondeu_com_erro_http(httpx_mock: HTTPXMock, status: int):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, status_code=status)
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)
        enriquecedor.enriquecer([vaga_do_parceiro()])

    assert enriquecedor.paginas_nao_lidas == 1


def test_conta_a_pagina_que_falhou_por_erro_de_rede(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.ConnectError("conexão recusada"))
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)
        enriquecedor.enriquecer([vaga_do_parceiro()])

    assert enriquecedor.paginas_nao_lidas == 1


def test_conta_a_pagina_com_url_que_o_httpx_recusa(httpx_mock: HTTPXMock):
    sem_porta_valida = vaga_truncada().model_copy(
        update={"url": "https://www.adzuna.com.br:porta/details/1"}
    )
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)
        enriquecedor.enriquecer([sem_porta_valida])

    assert httpx_mock.get_requests() == []
    assert enriquecedor.paginas_nao_lidas == 1


def test_nao_conta_como_nao_lida_a_pagina_que_respondeu_mesmo_sem_descricao_nem_origem(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, text="<html><body></body></html>")
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)
        enriquecedor.enriquecer([vaga_do_parceiro(), vaga_truncada()])

    assert enriquecedor.paginas_nao_lidas == 0


def test_nao_conta_como_nao_lida_a_vaga_de_outra_fonte(httpx_mock: HTTPXMock):
    da_jooble = vaga_truncada().model_copy(
        update={"fonte": "jooble", "url": "https://br.jooble.org/jdp/1000000000000000001"}
    )
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)
        enriquecedor.enriquecer([da_jooble])

    assert httpx_mock.get_requests() == []
    assert enriquecedor.paginas_nao_lidas == 0


def test_soma_as_paginas_nao_lidas_e_conta_uma_vez_a_mesma_vaga_pedida_de_novo(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(url=URL_DA_PAGINA_COM_PARCEIRO, status_code=403)
    httpx_mock.add_response(url="https://www.adzuna.com.br/details/5862521726", status_code=403)
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5880188747",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    lida = anuncio_da_adzuna("5880188747", "https://www.adzuna.com.br/details/5880188747")
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)
        primeira = enriquecedor.enriquecer([vaga_do_parceiro(), lida, vaga_truncada()])
        segunda = enriquecedor.enriquecer([vaga_do_parceiro(), vaga_truncada()])

    assert enriquecedor.paginas_nao_lidas == 2
    assert len(httpx_mock.get_requests()) == 3
    assert [vaga.descricao_completa for vaga in primeira] == [False, True, False]
    assert segunda == [vaga_do_parceiro(), vaga_truncada()]
