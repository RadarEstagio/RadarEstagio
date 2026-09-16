import re
from enum import StrEnum

from radar.domain.areas import normalizar
from radar.domain.models import Vaga

TERMO_PCD = r"(?:pcds?|pessoas? com deficiencias?|pessoas? portadoras? de deficiencias?)"
SUJEITO_DA_VAGA = r"(?:vaga|oportunidade|processo seletivo|selecao)"
QUALIFICADOR_DE_PUBLICO = (
    r"(?:exclusiv[ao]|exclusivamente|somente|apenas|unicamente"
    r"|destinad[ao]|voltad[ao]|direcionad[ao]|reservad[ao])"
)
SEM_OUTRO_PUBLICO_DEPOIS = r"(?!\s*,?\s*(?:e|ou)\b)(?!\s+tambem\b)(?!\s*[:?]?\s*nao\b)"
PADRAO_CITA_PCD = re.compile(rf"\b{TERMO_PCD}\b")
PADRAO_EXCLUSIVA_PARA_PCD = re.compile(
    rf"\b{SUJEITO_DA_VAGA}\s+(?:afirmativa\s+)?(?:de\s+(?:emprego|estagio)\s+)?"
    rf"(?:(?:e|sera|esta)\s+)?"
    rf"(?:para|{QUALIFICADOR_DE_PUBLICO}\s+(?:(?:para|a|as|aos)\s+)?)\s*{TERMO_PCD}\b"
    rf"{SEM_OUTRO_PUBLICO_DEPOIS}"
    rf"|\bvaga\s+{TERMO_PCD}\b{SEM_OUTRO_PUBLICO_DEPOIS}"
    rf"|\b(?:inscricoes|candidaturas)\s+(?:(?:sao|serao)\s+)?"
    rf"(?:exclusivas|exclusivamente|somente|apenas|unicamente)\s+(?:para|de)\s+{TERMO_PCD}\b"
    rf"{SEM_OUTRO_PUBLICO_DEPOIS}"
)
PADRAO_PCD_COMO_TRECHO_DO_TITULO = re.compile(
    rf"(?:^|\s[-|]\s*|\()\s*(?:vaga\s+)?(?:exclusiv[ao]\s+(?:para\s+)?)?{TERMO_PCD}"
    r"\s*(?:$|\)|\s[-|]\s)"
    rf"|^\W*estagi\w*\s+(?:exclusivo\s+)?para\s+{TERMO_PCD}\b{SEM_OUTRO_PUBLICO_DEPOIS}"
)
PADRAO_CONTEXTO_QUE_ANULA = re.compile(
    r"\b(?:nao|tambem|nossas?|outras?|confira|conheca|programas?|reservas?)\s+(?:[\w-]+\s+){0,3}$"
)
PADRAO_VAGA_AFIRMATIVA = re.compile(
    r"\b(?:vaga|acao|processo seletivo|oportunidade|estagio|programa|selecao)"
    r"\s+(?:de\s+estagio\s+)?afirmativ[ao]\b"
)
PADRAO_TITULO_AFIRMATIVO = re.compile(r"\bafirmativ[ao]s?\b")
PADRAO_GRUPOS_NA_DESCRICAO = re.compile(
    r"\b(?:vaga|a[cç][aã]o|processo seletivo|oportunidade|est[aá]gio|programa|sele[cç][aã]o)"
    r"\s+(?:de\s+est[aá]gio\s+)?afirmativ[ao]\b[^().]{0,40}?\(([^()]{3,80})\)",
    re.IGNORECASE,
)
PADRAO_GRUPOS_NO_TITULO = re.compile(
    r"\bafirmativ[ao]s?\b[^().]{0,40}?\(([^()]{3,80})\)", re.IGNORECASE
)
PADRAO_NOME_DE_GRUPO = re.compile(
    r"\b(?:pcds?|deficien\w*|negr[oa]s?|pret[oa]s?|pard[oa]s?|indigenas?|raca|racial|etni\w*"
    r"|mulher(?:es)?|genero|lgbt\w*|trans|\d{2}|idade|diversidade)\b"
)
CARACTERES_ANTES_DO_CONTEXTO = 60
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
    trecho = trecho_afirmativo(titulo, PADRAO_TITULO_AFIRMATIVO) or trecho_afirmativo(
        descricao, PADRAO_VAGA_AFIRMATIVA
    )
    if trecho is None:
        return PublicoDaVaga.GERAL
    grupos = grupos_da_vaga_afirmativa(vaga) or ""
    if PADRAO_CITA_PCD.search(trecho) or PADRAO_CITA_PCD.search(normalizar(grupos)):
        return PublicoDaVaga.AFIRMATIVO_COM_PCD
    return PublicoDaVaga.AFIRMATIVO


def exclusiva_para_pcd(titulo: str, descricao: str) -> bool:
    if PADRAO_TITULO_AFIRMATIVO.search(titulo) is None and afirma_publico(
        titulo, PADRAO_PCD_COMO_TRECHO_DO_TITULO
    ):
        return True
    return afirma_publico(titulo, PADRAO_EXCLUSIVA_PARA_PCD) or afirma_publico(
        descricao, PADRAO_EXCLUSIVA_PARA_PCD
    )


def afirma_publico(texto: str, padrao: re.Pattern[str]) -> bool:
    return any(
        not PADRAO_CONTEXTO_QUE_ANULA.search(
            texto[max(0, ocorrencia.start() - CARACTERES_ANTES_DO_CONTEXTO) : ocorrencia.start()]
        )
        for ocorrencia in padrao.finditer(texto)
    )


def trecho_afirmativo(texto: str, padrao: re.Pattern[str]) -> str | None:
    ocorrencia = padrao.search(texto)
    if ocorrencia is None:
        return None
    fim_da_frase = texto.find(". ", ocorrencia.end())
    limite = ocorrencia.start() + CARACTERES_DO_TRECHO_AFIRMATIVO
    fim = limite if fim_da_frase == -1 else min(fim_da_frase, limite)
    return texto[ocorrencia.start() : fim]


def grupos_da_vaga_afirmativa(vaga: Vaga) -> str | None:
    for texto, padrao in (
        (vaga.descricao, PADRAO_GRUPOS_NA_DESCRICAO),
        (vaga.titulo, PADRAO_GRUPOS_NO_TITULO),
    ):
        for ocorrencia in padrao.finditer(texto):
            grupos = " ".join(ocorrencia.group(1).split())
            if "," in grupos and PADRAO_NOME_DE_GRUPO.search(normalizar(grupos)):
                return grupos
    return None
