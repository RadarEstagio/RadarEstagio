import json
import logging
import re
import sys
from contextlib import nullcontext
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.__main__ import avaliar, executar_fluxo, main
from radar.collectors.adzuna import LIMITE_POR_DIA, RESULTADOS_POR_PAGINA, URL_BUSCA
from radar.collectors.errors import ErroDeColeta
from radar.cota import FONTE_DO_DIARIO, reserva_do_diario, reserva_do_diario_na_jooble
from radar.domain.datas import data_local
from radar.domain.models import EventosDoSite, Modalidade, Perfil, Usuario, Vaga
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


def codigo_de_saida_do_rodar(
    monkeypatch: pytest.MonkeyPatch,
    repositorio: RepositorioEmMemoria,
    settings: Settings | None = None,
) -> int:
    escolhidas = settings or settings_de_teste()
    monkeypatch.setattr("radar.__main__.carregar_settings", lambda: escolhidas)
    monkeypatch.setattr(
        "radar.__main__.abrir_repositorio", lambda _settings: nullcontext(repositorio)
    )
    monkeypatch.setattr(sys, "argv", ["radar", "rodar"])
    try:
        main()
    except SystemExit as saida:
        return int(saida.code or 0)
    return 0


def recusar_os_chats(httpx_mock: HTTPXMock, chats: set[str]) -> None:
    def telegram(requisicao: httpx.Request) -> httpx.Response:
        if json.loads(requisicao.content)["chat_id"] in chats:
            return httpx.Response(500, text="Bad Gateway")
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    httpx_mock.add_callback(telegram, url=URL_DO_TELEGRAM, is_reusable=True)


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


class BancoComErroInesperado(RepositorioEmMemoria):
    def listar_ativos(self) -> list[Usuario]:
        raise AttributeError("'str' object has no attribute 'get'")


def test_erro_inesperado_da_execucao_avisa_a_operacao(httpx_mock: HTTPXMock):
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http, pytest.raises(AttributeError):
        executar_fluxo(settings_de_teste(), cliente_http, BancoComErroInesperado([]))

    [aviso] = mensagens_de_operacao(httpx_mock)
    assert "falhou" in aviso
    assert "AttributeError" in aviso
    assert "object has no attribute" in aviso


def test_interrupcao_da_execucao_nao_vira_aviso_de_operacao(httpx_mock: HTTPXMock):
    class BancoInterrompido(RepositorioEmMemoria):
        def listar_ativos(self) -> list[Usuario]:
            raise KeyboardInterrupt

    with httpx.Client() as cliente_http, pytest.raises(KeyboardInterrupt):
        executar_fluxo(settings_de_teste(), cliente_http, BancoInterrompido([]))

    assert mensagens_de_operacao(httpx_mock) == []


def test_perfil_sem_entrega_a_fazer_retorna_sem_coletar_nem_avisar(httpx_mock: HTTPXMock):
    with httpx.Client() as cliente_http:
        executar_fluxo(
            settings_de_teste(),
            cliente_http,
            RepositorioEmMemoria([]),
            apenas_o_perfil=UUID(int=7),
        )

    assert httpx_mock.get_requests() == []


CHAT_DO_ESTUDANTE = "555"
OUTRO_CHAT_DO_ESTUDANTE = "556"


def estudante_de_direito_no_rio() -> Usuario:
    return Usuario(
        id=UUID(int=1),
        perfil=Perfil(
            curso="Direito",
            periodo=4,
            habilidades=[],
            cidade="Rio de Janeiro, RJ",
            modalidade=Modalidade.PRESENCIAL,
        ),
        chat_id=CHAT_DO_ESTUDANTE,
    )


def pagina_de_ti(quantidade: int) -> dict:
    return {"results": pagina_cheia()["results"][:quantidade]}


def mensagens_para(httpx_mock: HTTPXMock, chat_id: str) -> list[str]:
    corpos = [
        json.loads(requisicao.content)
        for requisicao in httpx_mock.get_requests(url=URL_DO_TELEGRAM)
    ]
    return [corpo["text"] for corpo in corpos if corpo["chat_id"] == chat_id]


def test_coleta_que_para_no_meio_nao_diz_ao_estudante_que_nao_ha_vaga(httpx_mock: HTTPXMock):
    def adzuna(requisicao: httpx.Request) -> httpx.Response:
        if requisicao.url.params.get("where"):
            return httpx.Response(200, json=pagina_de_ti(10))
        return httpx.Response(400, text="pedido inválido")

    httpx_mock.add_callback(adzuna, url=re.compile(re.escape(URL_BUSCA)), is_reusable=True)
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(
            settings_de_teste(), cliente_http, RepositorioEmMemoria([estudante_de_direito_no_rio()])
        )

    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Coleta da Adzuna incompleta" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo


def test_cota_que_acaba_no_meio_nao_diz_ao_estudante_que_nao_ha_vaga(httpx_mock: HTTPXMock):
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])
    repositorio.registrar_requisicoes_da_fonte(
        "adzuna", datetime.now(UTC).date(), LIMITE_POR_DIA - 1
    )
    httpx_mock.add_response(url=url_da_pagina(1), json=pagina_cheia())
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)

    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Cota da Adzuna esgotada" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo


def test_coleta_completa_continua_dizendo_ao_estudante_que_nao_ha_vaga(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)), json=pagina_de_ti(10), is_reusable=True
    )
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(
            settings_de_teste(), cliente_http, RepositorioEmMemoria([estudante_de_direito_no_rio()])
        )

    [mensagem] = mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE)
    assert "Nenhuma vaga nova compatível" in mensagem


HORARIO_DO_DIARIO = datetime(2026, 9, 14, 10, 23, tzinfo=UTC)
ANTES_DO_DIARIO_DO_DIA = datetime(2026, 9, 14, 3, 0, tzinfo=UTC)
TARDE_DO_DIARIO = datetime(2026, 9, 14, 15, 0, tzinfo=UTC)


def parar_o_relogio(monkeypatch: pytest.MonkeyPatch, momento: datetime) -> None:
    class RelogioParado(datetime):
        @classmethod
        def now(cls, tz=None):
            return momento

    monkeypatch.setattr("radar.__main__.datetime", RelogioParado)


