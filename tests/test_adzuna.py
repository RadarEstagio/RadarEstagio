import json
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.collectors.adzuna import (
    LIMITE_DE_PAGINAS_POR_REGIAO,
    LIMITE_POR_MINUTO,
    RESULTADOS_POR_PAGINA,
    URL_BUSCA,
    ColetorAdzuna,
    CotaDaAdzuna,
    saldo_da_adzuna,
)
from radar.collectors.errors import ColetaIncompleta, ErroDeColeta
from radar.collectors.tentativas import TENTATIVAS_POR_REQUISICAO
from radar.settings import Settings

CAMINHO_DO_FIXTURE = Path(__file__).parent / "fixtures" / "adzuna_resposta.json"
APP_KEY_DE_TESTE = "app-key-de-teste"
TERMOS_DE_BUSCA = ("desenvolvimento", "dados")


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key=APP_KEY_DE_TESTE,
        gemini_api_key="gemini-de-teste",
        telegram_bot_token="token-de-teste",
        telegram_chat_id="123",
        dias_recentes=3,
    )


def resposta_gravada() -> dict:
    return json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8"))


def item(numero: int, area: list[str] | None = None) -> dict:
    modelo = resposta_gravada()["results"][0]
    modelo["id"] = numero
    if area is not None:
        modelo["location"] = {"display_name": ", ".join(reversed(area[-2:])), "area": area}
    return modelo


def url_da_pagina(pagina: int) -> re.Pattern[str]:
    return re.compile(re.escape(f"{URL_BUSCA}/{pagina}?"))


def pagina_cheia(inicio: int) -> dict:
    return {"results": [item(numero) for numero in range(inicio, inicio + RESULTADOS_POR_PAGINA)]}


@pytest.fixture
def coletor():
    with httpx.Client() as cliente_http:
        yield ColetorAdzuna(
            settings_de_teste(), cliente_http, esperar=lambda _: None, termos=TERMOS_DE_BUSCA
        )


def test_converte_resposta_da_adzuna_em_vagas(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json=resposta_gravada())

    vagas = coletor.coletar()

    assert len(vagas) == 3
    primeira = vagas[0]
    assert primeira.id_externo == "9000000001"
    assert primeira.fonte == "adzuna"
    assert primeira.titulo == "Vaga de Estágio em TI"
    assert primeira.empresa == "Empresa Exemplo Tecnologia"
    assert primeira.localizacao == "Salvador, Bahia"
    assert primeira.descricao.startswith("Vaga ilustrativa de estágio em TI")
    assert primeira.url == (
        "https://www.adzuna.com.br/details/9000000001?utm_medium=api&utm_source=teste"
    )
    assert primeira.publicada_em == datetime(2026, 8, 25, 18, 49, 50, tzinfo=UTC)


def test_vaga_sem_empresa_ou_localizacao_recebe_valores_padrao(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna
):
    item = resposta_gravada()["results"][0]
    item["company"] = {"__CLASS__": "Adzuna::API::Response::Company"}
    del item["location"]
    httpx_mock.add_response(json={"results": [item]})

    vaga = coletor.coletar()[0]

    assert vaga.empresa == "Empresa não informada"
    assert vaga.localizacao == "Brasil"


def test_marca_resumo_de_500_caracteres_como_descricao_incompleta(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna
):
    resumido = item(1)
    resumido["description"] = "x" * 499 + "…"
    httpx_mock.add_response(json={"results": [resumido]})

    vaga = coletor.coletar()[0]

    assert not vaga.descricao_completa


def test_envia_credenciais_e_filtros_na_busca(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json={"results": []})

    coletor.coletar()

    requisicao = httpx_mock.get_request()
    assert requisicao.method == "GET"
    assert str(requisicao.url).startswith(URL_BUSCA)
    parametros = requisicao.url.params
    assert parametros["app_id"] == "app-id-de-teste"
    assert parametros["app_key"] == APP_KEY_DE_TESTE
    assert parametros["what_and"] == "estágio"
    assert parametros["what_or"] == "desenvolvimento dados"
    assert "category" not in parametros
    assert "where" not in parametros
    assert parametros["max_days_old"] == "3"
    assert parametros["results_per_page"] == "50"


