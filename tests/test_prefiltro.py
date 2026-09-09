from datetime import UTC, datetime

import pytest

from radar.domain.models import Modalidade, Perfil, Vaga
from radar.filtering.prefiltro import (
    deve_descartar,
    exige_anos_de_experiencia,
    exige_pos_graduacao,
    exige_senioridade,
    filtrar,
    fora_da_area_do_curso,
    localizacao_incompativel,
    modalidade_incompativel,
    nao_e_estagio,
)


def vaga(
    titulo: str = "Estágio em Desenvolvimento",
    descricao: str = "Vaga de estágio para estudantes de tecnologia.",
    localizacao: str = "Rio de Janeiro, Rio de Janeiro",
    modalidade: Modalidade | None = None,
) -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo=titulo,
        empresa="Empresa Exemplo",
        localizacao=localizacao,
        descricao=descricao,
        url="https://exemplo.com/vaga/1",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
        modalidade=modalidade,
    )


def perfil(
    modalidade: Modalidade = Modalidade.REMOTO,
    cidade: str = "Rio de Janeiro, RJ",
    curso: str = "Engenharia de Software",
) -> Perfil:
    return Perfil(
        curso=curso,
        periodo=4,
        habilidades=["Python"],
        cidade=cidade,
        modalidade=modalidade,
    )


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em TI",
        "ESTAGIO - CURSO TECNOLOGIA",
        "Estagiário de TI",
        "Estagiária de Dados",
        "Software Engineering Intern",
        "Internship - Data Science",
    ],
)
def test_reconhece_estagio_no_titulo_com_e_sem_acento(titulo: str):
    assert not nao_e_estagio(vaga(titulo=titulo))


@pytest.mark.parametrize(
    "titulo",
    [
        "Analista Suporte Técnico",
        "Preceptor - Fisioterapia - Estácio Angra Dos Reis",
        "Analista de Internet",
        "International Sales Analyst",
    ],
)
def test_descarta_titulo_que_nao_e_estagio(titulo: str):
    assert nao_e_estagio(vaga(titulo=titulo))


@pytest.mark.parametrize(
    "titulo",
    [
        "Desenvolvedor Pleno",
        "Analista Sênior",
        "Analista Senior",
        "Especialista em Dados",
        "Coordenador de TI",
        "Estagiário Pleno",
    ],
)
def test_descarta_senioridade_no_titulo(titulo: str):
    assert exige_senioridade(vaga(titulo=titulo))


def test_senioridade_apenas_na_descricao_nao_descarta():
    descricao = "O estagiário reportará ao coordenador de TI e apoiará os especialistas."
    assert not exige_senioridade(vaga(descricao=descricao))


@pytest.mark.parametrize(
    "descricao",
    [
        "Requisito: 2 anos de experiência com Python.",
        "Experiência mínima de 3 anos.",
        "5+ anos de experiencia em suporte técnico",
        "Experiência de 2 anos em redes",
    ],
)
def test_descarta_exigencia_de_dois_ou_mais_anos_de_experiencia(descricao: str):
    assert exige_anos_de_experiencia(vaga(descricao=descricao))


@pytest.mark.parametrize(
    "descricao",
    [
        "Não exige experiência.",
        "1 ano de experiência é desejável.",
        "Empresa com 20 anos de experiência no mercado.",
        "Experiência com Python é um diferencial.",
    ],
)
def test_mantem_vaga_sem_exigencia_de_experiencia(descricao: str):
    assert not exige_anos_de_experiencia(vaga(descricao=descricao))


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em Técnico em Eletrônica",
        "Estagiário de Engenharia Mecânica",
        "Estágio Financeiro - Novo Hamburgo/RS",
        "Estagio Jurídico",
        "ESTÁGIO SUPERIOR - ENGENHARIA DE MANUFATURA",
        "Estagiário(a) de Treinamento e Desenvolvimento",
        "Estagiário de R&S",
        "Estágio em Turismo - 619",
        "Estágio em Arquitetura e Urbanismo",
        "Estagiário de Recrutamento e Seleção",
    ],
)
def test_descarta_titulo_de_outra_area(titulo: str):
    assert fora_da_area_do_curso(vaga(titulo=titulo), perfil())


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em Desenvolvimento de Software",
        "Estágio em Ciência de Dados",
        "Estagiário de TI - Suporte e Redes",
        "Estágio - Engenharia de Software",
        "Estágio em Engenharia da Computação",
    ],
)
def test_mantem_titulo_de_computacao(titulo: str):
    assert not fora_da_area_do_curso(vaga(titulo=titulo), perfil())


