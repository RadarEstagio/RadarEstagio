import re
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest

from radar.collectors.adzuna import LIMITE_POR_MINUTO, CotaDaAdzuna
from radar.collectors.cota import CotaDeRequisicoes, CotaEsgotada
from radar.collectors.errors import ErroDeColeta
from radar.collectors.jooble import LIMITE_DE_PAGINAS_POR_REGIAO as PAGINAS_POR_REGIAO_NA_JOOBLE
from radar.collectors.jooble import LIMITE_POR_DIA as LIMITE_DIARIO_DA_JOOBLE
from radar.cota import (
    FONTE_DO_DIARIO,
    INICIO_DA_JANELA_DO_DIARIO_UTC,
    ColetorComRegistroDeUso,
    abrir_cota_da_adzuna,
    abrir_cota_da_jooble,
    registrar_diario_da_adzuna,
    registrar_uso_da_fonte,
    reserva_do_diario,
    reserva_do_diario_na_jooble,
    uso_da_adzuna,
    uso_da_jooble,
)
from radar.domain.models import Modalidade, Perfil, Usuario, Vaga
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria

AGORA = datetime(2026, 9, 12, 10, 23, tzinfo=UTC)


class RepositorioSemTabela(RepositorioEmMemoria):
    def requisicoes_da_fonte_desde(self, fonte: str, desde: date) -> int:
        raise ErroDeArmazenamento("relation uso_das_fontes does not exist")

    def registrar_requisicoes_da_fonte(self, fonte: str, dia: date, requisicoes: int) -> None:
        raise ErroDeArmazenamento("relation uso_das_fontes does not exist")


def test_saldo_do_dia_no_banco_limita_a_cota_da_execucao():
    repositorio = RepositorioEmMemoria([])
    repositorio.registrar_requisicoes_da_fonte("adzuna", date(2026, 9, 12), 240)

    cota = abrir_cota_da_adzuna(repositorio, AGORA)
    for _ in range(10):
        cota.reservar()

    with pytest.raises(CotaEsgotada):
        cota.reservar()


def test_uso_de_outros_meses_nao_conta_no_mes():
    repositorio = RepositorioEmMemoria([])
    repositorio.registrar_requisicoes_da_fonte("adzuna", date(2026, 8, 31), 2400)
    repositorio.registrar_requisicoes_da_fonte("adzuna", date(2026, 9, 1), 30)
    repositorio.registrar_requisicoes_da_fonte("adzuna", date(2026, 9, 12), 18)

    assert uso_da_adzuna(repositorio, AGORA) == (18, 48)


def test_uso_da_execucao_e_somado_ao_do_dia():
    repositorio = RepositorioEmMemoria([])
    repositorio.registrar_requisicoes_da_fonte("adzuna", date(2026, 9, 12), 18)
    cota = abrir_cota_da_adzuna(repositorio, AGORA)
    for _ in range(5):
        cota.reservar()

    registrar_uso_da_fonte(repositorio, "adzuna", cota.requisicoes, AGORA)

    assert uso_da_adzuna(repositorio, AGORA) == (23, 23)


def test_banco_sem_a_tabela_nao_derruba_a_execucao(caplog):
    repositorio = RepositorioSemTabela([])

    cota = abrir_cota_da_adzuna(repositorio, AGORA)
    cota.reservar()
    registrar_uso_da_fonte(repositorio, "adzuna", cota.requisicoes, AGORA)

    assert uso_da_adzuna(repositorio, AGORA) is None
    assert "uso_das_fontes" in caplog.text


class ColetorQueGasta:
    def __init__(
        self, cota: CotaDaAdzuna, requisicoes: int, erro: ErroDeColeta | None = None
    ) -> None:
        self._cota = cota
        self._requisicoes = requisicoes
        self._erro = erro

    def coletar(self) -> list[Vaga]:
        for _ in range(self._requisicoes):
            self._cota.reservar()
        if self._erro is not None:
            raise self._erro
        return []


