from pathlib import Path

MIGRACAO = Path(__file__).parent.parent / "supabase/migrations/0020_uso_das_fontes.sql"


def test_uso_das_fontes_e_privado_e_somado_por_fonte_e_dia():
    sql = MIGRACAO.read_text()

    assert "create table public.uso_das_fontes" in sql
    assert "primary key (fonte, dia)" in sql
    assert "check (requisicoes >= 0)" in sql
    assert "alter table public.uso_das_fontes enable row level security;" in sql
    assert "revoke all on public.uso_das_fontes from public, anon, authenticated;" in sql
