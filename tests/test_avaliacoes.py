import math
from datetime import UTC, datetime

import pytest

from radar.domain.models import AreaDeInteresse, ExtracaoDaVaga, Modalidade, Perfil, Vaga
from radar.matching.avaliacoes import pontuar


def vaga(modalidade: Modalidade | None = None) -> Vaga:
    return Vaga(
        id_externo="vaga-1",
        fonte="adzuna",
        titulo="Estágio em Desenvolvimento Web",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, RJ",
        descricao="Descrição",
        url="https://exemplo.com/vaga-1",
        publicada_em=datetime(2026, 8, 30, tzinfo=UTC),
        modalidade=modalidade,
    )


def perfil(habilidades: list[str] | None = None) -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python", "Java"] if habilidades is None else habilidades,
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )


CURSO_ACEITO_DE_COMPUTACAO = "Ciência da Computação"
CURSO_ACEITO_DE_OUTRA_AREA = "Engenharia Elétrica"


def extracao(**alteracoes) -> ExtracaoDaVaga:
    dados = {
        "id_vaga": "vaga-1",
        "area_da_vaga": "computacao",
        "cursos_aceitos": [CURSO_ACEITO_DE_COMPUTACAO],
        "habilidades_obrigatorias": [],
        "habilidades_desejaveis": [],
    }
    dados.update(alteracoes)
    return ExtracaoDaVaga.model_validate(dados)


def resultado_da(extracao_da_vaga: ExtracaoDaVaga, candidato: Perfil | None = None):
    return pontuar(vaga(), extracao_da_vaga, candidato or perfil())


def test_modalidade_extraida_preenche_vaga_sem_modalidade():
    resultado = resultado_da(extracao(modalidade="presencial"))

    assert resultado.vaga.modalidade is Modalidade.PRESENCIAL


def test_modalidade_da_fonte_prevalece_sobre_a_extraida():
    resultado = pontuar(
        vaga(modalidade=Modalidade.HIBRIDO), extracao(modalidade="remoto"), perfil()
    )

    assert resultado.vaga.modalidade is Modalidade.HIBRIDO


def test_modalidade_extraida_entra_na_logistica_da_nota():
    sem_modalidade = resultado_da(extracao())
    presencial_extraida = resultado_da(extracao(modalidade="presencial"))

    assert presencial_extraida.nota > sem_modalidade.nota


def test_cidade_vizinha_vale_metade_da_localizacao_na_nota():
    def nota_em(localizacao: str) -> int:
        na_localizacao = vaga(Modalidade.PRESENCIAL).model_copy(update={"localizacao": localizacao})
        return pontuar(na_localizacao, extracao(), perfil()).nota

    na_cidade = nota_em("Rio de Janeiro, Estado do Rio de Janeiro")
    na_regiao = nota_em("Niterói, Estado do Rio de Janeiro")
    longe = nota_em("São Paulo, Estado de São Paulo")

    assert na_cidade > na_regiao > longe


def test_stack_desejavel_sem_correspondencia_recebe_nota_baixa():
    requisitos = ["PHP", "MySQL", "SQL", "HTML5", "JavaScript", "REST", "VueJS", "AJAX", "jQuery"]

    resultado = resultado_da(extracao(habilidades_desejaveis=requisitos))

    assert resultado.nota == 57


def test_muitos_requisitos_ausentes_pesam_mais_que_um_so():
    muitos = ["PHP", "MySQL", "HTML5", "VueJS", "AJAX", "jQuery"]

    com_muitos = resultado_da(extracao(habilidades_desejaveis=muitos))
    com_um = resultado_da(extracao(habilidades_desejaveis=["PHP"]))

    assert com_muitos.nota < com_um.nota


def test_stack_principal_parcial_nao_recebe_nota_de_compatibilidade_total():
    resultado = resultado_da(
        extracao(habilidades_principais=["SQL", "C#", "JavaScript"]),
        perfil(habilidades=["Python", "Sprint Boot", "Django", "SQL", "Java"]),
    )

    assert resultado.nota == 75