def test_uso_e_gravado_assim_que_a_coleta_termina():
    repositorio = RepositorioEmMemoria([])
    cota = abrir_cota_da_adzuna(repositorio, AGORA)

    ColetorComRegistroDeUso(
        ColetorQueGasta(cota, 7), repositorio, {"adzuna": cota}, AGORA
    ).coletar()

    assert uso_da_adzuna(repositorio, AGORA) == (7, 7)


def test_uso_e_gravado_mesmo_quando_a_coleta_falha():
    repositorio = RepositorioEmMemoria([])
    cota = abrir_cota_da_adzuna(repositorio, AGORA)
    coletor = ColetorComRegistroDeUso(
        ColetorQueGasta(cota, 3, ErroDeColeta("HTTP 500")), repositorio, {"adzuna": cota}, AGORA
    )

    with pytest.raises(ErroDeColeta):
        coletor.coletar()

    assert uso_da_adzuna(repositorio, AGORA) == (3, 3)


def test_coletas_seguidas_gravam_so_o_que_cada_uma_gastou():
    repositorio = RepositorioEmMemoria([])
    cota = abrir_cota_da_adzuna(repositorio, AGORA)
    coletor = ColetorComRegistroDeUso(
        ColetorQueGasta(cota, 4), repositorio, {"adzuna": cota}, AGORA
    )

    coletor.coletar()
    coletor.coletar()

    assert uso_da_adzuna(repositorio, AGORA) == (8, 8)


def usuario_em(
    cidade: str, modalidade: Modalidade, curso: str = "Engenharia de Software", numero: int = 1
) -> Usuario:
    return Usuario(
        id=UUID(int=numero),
        perfil=Perfil(curso=curso, periodo=4, habilidades=[], cidade=cidade, modalidade=modalidade),
        chat_id=str(numero),
    )


def test_entrega_imediata_nao_gasta_a_reserva_do_diario():
    repositorio = RepositorioEmMemoria([])
    repositorio.registrar_requisicoes_da_fonte("adzuna", date(2026, 9, 12), 200)

    cota = abrir_cota_da_adzuna(repositorio, AGORA, reserva=40)
    for _ in range(10):
        cota.reservar()

    with pytest.raises(CotaEsgotada):
        cota.reservar()


def test_reserva_do_diario_cobre_todas_as_paginas_de_cada_regiao_e_busca():
    no_rio = usuario_em("Rio de Janeiro, RJ", Modalidade.PRESENCIAL)
    remoto = usuario_em("Recife, PE", Modalidade.REMOTO, numero=2)
    sem_area = usuario_em("Recife, PE", Modalidade.REMOTO, curso="Curso Que Não Existe", numero=3)

    assert reserva_do_diario([no_rio, remoto]) == 20
    assert reserva_do_diario([no_rio, remoto, sem_area]) == 40


DIA_DO_DIARIO = date(2026, 9, 13)
HORARIO_DO_DIARIO = datetime(2026, 9, 13, 10, 23, tzinfo=UTC)
ANTES_DO_DIARIO = datetime(2026, 9, 13, 8, 0, tzinfo=UTC)
DEPOIS_DO_DIARIO = datetime(2026, 9, 13, 15, 0, tzinfo=UTC)
NOITE_DE_BRASILIA = datetime(2026, 9, 14, 0, 30, tzinfo=UTC)
RESERVA = 40


def requisicoes_permitidas(cota: CotaDaAdzuna) -> int:
    for feitas in range(LIMITE_POR_MINUTO):
        try:
            cota.reservar()
        except CotaEsgotada:
            return feitas
    return LIMITE_POR_MINUTO


def uso_no_dia(dia: date, requisicoes: int) -> RepositorioEmMemoria:
    repositorio = RepositorioEmMemoria([])
    repositorio.registrar_requisicoes_da_fonte("adzuna", dia, requisicoes)
    return repositorio


