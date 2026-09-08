import re
from datetime import UTC, datetime
from uuid import UUID

import httpx
from pytest_httpx import HTTPXMock

from radar.collectors.adzuna import URL_BUSCA as URL_ADZUNA
from radar.collectors.factory import (
    areas_de_interesse,
    cidades_de_interesse,
    criar_coletor,
    termos_de_interesse,
)
from radar.collectors.gupy import URL_BUSCA as URL_GUPY
from radar.collectors.jooble import URL_BUSCA as URL_JOOBLE
from radar.domain.models import Modalidade, Perfil, Usuario
from radar.settings import Settings

AGORA = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)


def usuario(
    numero: int, cidade: str, modalidade: Modalidade, curso: str = "Ciência da Computação"
) -> Usuario:
    perfil = Perfil(
        curso=curso,
        periodo=3,
        habilidades=["Python"],
        cidade=cidade,
        modalidade=modalidade,
    )
    return Usuario(id=UUID(int=numero), perfil=perfil, chat_id=str(numero))


def settings_de_teste(fontes: str) -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="adzuna-id",
        adzuna_app_key="adzuna-chave",
        gemini_api_key="gemini-chave",
        telegram_bot_token="telegram-token",
        telegram_chat_id="123",
        fontes=fontes,
    )


def hosts_consultados(httpx_mock: HTTPXMock) -> set[str]:
    return {requisicao.url.host for requisicao in httpx_mock.get_requests()}


def test_consulta_somente_as_fontes_selecionadas(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=re.compile(re.escape(URL_ADZUNA)), json={"results": []})
    with httpx.Client() as cliente_http:
        criar_coletor(settings_de_teste("adzuna"), cliente_http, AGORA).coletar()

    assert hosts_consultados(httpx_mock) == {httpx.URL(URL_ADZUNA).host}


def test_jooble_selecionado_consulta_o_endpoint_do_jooble(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_JOOBLE)), json={"jobs": []}, is_reusable=True
    )
    settings = settings_de_teste("adzuna").model_copy(
        update={"fontes": "jooble", "jooble_api_key": "chave-jooble"}
    )
    with httpx.Client() as cliente_http:
        criar_coletor(settings, cliente_http, AGORA).coletar()

    assert hosts_consultados(httpx_mock) == {httpx.URL(URL_JOOBLE).host}


def test_consulta_todas_as_fontes_por_padrao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=re.compile(re.escape(URL_ADZUNA)), json={"results": []})
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_GUPY)), json={"data": []}, is_reusable=True
    )
    with httpx.Client() as cliente_http:
        criar_coletor(settings_de_teste("adzuna, gupy"), cliente_http, AGORA).coletar()

    assert hosts_consultados(httpx_mock) == {httpx.URL(URL_ADZUNA).host, httpx.URL(URL_GUPY).host}


def test_repassa_cidades_para_todas_as_fontes(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_ADZUNA)), json={"results": []}, is_reusable=True
    )
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_GUPY)), json={"data": []}, is_reusable=True
    )
    with httpx.Client() as cliente_http:
        criar_coletor(settings_de_teste("adzuna, gupy"), cliente_http, AGORA, ["Niterói"]).coletar()

    parametros = [requisicao.url.params for requisicao in httpx_mock.get_requests()]

    assert [p.get("where") for p in parametros if "app_id" in p] == [None, "Niterói"]
    assert [p.get("city") for p in parametros if "jobName" in p] == [None, "Niterói"]


def test_cidades_de_interesse_vem_de_perfis_presenciais_e_hibridos_sem_repetir():
    usuarios = [
        usuario(1, "Rio de Janeiro, RJ", Modalidade.PRESENCIAL),
        usuario(2, "rio de janeiro, RJ", Modalidade.HIBRIDO),
        usuario(3, "Niterói, RJ", Modalidade.PRESENCIAL),
        usuario(4, "São Paulo, SP", Modalidade.REMOTO),
        usuario(5, "Curitiba, PR", Modalidade.INDIFERENTE),
    ]

    assert cidades_de_interesse(usuarios) == ["Niterói", "Rio de Janeiro", "rio de janeiro"]


def test_cidades_de_interesse_sem_usuarios_e_vazia():
    assert cidades_de_interesse([]) == []


def test_areas_saem_dos_cursos_de_quem_esta_cadastrado():
    de_computacao = usuario(1, "Rio de Janeiro, RJ", Modalidade.REMOTO)
    de_direito = usuario(2, "Niterói, RJ", Modalidade.REMOTO, curso="Direito")

    assert areas_de_interesse([de_computacao]) == {"computacao"}
    assert areas_de_interesse([de_computacao, de_direito]) == {"computacao", "direito"}


def test_curso_sem_area_conhecida_nao_vira_termo_de_busca():
    exotico = usuario(1, "Rio de Janeiro, RJ", Modalidade.REMOTO, curso="Curso Inventado")

    assert areas_de_interesse([exotico]) == set()
    assert termos_de_interesse([exotico]) == ()


def test_termos_de_busca_acompanham_os_cursos_cadastrados():
    de_computacao = usuario(1, "Rio de Janeiro, RJ", Modalidade.REMOTO)
    de_direito = usuario(2, "Niterói, RJ", Modalidade.REMOTO, curso="Direito")

    somente_computacao = termos_de_interesse([de_computacao])

    assert "software" in somente_computacao
    assert "direito" not in somente_computacao

    com_direito = termos_de_interesse([de_computacao, de_direito])

    assert "software" in com_direito
    assert "direito" in com_direito


def test_curso_desconhecido_amplia_a_busca_em_grupo_misto(httpx_mock):
    conhecidos = usuario(1, "Rio", Modalidade.REMOTO)
    desconhecido = usuario(2, "Rio", Modalidade.REMOTO, curso="Agronomia")
    termos = termos_de_interesse(iter([conhecidos, desconhecido]))
    httpx_mock.add_response(url=re.compile(re.escape(URL_ADZUNA)), json={"results": []})
    with httpx.Client() as cliente:
        criar_coletor(settings_de_teste("adzuna"), cliente, AGORA, termos=termos).coletar()
    parametros = httpx_mock.get_request().url.params
    assert parametros["what_and"] == "estágio"
    assert "what_or" not in parametros


def test_busca_geral_jooble_nao_retorna_a_tecnologia(httpx_mock):
    import json

    httpx_mock.add_response(url=re.compile(re.escape(URL_JOOBLE)), json={"jobs": []})
    settings = settings_de_teste("adzuna").model_copy(
        update={"fontes": "jooble", "jooble_api_key": "teste"}
    )
    with httpx.Client() as cliente:
        criar_coletor(settings, cliente, AGORA, termos=()).coletar()
    assert json.loads(httpx_mock.get_request().content)["keywords"] == "estágio"
