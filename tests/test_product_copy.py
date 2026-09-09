from pathlib import Path

RAIZ = Path(__file__).parent.parent


def test_landing_exibe_promessa_multiarea_limite_canal_e_condicao_do_piloto():
    html = (RAIZ / "web/index.html").read_text()
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert '<span class="hero-title-primary">Cansado de procurar estágio?</span>' in html
    assert '<span class="hero-title-secondary">Nós levamos ele até você</span>' in html
    assert ".hero-title-primary { color: var(--ink); }" in css
    assert ".hero-title-secondary { color: var(--accent); }" in css
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
    assert "Fontes e tecnologias do Radar" in html
    assert ".chat-message-kicker span { color: var(--muted); font-size: 8px; font-weight: 500;" in css


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


def test_faq_cobre_fontes_telegram_ausencia_candidatura_e_conta():
    html = (RAIZ / "web/index.html").read_text()

    for trecho in (
        "não cobrem todo o mercado",
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
