import logging
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import httpx

from radar.domain.models import OrigemDoAnuncio, Vaga
from radar.domain.texto import sem_caracteres_invalidos

logger = logging.getLogger(__name__)

FONTE_ADZUNA = "adzuna"
CAMINHO_DO_ANUNCIO_LAND_AD = "/land/ad/"
BARRAS_REPETIDAS = re.compile(r"/{2,}")
CLASSE_DA_DESCRICAO = "adp-body"
PASTA_DOS_LOGOS_DE_PARCEIRO = "/partners/"
PADRAO_DO_ID_DO_PARCEIRO = re.compile(r'"source_id"\s*:\s*"([^"]+)"')
TAGS_DE_QUEBRA = frozenset({"br", "div", "li", "p"})
TAGS_SEM_FECHAMENTO = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }
)


class EnriquecedorDeDescricoes:
    def __init__(self, cliente_http: httpx.Client) -> None:
        self._cliente_http = cliente_http
        self._cache: dict[tuple[str, str], Vaga] = {}

    def enriquecer(self, vagas: list[Vaga]) -> list[Vaga]:
        sem_pagina_de_detalhe = [
            vaga
            for vaga in vagas
            if descricao_parece_truncada(vaga) and aponta_para_anuncio_land_ad(vaga.url)
        ]
        if sem_pagina_de_detalhe:
            logger.info(
                "%d vagas da Adzuna com anúncio /land/ad/ ficaram com a descrição da API",
                len(sem_pagina_de_detalhe),
            )
        return [self._enriquecer(vaga) for vaga in vagas]

    def _enriquecer(self, vaga: Vaga) -> Vaga:
        if not descricao_parece_truncada(vaga) or aponta_para_anuncio_land_ad(vaga.url):
            return vaga
        chave = (vaga.fonte, vaga.id_externo)
        if chave in self._cache:
            return self._cache[chave]
        enriquecida = ler_pagina_do_anuncio(vaga, self._cliente_http)
        self._cache[chave] = enriquecida
        return enriquecida


def descricao_parece_truncada(vaga: Vaga) -> bool:
    return vaga.fonte == FONTE_ADZUNA and not vaga.descricao_completa


def aponta_para_anuncio_land_ad(url: str) -> bool:
    return caminho_da_url(url).startswith(CAMINHO_DO_ANUNCIO_LAND_AD)


def caminho_da_url(url: str) -> str:
    try:
        caminho = urlsplit(url).path
    except ValueError:
        return ""
    return BARRAS_REPETIDAS.sub("/", caminho).casefold()


def ler_pagina_do_anuncio(vaga: Vaga, cliente_http: httpx.Client) -> Vaga:
    try:
        resposta = cliente_http.get(vaga.url, follow_redirects=True)
        resposta.raise_for_status()
    except (httpx.HTTPError, httpx.InvalidURL) as erro:
        logger.warning(
            "Não foi possível completar a descrição da vaga %s da Adzuna: %s",
            vaga.id_externo,
            type(erro).__name__,
        )
        return vaga
    com_origem = vaga.model_copy(update={"origem": extrair_origem_da_pagina(resposta.text)})
    descricao = extrair_descricao_da_pagina(resposta.text)
    if not descricao:
        logger.warning("Página da vaga %s da Adzuna não contém a descrição", vaga.id_externo)
        return com_origem
    return com_origem.model_copy(update={"descricao": descricao, "descricao_completa": True})


def extrair_origem_da_pagina(pagina: str) -> OrigemDoAnuncio:
    extrator = ExtratorDaOrigem()
    extrator.feed(pagina)
    return OrigemDoAnuncio(parceiro=extrator.parceiro, id_do_parceiro=extrator.id_do_parceiro)


def extrair_descricao_da_pagina(pagina: str) -> str:
    extrator = ExtratorDaDescricao()
    extrator.feed(pagina)
    return " ".join(sem_caracteres_invalidos("".join(extrator.partes)).split())


class ExtratorDaDescricao(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.partes: list[str] = []
        self._profundidade = 0

    def handle_starttag(self, tag: str, atributos: list[tuple[str, str | None]]) -> None:
        classes = (dict(atributos).get("class") or "").split()
        if not self._profundidade and tag == "section" and CLASSE_DA_DESCRICAO in classes:
            self._profundidade = 1
            return
        if not self._profundidade:
            return
        if tag in TAGS_DE_QUEBRA:
            self.partes.append(" ")
        if tag not in TAGS_SEM_FECHAMENTO:
            self._profundidade += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._profundidade or tag in TAGS_SEM_FECHAMENTO:
            return
        self._profundidade -= 1

    def handle_data(self, dados: str) -> None:
        if self._profundidade:
            self.partes.append(dados)


class ExtratorDaOrigem(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parceiro: str | None = None
        self.id_do_parceiro: str | None = None
        self._logo_encontrado = False
        self._dentro_de_script = False

    def handle_starttag(self, tag: str, atributos: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self._dentro_de_script = True
            return
        if tag != "img" or self._logo_encontrado:
            return
        campos = dict(atributos)
        if PASTA_DOS_LOGOS_DE_PARCEIRO not in (campos.get("src") or "").casefold():
            return
        self._logo_encontrado = True
        self.parceiro = (campos.get("alt") or "").strip() or None

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._dentro_de_script = False

    def handle_data(self, dados: str) -> None:
        if not self._dentro_de_script or self.id_do_parceiro is not None:
            return
        encontrado = PADRAO_DO_ID_DO_PARCEIRO.search(dados)
        if encontrado:
            self.id_do_parceiro = encontrado.group(1).strip() or None
