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

    assert sem_correspondencia.nota == 64
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

    assert resultado.nota == 64


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


def test_vaga_sem_requisito_atendido_nao_supera_vaga_sem_stack():
    sem_stack = resultado_da(extracao())
    pede_o_que_falta = resultado_da(
        extracao(habilidades_obrigatorias=["Excel"], habilidades_desejaveis=["Power BI"])
    )
    pede_uma_coisa = resultado_da(extracao(habilidades_obrigatorias=["C#"]))

    assert pede_o_que_falta.nota == sem_stack.nota
    assert pede_uma_coisa.nota == sem_stack.nota


def test_um_de_tres_atendido_fica_acima_de_um_so_requisito_nao_atendido():
    nenhum = resultado_da(extracao(habilidades_obrigatorias=["C#"]))
    um_de_tres = resultado_da(extracao(habilidades_obrigatorias=["Python", "C#", "Go"]))

    assert um_de_tres.nota > nenhum.nota


def test_office_atendido_nao_tira_vaga_de_computacao_do_teto_sem_atendidos():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Excel", "C#"]),
        perfil(habilidades=["Python", "Excel"]),
    )

    assert resultado.requisitos_atendidos == ["Excel"]
    assert resultado.nota == resultado_da(extracao()).nota


def test_teto_sem_requisito_atendido_vale_fora_de_computacao():
    candidato = perfil_de_direito(["Excel"])
    sem_stack = pontuar(vaga(), extracao_juridica([]), candidato)
    nao_atendido = pontuar(vaga(), extracao_juridica(["Contratos"]), candidato)

    assert nao_atendido.nota == sem_stack.nota


def test_perfil_sem_habilidades_fica_no_teto_e_recebe_o_aviso():
    candidato = perfil_de_direito([])
    sem_stack = pontuar(vaga(), extracao_juridica([]), candidato)
    resultado = pontuar(vaga(), extracao_juridica(["Contratos"]), candidato)

    assert resultado.nota == sem_stack.nota
    assert "Nota calculada sem habilidades no seu perfil" in resultado.avisos_objetivos


def test_requisito_com_nivel_acima_do_perfil_nao_tira_a_vaga_do_teto():
    candidato = perfil_de_direito(["Inglês básico"])
    sem_stack = pontuar(vaga(), extracao_juridica([]), candidato)
    resultado = pontuar(vaga(), extracao_juridica(["Inglês fluente"]), candidato)

    assert resultado.requisitos_atendidos == []
    assert resultado.nota == sem_stack.nota


@pytest.mark.parametrize("lista", ["habilidades_principais", "habilidades_desejaveis"])
def test_requisito_atendido_em_qualquer_lista_tira_a_vaga_do_teto_sem_atendidos(lista):
    resultado = resultado_da(extracao(habilidades_obrigatorias=["C#"], **{lista: ["Python"]}))

    assert resultado.nota > resultado_da(extracao()).nota


def test_c_nao_corresponde_a_csharp_nem_a_cpp():
    resultado = resultado_da(
        extracao(habilidades_desejaveis=["C#", "C++"]), perfil(habilidades=["C"])
    )

    assert resultado.nota == 64


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


