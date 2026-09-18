import logging
from uuid import UUID, uuid4

import pytest

from radar.domain.models import AreaDeInteresse
from radar.storage.postgres import converter_em_usuario, usuarios_das_linhas


def linha(
    curso: str,
    areas: list,
    pessoa_com_deficiencia: bool | None = None,
    habilidades: list | None = None,
) -> dict:
    return {
        "id": UUID(int=1),
        "curso": curso,
        "periodo": 3,
        "habilidades": ["Excel"] if habilidades is None else habilidades,
        "cidade": "Rio de Janeiro, RJ",
        "modalidade": "remoto",
        "areas_de_interesse": areas,
        "telegram_chat_id": "1",
        "sem_recomendacao_desde": None,
        "silencio_avisado_em": None,
        "pessoa_com_deficiencia": pessoa_com_deficiencia,
    }


def test_subarea_de_outro_campo_gravada_no_banco_e_ignorada_ao_carregar():
    usuario = converter_em_usuario(linha("Direito", ["desenvolvimento_web", "direito_contencioso"]))

    assert usuario.perfil.areas_de_interesse == [AreaDeInteresse.DIREITO_CONTENCIOSO]


def test_subareas_do_proprio_campo_sao_mantidas():
    usuario = converter_em_usuario(
        linha("Engenharia de Software", ["desenvolvimento_web", "dados_ia"])
    )

    assert usuario.perfil.areas_de_interesse == [
        AreaDeInteresse.DESENVOLVIMENTO_WEB,
        AreaDeInteresse.DADOS_IA,
    ]


def test_curso_sem_area_conhecida_carrega_sem_areas_de_interesse():
    usuario = converter_em_usuario(linha("Agronomia", ["desenvolvimento_web"]))

    assert usuario.perfil.areas_de_interesse == []


@pytest.mark.parametrize("resposta", [True, False, None])
def test_resposta_sobre_deficiencia_chega_ao_perfil_como_foi_gravada(resposta):
    usuario = converter_em_usuario(linha("Direito", [], pessoa_com_deficiencia=resposta))

    assert usuario.perfil.pessoa_com_deficiencia is resposta


@pytest.mark.parametrize(
    "ilegivel",
    [
        linha("Direito", [["direito_contencioso"], ["compliance"]]),
        linha("Direito", ["compliance"], habilidades=[["Excel", "Word"]]),
        linha("Direito", ["compliance"]) | {"modalidade": "hibrida"},
    ],
)
def test_linha_ilegivel_e_pulada_e_os_demais_usuarios_seguem(ilegivel):
    valida = linha("Direito", ["compliance"]) | {"id": uuid4()}

    usuarios = usuarios_das_linhas([ilegivel, valida])

    assert [usuario.id for usuario in usuarios] == [valida["id"]]


def test_linha_ilegivel_nao_leva_os_dados_do_perfil_para_o_log(caplog):
    with caplog.at_level(logging.WARNING):
        usuarios_das_linhas([linha("Direito", [["direito_contencioso"]])])

    assert "TypeError" in caplog.text
    assert "Direito" not in caplog.text
    assert "direito_contencioso" not in caplog.text
