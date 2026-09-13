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
