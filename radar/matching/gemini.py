import json
import re

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.domain.texto import sem_caracteres_invalidos
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
INICIO_DO_CORPO_NO_ERRO = 200


def configuracao_de_raciocinio(
    raciocinio: str | None, resumir_o_raciocinio: bool = False
) -> types.ThinkingConfig | None:
    if raciocinio is None and not resumir_o_raciocinio:
        return None
    return types.ThinkingConfig(
        thinking_level=types.ThinkingLevel(raciocinio.upper()) if raciocinio else None,
        include_thoughts=resumir_o_raciocinio or None,
    )


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
        resposta = chamar_o_modelo(
            self._cliente,
            self._modelo,
            montar_prompt(vagas),
            ExtracoesDeVagas,
            self._timeout_segundos,
            raciocinio=self._raciocinio,
            resumir_o_raciocinio=True,
        )
        resumo = resumo_do_raciocinio(resposta)
        return [
            extracao.model_copy(update={"raciocinio_do_lote": resumo})
            for extracao in validar_json(resposta.text, ExtracoesDeVagas).extracoes
        ]


def gerar_json[T: BaseModel](
    cliente: genai.Client,
    modelo: str,
    prompt: str,
    formato: type[T],
    timeout_segundos: int,
    raciocinio: str | None = None,
) -> T:
    resposta = chamar_o_modelo(
        cliente, modelo, prompt, formato, timeout_segundos, raciocinio=raciocinio
    )
    return validar_json(resposta.text, formato)


def chamar_o_modelo(
    cliente: genai.Client,
    modelo: str,
    prompt: str,
    formato: type[BaseModel],
    timeout_segundos: int,
    raciocinio: str | None = None,
    resumir_o_raciocinio: bool = False,
) -> types.GenerateContentResponse:
    configuracao = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=formato,
        temperature=TEMPERATURA_DETERMINISTICA,
        http_options=types.HttpOptions(timeout=timeout_segundos * MILISSEGUNDOS_POR_SEGUNDO),
        thinking_config=configuracao_de_raciocinio(raciocinio, resumir_o_raciocinio),
    )
    try:
        resposta = cliente.models.generate_content(
            model=modelo, contents=prompt, config=configuracao
        )
    except httpx.TimeoutException:
        raise AvaliadorIndisponivel(f"Gemini não respondeu em {timeout_segundos} s") from None
    except httpx.RequestError as erro:
        raise AvaliadorIndisponivel(
            f"Falha de rede ao falar com o Gemini ({type(erro).__name__}): {erro}"
        ) from None
    except errors.APIError as erro:
        mensagem = f"Gemini respondeu HTTP {erro.code}: {erro.message}"
        if erro.code == HTTP_COTA_EXCEDIDA:
            raise CotaDeAvaliacaoExcedida(mensagem, tempo_de_espera(erro.message)) from None
        if erro.code == HTTP_FALHA_INTERNA:
            raise FalhaInternaDoAvaliador(mensagem) from None
        if erro.code in HTTP_INDISPONIVEL:
            raise AvaliadorIndisponivel(mensagem) from None
        raise ErroDeAvaliacao(mensagem) from None
    except json.JSONDecodeError as erro:
        raise AvaliadorIndisponivel(
            f"Gemini devolveu corpo que não é JSON: {erro.doc[:INICIO_DO_CORPO_NO_ERRO]!r}"
        ) from None
    except (AttributeError, TypeError, ValidationError) as erro:
        raise AvaliadorIndisponivel(
            f"Gemini devolveu resposta fora do formato da API: {erro}"
        ) from None
    return resposta


def resumo_do_raciocinio(resposta: types.GenerateContentResponse) -> str | None:
    if not resposta.candidates or not resposta.candidates[0].content:
        return None
    partes = resposta.candidates[0].content.parts or []
    resumo = "\n".join(parte.text for parte in partes if parte.thought and parte.text)
    return sem_caracteres_invalidos(resumo) or None


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
