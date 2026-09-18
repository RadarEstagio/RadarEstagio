from datetime import UTC, datetime

import pytest

from radar.domain.models import Vaga
from radar.domain.publico import PublicoDaVaga, grupos_da_vaga_afirmativa, publico_da_vaga


def vaga(titulo: str = "Estágio em Dados", descricao: str = "Apoio às rotinas da área.") -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo=titulo,
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, Rio de Janeiro",
        descricao=descricao,
        url="https://exemplo.com/vaga/1",
        publicada_em=datetime(2026, 9, 15, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio Administrativo - PCD",
        "Estágio em Dados (PcD)",
        "PCD | Estagiário de Suporte",
        "Vaga exclusiva para PCD - Estágio em RH",
        "Estágio para Pessoas com Deficiência",
        "Estágio em RH - PCD - Rio de Janeiro",
        "Estágio em Dados (PcD) - Híbrido",
    ],
)
def test_titulo_que_dirige_a_vaga_a_pcd_e_exclusivo(titulo):
    assert publico_da_vaga(vaga(titulo=titulo)) is PublicoDaVaga.EXCLUSIVO_PCD


@pytest.mark.parametrize(
    "descricao",
    [
        "Requisitos da empresa: vaga de emprego para pessoas com deficiência (PCD).",
        "Processo seletivo exclusivo para PCD.",
        "Esta oportunidade é destinada a pessoas com deficiência.",
        "Vaga exclusivamente para pessoas com deficiência, com laudo.",
        "Inscrições somente para PCD.",
        "Vaga para pessoas com deficiência auditiva, com intérprete de Libras.",
        "Vaga PCD: Sim.",
        "Vaga PCD, com adaptação do posto de trabalho.",
        "Vaga para PCD - Sim",
        "Vaga exclusiva para PCD | Bolsa: R$ 1.200",
        "Vaga para pessoas com deficiência (PCD). Bolsa: R$ 1.200.",
    ],
)
def test_descricao_que_reserva_a_vaga_a_pcd_e_exclusiva(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is PublicoDaVaga.EXCLUSIVO_PCD


@pytest.mark.parametrize(
    "descricao",
    [
        "PcDs são sempre bem-vindas por aqui.",
        "Todas as nossas vagas também são extensivas para PCD.",
        "Todas as vagas da empresa aceitam candidatura de PCD.",
        "Nossas vagas podem ser preenchidas por profissionais PCDs e reabilitados.",
        "Contratamos sem distinção de gênero, raça, idade ou deficiência.",
        "Vaga elegível para pessoas com deficiência.",
        "Apoiamos a contratação de profissionais PCDs.",
        "Pessoas com deficiência são super bem-vindas no processo.",
        "Oferecemos auxílio para dependente PCD.",
        "Temos grupos de afinidade de pessoas com deficiência.",
        "Estimulamos a candidatura de pessoas diversas (LGBTQIAPN+, raça, gênero, PCD, 40+).",
        "A vaga não é exclusiva para PCD.",
        "Vagas para PCD e ampla concorrência.",
        "Esta vaga é para PCD também.",
    ],
)
def test_empresa_inclusiva_nao_torna_a_vaga_exclusiva(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em Acessibilidade e Inclusão de Pessoas com Deficiência",
        "Estágio em Educação Especial",
    ],
)
def test_titulo_sobre_o_tema_nao_torna_a_vaga_exclusiva(titulo):
    assert publico_da_vaga(vaga(titulo=titulo)) is PublicoDaVaga.GERAL


def test_vaga_afirmativa_que_lista_pcd_entre_os_grupos():
    afirmativa = vaga(
        titulo="Estágio em Suporte - Vaga Afirmativa (Lgbtqiapn, Raça, Pcd)",
        descricao="Na inscrição da vaga afirmativa, indique: (LGBTQIAPN+, RAÇA, PCD OU OUTROS)",
    )

    assert publico_da_vaga(afirmativa) is PublicoDaVaga.AFIRMATIVO_COM_PCD
    assert grupos_da_vaga_afirmativa(afirmativa) == "LGBTQIAPN+, RAÇA, PCD OU OUTROS"


def test_grupos_vem_do_titulo_quando_a_descricao_nao_os_lista():
    afirmativa = vaga(titulo="Estágio em TI - Vaga Afirmativa (Mulheres, Pessoas Negras)")

    assert publico_da_vaga(afirmativa) is PublicoDaVaga.AFIRMATIVO
    assert grupos_da_vaga_afirmativa(afirmativa) == "Mulheres, Pessoas Negras"


