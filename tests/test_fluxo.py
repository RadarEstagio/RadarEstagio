import json
import re
from pathlib import Path

import httpx
from pytest_httpx import HTTPXMock

from radar.__main__ import executar_fluxo
from radar.collectors.adzuna import RESULTADOS_POR_PAGINA, URL_BUSCA
from radar.settings import Settings
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
