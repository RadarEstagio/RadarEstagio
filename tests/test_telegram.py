import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.notification.formatador import LIMITE_DE_CARACTERES_DO_TELEGRAM
from radar.notification.telegram import ErroDeNotificacao, NotificadorTelegram

TOKEN_DE_TESTE = "token-de-teste"
CHAT_ID_DE_TESTE = "123"


@pytest.fixture
def notificador():
    with httpx.Client() as cliente_http:
        yield NotificadorTelegram(TOKEN_DE_TESTE, cliente_http)


def test_envia_mensagem_para_o_chat_com_html(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True})

    notificador.enviar(CHAT_ID_DE_TESTE, "<b>Radar OK</b>")

    requisicao = httpx_mock.get_request()
    assert requisicao.method == "POST"
    assert str(requisicao.url) == f"https://api.telegram.org/bot{TOKEN_DE_TESTE}/sendMessage"
    corpo = json.loads(requisicao.content)
    assert corpo == {
        "chat_id": CHAT_ID_DE_TESTE,
        "text": "<b>Radar OK</b>",
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }


def test_texto_acima_do_limite_vira_varias_requisicoes(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True}, is_reusable=True)
    texto = "\n\n───────────────\n\n".join("bloco " + "x" * 1000 for _ in range(6))

    notificador.enviar(CHAT_ID_DE_TESTE, texto)

    requisicoes = httpx_mock.get_requests()
    assert len(requisicoes) > 1
    textos = [json.loads(requisicao.content)["text"] for requisicao in requisicoes]
    assert all(len(parte) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for parte in textos)
    assert "\n\n───────────────\n\n".join(textos) == texto


def test_erro_http_levanta_erro_de_notificacao_com_descricao(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(
        status_code=400, json={"ok": False, "description": "Bad Request: chat not found"}
    )

    with pytest.raises(ErroDeNotificacao, match="400.*chat not found"):
        notificador.enviar(CHAT_ID_DE_TESTE, "Radar OK")


def test_falha_de_rede_levanta_erro_de_notificacao(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_exception(httpx.ConnectError("sem conexão"))

    with pytest.raises(ErroDeNotificacao, match="ConnectError"):
        notificador.enviar(CHAT_ID_DE_TESTE, "Radar OK")


def test_feedback_fica_na_ultima_parte_sem_mensagem_extra(httpx_mock, notificador):
    from radar.domain.models import BotaoDeFeedback, PerguntaDeFeedback

    httpx_mock.add_response(json={"ok": True}, is_reusable=True)
    texto = "\n\n───────────────\n\n".join("vaga " + "x" * 1000 for _ in range(6))
    texto += "\n\nDeixe seu feedback 👇"
    notificador.enviar_pergunta(
        CHAT_ID_DE_TESTE,
        PerguntaDeFeedback(
            texto=texto,
            linhas_de_botoes=[[BotaoDeFeedback(rotulo="1", dados="feedback:token")]],
        ),
    )
    corpos = [json.loads(r.content) for r in httpx_mock.get_requests()]
    assert len(corpos) == 2
    assert all(len(c["text"]) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for c in corpos)
    assert all(c["parse_mode"] == "HTML" for c in corpos)
    assert "reply_markup" not in corpos[0]
    assert corpos[-1]["text"].endswith("Deixe seu feedback 👇")
    assert corpos[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "feedback:token"


def test_erro_sem_corpo_json_vira_erro_de_notificacao_e_nao_derruba_a_execucao(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(status_code=502, text="<html>Bad Gateway</html>")

    with pytest.raises(ErroDeNotificacao, match="502.*Bad Gateway"):
        notificador.enviar(CHAT_ID_DE_TESTE, "Radar OK")