def test_stack_principal_usa_as_mesmas_habilidades_na_nota_e_na_explicacao():
    resultado = resultado_da(
        extracao(habilidades_principais=["SQL", "C#", "JavaScript"]),
        perfil(habilidades=["Python", "Sprint Boot", "Django", "SQL", "Java"]),
    )

    assert resultado.requisitos_atendidos == ["SQL"]
    assert resultado.requisitos_nao_atendidos == ["C#", "JavaScript"]
    assert resultado.requisitos_tecnicos_analisados
    assert resultado.pontos_a_favor == ["Curso compatível"]
    assert resultado.pontos_contra == []


def test_java_nao_corresponde_a_javascript():
    sem_correspondencia = resultado_da(extracao(habilidades_desejaveis=["JavaScript"]))
    com_correspondencia = resultado_da(
        extracao(habilidades_desejaveis=["JavaScript"]), perfil(habilidades=["JavaScript"])
    )

    assert sem_correspondencia.nota == 75
    assert com_correspondencia.nota == 98


def test_idiomas_e_pacote_office_nao_contam_na_nota_mas_aparecem_na_lista():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Inglês avançado", "Excel", "Python"])
    )

    assert resultado.nota == 98
    assert resultado.requisitos_atendidos == ["Python"]
    assert resultado.requisitos_nao_atendidos == ["Inglês avançado", "Excel"]


def test_vaga_que_so_pede_idiomas_e_office_e_tratada_como_sem_stack():
    so_genericos = resultado_da(extracao(habilidades_obrigatorias=["Inglês", "Word", "PowerPoint"]))
    sem_stack = resultado_da(extracao())

    assert so_genericos.nota == sem_stack.nota


def test_wordpress_nao_e_confundido_com_word():
    resultado = resultado_da(extracao(habilidades_obrigatorias=["WordPress", "PHP"]))

    assert resultado.nota == 68


def test_desejavel_nao_atendida_fica_fora_da_lista_de_cobranca():
    resultado = resultado_da(
        extracao(
            habilidades_obrigatorias=["Python", "C#"],
            habilidades_desejaveis=["Docker", "AWS", "Java"],
        )
    )

    assert resultado.requisitos_nao_atendidos == ["C#"]
    assert "Docker" not in resultado.requisitos_nao_atendidos
    assert set(resultado.requisitos_atendidos) == {"Python", "Java"}


def test_vaga_sem_stack_declarada_recebe_cobertura_neutra():
    resultado = resultado_da(extracao())

    assert resultado.nota == 64


def test_vaga_da_area_de_interesse_ganha_o_peso_cheio():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(areas_da_vaga=["desenvolvimento_web", "dados_ia"]), perfil_web
    )

    assert resultado.nota == 64
    assert resultado.avisos_objetivos == []


def test_outra_subarea_do_mesmo_campo_perde_metade_do_fator_e_nao_ganha_aviso():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(extracao(areas_da_vaga=["infraestrutura_redes"]), perfil_web)

    assert resultado.nota == 59
    assert resultado.avisos_objetivos == []


def test_vaga_de_outro_campo_perde_o_fator_inteiro_e_ganha_aviso():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(area_da_vaga="direito", areas_da_vaga=["direito_contencioso"]), perfil_web
    )

    assert "Fora das suas áreas de interesse" in resultado.avisos_objetivos


def test_vaga_sem_area_reconhecida_fica_neutra_para_quem_tem_interesses():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(extracao(areas_da_vaga=["area_inventada"]), perfil_web)

    assert resultado.nota == 59
    assert resultado.avisos_objetivos == []


def test_vaga_sem_area_reconhecida_tambem_respeita_o_teto_de_65():
    perfil_web = perfil(habilidades=["SQL"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["SQL"], areas_da_vaga=[]), perfil_web
    )

    assert resultado.nota == 65
    assert resultado.avisos_objetivos == []


def test_match_total_de_habilidades_fora_do_interesse_fica_limitado_a_65():
    perfil_web = perfil(habilidades=["SQL"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(
            habilidades_obrigatorias=["SQL"],
            area_da_vaga="direito",
            areas_da_vaga=["direito_contencioso"],
        ),
        perfil_web,
    )

    assert resultado.nota == 65
    assert "Fora das suas áreas de interesse" in resultado.avisos_objetivos


def test_area_recusada_zera_o_interesse_e_limita_a_65_com_aviso():
    candidato = perfil(habilidades=["Python"])
    candidato.areas_recusadas = [AreaDeInteresse.DADOS_IA]

    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Python"], areas_da_vaga=["dados_ia"]), candidato
    )

    assert resultado.nota <= 65
    assert resultado.avisos_objetivos == ["Área que você recusou nos últimos dias: Dados e IA"]


