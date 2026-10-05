import json
from datetime import date
from uuid import UUID

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.domain.models import AberturaSemResposta, Usuario
from radar.storage.memoria import RepositorioEmMemoria
from tests.test_fluxo import (
    CHAT_DE_OPERACAO,
    CHAT_DO_ESTUDANTE,
    URL_DO_TELEGRAM,
    aceitar_mensagens_do_telegram,
    codigo_de_saida_do_rodar,
    estudante_de_direito_no_rio,
    mensagens_para,
    responder_com_vagas_de_ti,
)

TOKEN = UUID(int=99)


class BancoComAberturaDeOntem(RepositorioEmMemoria):
    def abertura_sem_resposta(self, usuario: Usuario, hoje: date) -> AberturaSemResposta | None:
        return AberturaSemResposta(
            token=TOKEN, titulo="Estágio em Direito", empresa="Escritório Exemplo"
        )


def corpos_enviados_ao(httpx_mock: HTTPXMock, chat_id: str) -> list[dict]:
    corpos = [
        json.loads(requisicao.content)
        for requisicao in httpx_mock.get_requests(url=URL_DO_TELEGRAM)
    ]
    return [corpo for corpo in corpos if corpo["chat_id"] == chat_id]


def test_pergunta_do_dia_seguinte_chega_com_tres_botoes_e_o_resumo_a_conta(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_com_vagas_de_ti(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = BancoComAberturaDeOntem([estudante_de_direito_no_rio()])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    do_estudante = corpos_enviados_ao(httpx_mock, CHAT_DO_ESTUDANTE)
    assert "Nenhuma vaga nova compatível" in do_estudante[0]["text"]
    pergunta = do_estudante[1]
    assert pergunta["text"] == (
        "Ontem você abriu <b>Estágio em Direito — Escritório Exemplo</b>. E aí?"
    )
    botoes = [
        botao["callback_data"]
        for linha in pergunta["reply_markup"]["inline_keyboard"]
        for botao in linha
    ]
    assert botoes == [f"{acao}:{TOKEN}" for acao in ("candidatei", "nao_serviu", "ainda_vou_ver")]
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "Perguntas do dia seguinte enviadas: 1" in resumo


def test_pergunta_do_dia_seguinte_que_falha_so_avisa_e_a_execucao_segue_verde(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    def telegram(requisicao: httpx.Request) -> httpx.Response:
        if json.loads(requisicao.content)["text"].startswith("Ontem você abriu"):
            return httpx.Response(500, text="Bad Gateway")
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    responder_com_vagas_de_ti(httpx_mock)
    httpx_mock.add_callback(telegram, url=URL_DO_TELEGRAM, is_reusable=True)
    repositorio = BancoComAberturaDeOntem([estudante_de_direito_no_rio()])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "Perguntas do dia seguinte enviadas: 0" in resumo
    assert "⚠️ Perguntas do dia seguinte com falha: 1" in resumo
    assert "Usuários sem mensagem por falha" not in resumo