def test_busca_tambem_por_cidade_dos_usuarios_presenciais(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": []}, is_reusable=True)
    with httpx.Client() as cliente_http:
        ColetorAdzuna(
            settings_de_teste(), cliente_http, ["Rio de Janeiro", "Niterói"], termos=TERMOS_DE_BUSCA
        ).coletar()

    locais = [requisicao.url.params.get("where") for requisicao in httpx_mock.get_requests()]

    assert locais == [None, "Rio de Janeiro", "Niterói"]


def test_pagina_cheia_busca_a_proxima_pagina(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(url=url_da_pagina(1), json=pagina_cheia(1))
    httpx_mock.add_response(url=url_da_pagina(2), json={"results": [item(999)]})

    vagas = coletor.coletar()

    assert len(vagas) == RESULTADOS_POR_PAGINA + 1
    assert len(httpx_mock.get_requests()) == 2


def test_respeita_o_limite_de_paginas(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    for pagina in range(1, LIMITE_DE_PAGINAS_POR_REGIAO + 1):
        inicio = pagina * RESULTADOS_POR_PAGINA
        httpx_mock.add_response(url=url_da_pagina(pagina), json=pagina_cheia(inicio))

    vagas = coletor.coletar()

    assert len(vagas) == LIMITE_DE_PAGINAS_POR_REGIAO * RESULTADOS_POR_PAGINA
    assert len(httpx_mock.get_requests()) == LIMITE_DE_PAGINAS_POR_REGIAO


def test_mesma_vaga_no_pais_e_na_cidade_aparece_uma_vez(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": [item(1), item(2)]})
    httpx_mock.add_response(json={"results": [item(2), item(3)]})
    with httpx.Client() as cliente_http:
        vagas = ColetorAdzuna(
            settings_de_teste(), cliente_http, ["Rio de Janeiro"], termos=TERMOS_DE_BUSCA
        ).coletar()

    assert [vaga.id_externo for vaga in vagas] == ["1", "2", "3"]


def test_localizacao_usa_cidade_e_estado_mesmo_quando_ha_bairro(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna
):
    com_bairro = item(
        1, area=["Brasil", "Sudeste", "Estado do Rio de Janeiro", "Rio de Janeiro", "Copacabana"]
    )
    httpx_mock.add_response(json={"results": [com_bairro]})

    assert coletor.coletar()[0].localizacao == "Rio de Janeiro, Estado do Rio de Janeiro"


def test_resposta_sem_resultados_retorna_lista_vazia(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json={"count": 0, "results": []})

    assert coletor.coletar() == []


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_erro_http_levanta_erro_de_coleta_sem_expor_credenciais(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna, status: int
):
    httpx_mock.add_response(status_code=status, json={"exception": "erro"}, is_reusable=True)

    with pytest.raises(ErroDeColeta) as capturado:
        coletor.coletar()

    assert str(status) in str(capturado.value)
    assert APP_KEY_DE_TESTE not in str(capturado.value)
    assert capturado.value.__cause__ is None


def test_falha_de_rede_levanta_erro_de_coleta(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_exception(httpx.ConnectError("conexão recusada"), is_reusable=True)

    with pytest.raises(ErroDeColeta, match="ConnectError"):
        coletor.coletar()


def test_falha_numa_pagina_tardia_para_a_coleta_e_entrega_o_que_ja_veio(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    httpx_mock.add_response(url=url_da_pagina(1), json=pagina_cheia(1))
    httpx_mock.add_response(
        url=url_da_pagina(2), status_code=429, json={"exception": "limite"}, is_reusable=True
    )

    with httpx.Client() as cliente_http:
        coletor = ColetorAdzuna(
            settings_de_teste(),
            cliente_http,
            ["Rio de Janeiro"],
            esperar=lambda _: None,
            termos=TERMOS_DE_BUSCA,
        )
        with pytest.raises(ColetaIncompleta, match="429") as capturada:
            coletor.coletar()

    assert len(capturada.value.vagas) == RESULTADOS_POR_PAGINA
    assert len(httpx_mock.get_requests()) == 1 + TENTATIVAS_POR_REQUISICAO
    assert "429" in caplog.text
    assert APP_KEY_DE_TESTE not in str(capturada.value)


def test_falha_de_rede_depois_de_uma_regiao_mantem_as_vagas_da_regiao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": [item(1), item(2)]})
    httpx_mock.add_exception(httpx.ReadTimeout("lento"), is_reusable=True)

    with httpx.Client() as cliente_http:
        coletor = ColetorAdzuna(
            settings_de_teste(),
            cliente_http,
            ["Rio de Janeiro", "Niterói"],
            esperar=lambda _: None,
            termos=TERMOS_DE_BUSCA,
        )
        with pytest.raises(ColetaIncompleta, match="ReadTimeout") as capturada:
            coletor.coletar()

    assert [vaga.id_externo for vaga in capturada.value.vagas] == ["1", "2"]
    assert len(httpx_mock.get_requests()) == 1 + TENTATIVAS_POR_REQUISICAO


def test_falha_antes_de_qualquer_vaga_continua_erro_de_coleta(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": []})
    httpx_mock.add_response(status_code=500, text="erro", is_reusable=True)

    with httpx.Client() as cliente_http:
        coletor = ColetorAdzuna(
            settings_de_teste(),
            cliente_http,
            ["Rio de Janeiro"],
            esperar=lambda _: None,
            termos=TERMOS_DE_BUSCA,
        )
        with pytest.raises(ErroDeColeta, match="500") as capturado:
            coletor.coletar()

    assert not isinstance(capturado.value, ColetaIncompleta)


@pytest.mark.parametrize(
    "resposta",
    [
        {"text": "<html>Service temporarily unavailable</html>"},
        {"json": {"exception": "AUTH_FAIL"}},
        {"json": {"results": {"id": 1}}},
        {"json": {"results": None}},
        {"json": [1, 2]},
    ],
    ids=["html", "sem_results", "results_dicionario", "results_nulo", "corpo_lista"],
)
def test_resposta_200_com_corpo_invalido_vira_erro_de_coleta(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna, resposta: dict
):
    httpx_mock.add_response(**resposta)

    with pytest.raises(ErroDeColeta, match="Adzuna") as capturado:
        coletor.coletar()

    assert APP_KEY_DE_TESTE not in str(capturado.value)


def test_corpo_invalido_numa_pagina_tardia_mantem_as_vagas_ja_coletadas(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna
):
    httpx_mock.add_response(url=url_da_pagina(1), json=pagina_cheia(1))
    httpx_mock.add_response(url=url_da_pagina(2), text="<html>erro</html>")

    with pytest.raises(ColetaIncompleta) as capturada:
        coletor.coletar()

    assert len(capturada.value.vagas) == RESULTADOS_POR_PAGINA


def test_coletas_sucessivas_nao_compartilham_estado(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json=resposta_gravada())
    httpx_mock.add_response(json={"results": []})

    primeira_coleta = coletor.coletar()
    segunda_coleta = coletor.coletar()

    assert len(primeira_coleta) == 3
    assert segunda_coleta == []


def test_erro_transitorio_e_tentado_de_novo_antes_de_desistir(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503, text="indisponível")
    httpx_mock.add_response(json=resposta_gravada())
    esperas: list[float] = []
    with httpx.Client() as cliente_http:
        coletor = ColetorAdzuna(
            settings_de_teste(), cliente_http, esperar=esperas.append, termos=TERMOS_DE_BUSCA
        )
        vagas = coletor.coletar()

    assert len(vagas) == 3
    assert esperas == [2]


def test_erro_de_autenticacao_nao_e_tentado_de_novo(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=401, text="não autorizado")
    esperas: list[float] = []
    with httpx.Client() as cliente_http:
        coletor = ColetorAdzuna(
            settings_de_teste(), cliente_http, esperar=esperas.append, termos=TERMOS_DE_BUSCA
        )
        with pytest.raises(ErroDeColeta, match="401"):
            coletor.coletar()

    assert esperas == []


class Relogio:
    def __init__(self) -> None:
        self.agora = 0.0
        self.esperas: list[float] = []

    def __call__(self) -> float:
        return self.agora

    def esperar(self, segundos: float) -> None:
        self.esperas.append(segundos)
        self.agora += segundos


def test_cota_segura_a_requisicao_que_passaria_do_limite_por_minuto():
    relogio = Relogio()
    cota = CotaDaAdzuna(relogio=relogio, esperar=relogio.esperar)

    for _ in range(LIMITE_POR_MINUTO + 1):
        cota.reservar()

    assert relogio.esperas == [60]
    assert cota.requisicoes == LIMITE_POR_MINUTO + 1


def test_cota_nao_espera_depois_que_o_minuto_passou():
    relogio = Relogio()
    cota = CotaDaAdzuna(relogio=relogio, esperar=relogio.esperar)
    for _ in range(LIMITE_POR_MINUTO):
        cota.reservar()

    relogio.agora += 61
    cota.reservar()

    assert relogio.esperas == []


def test_saldo_e_o_menor_entre_dia_semana_e_mes():
    assert saldo_da_adzuna(hoje=0, semana=0, mes=0) == 250
    assert saldo_da_adzuna(hoje=10, semana=900, mes=100) == 100
    assert saldo_da_adzuna(hoje=10, semana=10, mes=2450) == 50
    assert saldo_da_adzuna(hoje=300, semana=0, mes=0) == 0


def test_coleta_para_quando_o_saldo_acaba_e_devolve_o_que_ja_trouxe(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=url_da_pagina(1), json=pagina_cheia(1))
    cota = CotaDaAdzuna(saldo=1, esperar=lambda _: None)

    with httpx.Client() as cliente_http:
        vagas = ColetorAdzuna(
            settings_de_teste(),
            cliente_http,
            esperar=lambda _: None,
            termos=TERMOS_DE_BUSCA,
            cota=cota,
        ).coletar()

    assert len(vagas) == RESULTADOS_POR_PAGINA
    assert len(httpx_mock.get_requests()) == 1
    assert cota.esgotada


def test_cota_conta_tambem_as_novas_tentativas(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503, text="indisponível")
    httpx_mock.add_response(json={"results": []})
    cota = CotaDaAdzuna(esperar=lambda _: None)

    with httpx.Client() as cliente_http:
        ColetorAdzuna(
            settings_de_teste(),
            cliente_http,
            esperar=lambda _: None,
            termos=TERMOS_DE_BUSCA,
            cota=cota,
        ).coletar()

    assert cota.requisicoes == 2


def test_cota_zerada_antes_da_primeira_busca_vira_erro_de_coleta(httpx_mock: HTTPXMock):
    cota = CotaDaAdzuna(saldo=0, esperar=lambda _: None)

    with httpx.Client() as cliente_http, pytest.raises(ErroDeColeta, match="Cota da Adzuna"):
        ColetorAdzuna(
            settings_de_teste(),
            cliente_http,
            esperar=lambda _: None,
            termos=TERMOS_DE_BUSCA,
            cota=cota,
        ).coletar()

    assert httpx_mock.get_requests() == []
