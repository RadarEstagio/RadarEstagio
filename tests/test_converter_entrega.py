from datetime import UTC, datetime
from uuid import UUID

from radar.domain.models import AreaDeInteresse, Modalidade
from radar.storage.postgres import converter_em_entrega


def linha(**alteracoes) -> dict:
    base = {
        "perfil_id": UUID(int=1),
        "enviada_em": datetime(2026, 9, 9, 10, 23, tzinfo=UTC),
        "curso": "Engenharia de Software",
        "periodo": 4,
        "habilidades": ["Python"],
        "cidade": "Rio de Janeiro, RJ",
        "modalidade_do_perfil": "hibrido",
        "areas_de_interesse": ["dados_ia", "direito_contencioso"],
        "fonte": "adzuna",
        "id_externo": "123",
        "titulo": "Estágio",
        "empresa": "Empresa",
        "localizacao": "Rio de Janeiro, RJ",
        "descricao": "d",
        "url": "https://exemplo.com/123",
        "publicada_em": datetime(2026, 9, 8, tzinfo=UTC),
        "modalidade": "remoto",
        "nota": 77,
        "feedback": "vaga_util",
        "motivo_do_feedback": None,
    }
    base.update(alteracoes)
    return base


def test_converte_linha_do_banco_em_entrega_para_julgar():
    entrega = converter_em_entrega(linha())

    assert entrega.perfil.curso == "Engenharia de Software"
    assert entrega.perfil.modalidade is Modalidade.HIBRIDO
    assert entrega.perfil.areas_de_interesse == [AreaDeInteresse("dados_ia")]
    assert entrega.vaga.id_externo == "123"
    assert entrega.vaga.modalidade is Modalidade.REMOTO
    assert entrega.nota_do_radar == 77
    assert entrega.feedback == "vaga_util"


def test_entrega_sem_avaliacao_nem_feedback_aceita_nulos():
    entrega = converter_em_entrega(linha(nota=None, feedback=None, modalidade=None, habilidades=[]))

    assert entrega.nota_do_radar is None
    assert entrega.feedback is None
    assert entrega.vaga.modalidade is None
    assert entrega.perfil.habilidades == []