def perfil_de_administracao(periodo: int) -> Perfil:
    return Perfil(
        curso="Administração",
        periodo=periodo,
        habilidades=["Pacote Office"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.HIBRIDO,
    )


def extracao_de_administracao(**alteracoes) -> ExtracaoDaVaga:
    dados = {
        "id_vaga": "adzuna:5882921354",
        "modalidade": "hibrido",
        "area_da_vaga": "administracao",
        "areas_da_vaga": ["rotinas_administrativas"],
        "cursos_aceitos": ["Administração"],
        "periodo_minimo": 4,
        "habilidades_principais": ["pacote Office"],
    }
    dados.update(alteracoes)
    return ExtracaoDaVaga.model_validate(dados)


def test_vaga_que_exige_periodo_acima_do_perfil_fica_abaixo_da_nota_minima_com_aviso():
    resultado = resultado_da(extracao_de_administracao(), perfil_de_administracao(1))

    assert resultado.nota == 35
    assert resultado.avisos_objetivos == ["Exige a partir do 4º período"]
    assert resultado.pontos_contra == []


def test_periodo_igual_ao_minimo_nao_limita_a_nota():
    resultado = resultado_da(extracao_de_administracao(), perfil_de_administracao(4))

    assert resultado.nota == 100
    assert resultado.avisos_objetivos == []


def test_periodo_acima_do_minimo_nao_limita_a_nota():
    resultado = resultado_da(extracao_de_administracao(), perfil_de_administracao(7))

    assert resultado.nota == 100
    assert resultado.avisos_objetivos == []


def test_vaga_sem_periodo_minimo_nao_limita_a_nota():
    resultado = resultado_da(
        extracao_de_administracao(periodo_minimo=None), perfil_de_administracao(1)
    )

    assert resultado.nota == 100
    assert resultado.avisos_objetivos == []


def test_curso_e_periodo_incompativeis_juntos_dao_um_teto_so_e_os_dois_avisos():
    resultado = resultado_da(
        extracao_de_administracao(cursos_aceitos=["Engenharia Civil"]), perfil_de_administracao(1)
    )

    assert resultado.nota == 35
    assert resultado.avisos_objetivos == [
        "Exige formação de outra área",
        "Exige a partir do 4º período",
    ]


def test_experiencia_exigida_vira_ponto_contra_e_o_periodo_vira_aviso():
    resultado = resultado_da(extracao(periodo_minimo=8, experiencia_minima_anos=2))

    assert resultado.pontos_contra == ["Exige experiência prévia"]
    assert resultado.avisos_objetivos == ["Exige a partir do 8º período"]


def test_experiencia_exigida_continua_sem_teto_de_elegibilidade():
    resultado = resultado_da(
        extracao(experiencia_minima_anos=2, habilidades_obrigatorias=["Python", "Java"])
    )

    assert resultado.nota == 83
    assert resultado.pontos_contra == ["Exige experiência prévia"]
    assert resultado.avisos_objetivos == []


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


@pytest.mark.parametrize(
    "requisito", ["planilhas", "planilhas eletrônicas", "Planilha eletrônica", "Google Sheets"]
)
def test_planilhas_sao_atendidas_por_excel_fora_de_computacao(requisito):
    resultado = pontuar(vaga(), extracao_juridica([requisito]), perfil_de_direito(["Excel"]))

    assert resultado.requisitos_atendidos == [requisito]


def test_planilhas_nao_sao_atendidas_por_word():
    resultado = pontuar(
        vaga(), extracao_juridica(["planilhas eletrônicas"]), perfil_de_direito(["Word"])
    )

    assert resultado.requisitos_atendidos == []


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


BANCOS_RELACIONAIS = [
    "MySQL",
    "PostgreSQL",
    "Postgres",
    "SQL Server",
    "Oracle Database",
    "SQLite",
    "MariaDB",
]
DIALETOS_DE_SQL = ["PL/SQL", "T-SQL"]
BANCOS_NAO_RELACIONAIS = ["MongoDB", "Redis", "DynamoDB", "Firebase", "NoSQL"]


@pytest.mark.parametrize("banco", BANCOS_RELACIONAIS + DIALETOS_DE_SQL)
def test_requisito_sql_e_atendido_por_banco_relacional_do_perfil(banco: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=["SQL"]), perfil([banco]))

    assert resultado.requisitos_atendidos == ["SQL"]
    assert resultado.requisitos_nao_atendidos == []


@pytest.mark.parametrize("banco", BANCOS_NAO_RELACIONAIS)
def test_requisito_sql_nao_e_atendido_por_banco_nao_relacional(banco: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=["SQL"]), perfil([banco]))

    assert resultado.requisitos_atendidos == []


def test_banco_relacional_atendendo_sql_tira_a_vaga_do_teto_sem_atendidos():
    exige_sql = extracao(habilidades_obrigatorias=["SQL"])

    com_mysql = pontuar(vaga(), exige_sql, perfil(["MySQL"]))
    com_mongodb = pontuar(vaga(), exige_sql, perfil(["MongoDB"]))

    assert com_mysql.nota > com_mongodb.nota


def test_sql_com_nivel_exige_o_nivel_declarado_no_banco_relacional():
    exigente = extracao(habilidades_obrigatorias=["SQL avançado"])

    assert pontuar(vaga(), exigente, perfil(["MySQL"])).requisitos_atendidos == []
    assert pontuar(vaga(), exigente, perfil(["MySQL básico"])).requisitos_atendidos == []
    assert pontuar(vaga(), exigente, perfil(["MySQL avançado"])).requisitos_atendidos == [
        "SQL avançado"
    ]


@pytest.mark.parametrize("banco", BANCOS_RELACIONAIS)
def test_banco_relacional_exigido_e_atendido_por_sql_do_perfil(banco: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[banco]), perfil(["SQL"]))

    assert resultado.requisitos_atendidos == [banco]
    assert resultado.requisitos_nao_atendidos == []


@pytest.mark.parametrize(
    ("do_perfil", "exigida"),
    [
        ("PostgreSQL", "MySQL"),
        ("MySQL", "PostgreSQL"),
        ("Postgres", "SQL Server"),
        ("SQLite", "MariaDB"),
        ("MySQL", "Oracle Database"),
        ("MySQL", "Oracle"),
        ("T-SQL", "MySQL"),
    ],
)
def test_sql_e_bancos_relacionais_formam_uma_classe_so(do_perfil: str, exigida: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil([do_perfil]))

    assert resultado.requisitos_atendidos == [exigida]


