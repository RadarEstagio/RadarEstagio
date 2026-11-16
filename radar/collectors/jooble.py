import logging
import time
from collections.abc import Callable, Iterable, Iterator
from datetime import UTC, datetime

import httpx

from radar.collectors.cota import CotaDeRequisicoes, CotaEsgotada
from radar.collectors.errors import ColetaIncompleta, ErroDeColeta
from radar.collectors.gupy import limpar_html
from radar.collectors.tentativas import requisitar_com_tentativas
from radar.domain.models import Vaga

URL_BUSCA = "https://br.jooble.org/api"
FONTE = "jooble"
EMPRESA_NAO_INFORMADA = "Empresa não informada"
LOCALIZACAO_PADRAO = "Brasil"
PALAVRA_DA_BUSCA = "estágio"
RESULTADOS_POR_PAGINA = 100
LIMITE_DE_PAGINAS_POR_REGIAO = 5
LIMITE_POR_DIA = 100
STATUS_DE_LIMITE_DIARIO_EXCEDIDO = 429

logger = logging.getLogger(__name__)


class ColetorJooble:
    def __init__(
        self,
        api_key: str,
        cliente_http: httpx.Client,
        publicadas_desde: datetime,
        cidades: Iterable[str] = (),
        esperar: Callable[[float], None] = time.sleep,
        cota: CotaDeRequisicoes | None = None,
    ) -> None:
        self._api_key = api_key
        self._cliente_http = cliente_http
        self._criadas_desde = publicadas_desde.astimezone(UTC).date()
        self._cidades = tuple(cidades)
        self._esperar = esperar
        self._cota = cota if cota is not None else CotaDeRequisicoes()

    def coletar(self) -> list[Vaga]:
        vagas_por_id: dict[str, Vaga] = {}
        try:
            for cidade in (*self._cidades, None):
                for item in self._buscar_regiao(cidade):
                    vaga = converter_ou_ignorar(item)
                    if vaga is not None and self._e_recente(vaga):
                        vagas_por_id.setdefault(vaga.id_externo, vaga)
        except CotaEsgotada:
            if not vagas_por_id:
                raise ErroDeColeta(
                    "Cota da Jooble esgotada antes de trazer a primeira vaga"
                ) from None
            logger.warning(
                "Cota da Jooble esgotada; a coleta parou com %d vagas", len(vagas_por_id)
            )
        except ErroDeColeta as erro:
            if not vagas_por_id:
                raise
            logger.warning(
                "Coleta da Jooble interrompida com %d vagas: %s", len(vagas_por_id), erro
            )
            raise ColetaIncompleta(str(erro), list(vagas_por_id.values())) from erro
        return list(vagas_por_id.values())

    def _buscar_regiao(self, cidade: str | None) -> Iterator[dict]:
        for pagina in range(1, LIMITE_DE_PAGINAS_POR_REGIAO + 1):
            itens = self._buscar_pagina(cidade, pagina)
            yield from itens
            if len(itens) < RESULTADOS_POR_PAGINA:
                break

    def _buscar_pagina(self, cidade: str | None, pagina: int) -> list[dict]:
        resposta = requisitar_com_tentativas(
            "Jooble",
            lambda: self._requisitar(cidade, pagina),
            self._esperar,
        )
        try:
            corpo = resposta.json()
        except ValueError:
            raise ErroDeColeta("Jooble respondeu com corpo que não é JSON") from None
        itens = corpo.get("jobs") if isinstance(corpo, dict) else None
        if not isinstance(itens, list):
            raise ErroDeColeta("Jooble respondeu sem a lista de vagas em jobs")
        return itens

    def _requisitar(self, cidade: str | None, pagina: int) -> httpx.Response:
        self._cota.reservar()
        resposta = self._cliente_http.post(
            f"{URL_BUSCA}/{self._api_key}", json=self._corpo_da_busca(cidade, pagina)
        )
        if resposta.status_code == STATUS_DE_LIMITE_DIARIO_EXCEDIDO:
            logger.warning("Jooble respondeu HTTP 429: o limite diário da chave foi excedido")
            self._cota.esgotar()
            raise CotaEsgotada
        return resposta

    def _corpo_da_busca(self, cidade: str | None, pagina: int) -> dict[str, str | int]:
        return {
            "keywords": PALAVRA_DA_BUSCA,
            "location": cidade or "",
            "page": pagina,
            "ResultOnPage": RESULTADOS_POR_PAGINA,
            "datecreatedfrom": self._criadas_desde.isoformat(),
        }

    def _e_recente(self, vaga: Vaga) -> bool:
        return vaga.publicada_em.astimezone(UTC).date() >= self._criadas_desde


def interpretar_data_de_publicacao(texto: str) -> datetime:
    data = datetime.fromisoformat(texto)
    if data.tzinfo is None:
        return data.replace(tzinfo=UTC)
    return data


def converter_ou_ignorar(item: dict) -> Vaga | None:
    try:
        return converter_em_vaga(item)
    except (KeyError, TypeError, ValueError, AttributeError) as erro:
        identificador = item.get("id") if isinstance(item, dict) else None
        logger.warning(
            "Vaga da Jooble ignorada por formato inesperado (id %s): %s",
            identificador,
            type(erro).__name__,
        )
        return None


def converter_em_vaga(item: dict) -> Vaga:
    return Vaga(
        id_externo=str(item["id"]),
        fonte=FONTE,
        titulo=limpar_html(item["title"]),
        empresa=limpar_html(item.get("company") or "") or EMPRESA_NAO_INFORMADA,
        localizacao=(item.get("location") or "").strip() or LOCALIZACAO_PADRAO,
        descricao=limpar_html(item.get("snippet") or ""),
        url=item["link"],
        publicada_em=interpretar_data_de_publicacao(item["updated"]),
        descricao_completa=False,
    )