def test_entrega_imediata_antes_do_diario_guarda_a_reserva():
    repositorio = uso_no_dia(DIA_DO_DIARIO, 200)

    cota = abrir_cota_da_adzuna(repositorio, ANTES_DO_DIARIO, reserva=RESERVA)

    assert requisicoes_permitidas(cota) == 10


def test_entrega_imediata_depois_do_diario_usa_o_saldo_do_dia_sem_a_reserva():
    repositorio = uso_no_dia(DIA_DO_DIARIO, 230)
    registrar_diario_da_adzuna(repositorio, 140, HORARIO_DO_DIARIO)

    cota = abrir_cota_da_adzuna(repositorio, DEPOIS_DO_DIARIO, reserva=RESERVA)

    assert requisicoes_permitidas(cota) == 20


def test_diario_sem_nenhuma_requisicao_tambem_conta_como_rodado():
    repositorio = uso_no_dia(DIA_DO_DIARIO, 230)
    registrar_diario_da_adzuna(repositorio, 0, HORARIO_DO_DIARIO)

    cota = abrir_cota_da_adzuna(repositorio, DEPOIS_DO_DIARIO, reserva=RESERVA)

    assert requisicoes_permitidas(cota) == 20


def test_entrega_imediata_na_noite_de_brasilia_guarda_a_reserva_do_diario_da_manha():
    repositorio = uso_no_dia(date(2026, 9, 14), 200)
    registrar_diario_da_adzuna(repositorio, 140, HORARIO_DO_DIARIO)

    cota = abrir_cota_da_adzuna(repositorio, NOITE_DE_BRASILIA, reserva=RESERVA)

    assert requisicoes_permitidas(cota) == 10


def test_diario_que_falhou_ou_nao_rodou_mantem_a_reserva_o_dia_todo():
    repositorio = uso_no_dia(DIA_DO_DIARIO, 200)

    cota = abrir_cota_da_adzuna(repositorio, DEPOIS_DO_DIARIO, reserva=RESERVA)

    assert requisicoes_permitidas(cota) == 10


@pytest.mark.parametrize(
    ("dia_do_uso_anterior", "uso_anterior"),
    [
        pytest.param(date(2026, 9, 8), 1000 - 100 - RESERVA - 15, id="semana"),
        pytest.param(date(2026, 9, 1), 2500 - 100 - RESERVA - 15, id="mes"),
    ],
)
def test_depois_do_diario_a_reserva_ainda_protege_o_diario_de_amanha_na_semana_e_no_mes(
    dia_do_uso_anterior: date, uso_anterior: int
):
    repositorio = uso_no_dia(DIA_DO_DIARIO, 100)
    repositorio.registrar_requisicoes_da_fonte("adzuna", dia_do_uso_anterior, uso_anterior)
    registrar_diario_da_adzuna(repositorio, 100, HORARIO_DO_DIARIO)

    cota = abrir_cota_da_adzuna(repositorio, DEPOIS_DO_DIARIO, reserva=RESERVA)

    assert requisicoes_permitidas(cota) == 15


def test_diario_registra_o_que_gastou_sem_mudar_o_uso_da_adzuna():
    repositorio = uso_no_dia(DIA_DO_DIARIO, 140)

    registrar_diario_da_adzuna(repositorio, 140, HORARIO_DO_DIARIO)

    assert repositorio.requisicoes_da_fonte_desde(FONTE_DO_DIARIO, DIA_DO_DIARIO) == 140
    assert uso_da_adzuna(repositorio, DEPOIS_DO_DIARIO) == (140, 140)


class RegistroDoDiarioIlegivel(RepositorioEmMemoria):
    def fonte_tem_registro_no_dia(self, fonte: str, dia: date) -> bool:
        raise ErroDeArmazenamento("connection reset")


