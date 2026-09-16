from datetime import UTC, datetime

import pytest

from radar.domain.models import Modalidade, Vaga
from radar.filtering.duplicatas import (
    chave_de_duplicata,
    descricoes_semelhantes,
    mais_completa,
    remover_duplicatas,
    remover_republicacoes_de,
    republicacao_da_mesma_empresa,
)


def vaga(
    titulo: str = "Estágio em Desenvolvimento",
    empresa: str = "Empresa Exemplo",
    fonte: str = "adzuna",
    descricao: str = "descrição",
    modalidade: Modalidade | None = None,
    numero: int = 1,
    localizacao: str = "Rio de Janeiro",
) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte=fonte,
        titulo=titulo,
        empresa=empresa,
        localizacao=localizacao,
        descricao=descricao,
        url=f"https://{fonte}.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
        modalidade=modalidade,
    )


def test_chave_ignora_acentos_maiusculas_pontuacao_e_espacos_extras():
    assert chave_de_duplicata(vaga("Estágio - Desenvolvimento  ", "Empresa Exemplo ")) == (
        chave_de_duplicata(vaga("ESTAGIO DESENVOLVIMENTO", "empresa exemplo"))
    )


def test_chave_distingue_empresas_diferentes_com_o_mesmo_titulo():
    assert chave_de_duplicata(vaga(empresa="A")) != chave_de_duplicata(vaga(empresa="B"))


def test_mais_completa_prefere_quem_informa_modalidade():
    sem = vaga(descricao="descrição bem mais longa que a outra")
    com = vaga(fonte="gupy", descricao="curta", modalidade=Modalidade.REMOTO)

    assert mais_completa(sem, com) is com
    assert mais_completa(com, sem) is com


def test_mais_completa_desempata_pela_descricao_mais_longa():
    curta = vaga(descricao="curta")
    longa = vaga(fonte="gupy", descricao="descrição mais longa", numero=2)

    assert mais_completa(curta, longa) is longa
    assert mais_completa(longa, curta) is longa


def test_mais_completa_em_empate_total_mantem_a_primeira():
    primeira = vaga(numero=1)
    segunda = vaga(numero=2)

    assert mais_completa(primeira, segunda) is primeira


def test_remover_duplicatas_mantem_a_versao_mais_completa_na_posicao_original():
    adzuna = vaga(fonte="adzuna", numero=1)
    outra = vaga(titulo="Estágio em Dados", numero=2)
    gupy = vaga(fonte="gupy", modalidade=Modalidade.HIBRIDO, numero=3)

    resultado = remover_duplicatas([adzuna, outra, gupy])

    assert resultado == [gupy, outra]


def test_remover_duplicatas_preserva_lista_sem_repeticao():
    vagas = [vaga(numero=1), vaga(titulo="Estágio em Dados", numero=2)]

    assert remover_duplicatas(vagas) == vagas
    assert remover_duplicatas([]) == []


ANUNCIO = (
    "Dar apoio e suporte nas atividades de desenvolvimento das ferramentas no site. "
    "Requisitos: desejável conhecimento em PHP orientado a objeto, MySQL, SQL, HTML5, "
    "JavaScript e REST API. Necessário cursando graduação em Ciência da Computação."
)
ANUNCIO_COM_SALARIO = ANUNCIO.replace("Requisitos:", "1000,00")


def test_descricoes_quase_iguais_sao_semelhantes():
    assert descricoes_semelhantes(vaga(descricao=ANUNCIO), vaga(descricao=ANUNCIO_COM_SALARIO))


def test_descricoes_diferentes_nao_sao_semelhantes():
    outra = "Estágio em suporte de infraestrutura, redes e atendimento a usuários internos."
    assert not descricoes_semelhantes(vaga(descricao=ANUNCIO), vaga(descricao=outra))


def test_descricao_curta_nunca_e_semelhante():
    curta = "Vaga de estágio em TI. Envie seu currículo."
    assert not descricoes_semelhantes(vaga(descricao=""), vaga(descricao=""))
    assert not descricoes_semelhantes(vaga(descricao=curta), vaga(descricao=curta))