def test_vaga_afirmativa_para_pcd_na_mesma_frase_inclui_pcd():
    afirmativa = vaga(descricao="Vaga afirmativa para pessoas com deficiência e pessoas negras.")

    assert publico_da_vaga(afirmativa) is PublicoDaVaga.AFIRMATIVO_COM_PCD


def test_pcd_citado_em_outra_frase_nao_entra_na_vaga_afirmativa():
    afirmativa = vaga(
        descricao="Vaga afirmativa para mulheres. Benefícios: auxílio para dependente PCD."
    )

    assert publico_da_vaga(afirmativa) is PublicoDaVaga.AFIRMATIVO


@pytest.mark.parametrize(
    ("titulo", "descricao"),
    [
        ("Estágio em TI (RJ) Vaga Afirmativa para Públicos", "Apoio ao suporte técnico."),
        ("Estágio Administrativo", "Conhecimento em Excel. Ação Afirmativa"),
    ],
)
def test_vaga_afirmativa_sem_grupos_legiveis(titulo, descricao):
    afirmativa = vaga(titulo=titulo, descricao=descricao)

    assert publico_da_vaga(afirmativa) is PublicoDaVaga.AFIRMATIVO
    assert grupos_da_vaga_afirmativa(afirmativa) is None


def test_exclusividade_para_pcd_vence_a_palavra_afirmativa():
    exclusiva = vaga(descricao="Vaga afirmativa exclusiva para pessoas com deficiência.")

    assert publico_da_vaga(exclusiva) is PublicoDaVaga.EXCLUSIVO_PCD


def test_acoes_afirmativas_da_empresa_nao_tornam_a_vaga_afirmativa():
    comum = vaga(descricao="A empresa mantém programas de diversidade e ações afirmativas.")

    assert publico_da_vaga(comum) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    "descricao",
    [
        "Haverá reserva de vagas para pessoas com deficiência, nos termos da lei.",
        "10% das vagas são reservadas para pessoas com deficiência.",
        "Somos uma empresa que oferece oportunidades para pessoas com deficiência.",
        "Também temos programa de estágio para pessoas com deficiência.",
        "Confira também nossas vagas PCD no site.",
        "Vagas para PCD e para ampla concorrência.",
        "Vagas destinadas a pessoas com deficiência: 2. Ampla concorrência: 18.",
        "Vaga para pessoas com deficiência e pessoas negras.",
        "Esta vaga é para PCD e/ou reabilitados do INSS.",
        "Vaga para PCD: Não. Nível: estágio.",
        "Vaga PCD? Não",
        "Esta oportunidade também está aberta para pessoas com deficiência.",
        "Oportunidade para pessoas com deficiência e sem deficiência.",
    ],
)
def test_cota_programa_ou_outras_vagas_nao_tornam_esta_vaga_exclusiva(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is not PublicoDaVaga.EXCLUSIVO_PCD


@pytest.mark.parametrize(
    "descricao",
    [
        "Vaga para PCD/Ampla concorrência.",
        "Vaga para PCD / ampla concorrência.",
        "Vaga PCD / Ampla concorrência.",
        "Vaga para PCD (não exclusiva).",
        "Vaga PCD (não exclusiva).",
        "Vaga exclusiva para PCD (não exclusiva).",
        "Vaga para PCD - Não. Nível: estágio.",
        "Vaga PCD - Não",
        "Vaga para PCD – Não",
        "Vaga para PCD, não exclusiva.",
        "Vaga para PCD? - Não",
        "Vaga PCD | Não | Bolsa: R$ 1.200",
        "Vaga para PCD/Não PCD.",
        "Vaga para PCD (também ampla concorrência).",
        "Vaga para PCD - ampla concorrência.",
        "Processo seletivo exclusivo para PCD / ampla concorrência.",
        "Inscrições somente para PCD/reabilitados.",
        "Vaga para pessoas com deficiência (PCD) / ampla concorrência.",
        "Vaga para pessoas com deficiência (PCD) - Não",
        "Vaga para pessoas com deficiência (PCD) e pessoas negras.",
        "Vaga para PCD, preferencialmente.",
        "Vaga PCD: N/A",
        "Vaga para PCD - Não",
        "Vaga PCD: Não.",
        "Vaga PCD? Não | Bolsa: R$ 1.200",
        "Vaga para PCD - Não - Bolsa: R$ 1.200",
        "Vaga PCD: Não; Nível: estágio",
        "Vaga PCD: Não, nível estágio",
        "Vaga para PCD (Não)",
        "Vaga PCD: Não se aplica",
        "Vaga PCD: Não informado",
        "Vaga para PCD - Não PCD",
    ],
)
def test_vaga_que_diz_nao_ser_so_de_pcd_nao_e_exclusiva(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    ("titulo", "descricao"),
    [
        ("Estágio em Dados", "Vaga exclusiva para PCD, não exigimos experiência."),
        (
            "Estágio em Dados",
            "Vaga exclusiva para pessoas com deficiência, não exigimos experiência.",
        ),
        ("Estágio em Dados", "Vaga para PCD - Não requer experiência."),
        ("Estágio em Dados", "Vaga PCD: não é necessário experiência."),
        ("Estágio em RH - PCD - Não requer experiência", "Apoio às rotinas da área."),
    ],
)
def test_nao_de_outra_oracao_depois_do_termo_nao_tira_a_exclusividade(titulo, descricao):
    assert publico_da_vaga(vaga(titulo=titulo, descricao=descricao)) is PublicoDaVaga.EXCLUSIVO_PCD


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio para PCD/Ampla Concorrência",
        "Estágio para PCD (não exclusiva)",
        "Estágio para PCD - Não",
        "Estágio em RH - Vaga PCD/Ampla",
        "Estágio em RH - Vaga para PCD (não exclusiva)",
    ],
)
def test_titulo_que_diz_nao_ser_so_de_pcd_depois_do_termo_nao_e_exclusivo(titulo):
    assert publico_da_vaga(vaga(titulo=titulo)) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    ("titulo", "descricao"),
    [
        ("Estágio em Dados", "Vaga para PCD (vaga não exclusiva)."),
        ("Estágio em Dados", "Vaga para PCD, mas não exclusiva."),
        ("Estágio em Dados", "Processo seletivo para PCD, porém não é exclusivo."),
        ("Estágio em RH - PCD - Vaga não exclusiva", "Apoio às rotinas da área."),
    ],
)
def test_nao_exclusiva_na_mesma_frase_tira_a_exclusividade(titulo, descricao):
    assert publico_da_vaga(vaga(titulo=titulo, descricao=descricao)) is PublicoDaVaga.GERAL