@pytest.mark.parametrize(
    "titulo",
    [
        "Estagiário(a) de T.I.",
        "Estágio em Ti - Infraestrutura",
        "Estagiário DevOps",
        "Estágio | Redes de Computadores, Sistemas de Informação",
        "Estágio Python",
        "Estágio Em Desenvolvimento Java - Recrutamento Aberto",
        "Estagiário - Arquitetura de Ti Vaga Afirmativa",
    ],
)
def test_reconhece_area_de_tecnologia_no_titulo(titulo: str):
    assert not fora_da_area_do_curso(vaga(titulo=titulo, descricao="Sem detalhes."), perfil())


@pytest.mark.parametrize(
    "titulo",
    [
        "Estagiário",
        "Programa de Estágio 2026.2",
        "Estágio de Hotelaria",
        "Estagiário de Endomarketing",
        "Estágio em Turismo",
    ],
)
def test_descarta_titulo_generico_sem_tecnologia_na_descricao(titulo: str):
    descricao = "Vaga para estudantes. Auxiliar a equipe nas rotinas do setor."
    assert fora_da_area_do_curso(vaga(titulo=titulo, descricao=descricao), perfil())


@pytest.mark.parametrize(
    "descricao",
    [
        "Buscamos estudantes de Ciência da Computação ou Sistemas de Informação.",
        "Atuar no desenvolvimento de software em Python.",
        "Apoiar o time de suporte técnico e help desk.",
        "Conhecimento em banco de dados e SQL.",
    ],
)
def test_mantem_titulo_generico_quando_descricao_e_de_tecnologia(descricao: str):
    assert not fora_da_area_do_curso(
        vaga(titulo="Programa de Estágio", descricao=descricao), perfil()
    )


def test_titulo_de_outra_area_e_descartado_mesmo_com_descricao_de_tecnologia():
    descricao = "Desejável conhecimento em programação em Python."
    assert fora_da_area_do_curso(
        vaga(titulo="Estágio em Eletrônica", descricao=descricao), perfil()
    )


@pytest.mark.parametrize(
    ("curso", "titulo"),
    [
        ("Direito", "Estagiário de Direito"),
        ("Ciências Contábeis", "Estagiário de contabilidade"),
        ("Publicidade e Propaganda", "Estagiário de marketing"),
        ("Psicologia", "Estágio em Recursos Humanos"),
        ("Logística", "Estágio em Logística"),
        ("Enfermagem", "Estagiário de Enfermagem"),
    ],
)
def test_mantem_a_vaga_da_area_do_curso_de_quem_nao_e_de_computacao(curso: str, titulo: str):
    assert not fora_da_area_do_curso(vaga(titulo=titulo), perfil(curso=curso))


@pytest.mark.parametrize(
    "titulo",
    ["Estágio em Desenvolvimento de Software", "Estagiário de TI", "Estagiário Programador"],
)
def test_descarta_vaga_de_computacao_para_quem_e_de_outro_curso(titulo: str):
    assert fora_da_area_do_curso(vaga(titulo=titulo), perfil(curso="Direito"))


def test_curso_sem_area_conhecida_recebe_titulos_genericos_e_nao_os_de_area_alheia():
    exotico = perfil(curso="Agronomia")

    for titulo in ("Programa de Estágio 2026", "Estagiário", "Estágio em Agronomia"):
        assert not fora_da_area_do_curso(vaga(titulo=titulo), exotico)
    for titulo in ("Estagiário de Direito", "Estágio em Desenvolvimento de Software"):
        assert fora_da_area_do_curso(vaga(titulo=titulo), exotico)


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio RH - Dados",
        "Estágio em Comércio Exterior, Processos e Tecnologia",
        "Estagiário(a) em Pré-Venda de Soluções de TI",
        "Estágio em CRM | Digital",
        "Estagiário(a) de People & Culture (People Analytics)",
    ],
)
def test_titulo_com_sinal_de_computacao_e_mantido_mesmo_citando_outra_area(titulo: str):
    assert not fora_da_area_do_curso(vaga(titulo=titulo), perfil())


