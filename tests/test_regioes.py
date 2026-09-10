import json
from pathlib import Path

import pytest

from radar.domain.regioes import (
    Proximidade,
    cidades_da_regiao,
    identificar_municipio,
    polo_da_regiao,
    proximidade,
)

RAIZ = Path(__file__).parent.parent


@pytest.mark.parametrize(
    "vizinha",
    [
        "Niterói, Estado do Rio de Janeiro",
        "São Gonçalo, Rio de Janeiro",
        "Duque de Caxias, RJ",
        "nova iguacu",
    ],
)
def test_cidade_vizinha_do_rio_e_da_mesma_regiao(vizinha: str):
    assert proximidade(vizinha, "Rio de Janeiro, RJ") is Proximidade.MESMA_REGIAO


def test_quem_mora_em_niteroi_alcanca_vaga_no_rio_nos_formatos_das_fontes():
    for localizacao in (
        "Rio de Janeiro, Estado do Rio de Janeiro",
        "Rio de Janeiro, Rio de Janeiro",
    ):
        assert proximidade(localizacao, "Niterói, RJ") is Proximidade.MESMA_REGIAO


@pytest.mark.parametrize(
    "localizacao",
    [
        "Rio de Janeiro, Estado do Rio de Janeiro",
        "Rio de Janeiro, Rio de Janeiro",
        "rio de janeiro",
        "RIO DE JANEIRO, RJ",
    ],
)
def test_reconhece_a_mesma_cidade_nos_formatos_das_fontes(localizacao: str):
    assert proximidade(localizacao, "Rio de Janeiro, RJ") is Proximidade.MESMA_CIDADE


@pytest.mark.parametrize(
    "localizacao",
    [
        "São Paulo, Estado de São Paulo",
        "Campos dos Goytacazes, Rio de Janeiro",
        "Petrópolis, Estado do Rio de Janeiro",
        "Brasil",
        "",
    ],
)
def test_outra_regiao_ou_local_desconhecido_e_distante(localizacao: str):
    assert proximidade(localizacao, "Niterói, RJ") is Proximidade.DISTANTE


def test_perfil_antigo_sem_estado_acha_a_regiao_pelo_nome_que_so_existe_num_estado():
    assert proximidade("Niterói, Estado do Rio de Janeiro", "Rio de Janeiro") is (
        Proximidade.MESMA_REGIAO
    )


def test_nome_repetido_em_varios_estados_sem_estado_nao_ganha_regiao():
    assert identificar_municipio("Bom Jesus").uf is None
    assert cidades_da_regiao("Bom Jesus") == ()
    assert proximidade("Bom Jesus, Piauí", "Bom Jesus") is Proximidade.MESMA_CIDADE


def test_mesmo_nome_em_estados_diferentes_nao_e_a_mesma_cidade():
    assert proximidade("Rio Branco, Mato Grosso", "Rio Branco, AC") is Proximidade.DISTANTE


def test_estado_que_nao_e_estado_cai_para_o_nome_quando_ele_e_unico():
    assert identificar_municipio("São Paulo, Zona Leste") == identificar_municipio("São Paulo, SP")


def test_polo_da_regiao_e_a_maior_cidade_dela():
    assert polo_da_regiao("Niterói, RJ") == "Rio de Janeiro"
    assert polo_da_regiao("Rio de Janeiro, RJ") == "Rio de Janeiro"
    assert polo_da_regiao("Cidade Inventada") is None
    assert "Niterói" in cidades_da_regiao("São Gonçalo, RJ")


def test_as_regioes_cobrem_as_mesmas_cidades_da_lista_do_site():
    regioes = json.loads((RAIZ / "radar/domain/regioes_imediatas.json").read_text())
    no_site = json.loads((RAIZ / "web/assets/cidades.json").read_text())

    assert sorted(cidade for regiao in regioes["regioes"] for cidade in regiao) == sorted(no_site)
    assert len(regioes["ufs"]) == 27
