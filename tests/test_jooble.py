import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.collectors.cota import CotaDeRequisicoes, CotaEsgotada
from radar.collectors.errors import ColetaIncompleta, ErroDeColeta
from radar.collectors.jooble import (
    LIMITE_DE_PAGINAS_POR_REGIAO,
    RESULTADOS_POR_PAGINA,
    URL_BUSCA,
    ColetorJooble,
)

CAMINHO_DO_FIXTURE = Path(__file__).parent / "fixtures" / "jooble_resposta.json"
PUBLICADAS_DESDE = datetime(2026, 11, 11, 10, 23, tzinfo=UTC)
CHAVE = "chave-de-teste"
RECENTE = "2026-11-14T11:32:43.5430000"


def item(numero: int, updated: str | None = RECENTE, source: str = "infojobs.com.br") -> dict:
    return {
        "title": "Estágio em <b>TI</b>",
        "location": "Rio de Janeiro, RJ",
        "snippet": "&nbsp;...Apoiar o time de <b>desenvolvimento</b>&nbsp;web.",
        "salary": "",
        "source": source,
        "type": "",
        "link": f"https://br.jooble.org/jdp/{numero}",
        "company": "Empresa Exemplo",
        "updated": updated,
        "id": numero,
    }


def resposta(*itens: dict) -> dict:
    return {"totalCount": len(itens), "jobs": list(itens)}


def pagina_cheia(primeiro: int = 1) -> dict:
    return resposta(*[item(numero) for numero in range(primeiro, primeiro + RESULTADOS_POR_PAGINA)])


def corpos_das_buscas(httpx_mock: HTTPXMock) -> list[dict]:
    return [json.loads(requisicao.content) for requisicao in httpx_mock.get_requests()]


def coletar(
    cidades: list[str] | None = None,
    esperas: list[float] | None = None,
    cota: CotaDeRequisicoes | None = None,
):
    registradas = esperas if esperas is not None else []
    with httpx.Client() as cliente_http:
        return ColetorJooble(
            CHAVE,
            cliente_http,
            PUBLICADAS_DESDE,
            cidades or [],
            esperar=registradas.append,
            cota=cota,
        ).coletar()