def test_nao_exclusiva_em_outra_frase_nao_tira_a_exclusividade():
    exclusiva = vaga(descricao="Processo seletivo exclusivo para PCD. Atuação não exclusiva em TI.")

    assert publico_da_vaga(exclusiva) is PublicoDaVaga.EXCLUSIVO_PCD


@pytest.mark.parametrize(
    "descricao",
    [
        "Estágio em instituição que atende exclusivamente pessoas com deficiência.",
        "Escola exclusiva para pessoas com deficiência visual.",
        "Centro de reabilitação com atendimento exclusivo a pessoas com deficiência.",
    ],
)
def test_instituicao_que_atende_pcd_nao_torna_a_vaga_exclusiva(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em Marketing (PcDs são bem-vindas)",
        "Estágio em Vendas - PcD bem-vindo",
        "Estágio (PCD e não PCD)",
        "Estágio em Direito - PcD ou Ampla Concorrência",
        "Estágio Administrativo - PCD e Ampla Concorrência",
        "Estágio em RH: PCD e Diversidade",
        "Estágio em Educação Especial / PcD",
        "Estágio em Educação para Pessoas com Deficiência",
    ],
)
def test_titulo_que_so_cita_pcd_nao_torna_a_vaga_exclusiva(titulo):
    assert publico_da_vaga(vaga(titulo=titulo)) is not PublicoDaVaga.EXCLUSIVO_PCD


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em RH - PCD - Não",
        "Estágio em RH - PCD - Não exclusiva",
        "Estágio em RH (PcD - não exclusiva)",
        "Estágio em RH - PCD - Ampla Concorrência",
        "Estágio em RH (PCD) ou Ampla Concorrência",
        "Estágio em RH (PCD) / Ampla Concorrência",
        "Estágio em RH - Vaga PCD - Não",
        "PCD - Não | Estágio em RH",
        "PCD | Também ampla concorrência | Estágio em RH",
    ],
)
def test_trecho_pcd_do_titulo_seguido_de_outro_publico_nao_e_exclusivo(titulo):
    assert publico_da_vaga(vaga(titulo=titulo)) is PublicoDaVaga.GERAL


