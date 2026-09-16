from uuid import UUID

import pytest

from radar.domain.models import AreaDeInteresse
from radar.storage.postgres import converter_em_usuario


def linha(curso: str, areas: list[str], pessoa_com_deficiencia: bool | None = None) -> dict:
    return {
        "id": UUID(int=1),
        "curso": curso,
        "periodo": 3,
        "habilidades": ["Excel"],
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
