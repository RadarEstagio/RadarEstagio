import re
from pathlib import Path

MIGRACOES = Path(__file__).parent.parent / "supabase/migrations"
MIGRACAO = MIGRACOES / "0021_entrega_imediata_unica.sql"
COLUNA = "entrega_imediata_disparada_em"
COLUNAS_QUE_O_SITE_EDITA = (
    "curso",
    "periodo",
    "habilidades",
    "cidade",
    "modalidade",
    "areas_de_interesse",
    "ativo",
    "motivo_pausa",
    "aceita_emails",
    "atualizado_em",
)
GRANT_POR_COLUNA_EM_PERFIS = re.compile(
    r"grant\s+(?:insert|update)\s*\(([^)]*)\)\s*on\s+(?:table\s+)?(?:public\.)?perfis\s+to\s+([^;]+);",
    re.IGNORECASE,
)


def test_marca_da_entrega_imediata_nasce_nula():
    sql = MIGRACAO.read_text()

    assert f"add column {COLUNA} timestamptz;" in sql


def test_quem_ja_vinculou_ou_ja_recebeu_nao_dispara_de_novo():
    sql = MIGRACAO.read_text()
    backfill = sql.split("update public.perfis")[1].split(";")[0]

    assert f"set {COLUNA} = now()" in backfill
    assert "telegram_chat_id is not null" in backfill
    assert "ativado_em is not null" in backfill
    assert "evento.nome = 'telegram_vinculado'" in backfill


def test_navegador_perde_escrita_de_tabela_inteira_em_perfis():
    sql = MIGRACAO.read_text()

    assert "revoke insert, update on table public.perfis from public, anon, authenticated;" in sql


def test_navegador_continua_editando_so_o_que_ja_editava():
    sql = MIGRACAO.read_text()
    colunas, papeis = GRANT_POR_COLUNA_EM_PERFIS.search(sql).groups()

    assert tuple(coluna.strip() for coluna in colunas.split(",")) == COLUNAS_QUE_O_SITE_EDITA
    assert papeis.strip() == "authenticated"


def test_nenhuma_migration_concede_a_marca_ao_navegador():
    for migracao in sorted(MIGRACOES.glob("*.sql")):
        for colunas, _ in GRANT_POR_COLUNA_EM_PERFIS.findall(migracao.read_text()):
            assert COLUNA not in colunas, migracao.name