def test_diario_que_termina_registra_que_rodou_e_quanto_gastou(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    repositorio = RepositorioEmMemoria([])
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)
    parar_o_relogio(monkeypatch, HORARIO_DO_DIARIO)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)

    hoje = HORARIO_DO_DIARIO.date()
    assert repositorio.fonte_tem_registro_no_dia(FONTE_DO_DIARIO, hoje)
    assert repositorio.requisicoes_da_fonte_desde(FONTE_DO_DIARIO, hoje) == 1


def test_diario_que_falha_nao_registra_que_rodou(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    repositorio = RepositorioEmMemoria([])
    httpx_mock.add_response(url=url_da_pagina(1), status_code=401, text="não autorizado")
    aceitar_mensagens_do_telegram(httpx_mock)
    parar_o_relogio(monkeypatch, HORARIO_DO_DIARIO)

    with httpx.Client() as cliente_http, pytest.raises(ErroDeColeta):
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)

    assert not repositorio.fonte_tem_registro_no_dia(FONTE_DO_DIARIO, HORARIO_DO_DIARIO.date())


def test_entrega_imediata_depois_do_diario_usa_o_saldo_do_dia_sem_se_registrar_como_diario(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    estudante = estudante_de_direito_no_rio()
    repositorio = RepositorioEmMemoria([estudante])
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)), json=pagina_de_ti(10), is_reusable=True
    )
    aceitar_mensagens_do_telegram(httpx_mock)
    parar_o_relogio(monkeypatch, HORARIO_DO_DIARIO)
    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)
    hoje = HORARIO_DO_DIARIO.date()
    gasto_do_diario = repositorio.requisicoes_da_fonte_desde("adzuna", hoje)
    reserva = reserva_do_diario([estudante])
    repositorio.registrar_requisicoes_da_fonte(
        "adzuna", hoje, LIMITE_POR_DIA - reserva - gasto_do_diario
    )
    parar_o_relogio(monkeypatch, TARDE_DO_DIARIO)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, repositorio, apenas_o_perfil=estudante.id)

    assert repositorio.requisicoes_da_fonte_desde("adzuna", hoje) == (
        LIMITE_POR_DIA - reserva + gasto_do_diario
    )
    assert repositorio.requisicoes_da_fonte_desde(FONTE_DO_DIARIO, hoje) == gasto_do_diario


RODAR_MANUAL_NA_NOITE_DE_BRASILIA = datetime(2026, 9, 15, 1, 0, tzinfo=UTC)
DIARIO_DA_MANHA_SEGUINTE = datetime(2026, 9, 15, 10, 23, tzinfo=UTC)


def test_rodar_sem_perfil_na_noite_de_brasilia_deixa_a_reserva_para_o_diario_das_07_23(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    estudante = estudante_de_direito_no_rio()
    repositorio = RepositorioEmMemoria([estudante])
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)), json=pagina_de_ti(10), is_reusable=True
    )
    aceitar_mensagens_do_telegram(httpx_mock)
    dia = RODAR_MANUAL_NA_NOITE_DE_BRASILIA.date()
    parar_o_relogio(monkeypatch, RODAR_MANUAL_NA_NOITE_DE_BRASILIA)
    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)
    reserva = reserva_do_diario([estudante])
    gasto_da_noite = repositorio.requisicoes_da_fonte_desde("adzuna", dia)
    repositorio.registrar_requisicoes_da_fonte(
        "adzuna", dia, LIMITE_POR_DIA - reserva - gasto_da_noite
    )

    for hora in (2, 4, 6):
        parar_o_relogio(monkeypatch, datetime(2026, 9, 15, hora, 0, tzinfo=UTC))
        with httpx.Client() as cliente_http, pytest.raises(ErroDeColeta):
            executar_fluxo(
                settings_de_teste(), cliente_http, repositorio, apenas_o_perfil=estudante.id
            )
    uso_antes_do_diario = repositorio.requisicoes_da_fonte_desde("adzuna", dia)
    parar_o_relogio(monkeypatch, DIARIO_DA_MANHA_SEGUINTE)
    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, repositorio)

    assert uso_antes_do_diario == LIMITE_POR_DIA - reserva
    assert repositorio.requisicoes_da_fonte_desde("adzuna", dia) > uso_antes_do_diario
    assert repositorio.fonte_tem_registro_no_dia(FONTE_DO_DIARIO, dia)


class BancoComEventosDoSite(RepositorioEmMemoria):
    def eventos_do_site_nas_ultimas_24_horas(self) -> EventosDoSite:
        return EventosDoSite(visitantes=2400, contas=12, horas_no_teto=1)


class BancoSemATabelaDosEventosDoSite(RepositorioEmMemoria):
    def eventos_do_site_nas_ultimas_24_horas(self) -> EventosDoSite:
        raise ErroDeArmazenamento("relation eventos_do_site_por_hora does not exist")


class BancoQueInformaOTamanho(RepositorioEmMemoria):
    def tamanho_do_banco(self) -> int:
        return 367_001_600


class BancoQueRecusaLerOTamanho(RepositorioEmMemoria):
    def tamanho_do_banco(self) -> int:
        raise ErroDeArmazenamento("permission denied for function pg_database_size")


class BancoComUmPerfilIlegivel(RepositorioEmMemoria):
    def listar_ativos(self) -> list[Usuario]:
        self.perfis_ilegiveis = 1
        return super().listar_ativos()


def test_resumo_de_operacao_avisa_os_perfis_que_ficaram_de_fora(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, BancoComUmPerfilIlegivel([]))

    resumo = mensagens_de_operacao(httpx_mock)[-1]
    assert "⚠️ Perfis com dados inválidos, fora da execução: 1" in resumo


def test_resumo_de_operacao_mostra_os_eventos_do_site(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, BancoComEventosDoSite([]))

    resumo = mensagens_de_operacao(httpx_mock)[-1]
    assert "Eventos do site nas últimas 24 h: 2.400 de visitantes, 12 de contas" in resumo
    assert "⚠️ Eventos do site chegaram ao teto em 1 hora das últimas 24 h" in resumo


URL_DO_GEMINI = re.compile(r"https://generativelanguage\.googleapis\.com/.*")
CHAT_DA_ESTUDANTE_DE_COMPUTACAO = "777"


