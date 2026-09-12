from pathlib import Path

RAIZ = Path(__file__).parent.parent


def test_nenhum_arquivo_de_rotulagem_fica_na_pasta_de_documentos():
    assert list((RAIZ / "docs").glob("gabarito-*.json")) == []
    assert list((RAIZ / "docs").glob("descartes-*.json")) == []


def test_git_ignora_os_arquivos_de_rotulagem():
    ignorados = (RAIZ / ".gitignore").read_text().splitlines()

    for padrao in ("gabaritos/", "gabarito-*.json", "descartes-*.json"):
        assert padrao in ignorados
