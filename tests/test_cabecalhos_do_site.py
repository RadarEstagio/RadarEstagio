from pathlib import Path

RAIZ = Path(__file__).parent.parent

CABECALHOS_DE_TODA_ROTA = {
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "content-security-policy": "frame-ancestors 'none'",
}


def regras_do_arquivo_de_cabecalhos() -> dict[str, dict[str, str]]:
    regras: dict[str, dict[str, str]] = {}
    rota = ""
    for linha in (RAIZ / "web/_headers").read_text().splitlines():
        if not linha.strip():
            continue
        if not linha.startswith((" ", "\t")):
            rota = linha.strip()
            regras[rota] = {}
            continue
        nome, separador, valor = linha.partition(":")
        assert separador, linha
        regras[rota][nome.strip().lower()] = valor.strip()
    return regras


def test_o_site_manda_os_cabecalhos_de_seguranca_em_toda_rota():
    regras = regras_do_arquivo_de_cabecalhos()

    assert list(regras) == ["/*"]
    assert regras["/*"] == CABECALHOS_DE_TODA_ROTA


def test_o_site_segue_sem_hsts_enquanto_a_decisao_registrada_for_essa():
    for cabecalhos in regras_do_arquivo_de_cabecalhos().values():
        assert "strict-transport-security" not in cabecalhos