def estudante_de_computacao_no_rio() -> Usuario:
    return Usuario(
        id=UUID(int=2),
        perfil=Perfil(
            curso="Ciência da Computação",
            periodo=4,
            habilidades=["Python"],
            cidade="Rio de Janeiro, RJ",
            modalidade=Modalidade.PRESENCIAL,
        ),
        chat_id=CHAT_DA_ESTUDANTE_DE_COMPUTACAO,
    )


def vagas_de_desenvolvimento_no_rio(quantidade: int) -> dict:
    publicada = (datetime.now(UTC) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "results": [
            {
                "id": str(9100 + numero),
                "title": f"Estágio em Desenvolvimento de Software {numero}",
                "company": {"display_name": f"Empresa {numero}"},
                "location": {
                    "display_name": "Rio de Janeiro, Rio de Janeiro",
                    "area": ["Brasil", "Sudeste", "Rio de Janeiro", "Rio de Janeiro"],
                },
                "description": "Estágio para estudantes de Ciência da Computação com Python.",
                "redirect_url": f"https://www.adzuna.com.br/details/{9100 + numero}",
                "created": publicada,
            }
            for numero in range(1, quantidade + 1)
        ]
    }


class RepositorioQueGuardaExtracoes(RepositorioEmMemoria):
    def __init__(self, usuarios: list[Usuario]) -> None:
        super().__init__(usuarios)
        self.extracoes_guardadas: list[str] = []

    def guardar_extracoes(self, extracoes, modelo: str) -> None:
        super().guardar_extracoes(extracoes, modelo)
        self.extracoes_guardadas.extend(vaga.identidade() for vaga, _ in extracoes)


def test_corpo_do_gemini_que_nao_e_json_nao_derruba_o_job_nem_perde_o_que_ja_extraiu(
    httpx_mock: HTTPXMock,
):
    chamadas_ao_gemini: list[list[str]] = []

    def gemini(requisicao: httpx.Request) -> httpx.Response:
        prompt = json.loads(requisicao.content)["contents"][0]["parts"][0]["text"]
        ids = re.findall(r"Vaga id=(\S+)", prompt)
        chamadas_ao_gemini.append(ids)
        if len(chamadas_ao_gemini) > 1:
            return httpx.Response(200, headers={"content-type": "text/html"}, text="<html>")
        extracoes = [{"id_vaga": id_vaga, "area_da_vaga": "computacao"} for id_vaga in ids]
        texto = json.dumps({"extracoes": extracoes})
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": texto}], "role": "model"}}]}
        )

    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)),
        json=vagas_de_desenvolvimento_no_rio(4),
        is_reusable=True,
    )
    httpx_mock.add_callback(gemini, url=URL_DO_GEMINI, is_reusable=True)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioQueGuardaExtracoes([estudante_de_computacao_no_rio()])
    settings = settings_de_teste().model_copy(
        update={
            "gemini_vagas_por_lote": 2,
            "gemini_timeout_segundos": 1,
            "prazo_da_extracao_segundos": 60,
        }
    )

    with httpx.Client() as cliente_http:
        executar_fluxo(settings, cliente_http, repositorio)

    assert len(chamadas_ao_gemini) == 2
    assert repositorio.extracoes_guardadas == chamadas_ao_gemini[0]
    [mensagem] = mensagens_para(httpx_mock, CHAT_DA_ESTUDANTE_DE_COMPUTACAO)
    enviadas = {
        f"adzuna:{9100 + numero}"
        for numero in range(1, 5)
        if f"Desenvolvimento de Software {numero}</b>" in mensagem
    }
    assert enviadas == set(chamadas_ao_gemini[0])
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "Requisições ao avaliador: 2" in resumo
    assert "⚠️ Vagas sem extração (cota ou avaliador fora): 2" in resumo


def test_resumo_de_operacao_mostra_o_tamanho_do_banco(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, BancoQueInformaOTamanho([]))

    resumo = mensagens_de_operacao(httpx_mock)[-1]
    assert "Tamanho do banco: 350,0 MB de 500,0 MB (70%)" in resumo
    assert "⚠️ Banco passou de 70% do limite do plano" in resumo


def test_falha_ao_ler_o_tamanho_do_banco_so_avisa_no_log(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, BancoQueRecusaLerOTamanho([]))

    resumo = mensagens_de_operacao(httpx_mock)[-1]
    assert "Vagas coletadas: 3" in resumo
    assert "Tamanho do banco" not in resumo
    assert "pg_database_size" in caplog.text


def test_falha_ao_ler_os_eventos_do_site_so_avisa_no_log(
    httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
):
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_de_teste(), cliente_http, BancoSemATabelaDosEventosDoSite([]))

    resumo = mensagens_de_operacao(httpx_mock)[-1]
    assert "Vagas coletadas: 3" in resumo
    assert "Eventos do site" not in resumo
    assert "eventos_do_site_por_hora" in caplog.text


