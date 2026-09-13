import json
import re
from datetime import date
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.__main__ import executar_fluxo
from radar.collectors.adzuna import RESULTADOS_POR_PAGINA, URL_BUSCA
from radar.collectors.errors import ErroDeColeta
from radar.domain.models import Usuario, Vaga
from radar.domain.ports import ColetorDeVagas
from radar.pipeline import ResumoDaExecucao, executar
from radar.settings import Settings
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria

CAMINHO_DO_FIXTURE = Path(__file__).parent / "fixtures" / "adzuna_resposta.json"
URL_DO_TELEGRAM = re.compile(r"https://api\.telegram\.org/.*")
CHAT_DE_OPERACAO = "999"


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key="app-key-de-teste",
        gemini_api_key="gemini-de-teste",
        telegram_bot_token="token-de-teste",
        telegram_chat_id=CHAT_DE_OPERACAO,
        dias_recentes=3,
    )


def url_da_pagina(pagina: int) -> re.Pattern[str]:
    return re.compile(re.escape(f"{URL_BUSCA}/{pagina}?"))


def pagina_cheia() -> dict:
    modelo = json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8"))["results"][0]
    return {"results": [{**modelo, "id": numero} for numero in range(1, RESULTADOS_POR_PAGINA + 1)]}


def aceitar_mensagens_do_telegram(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=URL_DO_TELEGRAM, json={"ok": True, "result": {"message_id": 1}}, is_reusable=True
    )


def mensagens_de_operacao(httpx_mock: HTTPXMock) -> list[str]:
    return [
        json.loads(requisicao.content)["text"]
        for requisicao in httpx_mock.get_requests(url=URL_DO_TELEGRAM)
    ]


def test_resumo_de_operacao_avisa_que_a_coleta_da_adzuna_parou_no_meio(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=url_da_pagina(1), json=pagina_cheia())
    httpx_mock.add_response(url=url_da_pagina(2), status_code=400, text="pedido inválido")
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, RepositorioEmMemoria([]))

    resumo = mensagens_de_operacao(httpx_mock)[-1]
    assert f"Vagas coletadas: {RESULTADOS_POR_PAGINA}" in resumo
    assert "⚠️ Coleta da Adzuna incompleta: Adzuna respondeu HTTP 400 ao buscar vagas" in resumo


class ColetorFixo:
    def __init__(self, vagas: list[Vaga]) -> None:
        self._vagas = vagas

    def coletar(self) -> list[Vaga]:
        return self._vagas


def uso_gravado(repositorio: RepositorioEmMemoria) -> int:
    return repositorio.requisicoes_da_fonte_desde("adzuna", date.min)


def test_uso_da_adzuna_fica_gravado_logo_depois_da_coleta_e_uma_vez_so(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    repositorio = RepositorioEmMemoria([])
    uso_ao_fim_da_coleta: list[int] = []

    def executar_observando_a_coleta(
        coletor: ColetorDeVagas, *argumentos, **nomeados
    ) -> ResumoDaExecucao:
        coletadas = coletor.coletar()
        uso_ao_fim_da_coleta.append(uso_gravado(repositorio))
        return executar(ColetorFixo(coletadas), *argumentos, **nomeados)

    monkeypatch.setattr("radar.__main__.executar", executar_observando_a_coleta)
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)

    assert uso_ao_fim_da_coleta == [1]
    assert uso_gravado(repositorio) == 1
    assert "Requisições à Adzuna: 1 hoje" in mensagens_de_operacao(httpx_mock)[-1]


def test_coleta_que_falha_grava_o_uso_e_avisa_a_operacao(httpx_mock: HTTPXMock):
    repositorio = RepositorioEmMemoria([])
    httpx_mock.add_response(url=url_da_pagina(1), status_code=401, text="não autorizado")
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http, pytest.raises(ErroDeColeta):
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)

    assert uso_gravado(repositorio) == 1
    assert "falhou" in mensagens_de_operacao(httpx_mock)[-1]


class BancoForaDoAr(RepositorioEmMemoria):
    def listar_ativos(self) -> list[Usuario]:
        raise ErroDeArmazenamento("Falha ao ler os perfis: connection reset")


def test_falha_ao_ler_os_usuarios_avisa_a_operacao(httpx_mock: HTTPXMock):
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http, pytest.raises(ErroDeArmazenamento):
        executar_fluxo(settings_de_teste(), cliente_http, BancoForaDoAr([]))

    [aviso] = mensagens_de_operacao(httpx_mock)
    assert "falhou" in aviso
    assert "connection reset" in aviso


def test_perfil_sem_entrega_a_fazer_retorna_sem_coletar_nem_avisar(httpx_mock: HTTPXMock):
    with httpx.Client() as cliente_http:
        executar_fluxo(
            settings_de_teste(),
            cliente_http,
            RepositorioEmMemoria([]),
            apenas_o_perfil=UUID(int=7),
        )

    assert httpx_mock.get_requests() == []
