from datetime import UTC, datetime

import pytest

from radar.domain.models import ExtracaoDaVaga, Modalidade, Perfil, Vaga
from radar.matching.avaliacoes import NIVEL_NAO_INFORMADO, nivel_exigido, pontuar
from radar.matching.prompt import INSTRUCAO_DE_EXTRACAO

EXEMPLOS_DE_NIVEL_NO_PROMPT = ("Excel avançado", "inglês intermediário")


def vaga_de_teste() -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio Administrativo",
        empresa="Empresa",
        localizacao="Rio de Janeiro, RJ",
        descricao="Rotinas administrativas.",
        url="https://exemplo.com/1",
        publicada_em=datetime(2026, 9, 9, tzinfo=UTC),
        modalidade=Modalidade.PRESENCIAL,
    )


def perfil_com(habilidades: list[str]) -> Perfil:
    return Perfil(
        curso="Administração",
        periodo=4,
        habilidades=habilidades,
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )


def extracao_exigindo(habilidade: str) -> ExtracaoDaVaga:
    return ExtracaoDaVaga(
        id_vaga="adzuna:1",
        area_da_vaga="administracao",
        habilidades_obrigatorias=[habilidade],
    )


@pytest.mark.parametrize("exemplo", EXEMPLOS_DE_NIVEL_NO_PROMPT)
def test_o_prompt_ensina_a_preservar_niveis_que_a_pontuacao_sabe_comparar(exemplo: str):
    assert exemplo in INSTRUCAO_DE_EXTRACAO
    assert nivel_exigido(exemplo) != NIVEL_NAO_INFORMADO


def test_o_prompt_nao_manda_mais_apagar_o_nivel_da_habilidade():
    assert "sem nível" not in INSTRUCAO_DE_EXTRACAO
    assert '"Excel avançado" continua "Excel avançado"' in INSTRUCAO_DE_EXTRACAO


def test_requisito_avancado_extraido_com_nivel_nao_e_atendido_por_quem_tem_o_basico():
    extracao = extracao_exigindo("Excel avançado")

    com_basico = pontuar(vaga_de_teste(), extracao, perfil_com(["Excel básico"]))
    com_avancado = pontuar(vaga_de_teste(), extracao, perfil_com(["Excel avançado"]))

    assert com_basico.requisitos_nao_atendidos == ["Excel avançado"]
    assert com_avancado.requisitos_atendidos == ["Excel avançado"]
    assert com_basico.nota < com_avancado.nota


def test_apagar_o_nivel_na_extracao_faria_o_basico_passar_por_avancado():
    perfil = perfil_com(["Excel básico"])

    com_nivel = pontuar(vaga_de_teste(), extracao_exigindo("Excel avançado"), perfil)
    sem_nivel = pontuar(vaga_de_teste(), extracao_exigindo("Excel"), perfil)

    assert com_nivel.requisitos_nao_atendidos == ["Excel avançado"]
    assert sem_nivel.requisitos_atendidos == ["Excel"]
    assert sem_nivel.nota > com_nivel.nota
