import re
from pathlib import Path

from radar.domain.areas import SUBAREAS

MIGRACOES = Path(__file__).parent.parent / "supabase/migrations"
MIGRACAO = MIGRACOES / "0017_areas_de_todos_os_cursos.sql"
DEFINICAO_DA_VALIDACAO = "function public.validar_cadastro_radar"
LISTA_DE_SUBAREAS = "where area not in ("


def valores_citados(trecho: str) -> set[str]:
    return set(re.findall(r"'([a-z_]+)'", trecho))


def test_a_restricao_do_banco_aceita_exatamente_as_subareas_do_codigo():
    sql = MIGRACAO.read_text()
    restricao = sql[sql.index("areas_de_interesse <@ array[") : sql.index("]::text[]")]

    assert valores_citados(restricao) == set(SUBAREAS)


def migracoes_que_definem_a_validacao() -> list[Path]:
    return [
        caminho
        for caminho in sorted(MIGRACOES.glob("*.sql"))
        if DEFINICAO_DA_VALIDACAO in caminho.read_text()
    ]


def test_a_versao_vigente_da_validacao_do_cadastro_aceita_exatamente_as_subareas_do_codigo():
    vigente = migracoes_que_definem_a_validacao()[-1]
    sql = vigente.read_text()

    assert vigente.name >= MIGRACAO.name
    validacao = sql[sql.index(LISTA_DE_SUBAREAS) : sql.index("raise exception 'habilidades")]
    assert valores_citados(validacao) == set(SUBAREAS), vigente.name


def test_toda_area_conhecida_tem_ao_menos_uma_subarea():
    from radar.domain.areas import AREAS

    assert all(area.subareas for area in AREAS)
    assert len(SUBAREAS) == len(set(SUBAREAS))
