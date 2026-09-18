import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from pytest_httpx import HTTPXMock

import radar.__main__ as cli
from radar.collectors.adzuna import LIMITE_POR_DIA, URL_BUSCA, CotaDaAdzuna
from radar.collectors.errors import ErroDeColeta
from radar.cota import reserva_do_diario
from radar.domain.models import ExtracaoDaVaga, Perfil, Usuario, Vaga
from radar.domain.perfil_fixo import perfil_de_exemplo
from radar.entrega_imediata import (
    RepositorioDosAtendidos,
    repositorio_da_execucao,
    usuarios_a_atender,
)
from radar.settings import Settings
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria

CAMINHO_DO_FIXTURE = Path(__file__).parent / "fixtures" / "adzuna_resposta.json"
URL_DO_TELEGRAM = re.compile(r"https://api\.telegram\.org/.*")
URL_DA_ADZUNA = re.compile(re.escape(URL_BUSCA))
URL_DO_ANUNCIO = re.compile(r"https://www\.adzuna\.com\.br/details/.*")
SEM_VAGA_COMPATIVEL = "Nenhuma vaga nova compatível"
TITULO_DA_VAGA_DE_SALVADOR = "Vaga de Estágio em TI"


def usuario(numero: int, cidade: str) -> Usuario:
    perfil = Perfil(**{**perfil_de_exemplo().model_dump(), "cidade": cidade})
    return Usuario(id=UUID(int=numero), perfil=perfil, chat_id=str(numero))


VINCULADO = usuario(1, "Recife, PE")
PENDENTE = usuario(2, "Niterói, RJ")
ANTIGO = usuario(3, "Belo Horizonte, MG")
NOVO = usuario(4, "Recife, PE")
EM_SALVADOR = usuario(5, "Salvador, BA")
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

    def entregas_imediatas_pendentes(self, perfil_id: UUID) -> set[UUID]:
        ativos = {usuario.id for usuario in self.listar_ativos()}
        return ({perfil_id} | self.pendentes) & ativos - self.atendidos

    def marcar_entregas_imediatas_atendidas(self, perfis: list[UUID]) -> None:
        self.atendidos |= set(perfis)


class RepositorioQueNaoMarca(RepositorioComMarcas):
    def marcar_entregas_imediatas_atendidas(self, perfis: list[UUID]) -> None:
        raise ErroDeArmazenamento("banco fora do ar")


class RepositorioAtendidoPorOutraExecucao(RepositorioComMarcas):
    def travar_atendimento(self, usuario: Usuario) -> None:
        if usuario.id == PENDENTE.id:
            self.atendidos.add(PENDENTE.id)


class ExecucaoInterrompida(BaseException):
    pass


class ExtratorDeVagasDeTI:
    def __init__(self) -> None:
        self.requisicoes = 0

    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        self.requisicoes += 1
        return [
            ExtracaoDaVaga(
                id_vaga=vaga.identidade(),
                area_da_vaga="computacao",
                areas_da_vaga=["desenvolvimento_web"],
                cursos_aceitos=["Ciência da Computação"],
                habilidades_obrigatorias=["Python"],
            )
            for vaga in vagas
        ]


class ExtratorForaDoAr(ExtratorDeVagasDeTI):
    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        self.requisicoes += 1
        return []


class ExtratorInterrompido(ExtratorDeVagasDeTI):
    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        raise ExecucaoInterrompida


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


def usar_o_extrator(monkeypatch: pytest.MonkeyPatch, extrator: ExtratorDeVagasDeTI) -> None:
    monkeypatch.setattr(cli, "montar_extrator", lambda settings: extrator)


def aceitar_o_telegram(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=URL_DO_TELEGRAM, json={"ok": True, "result": {"message_id": 1}}, is_reusable=True
    )


def vagas_da_adzuna() -> dict:
    return json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8"))


