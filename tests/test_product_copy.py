import re
from pathlib import Path

RAIZ = Path(__file__).parent.parent


def test_landing_exibe_promessa_multiarea_limite_canal_e_condicao_do_piloto():
    html = (RAIZ / "web/index.html").read_text()
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert '<span class="hero-title-primary">Cansado de procurar estágio?</span>' in html
    assert '<span class="hero-title-secondary">Nós levamos ele até você.</span>' in html
    assert ".hero-title-primary { color: var(--ink); }" in css
    assert ".hero-title-secondary { color: var(--accent-emphasis); }" in css
    assert "diferentes áreas" in html
    assert "até sete recomendações explicadas no Telegram" in html
    assert "100% automático" in html
    assert "Vagas que atendem seu perfil" in html
    assert "Pare de procurar estágio" not in html
    assert "A IA compara" not in html


def test_landing_atualiza_metadados_sociais_para_a_promessa_real():
    html = (RAIZ / "web/index.html").read_text()

    assert '<meta name="twitter:card" content="summary_large_image" />' in html
    assert html.count("até sete recomendações explicadas no Telegram") >= 3
    assert "As vagas certas chegam até você" not in html


def test_demo_da_landing_e_identificada_e_repete_o_formato_da_entrega():
    html = (RAIZ / "web/index.html").read_text()
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert "exemplo ilustrativo" in html.lower()
    assert "não é uma vaga real" in html.lower()
    assert "Nota 83/100" in html
    assert "Requisitos atendidos:" in html
    assert "Requisitos a conferir no seu perfil:" in html
    assert ">match<" not in html.lower()
    assert (
        ".chat-message-kicker span { color: var(--muted); font-size: 8px; font-weight: 500;" in css
    )


def test_demo_do_chat_respeita_preferencia_de_movimento_reduzido():
    css = (RAIZ / "web/assets/styles.css").read_text()

    regra_reduzida = css[css.index("@media (prefers-reduced-motion: reduce)") :]
    assert "animation-delay: 0ms !important" in regra_reduzida
    assert ".chat-typing { display: none; }" in regra_reduzida


def test_demo_do_chat_aguarda_rolagem_enquanto_exibe_digitacao():
    html = (RAIZ / "web/index.html").read_text()
    css = (RAIZ / "web/assets/styles.css").read_text()
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert 'class="hero-demo is-waiting"' in html
    assert ".hero-demo.is-waiting .chat-typing { opacity: 1; }" in css
    assert "const ROLAGEM_MINIMA_ATE_CHAT = 90;" in javascript
    assert "window.scrollY < ROLAGEM_MINIMA_ATE_CHAT" in javascript


def test_hero_da_landing_nao_tem_halo_verde_ao_fundo():
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert ".hero > .hero-grid { background: none; animation: none; }" in css


def test_marca_leva_ao_topo_pelo_hero_e_nao_pelo_cabecalho_grudado():
    html = (RAIZ / "web/index.html").read_text()
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert "position: sticky; top: 0;" in css[css.index(".site-header {") :]
    assert '<header class="site-header">' in html
    assert '<main id="conteudo">\n      <section class="hero" id="inicio">' in html
    assert html.count('id="inicio"') == 1
    assert html.count('href="#inicio"') == 2
    assert "#conteudo > section[id] { scroll-margin-top: 100px; }" in css


def test_faq_cobre_fontes_telegram_ausencia_candidatura_e_conta():
    html = (RAIZ / "web/index.html").read_text()

    for trecho in (
        "não cobre todo o mercado",
        "até sete recomendações",
        "Dias sem vaga podem acontecer",
        "candidatura continua sendo sua",
        "Preciso vincular o Telegram?",
        "Posso pausar ou apagar minha conta?",
    ):
        assert trecho in html


def test_landing_nao_promete_chegada_antecipada_ou_edicao_inexistente():
    html = (RAIZ / "web/index.html").read_text()

    assert "Chegue antes" not in html
    assert "você poderá editar depois" not in html
    assert "Vagas mais claras" in html