def test_resumo_que_nao_chega_ao_chat_de_operacao_termina_com_codigo_de_erro(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    recusar_os_chats(httpx_mock, {CHAT_DE_OPERACAO})

    codigo = codigo_de_saida_do_rodar(monkeypatch, RepositorioEmMemoria([]))

    assert codigo == 1


def test_execucao_relatada_sem_usuarios_ativos_termina_com_codigo_zero(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    httpx_mock.add_response(url=url_da_pagina(1), json={"results": pagina_cheia()["results"][:3]})
    aceitar_mensagens_do_telegram(httpx_mock)

    codigo = codigo_de_saida_do_rodar(monkeypatch, RepositorioEmMemoria([]))

    assert codigo == 0
    assert "Usuários ativos: 0" in mensagens_de_operacao(httpx_mock)[-1]


def atendido_hoje(usuario: Usuario) -> Usuario:
    return usuario.model_copy(update={"ultimo_dia_atendido": data_local(datetime.now(UTC))})


def test_diario_com_todos_ja_atendidos_hoje_nao_coleta_nem_manda_mensagem(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    repositorio = RepositorioEmMemoria([atendido_hoje(estudante_de_direito_no_rio())])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    assert httpx_mock.get_requests() == []
    assert "já foram atendidos hoje; coleta não executada" in capsys.readouterr().out


def test_diario_atende_so_quem_ainda_nao_recebeu_a_mensagem_de_hoje(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_com_vagas_de_ti(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    pendente = estudante_de_direito_no_rio().model_copy(
        update={"id": UUID(int=9), "chat_id": OUTRO_CHAT_DO_ESTUDANTE}
    )
    repositorio = RepositorioEmMemoria([atendido_hoje(estudante_de_direito_no_rio()), pendente])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    assert len(mensagens_para(httpx_mock, OUTRO_CHAT_DO_ESTUDANTE)) == 1
    resumo = mensagens_de_operacao(httpx_mock)[-1]
    assert "Usuários ativos: 1" in resumo
    assert "Já atendidos hoje, fora desta execução: 1" in resumo


def responder_com_vagas_de_ti(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)), json=pagina_de_ti(10), is_reusable=True
    )


def test_execucao_em_que_ninguem_recebe_mensagem_por_falha_termina_com_codigo_de_erro(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_com_vagas_de_ti(httpx_mock)
    recusar_os_chats(httpx_mock, {CHAT_DO_ESTUDANTE})
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 1
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Usuários sem mensagem por falha: 1" in resumo


def test_execucao_com_todas_as_mensagens_seguradas_termina_com_codigo_zero(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    def adzuna(requisicao: httpx.Request) -> httpx.Response:
        if requisicao.url.params.get("where"):
            return httpx.Response(200, json=pagina_de_ti(10))
        return httpx.Response(400, text="pedido inválido")

    httpx_mock.add_callback(adzuna, url=re.compile(re.escape(URL_BUSCA)), is_reusable=True)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "Receberam recomendação: 0" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo
    assert "Usuários sem mensagem por falha" not in resumo


def test_token_do_bot_revogado_nao_termina_em_verde(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_com_vagas_de_ti(httpx_mock)
    httpx_mock.add_response(
        url=URL_DO_TELEGRAM,
        status_code=401,
        json={"ok": False, "description": "Unauthorized"},
        is_reusable=True,
    )
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 1


def test_dia_em_que_todos_recebem_nenhuma_vaga_compativel_termina_com_codigo_zero(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_com_vagas_de_ti(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    assert "Nenhuma vaga nova compatível" in mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE)[0]
    assert "sem mensagem por falha" not in mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]


def test_falha_de_um_usuario_nao_derruba_o_codigo_de_saida_dos_outros(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    outra = estudante_de_direito_no_rio().model_copy(
        update={"id": UUID(int=3), "chat_id": OUTRO_CHAT_DO_ESTUDANTE}
    )
    responder_com_vagas_de_ti(httpx_mock)
    recusar_os_chats(httpx_mock, {CHAT_DO_ESTUDANTE})
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio(), outra])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    assert mensagens_para(httpx_mock, OUTRO_CHAT_DO_ESTUDANTE) != []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Usuários sem mensagem por falha: 1" in resumo


def bloquear_o_bot_nos_chats(httpx_mock: HTTPXMock, chats: set[str]) -> None:
    def telegram(requisicao: httpx.Request) -> httpx.Response:
        if json.loads(requisicao.content)["chat_id"] in chats:
            return httpx.Response(
                403,
                json={
                    "ok": False,
                    "error_code": 403,
                    "description": "Forbidden: bot was blocked by the user",
                },
            )
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    httpx_mock.add_callback(telegram, url=URL_DO_TELEGRAM, is_reusable=True)


ID_DE_QUEM_COMPLETA_O_LIMITE = UUID("814c6041-0000-4000-8000-000000000001")
ID_DE_QUEM_RECUSA_PELA_PRIMEIRA_VEZ = UUID("9f2a11bc-0000-4000-8000-000000000002")
CHAT_DA_PRIMEIRA_RECUSA = "557"


class BancoEmQueUmaRecusaDeHojeCompletaOLimite(RepositorioEmMemoria):
    def registrar_falha_de_envio(self, usuario: Usuario) -> int:
        if usuario.id == ID_DE_QUEM_COMPLETA_O_LIMITE:
            return settings_de_teste().falhas_de_envio_ate_pausar
        return 1


def test_resumo_de_operacao_avisa_quem_bloqueou_o_bot_e_quem_foi_pausado(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    no_limite = estudante_de_direito_no_rio().model_copy(
        update={"id": ID_DE_QUEM_COMPLETA_O_LIMITE}
    )
    na_primeira = estudante_de_direito_no_rio().model_copy(
        update={"id": ID_DE_QUEM_RECUSA_PELA_PRIMEIRA_VEZ, "chat_id": CHAT_DA_PRIMEIRA_RECUSA}
    )
    outra = estudante_de_direito_no_rio().model_copy(
        update={"id": UUID(int=3), "chat_id": OUTRO_CHAT_DO_ESTUDANTE}
    )
    responder_com_vagas_de_ti(httpx_mock)
    bloquear_o_bot_nos_chats(httpx_mock, {CHAT_DO_ESTUDANTE, CHAT_DA_PRIMEIRA_RECUSA})
    repositorio = BancoEmQueUmaRecusaDeHojeCompletaOLimite([no_limite, na_primeira, outra])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    assert mensagens_para(httpx_mock, OUTRO_CHAT_DO_ESTUDANTE) != []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert (
        "⚠️ Recusaram a mensagem (bot bloqueado ou conversa inexistente): 2 "
        "(...814c6041..., ...9f2a11bc...)"
    ) in resumo
    assert "⚠️ Pausados por recusas seguidas: 1 (...814c6041...)" in resumo
    assert "Usuários sem mensagem por falha" not in resumo
    saida = capsys.readouterr().out
    assert "2 recusaram a mensagem, 1 pausados por recusa" in saida
    assert str(ID_DE_QUEM_COMPLETA_O_LIMITE) not in saida + resumo
    assert str(ID_DE_QUEM_RECUSA_PELA_PRIMEIRA_VEZ) not in saida + resumo


def test_bot_bloqueado_antes_do_limite_aparece_no_resumo_sem_pausa(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_com_vagas_de_ti(httpx_mock)
    bloquear_o_bot_nos_chats(httpx_mock, {CHAT_DO_ESTUDANTE})
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])

    codigo = codigo_de_saida_do_rodar(monkeypatch, repositorio)

    assert codigo == 0
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Recusaram a mensagem" in resumo
    assert "Pausados" not in resumo


CAMINHO_DA_PAGINA_DO_EMPREGO_PT = (
    Path(__file__).parent / "fixtures" / "adzuna_detalhe_com_parceiro.html"
)
CAMINHO_DA_PAGINA_SEM_PARCEIRO = Path(__file__).parent / "fixtures" / "adzuna_detalhe.html"
URL_DA_PAGINA_DO_ANUNCIO = re.compile(r"https://www\.adzuna\.com\.br/details/\d+")


def pagina_do_emprego_pt() -> str:
    return CAMINHO_DA_PAGINA_DO_EMPREGO_PT.read_text(encoding="utf-8")


def pagina_do_sourcestack() -> str:
    return (
        pagina_do_emprego_pt()
        .replace("/images/br/jobs/partners/logo_emprego.png", "/images/BR/partners/logo.png")
        .replace('alt="Emprego"', 'alt="SourceStack"')
        .replace('"source_id" : "79986"', '"source_id" : "506674"')
    )


def vagas_com_descricao_cortada_pela_api(quantidade: int) -> dict:
    pagina = vagas_de_desenvolvimento_no_rio(quantidade)
    for item in pagina["results"]:
        item["description"] = item["description"].ljust(499) + "…"
    return pagina


def responder_com_as_paginas_dos_anuncios(
    httpx_mock: HTTPXMock, pagina_de_cada_anuncio: dict[str, str | None]
) -> list[str]:
    ids_pedidos_ao_gemini: list[str] = []

    def gemini(requisicao: httpx.Request) -> httpx.Response:
        prompt = json.loads(requisicao.content)["contents"][0]["parts"][0]["text"]
        ids = re.findall(r"Vaga id=(\S+)", prompt)
        ids_pedidos_ao_gemini.extend(ids)
        extracoes = [{"id_vaga": id_vaga, "area_da_vaga": "computacao"} for id_vaga in ids]
        texto = json.dumps({"extracoes": extracoes})
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": texto}], "role": "model"}}]}
        )

    def pagina_do_anuncio(requisicao: httpx.Request) -> httpx.Response:
        pagina = pagina_de_cada_anuncio[requisicao.url.path.split("/")[-1]]
        if pagina is None:
            return httpx.Response(403, text="Forbidden")
        return httpx.Response(200, text=pagina)

    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)),
        json=vagas_com_descricao_cortada_pela_api(len(pagina_de_cada_anuncio)),
        is_reusable=True,
    )
    httpx_mock.add_callback(pagina_do_anuncio, url=URL_DA_PAGINA_DO_ANUNCIO, is_reusable=True)
    httpx_mock.add_callback(gemini, url=URL_DO_GEMINI, is_reusable=True, is_optional=True)
    return ids_pedidos_ao_gemini


def rodar_com_as_paginas_dos_anuncios(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
    pagina_de_cada_anuncio: dict[str, str | None],
) -> list[str]:
    ids_pedidos_ao_gemini = responder_com_as_paginas_dos_anuncios(
        httpx_mock, pagina_de_cada_anuncio
    )
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio) == 0
    return ids_pedidos_ao_gemini