def test_titulo_afirmativa_sem_a_palavra_vaga_continua_afirmativa_com_pcd():
    afirmativa = vaga(titulo="Estágio em TI - Afirmativa (PCD, Mulheres)")

    assert publico_da_vaga(afirmativa) is PublicoDaVaga.AFIRMATIVO_COM_PCD
    assert grupos_da_vaga_afirmativa(afirmativa) == "PCD, Mulheres"


def test_politica_afirmativa_da_empresa_nao_empresta_grupos_a_vaga():
    afirmativa = vaga(
        descricao="Vaga afirmativa para mulheres. Nossas políticas afirmativas (PCD, raça) valem."
    )

    assert publico_da_vaga(afirmativa) is PublicoDaVaga.AFIRMATIVO
    assert grupos_da_vaga_afirmativa(afirmativa) is None


@pytest.mark.parametrize(
    "descricao",
    [
        "Vaga afirmativa para mulheres na unidade (Barra da Tijuca).",
        "Ação afirmativa: mulheres (cis e trans).",
    ],
)
def test_parentese_que_nao_lista_grupos_nao_vira_lista_de_grupos(descricao):
    assert grupos_da_vaga_afirmativa(vaga(descricao=descricao)) is None


@pytest.mark.parametrize(
    "descricao",
    [
        "Apoio ao recrutamento e seleção para pessoas com deficiência.",
        "Auxiliar nos processos de seleção para PCD.",
        "Participar da seleção para pessoas com deficiência junto ao RH.",
        "Atuar no processo seletivo para pessoas com deficiência.",
        "Acompanhar o processo seletivo para PCD da empresa.",
        "Triagem e seleção para pessoas com deficiência no projeto social.",
        "Curso de capacitação e seleção para pessoas com deficiência.",
    ],
)
def test_atividade_que_seleciona_pcd_nao_torna_a_vaga_exclusiva(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    "descricao",
    [
        "A empresa promove igualdade de oportunidade para pessoas com deficiência.",
        "Temos compromisso com a igualdade de oportunidade para PCD.",
        "Garantimos oportunidade para pessoas com deficiência em todas as etapas.",
        "Trabalhamos pela inclusão e oportunidade para pessoas com deficiência.",
        "Política de igualdade de oportunidade para pessoas com deficiência.",
        "Divulgação de vaga para pessoas com deficiência junto aos parceiros.",
        "Mapear oportunidade para pessoas com deficiência no mercado.",
    ],
)
def test_oportunidade_a_pcd_no_meio_da_frase_nao_torna_a_vaga_exclusiva(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    "descricao",
    [
        "Bolsa: R$ 1.200. Vaga exclusiva para pessoas com deficiência.",
        "- Requisitos da empresa: vaga de emprego para PCD.",
        "A vaga é para pessoas com deficiência.",
        "Esta seleção é destinada a pessoas com deficiência.",
        "**Vaga para PCD** com laudo médico.",
        "Sobre a empresa. Esta oportunidade é destinada a PCD.",
    ],
)
def test_sujeito_que_abre_a_frase_segue_exclusivo(descricao):
    assert publico_da_vaga(vaga(descricao=descricao)) is PublicoDaVaga.EXCLUSIVO_PCD


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em Psicologia - Pessoas com Deficiência",
        "Estágio em Pedagogia | Pessoas com Deficiência",
        "Estágio em Fisioterapia (Pessoas com Deficiência)",
        "Estágio em Fonoaudiologia - Pessoas Portadoras de Deficiência",
        "Pessoas com Deficiência | Estágio em Psicopedagogia",
        "Estágio em Educação Física - Pessoas com Deficiência - Rio de Janeiro",
    ],
)
def test_titulo_que_nomeia_pcd_por_extenso_nao_torna_a_vaga_exclusiva(titulo):
    assert publico_da_vaga(vaga(titulo=titulo)) is PublicoDaVaga.GERAL


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em TI - Vaga Pessoas com Deficiência",
        "Estágio em TI - Vaga Exclusiva Pessoas com Deficiência",
        "Estágio em TI - Exclusiva para Pessoas com Deficiência",
        "Estágio em TI (Vaga para Pessoas com Deficiência)",
    ],
)
def test_titulo_que_diz_ser_a_vaga_segue_exclusivo_com_o_termo_por_extenso(titulo):
    assert publico_da_vaga(vaga(titulo=titulo)) is PublicoDaVaga.EXCLUSIVO_PCD