def test_landing_e_cadastro_dizem_para_que_servem_os_dados():
    html = (RAIZ / "web/index.html").read_text()

    assert "selecionar e entregar vagas, manter sua conta e medir o uso" in html
    assert "Supabase, Telegram e GitHub Actions" in html
    assert "Seu perfil serve para selecionar vagas" in html
    assert "Nada é vendido nem compartilhado" not in html


def test_aviso_de_privacidade_aponta_para_o_painel_que_passou_a_existir():
    html = (RAIZ / "web/index.html").read_text()

    assert "fale com a equipe do projeto" not in html
    assert "entre na sua conta pelo botão de cadastro" in html
    assert 'id="delete-account"' in html


def test_aviso_de_privacidade_do_cadastro_aparece_tambem_no_celular():
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert ".privacy-note { display: none; }" not in css


def test_cadastro_rola_no_celular_em_vez_de_cortar_o_botao():
    css = (RAIZ / "web/assets/styles.css").read_text()
    regra_do_celular = css[css.index("@media (max-width: 760px)") :]

    assert "overflow-y: auto" in regra_do_celular.split(".dialog-shell")[0]


def _regras_das_telas_estreitas(css):
    regras = []
    for abertura in re.finditer(r"@media \(max-width: \d+px\) \{", css):
        profundidade = 1
        posicao = abertura.end()
        while profundidade:
            if css[posicao] == "{":
                profundidade += 1
            elif css[posicao] == "}":
                profundidade -= 1
            posicao += 1
        corpo = css[abertura.end() : posicao - 1]
        regras += [
            (seletores.strip(), declaracoes)
            for seletores, declaracoes in re.findall(r"([^{}]+)\{([^{}]*)\}", corpo)
        ]
    return regras


def _alcanca_a_navegacao_da_conta(seletor):
    compostos = re.split(r"\s*[>+~]\s*|\s+", seletor.strip())
    sujeito = compostos[-1]
    if re.search(r"(\.account-(nav|sidebar|sidebar-inner|shell)|#account-page)(?![\w-])", sujeito):
        return True
    return re.match(r"a(?![\w-])", sujeito) is not None and any(
        ".account-nav" in composto for composto in compostos[:-1]
    )


def test_navegacao_da_conta_segue_visivel_no_celular_com_as_quatro_secoes():
    html = (RAIZ / "web/index.html").read_text()
    css = (RAIZ / "web/assets/styles.css").read_text()
    navegacao = re.search(r'<nav class="account-nav"[^>]*>(.*?)</nav>', html, re.S).group(1)

    assert re.findall(r'<a [^>]*href="#([\w-]+)"', navegacao) == [
        "account-overview-panel",
        "account-delivery-panel",
        "account-data-panel",
        "account-privacy-panel",
    ]
    regras_que_escondem = [
        seletores
        for seletores, declaracoes in _regras_das_telas_estreitas(css)
        if re.search(r"display:\s*none|visibility:\s*hidden", declaracoes)
        and any(_alcanca_a_navegacao_da_conta(seletor) for seletor in seletores.split(","))
    ]
    assert regras_que_escondem == []


def test_navegacao_da_conta_no_celular_rola_sozinha_sem_alargar_a_pagina():
    css = (RAIZ / "web/assets/styles.css").read_text()
    regras = _regras_das_telas_estreitas(css)
    navegacao = " ".join(
        declaracoes for seletores, declaracoes in regras if seletores == ".account-nav"
    )
    alturas_dos_links = [
        int(altura)
        for seletores, declaracoes in regras
        if seletores == ".account-nav a"
        for altura in re.findall(r"min-height:\s*(\d+)px", declaracoes)
    ]

    assert "overflow-x: auto" in navegacao
    assert re.search(r"\n\.account-nav a \{[^}]*min-height: 44px", css)
    assert all(altura >= 44 for altura in alturas_dos_links)