def test_diario_corta_a_vaga_do_emprego_pt_antes_da_ia_e_relata_no_resumo(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    ids_pedidos_ao_gemini = rodar_com_as_paginas_dos_anuncios(
        httpx_mock,
        monkeypatch,
        {
            "9101": pagina_do_emprego_pt(),
            "9102": pagina_do_sourcestack(),
            "9103": pagina_do_sourcestack(),
        },
    )

    assert sorted(ids_pedidos_ao_gemini) == ["adzuna:9102", "adzuna:9103"]
    [mensagem] = mensagens_para(httpx_mock, CHAT_DA_ESTUDANTE_DE_COMPUTACAO)
    assert "Desenvolvimento de Software 1</b>" not in mensagem
    assert "Desenvolvimento de Software 2</b>" in mensagem
    assert "Desenvolvimento de Software 3</b>" in mensagem
    assert len(httpx_mock.get_requests(url=URL_DA_PAGINA_DO_ANUNCIO)) == 3
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "Vagas descartadas por virem do emprego.pt: 1" in resumo
    assert "sem origem identificada" not in resumo
    saida = capsys.readouterr().out
    assert "1 vagas descartadas por virem do emprego.pt" in saida
    assert "0 de 3 páginas de anúncio lidas sem origem identificada" in saida
    assert "não lidas" not in resumo
    assert "0 páginas de anúncio não lidas" in saida


def test_diario_avisa_quando_as_paginas_param_de_informar_a_origem_e_nao_corta_nada(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    sem_parceiro = CAMINHO_DA_PAGINA_SEM_PARCEIRO.read_text(encoding="utf-8")

    ids_pedidos_ao_gemini = rodar_com_as_paginas_dos_anuncios(
        httpx_mock,
        monkeypatch,
        {"9101": sem_parceiro, "9102": sem_parceiro, "9103": pagina_do_sourcestack()},
    )

    assert sorted(ids_pedidos_ao_gemini) == ["adzuna:9101", "adzuna:9102", "adzuna:9103"]
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert (
        "⚠️ Páginas da Adzuna lidas sem origem identificada: 2 de 3 "
        "(o corte do emprego.pt pode não estar funcionando)"
    ) in resumo
    assert "Vagas descartadas por virem do emprego.pt" not in resumo
    saida = capsys.readouterr().out
    assert "0 vagas descartadas por virem do emprego.pt" in saida
    assert "2 de 3 páginas de anúncio lidas sem origem identificada" in saida


def test_diario_relata_as_paginas_que_a_adzuna_recusou_e_segue_sem_cortar_essas_vagas(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    ids_pedidos_ao_gemini = rodar_com_as_paginas_dos_anuncios(
        httpx_mock,
        monkeypatch,
        {"9101": None, "9102": None, "9103": pagina_do_sourcestack()},
    )

    assert sorted(ids_pedidos_ao_gemini) == ["adzuna:9101", "adzuna:9102", "adzuna:9103"]
    [mensagem] = mensagens_para(httpx_mock, CHAT_DA_ESTUDANTE_DE_COMPUTACAO)
    assert "Desenvolvimento de Software 1</b>" in mensagem
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert (
        "⚠️ Páginas da Adzuna não lidas: 2 (o corte do emprego.pt não vale para elas)"
        in resumo.splitlines()
    )
    assert "sem origem identificada" not in resumo
    saida = capsys.readouterr().out
    assert "0 de 1 páginas de anúncio lidas sem origem identificada" in saida
    assert "2 páginas de anúncio não lidas" in saida


def avaliar_com_as_paginas_dos_anuncios(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, pagina_de_cada_anuncio: dict[str, str]
) -> list[str]:
    ids_pedidos_ao_gemini = responder_com_as_paginas_dos_anuncios(
        httpx_mock, pagina_de_cada_anuncio
    )
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])
    monkeypatch.setattr(
        "radar.__main__.abrir_repositorio", lambda _settings: nullcontext(repositorio)
    )

    avaliar(settings_de_teste())

    return ids_pedidos_ao_gemini


def test_avaliacao_manual_nao_pede_a_ia_a_vaga_do_emprego_pt(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    ids_pedidos_ao_gemini = avaliar_com_as_paginas_dos_anuncios(
        httpx_mock,
        monkeypatch,
        {
            "9101": pagina_do_emprego_pt(),
            "9102": pagina_do_sourcestack(),
            "9103": pagina_do_sourcestack(),
        },
    )

    assert sorted(ids_pedidos_ao_gemini) == ["adzuna:9102", "adzuna:9103"]
    assert len(httpx_mock.get_requests(url=URL_DA_PAGINA_DO_ANUNCIO)) == 3
    saida = capsys.readouterr().out
    assert "1 vagas descartadas por virem do emprego.pt" in saida
    assert "extraindo 2 com" in saida


def test_avaliacao_manual_so_com_vaga_do_emprego_pt_nao_chama_a_ia(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    ids_pedidos_ao_gemini = avaliar_com_as_paginas_dos_anuncios(
        httpx_mock,
        monkeypatch,
        {"9101": pagina_do_emprego_pt(), "9102": pagina_do_emprego_pt()},
    )

    assert ids_pedidos_ao_gemini == []
    assert httpx_mock.get_requests(url=URL_DO_GEMINI) == []
    saida = capsys.readouterr().out
    assert "2 vagas descartadas por virem do emprego.pt" in saida
    assert "extraindo 0 com" in saida


def test_avaliacao_manual_segue_com_a_vaga_sem_origem_identificada(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    sem_parceiro = CAMINHO_DA_PAGINA_SEM_PARCEIRO.read_text(encoding="utf-8")

    ids_pedidos_ao_gemini = avaliar_com_as_paginas_dos_anuncios(
        httpx_mock, monkeypatch, {"9101": sem_parceiro, "9102": pagina_do_sourcestack()}
    )

    assert sorted(ids_pedidos_ao_gemini) == ["adzuna:9101", "adzuna:9102"]
    assert "emprego.pt" not in capsys.readouterr().out


URL_DA_JOOBLE = re.compile(r"https://br\.jooble\.org/.*")
CHAVE_DA_JOOBLE = "chave-jooble-de-teste"


def settings_com_a_jooble() -> Settings:
    return settings_de_teste().model_copy(
        update={"fontes": "adzuna,jooble", "jooble_api_key": CHAVE_DA_JOOBLE}
    )


def vaga_da_jooble(numero: int, source: str) -> dict:
    publicada = (datetime.now(UTC) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.0000000")
    return {
        "title": f"Estágio em Desenvolvimento de Software {numero}",
        "location": "Rio de Janeiro, RJ",
        "snippet": "&nbsp;...Estágio para estudantes de Ciência da Computação com <b>Python</b>...",
        "salary": "",
        "source": source,
        "type": "",
        "link": f"https://br.jooble.org/jdp/{numero}",
        "company": f"Empresa {numero}",
        "updated": publicada,
        "id": numero,
    }


def responder_a_jooble(httpx_mock: HTTPXMock, vagas_de_cada_regiao: dict[str, list[dict]]) -> None:
    def jooble(requisicao: httpx.Request) -> httpx.Response:
        regiao = json.loads(requisicao.content)["location"]
        vagas = vagas_de_cada_regiao.get(regiao, [])
        return httpx.Response(200, json={"totalCount": len(vagas), "jobs": vagas})

    httpx_mock.add_callback(jooble, url=URL_DA_JOOBLE, is_reusable=True)


def responder_o_gemini(httpx_mock: HTTPXMock) -> list[str]:
    ids_pedidos: list[str] = []

    def gemini(requisicao: httpx.Request) -> httpx.Response:
        prompt = json.loads(requisicao.content)["contents"][0]["parts"][0]["text"]
        ids = re.findall(r"Vaga id=(\S+)", prompt)
        ids_pedidos.extend(ids)
        extracoes = [{"id_vaga": id_vaga, "area_da_vaga": "computacao"} for id_vaga in ids]
        texto = json.dumps({"extracoes": extracoes})
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": texto}], "role": "model"}}]}
        )

    httpx_mock.add_callback(gemini, url=URL_DO_GEMINI, is_reusable=True, is_optional=True)
    return ids_pedidos


def adzuna_sem_vagas(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)), json={"results": []}, is_reusable=True
    )


def uso_gravado_da_jooble(repositorio: RepositorioEmMemoria) -> int:
    return repositorio.requisicoes_da_fonte_desde("jooble", date.min)


def test_diario_com_a_jooble_entrega_a_vaga_dela_sem_a_da_gupy_e_relata_o_uso(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    adzuna_sem_vagas(httpx_mock)
    responder_a_jooble(
        httpx_mock,
        {
            "Rio de Janeiro": [
                vaga_da_jooble(1, "empregos.com.br"),
                vaga_da_jooble(2, "gupy.io"),
                vaga_da_jooble(3, "infojobs.com.br"),
            ]
        },
    )
    ids_pedidos_ao_gemini = responder_o_gemini(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioQueGuardaExtracoes([estudante_de_computacao_no_rio()])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    assert sorted(ids_pedidos_ao_gemini) == ["jooble:1", "jooble:3"]
    assert sorted(repositorio.extracoes_guardadas) == ["jooble:1", "jooble:3"]
    [mensagem] = mensagens_para(httpx_mock, CHAT_DA_ESTUDANTE_DE_COMPUTACAO)
    assert "Desenvolvimento de Software 1</b>" in mensagem
    assert "Desenvolvimento de Software 3</b>" in mensagem
    assert "Desenvolvimento de Software 2</b>" not in mensagem
    assert "🏷️ Fonte: Jooble" in mensagem
    assert "Adzuna" not in mensagem
    assert "Ver vaga em br.jooble.org" in mensagem
    assert "nota limitada a 60" in mensagem
    assert uso_gravado_da_jooble(repositorio) == 2
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "Requisições à Jooble: 2 de 100 hoje (2%)" in resumo
    assert "Cota da Jooble esgotada" not in resumo
    assert "2 requisições à Jooble" in capsys.readouterr().out


def test_diario_com_a_jooble_nunca_le_a_pagina_da_vaga_no_site_da_jooble(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    adzuna_sem_vagas(httpx_mock)
    responder_a_jooble(httpx_mock, {"Rio de Janeiro": [vaga_da_jooble(1, "empregos.com.br")]})
    responder_o_gemini(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    pedidos_a_jooble = httpx_mock.get_requests(url=URL_DA_JOOBLE)
    assert [(pedido.method, pedido.url.path) for pedido in pedidos_a_jooble] == [
        ("POST", f"/api/{CHAVE_DA_JOOBLE}"),
        ("POST", f"/api/{CHAVE_DA_JOOBLE}"),
    ]


@pytest.fixture
def httpx_sem_nivel_de_log_proprio():
    registrador = logging.getLogger("httpx")
    nivel_anterior = registrador.level
    registrador.setLevel(logging.NOTSET)
    yield
    registrador.setLevel(nivel_anterior)


def test_diario_nao_deixa_o_httpx_escrever_no_log_a_url_com_a_chave_da_jooble(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    httpx_sem_nivel_de_log_proprio: None,
):
    caplog.set_level(logging.INFO)
    adzuna_sem_vagas(httpx_mock)
    responder_a_jooble(httpx_mock, {"Rio de Janeiro": [vaga_da_jooble(1, "empregos.com.br")]})
    responder_o_gemini(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])
    settings = settings_com_a_jooble()

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings) == 0

    assert len(httpx_mock.get_requests(url=URL_DA_JOOBLE)) == 2
    assert "1 vagas coletadas em jooble" in caplog.text
    assert CHAVE_DA_JOOBLE not in caplog.text
    assert settings.adzuna_app_key not in caplog.text
    assert settings.telegram_bot_token not in caplog.text
    assert "HTTP Request" not in caplog.text


def test_diario_sem_a_jooble_ligada_nao_a_consulta_nem_fala_dela(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    adzuna_sem_vagas(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio) == 0

    assert httpx_mock.get_requests(url=URL_DA_JOOBLE) == []
    assert uso_gravado_da_jooble(repositorio) == 0
    assert "Jooble" not in mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]


def test_cota_da_jooble_que_acaba_no_meio_nao_diz_ao_estudante_que_nao_ha_vaga(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    adzuna_sem_vagas(httpx_mock)
    responder_a_jooble(httpx_mock, {"Rio de Janeiro": [vaga_da_jooble(1, "empregos.com.br")]})
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])
    repositorio.registrar_requisicoes_da_fonte("jooble", datetime.now(UTC).date(), 99)

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    assert len(httpx_mock.get_requests(url=URL_DA_JOOBLE)) == 1
    assert uso_gravado_da_jooble(repositorio) == 100
    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "Requisições à Jooble: 100 de 100 hoje (100%)" in resumo
    assert "⚠️ Cota da Jooble esgotada: a coleta parou antes do fim" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo


def test_jooble_sem_saldo_no_dia_fica_fora_da_execucao_e_a_adzuna_entrega(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)),
        json=vagas_de_desenvolvimento_no_rio(2),
        is_reusable=True,
    )
    responder_o_gemini(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])
    repositorio.registrar_requisicoes_da_fonte("jooble", datetime.now(UTC).date(), 100)

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    assert httpx_mock.get_requests(url=URL_DA_JOOBLE) == []
    assert uso_gravado_da_jooble(repositorio) == 100
    [mensagem] = mensagens_para(httpx_mock, CHAT_DA_ESTUDANTE_DE_COMPUTACAO)
    assert "Desenvolvimento de Software 1</b>" in mensagem
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Cota da Jooble esgotada: a coleta parou antes do fim" in resumo


