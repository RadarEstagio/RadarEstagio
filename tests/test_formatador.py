import re
from datetime import UTC, datetime

from radar.domain.models import Modalidade, Recomendacao, ResultadoMatch, Vaga
from radar.notification.formatador import (
    LIMITE_DE_CARACTERES_DO_TELEGRAM,
    SEPARADOR_ENTRE_VAGAS,
    dividir_em_mensagens,
    formatar_falha_da_execucao,
    formatar_mensagem,
    formatar_mensagem_sem_vagas,
    formatar_resumo_da_execucao,
    recomendacoes_por_parte,
)

MOMENTO_DE_TESTE = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
URL_DE_RASTREIO = "https://projeto.supabase.co/functions/v1/ir"


def mensagem(
    resultados: list[ResultadoMatch],
    momento: datetime = MOMENTO_DE_TESTE,
    url_de_rastreio: str = "",
) -> str:
    recomendacoes = [Recomendacao(resultado=item) for item in resultados]
    return formatar_mensagem(recomendacoes, momento, url_de_rastreio)


def vaga(titulo: str = "Estágio Python", numero: int = 1) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=titulo,
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url=f"https://exemplo.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


def resultado(
    nota: int,
    titulo: str = "Estágio Python",
    alerta: str | None = None,
    numero: int = 1,
    a_favor: list[str] | None = None,
    contra: list[str] | None = None,
    avisos: list[str] | None = None,
    requisitos_atendidos: list[str] | None = None,
    requisitos_nao_atendidos: list[str] | None = None,
    requisitos_analisados: bool = False,
) -> ResultadoMatch:
    return ResultadoMatch(
        vaga=vaga(titulo, numero),
        nota=nota,
        pontos_a_favor=["Python"] if a_favor is None else a_favor,
        pontos_contra=["Exige Java"] if contra is None else contra,
        avisos_objetivos=[] if avisos is None else avisos,
        requisitos_atendidos=[] if requisitos_atendidos is None else requisitos_atendidos,
        requisitos_nao_atendidos=(
            [] if requisitos_nao_atendidos is None else requisitos_nao_atendidos
        ),
        requisitos_tecnicos_analisados=requisitos_analisados,
        alerta_pegadinha=alerta,
    )


def test_cabecalho_contem_a_data():
    texto = mensagem([resultado(50)], MOMENTO_DE_TESTE)

    assert texto.startswith("📡 <b>Radar de Estágio</b> — 26/08/2026")


def test_dia_sem_vaga_avisa_que_a_busca_continua_amanha():
    texto = formatar_mensagem_sem_vagas(MOMENTO_DE_TESTE)

    assert "26/08/2026" in texto
    assert "Nenhuma vaga nova compatível com o seu perfil hoje." in texto
    assert "O Radar volta a procurar amanhã de manhã." in texto
    assert "sem nenhuma recomendação" not in texto


def test_silencio_prolongado_acrescenta_a_sugestao_sem_tirar_o_aviso_do_dia():
    texto = formatar_mensagem_sem_vagas(MOMENTO_DE_TESTE, 12)

    assert "O Radar volta a procurar amanhã de manhã." in texto
    assert "Já são 12 dias sem nenhuma recomendação" in texto
    assert "remoto ou híbrido" in texto


def test_ordena_por_nota_decrescente_e_numera():
    texto = mensagem(
        [
            resultado(40, "Baixa", numero=1),
            resultado(90, "Alta", numero=2),
            resultado(70, "Média", numero=3),
        ],
        MOMENTO_DE_TESTE,
    )

    assert texto.index("1. Alta") < texto.index("2. Média") < texto.index("3. Baixa")


def test_inclui_titulo_empresa_nota_pontos_e_link():
    texto = mensagem(
        [resultado(85, a_favor=["Python", "SQL"], contra=["Presencial em SP"])], MOMENTO_DE_TESTE
    )

    assert "Estágio Python" in texto
    assert "Empresa Exemplo" in texto
    assert "Nota 85/100" in texto
    assert "✅ Python · SQL" in texto
    assert "❌ Presencial em SP" in texto
    assert '<a href="https://exemplo.com/vaga/1">Ver vaga em exemplo.com</a>' in texto


def test_link_rastreavel_usa_o_token_do_envio_e_mantem_o_dominio_visivel():
    recomendacao = Recomendacao(resultado=resultado(85))

    texto = formatar_mensagem([recomendacao], MOMENTO_DE_TESTE, URL_DE_RASTREIO)

    assert f'<a href="{URL_DE_RASTREIO}?t={recomendacao.token}">' in texto
    assert "Ver vaga em exemplo.com" in texto
    assert "https://exemplo.com/vaga/1" not in texto


