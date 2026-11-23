from pathlib import Path

from radar.settings import FONTES_PADRAO, SEPARADOR_DE_FONTES

WORKFLOW = Path(__file__).parent.parent / ".github/workflows/radar-diario.yml"
NOME_DO_RUN_QUE_NAO_MOSTRA_O_PERFIL = (
    "run-name: ${{ inputs.perfil && 'Entrega imediata' || 'Radar diário' }}"
)


def test_execucoes_do_radar_esperam_a_anterior_em_vez_de_rodar_juntas():
    linhas = WORKFLOW.read_text().splitlines()
    inicio = linhas.index("concurrency:")

    assert linhas[inicio + 1 : inicio + 3] == [
        "  group: radar-diario",
        "  cancel-in-progress: false",
    ]
    assert inicio < linhas.index("jobs:")


def test_perfil_da_entrega_imediata_e_mascarado_no_primeiro_passo_do_job():
    conteudo = WORKFLOW.read_text()
    passos = conteudo.split("      - name: ")
    linhas_que_podem_mostrar_o_perfil = [
        linha for linha in conteudo.splitlines() if linha != NOME_DO_RUN_QUE_NAO_MOSTRA_O_PERFIL
    ]

    assert "::add-mask::" in passos[1]
    assert not any("${{ inputs." in linha for linha in linhas_que_podem_mostrar_o_perfil)
    assert 'rodar --perfil "$perfil"' in conteudo


def test_codigo_de_saida_do_radar_derruba_o_passo_e_dispara_o_aviso():
    conteudo = WORKFLOW.read_text()

    assert "continue-on-error" not in conteudo
    assert "|| true" not in conteudo
    assert "if: failure() || cancelled()" in conteudo


def variaveis_do_passo_do_radar() -> dict[str, str]:
    passo = next(
        passo
        for passo in WORKFLOW.read_text().split("      - name: ")
        if passo.startswith("Executar o radar")
    )
    linhas_do_env = passo.split("        env:\n")[1].splitlines()
    return {
        nome.strip(): valor.strip()
        for nome, _, valor in (linha.partition(":") for linha in linhas_do_env if linha.strip())
    }


def test_fontes_vem_de_variavel_do_repositorio_e_sem_ela_ficam_no_padrao_das_settings():
    padrao = SEPARADOR_DE_FONTES.join(FONTES_PADRAO)

    assert variaveis_do_passo_do_radar()["FONTES"] == f"${{{{ vars.FONTES || '{padrao}' }}}}"
    assert padrao == "adzuna"


def test_chave_da_jooble_chega_ao_radar_por_secret_e_nunca_por_variavel():
    conteudo = WORKFLOW.read_text()

    assert variaveis_do_passo_do_radar()["JOOBLE_API_KEY"] == "${{ secrets.JOOBLE_API_KEY }}"
    assert "vars.JOOBLE" not in conteudo
    assert conteudo.count("JOOBLE_API_KEY") == 2
