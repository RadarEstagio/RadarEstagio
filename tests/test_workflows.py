import re
from itertools import takewhile
from pathlib import Path

PASTA_DOS_WORKFLOWS = Path(__file__).parent.parent / ".github/workflows"

VERSAO_DE_CADA_ACAO = {
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1": "v7",
    "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d": "v10.0.1",
    "denoland/setup-deno@22d081ff2d3a40755e97629de92e3bcbfa7cf2ed": "v2.0.5",
}

LINHA_COM_USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(.*?)\s*$")
ACAO_FIXADA_POR_HASH = re.compile(r"[\w.-]+/[\w.-]+(?:/[\w./-]+)?@[0-9a-f]{40}")
ACAO_LOCAL = re.compile(r"\./[\w./-]+")
VERSAO_FIXA = re.compile(r"\d+\.\d+\.\d+")
NIVEIS_SO_DE_LEITURA = {"read", "none"}


def workflows():
    return sorted([*PASTA_DOS_WORKFLOWS.glob("*.yml"), *PASTA_DOS_WORKFLOWS.glob("*.yaml")])


def acoes_usadas(workflow):
    return [
        encontrada.group(1).strip("\"'")
        for linha in workflow.read_text().splitlines()
        if (encontrada := LINHA_COM_USES.match(linha))
    ]


def permissoes_do_topo(workflow):
    linhas = workflow.read_text().splitlines()
    if "permissions:" not in linhas:
        return {}
    depois_do_bloco = linhas[linhas.index("permissions:") + 1 :]
    bloco = takewhile(lambda linha: linha.startswith("  "), depois_do_bloco)
    return dict(linha.strip().split(": ", 1) for linha in bloco)


def recuo(linha):
    return len(linha) - len(linha.lstrip())


def entradas_do_passo(passo, coluna):
    linha_do_with = " " * coluna + "with:"
    if linha_do_with not in passo:
        return {}
    depois_do_with = passo[passo.index(linha_do_with) + 1 :]
    bloco = takewhile(lambda seguinte: recuo(seguinte) > coluna, depois_do_with)
    return {
        nome: valor.strip().strip("\"'")
        for nome, _, valor in (entrada.strip().partition(":") for entrada in bloco)
    }


def entradas_de_cada_uso(workflow, acao):
    linhas = workflow.read_text().splitlines()
    usos = []
    for indice, linha in enumerate(linhas):
        encontrada = LINHA_COM_USES.match(linha)
        if not (encontrada and encontrada.group(1).startswith(f"{acao}@")):
            continue
        coluna = linha.index("uses:")
        inicio = max(i for i in range(indice + 1) if linhas[i][coluna - 2 : coluna] == "- ")
        depois_do_uses = range(indice + 1, len(linhas))
        fim = next(
            (i for i in depois_do_uses if linhas[i].strip() and recuo(linhas[i]) < coluna),
            len(linhas),
        )
        usos.append(entradas_do_passo(linhas[inicio:fim], coluna))
    return usos


def test_toda_acao_de_terceiros_e_fixada_pelo_hash_do_commit():
    fora_da_regra = [
        f"{workflow.name}: {acao}"
        for workflow in workflows()
        for acao in acoes_usadas(workflow)
        if not (ACAO_FIXADA_POR_HASH.fullmatch(acao) or ACAO_LOCAL.fullmatch(acao))
    ]

    assert fora_da_regra == []


def test_todo_hash_usado_tem_a_versao_registrada_e_nenhum_registro_sobra():
    fixadas = {
        acao
        for workflow in workflows()
        for acao in acoes_usadas(workflow)
        if ACAO_FIXADA_POR_HASH.fullmatch(acao)
    }

    assert fixadas == set(VERSAO_DE_CADA_ACAO)


def test_todo_workflow_declara_no_topo_o_github_token_so_de_leitura():
    fora_da_regra = {
        workflow.name: permissoes
        for workflow in workflows()
        if not (permissoes := permissoes_do_topo(workflow))
        or set(permissoes.values()) - NIVEIS_SO_DE_LEITURA
    }

    assert fora_da_regra == {}


def test_checkout_de_workflow_com_segredos_nao_deixa_o_token_no_git():
    persistencia_de_cada_checkout = {
        f"{workflow.name} #{posicao}": entradas.get("persist-credentials")
        for workflow in workflows()
        if "secrets." in workflow.read_text()
        for posicao, entradas in enumerate(entradas_de_cada_uso(workflow, "actions/checkout"), 1)
    }

    assert persistencia_de_cada_checkout
    assert {
        checkout: persistencia
        for checkout, persistencia in persistencia_de_cada_checkout.items()
        if persistencia != "false"
    } == {}


def test_setup_uv_instala_um_numero_fixo_de_versao_do_uv():
    versao_de_cada_setup_uv = {
        f"{workflow.name} #{posicao}": entradas.get("version")
        for workflow in workflows()
        for posicao, entradas in enumerate(entradas_de_cada_uso(workflow, "astral-sh/setup-uv"), 1)
    }

    assert versao_de_cada_setup_uv
    assert {
        setup_uv: versao
        for setup_uv, versao in versao_de_cada_setup_uv.items()
        if not VERSAO_FIXA.fullmatch(versao or "")
    } == {}


def test_dependabot_propoe_em_pr_as_versoes_novas_das_acoes_depois_de_uma_espera():
    dependabot = PASTA_DOS_WORKFLOWS.parent / "dependabot.yml"

    assert dependabot.exists()
    linhas = [linha.strip() for linha in dependabot.read_text().splitlines()]
    assert '- package-ecosystem: "github-actions"' in linhas
    assert 'directory: "/"' in linhas
    assert "cooldown:" in linhas