def test_cada_vaga_recebe_o_proprio_link_rastreavel():
    primeira = Recomendacao(resultado=resultado(90, numero=1))
    segunda = Recomendacao(resultado=resultado(80, numero=2))

    texto = formatar_mensagem([primeira, segunda], MOMENTO_DE_TESTE, URL_DE_RASTREIO)

    assert primeira.token != segunda.token
    assert f"?t={primeira.token}" in texto
    assert f"?t={segunda.token}" in texto


def test_dominio_do_link_ignora_o_www():
    com_www = vaga().model_copy(update={"url": "https://www.gupy.io/vaga/9"})

    texto = mensagem([resultado(85).model_copy(update={"vaga": com_www})])

    assert "Ver vaga em gupy.io" in texto


def test_exibe_requisitos_tecnicos_atendidos_e_nao_atendidos_explicitamente():
    texto = mensagem(
        [
            resultado(
                64,
                a_favor=[],
                contra=[],
                requisitos_atendidos=["SQL"],
                requisitos_nao_atendidos=["C#", "JavaScript"],
                requisitos_analisados=True,
            )
        ],
        MOMENTO_DE_TESTE,
    )

    assert "✅ <b>Requisitos atendidos:</b> SQL" in texto
    assert "🔎 <b>Requisitos a conferir no seu perfil:</b> C# · JavaScript" in texto


def test_avisa_quando_descricao_nao_informa_requisitos_tecnicos():
    texto = mensagem(
        [resultado(73, a_favor=[], contra=[], requisitos_analisados=True)], MOMENTO_DE_TESTE
    )

    assert "ℹ️ <b>Requisitos técnicos:</b> não informados na descrição" in texto


def test_descricao_incompleta_nao_afirma_que_requisitos_nao_foram_informados():
    resultado_incompleto = resultado(
        60,
        a_favor=[],
        contra=[],
        requisitos_analisados=True,
        avisos=["Descrição incompleta: requisitos podem estar ausentes; nota limitada a 60"],
    )
    resultado_incompleto = resultado_incompleto.model_copy(
        update={"vaga": resultado_incompleto.vaga.model_copy(update={"descricao_completa": False})}
    )

    texto = mensagem([resultado_incompleto], MOMENTO_DE_TESTE)

    assert "requisitos podem estar ausentes" in texto
    assert "não informados na descrição" not in texto


def test_lista_longa_de_requisitos_e_resumida_na_mensagem():
    nao_atendidos = [f"Tecnologia{numero}" for numero in range(1, 21)]
    com_paredao = resultado(70, contra=[], requisitos_analisados=True)
    com_paredao = com_paredao.model_copy(update={"requisitos_nao_atendidos": nao_atendidos})

    texto = formatar_mensagem([Recomendacao(resultado=com_paredao)], MOMENTO_DE_TESTE)

    assert "Tecnologia8" in texto
    assert "Tecnologia9" not in texto
    assert "e mais 12" in texto


def test_lista_curta_de_requisitos_nao_ganha_resumo():
    com_poucos = resultado(70, contra=[], requisitos_analisados=True)
    com_poucos = com_poucos.model_copy(update={"requisitos_nao_atendidos": ["Python", "SQL"]})

    texto = formatar_mensagem([Recomendacao(resultado=com_poucos)], MOMENTO_DE_TESTE)

    assert "Python · SQL" in texto
    assert "e mais" not in texto


def test_inclui_localizacao_modalidade_fonte_e_data_de_publicacao():
    oportunidade = vaga().model_copy(update={"modalidade": Modalidade.HIBRIDO})
    texto = mensagem([resultado(85).model_copy(update={"vaga": oportunidade})], MOMENTO_DE_TESTE)

    assert "📍 Rio de Janeiro · Híbrido" in texto
    assert "🏷️ Fonte: Adzuna" in texto
    assert "Publicada em 25/08/2026" in texto


def test_modalidade_nao_informada_aparece_explicitamente():
    texto = mensagem([resultado(85)], MOMENTO_DE_TESTE)

    assert "📍 Rio de Janeiro · Modalidade não informada" in texto


def test_escapa_localizacao_e_fonte_dos_metadados():
    oportunidade = vaga().model_copy(
        update={"localizacao": "Rio <Centro> & região", "fonte": "portal_exemplo"}
    )
    texto = mensagem([resultado(85).model_copy(update={"vaga": oportunidade})], MOMENTO_DE_TESTE)

    assert "Rio &lt;Centro&gt; &amp; região" in texto
    assert "Fonte: Portal Exemplo" in texto
    assert "Rio <Centro>" not in texto