def test_registro_do_diario_ilegivel_mantem_a_reserva(caplog: pytest.LogCaptureFixture):
    repositorio = RegistroDoDiarioIlegivel([])
    repositorio.registrar_requisicoes_da_fonte("adzuna", DIA_DO_DIARIO, 200)
    registrar_diario_da_adzuna(repositorio, 140, HORARIO_DO_DIARIO)

    cota = abrir_cota_da_adzuna(repositorio, DEPOIS_DO_DIARIO, reserva=RESERVA)

    assert requisicoes_permitidas(cota) == 10
    assert "connection reset" in caplog.text


def test_falha_ao_registrar_o_diario_so_avisa(caplog: pytest.LogCaptureFixture):
    registrar_diario_da_adzuna(RepositorioSemTabela([]), 140, HORARIO_DO_DIARIO)

    assert "uso_das_fontes" in caplog.text


RODAR_MANUAL_NA_NOITE_DE_BRASILIA = datetime(2026, 9, 15, 1, 0, tzinfo=UTC)
MADRUGADA_DE_BRASILIA = datetime(2026, 9, 15, 5, 0, tzinfo=UTC)


def test_rodar_sem_perfil_na_noite_de_brasilia_nao_libera_a_reserva_do_diario_da_manha():
    dia = RODAR_MANUAL_NA_NOITE_DE_BRASILIA.date()
    repositorio = uso_no_dia(dia, 200)
    registrar_diario_da_adzuna(repositorio, 80, RODAR_MANUAL_NA_NOITE_DE_BRASILIA)

    cota = abrir_cota_da_adzuna(repositorio, MADRUGADA_DE_BRASILIA, reserva=RESERVA)

    assert not repositorio.fonte_tem_registro_no_dia(FONTE_DO_DIARIO, dia)
    assert requisicoes_permitidas(cota) == 10


@pytest.mark.parametrize(
    ("hora", "minuto", "registra"),
    [(0, 0, False), (9, 22, False), (9, 23, True), (10, 23, True), (23, 59, True)],
)
def test_diario_so_registra_que_rodou_a_partir_da_janela_do_diario(
    hora: int, minuto: int, registra: bool
):
    repositorio = RepositorioEmMemoria([])
    momento = datetime(2026, 9, 15, hora, minuto, tzinfo=UTC)

    registrar_diario_da_adzuna(repositorio, 80, momento)

    assert repositorio.fonte_tem_registro_no_dia(FONTE_DO_DIARIO, momento.date()) is registra


def test_janela_do_diario_e_a_mesma_da_telegram_webhook():
    webhook = Path(__file__).parent.parent / "supabase/functions/telegram-webhook"
    fonte = (webhook / "entrega_imediata.ts").read_text()
    encontrado = re.search(
        r"INICIO_DA_JANELA_DO_DIARIO_EM_MINUTOS_UTC = (\d+) \* 60 \+ (\d+);", fonte
    )

    assert encontrado is not None
    assert (INICIO_DA_JANELA_DO_DIARIO_UTC.hour, INICIO_DA_JANELA_DO_DIARIO_UTC.minute) == (
        int(encontrado.group(1)),
        int(encontrado.group(2)),
    )


def requisicoes_que_a_jooble_permite(cota: CotaDeRequisicoes) -> int:
    for feitas in range(2 * LIMITE_DIARIO_DA_JOOBLE):
        try:
            cota.reservar()
        except CotaEsgotada:
            return feitas
    return 2 * LIMITE_DIARIO_DA_JOOBLE


def uso_da_jooble_no_dia(dia: date, requisicoes: int) -> RepositorioEmMemoria:
    repositorio = RepositorioEmMemoria([])
    repositorio.registrar_requisicoes_da_fonte("jooble", dia, requisicoes)
    return repositorio