def test_area_recusada_vale_mesmo_sem_interesses_declarados():
    candidato = perfil(habilidades=["Python"])
    candidato.areas_de_interesse = []
    candidato.areas_recusadas = [AreaDeInteresse.SUPORTE_TECNICO]

    resultado = resultado_da(extracao(areas_da_vaga=["suporte_tecnico"]), candidato)

    assert resultado.avisos_objetivos == ["Área que você recusou nos últimos dias: Suporte técnico"]


def test_area_recusada_prevalece_sobre_o_interesse_declarado():
    candidato = perfil(habilidades=["Python"])
    candidato.areas_de_interesse = [AreaDeInteresse.DADOS_IA]
    candidato.areas_recusadas = [AreaDeInteresse.DADOS_IA]

    resultado = resultado_da(extracao(areas_da_vaga=["dados_ia"]), candidato)

    assert resultado.nota <= 65
    assert resultado.avisos_objetivos == ["Área que você recusou nos últimos dias: Dados e IA"]


def test_perfil_sem_interesses_nao_e_penalizado_por_area_da_vaga():
    resultado = resultado_da(extracao(areas_da_vaga=["infraestrutura_redes"]))

    assert resultado.nota == 64
    assert resultado.avisos_objetivos == []


def test_vaga_sem_stack_nao_supera_vaga_detalhada_e_meio_compativel():
    sem_stack = resultado_da(extracao())
    detalhada = resultado_da(
        extracao(habilidades_principais=["Python", "SQL", "Git"]),
        perfil(habilidades=["Python", "Git"]),
    )

    assert detalhada.nota > sem_stack.nota


def test_c_nao_corresponde_a_csharp_nem_a_cpp():
    resultado = resultado_da(
        extracao(habilidades_desejaveis=["C#", "C++"]), perfil(habilidades=["C"])
    )

    assert resultado.nota == 68


def test_csharp_por_extenso_corresponde_ao_simbolo():
    resultado = resultado_da(
        extracao(habilidades_desejaveis=["C#", "C++"]), perfil(habilidades=["CSharp", "CPP"])
    )

    assert resultado.nota == 98


def test_alias_js_corresponde_a_javascript():
    resultado = resultado_da(
        extracao(habilidades_desejaveis=["JavaScript"]), perfil(habilidades=["JS"])
    )

    assert resultado.nota == 98


def test_cobertura_total_da_stack_desejavel_recebe_98_pontos():
    resultado = resultado_da(extracao(habilidades_desejaveis=["Python", "Java"]))

    assert resultado.nota == 98


def test_obrigatorias_valem_oitenta_porcento_quando_ha_desejaveis():
    resultado = resultado_da(
        extracao(
            habilidades_obrigatorias=["Python", "Java"],
            habilidades_desejaveis=["SQL"],
        )
    )

    assert resultado.nota == 93


def test_habilidade_obrigatoria_ausente_reduz_a_nota_sem_vetar():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Python", "C#"]),
        perfil(habilidades=["Python"]),
    )

    assert resultado.nota == 83


def test_stack_principal_parcial_reduz_a_nota_proporcionalmente():
    resultado = resultado_da(
        extracao(
            habilidades_obrigatorias=["Python"],
            habilidades_principais=["C#", "JavaScript", "SQL"],
        ),
        perfil(habilidades=["Python", "SQL"]),
    )

    assert resultado.nota == 91


def test_curso_incompativel_limita_a_nota_a_35_com_aviso():
    resultado = resultado_da(
        extracao(
            cursos_aceitos=[CURSO_ACEITO_DE_OUTRA_AREA], habilidades_obrigatorias=["Python", "Java"]
        )
    )

    assert resultado.nota == 35
    assert "Exige formação de outra área" in resultado.avisos_objetivos


def test_curso_parcial_limita_a_nota_a_75():
    resultado = resultado_da(
        extracao(cursos_aceitos=[], habilidades_obrigatorias=["Python", "Java"])
    )

    assert resultado.nota == 75
    assert resultado.avisos_objetivos == []


