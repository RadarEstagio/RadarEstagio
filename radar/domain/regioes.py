import json
import re
import unicodedata
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple

ARQUIVO_DAS_REGIOES = Path(__file__).with_name("regioes_imediatas.json")
PREFIXO_DO_ESTADO = re.compile(r"^estado d[aeo] ")
FORA_DE_PALAVRA = re.compile(r"[^a-z0-9]+")


class Proximidade(StrEnum):
    MESMA_CIDADE = "mesma_cidade"
    MESMA_REGIAO = "mesma_regiao"
    DISTANTE = "distante"


class Municipio(NamedTuple):
    nome: str
    uf: str | None


def normalizar_lugar(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return FORA_DE_PALAVRA.sub(" ", sem_acentos.casefold()).strip()


def _municipio_do_catalogo(cidade: str) -> Municipio:
    nome, uf = cidade.rsplit(", ", 1)
    return Municipio(normalizar_lugar(nome), uf)


_CATALOGO = json.loads(ARQUIVO_DAS_REGIOES.read_text(encoding="utf-8"))
UF_DO_ESTADO = {
    **{normalizar_lugar(nome): sigla for nome, sigla in _CATALOGO["ufs"].items()},
    **{sigla.casefold(): sigla for sigla in _CATALOGO["ufs"].values()},
}
REGIAO_DO_MUNICIPIO = {
    _municipio_do_catalogo(cidade): indice
    for indice, regiao in enumerate(_CATALOGO["regioes"])
    for cidade in regiao
}
CIDADES_DA_REGIAO = tuple(
    tuple(cidade.rsplit(", ", 1)[0] for cidade in regiao) for regiao in _CATALOGO["regioes"]
)


def _ufs_de_cada_nome() -> dict[str, frozenset[str]]:
    ufs: dict[str, set[str]] = defaultdict(set)
    for municipio in REGIAO_DO_MUNICIPIO:
        ufs[municipio.nome].add(municipio.uf)
    return {nome: frozenset(siglas) for nome, siglas in ufs.items()}


UFS_DE_CADA_NOME = _ufs_de_cada_nome()


def identificar_municipio(localizacao: str) -> Municipio:
    nome, _, estado = localizacao.partition(",")
    nome_normalizado = normalizar_lugar(nome)
    uf = UF_DO_ESTADO.get(PREFIXO_DO_ESTADO.sub("", normalizar_lugar(estado)))
    if uf is None:
        ufs = UFS_DE_CADA_NOME.get(nome_normalizado, frozenset())
        uf = next(iter(ufs)) if len(ufs) == 1 else None
    return Municipio(nome_normalizado, uf)


def _mesma_cidade(uma: Municipio, outra: Municipio) -> bool:
    ufs_conferem = uma.uf is None or outra.uf is None or uma.uf == outra.uf
    return bool(uma.nome) and uma.nome == outra.nome and ufs_conferem


def proximidade(localizacao_da_vaga: str, cidade_do_perfil: str) -> Proximidade:
    da_vaga = identificar_municipio(localizacao_da_vaga)
    do_perfil = identificar_municipio(cidade_do_perfil)
    if _mesma_cidade(da_vaga, do_perfil):
        return Proximidade.MESMA_CIDADE
    regiao = REGIAO_DO_MUNICIPIO.get(do_perfil)
    if regiao is not None and regiao == REGIAO_DO_MUNICIPIO.get(da_vaga):
        return Proximidade.MESMA_REGIAO
    return Proximidade.DISTANTE


def cidades_da_regiao(cidade_do_perfil: str) -> tuple[str, ...]:
    regiao = REGIAO_DO_MUNICIPIO.get(identificar_municipio(cidade_do_perfil))
    return () if regiao is None else CIDADES_DA_REGIAO[regiao]


def polo_da_regiao(cidade_do_perfil: str) -> str | None:
    cidades = cidades_da_regiao(cidade_do_perfil)
    return cidades[0] if cidades else None