def test_remover_duplicatas_une_o_mesmo_anuncio_republicado_por_agregadores():
    original = vaga("Estágio em Programação", "BuscarVagas", descricao=ANUNCIO, numero=1)
    republicada = vaga("Estágio em Programação", "Divulga Vagas", descricao=ANUNCIO, numero=2)
    com_salario = vaga(
        "Estágio em Programação",
        "Divulga Vagas - Consultoria",
        descricao=ANUNCIO_COM_SALARIO,
        numero=3,
    )

    assert remover_duplicatas([original, republicada, com_salario]) == [original]


def test_descricao_truncada_pela_fonte_com_final_diferente_ainda_e_semelhante():
    cabecalho = (
        ANUNCIO + " Desejável também noções de Git, Docker e metodologias ágeis no dia a dia."
    )
    completa = cabecalho + " Benefícios: vale transporte, refeição no local e bolsa auxílio."
    truncada = cabecalho + " Horário: segunda a sexta, das 9h às 15h, na Barra da"
    assert descricoes_semelhantes(vaga(descricao=completa), vaga(descricao=truncada))


def test_remover_duplicatas_ignora_sufixo_de_agregador_no_titulo():
    original = vaga(
        "Estagiário de TI - São Gonçalo - RJ", "BuscarVagas", descricao=ANUNCIO, numero=1
    )
    com_sufixo = vaga(
        "Estagiário de TI - São Gonçalo - RJ - Vaga", "Divulga Vagas", descricao=ANUNCIO, numero=2
    )

    assert remover_duplicatas([original, com_sufixo]) == [original]


def test_remover_duplicatas_mantem_mesmo_titulo_em_cidades_diferentes():
    rio = vaga("Estágio em Programação", "A", descricao=ANUNCIO, numero=1)
    salvador = vaga(
        "Estágio em Programação", "B", descricao=ANUNCIO, numero=2, localizacao="Salvador, Bahia"
    )

    assert remover_duplicatas([rio, salvador]) == [rio, salvador]


def test_remover_duplicatas_mantem_mesmo_titulo_com_descricoes_diferentes():
    primeira = vaga("Estágio em TI", "A", descricao=ANUNCIO, numero=1)
    segunda = vaga(
        "Estágio em TI", "B", descricao="Suporte a usuários e manutenção de redes.", numero=2
    )

    assert remover_duplicatas([primeira, segunda]) == [primeira, segunda]


def test_remover_republicacoes_de_descarta_anuncio_igual_ao_ja_conhecido():
    enviada = vaga("Estagio Programador - Rio de Janeiro - Rj", "Divulga Vagas", descricao=ANUNCIO)
    republicada = vaga(
        "Estagio Programador - Rio de Janeiro - Rj - Vaga",
        "BuscarVagas",
        descricao=ANUNCIO_COM_SALARIO,
        numero=2,
    )
    inedita = vaga("Estágio em Dados", "Outra Empresa", descricao=ANUNCIO, numero=3)

    assert remover_republicacoes_de([republicada, inedita], [enviada]) == [inedita]


def test_remover_republicacoes_de_mantem_mesmo_titulo_com_descricao_diferente():
    enviada = vaga("Estágio em TI", "A", descricao=ANUNCIO)
    outra = vaga(
        "Estágio em TI",
        "B",
        descricao="Suporte a usuários, manutenção de redes e atendimento interno na sede.",
        numero=2,
    )

    assert remover_republicacoes_de([outra], [enviada]) == [outra]


def test_remover_republicacoes_de_sem_conhecidas_mantem_tudo():
    candidatas = [vaga("Estágio em TI", "A", descricao=ANUNCIO)]

    assert remover_republicacoes_de(candidatas, []) == candidatas


TEXTO_DE_AGENCIA = (
    "Agência de integração seleciona estudantes de Administração do terceiro ao sexto período "
    "para estágio em empresa parceira no Centro do Rio de Janeiro, com bolsa auxílio, auxílio "
    "transporte, seguro de vida, recesso remunerado, carga de seis horas diárias de segunda a "
    "sexta e possibilidade de efetivação ao fim do contrato."
)


