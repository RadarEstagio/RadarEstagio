from datetime import UTC, datetime

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