def test_converte_a_resposta_no_formato_da_jooble_em_vagas(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8")))

    vagas = coletar()

    primeira = vagas[0]
    assert primeira.id_externo == "1000000000000000001"
    assert primeira.fonte == "jooble"
    assert primeira.titulo == "Estágio em Desenvolvimento de Software"
    assert primeira.empresa == "Empresa Exemplo de Tecnologia"
    assert primeira.localizacao == "Rio de Janeiro, RJ"
    assert primeira.descricao == (
        "...Apoiar o time de desenvolvimento web; Participar das cerimônias ágeis "
        "Requisitos: cursando Ciência da Computação ou áreas afins ..."
    )
    assert primeira.url == "https://br.jooble.org/jdp/1000000000000000001"
    assert primeira.publicada_em == datetime(2026, 11, 14, 11, 32, 43, 543000, tzinfo=UTC)
    assert primeira.modalidade is None
    assert not primeira.descricao_completa


def test_identificador_negativo_e_empresa_vazia_do_formato_real_sao_aceitos(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(json=json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8")))

    por_id = {vaga.id_externo: vaga for vaga in coletar()}

    sem_empresa = por_id["-2000000000000000002"]
    assert sem_empresa.empresa == "Empresa não informada"
    assert sem_empresa.url == "https://br.jooble.org/away/-2000000000000000002"
    assert por_id["3000000000000000003"].publicada_em == datetime(
        2026, 11, 16, 8, 49, 26, 728147, tzinfo=UTC
    )


def test_nenhuma_vaga_da_jooble_chega_com_a_descricao_marcada_como_completa(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(json=json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8")))

    assert not any(vaga.descricao_completa for vaga in coletar())


def test_busca_so_a_palavra_estagio_em_cada_cidade_e_depois_no_pais(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=resposta(), is_reusable=True)

    coletar(["Rio de Janeiro", "Niterói"])

    assert all(
        str(requisicao.url) == f"{URL_BUSCA}/{CHAVE}" for requisicao in httpx_mock.get_requests()
    )
    assert corpos_das_buscas(httpx_mock) == [
        {
            "keywords": "estágio",
            "location": regiao,
            "page": 1,
            "ResultOnPage": 100,
            "datecreatedfrom": "2026-11-11",
        }
        for regiao in ["Rio de Janeiro", "Niterói", ""]
    ]


def test_data_de_corte_enviada_e_o_dia_em_utc(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=resposta())
    noite_de_brasilia = datetime.fromisoformat("2026-11-10T22:30:00-03:00")
    with httpx.Client() as cliente_http:
        ColetorJooble(CHAVE, cliente_http, noite_de_brasilia).coletar()

    assert corpos_das_buscas(httpx_mock)[0]["datecreatedfrom"] == "2026-11-11"


def test_pagina_cheia_pede_a_proxima_ate_o_teto_da_regiao(httpx_mock: HTTPXMock):
    httpx_mock.add_callback(
        lambda requisicao: httpx.Response(
            200,
            json=pagina_cheia(json.loads(requisicao.content)["page"] * RESULTADOS_POR_PAGINA),
        ),
        is_reusable=True,
    )

    vagas = coletar()

    assert [corpo["page"] for corpo in corpos_das_buscas(httpx_mock)] == list(
        range(1, LIMITE_DE_PAGINAS_POR_REGIAO + 1)
    )
    assert len(vagas) == LIMITE_DE_PAGINAS_POR_REGIAO * RESULTADOS_POR_PAGINA


def test_pagina_incompleta_encerra_a_regiao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=pagina_cheia())
    httpx_mock.add_response(json=resposta(*[item(numero) for numero in range(1000, 1037)]))

    vagas = coletar()

    assert [corpo["page"] for corpo in corpos_das_buscas(httpx_mock)] == [1, 2]
    assert len(vagas) == RESULTADOS_POR_PAGINA + 37


def test_teto_de_paginas_vale_para_cada_regiao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=pagina_cheia())
    httpx_mock.add_response(json=resposta(item(1000)))
    httpx_mock.add_response(json=resposta(item(2000)))

    coletar(["Rio de Janeiro"])

    assert [(corpo["location"], corpo["page"]) for corpo in corpos_das_buscas(httpx_mock)] == [
        ("Rio de Janeiro", 1),
        ("Rio de Janeiro", 2),
        ("", 1),
    ]


def test_descarta_no_cliente_a_vaga_de_antes_do_dia_de_corte(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        json=resposta(
            item(1),
            item(2, updated="2026-11-10T23:59:59.0000000"),
            item(3, updated="2026-10-20T00:00:00.0000000"),
            item(4, updated="2026-11-16T08:49:26.7281474+00:00"),
        )
    )

    assert [vaga.id_externo for vaga in coletar()] == ["1", "4"]


def test_vaga_do_dia_de_corte_so_com_a_data_passa_como_passa_no_filtro_da_jooble(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        json=resposta(
            item(1, updated="2026-11-11T00:00:00.0000000"),
            item(2, updated="2026-11-11T06:52:19.0410585+00:00"),
        )
    )

    assert [vaga.id_externo for vaga in coletar()] == ["1", "2"]


@pytest.mark.parametrize("updated", [None, "", "ontem"])
def test_vaga_sem_data_legivel_e_pulada_com_aviso(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture, updated: str | None
):
    httpx_mock.add_response(json=resposta(item(1), item(2, updated=updated)))

    assert [vaga.id_externo for vaga in coletar()] == ["1"]
    assert "Vaga da Jooble ignorada por formato inesperado (id 2)" in caplog.text


def test_item_que_nao_converte_e_pulado_sem_perder_os_outros(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    sem_titulo = item(2)
    del sem_titulo["title"]
    httpx_mock.add_response(json=resposta(item(1), sem_titulo, "texto solto", item(3)))

    assert [vaga.id_externo for vaga in coletar()] == ["1", "3"]
    assert "Vaga da Jooble ignorada por formato inesperado (id 2)" in caplog.text


def test_mesma_vaga_em_duas_regioes_aparece_uma_vez(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=resposta(item(1), item(2)))
    httpx_mock.add_response(json=resposta(item(2), item(3)))

    assert [vaga.id_externo for vaga in coletar(["Rio de Janeiro"])] == ["1", "2", "3"]


def test_localizacao_vazia_vira_brasil(httpx_mock: HTTPXMock):
    sem_local = item(1)
    sem_local["location"] = ""
    httpx_mock.add_response(json=resposta(sem_local))

    assert coletar()[0].localizacao == "Brasil"


def test_erro_transitorio_e_tentado_de_novo(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503, text="indisponível")
    httpx_mock.add_response(json=resposta(item(1)))
    esperas: list[float] = []

    vagas = coletar(esperas=esperas)

    assert len(vagas) == 1
    assert esperas == [2]


def test_erro_de_chave_nao_e_tentado_de_novo(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=403, text="Access Denied")

    with pytest.raises(ErroDeColeta, match="403"):
        coletar()

    assert len(httpx_mock.get_requests()) == 1


def test_resposta_sem_resultado_nenhum_e_coleta_vazia_e_nao_erro(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"totalCount": 0, "jobs": []})

    assert coletar() == []


@pytest.mark.parametrize(
    "corpo",
    [
        {"totalCount": 0},
        {"error": "location is required"},
        {"totalCount": 3, "jobs": None},
        {"totalCount": 3, "jobs": "nenhuma"},
        ["jobs"],
    ],
)
def test_resposta_sem_a_lista_de_vagas_e_falha_da_fonte_e_nao_zero_vagas(
    httpx_mock: HTTPXMock, corpo: object
):
    httpx_mock.add_response(json=corpo)

    with pytest.raises(ErroDeColeta, match="sem a lista de vagas em jobs"):
        coletar()


def test_corpo_que_nao_e_json_e_falha_da_fonte(httpx_mock: HTTPXMock):
    httpx_mock.add_response(text="<html>manutenção</html>")

    with pytest.raises(ErroDeColeta, match="não é JSON"):
        coletar()


def test_falha_depois_de_trazer_vagas_devolve_o_que_ja_veio_como_coleta_incompleta(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(json=resposta(item(1), item(2)))
    httpx_mock.add_response(status_code=400, text="location is required")

    with pytest.raises(ColetaIncompleta, match="Jooble respondeu HTTP 400") as incompleta:
        coletar(["Rio de Janeiro", "Niterói"])

    assert [vaga.id_externo for vaga in incompleta.value.vagas] == ["1", "2"]
    assert len(httpx_mock.get_requests()) == 2


def test_falha_na_primeira_regiao_sem_vaga_nenhuma_e_erro_de_coleta(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=400, text="pedido inválido")

    with pytest.raises(ErroDeColeta) as erro:
        coletar(["Rio de Janeiro"])

    assert not isinstance(erro.value, ColetaIncompleta)
    assert len(httpx_mock.get_requests()) == 1


def test_chave_da_api_nao_aparece_no_erro_nem_no_log(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    caplog.set_level("DEBUG", logger="radar")
    httpx_mock.add_response(json=resposta(item(1)))
    httpx_mock.add_exception(httpx.ConnectError("conexão recusada"), is_reusable=True)

    with pytest.raises(ColetaIncompleta) as incompleta:
        coletar(["Rio de Janeiro"])

    assert CHAVE not in str(incompleta.value)
    assert CHAVE not in caplog.text


def test_texto_com_nul_e_metade_solta_de_emoji_chega_limpo(httpx_mock: HTTPXMock):
    anuncio = item(1)
    anuncio["title"] = "Estágio\x00 em TI"
    anuncio["snippet"] = "Apoiar o " + chr(0xD83D) + "time"
    httpx_mock.add_response(content=json.dumps(resposta(anuncio)).encode())

    vaga = coletar()[0]

    assert vaga.titulo == "Estágio em TI"
    assert vaga.descricao == "Apoiar o time"


def test_cada_requisicao_conta_na_cota_inclusive_a_tentativa_repetida(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503, text="indisponível")
    httpx_mock.add_response(json=resposta(item(1)))
    httpx_mock.add_response(json=resposta(item(2)))
    cota = CotaDeRequisicoes()

    coletar(["Rio de Janeiro"], cota=cota)

    assert cota.requisicoes == 3
    assert not cota.esgotada


def test_coleta_para_quando_o_saldo_do_dia_acaba_e_devolve_o_que_ja_trouxe(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    httpx_mock.add_response(json=resposta(item(1), item(2)))
    cota = CotaDeRequisicoes(saldo=1)

    vagas = coletar(["Rio de Janeiro", "Niterói"], cota=cota)

    assert [vaga.id_externo for vaga in vagas] == ["1", "2"]
    assert len(httpx_mock.get_requests()) == 1
    assert cota.esgotada
    assert "Cota da Jooble esgotada; a coleta parou com 2 vagas" in caplog.text


def test_cota_sem_saldo_antes_da_primeira_vaga_e_erro_de_coleta_e_nao_zero_vagas(
    httpx_mock: HTTPXMock,
):
    cota = CotaDeRequisicoes(saldo=0)

    with pytest.raises(ErroDeColeta, match="Cota da Jooble esgotada"):
        coletar(["Rio de Janeiro"], cota=cota)

    assert httpx_mock.get_requests() == []
    assert cota.esgotada


def test_limite_diario_excedido_na_jooble_nao_e_tentado_de_novo(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=429, text="Too Many Requests")
    cota = CotaDeRequisicoes()
    esperas: list[float] = []

    with pytest.raises(ErroDeColeta, match="Cota da Jooble esgotada"):
        coletar(["Rio de Janeiro"], esperas=esperas, cota=cota)

    assert len(httpx_mock.get_requests()) == 1
    assert esperas == []
    assert cota.requisicoes == 1
    assert cota.esgotada


def test_limite_diario_excedido_depois_de_trazer_vagas_para_a_coleta_com_o_que_veio(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(json=resposta(item(1)))
    httpx_mock.add_response(status_code=429, text="Too Many Requests")
    cota = CotaDeRequisicoes()

    vagas = coletar(["Rio de Janeiro", "Niterói"], cota=cota)

    assert [vaga.id_externo for vaga in vagas] == ["1"]
    assert len(httpx_mock.get_requests()) == 2
    assert cota.requisicoes == 2
    assert cota.esgotada


def test_cota_que_a_fonte_declarou_esgotada_recusa_a_reserva_seguinte():
    cota = CotaDeRequisicoes(saldo=100)
    cota.reservar()

    cota.esgotar()

    assert cota.esgotada
    with pytest.raises(CotaEsgotada):
        cota.reservar()
    assert cota.requisicoes == 1


def test_sem_cota_informada_a_coleta_nao_tem_saldo_que_a_pare(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=resposta(item(1)), is_reusable=True)

    assert len(coletar(["Rio de Janeiro", "Niterói"])) == 1
    assert len(httpx_mock.get_requests()) == 3
