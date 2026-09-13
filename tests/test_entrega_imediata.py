from uuid import UUID

import httpx
import pytest

import radar.__main__ as cli
from radar.collectors.adzuna import CotaDaAdzuna
from radar.cota import reserva_do_diario
from radar.domain.models import Perfil, Usuario
from radar.domain.perfil_fixo import perfil_de_exemplo
from radar.entrega_imediata import RepositorioDosAtendidos, usuarios_a_atender
from radar.settings import Settings
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria


def usuario(numero: int, cidade: str) -> Usuario:
    perfil = Perfil(**{**perfil_de_exemplo().model_dump(), "cidade": cidade})
    return Usuario(id=UUID(int=numero), perfil=perfil, chat_id=str(numero))


VINCULADO = usuario(1, "Recife, PE")
PENDENTE = usuario(2, "Niterói, RJ")
ANTIGO = usuario(3, "Belo Horizonte, MG")
NOVO = usuario(4, "Recife, PE")
TODOS = [VINCULADO, PENDENTE, ANTIGO, NOVO]


class RepositorioComMarcas(RepositorioEmMemoria):
    def __init__(
        self,
        usuarios: list[Usuario],
        pendentes: list[UUID] | None = None,
        atendidos: list[UUID] | None = None,
    ) -> None:
        super().__init__(usuarios)
        self.pendentes = set(pendentes or [])
        self.atendidos = set(atendidos or [])

    def reivindicar_entregas_imediatas(self, perfil_id: UUID) -> set[UUID]:
        ativos = {usuario.id for usuario in self.listar_ativos()}
        reivindicados = ({perfil_id} | self.pendentes) & ativos - self.atendidos
        self.atendidos |= reivindicados
        return reivindicados

    def marcar_entregas_imediatas_atendidas(self, perfis: list[UUID]) -> None:
        self.atendidos |= set(perfis)


class RepositorioQueNaoMarca(RepositorioComMarcas):
    def marcar_entregas_imediatas_atendidas(self, perfis: list[UUID]) -> None:
        raise ErroDeArmazenamento("banco fora do ar")


class ExecucaoInterrompida(Exception):
    pass


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="adzuna-id",
        adzuna_app_key="adzuna-chave",
        avaliador="agy",
        telegram_bot_token="telegram-token",
        telegram_chat_id="123",
    )


def cliente_sem_rede() -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(lambda requisicao: httpx.Response(500)))


def interceptar_execucao(monkeypatch: pytest.MonkeyPatch) -> dict:
    capturado: dict = {}

    def montar_coletor(settings, cliente_http, usuarios, cota):
        capturado["coleta"] = usuarios
        return object()

    def abrir_cota(repositorio, agora, reserva=0):
        capturado["reserva"] = reserva
        return CotaDaAdzuna()

    def executar(coletor, extrator, notificador, repositorio, parametros, agora, **opcoes):
        capturado["atendidos"] = repositorio.listar_ativos()
        capturado["apenas_o_perfil"] = opcoes.get("apenas_o_perfil")
        raise ExecucaoInterrompida

    monkeypatch.setattr(cli, "montar_extrator", lambda settings: object())
    monkeypatch.setattr(cli, "montar_coletor", montar_coletor)
    monkeypatch.setattr(cli, "abrir_cota_da_adzuna", abrir_cota)
    monkeypatch.setattr(cli, "executar", executar)
    return capturado


def test_entrega_imediata_atende_o_perfil_e_quem_ficou_pendente():
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id, NOVO.id]
    )

    assert usuarios_a_atender(repositorio, TODOS, VINCULADO.id) == [VINCULADO, PENDENTE]
    assert usuarios_a_atender(repositorio, TODOS, PENDENTE.id) == []


def test_disparo_recusado_deixa_o_perfil_para_a_proxima_execucao():
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[PENDENTE.id], atendidos=[VINCULADO.id, ANTIGO.id]
    )

    assert usuarios_a_atender(repositorio, TODOS, NOVO.id) == [PENDENTE, NOVO]


def test_perfil_vinculado_depois_da_primeira_leitura_ainda_e_atendido():
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[NOVO.id], atendidos=[PENDENTE.id, ANTIGO.id]
    )
    lidos_antes_do_vinculo = [VINCULADO, PENDENTE, ANTIGO]

    assert usuarios_a_atender(repositorio, lidos_antes_do_vinculo, VINCULADO.id) == [
        VINCULADO,
        NOVO,
    ]


def test_diario_atende_todos_e_a_entrega_imediata_seguinte_nao_repete():
    repositorio = RepositorioComMarcas(TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id])

    assert usuarios_a_atender(repositorio, TODOS, None) == TODOS
    assert usuarios_a_atender(repositorio, TODOS, VINCULADO.id) == []


def test_falha_ao_marcar_nao_impede_o_diario(caplog: pytest.LogCaptureFixture):
    repositorio = RepositorioQueNaoMarca(TODOS)

    assert usuarios_a_atender(repositorio, TODOS, None) == TODOS
    assert "não foram marcadas" in caplog.text


def test_visao_lista_so_os_atendidos_e_repassa_o_resto():
    visao = RepositorioDosAtendidos(RepositorioComMarcas(TODOS), [VINCULADO])

    assert visao.listar_ativos() == [VINCULADO]
    assert visao.pode_entregar(ANTIGO)


def test_entrega_imediata_coleta_e_atende_os_pendentes_com_a_reserva_de_todos(
    monkeypatch: pytest.MonkeyPatch,
):
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id, NOVO.id]
    )
    capturado = interceptar_execucao(monkeypatch)

    with cliente_sem_rede() as cliente, pytest.raises(ExecucaoInterrompida):
        cli.executar_fluxo(settings_de_teste(), cliente, repositorio, VINCULADO.id)

    assert capturado["coleta"] == [VINCULADO, PENDENTE]
    assert capturado["atendidos"] == [VINCULADO, PENDENTE]
    assert capturado["apenas_o_perfil"] is None
    assert capturado["reserva"] == reserva_do_diario(TODOS)
    assert capturado["reserva"] > reserva_do_diario([VINCULADO, PENDENTE])


def test_diario_coleta_e_atende_todos_sem_reserva_e_marca_os_atendidos(
    monkeypatch: pytest.MonkeyPatch,
):
    repositorio = RepositorioComMarcas(TODOS, pendentes=[PENDENTE.id])
    capturado = interceptar_execucao(monkeypatch)

    with cliente_sem_rede() as cliente, pytest.raises(ExecucaoInterrompida):
        cli.executar_fluxo(settings_de_teste(), cliente, repositorio, None)

    assert capturado["coleta"] == TODOS
    assert capturado["atendidos"] == TODOS
    assert capturado["reserva"] == 0
    assert repositorio.atendidos == {usuario.id for usuario in TODOS}


def test_entrega_imediata_sem_ninguem_a_atender_nem_abre_a_cota(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    repositorio = RepositorioComMarcas(TODOS, atendidos=[usuario.id for usuario in TODOS])
    capturado = interceptar_execucao(monkeypatch)

    with cliente_sem_rede() as cliente:
        cli.executar_fluxo(settings_de_teste(), cliente, repositorio, VINCULADO.id)

    assert "reserva" not in capturado
    assert "sem entrega a fazer" in capsys.readouterr().out