def test_limite_diario_excedido_na_jooble_gasta_uma_requisicao_e_aparece_no_resumo(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    adzuna_sem_vagas(httpx_mock)
    httpx_mock.add_response(
        url=URL_DA_JOOBLE, status_code=429, text="Too Many Requests", is_reusable=True
    )
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    assert len(httpx_mock.get_requests(url=URL_DA_JOOBLE)) == 1
    assert uso_gravado_da_jooble(repositorio) == 1
    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Cota da Jooble esgotada: a coleta parou antes do fim" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo


def test_busca_da_jooble_que_falha_depois_da_cidade_aparece_como_coleta_incompleta(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    adzuna_sem_vagas(httpx_mock)

    def jooble(requisicao: httpx.Request) -> httpx.Response:
        if json.loads(requisicao.content)["location"]:
            return httpx.Response(
                200, json={"totalCount": 1, "jobs": [vaga_da_jooble(1, "empregos.com.br")]}
            )
        return httpx.Response(400, text="location is required")

    httpx_mock.add_callback(jooble, url=URL_DA_JOOBLE, is_reusable=True)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_direito_no_rio()])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Coleta da Jooble incompleta: Jooble respondeu HTTP 400 ao buscar vagas" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo
    assert CHAVE_DA_JOOBLE not in resumo


