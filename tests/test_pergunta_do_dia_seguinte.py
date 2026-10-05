from datetime import date
from uuid import UUID

import pytest

from radar.domain.models import AberturaSemResposta, Usuario
from radar.notification.telegram import ErroDeNotificacao
from radar.pipeline import executar
from radar.storage.errors import ErroDeArmazenamento
from tests.test_pipeline import (
    AGORA_DE_TESTE,
    ID_OUTRO_USUARIO,
    ID_USUARIO,
    ColetorFalso,
    ExtratorFalso,
    NotificadorFalso,
    PontuadorFalso,
    RepositorioFalso,
    parametros,
    usuario,
    vaga,
)

HOJE = date(2026, 8, 26)
TOKEN = UUID("15130004-9e8c-4247-aa2d-0514b82d078e")
TEXTO_DA_PERGUNTA = "Ontem você abriu"


def abertura(token: UUID = TOKEN) -> AberturaSemResposta:
    return AberturaSemResposta(token=token, titulo="Estágio Python", empresa="Empresa 9")


class RepositorioComAberturas(RepositorioFalso):
    def __init__(
        self,
        usuarios: list[Usuario],
        aberturas: dict[UUID, AberturaSemResposta],
        falha_ao_ler: Exception | None = None,
        falha_ao_reservar: Exception | None = None,
        falha_ao_liberar: Exception | None = None,
    ) -> None:
        super().__init__(usuarios)
        self._aberturas = aberturas
        self._falha_ao_ler = falha_ao_ler
        self.falha_ao_reservar = falha_ao_reservar
        self.falha_ao_liberar = falha_ao_liberar
        self.consultas: list[tuple[UUID, date]] = []
        self.marcas: set[UUID] = set()
        self.reservas: list[tuple[UUID, UUID]] = []
        self.liberacoes: list[tuple[UUID, UUID]] = []

    def abertura_sem_resposta(self, usuario: Usuario, hoje: date) -> AberturaSemResposta | None:
        self.consultas.append((usuario.id, hoje))
        if self._falha_ao_ler is not None:
            raise self._falha_ao_ler
        abertura = self._aberturas.get(usuario.id)
        return None if abertura is None or abertura.token in self.marcas else abertura

    def reservar_pergunta_do_dia_seguinte(
        self, usuario: Usuario, abertura: AberturaSemResposta
    ) -> bool:
        if self.falha_ao_reservar is not None:
            raise self.falha_ao_reservar
        if abertura.token in self.marcas:
            return False
        self.marcas.add(abertura.token)
        self.reservas.append((usuario.id, abertura.token))
        return True

    def liberar_pergunta_do_dia_seguinte(
        self, usuario: Usuario, abertura: AberturaSemResposta
    ) -> None:
        if self.falha_ao_liberar is not None:
            raise self.falha_ao_liberar
        self.marcas.discard(abertura.token)
        self.liberacoes.append((usuario.id, abertura.token))


class NotificadorQueFalhaNaPergunta(NotificadorFalso):
    def __init__(self, vezes: int = 1) -> None:
        super().__init__()
        self._vezes = vezes

    def enviar_pergunta(self, chat_id, pergunta):
        if pergunta.texto.startswith(TEXTO_DA_PERGUNTA) and self._vezes > 0:
            self._vezes -= 1
            raise ErroDeNotificacao("Telegram respondeu HTTP 502: Bad Gateway")
        super().enviar_pergunta(chat_id, pergunta)


def rodar(repositorio: RepositorioFalso, notificador: NotificadorFalso, vagas=None):
    vagas = [vaga(1)] if vagas is None else vagas
    return executar(
        ColetorFalso(vagas),
        ExtratorFalso({"1": 70}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 70}),
    )


def perguntas_enviadas(notificador: NotificadorFalso) -> list[str]:
    return [texto for texto in notificador.textos if texto.startswith(TEXTO_DA_PERGUNTA)]


def test_pergunta_sai_depois_da_mensagem_de_recomendacoes_sobre_a_abertura_de_ontem():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert len(notificador.textos) == 2
    assert "Radar de Estágio" in notificador.textos[0]
    assert notificador.textos[1] == "Ontem você abriu <b>Estágio Python — Empresa 9</b>. E aí?"
    assert notificador.chats == ["123", "123"]
    assert repositorio.consultas == [(ID_USUARIO, HOJE)]
    assert repositorio.reservas == [(ID_USUARIO, TOKEN)]
    assert repositorio.liberacoes == []
    assert resumo.perguntas_do_dia_seguinte == 1
    assert resumo.perguntas_do_dia_seguinte_com_falha == 0


