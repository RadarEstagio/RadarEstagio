from datetime import UTC, datetime

import pytest

from radar.domain.models import ExtracaoDaVaga, Modalidade, Perfil, Vaga
from radar.matching import avaliacoes

VAGA = Vaga(
    id_externo="1",
    fonte="adzuna",
    titulo="Estágio",
    empresa="Empresa",
    localizacao="Rio de Janeiro, RJ",
    descricao="Estágio.",
    url="https://exemplo.com/1",
    publicada_em=datetime(2026, 9, 13, tzinfo=UTC),
    modalidade=Modalidade.PRESENCIAL,
)
CURSOS = ["Ciência da Computação", "Ciências Contábeis", "Direito"]
AREAS_DA_VAGA = ["computacao", "financas", "direito"]
HABILIDADES_DO_PERFIL = [
    ["SQL"],
    ["MySQL"],
    ["PostgreSQL", "Python"],
    ["SQL Server"],
    ["Oracle"],
    ["Oracle Database"],
    ["PL/SQL"],
    ["PL-SQL"],
    ["T-SQL"],
    ["MongoDB"],
    ["NoSQL"],
    ["SQL avançado"],
    ["MySQL básico"],
    ["Consultas SQL"],
    ["Banco de dados MySQL"],
    ["ERP Oracle"],
    ["Excel", "SAP"],
]
REQUISITOS = [
    ["SQL"],
    ["MySQL"],
    ["PostgreSQL", "MySQL", "Oracle"],
    ["SQL Server"],
    ["Oracle"],
    ["Oracle Database"],
    ["PL/SQL"],
    ["T-SQL"],
    ["MongoDB"],
    ["SQL avançado"],
    ["MySQL e Python"],
    ["banco de dados"],
    ["ETL"],
    ["análise de dados"],
    ["Consultas SQL"],
    ["Excel", "SQL"],
    ["Python", "Git"],
    ["SQL Server Reporting Services"],
]


def pares_de_perfil_e_vaga() -> list[tuple[Perfil, ExtracaoDaVaga]]:
    return [
        (
            Perfil(
                curso=curso,
                periodo=4,
                habilidades=habilidades,
                cidade="Rio de Janeiro, RJ",
                modalidade=Modalidade.PRESENCIAL,
            ),
            ExtracaoDaVaga(id_vaga="1", area_da_vaga=area, habilidades_obrigatorias=requisitos),
        )
        for curso in CURSOS
        for habilidades in HABILIDADES_DO_PERFIL
        for area in AREAS_DA_VAGA
        for requisitos in REQUISITOS
    ]


def notas(pares: list[tuple[Perfil, ExtracaoDaVaga]]) -> list[int]:
    return [avaliacoes.pontuar(VAGA, extracao, candidato).nota for candidato, extracao in pares]


def limpar_caches_das_equivalencias() -> None:
    avaliacoes._membros_equivalentes.cache_clear()
    avaliacoes._habilidades_declaradas.cache_clear()
    avaliacoes._exigencia.cache_clear()


@pytest.mark.parametrize(
    ("constante", "desligada"),
    [
        ("EQUIVALENCIAS_DE_HABILIDADES", {}),
        ("GRAFIAS_DE_DIALETOS_DE_SQL", ()),
    ],
)
def test_equivalencia_de_bancos_nunca_derruba_nota_e_sobe_alguma(
    monkeypatch: pytest.MonkeyPatch, constante: str, desligada: object
):
    pares = pares_de_perfil_e_vaga()
    ligadas = notas(pares)
    try:
        monkeypatch.setattr(avaliacoes, constante, desligada)
        limpar_caches_das_equivalencias()
        desligadas = notas(pares)
    finally:
        monkeypatch.undo()
        limpar_caches_das_equivalencias()

    quedas = [
        (
            candidato.curso,
            candidato.habilidades,
            extracao.area_da_vaga,
            extracao.habilidades_obrigatorias,
        )
        for (candidato, extracao), com, sem in zip(pares, ligadas, desligadas, strict=True)
        if com < sem
    ]
    assert quedas == []
    assert any(com > sem for com, sem in zip(ligadas, desligadas, strict=True))
