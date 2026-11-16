from datetime import UTC, datetime

import pytest

from radar.domain.models import OrigemDoAnuncio, Vaga
from radar.filtering.origem import origem_bloqueada, separar_as_de_origem_bloqueada


def vaga(numero: int, origem: OrigemDoAnuncio | None) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo="Estágio Python",
        empresa=f"Empresa {numero}",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url=f"https://www.adzuna.com.br/details/{numero}",
        publicada_em=datetime(2026, 11, 15, tzinfo=UTC),
        origem_lida_da_pagina=origem,
    )


@pytest.mark.parametrize(
    "origem",
    [
        OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="79986"),
        OrigemDoAnuncio(id_do_parceiro="79986"),
        OrigemDoAnuncio(parceiro="Outro nome", id_do_parceiro="79986"),
        OrigemDoAnuncio(id_do_parceiro=" 79986 "),
        OrigemDoAnuncio(parceiro="Emprego"),
        OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="1"),
        OrigemDoAnuncio(parceiro="  emprego  "),
        OrigemDoAnuncio(parceiro="EMPREGO"),
    ],
)
def test_anuncio_do_emprego_pt_e_bloqueado_pelo_identificador_ou_pelo_nome(
    origem: OrigemDoAnuncio,
):
    assert origem_bloqueada(origem)


@pytest.mark.parametrize(
    "origem",
    [
        OrigemDoAnuncio(parceiro="Empregos"),
        OrigemDoAnuncio(parceiro="Empregos", id_do_parceiro="1"),
        OrigemDoAnuncio(parceiro="empregos"),
        OrigemDoAnuncio(parceiro="SourceStack", id_do_parceiro="506674"),
        OrigemDoAnuncio(parceiro="Divulgar Vagas"),
        OrigemDoAnuncio(id_do_parceiro="799860"),
        OrigemDoAnuncio(id_do_parceiro="7998"),
    ],
)
def test_outro_parceiro_nao_e_bloqueado_nem_o_empregos_de_nome_parecido(
    origem: OrigemDoAnuncio,
):
    assert not origem_bloqueada(origem)


@pytest.mark.parametrize("origem", [None, OrigemDoAnuncio()])
def test_vaga_sem_origem_identificada_nao_e_bloqueada(origem: OrigemDoAnuncio | None):
    assert not origem_bloqueada(origem)


def test_separa_as_bloqueadas_mantendo_a_ordem_das_que_seguem():
    do_emprego_pt = vaga(1, OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="79986"))
    sem_pagina = vaga(2, None)
    do_empregos = vaga(3, OrigemDoAnuncio(parceiro="Empregos"))
    so_com_o_id = vaga(4, OrigemDoAnuncio(id_do_parceiro="79986"))
    sem_origem = vaga(5, OrigemDoAnuncio())

    seguem, bloqueadas = separar_as_de_origem_bloqueada(
        [do_emprego_pt, sem_pagina, do_empregos, so_com_o_id, sem_origem]
    )

    assert seguem == [sem_pagina, do_empregos, sem_origem]
    assert bloqueadas == [do_emprego_pt, so_com_o_id]
