from uuid import UUID

from radar.domain.models import AreaDeInteresse
from radar.storage.postgres import converter_em_usuario


def linha(curso: str, areas: list[str]) -> dict:
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