def test_pergunta_sai_mesmo_no_dia_sem_vaga_compativel():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador, vagas=[])

    assert "volta a procurar amanhã" in notificador.textos[0]
    assert notificador.textos[1].startswith(TEXTO_DA_PERGUNTA)
    assert resumo.perguntas_do_dia_seguinte == 1


def test_quem_nao_abriu_nada_ontem_nao_recebe_pergunta():
    repositorio = RepositorioComAberturas(
        [usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")], {ID_OUTRO_USUARIO: abertura()}
    )
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert notificador.chats == ["123", "456", "456"]
    assert notificador.textos[2].startswith(TEXTO_DA_PERGUNTA)
    assert resumo.perguntas_do_dia_seguinte == 1


def test_cada_pessoa_recebe_no_maximo_uma_pergunta_por_execucao():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    rodar(repositorio, notificador)

    assert repositorio.consultas == [(ID_USUARIO, HOJE)]
    assert len(repositorio.reservas) == 1


def test_a_pergunta_nao_se_repete_na_segunda_execucao_do_mesmo_dia():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    rodar(repositorio, notificador)
    rodar(repositorio, notificador)

    assert len(perguntas_enviadas(notificador)) == 1


def test_a_vaga_e_reservada_antes_do_envio_e_nao_depois():
    ordem: list[str] = []

    class Repositorio(RepositorioComAberturas):
        def reservar_pergunta_do_dia_seguinte(self, usuario, abertura):
            ordem.append("reservar")
            return super().reservar_pergunta_do_dia_seguinte(usuario, abertura)

    class Notificador(NotificadorFalso):
        def enviar_pergunta(self, chat_id, pergunta):
            if pergunta.texto.startswith(TEXTO_DA_PERGUNTA):
                ordem.append("enviar")
            super().enviar_pergunta(chat_id, pergunta)

    rodar(Repositorio([usuario()], {ID_USUARIO: abertura()}), Notificador())

    assert ordem == ["reservar", "enviar"]


def test_falha_do_telegram_na_pergunta_libera_a_reserva_e_a_proxima_execucao_tenta_de_novo():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorQueFalhaNaPergunta(vezes=1)

    primeira = rodar(repositorio, notificador)

    assert primeira.perguntas_do_dia_seguinte == 0
    assert primeira.perguntas_do_dia_seguinte_com_falha == 1
    assert primeira.usuarios_com_mensagem == 1
    assert primeira.usuarios_sem_mensagem_por_falha == 0
    assert primeira.ninguem_foi_atendido_por_falha() is False
    assert repositorio.liberacoes == [(ID_USUARIO, TOKEN)]
    assert repositorio.marcas == set()
    assert repositorio.pausados == []
    assert repositorio.falhas_por_usuario == {ID_USUARIO: 0}

    segunda = rodar(repositorio, notificador)

    assert segunda.perguntas_do_dia_seguinte == 1
    assert len(perguntas_enviadas(notificador)) == 1


def test_falha_na_reserva_nao_envia_a_pergunta_e_so_conta_como_falha():
    repositorio = RepositorioComAberturas(
        [usuario()], {ID_USUARIO: abertura()}, falha_ao_reservar=ErroDeArmazenamento("banco caiu")
    )
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert perguntas_enviadas(notificador) == []
    assert resumo.perguntas_do_dia_seguinte_com_falha == 1
    assert resumo.usuarios_com_mensagem == 1

    repositorio.falha_ao_reservar = None
    rodar(repositorio, notificador)

    assert len(perguntas_enviadas(notificador)) == 1


def test_envio_que_falha_com_a_liberacao_tambem_falhando_nao_repete_a_pergunta_depois():
    repositorio = RepositorioComAberturas(
        [usuario()], {ID_USUARIO: abertura()}, falha_ao_liberar=ErroDeArmazenamento("banco caiu")
    )
    notificador = NotificadorQueFalhaNaPergunta(vezes=1)

    primeira = rodar(repositorio, notificador)
    repositorio.falha_ao_liberar = None
    rodar(repositorio, notificador)

    assert primeira.perguntas_do_dia_seguinte_com_falha == 1
    assert repositorio.marcas == {TOKEN}
    assert perguntas_enviadas(notificador) == []


def test_em_nenhum_caminho_de_falha_a_mesma_pergunta_chega_duas_vezes():
    cenarios = [
        {"falha_ao_reservar": ErroDeArmazenamento("banco caiu")},
        {"falha_ao_liberar": ErroDeArmazenamento("banco caiu")},
        {},
    ]
    for opcoes in cenarios:
        repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()}, **opcoes)
        notificador = NotificadorQueFalhaNaPergunta(vezes=1)

        for _ in range(3):
            rodar(repositorio, notificador)
            repositorio.falha_ao_reservar = None
            repositorio.falha_ao_liberar = None

        assert len(perguntas_enviadas(notificador)) <= 1, opcoes