def test_saldo_da_jooble_e_o_que_falta_das_cem_requisicoes_do_dia():
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 93)

    cota = abrir_cota_da_jooble(repositorio, HORARIO_DO_DIARIO)

    assert LIMITE_DIARIO_DA_JOOBLE == 100
    assert requisicoes_que_a_jooble_permite(cota) == 7
    assert cota.esgotada


def test_dia_sem_uso_abre_a_jooble_com_as_cem_requisicoes():
    cota = abrir_cota_da_jooble(RepositorioEmMemoria([]), HORARIO_DO_DIARIO)

    assert requisicoes_que_a_jooble_permite(cota) == 100


def test_uso_de_ontem_e_uso_da_adzuna_nao_entram_no_dia_da_jooble():
    repositorio = uso_da_jooble_no_dia(date(2026, 9, 12), 100)
    repositorio.registrar_requisicoes_da_fonte("adzuna", DIA_DO_DIARIO, 240)
    repositorio.registrar_requisicoes_da_fonte("jooble", DIA_DO_DIARIO, 10)

    cota = abrir_cota_da_jooble(repositorio, HORARIO_DO_DIARIO)

    assert requisicoes_que_a_jooble_permite(cota) == 90
    assert uso_da_jooble(repositorio, HORARIO_DO_DIARIO) == 10


def test_uso_acima_do_limite_deixa_o_saldo_da_jooble_em_zero():
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 130)

    cota = abrir_cota_da_jooble(repositorio, HORARIO_DO_DIARIO)

    assert requisicoes_que_a_jooble_permite(cota) == 0


def test_dia_da_jooble_vira_a_meia_noite_em_utc_e_nao_na_de_brasilia():
    noite_de_brasilia = datetime.fromisoformat("2026-09-13T21:30:00-03:00")
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 100)

    cota = abrir_cota_da_jooble(repositorio, noite_de_brasilia)
    registrar_uso_da_fonte(repositorio, "jooble", 4, noite_de_brasilia)

    assert requisicoes_que_a_jooble_permite(cota) == 100
    assert repositorio.requisicoes_da_fonte_desde("jooble", date(2026, 9, 14)) == 4
    assert uso_da_jooble(repositorio, noite_de_brasilia) == 4


def test_entrega_imediata_antes_do_diario_nao_gasta_o_que_o_diario_precisa_na_jooble():
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 80)

    cota = abrir_cota_da_jooble(repositorio, ANTES_DO_DIARIO, reserva=15)

    assert requisicoes_que_a_jooble_permite(cota) == 5


def test_entrega_imediata_depois_do_diario_usa_o_saldo_da_jooble_sem_a_reserva():
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 80)
    registrar_diario_da_adzuna(repositorio, 20, HORARIO_DO_DIARIO)

    cota = abrir_cota_da_jooble(repositorio, DEPOIS_DO_DIARIO, reserva=15)

    assert requisicoes_que_a_jooble_permite(cota) == 20


def test_diario_que_nao_rodou_mantem_a_reserva_da_jooble_o_dia_todo():
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 80)

    cota = abrir_cota_da_jooble(repositorio, DEPOIS_DO_DIARIO, reserva=15)

    assert requisicoes_que_a_jooble_permite(cota) == 5


def test_reserva_maior_que_o_saldo_da_jooble_deixa_a_entrega_imediata_sem_requisicao():
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 95)

    cota = abrir_cota_da_jooble(repositorio, ANTES_DO_DIARIO, reserva=15)

    assert requisicoes_que_a_jooble_permite(cota) == 0


def test_diario_abre_a_jooble_sem_reserva():
    repositorio = uso_da_jooble_no_dia(DIA_DO_DIARIO, 80)

    cota = abrir_cota_da_jooble(repositorio, HORARIO_DO_DIARIO)

    assert requisicoes_que_a_jooble_permite(cota) == 20


