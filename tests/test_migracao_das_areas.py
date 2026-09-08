import re
from pathlib import Path

from radar.domain.areas import SUBAREAS

MIGRACAO = Path(__file__).parent.parent / "supabase/migrations/0017_areas_de_todos_os_cursos.sql"


def valores_citados(trecho: str) -> set[str]:
    return set(re.findall(r"'([a-z_]+)'", trecho))


def test_a_restricao_do_banco_aceita_exatamente_as_subareas_do_codigo():
    sql = MIGRACAO.read_text()
    restricao = sql[sql.index("areas_de_interesse <@ array[") : sql.index("]::text[]")]

    assert valores_citados(restricao) == set(SUBAREAS)


def test_a_validacao_do_cadastro_aceita_exatamente_as_subareas_do_codigo():
    sql = MIGRACAO.read_text()
    validacao = sql[sql.index("where area not in (") : sql.index("raise exception 'habilidades")]

    assert valores_citados(validacao) == set(SUBAREAS)


def test_toda_area_conhecida_tem_ao_menos_uma_subarea():
    from radar.domain.areas import AREAS

    assert all(area.subareas for area in AREAS)
    assert len(SUBAREAS) == len(set(SUBAREAS))
