import logging
import time
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from datetime import UTC, datetime

import httpx

from radar.collectors.cota import CotaDeRequisicoes, CotaEsgotada
from radar.collectors.errors import ColetaIncompleta, ErroDeColeta
from radar.collectors.gupy import limpar_html
from radar.collectors.tentativas import requisitar_com_tentativas
from radar.domain.models import OrigemDoAnuncio, Vaga
from radar.filtering.origem import motivo_do_bloqueio, origem_bloqueada

URL_BUSCA = "https://br.jooble.org/api"
FONTE = "jooble"
EMPRESA_NAO_INFORMADA = "Empresa não informada"
LOCALIZACAO_PADRAO = "Brasil"
PALAVRA_DA_BUSCA = "estágio"
RESULTADOS_POR_PAGINA = 100
LIMITE_DE_PAGINAS_POR_REGIAO = 5
LIMITE_POR_DIA = 100
STATUS_DE_LIMITE_DIARIO_EXCEDIDO = 429
ROTULO_SEM_ORIGEM = "sem origem"
NENHUMA = "nenhuma"

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
        mantidas: dict[str, Vaga] = {}
        cortadas: dict[str, Vaga] = {}
        try:
            for cidade in (*self._cidades, None):
                for item in self._buscar_regiao(cidade):
                    vaga = converter_ou_ignorar(item)
                    if vaga is None or not self._e_recente(vaga):
                        continue
                    destino = cortadas if origem_bloqueada(vaga.origem) else mantidas
                    destino.setdefault(vaga.id_externo, vaga)
        except CotaEsgotada:
            if not mantidas:
                raise ErroDeColeta(
                    "Cota da Jooble esgotada antes de trazer a primeira vaga"
                ) from None
            logger.warning("Cota da Jooble esgotada; a coleta parou com %d vagas", len(mantidas))
        except ErroDeColeta as erro:
            if not mantidas:
                raise
            logger.warning("Coleta da Jooble interrompida com %d vagas: %s", len(mantidas), erro)
            raise ColetaIncompleta(str(erro), list(mantidas.values())) from erro
        finally:
            registrar_origens(list(mantidas.values()), list(cortadas.values()))
        return list(mantidas.values())

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
        return vaga.publicada_em.date() >= self._criadas_desde


def saldo_da_jooble(hoje: int) -> int:
    return max(0, LIMITE_POR_DIA - hoje)


def interpretar_data_de_publicacao(texto: str) -> datetime:
    data = datetime.fromisoformat(texto)
    if data.tzinfo is None:
        return data.replace(tzinfo=UTC)
    return data.astimezone(UTC)


def converter_ou_ignorar(item: dict) -> Vaga | None:
    try:
        return converter_em_vaga(item)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as erro:
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
        origem=origem_informada(item.get("source")),
    )


def origem_informada(source: object) -> OrigemDoAnuncio | None:
    dominio = source.strip().casefold() if isinstance(source, str) else ""
    return OrigemDoAnuncio(dominio=dominio) if dominio else None


def registrar_origens(mantidas: list[Vaga], cortadas: list[Vaga]) -> None:
    if not mantidas and not cortadas:
        return
    logger.info(
        "Jooble: %d vagas mantidas por origem (%s); %d cortadas por origem bloqueada (%s)",
        len(mantidas),
        contagem_por_dominio(mantidas),
        len(cortadas),
        contagem_com_o_motivo_do_bloqueio(cortadas),
    )


def dominio_de_origem(vaga: Vaga) -> str:
    return (vaga.origem.dominio if vaga.origem else None) or ROTULO_SEM_ORIGEM


def contagem_por_dominio(vagas: list[Vaga]) -> str:
    contagem = Counter(dominio_de_origem(vaga) for vaga in vagas)
    return ", ".join(f"{dominio} {total}" for dominio, total in contagem.most_common()) or NENHUMA


def contagem_com_o_motivo_do_bloqueio(cortadas: list[Vaga]) -> str:
    contagem = Counter(dominio_de_origem(vaga) for vaga in cortadas)
    motivos = {dominio_de_origem(vaga): motivo_do_bloqueio(vaga.origem) for vaga in cortadas}
    return (
        "; ".join(
            f"{dominio} {total}: {motivos[dominio]}" for dominio, total in contagem.most_common()
        )
        or NENHUMA
    )