def responder_com_as_vagas(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=URL_DA_ADZUNA, json=vagas_da_adzuna(), is_reusable=True)
    httpx_mock.add_response(url=URL_DO_ANUNCIO, status_code=404, is_reusable=True, is_optional=True)


def mensagens_para(httpx_mock: HTTPXMock, destinatario: Usuario) -> list[str]:
    corpos = [
        json.loads(requisicao.content)
        for requisicao in httpx_mock.get_requests(url=URL_DO_TELEGRAM)
    ]
    return [corpo["text"] for corpo in corpos if corpo["chat_id"] == destinatario.chat_id]


def rodar(repositorio: RepositorioComMarcas, apenas_o_perfil: UUID | None = None) -> None:
    with httpx.Client() as cliente_http:
        cli.executar_fluxo(settings_de_teste(), cliente_http, repositorio, apenas_o_perfil)


def test_entrega_imediata_escolhe_o_perfil_e_quem_ficou_pendente_sem_marcar_ninguem():
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id, NOVO.id]
    )

    assert usuarios_a_atender(repositorio, TODOS, VINCULADO.id) == [VINCULADO, PENDENTE]
    assert usuarios_a_atender(repositorio, TODOS, VINCULADO.id) == [VINCULADO, PENDENTE]
    assert usuarios_a_atender(repositorio, TODOS, PENDENTE.id) == [PENDENTE]
    assert repositorio.atendidos == {ANTIGO.id, NOVO.id}


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


def test_diario_atende_todos_sem_marcar_ninguem_antes_de_atender():
    repositorio = RepositorioComMarcas(TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id])

    assert usuarios_a_atender(repositorio, TODOS, None) == TODOS
    assert repositorio.atendidos == {ANTIGO.id}


def test_visao_lista_so_os_atendidos_e_repassa_o_resto():
    visao = RepositorioDosAtendidos(RepositorioComMarcas(TODOS), [VINCULADO])

    assert visao.listar_ativos() == [VINCULADO]
    assert visao.pode_entregar(ANTIGO)


def test_entrega_imediata_so_entrega_a_quem_continua_pendente_na_hora_de_enviar():
    repositorio = RepositorioComMarcas(TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id])
    visao = repositorio_da_execucao(repositorio, [VINCULADO, PENDENTE], VINCULADO.id)

    assert visao.listar_ativos() == [VINCULADO, PENDENTE]
    assert visao.pode_entregar(PENDENTE)
    repositorio.marcar_entregas_imediatas_atendidas([PENDENTE.id])
    assert not visao.pode_entregar(PENDENTE)


def test_diario_entrega_tambem_a_quem_ja_teve_a_entrega_imediata_atendida():
    repositorio = RepositorioComMarcas(TODOS, atendidos=[ANTIGO.id])
    visao = repositorio_da_execucao(repositorio, TODOS, None)

    assert visao.listar_ativos() == TODOS
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
    assert repositorio.atendidos == {ANTIGO.id, NOVO.id}


def test_diario_interrompido_coleta_e_atende_todos_sem_reserva_e_sem_marcar_ninguem(
    monkeypatch: pytest.MonkeyPatch,
):
    repositorio = RepositorioComMarcas(TODOS, pendentes=[PENDENTE.id])
    capturado = interceptar_execucao(monkeypatch)

    with cliente_sem_rede() as cliente, pytest.raises(ExecucaoInterrompida):
        cli.executar_fluxo(settings_de_teste(), cliente, repositorio, None)

    assert capturado["coleta"] == TODOS
    assert capturado["atendidos"] == TODOS
    assert capturado["reserva"] == 0
    assert repositorio.atendidos == set()