def test_republicacao_da_mesma_empresa_nao_junta_clientes_diferentes_com_texto_de_agencia():
    marcada = vaga(
        "Estágio em Administração",
        "Vistorias Rio",
        descricao=TEXTO_DE_AGENCIA + " Atividades: vistoria de imóveis e laudos.",
    )
    de_outra_empresa = vaga(
        "Estágio em Administração",
        "Engenharia Rio",
        descricao=TEXTO_DE_AGENCIA + " Atividades: apoio ao canteiro de obras.",
        numero=2,
    )

    assert remover_republicacoes_de([de_outra_empresa], [marcada]) == []
    assert remover_republicacoes_de(
        [de_outra_empresa], [marcada], republicacao_da_mesma_empresa
    ) == [de_outra_empresa]


@pytest.mark.parametrize(
    ("empresa_marcada", "empresa_republicada"),
    [
        ("Divulga Vagas", "DIVULGA VAGAS"),
        ("Empresa não informada", "BuscarVagas"),
        ("BuscarVagas", "Confidencial"),
        ("Divulga Vagas", ""),
    ],
)
def test_republicacao_da_mesma_empresa_ou_de_empresa_sem_nome_continua_junta(
    empresa_marcada: str, empresa_republicada: str
):
    marcada = vaga("Estágio em Programação", empresa_marcada, descricao=ANUNCIO)
    republicada = vaga(
        "Estágio em Programação - Vaga",
        empresa_republicada,
        descricao=ANUNCIO_COM_SALARIO,
        numero=2,
    )

    assert remover_republicacoes_de([republicada], [marcada], republicacao_da_mesma_empresa) == []


def test_republicacao_da_mesma_empresa_ainda_exige_descricao_semelhante():
    marcada = vaga("Estágio em TI", "A", descricao=ANUNCIO)
    outra = vaga("Estágio em TI", "A", descricao=OUTRO_ANUNCIO, numero=2)

    assert not republicacao_da_mesma_empresa(marcada, outra)


OUTRO_ANUNCIO = (
    "Apoio ao setor financeiro no lançamento de notas, conciliação bancária e controle de "
    "contas a pagar e a receber. Necessário cursar Administração ou Ciências Contábeis a "
    "partir do terceiro período, com disponibilidade de seis horas por dia."
)


@pytest.mark.parametrize(
    "empresa", ["Empresa não informada", "Confidencial", "EMPRESA CONFIDENCIAL", "", "  "]
)
def test_empresa_sem_nome_nao_junta_anuncios_diferentes_com_o_mesmo_titulo(empresa: str):
    primeira = vaga("Estágio Administrativo", empresa, descricao=ANUNCIO, numero=1)
    segunda = vaga("Estágio Administrativo", empresa, descricao=OUTRO_ANUNCIO, numero=2)

    assert remover_duplicatas([primeira, segunda]) == [primeira, segunda]


def test_empresa_sem_nome_ainda_une_o_mesmo_anuncio_republicado():
    original = vaga("Estágio em Programação", "Empresa não informada", descricao=ANUNCIO)
    republicada = vaga(
        "Estágio em Programação",
        "Empresa não informada",
        descricao=ANUNCIO_COM_SALARIO,
        numero=2,
    )

    assert remover_duplicatas([original, republicada]) == [original]


def test_empresa_sem_nome_ainda_une_anuncio_curto_repetido_com_o_mesmo_texto():
    curta = "Alimentação de planilhas, cadastro de imóveis e atendimento telefônico."
    original = vaga("ESTAGIO ADMINISTRATIVO", "Empresa não informada", descricao=curta)
    repetida = vaga(
        "Estágio Administrativo",
        "Empresa não informada",
        descricao=curta.upper().rstrip("."),
        numero=2,
    )

    assert remover_duplicatas([original, repetida]) == [original]


def test_linguagens_que_so_diferem_pelo_simbolo_nao_sao_duplicatas():
    csharp = vaga("Estágio em Desenvolvimento C#", numero=1)
    cpp = vaga("Estágio em Desenvolvimento C++", numero=2)
    c = vaga("Estágio em Desenvolvimento C", numero=3)

    assert remover_duplicatas([csharp, cpp, c]) == [csharp, cpp, c]


def test_republicacao_nao_junta_linguagens_que_so_diferem_pelo_simbolo():
    csharp = vaga("Estágio Desenvolvedor C#", "BuscarVagas", descricao=ANUNCIO, numero=1)
    cpp = vaga("Estágio Desenvolvedor C++", "Divulga Vagas", descricao=ANUNCIO, numero=2)

    assert remover_duplicatas([csharp, cpp]) == [csharp, cpp]
    assert remover_republicacoes_de([cpp], [csharp]) == [cpp]


