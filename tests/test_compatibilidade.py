import pytest

from radar.domain.models import ExtracaoDaVaga, Modalidade, NivelCompatibilidade, Perfil
from radar.matching.compatibilidade import derivar_niveis, montar_pontos


def perfil(curso: str = "Engenharia de Software", periodo: int = 4) -> Perfil:
    return Perfil(
        curso=curso,
        periodo=periodo,
        habilidades=["Python"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )


def extracao(**alteracoes) -> ExtracaoDaVaga:
    dados = {"id_vaga": "vaga-1", "area_da_vaga": "computacao"}
    dados.update(alteracoes)
    return ExtracaoDaVaga.model_validate(dados)


def curso_de(extracao_da_vaga: ExtracaoDaVaga, candidato: Perfil | None = None):
    return derivar_niveis(extracao_da_vaga, candidato or perfil()).curso


def periodo_de(extracao_da_vaga: ExtracaoDaVaga, candidato: Perfil | None = None):
    return derivar_niveis(extracao_da_vaga, candidato or perfil()).periodo_experiencia


def test_vaga_sem_curso_declarado_fica_parcial_em_vez_de_incompativel():
    assert curso_de(extracao(cursos_aceitos=[])) is NivelCompatibilidade.PARCIAL


def test_qualquer_curso_aceito_e_compativel():
    assert curso_de(extracao(aceita_qualquer_curso=True)) is NivelCompatibilidade.COMPATIVEL


def test_lista_com_algum_curso_de_computacao_e_compativel():
    aceitos = ["Administração", "Ciência da Computação"]

    assert curso_de(extracao(cursos_aceitos=aceitos)) is NivelCompatibilidade.COMPATIVEL


def test_curso_correlato_de_computacao_conta_mesmo_sem_ser_o_do_perfil():
    aceitos = ["Análise e Desenvolvimento de Sistemas"]

    assert curso_de(extracao(cursos_aceitos=aceitos)) is NivelCompatibilidade.COMPATIVEL


def test_lista_sem_curso_de_computacao_e_incompativel():
    aceitos = ["Engenharia Elétrica", "Engenharia Mecânica", "Administração"]

    assert curso_de(extracao(cursos_aceitos=aceitos)) is NivelCompatibilidade.INCOMPATIVEL


def test_curso_do_perfil_aceito_explicitamente_vale_mesmo_fora_do_catalogo():
    candidato = perfil(curso="Engenharia de Controle e Automação")
    aceitos = ["Engenharia de Controle e Automação"]

    assert curso_de(extracao(cursos_aceitos=aceitos), candidato) is (
        NivelCompatibilidade.COMPATIVEL
    )


def test_vaga_sem_exigencia_de_periodo_e_compativel():
    assert periodo_de(extracao()) is NivelCompatibilidade.COMPATIVEL


def test_periodo_minimo_atendido_e_compativel():
    assert periodo_de(extracao(periodo_minimo=4)) is NivelCompatibilidade.COMPATIVEL


def test_periodo_minimo_acima_do_perfil_e_incompativel():
    assert periodo_de(extracao(periodo_minimo=6)) is NivelCompatibilidade.INCOMPATIVEL


def test_experiencia_obrigatoria_e_incompativel():
    assert periodo_de(extracao(experiencia_minima_anos=1)) is NivelCompatibilidade.INCOMPATIVEL


def test_experiencia_apenas_desejavel_e_parcial():
    assert periodo_de(extracao(experiencia_desejavel=True)) is NivelCompatibilidade.PARCIAL


def area_de(extracao_da_vaga: ExtracaoDaVaga, candidato: Perfil | None = None):
    return derivar_niveis(extracao_da_vaga, candidato or perfil()).area


def test_area_da_vaga_igual_a_do_curso_e_compativel():
    assert area_de(extracao(area_da_vaga="computacao")) is NivelCompatibilidade.COMPATIVEL
    assert (
        area_de(extracao(area_da_vaga="direito"), perfil(curso="Direito"))
        is NivelCompatibilidade.COMPATIVEL
    )


def test_area_da_vaga_de_outro_curso_e_incompativel():
    assert area_de(extracao(area_da_vaga="direito")) is NivelCompatibilidade.INCOMPATIVEL
    assert (
        area_de(extracao(area_da_vaga="computacao"), perfil(curso="Direito"))
        is NivelCompatibilidade.INCOMPATIVEL
    )


def test_vaga_aberta_a_qualquer_formacao_fica_parcial():
    assert area_de(extracao(area_da_vaga=None)) is NivelCompatibilidade.PARCIAL


def test_curso_sem_area_conhecida_nao_e_punido_pela_area():
    exotico = perfil(curso="Curso Que Ninguém Tem")

    assert area_de(extracao(area_da_vaga="direito"), exotico) is NivelCompatibilidade.PARCIAL


def test_vaga_que_aceita_curso_da_mesma_area_conta_como_compativel():
    da_area = extracao(cursos_aceitos=["Ciência da Computação"])

    assert curso_de(da_area) is NivelCompatibilidade.COMPATIVEL


def test_curso_de_computacao_aceito_nao_serve_para_quem_e_de_outra_area():
    so_de_computacao = extracao(cursos_aceitos=["Ciência da Computação"])

    assert curso_de(so_de_computacao, perfil(curso="Direito")) is NivelCompatibilidade.INCOMPATIVEL


def test_curso_compativel_sem_lista_declarada_nao_vira_ponto_a_favor():
    extracao_sem_curso = extracao(cursos_aceitos=[])
    niveis = derivar_niveis(extracao_sem_curso, perfil())

    a_favor, contra = montar_pontos(extracao_sem_curso, niveis)

    assert a_favor == []
    assert contra == []


def test_engenharias_diferentes_nao_sao_curso_equivalente():
    aceita_civil = extracao(cursos_aceitos=["Engenharia Civil"])
    quimica = perfil(curso="Engenharia Química")

    assert curso_de(aceita_civil, quimica) is NivelCompatibilidade.INCOMPATIVEL


def test_economia_nao_herda_vaga_exclusiva_de_contabeis():
    aceita_contabeis = extracao(cursos_aceitos=["Ciências Contábeis"])

    assert curso_de(aceita_contabeis, perfil(curso="Economia")) is NivelCompatibilidade.INCOMPATIVEL


def test_medicina_nao_aceita_medicina_veterinaria_por_substring():
    anuncio = extracao(cursos_aceitos=["Medicina"])
    assert (
        curso_de(anuncio, perfil(curso="Medicina Veterinária")) is NivelCompatibilidade.INCOMPATIVEL
    )


def test_prefixo_de_formacao_nao_impede_curso_explicitamente_aceito():
    anuncio = extracao(cursos_aceitos=["Bacharelado em Administração"])
    assert curso_de(anuncio, perfil(curso="Administração")) is NivelCompatibilidade.COMPATIVEL


@pytest.mark.parametrize(
    ("aceito", "curso"),
    [
        ("Engenharia", "Engenharia Civil"),
        ("Engenharias", "Engenharia Química"),
        ("Química", "Engenharia Química"),
        ("Administração", "Administração de Empresas"),
    ],
)
def test_curso_generico_aceito_vale_para_a_formacao_especifica_reconhecida(aceito, curso):
    anuncio = extracao(cursos_aceitos=[aceito])

    assert curso_de(anuncio, perfil(curso=curso)) is NivelCompatibilidade.COMPATIVEL


def test_curso_generico_nao_vale_para_formacao_que_o_catalogo_nao_conhece():
    anuncio = extracao(cursos_aceitos=["Medicina"])

    assert (
        curso_de(anuncio, perfil(curso="Medicina Veterinária")) is NivelCompatibilidade.INCOMPATIVEL
    )


@pytest.mark.parametrize("valor", ["Computação", "computação", " computacao ", "COMPUTACAO"])
def test_area_da_vaga_e_normalizada_antes_de_comparar(valor: str):
    assert extracao(area_da_vaga=valor).area_da_vaga == "computacao"
    assert area_de(extracao(area_da_vaga=valor)) is NivelCompatibilidade.COMPATIVEL


@pytest.mark.parametrize("valor", ["tecnologia", "juridico", "", "ti", 42, None])
def test_area_da_vaga_fora_do_catalogo_vira_desconhecida_e_nao_outra_area(valor):
    assert extracao(area_da_vaga=valor).area_da_vaga is None
    assert area_de(extracao(area_da_vaga=valor)) is NivelCompatibilidade.PARCIAL


@pytest.mark.parametrize(
    ("aceito", "curso"),
    [
        ("Economia", "Ciências Econômicas"),
        ("Ciências Econômicas", "Economia"),
        ("Contabilidade", "Ciências Contábeis"),
        ("Gestão de Recursos Humanos", "Recursos Humanos"),
        ("Cursando Engenharia Civil", "Engenharia Civil"),
        ("Graduação em Direito", "Direito"),
        ("Sistemas", "Sistemas de Informação"),
        ("Negócios", "Negócios Internacionais"),
    ],
)
def test_sinonimo_formacao_e_plural_nao_viram_formacao_de_outra_area(aceito, curso):
    assert curso_de(extracao(cursos_aceitos=[aceito]), perfil(curso=curso)) is (
        NivelCompatibilidade.COMPATIVEL
    )


@pytest.mark.parametrize(
    "aceito", ["Qualquer curso", "Qualquer graduação", "Qualquer formação", "Todos os cursos"]
)
def test_abertura_explicita_na_lista_aceita_qualquer_curso(aceito):
    assert (
        curso_de(extracao(cursos_aceitos=["Enfermagem", aceito]), perfil(curso="Direito"))
        is NivelCompatibilidade.COMPATIVEL
    )


@pytest.mark.parametrize(
    "generico", ["Ensino Superior", "Nível superior completo", "Áreas afins", "Áreas correlatas"]
)
def test_termo_generico_nao_anula_restricao_de_curso(generico):
    anuncio = extracao(cursos_aceitos=["Enfermagem", generico], aceita_qualquer_curso=False)
    assert curso_de(anuncio, perfil(curso="Direito")) is NivelCompatibilidade.INCOMPATIVEL
    assert curso_de(anuncio, perfil(curso="Enfermagem")) is NivelCompatibilidade.COMPATIVEL


@pytest.mark.parametrize(
    "generico", ["Ensino Superior", "Nível superior completo", "Áreas afins", "Áreas correlatas"]
)
def test_termo_generico_sozinho_nao_comprova_curso(generico):
    assert (
        curso_de(extracao(cursos_aceitos=[generico]), perfil(curso="Direito"))
        is NivelCompatibilidade.PARCIAL
    )