def test_fatores_parciais_recebem_metade_do_peso():
    resultado = resultado_da(
        extracao(
            area_da_vaga=None,
            cursos_aceitos=[],
            experiencia_desejavel=True,
            habilidades_obrigatorias=["Python"],
        )
    )

    assert resultado.nota == 75


def test_habilidade_nao_vira_ponto_porque_ja_aparece_na_lista_de_requisitos():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Python"], cursos_aceitos=[]),
        perfil(habilidades=["Python"]),
    )

    assert resultado.requisitos_atendidos == ["Python"]
    assert resultado.pontos_a_favor == []
    assert resultado.pontos_contra == []


def test_periodo_minimo_acima_do_perfil_vira_ponto_contra():
    resultado = resultado_da(extracao(periodo_minimo=8))

    assert resultado.pontos_contra == ["Período mínimo incompatível"]


def test_experiencia_exigida_vira_ponto_contra_no_lugar_do_periodo():
    resultado = resultado_da(extracao(periodo_minimo=8, experiencia_minima_anos=2))

    assert resultado.pontos_contra == ["Exige experiência prévia"]


def test_variantes_de_office_e_google_nao_contam_na_nota():
    ferramentas = ["Microsoft Excel", "Documentos", "Drive", "Google Sheets"]

    so_ferramentas = resultado_da(extracao(habilidades_obrigatorias=ferramentas))
    sem_stack = resultado_da(extracao(habilidades_obrigatorias=[]))

    assert so_ferramentas.nota == sem_stack.nota
    assert so_ferramentas.requisitos_nao_atendidos == ferramentas


def test_ferramenta_de_escritorio_nao_penaliza_vaga_que_declara_stack():
    com_ferramentas = resultado_da(
        extracao(habilidades_obrigatorias=["Python", "Microsoft Excel", "Documentos", "Drive"])
    )
    so_a_stack = resultado_da(extracao(habilidades_obrigatorias=["Python"]))

    assert com_ferramentas.nota == so_a_stack.nota


def test_excel_do_perfil_corresponde_a_microsoft_excel_da_vaga():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Microsoft Excel"]),
        perfil(habilidades=["Excel"]),
    )

    assert resultado.requisitos_atendidos == ["Microsoft Excel"]


def test_office_e_idioma_diferenciam_perfis_fora_de_computacao():
    anuncio = extracao(
        area_da_vaga="administracao",
        cursos_aceitos=["Administração"],
        habilidades_obrigatorias=["Microsoft Excel", "Inglês"],
    )
    atende = perfil(["Excel", "Inglês"]).model_copy(update={"curso": "Administração"})
    nao_informa = perfil(["Python"]).model_copy(update={"curso": "Administração"})
    bom = resultado_da(anuncio, atende)
    incompleto = resultado_da(anuncio, nao_informa)
    assert bom.nota > incompleto.nota
    assert bom.requisitos_nao_atendidos == []
    assert incompleto.requisitos_nao_atendidos == ["Microsoft Excel", "Inglês"]


def test_outra_subarea_do_mesmo_campo_nao_fica_presa_ao_teto_de_65():
    perfil_web = perfil(habilidades=["SQL"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["SQL"], areas_da_vaga=["infraestrutura_redes"]),
        perfil_web,
    )

    assert resultado.nota > 65
    assert resultado.avisos_objetivos == []


def test_subarea_marcada_ainda_vence_outra_subarea_do_mesmo_campo():
    perfil_web = perfil(habilidades=["SQL"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]
    vaga_marcada = extracao(habilidades_obrigatorias=["SQL"], areas_da_vaga=["desenvolvimento_web"])
    vaga_do_campo = extracao(
        habilidades_obrigatorias=["SQL"], areas_da_vaga=["infraestrutura_redes"]
    )

    assert (
        resultado_da(vaga_marcada, perfil_web).nota > resultado_da(vaga_do_campo, perfil_web).nota
    )


def test_programa_aberto_a_varias_formacoes_com_subarea_do_campo_nao_ganha_aviso():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]
    aberto = extracao(area_da_vaga=None, areas_da_vaga=["dados_ia"])
    do_campo = extracao(area_da_vaga="computacao", areas_da_vaga=["dados_ia"])

    assert resultado_da(aberto, perfil_web).avisos_objetivos == []
    assert resultado_da(aberto, perfil_web).nota >= resultado_da(do_campo, perfil_web).nota - 5


