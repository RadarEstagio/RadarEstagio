import re
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


def test_troca_de_tema_desliga_as_transicoes_ate_o_estilo_novo_assentar():
    css = ler_css()
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert ".sem-transicao *:not(.theme-icon-sun, .theme-icon-moon)" in css
    assert "transition: none !important" in css
    assert 'raiz.classList.add("sem-transicao");' in javascript
    assert "void raiz.offsetHeight;" in javascript
    assert 'raiz.classList.remove("sem-transicao")' in javascript
    assert "trocarTemaSemTransicao(tema);" in javascript


def test_icones_que_trocam_de_estado_fazem_cross_fade_em_vez_de_sumir_por_display():
    css = ler_css()

    assert ".theme-toggle svg { grid-area: 1 / 1;" in css
    assert (
        ':root:not([data-tema="escuro"]) .theme-icon-moon { opacity: 0; scale: .25; '
        "filter: blur(4px); }" in css
    )
    assert ".theme-icon-moon { display: none; }" not in css
    assert '.faq-list summary::before { content: "+"; }' in css
    assert '.faq-list summary::after { content: "\\00d7";' in css
    assert ".faq-list details[open] summary::before { opacity: 0; scale: .25;" in css
    assert ".faq-list details[open] summary::after { opacity: 1; scale: 1;" in css


def test_profundidade_vem_do_anel_de_sombra_e_nao_de_borda_com_cor_fixa():
    css = ler_css()
    tema_escuro = css[css.index(':root[data-tema="escuro"] {') : css.index("* { box-sizing")]

    assert "--shadow-border: 0 0 0 1px oklch(0 0 0 / 0.06)," in css
    assert "--shadow-border: 0 0 0 1px oklch(1 0 0 / 0.08);" in tema_escuro
    assert "rgba(23, 32, 26, 0.08)" not in css
    assert "rgba(23, 32, 26, .1)" not in css
    for seletor in (".benefit-card", ".area-tile", ".how-layout", ".account-row"):
        inicio = re.search(rf"^{re.escape(seletor)} \{{", css, re.MULTILINE).start()
        regra = css[inicio:].split("}", 1)[0]
        assert "border: 1px solid transparent;" in regra, seletor
        assert "var(--shadow-border)" in regra, seletor


def test_alto_contraste_devolve_a_borda_aos_cards_que_perderam_a_cor():
    css = ler_css()
    alto_contraste = css[css.index("@media (forced-colors: active) {") :].split("\n}", 1)[0]

    for seletor in (".telegram-chat", ".area-tile", ".benefit-card", ".how-layout", ".account-row"):
        assert seletor in alto_contraste, seletor
    assert "border-color: CanvasText;" in alto_contraste


def raio_da_regra(css: str, seletor: str) -> int:
    inicio = re.search(rf"^{re.escape(seletor)} \{{", css, re.MULTILINE).start()
    regra = css[inicio:].split("}", 1)[0]
    return int(re.search(r"border-radius: (\d+)px", regra).group(1))


def test_raio_interno_e_o_externo_menos_o_recuo_nas_listas_e_nos_campos():
    css = ler_css()

    assert raio_da_regra(css, ".combobox-options") == 12
    assert raio_da_regra(css, ".combobox-options li") == 12 - 6
    assert raio_da_regra(css, ".field input, .field select") == 12
    assert raio_da_regra(css, ".password-toggle") == 12 - 4
    assert raio_da_regra(css, ".combobox-toggle") == 12 - 4


def test_icones_decorativos_sao_svg_com_a_cor_do_texto_e_nao_glifos_de_fonte():
    html = (RAIZ / "web/index.html").read_text()
    css = ler_css()

    for glifo in "⌁✦↗":
        assert glifo not in html, glifo
    assert html.count('class="card-icon" aria-hidden="true"><svg') == 3
    assert '<span aria-hidden="true">✓</span>' not in html
    assert '<div class="success-icon" aria-hidden="true"><svg' in html
    assert 'aria-label="Fechar cadastro"><svg' in html
    assert 'aria-label="Fechar confirmação"><svg' in html
    for seletor in (".card-icon svg", ".trust-list svg", ".plan li svg"):
        inicio = re.search(rf"^{re.escape(seletor)} \{{", css, re.MULTILINE).start()
        assert "stroke: currentColor;" in css[inicio:].split("}", 1)[0], seletor
    assert ".success-icon svg { width: 24px; height: 24px; fill: none; stroke: currentColor;" in css
