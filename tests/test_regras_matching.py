from datetime import UTC, datetime

import pytest

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Vaga
from radar.matching.regras import aplicar_regras_objetivas


def vaga(modalidade: Modalidade | None) -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio em Data Science",
        empresa="Visagio",
        localizacao="Rio de Janeiro",
        descricao="Python e SQL desejável",
        url="https://exemplo.com/vaga/1",
        publicada_em=datetime(2026, 8, 28, tzinfo=UTC),
        modalidade=modalidade,
    )


def perfil(modalidade: Modalidade = Modalidade.REMOTO) -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python"],
        cidade="Rio de Janeiro, RJ",
        modalidade=modalidade,
    )


def test_mantem_nota_sem_modalidade_e_preserva_apenas_lacunas_semanticas():
    original = ResultadoMatch(
        vaga=vaga(None),
        nota=95,
        pontos_contra=["Modalidade não informada", "SQL não informado"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 95
    assert corrigido.pontos_contra == ["SQL não informado"]
    assert corrigido.avisos_objetivos == []
    assert original.pontos_contra == ["Modalidade não informada", "SQL não informado"]


def test_nao_cria_aviso_quando_nota_ja_respeita_o_limite():
    original = ResultadoMatch(
        vaga=vaga(Modalidade.PRESENCIAL),
        nota=25,
        pontos_contra=["Vaga presencial"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 25
    assert corrigido.pontos_contra == []
    assert corrigido.avisos_objetivos == []


def test_limita_modalidade_incompativel_para_perfil_remoto():
    original = ResultadoMatch(
        vaga=vaga(Modalidade.PRESENCIAL),
        nota=90,
        pontos_contra=["Vaga presencial", "SQL não informado"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 30
    assert corrigido.pontos_contra == ["SQL não informado"]
    assert corrigido.avisos_objetivos == ["Nota limitada a 30: modalidade incompatível"]


def test_mantem_resultado_quando_modalidade_e_compativel():
    original = ResultadoMatch(
        vaga=vaga(Modalidade.REMOTO),
        nota=95,
        pontos_contra=["SQL não informado"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 95
    assert corrigido.pontos_contra == ["SQL não informado"]
    assert corrigido.avisos_objetivos == []


def test_limita_nota_e_avisa_quando_descricao_continua_incompleta():
    original = ResultadoMatch(
        vaga=vaga(Modalidade.REMOTO).model_copy(update={"descricao_completa": False}),
        nota=95,
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 60
    assert corrigido.avisos_objetivos == [
        "Descrição incompleta: requisitos podem estar ausentes; nota limitada a 60"
    ]


def test_guarda_a_nota_de_antes_dos_limites_sem_mudar_a_nota_limitada():
    incompleta = ResultadoMatch(
        vaga=vaga(Modalidade.REMOTO).model_copy(update={"descricao_completa": False}),
        nota=81,
    )
    presencial = ResultadoMatch(vaga=vaga(Modalidade.PRESENCIAL), nota=90)
    sem_limite = ResultadoMatch(vaga=vaga(Modalidade.REMOTO), nota=70)

    corrigidos = aplicar_regras_objetivas([incompleta, presencial, sem_limite], perfil())

    assert [
        (corrigido.nota, corrigido.nota_antes_dos_limites_objetivos) for corrigido in corrigidos
    ] == [(60, 81), (30, 90), (70, 70)]
    assert incompleta.nota_antes_dos_limites_objetivos is None


def test_reaplicar_as_regras_preserva_a_nota_de_antes_dos_limites():
    incompleta = ResultadoMatch(
        vaga=vaga(Modalidade.REMOTO).model_copy(update={"descricao_completa": False}),
        nota=81,
    )
    presencial = ResultadoMatch(vaga=vaga(Modalidade.PRESENCIAL), nota=90)

    uma_vez = aplicar_regras_objetivas([incompleta, presencial], perfil())
    duas_vezes = aplicar_regras_objetivas(uma_vez, perfil())

    assert [
        (corrigido.nota, corrigido.nota_antes_dos_limites_objetivos) for corrigido in duas_vezes
    ] == [(60, 81), (30, 90)]
    assert duas_vezes == uma_vez


def vaga_em(localizacao: str, modalidade: Modalidade | None) -> Vaga:
    return vaga(modalidade).model_copy(update={"localizacao": localizacao})


def test_limita_vaga_presencial_de_outra_cidade_para_perfil_hibrido_ou_indiferente():
    for modalidade_do_perfil in (Modalidade.HIBRIDO, Modalidade.INDIFERENTE):
        for modalidade_da_vaga in (Modalidade.PRESENCIAL, Modalidade.HIBRIDO):
            original = ResultadoMatch(
                vaga=vaga_em("Palhoça, Santa Catarina", modalidade_da_vaga), nota=88
            )

            corrigido = aplicar_regras_objetivas([original], perfil(modalidade_do_perfil))[0]

            assert corrigido.nota == 30
            assert "outra cidade" in corrigido.avisos_objetivos[0]


def test_nao_limita_vaga_presencial_de_cidade_vizinha_para_perfil_hibrido_ou_indiferente():
    for modalidade_do_perfil in (Modalidade.HIBRIDO, Modalidade.INDIFERENTE):
        de_niteroi = perfil(modalidade_do_perfil).model_copy(update={"cidade": "Niterói, RJ"})
        no_rio = ResultadoMatch(
            vaga=vaga_em("Rio de Janeiro, Estado do Rio de Janeiro", Modalidade.PRESENCIAL),
            nota=88,
        )

        corrigido = aplicar_regras_objetivas([no_rio], de_niteroi)[0]

        assert corrigido.nota == 88
        assert not any("outra cidade" in aviso for aviso in corrigido.avisos_objetivos)


def test_mantem_nota_de_vaga_remota_ou_da_propria_cidade_para_perfil_hibrido():
    hibrido = perfil(Modalidade.HIBRIDO)
    remota_longe = ResultadoMatch(vaga=vaga_em("São Paulo, São Paulo", Modalidade.REMOTO), nota=88)
    presencial_perto = ResultadoMatch(
        vaga=vaga_em("Rio de Janeiro, Rio de Janeiro", Modalidade.PRESENCIAL), nota=88
    )

    assert aplicar_regras_objetivas([remota_longe], hibrido)[0].nota == 88
    assert aplicar_regras_objetivas([presencial_perto], hibrido)[0].nota == 88


EXCLUSIVA_PARA_PCD = "Processo seletivo exclusivo para pessoas com deficiência. Python e SQL."
AFIRMATIVA_COM_GRUPOS = "Vaga afirmativa, indique seu grupo: (LGBTQIAPN+, RAÇA, PCD OU OUTROS)"


def vaga_com(descricao: str) -> Vaga:
    return vaga(None).model_copy(update={"descricao": descricao})


def respondido(resposta: bool | None) -> Perfil:
    return perfil().model_copy(update={"pessoa_com_deficiencia": resposta})


def test_vaga_exclusiva_para_pcd_e_prioritaria_para_pcd_sem_mudar_a_nota():
    original = ResultadoMatch(
        vaga=vaga_com(EXCLUSIVA_PARA_PCD), nota=55, pontos_a_favor=["Curso compatível"]
    )

    corrigido = aplicar_regras_objetivas([original], respondido(True))[0]

    assert corrigido.nota == 55
    assert corrigido.prioritaria_para_pcd is True
    assert corrigido.pontos_a_favor == ["Vaga exclusiva para PCD", "Curso compatível"]
    assert corrigido.avisos_objetivos == []


def test_vaga_afirmativa_que_inclui_pcd_e_prioritaria_para_pcd():
    corrigido = aplicar_regras_objetivas(
        [ResultadoMatch(vaga=vaga_com(AFIRMATIVA_COM_GRUPOS), nota=70)], respondido(True)
    )[0]

    assert corrigido.prioritaria_para_pcd is True
    assert corrigido.pontos_a_favor == ["Vaga afirmativa que inclui PCD"]
    assert corrigido.avisos_objetivos == []


def test_quem_nao_informou_recebe_vaga_exclusiva_para_pcd_com_aviso_e_sem_prioridade():
    corrigido = aplicar_regras_objetivas(
        [ResultadoMatch(vaga=vaga_com(EXCLUSIVA_PARA_PCD), nota=80)], respondido(None)
    )[0]

    assert corrigido.prioritaria_para_pcd is False
    assert corrigido.pontos_a_favor == []
    assert corrigido.avisos_objetivos == ["Vaga exclusiva para pessoas com deficiência (PCD)"]


@pytest.mark.parametrize("resposta", [False, None])
def test_quem_nao_e_pcd_ou_nao_informou_ve_os_grupos_da_vaga_afirmativa(resposta):
    corrigido = aplicar_regras_objetivas(
        [ResultadoMatch(vaga=vaga_com(AFIRMATIVA_COM_GRUPOS), nota=100)], respondido(resposta)
    )[0]

    assert corrigido.nota == 100
    assert corrigido.prioritaria_para_pcd is False
    assert corrigido.avisos_objetivos == [
        "Vaga afirmativa: confira se você faz parte de um destes grupos: "
        "LGBTQIAPN+, RAÇA, PCD OU OUTROS"
    ]


def test_vaga_afirmativa_sem_pcd_conhecido_avisa_inclusive_quem_e_pcd():
    afirmativa = vaga(None).model_copy(
        update={"titulo": "Estágio em Data Science - Vaga Afirmativa para Públicos"}
    )

    corrigido = aplicar_regras_objetivas(
        [ResultadoMatch(vaga=afirmativa, nota=70)], respondido(True)
    )[0]

    assert corrigido.prioritaria_para_pcd is False
    assert corrigido.avisos_objetivos == [
        "Vaga afirmativa: confira no anúncio a quem ela se destina"
    ]


@pytest.mark.parametrize("resposta", [True, False, None])
def test_vaga_comum_nao_ganha_prioridade_nem_aviso_de_publico(resposta):
    corrigido = aplicar_regras_objetivas(
        [ResultadoMatch(vaga=vaga_com("PcDs são bem-vindas. Python e SQL."), nota=70)],
        respondido(resposta),
    )[0]

    assert corrigido.prioritaria_para_pcd is False
    assert corrigido.avisos_objetivos == []
    assert corrigido.pontos_a_favor == []


def test_aplicar_as_regras_duas_vezes_nao_repete_ponto_nem_aviso():
    exclusiva = ResultadoMatch(vaga=vaga_com(EXCLUSIVA_PARA_PCD), nota=70)
    afirmativa = ResultadoMatch(vaga=vaga_com(AFIRMATIVA_COM_GRUPOS), nota=70)

    para_pcd = aplicar_regras_objetivas(
        aplicar_regras_objetivas([exclusiva], respondido(True)), respondido(True)
    )[0]
    para_outros = aplicar_regras_objetivas(
        aplicar_regras_objetivas([afirmativa], respondido(False)), respondido(False)
    )[0]

    assert para_pcd.pontos_a_favor == ["Vaga exclusiva para PCD"]
    assert len(para_outros.avisos_objetivos) == 1
