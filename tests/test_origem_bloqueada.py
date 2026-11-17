from datetime import UTC, datetime

import pytest

from radar.domain.models import OrigemDoAnuncio, Vaga
from radar.filtering.origem import (
    MOTIVO_DE_CADA_DOMINIO_BLOQUEADO,
    descarte_sem_origem_generalizado,
    motivo_do_bloqueio,
    origem_bloqueada,
    origem_desconhecida,
    separar_as_de_origem_bloqueada,
    separar_as_sem_origem_identificada,
)


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
        origem=origem,
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


@pytest.mark.parametrize(
    "dominio",
    [
        "gupy.io",
        "empresa.gupy.io",
        "vagas.empresa.gupy.io",
        "GUPY.IO",
        "  gupy.io  ",
        "linkedin.com",
        "br.linkedin.com",
        "emprego.pt",
        "www.emprego.pt",
    ],
)
def test_dominio_bloqueado_vale_para_ele_e_para_os_subdominios(dominio: str):
    assert origem_bloqueada(OrigemDoAnuncio(dominio=dominio))


@pytest.mark.parametrize(
    "dominio",
    [
        "empregos.com.br",
        "infojobs.com.br",
        "pandape.com.br",
        "nube.com.br",
        "boards.greenhouse.io",
        "meugupy.io",
        "gupy.io.exemplo.com.br",
        "emprego.pt.exemplo.com.br",
        "",
        None,
    ],
)
def test_outro_dominio_nao_e_bloqueado_nem_o_que_so_contem_o_nome(dominio: str | None):
    assert not origem_bloqueada(OrigemDoAnuncio(dominio=dominio))


def test_cada_dominio_bloqueado_tem_o_motivo_escrito():
    assert set(MOTIVO_DE_CADA_DOMINIO_BLOQUEADO) == {"gupy.io", "linkedin.com", "emprego.pt"}
    assert all(motivo.strip() for motivo in MOTIVO_DE_CADA_DOMINIO_BLOQUEADO.values())


def test_motivo_do_bloqueio_e_o_do_dominio_ou_o_do_parceiro_da_adzuna():
    da_gupy = motivo_do_bloqueio(OrigemDoAnuncio(dominio="empresa.gupy.io"))
    do_linkedin = motivo_do_bloqueio(OrigemDoAnuncio(dominio="linkedin.com"))
    do_parceiro = motivo_do_bloqueio(OrigemDoAnuncio(parceiro="Emprego", id_do_parceiro="79986"))

    assert da_gupy == MOTIVO_DE_CADA_DOMINIO_BLOQUEADO["gupy.io"]
    assert do_linkedin == MOTIVO_DE_CADA_DOMINIO_BLOQUEADO["linkedin.com"]
    assert do_parceiro == MOTIVO_DE_CADA_DOMINIO_BLOQUEADO["emprego.pt"]
    assert motivo_do_bloqueio(OrigemDoAnuncio(dominio="empregos.com.br")) is None
    assert motivo_do_bloqueio(None) is None


def test_origem_so_com_o_dominio_conta_como_identificada():
    assert OrigemDoAnuncio(dominio="empregos.com.br").identificada()
    assert not OrigemDoAnuncio(dominio="").identificada()


def test_separa_pelo_dominio_e_mantem_as_de_dominio_permitido():
    da_gupy = vaga(1, OrigemDoAnuncio(dominio="gupy.io"))
    do_empregos = vaga(2, OrigemDoAnuncio(dominio="empregos.com.br"))
    do_linkedin = vaga(3, OrigemDoAnuncio(dominio="br.linkedin.com"))
    do_infojobs = vaga(4, OrigemDoAnuncio(dominio="infojobs.com.br"))

    seguem, bloqueadas = separar_as_de_origem_bloqueada(
        [da_gupy, do_empregos, do_linkedin, do_infojobs]
    )

    assert seguem == [do_empregos, do_infojobs]
    assert bloqueadas == [da_gupy, do_linkedin]


ORIGEM_PERMITIDA = OrigemDoAnuncio(parceiro="SourceStack", id_do_parceiro="506674")


def da_jooble(numero: int, origem: OrigemDoAnuncio | None) -> Vaga:
    return vaga(numero, origem).model_copy(update={"fonte": "jooble"})


@pytest.mark.parametrize("origem", [None, OrigemDoAnuncio()])
def test_vaga_da_adzuna_sem_parceiro_nem_identificador_tem_origem_desconhecida(origem):
    assert origem_desconhecida(vaga(1, origem))


@pytest.mark.parametrize(
    "origem",
    [
        ORIGEM_PERMITIDA,
        OrigemDoAnuncio(parceiro="Empregos"),
        OrigemDoAnuncio(id_do_parceiro="516421"),
    ],
)
def test_vaga_da_adzuna_com_parceiro_ou_identificador_tem_origem_conhecida(origem):
    assert not origem_desconhecida(vaga(1, origem))


def test_vaga_de_fonte_que_nao_exige_origem_nunca_tem_origem_desconhecida():
    assert not origem_desconhecida(da_jooble(1, None))
    assert not origem_desconhecida(da_jooble(2, OrigemDoAnuncio()))


def test_separa_as_vagas_da_adzuna_sem_origem_e_mantem_a_ordem():
    sem_pagina = vaga(1, None)
    permitida = vaga(2, ORIGEM_PERMITIDA)
    sem_logo = vaga(3, OrigemDoAnuncio())
    jooble = da_jooble(4, None)

    seguem, sem_origem = separar_as_sem_origem_identificada(
        [sem_pagina, permitida, sem_logo, jooble]
    )

    assert seguem == [permitida, jooble]
    assert sem_origem == [sem_pagina, sem_logo]


@pytest.mark.parametrize(
    ("sem_origem", "com_origem", "generalizado"),
    [(0, 0, False), (0, 3, False), (1, 1, False), (1, 0, True), (2, 1, True), (2, 2, False)],
)
def test_descarte_generalizado_e_mais_da_metade_das_que_exigem_origem(
    sem_origem: int, com_origem: int, generalizado: bool
):
    descartadas = [vaga(numero, None) for numero in range(sem_origem)]
    vagas = descartadas + [vaga(100 + numero, ORIGEM_PERMITIDA) for numero in range(com_origem)]

    assert descarte_sem_origem_generalizado(descartadas, vagas) is generalizado


def test_vaga_de_fonte_que_nao_exige_origem_nao_dilui_o_descarte_generalizado():
    descartada = vaga(1, None)
    vagas = [descartada, *(da_jooble(numero, None) for numero in range(2, 6))]

    assert descarte_sem_origem_generalizado([descartada], vagas)
