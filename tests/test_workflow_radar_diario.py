from pathlib import Path

WORKFLOW = Path(__file__).parent.parent / ".github/workflows/radar-diario.yml"


def test_execucoes_do_radar_esperam_a_anterior_em_vez_de_rodar_juntas():
    linhas = WORKFLOW.read_text().splitlines()
    inicio = linhas.index("concurrency:")

    assert linhas[inicio + 1 : inicio + 3] == [
        "  group: radar-diario",
        "  cancel-in-progress: false",
    ]
    assert inicio < linhas.index("jobs:")


def test_codigo_de_saida_do_radar_derruba_o_passo_e_dispara_o_aviso():
    conteudo = WORKFLOW.read_text()

    assert "continue-on-error" not in conteudo
    assert "|| true" not in conteudo
    assert "if: failure() || cancelled()" in conteudo
