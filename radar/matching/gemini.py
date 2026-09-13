import re

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.matching.errors import (
    AvaliadorIndisponivel,
    CotaDeAvaliacaoExcedida,
    ErroDeAvaliacao,
    FalhaInternaDoAvaliador,
)
from radar.matching.extracao import ExtracoesDeVagas
from radar.matching.prompt import montar_prompt
from radar.settings import Settings

TEMPERATURA_DETERMINISTICA = 0
HTTP_COTA_EXCEDIDA = 429
HTTP_FALHA_INTERNA = 500
HTTP_INDISPONIVEL = frozenset({502, 503, 504})
MILISSEGUNDOS_POR_SEGUNDO = 1000
PADRAO_TEMPO_DE_ESPERA = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)
RACIOCINIO_DO_MODELO = "padrao"


def configuracao_de_raciocinio(raciocinio: str | None) -> types.ThinkingConfig | None:
    if raciocinio is None:
        return None
    return types.ThinkingConfig(thinking_level=types.ThinkingLevel(raciocinio.upper()))


class ExtratorGemini:
    def __init__(self, settings: Settings, cliente: genai.Client) -> None:
        self._modelo = settings.gemini_modelo
        self._timeout_segundos = settings.gemini_timeout_segundos
        self._raciocinio = (
            None
            if settings.gemini_raciocinio == RACIOCINIO_DO_MODELO
            else settings.gemini_raciocinio
        )
        self._cliente = cliente

    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        if not vagas:
            return []
        return gerar_json(
            self._cliente,
            self._modelo,
            montar_prompt(vagas),
            ExtracoesDeVagas,
            self._timeout_segundos,
            raciocinio=self._raciocinio,
        ).extracoes


def gerar_json[T: BaseModel](
    cliente: genai.Client,
    modelo: str,
    prompt: str,
    formato: type[T],
    timeout_segundos: int,
    raciocinio: str | None = None,
) -> T:
    try:
        resposta = cliente.models.generate_content(
            model=modelo,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=formato,
                temperature=TEMPERATURA_DETERMINISTICA,
                http_options=types.HttpOptions(
                    timeout=timeout_segundos * MILISSEGUNDOS_POR_SEGUNDO
                ),
                thinking_config=configuracao_de_raciocinio(raciocinio),
            ),
        )
    except httpx.TimeoutException:
        raise AvaliadorIndisponivel(f"Gemini não respondeu em {timeout_segundos} s") from None
    except httpx.TransportError as erro:
        raise AvaliadorIndisponivel(f"Falha de rede ao falar com o Gemini: {erro}") from None
    except errors.APIError as erro:
        mensagem = f"Gemini respondeu HTTP {erro.code}: {erro.message}"
        if erro.code == HTTP_COTA_EXCEDIDA:
            raise CotaDeAvaliacaoExcedida(mensagem, tempo_de_espera(erro.message)) from None
        if erro.code == HTTP_FALHA_INTERNA:
            raise FalhaInternaDoAvaliador(mensagem) from None
        if erro.code in HTTP_INDISPONIVEL:
            raise AvaliadorIndisponivel(mensagem) from None
        raise ErroDeAvaliacao(mensagem) from None
    return validar_json(resposta.text, formato)


def tempo_de_espera(mensagem: str | None) -> float | None:
    encontrado = PADRAO_TEMPO_DE_ESPERA.search(mensagem or "")
    return float(encontrado.group(1)) if encontrado else None


def interpretar_resposta(texto: str | None) -> ExtracoesDeVagas:
    return validar_json(texto, ExtracoesDeVagas)


def validar_json[T: BaseModel](texto: str | None, formato: type[T]) -> T:
    if not texto:
        raise ErroDeAvaliacao("Gemini devolveu resposta vazia")
    try:
        return formato.model_validate_json(texto)
    except ValidationError as erro:
        raise ErroDeAvaliacao(f"Gemini devolveu JSON fora do esperado: {erro}") from None
