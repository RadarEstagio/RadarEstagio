import json
import re
from pathlib import Path

from radar.domain.models import Modalidade, Perfil
from scripts.gerar_cidades import montar_cidades, populacao_por_municipio

ARQUIVO = Path(__file__).parent.parent / "web/assets/cidades.json"
FORMATO_DO_PERFIL = re.compile(r"^[^,]+, [A-Z]{2}$")


def cidades() -> list[str]:
    return json.loads(ARQUIVO.read_text())


def test_a_lista_tem_cada_municipio_uma_vez_no_formato_do_perfil():
    lista = cidades()

    assert len(lista) >= 5570
    assert len(set(lista)) == len(lista)
    assert [cidade for cidade in lista if not FORMATO_DO_PERFIL.match(cidade)] == []
    assert len({cidade[-2:] for cidade in lista}) == 27


def test_a_lista_comeca_pelas_maiores_cidades():
    assert cidades()[:3] == ["São Paulo, SP", "Rio de Janeiro, RJ", "Brasília, DF"]


def test_o_backend_le_o_nome_da_cidade_escolhida_na_lista():
    perfil = Perfil(
        curso="Direito",
        periodo=3,
        habilidades=["Redação"],
        cidade="Niterói, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )

    assert perfil.cidade in cidades()
    assert perfil.nome_da_cidade() == "Niterói"


def test_ordena_por_populacao_e_desempata_pelo_nome():
    municipios = [
        {"municipio-id": 1, "municipio-nome": "Bom Jesus", "UF-sigla": "PI"},
        {"municipio-id": 2, "municipio-nome": "Areal", "UF-sigla": "RJ"},
        {"municipio-id": 3, "municipio-nome": "Capital", "UF-sigla": "SP"},
        {"municipio-id": 4, "municipio-nome": "Recém-criado", "UF-sigla": "MT"},
    ]
    populacao = {"1": 100, "2": 100, "3": 900}

    assert montar_cidades(municipios, populacao) == [
        "Capital, SP",
        "Areal, RJ",
        "Bom Jesus, PI",
        "Recém-criado, MT",
    ]


def test_le_a_populacao_da_resposta_do_ibge():
    resposta = [
        {
            "resultados": [
                {"series": [{"localidade": {"id": "3304557"}, "serie": {"2022": "6211223"}}]}
            ]
        }
    ]

    assert populacao_por_municipio(resposta) == {"3304557": 6211223}
