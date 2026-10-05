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


def abertura(token: UUID = TOKEN) -> AberturaSemResposta:
    return AberturaSemResposta(token=token, titulo="Estágio Python", empresa="Empresa 9")


class RepositorioComAberturas(RepositorioFalso):
    def __init__(
        self,
        usuarios: list[Usuario],
        aberturas: dict[UUID, AberturaSemResposta],
        falha_ao_ler: Exception | None = None,
        falha_ao_registrar: Exception | None = None,
    ) -> None:
        super().__init__(usuarios)
        self._aberturas = aberturas
        self._falha_ao_ler = falha_ao_ler
        self._falha_ao_registrar = falha_ao_registrar
        self.consultas: list[tuple[UUID, date]] = []
        self.perguntas_registradas: list[tuple[UUID, UUID]] = []

    def abertura_sem_resposta(self, usuario: Usuario, hoje: date) -> AberturaSemResposta | None:
        self.consultas.append((usuario.id, hoje))
        if self._falha_ao_ler is not None:
            raise self._falha_ao_ler
        return self._aberturas.get(usuario.id)

    def registrar_pergunta_do_dia_seguinte(
        self, usuario: Usuario, abertura: AberturaSemResposta
    ) -> None:
        if self._falha_ao_registrar is not None:
            raise self._falha_ao_registrar
        self.perguntas_registradas.append((usuario.id, abertura.token))


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


def test_pergunta_sai_depois_da_mensagem_de_recomendacoes_sobre_a_abertura_de_ontem():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert len(notificador.textos) == 2
    assert "Radar de Estágio" in notificador.textos[0]
    assert notificador.textos[1] == "Ontem você abriu <b>Estágio Python — Empresa 9</b>. E aí?"
    assert notificador.chats == ["123", "123"]
    assert repositorio.consultas == [(ID_USUARIO, HOJE)]
    assert repositorio.perguntas_registradas == [(ID_USUARIO, TOKEN)]
    assert resumo.perguntas_do_dia_seguinte == 1
    assert resumo.perguntas_do_dia_seguinte_com_falha == 0


def test_pergunta_sai_mesmo_no_dia_sem_vaga_compativel():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador, vagas=[])

    assert "volta a procurar amanhã" in notificador.textos[0]
    assert notificador.textos[1].startswith("Ontem você abriu")
    assert resumo.perguntas_do_dia_seguinte == 1


def test_quem_nao_abriu_nada_ontem_nao_recebe_pergunta():
    repositorio = RepositorioComAberturas(
        [usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")], {ID_OUTRO_USUARIO: abertura()}
    )
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert notificador.chats == ["123", "456", "456"]
    assert notificador.textos[2].startswith("Ontem você abriu")
    assert resumo.perguntas_do_dia_seguinte == 1


def test_cada_pessoa_recebe_no_maximo_uma_pergunta_por_execucao():
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})
    notificador = NotificadorFalso()

    rodar(repositorio, notificador)

    assert repositorio.consultas == [(ID_USUARIO, HOJE)]
    assert len(repositorio.perguntas_registradas) == 1


def test_falha_do_telegram_na_pergunta_vira_aviso_e_nao_toca_a_entrega():
    class NotificadorQueFalhaNaPergunta(NotificadorFalso):
        def enviar_pergunta(self, chat_id, pergunta):
            if pergunta.texto.startswith("Ontem"):
                raise ErroDeNotificacao("Telegram respondeu HTTP 502: Bad Gateway")
            super().enviar_pergunta(chat_id, pergunta)

    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()})

    resumo = rodar(repositorio, NotificadorQueFalhaNaPergunta())

    assert resumo.perguntas_do_dia_seguinte == 0
    assert resumo.perguntas_do_dia_seguinte_com_falha == 1
    assert resumo.usuarios_com_mensagem == 1
    assert resumo.usuarios_sem_mensagem_por_falha == 0
    assert resumo.ninguem_foi_atendido_por_falha() is False
    assert repositorio.perguntas_registradas == []
    assert repositorio.pausados == []
    assert repositorio.falhas_por_usuario == {ID_USUARIO: 0}


@pytest.mark.parametrize(
    "erro", [ErroDeArmazenamento("banco caiu"), RuntimeError("inesperado")], ids=["banco", "erro"]
)
def test_falha_ao_ler_a_abertura_nao_derruba_a_execucao_nem_a_mensagem(erro: Exception):
    repositorio = RepositorioComAberturas([usuario()], {ID_USUARIO: abertura()}, falha_ao_ler=erro)
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
def test_pergunta_enviada_e_nao_gravada_conta_como_falha_sem_derrubar_ninguem(erro: Exception):
    repositorio = RepositorioComAberturas(
        [usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")],
        {ID_USUARIO: abertura(), ID_OUTRO_USUARIO: abertura(UUID(int=7))},
        falha_ao_registrar=erro,
    )
    notificador = NotificadorFalso()

    resumo = rodar(repositorio, notificador)

    assert notificador.chats.count("123") == 2
    assert notificador.chats.count("456") == 2
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

    assert repositorio.perguntas_registradas == [(ID_OUTRO_USUARIO, UUID(int=7))]
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
    assert repositorio.perguntas_registradas == [(ID_OUTRO_USUARIO, UUID(int=7))]
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
    assert repositorio.perguntas_registradas == []
    assert resumo.perguntas_do_dia_seguinte == 0
    assert resumo.perguntas_do_dia_seguinte_com_falha == 0


def test_repositorio_sem_banco_nunca_pergunta_nada():
    from radar.storage.memoria import RepositorioEmMemoria

    notificador = NotificadorFalso()

    resumo = rodar(RepositorioEmMemoria([usuario()]), notificador)

    assert len(notificador.textos) == 1
    assert resumo.perguntas_do_dia_seguinte == 0