@pytest.mark.parametrize(
    ("curso", "titulo"),
    [
        ("Direito", "Estágio em Direito Civil"),
        ("Direito", "Estágio Jurídico - Direito Comercial"),
        ("Administração", "Estágio Administrativo Financeiro"),
        ("Ciências Contábeis", "Estágio Administrativo Financeiro"),
        ("Publicidade e Propaganda", "Estágio em Marketing Comercial"),
        ("Comércio Exterior", "Estágio em Marketing Comercial"),
        ("Psicologia", "Estágio de Comunicação e RH"),
        ("Publicidade e Propaganda", "Estágio - Produção de Conteúdo"),
        ("Pedagogia", "Estágio em Produção de Material Didático"),
        ("Engenharia Civil", "Estágio em Engenharia"),
        ("Pedagogia", "Estágio em Educação Infantil"),
        ("Enfermagem", "Estágio em Saúde"),
        ("Design Gráfico", "Estágio em Design Gráfico"),
        ("Engenharia de Software", "Estágio Front End"),
        ("Administração", "Estágio Back Office"),
        ("Ciências Contábeis", "Estágio em Compliance"),
    ],
)
def test_sinal_da_propria_area_vence_o_veto_de_outra(curso: str, titulo: str):
    assert not fora_da_area_do_curso(vaga(titulo=titulo), perfil(curso=curso))


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em Redes Sociais",
        "Estágio em Desenvolvimento de Pessoas",
        "Estágio em Suporte Administrativo",
        "Estágio em Automação Industrial",
        "Estágio em Publicidade Digital",
        "Estágio - Direito Digital",
        "Estagiário(a) de Treinamento e Desenvolvimento",
    ],
)
def test_palavra_curta_de_computacao_nao_puxa_vaga_de_outra_area(titulo: str):
    assert fora_da_area_do_curso(vaga(titulo=titulo, descricao="Sem detalhes."), perfil())


@pytest.mark.parametrize(
    ("curso", "titulo", "descricao"),
    [
        ("Direito", "Estágio em Enfermagem", "O estagiário terá direito a vale-transporte."),
        ("Comunicação", "Estágio em Desenvolvimento de Software", "Requisitos: boa comunicação."),
        ("Direito", "Estágio em Suporte Técnico", "Prestar suporte a todas as áreas da empresa."),
        ("Direito", "Estágio em Engenharia", "Estudantes de qualquer curso de engenharia."),
    ],
)
def test_nome_do_curso_solto_na_descricao_nao_mantem_a_vaga(
    curso: str, titulo: str, descricao: str
):
    assert fora_da_area_do_curso(vaga(titulo=titulo, descricao=descricao), perfil(curso=curso))


@pytest.mark.parametrize(
    ("curso", "titulo", "descricao"),
    [
        ("Direito", "Estágio Comercial", "Cursando Direito ou Administração."),
        (
            "Psicologia",
            "Estágio Financeiro",
            "Estudantes de Psicologia, Administração ou áreas afins.",
        ),
        ("Direito", "Estágio - Vaga pra ti", "Estudantes de Direito a partir do 5º período."),
    ],
)
def test_curso_citado_com_contexto_de_formacao_mantem_a_vaga(
    curso: str, titulo: str, descricao: str
):
    assert not fora_da_area_do_curso(vaga(titulo=titulo, descricao=descricao), perfil(curso=curso))


def test_perfil_remoto_nao_avalia_a_cidade_da_vaga():
    vaga_em_outra_cidade = vaga(localizacao="Salvador, Bahia")
    assert not localizacao_incompativel(vaga_em_outra_cidade, perfil(modalidade=Modalidade.REMOTO))


def test_presencial_mantem_vaga_na_mesma_cidade():
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_no_rio = vaga(localizacao="Rio de Janeiro, Rio de Janeiro")
    assert not localizacao_incompativel(vaga_no_rio, presencial)


