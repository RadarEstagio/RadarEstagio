from pathlib import Path

from tests.test_migracao_entrega_imediata import GRANT_POR_COLUNA_EM_PERFIS

MIGRACOES = Path(__file__).parent.parent / "supabase/migrations"
MIGRACAO = MIGRACOES / "0036_ultimo_dia_atendido.sql"


def test_perfil_guarda_o_ultimo_dia_de_brasilia_em_que_foi_atendido():
    sql = MIGRACAO.read_text()

    assert "alter table public.perfis" in sql
    assert "add column ultimo_dia_atendido date;" in sql


def test_nenhuma_migration_concede_o_dia_do_atendimento_ao_navegador():
    for migracao in sorted(MIGRACOES.glob("*.sql")):
        for colunas, _ in GRANT_POR_COLUNA_EM_PERFIS.findall(migracao.read_text()):
            assert "ultimo_dia_atendido" not in colunas, migracao.name