def test_reserva_do_diario_na_jooble_cobre_as_paginas_de_cada_regiao_sem_multiplicar_por_busca():
    no_rio = usuario_em("Rio de Janeiro, RJ", Modalidade.PRESENCIAL)
    remoto = usuario_em("Recife, PE", Modalidade.REMOTO, numero=2)
    sem_area = usuario_em("Recife, PE", Modalidade.REMOTO, curso="Curso Que Não Existe", numero=3)
    em_niteroi = usuario_em("Niterói, RJ", Modalidade.HIBRIDO, numero=4)

    assert PAGINAS_POR_REGIAO_NA_JOOBLE == 5
    assert reserva_do_diario_na_jooble([remoto]) == 5
    assert reserva_do_diario_na_jooble([no_rio, remoto]) == 10
    assert reserva_do_diario_na_jooble([no_rio, remoto, sem_area]) == 10
    assert reserva_do_diario_na_jooble([no_rio, remoto, em_niteroi]) == 15


def test_banco_fora_do_ar_nao_derruba_a_cota_nem_o_registro_da_jooble(
    caplog: pytest.LogCaptureFixture,
):
    repositorio = RepositorioSemTabela([])

    cota = abrir_cota_da_jooble(repositorio, HORARIO_DO_DIARIO, reserva=15)
    cota.reservar()
    registrar_uso_da_fonte(repositorio, "jooble", cota.requisicoes, HORARIO_DO_DIARIO)

    assert not cota.esgotada
    assert uso_da_jooble(repositorio, HORARIO_DO_DIARIO) is None
    assert "Uso da Jooble não pôde ser lido" in caplog.text
    assert "Uso da fonte jooble não foi gravado (1 requisições)" in caplog.text


def test_registro_do_diario_ilegivel_mantem_a_reserva_da_jooble():
    repositorio = RegistroDoDiarioIlegivel([])
    repositorio.registrar_requisicoes_da_fonte("jooble", DIA_DO_DIARIO, 80)
    registrar_diario_da_adzuna(repositorio, 20, HORARIO_DO_DIARIO)

    cota = abrir_cota_da_jooble(repositorio, DEPOIS_DO_DIARIO, reserva=15)

    assert requisicoes_que_a_jooble_permite(cota) == 5


def test_coleta_grava_o_uso_de_cada_fonte_com_o_proprio_nome():
    repositorio = RepositorioEmMemoria([])
    cota_da_adzuna = abrir_cota_da_adzuna(repositorio, AGORA)
    cota_da_jooble = abrir_cota_da_jooble(repositorio, AGORA)

    class ColetorDasDuasFontes:
        def coletar(self) -> list[Vaga]:
            for _ in range(6):
                cota_da_adzuna.reservar()
            for _ in range(4):
                cota_da_jooble.reservar()
            raise ErroDeColeta("HTTP 500")

    coletor = ColetorComRegistroDeUso(
        ColetorDasDuasFontes(),
        repositorio,
        {"adzuna": cota_da_adzuna, "jooble": cota_da_jooble},
        AGORA,
    )
    with pytest.raises(ErroDeColeta):
        coletor.coletar()

    assert uso_da_adzuna(repositorio, AGORA) == (6, 6)
    assert uso_da_jooble(repositorio, AGORA) == 4


def test_fonte_que_nao_gastou_nada_nao_ganha_linha_de_uso():
    repositorio = RepositorioEmMemoria([])
    cota_da_adzuna = abrir_cota_da_adzuna(repositorio, AGORA)
    cota_da_jooble = abrir_cota_da_jooble(repositorio, AGORA)

    ColetorComRegistroDeUso(
        ColetorQueGasta(cota_da_adzuna, 2),
        repositorio,
        {"adzuna": cota_da_adzuna, "jooble": cota_da_jooble},
        AGORA,
    ).coletar()

    assert not repositorio.fonte_tem_registro_no_dia("jooble", AGORA.date())
    assert repositorio.fonte_tem_registro_no_dia("adzuna", AGORA.date())