@pytest.mark.parametrize(
    "localizacao",
    ["Salvador, Bahia", "Niterói, Rio de Janeiro", "Campinas, Estado de São Paulo", "Brasil"],
)
def test_presencial_descarta_vaga_em_outra_cidade(localizacao: str):
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    assert localizacao_incompativel(vaga(localizacao=localizacao), presencial)


@pytest.mark.parametrize(
    "localizacao",
    ["Rio de Janeiro, Estado do Rio de Janeiro", "rio de janeiro", "RIO DE JANEIRO, RJ"],
)
def test_presencial_compara_apenas_a_cidade_ignorando_acentos_e_caixa(localizacao: str):
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    assert not localizacao_incompativel(vaga(localizacao=localizacao), presencial)


@pytest.mark.parametrize(
    "descricao",
    [
        "Trabalho 100% remoto.",
        "Regime de home office.",
        "Fully remote position.",
        "Prestar suporte técnico presencial e remoto aos usuários.",
    ],
)
def test_presencial_descarta_vaga_de_outra_cidade_mesmo_com_texto_remoto(descricao: str):
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_fora = vaga(localizacao="São Paulo, Estado de São Paulo", descricao=descricao)
    assert localizacao_incompativel(vaga_fora, presencial)


@pytest.mark.parametrize(
    "modalidade", [Modalidade.PRESENCIAL, Modalidade.HIBRIDO, Modalidade.INDIFERENTE]
)
def test_modalidade_so_e_avaliada_para_perfil_remoto(modalidade: Modalidade):
    vaga_presencial = vaga(descricao="Trabalho presencial na sede.")
    assert not modalidade_incompativel(vaga_presencial, perfil(modalidade=modalidade))


@pytest.mark.parametrize(
    "descricao",
    [
        "Trabalho presencial na sede.",
        "Atuação presencialmente em São Paulo.",
        "Modelo híbrido, 3 dias no escritório.",
        "Hybrid work model.",
        "On-site position.",
    ],
)
def test_remoto_descarta_vaga_presencial_ou_hibrida(descricao: str):
    assert modalidade_incompativel(vaga(descricao=descricao), perfil(modalidade=Modalidade.REMOTO))


@pytest.mark.parametrize(
    "descricao",
    ["Trabalho 100% remoto.", "Regime de home office.", "Fully remote position."],
)
def test_remoto_mantem_vaga_remota_de_qualquer_lugar(descricao: str):
    vaga_remota = vaga(localizacao="Lisboa, Portugal", descricao=descricao)
    assert not modalidade_incompativel(vaga_remota, perfil(modalidade=Modalidade.REMOTO))


@pytest.mark.parametrize("modalidade", [Modalidade.PRESENCIAL, Modalidade.HIBRIDO])
def test_remoto_descarta_pela_modalidade_informada_pela_fonte(modalidade: Modalidade):
    vaga_com_texto_remoto = vaga(descricao="Trabalho remoto.", modalidade=modalidade)
    assert modalidade_incompativel(vaga_com_texto_remoto, perfil(modalidade=Modalidade.REMOTO))


def test_remoto_mantem_vaga_marcada_como_remota_pela_fonte_mesmo_com_texto_presencial():
    vaga_remota = vaga(descricao="Escritório presencial em SP.", modalidade=Modalidade.REMOTO)
    assert not modalidade_incompativel(vaga_remota, perfil(modalidade=Modalidade.REMOTO))


def test_presencial_descarta_vaga_marcada_como_remota_pela_fonte_em_outra_cidade():
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_remota = vaga(localizacao="Salvador, Bahia", modalidade=Modalidade.REMOTO)
    assert localizacao_incompativel(vaga_remota, presencial)


def test_remoto_mantem_vaga_sem_modalidade_informada():
    sem_modalidade = vaga(localizacao="São Paulo, São Paulo", descricao="Vaga de estágio em TI.")
    assert not modalidade_incompativel(sem_modalidade, perfil(modalidade=Modalidade.REMOTO))


def test_remoto_mantem_vaga_que_menciona_presencial_e_remoto():
    ambigua = vaga(descricao="Presencial ou remoto, a combinar.")
    assert not modalidade_incompativel(ambigua, perfil(modalidade=Modalidade.REMOTO))