def test_curso_desconhecido_com_interesses_ainda_reconhece_o_proprio_campo():
    exotico = perfil(habilidades=["Python", "Java"])
    exotico.curso = "Curso Que Ninguém Tem"
    exotico.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(extracao(areas_da_vaga=["dados_ia"]), exotico)

    assert "Fora das suas áreas de interesse" not in resultado.avisos_objetivos


def test_qualificador_de_nivel_nao_fura_a_exclusao_de_office_em_computacao():
    so_office = resultado_da(
        extracao(habilidades_obrigatorias=["Excel avançado", "Pacote Office", "Office 365"])
    )

    assert so_office.nota == resultado_da(extracao()).nota


def test_fora_de_computacao_variantes_de_office_e_nivel_casam_com_o_perfil():
    de_direito = Perfil(
        curso="Direito",
        periodo=4,
        habilidades=["Excel avançado", "Inglês intermediário", "Redação", "Pacote Office"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )
    exigentes = ["Excel avançado", "Inglês intermediário", "Boa redação", "Office 365"]
    anuncio = extracao(
        area_da_vaga="direito", cursos_aceitos=["Direito"], habilidades_obrigatorias=exigentes
    )
    sem_exigencias = extracao(area_da_vaga="direito", cursos_aceitos=["Direito"])

    resultado = resultado_da(anuncio, de_direito)

    assert resultado.requisitos_nao_atendidos == []
    assert resultado.nota > resultado_da(sem_exigencias, de_direito).nota


def test_aviso_de_recusa_nomeia_so_as_subareas_recusadas_que_a_vaga_tem():
    candidato = perfil(habilidades=["Python"])
    candidato.areas_recusadas = [AreaDeInteresse.DADOS_IA, AreaDeInteresse.QA_TESTES]

    resultado = resultado_da(
        extracao(areas_da_vaga=["desenvolvimento_web", "qa_testes", "dados_ia"]), candidato
    )

    assert resultado.avisos_objetivos == [
        "Área que você recusou nos últimos dias: Dados e IA, QA e testes"
    ]


def perfil_de_direito(habilidades: list[str]) -> Perfil:
    return Perfil(
        curso="Direito",
        periodo=4,
        habilidades=habilidades,
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.REMOTO,
    )


def extracao_juridica(obrigatorias: list[str]) -> ExtracaoDaVaga:
    return ExtracaoDaVaga(
        id_vaga="vaga-1",
        area_da_vaga="direito",
        cursos_aceitos=["Direito"],
        habilidades_obrigatorias=obrigatorias,
    )


def test_perfis_iniciantes_de_computacao_e_direito_recebem_nota_finita_sem_requisito_atendido():
    casos = [
        (
            Perfil(
                curso="Engenharia de Software",
                periodo=4,
                habilidades=[],
                cidade="Rio de Janeiro, RJ",
                modalidade=Modalidade.PRESENCIAL,
            ),
            extracao(habilidades_obrigatorias=["Python"]),
        ),
        (
            perfil_de_direito([]),
            extracao_juridica(["Excel"]),
        ),
    ]

    for candidato, vaga_extraida in casos:
        resultado = pontuar(vaga(), vaga_extraida, candidato)

        assert math.isfinite(resultado.nota)
        assert 0 <= resultado.nota <= 100
        assert resultado.requisitos_atendidos == []
        assert resultado.requisitos_nao_atendidos


def test_perfil_iniciante_preserva_limites_de_curso_e_modalidade():
    candidato = Perfil(
        curso="Direito",
        periodo=4,
        habilidades=[],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.REMOTO,
    )
    resultado = pontuar(
        vaga(modalidade=Modalidade.PRESENCIAL),
        extracao(cursos_aceitos=["Engenharia de Software"], habilidades_obrigatorias=["Python"]),
        candidato,
    )

    assert resultado.nota <= 35
    assert resultado.requisitos_atendidos == []


def test_nivel_basico_nao_satisfaz_requisito_avancado():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Inglês fluente", "Excel avançado"]),
        perfil_de_direito(["Inglês básico", "Excel básico"]),
    )

    assert resultado.requisitos_atendidos == []
    assert resultado.requisitos_nao_atendidos == ["Inglês fluente", "Excel avançado"]
    assert resultado.nota < 100


