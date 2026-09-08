import pytest

from radar.domain.areas import (
    COMPUTACAO,
    area_do_curso,
    descricao_e_da_area,
    termos_de_busca,
    titulo_e_da_area,
    titulo_e_de_outra_area,
)


@pytest.mark.parametrize(
    ("curso", "esperada"),
    [
        ("Engenharia de Software", COMPUTACAO),
        ("Ciência da Computação", COMPUTACAO),
        ("Análise e Desenvolvimento de Sistemas", COMPUTACAO),
        ("Gestão da Tecnologia da Informação", COMPUTACAO),
        ("Direito", "direito"),
        ("Administração", "administracao"),
        ("Ciências Contábeis", "financas"),
        ("Economia", "financas"),
        ("Publicidade e Propaganda", "marketing"),
        ("Psicologia", "pessoas"),
        ("Gestão de Pessoas", "pessoas"),
        ("Comércio Exterior", "comercial"),
        ("Logística", "logistica"),
        ("Engenharia Civil", "engenharias"),
        ("Enfermagem", "saude"),
        ("Pedagogia", "educacao"),
        ("Gastronomia", "turismo"),
    ],
)
def test_reconhece_a_area_do_curso(curso: str, esperada: str):
    assert area_do_curso(curso) == esperada


@pytest.mark.parametrize("curso", ["", "   ", "Curso Que Ninguém Tem"])
def test_curso_desconhecido_nao_tem_area(curso: str):
    assert area_do_curso(curso) is None


def test_curso_com_nome_mais_especifico_vence_o_mais_generico():
    assert area_do_curso("Gestão de Pessoas") == "pessoas"
    assert area_do_curso("Gestão") == "administracao"


@pytest.mark.parametrize(
    ("titulo", "area"),
    [
        ("estagio em desenvolvimento", COMPUTACAO),
        ("estagiario de direito", "direito"),
        ("estagiario de marketing", "marketing"),
        ("estagio - controladoria", "financas"),
        ("estagiario de engenharia civil", "engenharias"),
    ],
)
def test_reconhece_o_titulo_da_propria_area(titulo: str, area: str):
    assert titulo_e_da_area(titulo, area)


def test_titulo_generico_nao_pertence_a_area_alguma():
    assert not titulo_e_da_area("estagiario", COMPUTACAO)
    assert not titulo_e_de_outra_area("estagiario", COMPUTACAO)


@pytest.mark.parametrize(
    "titulo",
    [
        "estagiario de direito",
        "estagiario de contabilidade",
        "estagiario de marketing",
        "estagiario de recursos humanos",
        "estagio em logistica",
        "estagiario de enfermagem",
    ],
)
def test_titulo_de_outra_area_e_rejeitado_para_quem_e_de_computacao(titulo: str):
    assert titulo_e_de_outra_area(titulo, COMPUTACAO)


@pytest.mark.parametrize(
    "titulo",
    ["estagio em desenvolvimento de software", "estagiario programador", "estagio em ti"],
)
def test_titulo_de_computacao_e_rejeitado_para_quem_e_de_direito(titulo: str):
    assert titulo_e_de_outra_area(titulo, "direito")


def test_a_propria_area_nunca_conta_como_outra():
    assert not titulo_e_de_outra_area("estagiario de direito", "direito")
    assert not titulo_e_de_outra_area("estagio em desenvolvimento", COMPUTACAO)


def test_descricao_confirma_a_area_quando_o_titulo_e_generico():
    assert descricao_e_da_area("vaga para estudantes de programacao", COMPUTACAO)
    assert descricao_e_da_area("rotina de escritorio de advocacia", "direito")
    assert not descricao_e_da_area("vaga para estudantes de programacao", "direito")


def test_termos_de_busca_saem_das_areas_pedidas():
    somente_computacao = termos_de_busca({COMPUTACAO})

    assert "software" in somente_computacao
    assert "direito" not in somente_computacao

    com_direito = termos_de_busca({COMPUTACAO, "direito"})

    assert "software" in com_direito
    assert "direito" in com_direito


def test_sem_area_alguma_nao_ha_termos():
    assert termos_de_busca(set()) == ()


@pytest.mark.parametrize(
    "titulo",
    [
        "estagio em gestao de projetos de software",
        "estagio em gestao de desenvolvimento android",
    ],
)
def test_vaga_de_software_nao_vaza_para_administracao(titulo: str):
    assert titulo_e_de_outra_area(titulo, "administracao")


def test_treinamento_e_desenvolvimento_continua_sendo_de_pessoas():
    assert not titulo_e_de_outra_area("estagio em treinamento e desenvolvimento", "pessoas")
    assert titulo_e_da_area("estagio em treinamento e desenvolvimento", "pessoas")


def test_vaga_de_base_de_dados_nao_vaza_para_financas():
    assert titulo_e_de_outra_area("estagio em base de dados", "financas")