def test_banco_especifico_no_perfil_vale_o_mesmo_que_sql_generico():
    exige_tres_bancos = extracao(habilidades_obrigatorias=["PostgreSQL", "MySQL", "Oracle"])

    com_sql = pontuar(vaga(), exige_tres_bancos, perfil(["SQL"]))
    com_mysql = pontuar(vaga(), exige_tres_bancos, perfil(["MySQL"]))

    assert com_mysql.requisitos_atendidos == com_sql.requisitos_atendidos
    assert com_mysql.nota == com_sql.nota


def test_nivel_exigido_vale_dentro_da_classe():
    exigente = extracao(habilidades_obrigatorias=["MySQL avançado"])

    assert pontuar(vaga(), exigente, perfil(["PostgreSQL"])).requisitos_atendidos == []
    assert pontuar(vaga(), exigente, perfil(["PostgreSQL avançado"])).requisitos_atendidos == [
        "MySQL avançado"
    ]


@pytest.mark.parametrize("do_perfil", ["MySQL", "PostgreSQL"])
@pytest.mark.parametrize("exigida", DIALETOS_DE_SQL + BANCOS_NAO_RELACIONAIS)
def test_banco_relacional_nao_atende_dialeto_nem_banco_nao_relacional(do_perfil: str, exigida: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil([do_perfil]))

    assert resultado.requisitos_atendidos == []


@pytest.mark.parametrize("do_perfil", BANCOS_NAO_RELACIONAIS)
def test_banco_nao_relacional_nao_atende_banco_relacional(do_perfil: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=["MySQL"]), perfil([do_perfil]))

    assert resultado.requisitos_atendidos == []


@pytest.mark.parametrize("exigida", ["ETL", "análise de dados", "dados"])
@pytest.mark.parametrize("do_perfil", ["MySQL", "PostgreSQL", "SQL Server"])
def test_membro_da_classe_vale_pelo_sql_dentro_da_familia(do_perfil: str, exigida: str):
    exige_familia = extracao(habilidades_obrigatorias=[exigida])

    com_banco = pontuar(vaga(), exige_familia, perfil([do_perfil]))
    com_sql = pontuar(vaga(), exige_familia, perfil(["SQL"]))

    assert com_banco.requisitos_atendidos == com_sql.requisitos_atendidos == [exigida]
    assert com_banco.nota == com_sql.nota


@pytest.mark.parametrize("do_perfil", ["Oracle", "MongoDB"])
def test_quem_esta_fora_da_classe_nao_ganha_familia_pelo_sql(do_perfil: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=["ETL"]), perfil([do_perfil]))

    assert resultado.requisitos_atendidos == []


GRAFIAS_DE_PL_SQL = ["PL/SQL", "PL-SQL", "PLSQL", "pl / sql"]
GRAFIAS_DE_T_SQL = ["T-SQL", "TSQL", "Transact-SQL"]
REQUISITOS_PARA_AS_GRAFIAS = [
    "SQL",
    "MySQL",
    "Oracle",
    "banco de dados",
    "ETL",
    "PL/SQL",
    "T-SQL",
    "SQL Server Reporting Services",
]


def extracao_de_computacao(obrigatorias: list[str]) -> ExtracaoDaVaga:
    return extracao(habilidades_obrigatorias=obrigatorias)


@pytest.mark.parametrize("grafias", [GRAFIAS_DE_PL_SQL, GRAFIAS_DE_T_SQL])
@pytest.mark.parametrize(
    ("candidato", "vaga_do_contexto"),
    [(perfil, extracao_de_computacao), (perfil_de_direito, extracao_juridica)],
)
def test_todas_as_grafias_do_dialeto_dao_o_mesmo_resultado(grafias, candidato, vaga_do_contexto):
    def resultados(grafia: str) -> list[tuple[list[str], int]]:
        return [
            (resultado.requisitos_atendidos, resultado.nota)
            for resultado in (
                pontuar(vaga(), vaga_do_contexto([exigida]), candidato([grafia]))
                for exigida in REQUISITOS_PARA_AS_GRAFIAS
            )
        ]

    primeira, *outras = grafias
    for grafia in outras:
        assert resultados(grafia) == resultados(primeira), grafia


@pytest.mark.parametrize("grafia", GRAFIAS_DE_PL_SQL + GRAFIAS_DE_T_SQL)
@pytest.mark.parametrize("exigida", ["SQL", "MySQL", "banco de dados", "ETL"])
def test_dialeto_no_perfil_implica_sql_em_qualquer_grafia(grafia: str, exigida: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil([grafia]))

    assert resultado.requisitos_atendidos == [exigida]


@pytest.mark.parametrize("exigida", GRAFIAS_DE_PL_SQL + GRAFIAS_DE_T_SQL)
@pytest.mark.parametrize("do_perfil", ["SQL", "MySQL"])
def test_dialeto_exigido_em_qualquer_grafia_nao_e_atendido_por_sql_nem_banco(
    do_perfil: str, exigida: str
):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil([do_perfil]))

    assert resultado.requisitos_atendidos == []