def test_linha_de_pontos_some_quando_a_lista_esta_vazia():
    so_contra = mensagem([resultado(10, a_favor=[], contra=["Fora da área"])], MOMENTO_DE_TESTE)
    so_a_favor = mensagem([resultado(95, a_favor=["Python"], contra=[])], MOMENTO_DE_TESTE)

    assert "✅" not in so_contra
    assert "❌ Fora da área" in so_contra
    assert "✅ Python" in so_a_favor
    assert "❌" not in so_a_favor


def test_exibe_no_maximo_tres_pontos_de_cada_tipo():
    texto = mensagem(
        [
            resultado(
                80,
                a_favor=["Python", "SQL", "Git", "Docker"],
                contra=["Java", "AWS", "Presencial", "Inglês"],
            )
        ],
        MOMENTO_DE_TESTE,
    )

    assert "✅ Python · SQL · Git" in texto
    assert "❌ Java · AWS · Presencial" in texto
    assert "Docker" not in texto
    assert "Inglês" not in texto


def test_alerta_aparece_somente_quando_existe():
    com_alerta = mensagem([resultado(30, alerta="Exige pleno")], MOMENTO_DE_TESTE)
    sem_alerta = mensagem([resultado(30)], MOMENTO_DE_TESTE)

    assert "⚠️ Exige pleno" in com_alerta
    assert "⚠️" not in sem_alerta


def test_aviso_objetivo_aparece_separado_dos_pontos_contra():
    texto = mensagem(
        [
            resultado(
                85,
                contra=["SQL não informado"],
                avisos=["Nota limitada a 30: modalidade incompatível"],
            )
        ],
        MOMENTO_DE_TESTE,
    )

    assert "❌ SQL não informado" in texto
    assert "⚠️ Nota limitada a 30: modalidade incompatível" in texto
    assert "❌ Nota limitada" not in texto


def test_escapa_caracteres_html_dos_dados_da_vaga_e_dos_pontos():
    texto = mensagem(
        [resultado(50, titulo="Dev <Júnior> & Estágio", contra=["C++ & <Go>"])], MOMENTO_DE_TESTE
    )

    assert "Dev &lt;Júnior&gt; &amp; Estágio" in texto
    assert "C++ &amp; &lt;Go&gt;" in texto
    assert "<Júnior>" not in texto


def test_vagas_sao_separadas_por_linha_divisoria():
    texto = mensagem([resultado(50, numero=1), resultado(40, numero=2)], MOMENTO_DE_TESTE)

    assert texto.count("───────────────") == 1
    assert texto.index("1. ") < texto.index("───────────────") < texto.index("2. ")


def test_mensagem_curta_nao_e_dividida():
    texto = mensagem([resultado(50)], MOMENTO_DE_TESTE)

    assert dividir_em_mensagens(texto) == [texto]


def test_mensagem_longa_e_dividida_sem_quebrar_vagas():
    resultados = [
        resultado(50, titulo="Estágio " + "x" * 400, numero=numero) for numero in range(20)
    ]
    texto = mensagem(resultados, MOMENTO_DE_TESTE)

    partes = dividir_em_mensagens(texto)

    assert len(partes) > 1
    assert all(len(parte) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for parte in partes)
    assert all(parte.count("<b>") == parte.count("</b>") for parte in partes)
    assert "\n\n───────────────\n\n".join(partes) == texto


def test_resumo_da_execucao_traz_os_numeros_da_operacao():
    texto = formatar_resumo_da_execucao(MOMENTO_DE_TESTE, 12, 9, 31, 480, 18)

    assert "execução de 26/08/2026" in texto
    assert "Usuários ativos: 12" in texto
    assert "Receberam recomendação: 9" in texto
    assert "Vagas enviadas: 31" in texto
    assert "Vagas coletadas: 480" in texto
    assert "Requisições ao avaliador: 18" in texto


def test_falha_da_execucao_escapa_a_mensagem_do_erro():
    texto = formatar_falha_da_execucao(MOMENTO_DE_TESTE, "Gemini <429> & cota")

    assert "26/08/2026 falhou" in texto
    assert "Gemini &lt;429&gt; &amp; cota" in texto


def test_resumo_avisa_operacao_sobre_revalidacao_indisponivel():
    texto = formatar_resumo_da_execucao(MOMENTO_DE_TESTE, 12, 9, 31, 480, 18, 3, 2)
    assert "Usuários com falha de revalidação: 3" in texto
    assert "Sem entrega por falha de revalidação: 2" in texto


