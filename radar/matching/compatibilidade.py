import re

from pydantic import BaseModel

from radar.domain.areas import (
    AREAS_POR_NOME,
    area_do_curso,
    curso_de_nivel_tecnico,
    formacao_de_nivel_superior,
    normalizar,
    normalizar_curso,
)
from radar.domain.models import ExtracaoDaVaga, NivelCompatibilidade, Perfil

PONTO_CURSO_COMPATIVEL = "Curso compatível"
PONTO_EXPERIENCIA_EXIGIDA = "Exige experiência prévia"
ABERTURAS_A_QUALQUER_CURSO = frozenset(
    {"qualquer curso", "qualquer graduacao", "qualquer formacao", "todos os cursos"}
)
PADRAO_TECNICO_NO_ITEM = re.compile(r"\btecnic[oa]s?\b")
PADRAO_ALTERNATIVAS_DO_ITEM = re.compile(r"\s+(?:e/)?ou\s+|\s*[/,]\s*")
PADRAO_NIVEL_NO_INICIO = re.compile(
    r"^(?:(?:cursando|estudantes?|ensino|curso|nivel)\s+)*"
    r"(?:tecnic[oa]s?|superior|graduacao|graduand[oa]s?|bacharel(?:ado)?|licenciatura"
    r"|tecnolog[oa]s?|cst)(?:\s+(?:em|de|do|da|no|na))?(?:\s+|$)"
)


class NiveisDeCompatibilidade(BaseModel):
    area: NivelCompatibilidade
    curso: NivelCompatibilidade
    periodo_experiencia: NivelCompatibilidade
    so_para_curso_tecnico: bool = False


def derivar_niveis(extracao: ExtracaoDaVaga, perfil: Perfil) -> NiveisDeCompatibilidade:
    return NiveisDeCompatibilidade(
        area=nivel_da_area(extracao, perfil),
        curso=nivel_do_curso(extracao, perfil),
        periodo_experiencia=nivel_do_periodo(extracao, perfil),
        so_para_curso_tecnico=vaga_so_para_curso_tecnico(extracao, perfil),
    )


def nivel_da_area(extracao: ExtracaoDaVaga, perfil: Perfil) -> NivelCompatibilidade:
    if extracao.area_da_vaga is None:
        return NivelCompatibilidade.PARCIAL
    area_da_pessoa = area_do_curso(perfil.curso)
    if area_da_pessoa is None:
        return NivelCompatibilidade.PARCIAL
    if extracao.area_da_vaga == area_da_pessoa:
        return NivelCompatibilidade.COMPATIVEL
    return NivelCompatibilidade.INCOMPATIVEL


def nivel_do_curso(extracao: ExtracaoDaVaga, perfil: Perfil) -> NivelCompatibilidade:
    if aceita_qualquer_curso(extracao):
        return NivelCompatibilidade.COMPATIVEL
    if vaga_so_para_curso_tecnico(extracao, perfil):
        return NivelCompatibilidade.INCOMPATIVEL
    aceitos = [
        curso
        for item in extracao.cursos_aceitos
        for curso in cursos_do_item(item)
        if normalizar_curso(curso)
    ]
    if not aceitos:
        return NivelCompatibilidade.PARCIAL
    if any(mesma_area(curso, perfil.curso) for curso in aceitos):
        return NivelCompatibilidade.COMPATIVEL
    if any(mesmo_curso(curso, perfil.curso) for curso in aceitos):
        return NivelCompatibilidade.COMPATIVEL
    return NivelCompatibilidade.INCOMPATIVEL


def alternativas_do_item(curso: str) -> list[str]:
    texto = normalizar(curso)
    if PADRAO_TECNICO_NO_ITEM.search(texto) is None:
        return []
    alternativas = PADRAO_ALTERNATIVAS_DO_ITEM.split(texto)
    return alternativas if len(alternativas) > 1 else []


def formacoes_do_item(curso: str) -> list[str]:
    return alternativas_do_item(curso) or [curso]


def cursos_do_item(curso: str) -> list[str]:
    alternativas = alternativas_do_item(curso)
    if not alternativas:
        return [curso]
    return [PADRAO_NIVEL_NO_INICIO.sub("", alternativa) for alternativa in alternativas]


def aceita_qualquer_curso(extracao: ExtracaoDaVaga) -> bool:
    return extracao.aceita_qualquer_curso or any(
        normalizar(curso) in ABERTURAS_A_QUALQUER_CURSO for curso in extracao.cursos_aceitos
    )


def vaga_so_para_curso_tecnico(extracao: ExtracaoDaVaga, perfil: Perfil) -> bool:
    if curso_de_nivel_tecnico(perfil.curso) or aceita_qualquer_curso(extracao):
        return False
    formacoes = [
        formacao for curso in extracao.cursos_aceitos for formacao in formacoes_do_item(curso)
    ]
    return any(curso_de_nivel_tecnico(formacao) for formacao in formacoes) and not any(
        formacao_de_nivel_superior(formacao) for formacao in formacoes
    )


def nivel_do_periodo(extracao: ExtracaoDaVaga, perfil: Perfil) -> NivelCompatibilidade:
    if extracao.experiencia_minima_anos:
        return NivelCompatibilidade.INCOMPATIVEL
    if periodo_abaixo_do_minimo(extracao, perfil):
        return NivelCompatibilidade.INCOMPATIVEL
    if extracao.experiencia_desejavel:
        return NivelCompatibilidade.PARCIAL
    return NivelCompatibilidade.COMPATIVEL


def periodo_abaixo_do_minimo(extracao: ExtracaoDaVaga, perfil: Perfil) -> bool:
    return extracao.periodo_minimo is not None and perfil.periodo < extracao.periodo_minimo


def montar_pontos(
    extracao: ExtracaoDaVaga, niveis: NiveisDeCompatibilidade
) -> tuple[list[str], list[str]]:
    a_favor = []
    contra = []
    if niveis.curso is NivelCompatibilidade.COMPATIVEL and (
        extracao.cursos_aceitos or extracao.aceita_qualquer_curso
    ):
        a_favor.append(PONTO_CURSO_COMPATIVEL)
    if extracao.experiencia_minima_anos:
        contra.append(PONTO_EXPERIENCIA_EXIGIDA)
    return a_favor, contra


def mesma_area(aceito: str, do_perfil: str) -> bool:
    area_aceita = area_do_curso(aceito)
    if area_aceita is None or area_aceita != area_do_curso(do_perfil):
        return False
    return AREAS_POR_NOME[area_aceita].cursos_intercambiaveis


def mesmo_curso(aceito: str, do_perfil: str) -> bool:
    esquerda = normalizar_curso(aceito)
    direita = normalizar_curso(do_perfil)
    if not esquerda or not direita:
        return False
    if esquerda == direita:
        return True
    if area_do_curso(direita) is None:
        return False
    formas = [re.escape(esquerda)]
    if esquerda.endswith("s") and " " not in esquerda:
        formas.append(re.escape(esquerda[:-1]))
    return re.search(rf"\b(?:{'|'.join(formas)})\b", direita) is not None
