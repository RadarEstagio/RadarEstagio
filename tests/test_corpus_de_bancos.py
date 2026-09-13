from datetime import UTC, datetime

import pytest

from radar.domain.models import ExtracaoDaVaga, Modalidade, Perfil, ResultadoMatch, Vaga
from radar.matching import avaliacoes

REGRAS_NOVAS_DESLIGADAS = {
    "EQUIVALENCIAS_DE_HABILIDADES": {},
    "ALIASES_DE_COMPARACAO": {},
    "GRAFIAS_DE_DIALETOS_DE_SQL": (),
}
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
CONTEXTOS = [
    ("Ciência da Computação", "computacao"),
    ("Direito", "direito"),
    ("Ciências Contábeis", "financas"),
    ("Ciências Contábeis", "computacao"),
]
HABILIDADES_DO_PERFIL = [
    ["SQL"],
    ["MySQL"],
    ["PostgreSQL"],
    ["SQL Server"],
    ["Oracle"],
    ["ERP Oracle"],
    ["Oracle Database"],
    ["PL/SQL"],
    ["PL-SQL"],
    ["PLSQL"],
    ["PL/SQL avançado"],
    ["T-SQL"],
    ["Transact-SQL"],
    ["Procedures em T-SQL"],
    ["Oracle PL/SQL"],
    ["Linguagem PL/SQL"],
    ["Programação PL/SQL"],
    ["Procedures PL/SQL"],
    ["Banco de dados Oracle PL/SQL"],
    ["Azure SQL Database"],
    ["Consultas SQL"],
    ["Linguagem SQL"],
    ["Banco de dados SQL"],
    ["Postgre"],
    ["Oracle DB"],
    ["Microsoft SQL Server"],
    ["MongoDB"],
    ["NoSQL"],
    ["SQL avançado"],
    ["Excel", "SAP"],
]
REQUISITOS_DA_VAGA = [
    (["SQL"], []),
    (["MySQL"], []),
    (["Oracle"], []),
    (["Oracle PL/SQL"], []),
    (["PL/SQL"], []),
    (["PL-SQL"], []),
    (["T-SQL"], []),
    (["banco de dados"], []),
    (["ETL"], []),
    (["dados"], []),
    (["análise de dados"], []),
    (["SQL Server Reporting Services"], []),
    (["SQL Server avançado", "Azure SQL Database"], []),
    (["SQL avançado", "Consultas SQL"], []),
    (["SQL básico", "Linguagem SQL"], []),
    (["PostgreSQL avançado", "Postgre"], []),
    (["Oracle Database avançado", "Oracle DB"], []),
    (["SQL SERVER"], ["Azure SQL Database"]),
    (["SQL avançado", "Consultas SQL", "Excel"], []),
    (["MongoDB"], []),
    (["Python", "Git"], []),
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
            ExtracaoDaVaga(
                id_vaga="1",
                area_da_vaga=area,
                habilidades_obrigatorias=obrigatorias,
                habilidades_desejaveis=desejaveis,
            ),
        )
        for curso, area in CONTEXTOS
        for habilidades in HABILIDADES_DO_PERFIL
        for obrigatorias, desejaveis in REQUISITOS_DA_VAGA
    ]


def resultados(pares: list[tuple[Perfil, ExtracaoDaVaga]]) -> list[ResultadoMatch]:
    return [avaliacoes.pontuar(VAGA, extracao, candidato) for candidato, extracao in pares]


def limpar_caches() -> None:
    avaliacoes._membros_equivalentes.cache_clear()
    avaliacoes._membros_das_familias.cache_clear()
    avaliacoes._habilidades_declaradas.cache_clear()
    avaliacoes._exigencia.cache_clear()


def test_regras_novas_de_bancos_nunca_derrubam_nota_nem_tiram_requisito(
    monkeypatch: pytest.MonkeyPatch,
):
    pares = pares_de_perfil_e_vaga()
    ligadas = resultados(pares)
    try:
        for constante, desligada in REGRAS_NOVAS_DESLIGADAS.items():
            monkeypatch.setattr(avaliacoes, constante, desligada)
        limpar_caches()
        desligadas = resultados(pares)
    finally:
        monkeypatch.undo()
        limpar_caches()

    quedas = [
        (
            candidato.curso,
            candidato.habilidades,
            extracao.area_da_vaga,
            extracao.habilidades_obrigatorias,
            extracao.habilidades_desejaveis,
        )
        for (candidato, extracao), com, sem in zip(pares, ligadas, desligadas, strict=True)
        if com.nota < sem.nota or set(sem.requisitos_atendidos) - set(com.requisitos_atendidos)
    ]
    assert quedas == []
    assert any(com.nota > sem.nota for com, sem in zip(ligadas, desligadas, strict=True))