def test_nivel_igual_ou_maior_satisfaz_o_requisito():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Inglês intermediário", "Excel avançado"]),
        perfil_de_direito(["Inglês avançado", "Excel avançado"]),
    )

    assert resultado.requisitos_atendidos == ["Inglês intermediário", "Excel avançado"]
    assert resultado.requisitos_nao_atendidos == []


def test_nivel_desconhecido_nao_comprova_proficiencia_exigida():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Inglês fluente", "Excel avançado"]),
        perfil_de_direito(["Inglês", "Excel"]),
    )
    assert resultado.requisitos_atendidos == []
    assert resultado.requisitos_nao_atendidos == ["Inglês fluente", "Excel avançado"]
    assert resultado.nota < 100


def test_requisito_sem_nivel_aceita_habilidade_conhecida():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Inglês", "Office 365"]),
        perfil_de_direito(["Inglês", "Pacote Office básico"]),
    )
    assert resultado.requisitos_atendidos == ["Inglês", "Office 365"]
    assert resultado.requisitos_nao_atendidos == []


def test_requisito_generico_e_atendido_por_habilidade_especifica_da_familia():
    resultado = pontuar(
        vaga(),
        extracao(habilidades_obrigatorias=["banco de dados", "front-end", "back-end", "ETL"]),
        perfil(["SQL", "Java", "Spring Boot", "Python", "Django", "MySQL"]),
    )

    assert resultado.requisitos_atendidos == ["banco de dados", "back-end", "ETL"]
    assert resultado.requisitos_nao_atendidos == ["front-end"]


def test_familia_respeita_o_nivel_exigido():
    exigente = extracao(habilidades_obrigatorias=["banco de dados avançado"])

    assert pontuar(vaga(), exigente, perfil(["SQL básico"])).requisitos_atendidos == []
    assert pontuar(vaga(), exigente, perfil(["SQL avançado"])).requisitos_atendidos == [
        "banco de dados avançado"
    ]


def test_programacao_e_atendida_por_qualquer_linguagem():
    generica = extracao(habilidades_obrigatorias=["Programação", "Lógica de programação"])

    assert pontuar(vaga(), generica, perfil(["Lua"])).requisitos_nao_atendidos == []
    assert pontuar(vaga(), generica, perfil(["Excel"])).requisitos_nao_atendidos == [
        "Programação",
        "Lógica de programação",
    ]


def test_pacote_office_e_atendido_por_excel_fora_de_computacao():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Pacote Office", "Inglês"]),
        perfil_de_direito(["Excel", "Inglês"]),
    )

    assert resultado.requisitos_atendidos == ["Pacote Office", "Inglês"]
    assert resultado.requisitos_nao_atendidos == []


def test_vaga_que_so_pede_soft_skills_e_tratada_como_sem_stack_em_computacao():
    so_soft_skills = resultado_da(
        extracao(habilidades_obrigatorias=["Comunicação", "Proatividade", "Trabalho em equipe"])
    )
    sem_stack = resultado_da(extracao())

    assert so_soft_skills.nota == sem_stack.nota
    assert so_soft_skills.requisitos_nao_atendidos == [
        "Comunicação",
        "Proatividade",
        "Trabalho em equipe",
    ]


def test_soft_skill_continua_contando_fora_de_computacao():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Comunicação", "Redação"]),
        perfil_de_direito(["Comunicação", "Redação"]),
    )

    assert resultado.requisitos_atendidos == ["Comunicação", "Redação"]
    assert resultado.requisitos_nao_atendidos == []


def test_complemento_entre_parenteses_nao_esconde_a_familia_nem_o_nivel():
    resultado = pontuar(
        vaga(),
        extracao(habilidades_obrigatorias=["Front-end (React)", "Excel (avançado)"]),
        perfil(["HTML", "CSS", "Excel básico"]),
    )

    assert resultado.requisitos_atendidos == ["Front-end (React)"]
    assert resultado.requisitos_nao_atendidos == ["Excel (avançado)"]