def test_simbolo_de_linguagem_ainda_ignora_caixa_acento_e_pontuacao():
    original = vaga("Estágio - Desenvolvedor C#/.NET", numero=1)
    variacao = vaga("ESTAGIO DESENVOLVEDOR c# .net", numero=2)

    assert remover_duplicatas([original, variacao]) == [original]


def test_mesma_vaga_em_cidades_diferentes_nao_e_duplicata():
    em_sao_paulo = vaga(localizacao="São Paulo", numero=1)
    em_recife = vaga(localizacao="Recife", numero=2)

    restantes = remover_duplicatas([em_sao_paulo, em_recife])

    assert [vaga.localizacao for vaga in restantes] == ["São Paulo", "Recife"]


def test_cidades_de_mesmo_nome_em_estados_diferentes_nao_sao_duplicatas():
    no_piaui = vaga(localizacao="Bom Jesus, Piauí", numero=1)
    no_rio_grande_do_sul = vaga(localizacao="Bom Jesus, RS", numero=2)

    assert remover_duplicatas([no_piaui, no_rio_grande_do_sul]) == [
        no_piaui,
        no_rio_grande_do_sul,
    ]


def test_republicacao_nao_junta_cidades_de_mesmo_nome_em_estados_diferentes():
    no_piaui = vaga(
        "Estágio em Programação",
        "BuscarVagas",
        descricao=ANUNCIO,
        localizacao="Bom Jesus, Piauí",
    )
    no_rio_grande_do_sul = vaga(
        "Estágio em Programação",
        "Divulga Vagas",
        descricao=ANUNCIO_COM_SALARIO,
        numero=2,
        localizacao="Bom Jesus, Rio Grande do Sul",
    )

    assert remover_duplicatas([no_piaui, no_rio_grande_do_sul]) == [
        no_piaui,
        no_rio_grande_do_sul,
    ]
    assert remover_republicacoes_de([no_rio_grande_do_sul], [no_piaui]) == [no_rio_grande_do_sul]


@pytest.mark.parametrize(
    ("com_estado", "outra_forma"),
    [
        ("Niterói, Estado do Rio de Janeiro", "Niterói"),
        ("Rio de Janeiro, Estado do Rio de Janeiro", "Rio de Janeiro, Rio de Janeiro"),
        ("São Paulo, Estado de São Paulo", "São Paulo, SP"),
    ],
)
def test_mesma_cidade_escrita_de_outra_forma_segue_duplicata(com_estado: str, outra_forma: str):
    da_adzuna = vaga(numero=1, localizacao=com_estado)
    da_gupy = vaga(fonte="gupy", numero=2, localizacao=outra_forma, modalidade=Modalidade.HIBRIDO)
    original = vaga(
        "Estágio em Programação",
        "BuscarVagas",
        descricao=ANUNCIO,
        numero=3,
        localizacao=com_estado,
    )
    republicada = vaga(
        "Estágio em Programação",
        "Divulga Vagas",
        descricao=ANUNCIO_COM_SALARIO,
        numero=4,
        localizacao=outra_forma,
    )

    assert remover_duplicatas([da_adzuna, da_gupy]) == [da_gupy]
    assert remover_duplicatas([original, republicada]) == [original]
    assert remover_republicacoes_de([republicada], [original]) == []


def test_cidade_sem_estado_de_nome_repetido_nao_e_unida_por_palpite():
    sem_estado = vaga(localizacao="Bom Jesus", numero=1)
    no_piaui = vaga(localizacao="Bom Jesus, PI", numero=2)

    assert remover_duplicatas([sem_estado, no_piaui]) == [sem_estado, no_piaui]


def test_mesma_vaga_na_mesma_cidade_por_duas_fontes_continua_sendo_uma_so():
    da_adzuna = vaga(fonte="adzuna", numero=1, localizacao="Rio de Janeiro, RJ")
    da_gupy = vaga(
        fonte="gupy", numero=2, localizacao="Rio de Janeiro", modalidade=Modalidade.HIBRIDO
    )

    restantes = remover_duplicatas([da_adzuna, da_gupy])

    assert len(restantes) == 1
    assert restantes[0].fonte == "gupy"
