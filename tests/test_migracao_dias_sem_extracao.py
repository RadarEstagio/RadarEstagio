from pathlib import Path

MIGRACAO = Path(__file__).parent.parent / "supabase/migrations/0022_dias_sem_extracao.sql"


def test_vaga_guarda_quantos_dias_ficou_sem_extracao_e_o_ultimo_deles():
    sql = MIGRACAO.read_text()

    assert "alter table public.vagas" in sql
    assert "add column dias_sem_extracao smallint not null default 0" in sql
    assert "check (dias_sem_extracao >= 0)" in sql
    assert "add column ultimo_dia_sem_extracao date" in sql
