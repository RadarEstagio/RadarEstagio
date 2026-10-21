from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import pytest

from radar.domain.models import Usuario
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
    rodar_com_vaga_que_nunca_e_extraida,
    usuario,
    vaga,
)

DIA_DE_TESTE = date(2026, 8, 26)


def diario(repositorio, notificador, agora=AGORA_DE_TESTE, notas=None, apenas_o_perfil=None):
    notas = notas or {"1": 90, "2": 80}
    return executar(
        ColetorFalso([vaga(int(numero)) for numero in notas]),
        ExtratorFalso(notas),
        notificador,
        repositorio,
        parametros(nota_minima=40),
        agora,
        PontuadorFalso(notas),
        apenas_o_perfil=apenas_o_perfil,
    )


def test_segundo_diario_no_mesmo_dia_nao_manda_outra_mensagem_a_quem_ja_recebeu():
    repositorio = RepositorioFalso([usuario(), usuario(ID_OUTRO_USUARIO, "456")])
    notificador = NotificadorFalso()

    diario(repositorio, notificador)
    segundo = diario(repositorio, notificador, AGORA_DE_TESTE + timedelta(minutes=15))

    assert notificador.chats == ["123", "456"]
    assert segundo.enviadas_por_usuario == {}
    assert segundo.usuarios_ja_atendidos_hoje == 2
    assert not segundo.ninguem_foi_atendido_por_falha()


def test_quem_recebeu_o_nada_compativel_tambem_conta_como_atendido_no_dia():
    repositorio = RepositorioFalso([usuario()])
    notificador = NotificadorFalso()

    diario(repositorio, notificador, notas={"1": 10})
    diario(repositorio, notificador, AGORA_DE_TESTE + timedelta(minutes=15))

    assert notificador.chats == ["123"]
    assert repositorio.atendido_no_dia(usuario(), DIA_DE_TESTE)


def test_quem_ficou_sem_mensagem_por_falha_do_telegram_e_atendido_no_segundo_diario():
    repositorio = RepositorioFalso([usuario(), usuario(ID_OUTRO_USUARIO, "456")])
    primeiro = NotificadorFalso(chats_com_falha_temporaria={"456"})
    segundo = NotificadorFalso()

    diario(repositorio, primeiro)
    resumo = diario(repositorio, segundo, AGORA_DE_TESTE + timedelta(minutes=15))

    assert primeiro.chats == ["123"]
    assert segundo.chats == ["456"]
    assert resumo.usuarios_ja_atendidos_hoje == 1


def test_mensagem_segurada_por_falta_de_extracao_nao_marca_o_dia():
    repositorio = RepositorioFalso([usuario(dias_sem_recomendacao=1)])
    notificador = NotificadorFalso()

    resumo = rodar_com_vaga_que_nunca_e_extraida(repositorio, notificador, AGORA_DE_TESTE)

    assert notificador.chats == []
    assert resumo.mensagens_seguradas_por_falta_de_extracao == 1
    assert not repositorio.atendido_no_dia(usuario(), DIA_DE_TESTE)


def test_diario_do_dia_seguinte_atende_de_novo():
    repositorio = RepositorioFalso([usuario()])
    notificador = NotificadorFalso()

    diario(repositorio, notificador)
    diario(repositorio, notificador, AGORA_DE_TESTE + timedelta(days=1))

    assert notificador.chats == ["123", "123"]


@pytest.mark.parametrize(
    ("primeiro", "segundo", "mensagens"),
    [
        (
            datetime(2026, 8, 27, 2, 30, tzinfo=UTC),
            datetime(2026, 8, 27, 10, 23, tzinfo=UTC),
            2,
        ),
        (
            datetime(2026, 8, 26, 10, 23, tzinfo=UTC),
            datetime(2026, 8, 27, 1, 0, tzinfo=UTC),
            1,
        ),
    ],
    ids=["23h30-de-brasilia-e-outro-dia", "22h-de-brasilia-e-o-mesmo-dia"],
)
def test_a_virada_do_dia_do_atendimento_e_a_de_brasilia(primeiro, segundo, mensagens):
    repositorio = RepositorioFalso([usuario()])
    notificador = NotificadorFalso()

    diario(repositorio, notificador, primeiro)
    diario(repositorio, notificador, segundo)

    assert len(notificador.chats) == mensagens


def test_entrega_imediata_marca_o_dia_e_o_diario_do_mesmo_dia_nao_repete():
    repositorio = RepositorioFalso([usuario()])
    notificador = NotificadorFalso()

    diario(
        repositorio, notificador, AGORA_DE_TESTE - timedelta(hours=5), apenas_o_perfil=ID_USUARIO
    )
    diario(repositorio, notificador)

    assert notificador.chats == ["123"]


class RepositorioQueNaoMarcaODia(RepositorioFalso):
    def marcar_atendidos_no_dia(self, perfis: list[UUID], dia: date) -> None:
        raise ErroDeArmazenamento("banco caiu")


def test_falha_ao_marcar_o_dia_vira_aviso_e_nao_para_os_demais(caplog: pytest.LogCaptureFixture):
    repositorio = RepositorioQueNaoMarcaODia([usuario(), usuario(ID_OUTRO_USUARIO, "456")])
    notificador = NotificadorFalso()

    resumo = diario(repositorio, notificador)

    assert notificador.chats == ["123", "456"]
    assert set(resumo.enviadas_por_usuario) == {ID_USUARIO, ID_OUTRO_USUARIO}
    assert "o dia do atendimento não foi marcado" in caplog.text


class RepositorioAtendidoPorOutraExecucao(RepositorioFalso):
    def atendido_no_dia(self, usuario: Usuario, dia: date) -> bool:
        return True


def test_dia_do_atendimento_e_relido_depois_de_travar_o_perfil():
    repositorio = RepositorioAtendidoPorOutraExecucao([usuario()])
    notificador = NotificadorFalso()

    resumo = diario(repositorio, notificador)

    assert notificador.chats == []
    assert resumo.usuarios_ja_atendidos_hoje == 1
    assert repositorio.travas == [("travar", ID_USUARIO), ("liberar", ID_USUARIO)]


class RepositorioQueMarcaNaOrdem(RepositorioFalso):
    def marcar_entregas_imediatas_atendidas(self, perfis: list[UUID]) -> None:
        self.travas.extend(("atendido", perfil) for perfil in perfis)

    def marcar_atendidos_no_dia(self, perfis: list[UUID], dia: date) -> None:
        self.travas.extend((f"dia {dia:%d/%m}", perfil) for perfil in perfis)


def test_dia_do_atendimento_e_marcado_antes_de_liberar_a_trava_do_perfil():
    repositorio = RepositorioQueMarcaNaOrdem([usuario()])

    diario(repositorio, NotificadorFalso())

    assert repositorio.travas == [
        ("travar", ID_USUARIO),
        ("atendido", ID_USUARIO),
        ("dia 26/08", ID_USUARIO),
        ("liberar", ID_USUARIO),
    ]