def test_resumo_avisa_vagas_sem_extracao_e_extracoes_nao_gravadas():
    texto = formatar_resumo_da_execucao(MOMENTO_DE_TESTE, 2, 2, 13, 830, 7, 0, 0, 36, 0)

    assert "Vagas sem extração (cota ou avaliador fora): 36" in texto
    assert "Extrações não gravadas" not in texto

    com_falha_de_gravacao = formatar_resumo_da_execucao(
        MOMENTO_DE_TESTE, 2, 2, 13, 830, 7, 0, 0, 0, 12
    )

    assert "Extrações não gravadas no banco: 12" in com_falha_de_gravacao
    assert "Vagas sem extração" not in com_falha_de_gravacao


def test_resumo_sem_problemas_de_extracao_nao_mostra_avisos():
    texto = formatar_resumo_da_execucao(MOMENTO_DE_TESTE, 2, 2, 13, 830, 7)

    assert "⚠️" not in texto


def test_diferenciais_que_faltam_aparecem_em_linha_propria_depois_dos_requisitos():
    from datetime import UTC, datetime
    from uuid import uuid4

    from radar.domain.models import Recomendacao, ResultadoMatch, Vaga
    from radar.notification.formatador import formatar_vaga

    anuncio = Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio Java",
        empresa="Empresa",
        localizacao="Rio de Janeiro, RJ",
        descricao="d",
        url="https://exemplo.com/1",
        publicada_em=datetime(2026, 9, 9, tzinfo=UTC),
    )
    com = Recomendacao(
        resultado=ResultadoMatch(
            vaga=anuncio,
            nota=80,
            requisitos_atendidos=["Java"],
            requisitos_nao_atendidos=["Docker"],
            diferenciais_nao_atendidos=["Angular", "Spring"],
        ),
        token=uuid4(),
    )
    sem = Recomendacao(resultado=ResultadoMatch(vaga=anuncio, nota=80), token=uuid4())

    linhas = formatar_vaga(1, com).split("\n")
    posicao_requisitos = next(i for i, linha in enumerate(linhas) if "a conferir" in linha)

    assert (
        linhas[posicao_requisitos + 1] == "✨ <b>Diferenciais que a vaga cita:</b> Angular · Spring"
    )
    assert "Diferenciais" not in formatar_vaga(1, sem)


def test_entrega_da_madrugada_usa_a_data_de_brasilia_e_nao_a_do_utc():
    madrugada = datetime(2026, 9, 10, 1, 30, tzinfo=UTC)

    assert "09/09/2026" in mensagem([resultado(50)], madrugada)
    assert "09/09/2026" in formatar_mensagem_sem_vagas(madrugada)
    assert "09/09/2026" in formatar_resumo_da_execucao(madrugada, 1, 1, 1, 1, 1)
    assert "09/09/2026" in formatar_falha_da_execucao(madrugada, "erro")


def test_execucao_das_sete_da_manha_mantem_a_data_do_dia():
    manha = datetime(2026, 9, 10, 10, 23, tzinfo=UTC)

    assert "10/09/2026" in mensagem([resultado(50)], manha)


def resultado_gigante() -> ResultadoMatch:
    enorme = ResultadoMatch(
        vaga=Vaga(
            id_externo="1",
            fonte="adzuna",
            titulo="Título " + "muito longo " * 40,
            empresa="Empresa " + "com nome interminável " * 20,
            localizacao="Cidade " + "com nome enorme " * 20,
            descricao="descrição",
            url="https://exemplo.com/vaga/1",
            publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
        ),
        nota=80,
        requisitos_atendidos=[f"requisito atendido {n} " + "detalhado " * 40 for n in range(12)],
        requisitos_nao_atendidos=[f"a conferir {n} " + "detalhado " * 40 for n in range(12)],
        diferenciais_nao_atendidos=[f"diferencial {n} " + "detalhado " * 40 for n in range(12)],
        pontos_a_favor=["ponto a favor " * 40] * 4,
        pontos_contra=["ponto contra " * 40] * 4,
        avisos_objetivos=["aviso " * 60] * 3,
        alerta_pegadinha="alerta " * 80,
    )
    return enorme


def test_vaga_com_textos_enormes_cabe_nas_partes_do_telegram():
    texto = mensagem([resultado_gigante()])

    partes = dividir_em_mensagens(texto)

    assert all(len(parte) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for parte in partes)


def test_sete_vagas_enormes_continuam_dentro_do_limite():
    resultados = [resultado_gigante() for _ in range(7)]

    partes = dividir_em_mensagens(mensagem(resultados))

    assert all(len(parte) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for parte in partes)


