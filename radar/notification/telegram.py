import httpx

from radar.domain.models import BotaoDeFeedback, PerguntaDeFeedback
from radar.notification.formatador import dividir_em_mensagens

URL_BASE_DA_API = "https://api.telegram.org"
HTTP_PEDIDO_INVALIDO = 400
HTTP_PROIBIDO = 403
LIMITE_DA_DESCRICAO_DO_ERRO = 200
MOTIVOS_DE_RECUSA_DO_DESTINATARIO = (
    "chat not found",
    "bot was blocked",
    "user is deactivated",
    "bot can't initiate conversation",
    "peer_id_invalid",
    "chat_write_forbidden",
)


class ErroDeNotificacao(Exception):
    pass


class DestinatarioRecusouAMensagem(ErroDeNotificacao):
    pass


class NotificadorTelegram:
    def __init__(self, token_do_bot: str, cliente_http: httpx.Client) -> None:
        self._url_envio = f"{URL_BASE_DA_API}/bot{token_do_bot}/sendMessage"
        self._cliente_http = cliente_http

    def enviar(self, chat_id: str, texto: str) -> None:
        for mensagem in dividir_em_mensagens(texto):
            self._enviar_mensagem(chat_id, mensagem)

    def enviar_pergunta(self, chat_id: str, pergunta: PerguntaDeFeedback) -> None:
        partes = dividir_em_mensagens(pergunta.texto)
        for indice, parte in enumerate(partes):
            corpo = {
                "chat_id": chat_id,
                "text": parte,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            if indice == len(partes) - 1:
                corpo["reply_markup"] = {"inline_keyboard": teclado(pergunta.linhas_de_botoes)}
            self._postar(corpo)

    def _enviar_mensagem(self, chat_id: str, mensagem: str) -> None:
        self._postar(
            {
                "chat_id": chat_id,
                "text": mensagem,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
        )

    def _postar(self, corpo: dict) -> None:
        try:
            resposta = self._cliente_http.post(self._url_envio, json=corpo)
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            status = erro.response.status_code
            descricao = descricao_do_erro(erro.response)
            mensagem = f"Telegram respondeu HTTP {status}: {descricao}"
            if destinatario_recusou(status, descricao):
                raise DestinatarioRecusouAMensagem(mensagem) from None
            raise ErroDeNotificacao(mensagem) from None
        except httpx.HTTPError as erro:
            raise ErroDeNotificacao(
                f"Falha de rede ao enviar mensagem no Telegram ({type(erro).__name__})"
            ) from erro


def descricao_do_erro(resposta: httpx.Response) -> str:
    try:
        return str(resposta.json().get("description", ""))
    except ValueError:
        return resposta.text[:LIMITE_DA_DESCRICAO_DO_ERRO].strip()


def destinatario_recusou(status: int, descricao: str) -> bool:
    if status == HTTP_PROIBIDO:
        return True
    if status != HTTP_PEDIDO_INVALIDO:
        return False
    return any(motivo in descricao.casefold() for motivo in MOTIVOS_DE_RECUSA_DO_DESTINATARIO)


def teclado(linhas: list[list[BotaoDeFeedback]]) -> list[list[dict]]:
    return [
        [{"text": botao.rotulo, "callback_data": botao.dados} for botao in linha]
        for linha in linhas
    ]
