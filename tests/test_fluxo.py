import json
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.__main__ import executar_fluxo
from radar.collectors.adzuna import LIMITE_POR_DIA, RESULTADOS_POR_PAGINA, URL_BUSCA
from radar.collectors.errors import ErroDeColeta
from radar.cota import FONTE_DO_DIARIO, reserva_do_diario
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
    assert "⚠️ Coleta da Adzuna incompleta" in mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]


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
    assert "⚠️ Cota da Adzuna esgotada" in mensagens_para(httpx_mock, CHAT_DE_OPERACAO)[-1]


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
