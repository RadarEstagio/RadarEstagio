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
        "Vaga PCD, com adaptação do posto de trabalho.",
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