def test_entrega_imediata_antes_do_diario_deixa_para_ele_a_reserva_da_jooble(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    estudante = estudante_de_direito_no_rio()
    repositorio = RepositorioEmMemoria([estudante])
    reserva = reserva_do_diario_na_jooble([estudante])
    hoje = ANTES_DO_DIARIO_DO_DIA.date()
    repositorio.registrar_requisicoes_da_fonte("jooble", hoje, 100 - reserva - 1)
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)), json=pagina_de_ti(10), is_reusable=True
    )
    responder_a_jooble(httpx_mock, {"Rio de Janeiro": [vaga_da_jooble(1, "empregos.com.br")]})
    aceitar_mensagens_do_telegram(httpx_mock)
    parar_o_relogio(monkeypatch, ANTES_DO_DIARIO_DO_DIA)

    with httpx.Client() as cliente_http:
        executar_fluxo(
            settings_com_a_jooble(), cliente_http, repositorio, apenas_o_perfil=estudante.id
        )

    assert len(httpx_mock.get_requests(url=URL_DA_JOOBLE)) == 1
    assert repositorio.requisicoes_da_fonte_desde("jooble", hoje) == 100 - reserva
    parar_o_relogio(monkeypatch, HORARIO_DO_DIARIO)

    with httpx.Client() as cliente_http:
        executar_fluxo(settings_com_a_jooble(), cliente_http, repositorio)

    assert len(httpx_mock.get_requests(url=URL_DA_JOOBLE)) == 3
    assert repositorio.requisicoes_da_fonte_desde("jooble", hoje) == 100 - reserva + 2