def test_entrega_imediata_sem_ninguem_a_atender_nem_abre_a_cota(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    repositorio = RepositorioComMarcas(TODOS, atendidos=[usuario.id for usuario in TODOS])
    capturado = interceptar_execucao(monkeypatch)

    with cliente_sem_rede() as cliente:
        cli.executar_fluxo(settings_de_teste(), cliente, repositorio, VINCULADO.id)

    assert "reserva" not in capturado
    assert "sem entrega a fazer" in capsys.readouterr().out


def test_coleta_que_falha_deixa_a_entrega_imediata_para_a_execucao_seguinte(
    httpx_mock: HTTPXMock,
):
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[VINCULADO.id, PENDENTE.id], atendidos=[ANTIGO.id, NOVO.id]
    )
    httpx_mock.add_response(url=URL_DA_ADZUNA, status_code=401, text="não autorizado")
    aceitar_o_telegram(httpx_mock)

    with pytest.raises(ErroDeColeta):
        rodar(repositorio, VINCULADO.id)

    assert repositorio.atendidos == {ANTIGO.id, NOVO.id}
    responder_com_as_vagas(httpx_mock)

    rodar(repositorio, PENDENTE.id)

    assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, VINCULADO)[0]
    assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, PENDENTE)[0]
    assert repositorio.atendidos == {usuario.id for usuario in TODOS}


def test_cota_sem_saldo_deixa_todos_os_pendentes_para_a_execucao_seguinte(
    httpx_mock: HTTPXMock,
):
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[PENDENTE.id, NOVO.id], atendidos=[ANTIGO.id]
    )
    repositorio.registrar_requisicoes_da_fonte("adzuna", datetime.now(UTC).date(), LIMITE_POR_DIA)
    aceitar_o_telegram(httpx_mock)

    for vinculado_agora in (VINCULADO, PENDENTE, NOVO):
        with pytest.raises(ErroDeColeta):
            rodar(repositorio, vinculado_agora.id)

    assert httpx_mock.get_requests(url=URL_DA_ADZUNA) == []
    assert repositorio.atendidos == {ANTIGO.id}


def test_mensagem_segurada_por_falta_de_extracao_deixa_a_entrega_imediata_pendente(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    repositorio = RepositorioComMarcas([EM_SALVADOR], pendentes=[EM_SALVADOR.id])
    responder_com_as_vagas(httpx_mock)
    aceitar_o_telegram(httpx_mock)
    usar_o_extrator(monkeypatch, ExtratorForaDoAr())

    rodar(repositorio, EM_SALVADOR.id)

    assert mensagens_para(httpx_mock, EM_SALVADOR) == []
    assert repositorio.atendidos == set()
    usar_o_extrator(monkeypatch, ExtratorDeVagasDeTI())

    rodar(repositorio, EM_SALVADOR.id)

    [mensagem] = mensagens_para(httpx_mock, EM_SALVADOR)
    assert TITULO_DA_VAGA_DE_SALVADOR in mensagem
    assert repositorio.atendidos == {EM_SALVADOR.id}


def test_mensagem_segurada_por_coleta_incompleta_deixa_a_entrega_imediata_pendente(
    httpx_mock: HTTPXMock,
):
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id, NOVO.id]
    )

    def adzuna(requisicao: httpx.Request) -> httpx.Response:
        if requisicao.url.params.get("where"):
            return httpx.Response(200, json=vagas_da_adzuna())
        return httpx.Response(400, text="pedido inválido")

    httpx_mock.add_callback(adzuna, url=URL_DA_ADZUNA, is_reusable=True)
    aceitar_o_telegram(httpx_mock)

    rodar(repositorio, VINCULADO.id)

    assert mensagens_para(httpx_mock, VINCULADO) == []
    assert mensagens_para(httpx_mock, PENDENTE) == []
    assert repositorio.atendidos == {ANTIGO.id, NOVO.id}