def test_filtrar_remove_apenas_vagas_com_motivo_de_descarte():
    limpa = vaga(titulo="Estágio em Desenvolvimento")
    nao_estagio = vaga(titulo="Analista de Suporte")
    com_senioridade = vaga(titulo="Estagiário Pleno")
    com_experiencia = vaga(titulo="Estágio em Dados", descricao="Mínimo 3 anos de experiência.")
    em_outra_cidade = vaga(titulo="Estágio em Redes", localizacao="Salvador, Bahia")
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")

    resultado = filtrar(
        [nao_estagio, limpa, com_senioridade, com_experiencia, em_outra_cidade], presencial
    )

    assert resultado == [limpa]


def test_filtrar_para_perfil_remoto_remove_presencial_e_mantem_sem_modalidade():
    remota = vaga(titulo="Estágio Dev", localizacao="Lisboa, Portugal", descricao="100% remoto.")
    sem_modalidade = vaga(titulo="Estágio Dev", localizacao="São Paulo, São Paulo")
    presencial = vaga(titulo="Estágio Dev", descricao="Trabalho presencial.")

    resultado = filtrar([remota, sem_modalidade, presencial], perfil(modalidade=Modalidade.REMOTO))

    assert resultado == [remota, sem_modalidade]


def test_filtrar_preserva_ordem_e_aceita_lista_vazia():
    primeira = vaga(titulo="Estágio em TI A")
    segunda = vaga(titulo="Estágio em TI B")

    assert filtrar([], perfil()) == []
    assert filtrar([segunda, primeira], perfil()) == [segunda, primeira]


@pytest.mark.parametrize(
    ("curso", "titulo", "descricao"),
    [
        ("Administração", "Estágio Financeiro", "Aceita Administração ou Economia."),
        ("Administração", "Estágio em Recursos Humanos", "Cursando Administração ou Psicologia."),
        (
            "Ciência da Computação",
            "Estágio em Software para Laboratório",
            "Cursando Ciência da Computação. Python.",
        ),
        ("Direito", "Estágio Comercial", "Aceita qualquer curso."),
    ],
)
def test_titulo_de_outra_area_nao_veta_curso_mencionado(curso, titulo, descricao):
    assert not fora_da_area_do_curso(vaga(titulo=titulo, descricao=descricao), perfil(curso=curso))


@pytest.mark.parametrize(
    "titulo",
    ["Desenvolvimento de Software para Laboratório", "Estágio em Laboratório de Inovação"],
)
def test_laboratorio_no_titulo_nao_veta_vaga_de_computacao(titulo: str):
    descricao = "Desenvolver sistemas em Python e APIs web para a equipe de pesquisa."
    assert not fora_da_area_do_curso(vaga(titulo=titulo, descricao=descricao), perfil())


@pytest.mark.parametrize(
    ("curso", "descricao"),
    [
        ("Direito", "Contratação ao final do estágio, com direito a bolsas de estudo."),
        ("Direito", "Nascemos para ser o braço direito das pessoas. Atividades: análise de dados."),
        (
            "Recursos Humanos",
            "Empresa: ABRH Consultoria em Recursos Humanos. Ramo: recursos humanos/recrutamento."
            " Atividades: suporte técnico de TI.",
        ),
        (
            "Economia",
            "Movemos o mercado financeiro para o futuro. Atividades: desenvolvimento em Java.",
        ),
        (
            "Marketing",
            "Você vai trabalhar com equipes multidisciplinares como marketing e compras.",
        ),
    ],
)
def test_termo_da_area_em_texto_institucional_nao_mantem_titulo_generico(curso, descricao):
    assert fora_da_area_do_curso(
        vaga(titulo="Estagiário(a)", descricao=descricao), perfil(curso=curso)
    )