def test_variantes_de_banco_de_dados_e_ia_tambem_sao_familias():
    resultado = pontuar(
        vaga(),
        extracao(habilidades_obrigatorias=["Bancos de dados relacionais", "IA generativa"]),
        perfil(["PostgreSQL", "LLM"]),
    )

    assert resultado.requisitos_nao_atendidos == []


def test_desejaveis_que_faltam_viram_diferenciais_sem_repetir_os_atendidos():
    resultado = pontuar(
        vaga(),
        extracao(
            habilidades_obrigatorias=["Java"],
            habilidades_desejaveis=["Angular", "Spring", "Java", "Python"],
        ),
        perfil(["Java", "Python"]),
    )

    assert resultado.requisitos_atendidos == ["Java", "Python"]
    assert resultado.requisitos_nao_atendidos == []
    assert resultado.diferenciais_nao_atendidos == ["Angular", "Spring"]


def test_diferencial_nao_entra_nos_requisitos_a_conferir():
    com_desejaveis = pontuar(
        vaga(),
        extracao(habilidades_obrigatorias=["Java"], habilidades_desejaveis=["Angular"]),
        perfil(["Java"]),
    )

    assert com_desejaveis.requisitos_nao_atendidos == []
    assert com_desejaveis.diferenciais_nao_atendidos == ["Angular"]


def test_habilidade_do_perfil_contida_no_requisito_o_atende():
    resultado = pontuar(
        vaga(),
        extracao_juridica(
            [
                "revisão de contratos",
                "atendimento ao público",
                "organização de arquivos",
                "redação de peças processuais",
            ]
        ),
        perfil_de_direito(["Contratos", "Atendimento", "Organização", "Redação"]),
    )

    assert resultado.requisitos_nao_atendidos == []


def test_requisito_generico_contido_na_habilidade_do_perfil_e_atendido():
    assert pontuar(
        vaga(), extracao_juridica(["pesquisas"]), perfil_de_direito(["Pesquisa jurídica"])
    ).requisitos_atendidos == ["pesquisas"]


def test_computacao_nao_compara_habilidade_por_palavras():
    resultado = pontuar(
        vaga(),
        extracao(
            habilidades_obrigatorias=[
                "Angular JS",
                "Node JS",
                "React Native",
                "PL/SQL",
                "C/C++",
                "HTML/CSS/JavaScript",
                "Spring",
                "comunicação verbal",
            ]
        ),
        perfil(["Python", "JavaScript", "React", "SQL", "C", "HTML", "Spring Boot", "Comunicação"]),
    )

    assert resultado.requisitos_atendidos == []


def test_requisito_composto_de_computacao_e_atendido_quando_todas_as_partes_batem():
    resultado = pontuar(
        vaga(),
        extracao(habilidades_obrigatorias=["HTML/CSS/JavaScript"]),
        perfil(["HTML", "CSS", "JavaScript"]),
    )

    assert resultado.requisitos_atendidos == ["HTML/CSS/JavaScript"]


@pytest.mark.parametrize(
    ("do_perfil", "exigida", "atende"),
    [
        (["Excel"], "Excel e Power BI", False),
        (["Excel", "Power BI"], "Excel e Power BI", True),
        (["SQL"], "SQL/Python", False),
        (["Inglês"], "Inglês e Espanhol", False),
        (["Contratos", "Redação"], "revisão de contratos e redação", True),
    ],
)
def test_requisito_composto_exige_todas_as_partes(do_perfil, exigida: str, atende: bool):
    resultado = pontuar(vaga(), extracao_juridica([exigida]), perfil_de_direito(do_perfil))

    assert (resultado.requisitos_atendidos == [exigida]) is atende


def test_nivel_de_uma_parte_da_habilidade_nao_vaza_para_a_outra():
    estudante = perfil_de_direito(["Inglês fluente e Espanhol básico"])

    assert pontuar(vaga(), extracao_juridica(["Espanhol avançado"]), estudante).nota < 100
    assert (
        pontuar(vaga(), extracao_juridica(["Espanhol avançado"]), estudante).requisitos_atendidos
        == []
    )
    assert pontuar(
        vaga(), extracao_juridica(["Inglês avançado"]), estudante
    ).requisitos_atendidos == ["Inglês avançado"]