def test_excecao_antes_de_entregar_deixa_todos_os_pendentes(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    repositorio = RepositorioComMarcas([VINCULADO, EM_SALVADOR], pendentes=[EM_SALVADOR.id])
    responder_com_as_vagas(httpx_mock)
    usar_o_extrator(monkeypatch, ExtratorInterrompido())

    with pytest.raises(ExecucaoInterrompida):
        rodar(repositorio, VINCULADO.id)

    assert repositorio.atendidos == set()


def test_execucao_interrompida_no_meio_marca_so_quem_ja_recebeu(httpx_mock: HTTPXMock):
    repositorio = RepositorioComMarcas(
        TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id, NOVO.id]
    )
    responder_com_as_vagas(httpx_mock)

    def telegram(requisicao: httpx.Request) -> httpx.Response:
        if json.loads(requisicao.content)["chat_id"] == PENDENTE.chat_id:
            raise ExecucaoInterrompida
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    httpx_mock.add_callback(telegram, url=URL_DO_TELEGRAM, is_reusable=True)

    with pytest.raises(ExecucaoInterrompida):
        rodar(repositorio, VINCULADO.id)

    assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, VINCULADO)[0]
    assert repositorio.atendidos == {ANTIGO.id, NOVO.id, VINCULADO.id}


def test_entrega_com_vagas_e_sem_vaga_marcam_os_atendidos_e_nao_se_repetem(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    repositorio = RepositorioComMarcas(
        [VINCULADO, EM_SALVADOR, ANTIGO], pendentes=[EM_SALVADOR.id], atendidos=[ANTIGO.id]
    )
    responder_com_as_vagas(httpx_mock)
    aceitar_o_telegram(httpx_mock)
    usar_o_extrator(monkeypatch, ExtratorDeVagasDeTI())

    rodar(repositorio, VINCULADO.id)

    assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, VINCULADO)[0]
    assert TITULO_DA_VAGA_DE_SALVADOR in mensagens_para(httpx_mock, EM_SALVADOR)[0]
    assert repositorio.atendidos == {VINCULADO.id, EM_SALVADOR.id, ANTIGO.id}
    requisicoes_ate_aqui = len(httpx_mock.get_requests())
    capsys.readouterr()

    rodar(repositorio, EM_SALVADOR.id)

    assert len(httpx_mock.get_requests()) == requisicoes_ate_aqui
    assert "sem entrega a fazer" in capsys.readouterr().out


def test_diario_marca_so_quem_atendeu(httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch):
    repositorio = RepositorioComMarcas(
        [VINCULADO, EM_SALVADOR, ANTIGO],
        pendentes=[VINCULADO.id, EM_SALVADOR.id],
        atendidos=[ANTIGO.id],
    )
    responder_com_as_vagas(httpx_mock)
    aceitar_o_telegram(httpx_mock)
    usar_o_extrator(monkeypatch, ExtratorForaDoAr())

    rodar(repositorio)

    assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, VINCULADO)[0]
    assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, ANTIGO)[0]
    assert mensagens_para(httpx_mock, EM_SALVADOR) == []
    assert repositorio.atendidos == {ANTIGO.id, VINCULADO.id}


def test_pendente_atendido_por_outra_execucao_nao_recebe_de_novo(httpx_mock: HTTPXMock):
    repositorio = RepositorioAtendidoPorOutraExecucao(
        TODOS, pendentes=[PENDENTE.id], atendidos=[ANTIGO.id, NOVO.id]
    )
    responder_com_as_vagas(httpx_mock)
    aceitar_o_telegram(httpx_mock)

    rodar(repositorio, VINCULADO.id)

    assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, VINCULADO)[0]
    assert mensagens_para(httpx_mock, PENDENTE) == []


def test_falha_ao_marcar_nao_impede_a_entrega(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    repositorio = RepositorioQueNaoMarca(TODOS, pendentes=[PENDENTE.id])
    responder_com_as_vagas(httpx_mock)
    aceitar_o_telegram(httpx_mock)

    rodar(repositorio)

    for destinatario in TODOS:
        assert SEM_VAGA_COMPATIVEL in mensagens_para(httpx_mock, destinatario)[0]
    assert "não foi marcada como atendida" in caplog.text