@pytest.mark.parametrize(
    ("do_perfil", "exigida", "atende"),
    [
        ("PL-SQL", "PL/SQL", True),
        ("PL/SQL", "PLSQL", True),
        ("TSQL", "T-SQL", True),
        ("Transact-SQL", "T-SQL", True),
        ("PL/SQL", "T-SQL", False),
        ("T-SQL", "PL-SQL", False),
    ],
)
def test_dialeto_exigido_e_atendido_so_pelo_proprio_dialeto(
    do_perfil: str, exigida: str, atende: bool
):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil([do_perfil]))

    assert (resultado.requisitos_atendidos == [exigida]) is atende


FORMAS_COMPOSTAS_DA_CLASSE = [
    "Banco de dados SQL",
    "Linguagem SQL",
    "Consultas SQL",
    "Microsoft SQL Server",
    "MS SQL Server",
    "Oracle Database",
    "Oracle DB",
    "Azure SQL Database",
    "Postgre",
]
FORMAS_FORA_DA_CLASSE = [
    "NoSQL",
    "Banco de dados NoSQL",
    "MySQL Workbench",
    "SQL Server Reporting Services",
    "SSRS",
    "Oracle ERP",
    "Oracle Cloud",
]


@pytest.mark.parametrize("forma", FORMAS_COMPOSTAS_DA_CLASSE)
def test_forma_composta_exigida_e_atendida_por_sql_em_computacao(forma: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[forma]), perfil(["SQL"]))

    assert resultado.requisitos_atendidos == [forma]


@pytest.mark.parametrize("forma", FORMAS_COMPOSTAS_DA_CLASSE)
def test_forma_composta_no_perfil_atende_sql_em_computacao(forma: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=["SQL"]), perfil([forma]))

    assert resultado.requisitos_atendidos == ["SQL"]


@pytest.mark.parametrize("forma", FORMAS_FORA_DA_CLASSE)
def test_forma_que_nao_e_banco_relacional_fica_fora_da_classe(forma: str):
    exige_forma = pontuar(vaga(), extracao(habilidades_obrigatorias=[forma]), perfil(["SQL"]))
    forma_no_perfil = pontuar(vaga(), extracao(habilidades_obrigatorias=["SQL"]), perfil([forma]))

    assert exige_forma.requisitos_atendidos == []
    assert forma_no_perfil.requisitos_atendidos == []


@pytest.mark.parametrize(
    ("do_perfil", "exigidas"),
    [
        ("Azure SQL Database", ["SQL Server avançado", "Azure SQL Database"]),
        ("Consultas SQL", ["SQL avançado", "Consultas SQL"]),
        ("Linguagem SQL", ["SQL básico", "Linguagem SQL"]),
        ("Microsoft SQL Server", ["SQL Server intermediário", "Microsoft SQL Server"]),
        ("Postgre", ["PostgreSQL avançado", "Postgre"]),
        ("Oracle DB", ["Oracle Database avançado", "Oracle DB"]),
    ],
)
def test_requisito_juntado_pelo_alias_nao_herda_o_nivel_do_outro(
    do_perfil: str, exigidas: list[str]
):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=exigidas), perfil([do_perfil]))

    assert resultado.requisitos_atendidos == [exigidas[1]]
    assert resultado.requisitos_nao_atendidos == [exigidas[0]]


def test_desejavel_juntado_pelo_alias_continua_nos_diferenciais():
    resultado = pontuar(
        vaga(),
        extracao(
            habilidades_obrigatorias=["SQL Server"], habilidades_desejaveis=["Azure SQL Database"]
        ),
        perfil(["MongoDB"]),
    )

    assert resultado.requisitos_nao_atendidos == ["SQL Server"]
    assert resultado.diferenciais_nao_atendidos == ["Azure SQL Database"]


def test_requisitos_juntados_pelo_alias_aparecem_com_os_nomes_do_anuncio():
    resultado = pontuar(
        vaga(),
        extracao(
            habilidades_obrigatorias=["SQL SERVER"], habilidades_desejaveis=["Azure SQL Database"]
        ),
        perfil(["SQL Server"]),
    )

    assert resultado.requisitos_atendidos == ["SQL SERVER", "Azure SQL Database"]


DIALETO_EM_HABILIDADE_COMPOSTA = [
    "Oracle PL/SQL",
    "Linguagem PL/SQL",
    "Programação PL/SQL",
    "Procedures PL/SQL",
    "Banco de dados Oracle PL/SQL",
    "Oracle PL-SQL",
    "Procedures em T-SQL",
]


@pytest.mark.parametrize("habilidade", DIALETO_EM_HABILIDADE_COMPOSTA)
@pytest.mark.parametrize("exigida", ["SQL", "banco de dados", "ETL", "análise de dados"])
def test_dialeto_dentro_de_habilidade_composta_continua_implicando_sql(
    habilidade: str, exigida: str
):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil([habilidade]))

    assert resultado.requisitos_atendidos == [exigida]


