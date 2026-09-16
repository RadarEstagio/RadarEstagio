import re
from enum import StrEnum

from radar.domain.areas import normalizar
from radar.domain.models import Vaga

TERMO_PCD = r"(?:pcds?|pessoas? com deficiencias?|pessoas? portadoras? de deficiencias?)"
PADRAO_CITA_PCD = re.compile(rf"\b{TERMO_PCD}\b")
PADRAO_EXCLUSIVA_PARA_PCD = re.compile(
    rf"\bexclusiv(?:[ao]s?|amente)\s+(?:(?:para|a|as|aos)\s+)?{TERMO_PCD}\b"
    rf"|\b(?:somente|apenas|unicamente|so)\s+(?:para\s+)?{TERMO_PCD}\b"
    r"|\b(?:vagas?|oportunidades?|processos? seletivos?|estagios?)\s+"
    r"(?:de\s+(?:emprego|estagio)\s+)?"
    r"(?:(?:e|sao|esta|estao)\s+)?"
    r"(?:para|(?:destinad|voltad|direcionad|reservad)[ao]s?\s+(?:a|as|aos|para))\s+"
    rf"{TERMO_PCD}\b(?!\s+(?:tambem\b|(?:e|ou)\s+(?:ampla|demais|nao)\b))"
    rf"|\bvagas?\s+{TERMO_PCD}\b"
)
PADRAO_PCD_COMO_TRECHO_DO_TITULO = re.compile(rf"(?:^|[-|(/:]\s*){TERMO_PCD}\b")
PADRAO_NEGACAO_ANTES = re.compile(r"\bnao\s+(?:\w+\s+){0,2}$")
PADRAO_VAGA_AFIRMATIVA = re.compile(
    r"\b(?:vagas?|acao|processos? seletivos?|oportunidades?|estagios?|programas?)"
    r"\s+(?:de\s+estagio\s+)?afirmativ[ao]s?\b"
)
PADRAO_GRUPOS_DA_VAGA_AFIRMATIVA = re.compile(
    r"afirmativ[ao]s?\b[^()]{0,60}?\(([^()]{3,80})\)", re.IGNORECASE
)
CARACTERES_ANTES_DA_NEGACAO = 40
CARACTERES_DO_TRECHO_AFIRMATIVO = 160


class PublicoDaVaga(StrEnum):
    GERAL = "geral"
    EXCLUSIVO_PCD = "exclusivo_pcd"
    AFIRMATIVO = "afirmativo"
    AFIRMATIVO_COM_PCD = "afirmativo_com_pcd"


def publico_da_vaga(vaga: Vaga) -> PublicoDaVaga:
    titulo = normalizar(vaga.titulo)
    descricao = normalizar(vaga.descricao)
    if exclusiva_para_pcd(titulo, descricao):
        return PublicoDaVaga.EXCLUSIVO_PCD
    trecho = trecho_afirmativo(titulo) or trecho_afirmativo(descricao)
    if trecho is None:
        return PublicoDaVaga.GERAL
    grupos = grupos_da_vaga_afirmativa(vaga) or ""
    if PADRAO_CITA_PCD.search(trecho) or PADRAO_CITA_PCD.search(normalizar(grupos)):
        return PublicoDaVaga.AFIRMATIVO_COM_PCD
    return PublicoDaVaga.AFIRMATIVO


def exclusiva_para_pcd(titulo: str, descricao: str) -> bool:
    if trecho_afirmativo(titulo) is None and PADRAO_PCD_COMO_TRECHO_DO_TITULO.search(titulo):
        return True
    return afirma_exclusividade(titulo) or afirma_exclusividade(descricao)


def afirma_exclusividade(texto: str) -> bool:
    return any(
        not PADRAO_NEGACAO_ANTES.search(
            texto[max(0, ocorrencia.start() - CARACTERES_ANTES_DA_NEGACAO) : ocorrencia.start()]
        )
        for ocorrencia in PADRAO_EXCLUSIVA_PARA_PCD.finditer(texto)
    )


def trecho_afirmativo(texto: str) -> str | None:
    ocorrencia = PADRAO_VAGA_AFIRMATIVA.search(texto)
    if ocorrencia is None:
        return None
    fim_da_frase = texto.find(". ", ocorrencia.end())
    limite = ocorrencia.start() + CARACTERES_DO_TRECHO_AFIRMATIVO
    fim = limite if fim_da_frase == -1 else min(fim_da_frase, limite)
    return texto[ocorrencia.start() : fim]


def grupos_da_vaga_afirmativa(vaga: Vaga) -> str | None:
    for texto in (vaga.descricao, vaga.titulo):
        ocorrencia = PADRAO_GRUPOS_DA_VAGA_AFIRMATIVA.search(texto)
        if ocorrencia is not None:
            return " ".join(ocorrencia.group(1).split())
    return None