@pytest.mark.parametrize(
    "erro", [ErroDeArmazenamento("banco caiu"), RuntimeError("inesperado")], ids=["banco", "erro"]
)
def test_falha_ao_ler_a_abertura_nao_derruba_a_execucao_nem_a_mensagem(erro: Exception):
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    repositorio._falha_ao_ler = erro
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert len(notificador.textos) == 1
    assert resumo.usuarios_com_mensagem == 1
    assert resumo.perguntas_do_dia_seguinte == 0
    assert resumo.perguntas_do_dia_seguinte_com_falha == 1
    assert resumo.ninguem_foi_atendido_por_falha() is False


@pytest.mark.parametrize(
    "erro", [ErroDeArmazenamento("banco caiu"), RuntimeError("inesperado")], ids=["banco", "erro"]
)
def test_falha_ao_reservar_para_dois_usuarios_conta_duas_falhas_sem_derrubar_ninguem(
    erro: Exception,
):
    repositorio = RepositorioComAberturas(
        [usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")],
        {ID_USUARIO: abertura(), ID_OUTRO_USUARIO: abertura(UUID(int=7))},
        falha_ao_reservar=erro,
    )
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert notificador.chats.count("123") == 1
    assert notificador.chats.count("456") == 1
    assert resumo.perguntas_do_dia_seguinte_com_falha == 2
    assert resumo.usuarios_com_mensagem == 2


def test_um_usuario_com_falha_na_pergunta_nao_impede_a_pergunta_dos_outros():
    class RepositorioQueFalhaParaUm(RepositorioComAberturas):
        def abertura_sem_resposta(self, usuario, hoje):
            if usuario.id == ID_USUARIO:
                raise ErroDeArmazenamento("banco caiu")
            return super().abertura_sem_resposta(usuario, hoje)

    repositorio = RepositorioQueFalhaParaUm(
        [usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")],
        {ID_USUARIO: abertura(), ID_OUTRO_USUARIO: abertura(UUID(int=7))},
    )

    resumo = rodar(repositorio, NotificadorFalso())

    assert repositorio.reservas == [(ID_OUTRO_USUARIO, UUID(int=7))]
    assert resumo.perguntas_do_dia_seguinte == 1
    assert resumo.perguntas_do_dia_seguinte_com_falha == 1


def test_quem_ficou_sem_a_mensagem_por_falha_do_telegram_nao_recebe_pergunta():
    repositorio = RepositorioComAberturas(
        [usuario(chat_id="bloqueado"), usuario(ID_OUTRO_USUARIO, chat_id="456")],
        {ID_USUARIO: abertura(), ID_OUTRO_USUARIO: abertura(UUID(int=7))},
    )
    notificador = NotificadorFalso(chats_com_falha_temporaria={"bloqueado"})

    resumo = rodar(repositorio, notificador)

    assert "bloqueado" not in notificador.chats
    assert repositorio.reservas == [(ID_OUTRO_USUARIO, UUID(int=7))]
    assert resumo.perguntas_do_dia_seguinte_com_falha == 0


def test_conta_que_deixou_de_poder_receber_durante_a_execucao_nao_recebe_pergunta():
    class RepositorioQueDesvinculaNaPergunta(RepositorioComAberturas):
        def abertura_sem_resposta(self, usuario, hoje):
            self._usuarios = []
            return super().abertura_sem_resposta(usuario, hoje)

    repositorio = RepositorioQueDesvinculaNaPergunta([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert len(notificador.textos) == 1
    assert repositorio.reservas == []
    assert resumo.perguntas_do_dia_seguinte == 0
    assert resumo.perguntas_do_dia_seguinte_com_falha == 0


def test_repositorio_sem_banco_nunca_pergunta_nada():
    from radar.storage.memoria import RepositorioEmMemoria

    notificador = NotificadorFalso()

    resumo = rodar(RepositorioEmMemoria([usuario()]), notificador)

    assert len(notificador.textos) == 1
    assert resumo.perguntas_do_dia_seguinte == 0