def test_nivel_dito_uma_vez_vale_para_todas_as_partes_do_requisito():
    exigente = extracao_juridica(["Inglês e Espanhol avançados"])

    assert pontuar(
        vaga(), exigente, perfil_de_direito(["Inglês avançado", "Espanhol fluente"])
    ).requisitos_atendidos == ["Inglês e Espanhol avançados"]
    assert (
        pontuar(
            vaga(), exigente, perfil_de_direito(["Inglês avançado", "Espanhol"])
        ).requisitos_atendidos
        == []
    )


def test_acrescentar_habilidade_ao_perfil_nunca_derruba_o_que_ja_era_atendido():
    exigente = extracao_juridica(["Inglês avançado"])
    so_tecnico = perfil_de_direito(["Inglês técnico avançado"])
    com_basico = perfil_de_direito(["Inglês técnico avançado", "Inglês básico"])

    assert pontuar(vaga(), exigente, so_tecnico).requisitos_atendidos == ["Inglês avançado"]
    assert pontuar(vaga(), exigente, com_basico).requisitos_atendidos == ["Inglês avançado"]


def test_familia_decide_sozinha_o_requisito_que_nomeia():
    resultado = pontuar(
        vaga(), extracao_juridica(["banco de dados"]), perfil_de_direito(["Estrutura de dados"])
    )

    assert resultado.requisitos_atendidos == []


def test_apelido_de_tecnologia_nao_vale_palavra_por_palavra():
    resultado = pontuar(vaga(), extracao_juridica(["React JS"]), perfil_de_direito(["JavaScript"]))

    assert resultado.requisitos_atendidos == []


@pytest.mark.parametrize(
    ("do_perfil", "exigida"),
    [
        ("Contrato", "contratos"),
        ("Petição", "elaboração de petições"),
        ("Rede social", "redes sociais"),
        ("API", "APIs REST"),
        ("Gestor de tráfego", "gestores de tráfego"),
        ("Software", "softwares de gestão"),
        ("Contábil", "rotinas contábeis"),
        ("Processo civil", "processos civis"),
    ],
)
def test_plural_nao_impede_a_correspondencia_por_palavras(do_perfil: str, exigida: str):
    resultado = pontuar(vaga(), extracao_juridica([exigida]), perfil_de_direito([do_perfil]))

    assert resultado.requisitos_atendidos == [exigida]


@pytest.mark.parametrize(
    ("do_perfil", "exigida"),
    [
        ("Java", "JavaScript"),
        ("Word", "WordPress"),
        ("SQL", "MySQL"),
        ("Análise de dados", "análise de crédito"),
        ("Power BI", "Power Apps"),
        ("Redes", "Red Hat"),
    ],
)
def test_palavra_parecida_ou_so_uma_em_comum_nao_basta(do_perfil: str, exigida: str):
    resultado = pontuar(vaga(), extracao_juridica([exigida]), perfil_de_direito([do_perfil]))

    assert resultado.requisitos_atendidos == []
    assert resultado.requisitos_nao_atendidos == [exigida]


def test_nivel_continua_valendo_na_correspondencia_por_palavras():
    exigente = extracao_juridica(["inglês técnico avançado"])

    assert pontuar(vaga(), exigente, perfil_de_direito(["Inglês"])).requisitos_atendidos == []
    assert pontuar(
        vaga(), exigente, perfil_de_direito(["Inglês avançado"])
    ).requisitos_atendidos == ["inglês técnico avançado"]


def test_vaga_que_descreve_as_habilidades_do_perfil_passa_a_vaga_muda():
    estudante = perfil_de_direito(["Redação", "Pesquisa jurídica", "Contratos"])
    muda = ExtracaoDaVaga(id_vaga="vaga-1", area_da_vaga="direito", cursos_aceitos=["Direito"])
    descritiva = ExtracaoDaVaga(
        id_vaga="vaga-1",
        area_da_vaga="direito",
        cursos_aceitos=["Direito"],
        habilidades_principais=["pesquisas", "elaboração de petições", "revisão de contratos"],
    )

    assert pontuar(vaga(), descritiva, estudante).nota > pontuar(vaga(), muda, estudante).nota
