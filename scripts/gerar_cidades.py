import json
from pathlib import Path

import httpx

URL_DOS_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
URL_DA_POPULACAO = "https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/-1/variaveis/93"
RAIZ = Path(__file__).parent.parent
ARQUIVO_DO_SITE = RAIZ / "web/assets/cidades.json"
ARQUIVO_DAS_REGIOES = RAIZ / "radar/domain/regioes_imediatas.json"


def populacao_por_municipio(resposta: list[dict]) -> dict[str, int]:
    series = resposta[0]["resultados"][0]["series"]
    return {item["localidade"]["id"]: int(*item["serie"].values()) for item in series}


def por_populacao(municipios: list[dict], populacao: dict[str, int]) -> list[dict]:
    return sorted(
        municipios,
        key=lambda municipio: (
            -populacao.get(str(municipio["municipio-id"]), 0),
            municipio["municipio-nome"].casefold(),
        ),
    )


def nome_com_uf(municipio: dict) -> str:
    return f"{municipio['municipio-nome']}, {municipio['UF-sigla']}"


def montar_cidades(municipios: list[dict], populacao: dict[str, int]) -> list[str]:
    return [nome_com_uf(municipio) for municipio in por_populacao(municipios, populacao)]


def montar_regioes(municipios: list[dict], populacao: dict[str, int]) -> dict:
    regioes: dict[int, list[str]] = {}
    for municipio in por_populacao(municipios, populacao):
        regioes.setdefault(municipio["regiao-imediata-id"], []).append(nome_com_uf(municipio))
    ufs = {municipio["UF-nome"]: municipio["UF-sigla"] for municipio in municipios}
    return {"ufs": dict(sorted(ufs.items())), "regioes": list(regioes.values())}


def gravar(caminho: Path, conteudo: list | dict) -> None:
    caminho.write_text(json.dumps(conteudo, ensure_ascii=False, indent=0) + "\n")


def main() -> None:
    with httpx.Client(timeout=60) as cliente:
        resposta_dos_municipios = cliente.get(URL_DOS_MUNICIPIOS, params={"view": "nivelado"})
        resposta_da_populacao = cliente.get(URL_DA_POPULACAO, params={"localidades": "N6[all]"})
    municipios = resposta_dos_municipios.raise_for_status().json()
    populacao = populacao_por_municipio(resposta_da_populacao.raise_for_status().json())
    gravar(ARQUIVO_DO_SITE, montar_cidades(municipios, populacao))
    gravar(ARQUIVO_DAS_REGIOES, montar_regioes(municipios, populacao))


if __name__ == "__main__":
    main()
