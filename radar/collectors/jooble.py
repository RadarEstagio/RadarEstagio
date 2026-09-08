import time
from collections.abc import Callable, Iterable
from datetime import UTC, datetime

import httpx

from radar.collectors.gupy import limpar_html
from radar.collectors.tentativas import requisitar_com_tentativas
from radar.domain.models import Vaga

URL_BUSCA = "https://br.jooble.org/api"
FONTE = "jooble"
EMPRESA_NAO_INFORMADA = "Empresa não informada"
LOCALIZACAO_PADRAO = "Brasil"
TERMO_OBRIGATORIO = "estágio"
LIMITE_DE_PAGINAS_POR_BUSCA = 3
PAGINA_CONSIDERADA_INCOMPLETA = 20


class ColetorJooble:
    def __init__(
        self,
        api_key: str,
        cliente_http: httpx.Client,
        publicadas_desde: datetime,
        cidades: Iterable[str] = (),
        esperar: Callable[[float], None] = time.sleep,
        termos: Iterable[str] = (),
        busca_geral: bool = False,
    ) -> None:
        self._api_key = api_key
        self._cliente_http = cliente_http
        self._publicadas_desde = publicadas_desde
        self._cidades = tuple(cidades)
        self._esperar = esperar
        dirigidos = tuple(f"{TERMO_OBRIGATORIO} {termo}" for termo in termos)
        geral = (TERMO_OBRIGATORIO,) if busca_geral or not dirigidos else ()
        self._termos = dirigidos + geral

    def coletar(self) -> list[Vaga]:
        vagas_por_id: dict[str, Vaga] = {}
        for cidade in (None, *self._cidades):
            for termo in self._termos:
                for item in self._buscar_recentes(termo, cidade):
                    vaga = converter_em_vaga(item)
                    vagas_por_id.setdefault(vaga.id_externo, vaga)
        return list(vagas_por_id.values())

    def _buscar_recentes(self, termo: str, cidade: str | None) -> list[dict]:
        recentes: list[dict] = []
        for pagina in range(1, LIMITE_DE_PAGINAS_POR_BUSCA + 1):
            itens = self._buscar_pagina(termo, cidade, pagina)
            recentes.extend(item for item in itens if self._e_recente(item))
            if len(itens) < PAGINA_CONSIDERADA_INCOMPLETA:
                break
        return recentes

    def _buscar_pagina(self, termo: str, cidade: str | None, pagina: int) -> list[dict]:
        corpo = {"keywords": termo, "location": cidade or "", "page": str(pagina)}
        resposta = requisitar_com_tentativas(
            "Jooble",
            lambda: self._cliente_http.post(f"{URL_BUSCA}/{self._api_key}", json=corpo),
            self._esperar,
        )
        return resposta.json().get("jobs", [])

    def _e_recente(self, item: dict) -> bool:
        publicada_em = interpretar_data_de_publicacao(item.get("updated"))
        if publicada_em is None:
            return False
        return publicada_em >= self._publicadas_desde


def interpretar_data_de_publicacao(texto: str | None) -> datetime | None:
    if not texto:
        return None
    try:
        data = datetime.fromisoformat(texto)
    except ValueError:
        return None
    if data.tzinfo is None:
        return data.replace(tzinfo=UTC)
    return data


def converter_em_vaga(item: dict) -> Vaga:
    return Vaga(
        id_externo=str(item["id"]),
        fonte=FONTE,
        titulo=limpar_html(item["title"]),
        empresa=limpar_html(item.get("company") or "") or EMPRESA_NAO_INFORMADA,
        localizacao=(item.get("location") or "").strip() or LOCALIZACAO_PADRAO,
        descricao=limpar_html(item.get("snippet") or ""),
        url=item["link"],
        publicada_em=interpretar_data_de_publicacao(item.get("updated")) or datetime.now(UTC),
        descricao_completa=False,
    )
