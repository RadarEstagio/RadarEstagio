import logging
import math
import time
from collections.abc import Callable, Iterable, Iterator

import httpx

from radar.collectors.errors import ColetaIncompleta, ErroDeColeta
from radar.collectors.tentativas import requisitar_com_tentativas
from radar.domain.models import Vaga
from radar.settings import Settings

URL_BUSCA = "https://api.adzuna.com/v1/api/jobs/br/search"
FONTE = "adzuna"
EMPRESA_NAO_INFORMADA = "Empresa não informada"
LOCALIZACAO_PADRAO = "Brasil"
TERMO_OBRIGATORIO = "estágio"
RESULTADOS_POR_PAGINA = 50
LIMITE_DE_PAGINAS_POR_REGIAO = 10
POSICAO_DO_ESTADO = 2
POSICAO_DA_CIDADE = 3
TAMANHO_DO_RESUMO_DA_API = 500
LIMITE_POR_MINUTO = 25
LIMITE_POR_DIA = 250
LIMITE_POR_SEMANA = 1000
LIMITE_POR_MES = 2500
JANELA_DE_UM_MINUTO_EM_SEGUNDOS = 60

logger = logging.getLogger(__name__)


class CotaDaAdzunaEsgotada(Exception):
    pass


class CotaDaAdzuna:
    def __init__(
        self,
        saldo: float = math.inf,
        relogio: Callable[[], float] = time.monotonic,
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        self._saldo = saldo
        self._relogio = relogio
        self._esperar = esperar
        self._momentos: list[float] = []
        self.requisicoes = 0
        self.esgotada = False

    def reservar(self) -> None:
        if self.requisicoes >= self._saldo:
            self.esgotada = True
            raise CotaDaAdzunaEsgotada
        agora = self._recentes()
        if len(self._momentos) >= LIMITE_POR_MINUTO:
            self._esperar(
                JANELA_DE_UM_MINUTO_EM_SEGUNDOS - (agora - self._momentos[-LIMITE_POR_MINUTO])
            )
            agora = self._recentes()
        self._momentos.append(agora)
        self.requisicoes += 1

    def _recentes(self) -> float:
        agora = self._relogio()
        self._momentos = [
            momento
            for momento in self._momentos
            if agora - momento < JANELA_DE_UM_MINUTO_EM_SEGUNDOS
        ]
        return agora


def saldo_da_adzuna(hoje: int, semana: int, mes: int) -> int:
    return max(0, min(LIMITE_POR_DIA - hoje, LIMITE_POR_SEMANA - semana, LIMITE_POR_MES - mes))


class ColetorAdzuna:
    def __init__(
        self,
        settings: Settings,
        cliente_http: httpx.Client,
        cidades: Iterable[str] = (),
        esperar: Callable[[float], None] = time.sleep,
        termos: Iterable[str] = (),
        busca_geral: bool = False,
        cota: CotaDaAdzuna | None = None,
    ) -> None:
        self._settings = settings
        self._cliente_http = cliente_http
        self._cidades = tuple(cidades)
        self._esperar = esperar
        self._cota = cota if cota is not None else CotaDaAdzuna(esperar=esperar)
        dirigida = " ".join(termos)
        self._buscas = tuple(
            dict.fromkeys([dirigida] + ([""] if busca_geral or not dirigida else []))
        )

    def coletar(self) -> list[Vaga]:
        vagas_por_id: dict[str, Vaga] = {}
        try:
            for cidade in (None, *self._cidades):
                for termos in self._buscas:
                    for item in self._buscar_regiao(cidade, termos):
                        vaga = converter_em_vaga(item)
                        vagas_por_id.setdefault(vaga.id_externo, vaga)
        except CotaDaAdzunaEsgotada:
            if not vagas_por_id:
                raise ErroDeColeta("Cota da Adzuna esgotada antes da primeira busca") from None
            logger.warning(
                "Cota da Adzuna esgotada; a coleta parou com %d vagas", len(vagas_por_id)
            )
        except ErroDeColeta as erro:
            if not vagas_por_id:
                raise
            logger.warning(
                "Coleta da Adzuna interrompida com %d vagas: %s", len(vagas_por_id), erro
            )
            raise ColetaIncompleta(str(erro), list(vagas_por_id.values())) from erro
        return list(vagas_por_id.values())

    def _buscar_regiao(self, cidade: str | None, termos: str) -> Iterator[dict]:
        for pagina in range(1, LIMITE_DE_PAGINAS_POR_REGIAO + 1):
            resultados = self._buscar_pagina(pagina, cidade, termos)
            yield from resultados
            if len(resultados) < RESULTADOS_POR_PAGINA:
                break

    def _buscar_pagina(self, pagina: int, cidade: str | None, termos: str) -> list[dict]:
        resposta = requisitar_com_tentativas(
            "Adzuna",
            lambda: self._requisitar(pagina, cidade, termos),
            self._esperar,
        )
        return resposta.json()["results"]

    def _requisitar(self, pagina: int, cidade: str | None, termos: str) -> httpx.Response:
        self._cota.reservar()
        return self._cliente_http.get(
            f"{URL_BUSCA}/{pagina}", params=self._parametros_da_busca(cidade, termos)
        )

    def _parametros_da_busca(self, cidade: str | None, termos: str) -> dict[str, str | int]:
        parametros: dict[str, str | int] = {
            "app_id": self._settings.adzuna_app_id,
            "app_key": self._settings.adzuna_app_key,
            "what_and": TERMO_OBRIGATORIO,
            "max_days_old": self._settings.dias_recentes,
            "results_per_page": RESULTADOS_POR_PAGINA,
            "content-type": "application/json",
        }
        if termos:
            parametros["what_or"] = termos
        if cidade:
            parametros["where"] = cidade
        return parametros


def nome_exibido(campo: dict | None, padrao: str) -> str:
    nome = (campo or {}).get("display_name")
    return nome.strip() if nome and nome.strip() else padrao


def formatar_localizacao(campo: dict | None) -> str:
    area = (campo or {}).get("area") or []
    if len(area) > POSICAO_DA_CIDADE:
        return f"{area[POSICAO_DA_CIDADE]}, {area[POSICAO_DO_ESTADO]}"
    return nome_exibido(campo, LOCALIZACAO_PADRAO)


def converter_em_vaga(item: dict) -> Vaga:
    descricao = item["description"]
    return Vaga(
        id_externo=str(item["id"]),
        fonte=FONTE,
        titulo=item["title"],
        empresa=nome_exibido(item.get("company"), EMPRESA_NAO_INFORMADA),
        localizacao=formatar_localizacao(item.get("location")),
        descricao=descricao,
        url=item["redirect_url"],
        publicada_em=item["created"],
        descricao_completa=not descricao_esta_truncada(descricao),
    )


def descricao_esta_truncada(descricao: str) -> bool:
    return len(descricao) >= TAMANHO_DO_RESUMO_DA_API or descricao.rstrip().endswith(("…", "..."))