def test_painel_da_conta_oferece_editar_pausar_desvincular_e_excluir():
    html = (RAIZ / "web/index.html").read_text()

    for controle in ("edit-profile", "toggle-deliveries", "unlink-telegram", "delete-account"):
        assert f'id="{controle}"' in html


def test_acao_destrutiva_pede_confirmacao_antes():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "pedirConfirmacao(" in javascript
    assert "#account-confirm-yes" in javascript


def test_exclusao_diz_a_verdade_sobre_os_60_dias_e_o_arrependimento():
    javascript = (RAIZ / "web/assets/app.js").read_text()
    html = (RAIZ / "web/index.html").read_text()

    assert "Não dá para desfazer" not in javascript
    assert "Seus dados foram apagados" not in javascript
    assert "As entregas param na hora" in javascript
    assert "entre aqui de novo para cancelar" in javascript
    assert 'rpc("cancelar_exclusao_da_minha_conta")' in javascript
    assert 'id="cancel-deletion"' in html


def test_exclusao_e_desvinculo_passam_pelas_funcoes_do_banco():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert 'rpc("desvincular_meu_telegram")' in javascript
    assert 'rpc("excluir_minha_conta")' in javascript


def test_edicao_dispensa_as_credenciais_de_quem_ja_tem_sessao():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "function entrarNoModoEdicao()" in javascript
    assert "form.elements.senha.required = false" in javascript


def test_perfil_pausado_que_revincula_nao_diz_que_esta_ativo():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "if (profile?.telegram_chat_id) showActivation(profile)" not in javascript
    assert javascript.count("mostrarEstadoDoPerfil(profile)") >= 2


def test_sessao_perdida_no_meio_avisa_em_vez_de_falhar_calado():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "MENSAGEM_SEM_SESSAO" in javascript
    assert "MENSAGEM_SEM_PERFIL" in javascript
    assert "if (editandoPerfilExistente && !existingSession) {" in javascript


def test_pedir_exclusao_mantem_a_sessao_para_a_pessoa_poder_cancelar():
    javascript = (RAIZ / "web/assets/app.js").read_text()
    trecho = javascript[javascript.index('rpc("excluir_minha_conta")') :][:600]

    assert "signOut" not in trecho


SELO_DA_ADZUNA = (
    '<span class="jobs-by-adzuna">'
    '<a href="https://www.adzuna.com.br" target="_blank" rel="noopener">Jobs</a> by '
    '<a href="https://www.adzuna.com.br" target="_blank" rel="noopener">'
    '<img src="assets/adzuna-logo.png" alt="Adzuna" width="87" height="23" /></a></span>'
)


def test_site_nao_cita_a_gupy_e_a_faixa_de_fontes_volta_sem_ela():
    html = (RAIZ / "web/index.html").read_text()
    faixa = html[html.index('class="proof-strip"') :]
    faixa = faixa[: faixa.index("</section>")]

    assert "gupy" not in html.lower()
    assert "Fontes e tecnologias do Radar" in faixa
    assert "<span>ADZUNA</span><span>GEMINI</span><span>TELEGRAM</span>" in faixa
    assert "Gupy" not in (RAIZ / "web/privacidade.html").read_text()
    assert "Gupy" not in (RAIZ / "docs/politica-de-privacidade.md").read_text()


def test_vagas_de_exemplo_e_fonte_levam_o_selo_jobs_by_adzuna():
    html = (RAIZ / "web/index.html").read_text()
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert html.count(SELO_DA_ADZUNA) == 3
    assert "Fonte: Adzuna" not in html
    assert ".jobs-by-adzuna { display: inline-flex; align-items: center; gap: 4px;" in css
    assert "min-width: 116px; min-height: 23px;" in css
    assert (RAIZ / "web/assets/adzuna-logo.png").exists()


def test_card_de_precos_nao_promete_duas_fontes_de_vagas():
    html = (RAIZ / "web/index.html").read_text()

    assert "duas fontes" not in html.lower()
    assert "Busca diária de vagas na Adzuna" in html
