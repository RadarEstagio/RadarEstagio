from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from radar.collectors.adzuna import CotaDaAdzunaEsgotada
from radar.cota import (
    abrir_cota_da_adzuna,
    registrar_uso_da_adzuna,
    reserva_do_diario,
    uso_da_adzuna,
)
from radar.domain.models import Modalidade, Perfil, Usuario
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

    with pytest.raises(CotaDaAdzunaEsgotada):
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

    registrar_uso_da_adzuna(repositorio, cota, AGORA)

    assert uso_da_adzuna(repositorio, AGORA) == (23, 23)


def test_banco_sem_a_tabela_nao_derruba_a_execucao(caplog):
    repositorio = RepositorioSemTabela([])

    cota = abrir_cota_da_adzuna(repositorio, AGORA)
    cota.reservar()
    registrar_uso_da_adzuna(repositorio, cota, AGORA)

    assert uso_da_adzuna(repositorio, AGORA) is None
    assert "uso_das_fontes" in caplog.text


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

    with pytest.raises(CotaDaAdzunaEsgotada):
        cota.reservar()


def test_reserva_do_diario_cobre_todas_as_paginas_de_cada_regiao_e_busca():
    no_rio = usuario_em("Rio de Janeiro, RJ", Modalidade.PRESENCIAL)
    remoto = usuario_em("Recife, PE", Modalidade.REMOTO, numero=2)
    sem_area = usuario_em("Recife, PE", Modalidade.REMOTO, curso="Curso Que Não Existe", numero=3)

    assert reserva_do_diario([no_rio, remoto]) == 20
    assert reserva_do_diario([no_rio, remoto, sem_area]) == 40