@pytest.mark.parametrize("habilidade", DIALETO_EM_HABILIDADE_COMPOSTA)
def test_dialeto_em_habilidade_composta_implica_sql_fora_de_computacao(habilidade: str):
    resultado = pontuar(
        vaga(), extracao_juridica(["SQL", "Consultas SQL"]), perfil_de_direito([habilidade])
    )

    assert resultado.requisitos_atendidos == ["SQL", "Consultas SQL"]


def test_oracle_no_perfil_nao_atende_oracle_pl_sql_por_palavras():
    resultado = pontuar(vaga(), extracao_juridica(["Oracle PL/SQL"]), perfil_de_direito(["Oracle"]))

    assert resultado.requisitos_atendidos == []


@pytest.mark.parametrize("grafia", GRAFIAS_DE_PL_SQL + GRAFIAS_DE_T_SQL)
def test_dialeto_leva_a_palavra_sql_fora_de_computacao(grafia: str):
    resultado = pontuar(
        vaga(), extracao_juridica(["SQL Server Reporting Services"]), perfil_de_direito([grafia])
    )

    assert resultado.requisitos_atendidos == ["SQL Server Reporting Services"]


@pytest.mark.parametrize("dialeto", DIALETOS_DE_SQL)
def test_dialeto_de_sql_exigido_nao_e_atendido_so_por_sql(dialeto: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[dialeto]), perfil(["SQL"]))

    assert resultado.requisitos_atendidos == []


@pytest.mark.parametrize("banco", BANCOS_NAO_RELACIONAIS)
def test_banco_nao_relacional_exigido_nao_e_atendido_por_sql(banco: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[banco]), perfil(["SQL"]))

    assert resultado.requisitos_atendidos == []


def test_banco_relacional_com_nivel_exige_o_nivel_declarado_no_sql():
    exigente = extracao(habilidades_obrigatorias=["MySQL avançado"])

    assert pontuar(vaga(), exigente, perfil(["SQL"])).requisitos_atendidos == []
    assert pontuar(vaga(), exigente, perfil(["SQL avançado"])).requisitos_atendidos == [
        "MySQL avançado"
    ]


def test_banco_relacional_em_requisito_composto_nao_dispensa_as_outras_partes():
    composto = extracao(habilidades_obrigatorias=["MySQL e Python"])

    assert pontuar(vaga(), composto, perfil(["SQL"])).requisitos_atendidos == []
    assert pontuar(vaga(), composto, perfil(["SQL", "Python"])).requisitos_atendidos == [
        "MySQL e Python"
    ]


@pytest.mark.parametrize(
    ("do_perfil", "exigida", "nota_no_b1ccbf1"),
    [
        ("Consultas SQL", "SQL", 98),
        ("Banco de dados MySQL", "MySQL", 98),
        ("ERP Oracle", "Oracle", 98),
    ],
)
def test_equivalencia_de_bancos_nao_desliga_a_comparacao_por_palavras(
    do_perfil: str, exigida: str, nota_no_b1ccbf1: int
):
    resultado = pontuar(vaga(), extracao_juridica([exigida]), perfil_de_direito([do_perfil]))

    assert resultado.requisitos_atendidos == [exigida]
    assert resultado.nota == nota_no_b1ccbf1


@pytest.mark.parametrize("exigida", ["SQL", "MySQL", "Oracle Database"])
def test_oracle_no_perfil_nao_atende_a_classe_porque_tambem_e_nome_de_erp(exigida: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil(["Oracle"]))

    assert resultado.requisitos_atendidos == []


@pytest.mark.parametrize("do_perfil", ["SQL", "Oracle Database"])
@pytest.mark.parametrize("exigida", ["Oracle", "Oracle Database"])
def test_requisito_oracle_e_atendido_por_sql_ou_oracle_database(do_perfil: str, exigida: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil([do_perfil]))

    assert resultado.requisitos_atendidos == [exigida]


def test_oracle_como_erp_no_perfil_de_engenharia_nao_ganha_sql():
    engenharia = Perfil(
        curso="Engenharia de Produção",
        periodo=4,
        habilidades=["Excel", "Oracle", "SAP"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )
    exige_sql = extracao(area_da_vaga="engenharias", habilidades_obrigatorias=["SQL"])

    assert pontuar(vaga(), exige_sql, engenharia).requisitos_atendidos == []


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

    assert (
        pontuar(vaga(), extracao_juridica(["Espanhol avançado"]), estudante).requisitos_atendidos
        == []
    )
    assert pontuar(
        vaga(), extracao_juridica(["Inglês avançado"]), estudante
    ).requisitos_atendidos == ["Inglês avançado"]


def test_frase_com_dois_niveis_sem_separador_nao_compara_por_palavras():
    estudante = perfil_de_direito(["Inglês fluente Espanhol básico"])

    assert (
        pontuar(vaga(), extracao_juridica(["Espanhol avançado"]), estudante).requisitos_atendidos
        == []
    )


def test_nivel_dito_no_fim_vale_para_todas_as_partes_do_requisito():
    exigente = extracao_juridica(["Inglês e Espanhol avançados"])

    assert pontuar(
        vaga(), exigente, perfil_de_direito(["Inglês avançado", "Espanhol fluente"])
    ).requisitos_atendidos == ["Inglês e Espanhol avançados"]
    for sem_nivel in (["Inglês avançado", "Espanhol"], ["Inglês", "Espanhol avançado"]):
        assert pontuar(vaga(), exigente, perfil_de_direito(sem_nivel)).requisitos_atendidos == []


def test_nivel_dito_no_fim_da_habilidade_do_perfil_vale_para_todas_as_partes():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Inglês avançado"]),
        perfil_de_direito(["Inglês e Espanhol fluentes"]),
    )

    assert resultado.requisitos_atendidos == ["Inglês avançado"]


