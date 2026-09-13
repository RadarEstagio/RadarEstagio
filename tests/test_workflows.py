import re
from itertools import takewhile
from pathlib import Path

import pytest

PASTA_DOS_WORKFLOWS = Path(__file__).parent.parent / ".github/workflows"

VERSAO_DE_CADA_ACAO = {
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1": "v7.0.1",
    "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020": "v7.0.0",
    "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a": "v7.0.1",
    "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d": "v10.0.1",
    "denoland/setup-deno@22d081ff2d3a40755e97629de92e3bcbfa7cf2ed": "v2.0.5",
}

LINHA_COM_USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(.*?)\s*$")
ACAO_FIXADA_POR_HASH = re.compile(r"[\w.-]+/[\w.-]+(?:/[\w./-]+)?@[0-9a-f]{40}")
ACAO_LOCAL = re.compile(r"\./[\w./-]+")
VERSAO_FIXA = re.compile(r"\d+\.\d+\.\d+")
NIVEIS_SO_DE_LEITURA = {"read", "none"}
PERMISSOES_EM_LINHA_SO_DE_LEITURA = {"read-all", "{}"}


def workflows():
    return sorted([*PASTA_DOS_WORKFLOWS.glob("*.yml"), *PASTA_DOS_WORKFLOWS.glob("*.yaml")])


def sem_aspas(valor):
    return valor.strip().strip("\"'")


def acao_da_linha(linha):
    encontrada = LINHA_COM_USES.match(linha)
    return sem_aspas(encontrada.group(1)) if encontrada else None


def acoes_usadas(workflow):
    return [
        acao
        for linha in workflow.read_text().splitlines()
        if (acao := acao_da_linha(linha)) is not None
    ]


def permissoes_do_topo(workflow):
    linhas = workflow.read_text().splitlines()
    linha_do_topo = next((linha for linha in linhas if linha.startswith("permissions:")), None)
    if linha_do_topo is None:
        return None
    em_linha = sem_aspas(linha_do_topo.removeprefix("permissions:"))
    if em_linha:
        return em_linha
    depois_do_bloco = linhas[linhas.index(linha_do_topo) + 1 :]
    bloco = takewhile(lambda linha: linha.startswith("  "), depois_do_bloco)
    return {
        nome.strip(): sem_aspas(nivel)
        for nome, _, nivel in (linha.partition(":") for linha in bloco)
    }


def github_token_so_de_leitura(workflow):
    permissoes = permissoes_do_topo(workflow)
    if isinstance(permissoes, str):
        return permissoes in PERMISSOES_EM_LINHA_SO_DE_LEITURA
    return bool(permissoes) and set(permissoes.values()) <= NIVEIS_SO_DE_LEITURA


def recuo(linha):
    return len(linha) - len(linha.lstrip())


def entradas_do_passo(passo, coluna):
    linha_do_with = " " * coluna + "with:"
    if linha_do_with not in passo:
        return {}
    depois_do_with = passo[passo.index(linha_do_with) + 1 :]
    bloco = takewhile(lambda seguinte: recuo(seguinte) > coluna, depois_do_with)
    return {
        nome: sem_aspas(valor)
        for nome, _, valor in (entrada.strip().partition(":") for entrada in bloco)
    }


def entradas_de_cada_uso(workflow, acao):
    linhas = workflow.read_text().splitlines()
    usos = []
    for indice, linha in enumerate(linhas):
        usada = acao_da_linha(linha)
        if not (usada and usada.startswith(f"{acao}@")):
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


def acoes_fora_da_regra(workflow):
    return [
        acao
        for acao in acoes_usadas(workflow)
        if not (ACAO_FIXADA_POR_HASH.fullmatch(acao) or ACAO_LOCAL.fullmatch(acao))
    ]


def test_toda_acao_de_terceiros_e_fixada_pelo_hash_do_commit():
    fora_da_regra = [
        f"{workflow.name}: {acao}"
        for workflow in workflows()
        for acao in acoes_fora_da_regra(workflow)
    ]

    assert fora_da_regra == []


@pytest.mark.parametrize("aspas", ['"', "'"])
def test_uses_entre_aspas_vale_como_a_forma_sem_aspas(tmp_path, aspas):
    fixada = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    workflow = tmp_path / "exemplo.yml"
    workflow.write_text(
        "jobs:\n  a:\n    steps:\n"
        f"      - uses: {aspas}{fixada}{aspas}\n"
        "        with:\n"
        "          persist-credentials: false\n"
        f"      - uses: {aspas}actions/checkout@v7{aspas}\n"
    )

    assert acoes_fora_da_regra(workflow) == ["actions/checkout@v7"]
    assert entradas_de_cada_uso(workflow, "actions/checkout") == [
        {"persist-credentials": "false"},
        {},
    ]


def test_todo_hash_usado_tem_a_versao_registrada_e_nenhum_registro_sobra():
    fixadas = {
        acao
        for workflow in workflows()
        for acao in acoes_usadas(workflow)
        if ACAO_FIXADA_POR_HASH.fullmatch(acao)
    }

    assert fixadas == set(VERSAO_DE_CADA_ACAO)


def test_versao_registrada_de_cada_hash_e_a_tag_exata_que_nao_se_move():
    tags_que_se_movem = [
        versao
        for versao in VERSAO_DE_CADA_ACAO.values()
        if not VERSAO_FIXA.fullmatch(versao.removeprefix("v"))
    ]

    assert tags_que_se_movem == []


def test_todo_workflow_declara_no_topo_o_github_token_so_de_leitura():
    fora_da_regra = [
        workflow.name for workflow in workflows() if not github_token_so_de_leitura(workflow)
    ]

    assert fora_da_regra == []


@pytest.mark.parametrize(
    ("permissoes", "so_de_leitura"),
    [
        ("permissions:\n  contents: read\n", True),
        ('permissions:\n  contents: "read"\n', True),
        ("permissions:\n  contents: 'read'\n  actions: none\n", True),
        ("permissions: read-all\n", True),
        ("permissions: {}\n", True),
        ("permissions: write-all\n", False),
        ("permissions:\n  contents: write\n", False),
        ('permissions:\n  contents: "write"\n', False),
        ("permissions:\n  contents: read\n  id-token: write\n", False),
        ("permissions:\n", False),
        ("", False),
    ],
)
def test_so_leitura_no_topo_aceita_as_formas_de_leitura_e_recusa_escrita(
    tmp_path, permissoes, so_de_leitura
):
    workflow = tmp_path / "exemplo.yml"
    workflow.write_text(f"on: push\n\n{permissoes}\njobs:\n  a:\n    runs-on: ubuntu-latest\n")

    assert github_token_so_de_leitura(workflow) is so_de_leitura


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
    assert "groups:" in linhas