def responder_sem_esperar_entre_as_tentativas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("radar.collectors.tentativas.ESPERAS_ENTRE_TENTATIVAS_EM_SEGUNDOS", (0, 0))


def adzuna_fora_do_ar(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)),
        status_code=503,
        text="Service Unavailable",
        is_reusable=True,
    )


def test_adzuna_fora_do_ar_com_a_jooble_respondendo_nao_diz_ao_estudante_que_nao_ha_vaga(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_sem_esperar_entre_as_tentativas(monkeypatch)
    adzuna_fora_do_ar(httpx_mock)
    responder_a_jooble(httpx_mock, {"Rio de Janeiro": []})
    aceitar_mensagens_do_telegram(httpx_mock)
    estudante = estudante_de_direito_no_rio()
    repositorio = RepositorioEmMemoria([estudante])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    assert not repositorio.atendido_no_dia(estudante, data_local(datetime.now(UTC)))
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Coleta da Adzuna incompleta: Adzuna respondeu HTTP 503 ao buscar vagas" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo


def test_jooble_recusada_com_a_adzuna_respondendo_nao_diz_ao_estudante_que_nao_ha_vaga(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    adzuna_sem_vagas(httpx_mock)
    httpx_mock.add_response(
        url=URL_DA_JOOBLE, status_code=403, text="Access Denied", is_reusable=True
    )
    aceitar_mensagens_do_telegram(httpx_mock)
    estudante = estudante_de_direito_no_rio()
    repositorio = RepositorioEmMemoria([estudante])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    assert not repositorio.atendido_no_dia(estudante, data_local(datetime.now(UTC)))
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Coleta da Jooble incompleta: Jooble respondeu HTTP 403 ao buscar vagas" in resumo
    assert "⚠️ Mensagens seguradas pela coleta incompleta: 1" in resumo
    assert CHAVE_DA_JOOBLE not in resumo


def test_fonte_que_falha_inteira_nao_segura_a_mensagem_de_quem_tem_vaga_da_outra(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)),
        json=vagas_de_desenvolvimento_no_rio(2),
        is_reusable=True,
    )
    httpx_mock.add_response(
        url=URL_DA_JOOBLE, status_code=403, text="Access Denied", is_reusable=True
    )
    responder_o_gemini(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings_com_a_jooble()) == 0

    [mensagem] = mensagens_para(httpx_mock, CHAT_DA_ESTUDANTE_DE_COMPUTACAO)
    assert "Desenvolvimento de Software 1</b>" in mensagem
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert "⚠️ Coleta da Jooble incompleta: Jooble respondeu HTTP 403 ao buscar vagas" in resumo
    assert "Mensagens seguradas pela coleta incompleta" not in resumo


def test_adzuna_fora_do_ar_como_unica_fonte_continua_terminando_com_codigo_de_erro(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
):
    responder_sem_esperar_entre_as_tentativas(monkeypatch)
    adzuna_fora_do_ar(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    estudante = estudante_de_direito_no_rio()
    repositorio = RepositorioEmMemoria([estudante])

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio) == 1

    assert mensagens_para(httpx_mock, CHAT_DO_ESTUDANTE) == []
    assert not repositorio.atendido_no_dia(estudante, data_local(datetime.now(UTC)))
    [aviso] = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)
    assert "falhou" in aviso
    assert "Nenhuma fonte respondeu: adzuna: Adzuna respondeu HTTP 503 ao buscar vagas" in aviso


def test_chave_da_jooble_que_nao_cabe_na_url_nao_derruba_a_execucao_nem_aparece_em_lugar_algum(
    httpx_mock: HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture,
):
    caplog.set_level("DEBUG")
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_BUSCA)),
        json=vagas_de_desenvolvimento_no_rio(2),
        is_reusable=True,
    )
    responder_o_gemini(httpx_mock)
    aceitar_mensagens_do_telegram(httpx_mock)
    repositorio = RepositorioEmMemoria([estudante_de_computacao_no_rio()])
    settings = settings_com_a_jooble().model_copy(
        update={"jooble_api_key": "chave-secreta\ncolada"}
    )

    assert codigo_de_saida_do_rodar(monkeypatch, repositorio, settings) == 0

    assert httpx_mock.get_requests(url=URL_DA_JOOBLE) == []
    [mensagem] = mensagens_para(httpx_mock, CHAT_DA_ESTUDANTE_DE_COMPUTACAO)
    assert "Desenvolvimento de Software 1</b>" in mensagem
    resumo = mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]
    assert (
        "⚠️ Coleta da Jooble incompleta: "
        "Requisição inválida ao buscar vagas na Jooble (InvalidURL)" in resumo
    )
    saida = capsys.readouterr()
    for texto in (resumo, mensagem, caplog.text, saida.out, saida.err):
        assert "chave-secreta" not in texto
        assert "colada" not in texto