def test_nivel_dito_so_na_primeira_parte_nao_vale_para_as_outras():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Excel avançado e Power BI"]),
        perfil_de_direito(["Excel avançado", "Power BI"]),
    )

    assert resultado.requisitos_atendidos == ["Excel avançado e Power BI"]


def test_nivel_entre_parenteses_fica_com_a_propria_parte():
    exigente = extracao_juridica(["Inglês (avançado) e Espanhol (básico)"])

    assert (
        pontuar(
            vaga(), exigente, perfil_de_direito(["Inglês básico", "Espanhol básico"])
        ).requisitos_atendidos
        == []
    )
    assert pontuar(
        vaga(), exigente, perfil_de_direito(["Inglês avançado", "Espanhol básico"])
    ).requisitos_atendidos == ["Inglês (avançado) e Espanhol (básico)"]


def test_separador_dentro_de_parenteses_nao_parte_o_requisito():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["revisão de contratos (civis, trabalhistas)"]),
        perfil_de_direito(["Contratos"]),
    )

    assert resultado.requisitos_atendidos == ["revisão de contratos (civis, trabalhistas)"]


@pytest.mark.parametrize("exigida", ["Inglês ou Espanhol", "Inglês e/ou Espanhol"])
def test_ou_e_alternativa_e_basta_uma_parte(exigida: str):
    assert pontuar(
        vaga(), extracao_juridica([exigida]), perfil_de_direito(["Espanhol"])
    ).requisitos_atendidos == [exigida]
    assert (
        pontuar(
            vaga(), extracao_juridica([exigida]), perfil_de_direito(["Francês"])
        ).requisitos_atendidos
        == []
    )


@pytest.mark.parametrize("exigida", ["Excel & Power BI", "Excel + Power BI"])
def test_e_comercial_e_mais_com_espacos_juntam_partes(exigida: str):
    assert (
        pontuar(
            vaga(), extracao_juridica([exigida]), perfil_de_direito(["Excel"])
        ).requisitos_atendidos
        == []
    )
    assert pontuar(
        vaga(), extracao_juridica([exigida]), perfil_de_direito(["Excel", "Power BI"])
    ).requisitos_atendidos == [exigida]


def test_requisito_repetido_nao_depende_da_ordem_em_que_a_ia_listou():
    estudante = perfil_de_direito(["Excel"])
    uma_ordem = pontuar(
        vaga(), extracao_juridica(["Excel Power BI", "Excel / Power BI"]), estudante
    )
    outra_ordem = pontuar(
        vaga(), extracao_juridica(["Excel / Power BI", "Excel Power BI"]), estudante
    )

    assert uma_ordem.nota == outra_ordem.nota
    assert uma_ordem.requisitos_atendidos == outra_ordem.requisitos_atendidos == []


def test_acrescentar_habilidade_ao_perfil_nunca_derruba_o_que_ja_era_atendido():
    exigente = extracao_juridica(["Inglês avançado"])
    so_tecnico = perfil_de_direito(["Inglês técnico avançado"])
    com_basico = perfil_de_direito(["Inglês técnico avançado", "Inglês básico"])

    assert pontuar(vaga(), exigente, so_tecnico).requisitos_atendidos == ["Inglês avançado"]
    assert pontuar(vaga(), exigente, com_basico).requisitos_atendidos == ["Inglês avançado"]


def test_familia_decide_sozinha_o_requisito_que_nomeia():
    resultado = pontuar(
        vaga(), extracao_juridica(["Dados"]), perfil_de_direito(["Estrutura de dados"])
    )

    assert resultado.requisitos_atendidos == []


