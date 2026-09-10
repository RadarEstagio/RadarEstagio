import json
from pathlib import Path

import httpx

URL_DOS_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
URL_DA_POPULACAO = "https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/-1/variaveis/93"
ARQUIVO = Path(__file__).parent.parent / "web/assets/cidades.json"


def populacao_por_municipio(resposta: list[dict]) -> dict[str, int]:
    series = resposta[0]["resultados"][0]["series"]
    return {item["localidade"]["id"]: int(*item["serie"].values()) for item in series}


def montar_cidades(municipios: list[dict], populacao: dict[str, int]) -> list[str]:
    ordenados = sorted(
        municipios,
        key=lambda municipio: (
            -populacao.get(str(municipio["municipio-id"]), 0),
            municipio["municipio-nome"].casefold(),
        ),
    )
    return [f"{municipio['municipio-nome']}, {municipio['UF-sigla']}" for municipio in ordenados]


def main() -> None:
    with httpx.Client(timeout=60) as cliente:
        municipios = cliente.get(URL_DOS_MUNICIPIOS, params={"view": "nivelado"})
        populacao = cliente.get(URL_DA_POPULACAO, params={"localidades": "N6[all]"})
    cidades = montar_cidades(
        municipios.raise_for_status().json(),
        populacao_por_municipio(populacao.raise_for_status().json()),
    )
    ARQUIVO.write_text(json.dumps(cidades, ensure_ascii=False, indent=0) + "\n")


if __name__ == "__main__":
    main()