@pytest.mark.parametrize(
    ("curso", "descricao"),
    [
        (
            "Engenharia Civil",
            "Requisitos: estar cursando engenharia mecânica ou engenharia de produção.",
        ),
        ("Economia", "Você vai atuar na área financeira, apoiando contas a pagar e a receber."),
        ("Administração", "Responsabilidades: apoio nas rotinas administrativas do setor."),
        ("Recursos Humanos", "Atividades: apoiar o time de recrutamento e seleção."),
        ("Engenharia Civil", "Desejável conhecimento em AutoCAD."),
    ],
)
def test_termo_da_area_em_requisito_ou_atuacao_mantem_titulo_generico(curso, descricao):
    assert not fora_da_area_do_curso(
        vaga(titulo="Estagiário(a)", descricao=descricao), perfil(curso=curso)
    )


@pytest.mark.parametrize("modalidade", [Modalidade.HIBRIDO, Modalidade.INDIFERENTE])
@pytest.mark.parametrize(
    "descricao",
    ["Estágio presencial na escola.", "Sem detalhes.", "Modelo híbrido, 3 dias no escritório."],
)
def test_hibrido_e_indiferente_descartam_vaga_de_outra_cidade_que_nao_admite_remoto(
    modalidade: Modalidade, descricao: str
):
    do_rio = perfil(modalidade=modalidade, cidade="Rio de Janeiro, RJ")
    em_palhoca = vaga(localizacao="Palhoça, Santa Catarina", descricao=descricao)

    assert localizacao_incompativel(em_palhoca, do_rio)


@pytest.mark.parametrize("modalidade", [Modalidade.HIBRIDO, Modalidade.INDIFERENTE])
def test_hibrido_e_indiferente_mantem_vaga_remota_de_outra_cidade_e_qualquer_vaga_da_propria(
    modalidade: Modalidade,
):
    do_rio = perfil(modalidade=modalidade, cidade="Rio de Janeiro, RJ")

    assert not localizacao_incompativel(
        vaga(localizacao="São Paulo, São Paulo", descricao="Trabalho 100% remoto."), do_rio
    )
    assert not localizacao_incompativel(
        vaga(
            localizacao="São Paulo, São Paulo",
            descricao="Sem detalhes.",
            modalidade=Modalidade.REMOTO,
        ),
        do_rio,
    )
    assert not localizacao_incompativel(
        vaga(localizacao="Rio de Janeiro, Rio de Janeiro", descricao="Estágio presencial."), do_rio
    )


@pytest.mark.parametrize(
    "titulo",
    [
        "Estagio de Mestrado em Economia, Contabilidade, Engenharia",
        "Estágio de Mestrado em Meteorologia - EPE/RJ",
        "Estágio para doutorandos em Química",
        "Estágio de Pós-Graduação em Direito",
    ],
)
def test_estagio_restrito_a_pos_graduacao_e_descartado(titulo: str):
    assert exige_pos_graduacao(vaga(titulo=titulo))
    assert deve_descartar(vaga(titulo=titulo), perfil(curso="Economia"))


@pytest.mark.parametrize("titulo", ["Estágio em Economia", "Estágio em Direito - Graduação"])
def test_estagio_de_graduacao_nao_e_confundido_com_pos(titulo: str):
    assert not exige_pos_graduacao(vaga(titulo=titulo))


@pytest.mark.parametrize("titulo", ["Estágio: Administrativa", "Estágio Administrativo"])
def test_titulo_administrativo_sem_sinal_da_area_do_perfil_e_descartado(titulo: str):
    descricao = "Apoio em rotinas administrativas; conhecimento em informática."

    assert fora_da_area_do_curso(vaga(titulo=titulo, descricao=descricao), perfil())
    assert fora_da_area_do_curso(vaga(titulo=titulo, descricao=descricao), perfil(curso="Direito"))


@pytest.mark.parametrize(
    ("titulo", "curso"),
    [
        ("Pessoa Estagiária Administrativa de Tecnologia", "Engenharia de Software"),
        ("Estágio Administrativo Financeiro", "Ciências Econômicas"),
        ("Estágio Administrativo - RH", "Recursos Humanos"),
        ("Estágio Administrativo", "Administração"),
    ],
)
def test_titulo_administrativo_com_sinal_da_propria_area_continua(titulo: str, curso: str):
    assert not fora_da_area_do_curso(
        vaga(titulo=titulo, descricao="Sem detalhes."), perfil(curso=curso)
    )