def test_vaga_de_computacao_nao_compara_por_palavras_nem_para_quem_e_de_outro_curso():
    estatistica = Perfil(
        curso="Estatística",
        periodo=4,
        habilidades=["React", "Angular", "Spring"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )
    de_computacao = extracao(
        cursos_aceitos=["Estatística"],
        habilidades_obrigatorias=["React Native", "Angular JS", "Spring Boot"],
    )

    assert pontuar(vaga(), de_computacao, estatistica).requisitos_atendidos == []


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
        ("SQL", "NoSQL"),
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


def test_nome_inteiro_do_requisito_composto_exige_o_maior_nivel_citado():
    exigente = extracao_juridica(["Inglês avançado e Espanhol básico"])

    for estudante in (["Inglês e Espanhol básicos"], ["Inglês (básico) e Espanhol (avançado)"]):
        assert pontuar(vaga(), exigente, perfil_de_direito(estudante)).requisitos_atendidos == []


def test_nome_inteiro_da_habilidade_composta_do_perfil_vale_pelo_menor_nivel():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Inglês e Espanhol avançados"]),
        perfil_de_direito(["Inglês (básico) e Espanhol (avançado)"]),
    )

    assert resultado.requisitos_atendidos == []


def test_nivel_se_espalha_so_dentro_da_propria_alternativa():
    assert (
        pontuar(
            vaga(),
            extracao_juridica(["Inglês e Espanhol avançados ou Francês"]),
            perfil_de_direito(["Inglês", "Espanhol avançado"]),
        ).requisitos_atendidos
        == []
    )
    assert pontuar(
        vaga(),
        extracao_juridica(["Inglês ou Espanhol e Francês avançado"]),
        perfil_de_direito(["Inglês"]),
    ).requisitos_atendidos == ["Inglês ou Espanhol e Francês avançado"]


def test_parte_com_nivel_proprio_nao_herda_o_da_ultima():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Excel básico e Word avançado"]),
        perfil_de_direito(["Excel básico", "Word avançado"]),
    )

    assert resultado.requisitos_atendidos == ["Excel básico e Word avançado"]


def test_parte_do_perfil_sem_nivel_nao_herda_o_da_primeira():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Espanhol básico"]),
        perfil_de_direito(["Inglês básico e Espanhol"]),
    )

    assert resultado.requisitos_atendidos == []


def test_parte_da_habilidade_composta_do_perfil_compara_por_palavras():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["revisão de contratos"]),
        perfil_de_direito(["Contratos e Redação"]),
    )

    assert resultado.requisitos_atendidos == ["revisão de contratos"]


@pytest.mark.parametrize(
    ("do_perfil", "exigida", "atende"),
    [
        (["Excel e Word iniciantes"], "Word", True),
        (["Excel e Word iniciantes"], "Word intermediário", False),
        (["Inglês e Espanhol nativos"], "Espanhol fluente", True),
        (["Inglês e Espanhol fluentes"], "Espanhol", True),
    ],
)
def test_nivel_no_plural_e_lido_e_sai_do_nome(do_perfil, exigida: str, atende: bool):
    resultado = pontuar(vaga(), extracao_juridica([exigida]), perfil_de_direito(do_perfil))

    assert (resultado.requisitos_atendidos == [exigida]) is atende


@pytest.mark.parametrize(
    ("do_perfil", "exigida"),
    [
        (["Python e Java iniciantes"], "Java básico"),
        (["Python e Java iniciantes"], "Java"),
        (["Python e Java fluentes"], "Java avançado"),
    ],
)
def test_nivel_no_plural_sai_do_nome_mesmo_sem_comparar_por_palavras(do_perfil, exigida: str):
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=[exigida]), perfil(do_perfil))

    assert resultado.requisitos_atendidos == [exigida]


@pytest.mark.parametrize("exigida", ["Excel; Power BI", "Excel | Power BI"])
def test_ponto_e_virgula_e_barra_vertical_juntam_partes(exigida: str):
    assert (
        pontuar(
            vaga(), extracao_juridica([exigida]), perfil_de_direito(["Excel"])
        ).requisitos_atendidos
        == []
    )


def test_trava_pela_area_da_vaga_vale_tambem_na_nota():
    def estatistica(habilidades: list[str]) -> Perfil:
        return Perfil(
            curso="Estatística",
            periodo=4,
            habilidades=habilidades,
            cidade="Rio de Janeiro, RJ",
            modalidade=Modalidade.PRESENCIAL,
        )

    de_computacao = extracao(
        cursos_aceitos=["Estatística"],
        habilidades_obrigatorias=["React Native", "Angular JS", "Spring Boot"],
    )

    assert (
        pontuar(vaga(), de_computacao, estatistica(["React", "Angular", "Spring"])).nota
        == pontuar(vaga(), de_computacao, estatistica(["Cobol"])).nota
    )


def test_trava_pelo_curso_vale_mesmo_em_vaga_de_outra_area():
    de_financas = extracao(area_da_vaga="financas", habilidades_obrigatorias=["React Native"])

    assert pontuar(vaga(), de_financas, perfil(["React"])).requisitos_atendidos == []