def test_corte_nao_deixa_entidade_html_pela_metade():
    com_ecomercial = resultado(50, titulo="P&D " * 200)

    texto = mensagem([com_ecomercial])

    assert "&am" not in texto.replace("&amp;", "")


def test_recomendacoes_sao_distribuidas_entre_as_partes_na_ordem_da_mensagem():
    resultados = [resultado(90 - numero, numero=numero) for numero in range(1, 6)]
    recomendacoes = [Recomendacao(resultado=item) for item in resultados]
    texto = formatar_mensagem(recomendacoes, MOMENTO_DE_TESTE)
    partes = dividir_em_mensagens(texto)

    grupos = recomendacoes_por_parte(partes, recomendacoes)

    assert [len(grupo) for grupo in grupos] == [5]
    assert [r.resultado.nota for r in grupos[0]] == [89, 88, 87, 86, 85]


def test_cada_parte_leva_as_vagas_que_estao_dentro_dela():
    resultados = [
        ResultadoMatch(
            vaga=vaga(numero=numero),
            nota=90 - numero,
            requisitos_atendidos=[f"requisito {i} " + "detalhado " * 20 for i in range(12)],
            requisitos_nao_atendidos=[f"conferir {i} " + "detalhado " * 20 for i in range(12)],
            diferenciais_nao_atendidos=[f"diferencial {i} " + "detalhado " * 20 for i in range(12)],
        )
        for numero in range(1, 5)
    ]
    recomendacoes = [Recomendacao(resultado=item) for item in resultados]
    partes = dividir_em_mensagens(formatar_mensagem(recomendacoes, MOMENTO_DE_TESTE))

    grupos = recomendacoes_por_parte(partes, recomendacoes)

    assert len(partes) > 1
    assert sum(len(grupo) for grupo in grupos) == 4
    assert [r.resultado.nota for grupo in grupos for r in grupo] == [89, 88, 87, 86]


def test_titulo_com_quebras_de_linha_nao_inventa_uma_vaga_a_mais():
    poluido = resultado(90, titulo="Estágio" + SEPARADOR_ENTRE_VAGAS + "falso", numero=1)
    outros = [resultado(80 - numero, numero=numero) for numero in range(2, 5)]
    recomendacoes = [Recomendacao(resultado=item) for item in [poluido, *outros]]
    texto = formatar_mensagem(recomendacoes, MOMENTO_DE_TESTE)

    grupos = recomendacoes_por_parte(dividir_em_mensagens(texto), recomendacoes)

    assert texto.count(SEPARADOR_ENTRE_VAGAS) == len(recomendacoes) - 1
    assert sum(len(grupo) for grupo in grupos) == len(recomendacoes)


def test_texto_da_fonte_com_quebra_de_linha_vira_uma_linha_so():
    com_quebra = resultado(50, titulo="Estágio\nem\tDados")

    assert "Estágio em Dados" in mensagem([com_quebra])


def test_todas_as_datas_da_mensagem_usam_o_mesmo_fuso():
    publicada_as_21h30_de_brasilia = datetime(2026, 9, 10, 0, 30, tzinfo=UTC)
    entregue_as_22h_de_brasilia = datetime(2026, 9, 10, 1, 0, tzinfo=UTC)
    vaga_da_noite = resultado(80).model_copy(
        update={"vaga": vaga().model_copy(update={"publicada_em": publicada_as_21h30_de_brasilia})}
    )

    texto = mensagem([vaga_da_noite], entregue_as_22h_de_brasilia)

    assert set(re.findall(r"\d{2}/\d{2}/\d{4}", texto)) == {"09/09/2026"}


def test_fonte_que_so_informa_a_data_mantem_o_dia_informado():
    so_a_data = datetime(2026, 9, 4, tzinfo=UTC)
    vaga_sem_hora = resultado(80).model_copy(
        update={"vaga": vaga().model_copy(update={"publicada_em": so_a_data})}
    )

    assert "Publicada em 04/09/2026" in mensagem([vaga_sem_hora], MOMENTO_DE_TESTE)


def test_horario_real_depois_das_21h_de_brasilia_fica_no_proprio_dia():
    as_22h_de_brasilia = datetime(2026, 9, 5, 1, 0, tzinfo=UTC)
    vaga_da_noite = resultado(80).model_copy(
        update={"vaga": vaga().model_copy(update={"publicada_em": as_22h_de_brasilia})}
    )

    assert "Publicada em 04/09/2026" in mensagem([vaga_da_noite], MOMENTO_DE_TESTE)
