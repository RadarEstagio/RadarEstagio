from pathlib import Path

RAIZ = Path(__file__).parent.parent
ABERTURA_DO_BLOCO_DE_HOVER = "@media (hover: hover) {"


def ler_css() -> str:
    return (RAIZ / "web/assets/styles.css").read_text()


def sem_blocos_de_hover(css: str) -> str:
    resto = css
    while ABERTURA_DO_BLOCO_DE_HOVER in resto:
        inicio = resto.index(ABERTURA_DO_BLOCO_DE_HOVER)
        fim = inicio + len(ABERTURA_DO_BLOCO_DE_HOVER)
        profundidade = 1
        while profundidade:
            profundidade += {"{": 1, "}": -1}.get(resto[fim], 0)
            fim += 1
        resto = resto[:inicio] + resto[fim:]
    return resto


def test_botao_afunda_ao_ser_pressionado():
    css = ler_css()

    assert ".button:active:not(:disabled) { scale: .96; }" in css


def test_botao_transiciona_so_o_que_muda_e_inclui_a_borda():
    css = ler_css()

    assert (
        "transition-property: transform, scale, background-color, border-color, box-shadow;" in css
    )
    assert "background 160ms ease" not in css
    assert "transition: all" not in css


def test_hover_so_vale_onde_o_ponteiro_paira_para_nao_ficar_preso_no_toque():
    fora_dos_blocos = sem_blocos_de_hover(ler_css())

    assert ":hover" not in fora_dos_blocos


def test_link_de_texto_responde_ao_hover_com_a_cor_da_propria_letra():
    css = ler_css()

    assert ".text-link:hover { border-bottom-color: currentColor; }" in css