def test_versao_mais_exigente_do_requisito_repetido_decide_a_nota():
    estudante = perfil_de_direito(["Excel"])
    repetido = pontuar(vaga(), extracao_juridica(["Excel Power BI", "Excel / Power BI"]), estudante)
    so_exigente = pontuar(vaga(), extracao_juridica(["Excel / Power BI"]), estudante)

    assert repetido.nota == so_exigente.nota


def test_mensagem_mostra_a_versao_do_requisito_que_falta():
    resultado = pontuar(
        vaga(),
        ExtracaoDaVaga(
            id_vaga="vaga-1",
            area_da_vaga="direito",
            cursos_aceitos=["Direito"],
            habilidades_obrigatorias=["Excel"],
            habilidades_principais=["Excel avançado"],
        ),
        perfil_de_direito(["Excel"]),
    )

    assert resultado.requisitos_nao_atendidos == ["Excel avançado"]


def test_desejavel_que_repete_uma_exigida_nao_vira_diferencial():
    resultado = pontuar(
        vaga(),
        ExtracaoDaVaga(
            id_vaga="vaga-1",
            area_da_vaga="direito",
            cursos_aceitos=["Direito"],
            habilidades_obrigatorias=["Java"],
            habilidades_desejaveis=["Java avançado"],
        ),
        perfil_de_direito(["Python"]),
    )

    assert resultado.requisitos_nao_atendidos == ["Java"]
    assert resultado.diferenciais_nao_atendidos == []


@pytest.mark.parametrize(
    ("exigida", "do_perfil", "atende"),
    [
        ("Inglês intermediário/avançado", "Inglês intermediário", True),
        ("Excel básico/intermediário", "Excel básico", True),
        ("Inglês: intermediário/avançado", "Inglês intermediário", True),
        ("Inglês intermediário, avançado", "Inglês intermediário", True),
        ("Inglês intermediário/avançado", "Inglês básico", False),
        ("Inglês intermediário ou avançado", "Inglês intermediário", True),
        ("Inglês intermediário ou avançado", "Inglês básico", False),
        ("Inglês intermediário e avançado", "Inglês intermediário", True),
    ],
)
def test_faixa_de_nivel_escrita_com_separador_vale_pelo_menor(exigida, do_perfil, atende):
    resultado = pontuar(vaga(), extracao_juridica([exigida]), perfil_de_direito([do_perfil]))

    assert (resultado.requisitos_atendidos == [exigida]) is atende


@pytest.mark.parametrize(
    "exigida", ["Inglês intermediário ou avançado", "Experiência", "Conhecimentos avançados"]
)
def test_nivel_solto_depois_de_ou_no_perfil_nao_atende_requisito_algum(exigida):
    resultado = pontuar(
        vaga(),
        extracao_juridica([exigida]),
        perfil_de_direito(["Inglês básico", "Espanhol intermediário ou avançado"]),
    )

    assert resultado.requisitos_atendidos == []


def test_parte_sem_nivel_baixa_o_nivel_do_nome_inteiro_da_habilidade_do_perfil():
    resultado = pontuar(
        vaga(),
        extracao_juridica(["Inglês e Espanhol avançados"]),
        perfil_de_direito(["Inglês avançado e Espanhol"]),
    )

    assert resultado.requisitos_atendidos == []


def test_mensagem_mostra_a_versao_que_falta_em_qualquer_ordem():
    resultado = pontuar(
        vaga(),
        ExtracaoDaVaga(
            id_vaga="vaga-1",
            area_da_vaga="direito",
            cursos_aceitos=["Direito"],
            habilidades_obrigatorias=["Excel avançado"],
            habilidades_principais=["Excel"],
        ),
        perfil_de_direito(["Excel"]),
    )

    assert resultado.requisitos_nao_atendidos == ["Excel avançado"]


def test_exigida_atendida_aparece_mesmo_com_desejavel_mais_exigente():
    resultado = pontuar(
        vaga(),
        ExtracaoDaVaga(
            id_vaga="vaga-1",
            area_da_vaga="direito",
            cursos_aceitos=["Direito"],
            habilidades_obrigatorias=["Java"],
            habilidades_desejaveis=["Java avançado"],
        ),
        perfil_de_direito(["Java"]),
    )

    assert resultado.requisitos_atendidos == ["Java"]


def test_habilidade_composta_do_perfil_tambem_vale_pelo_nome_inteiro():
    resultado = pontuar(vaga(), extracao(habilidades_obrigatorias=["CI-CD"]), perfil(["CI/CD"]))

    assert resultado.requisitos_atendidos == ["CI-CD"]


def test_office_conta_para_quem_nao_e_de_computacao_mesmo_em_vaga_de_computacao():
    vaga_de_computacao = extracao(
        cursos_aceitos=["Direito"], habilidades_obrigatorias=["Excel", "Python"]
    )

    assert (
        pontuar(vaga(), vaga_de_computacao, perfil_de_direito(["Excel"])).nota
        > pontuar(vaga(), vaga_de_computacao, perfil_de_direito(["Cobol"])).nota
    )


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
