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
PONTO_PERIODO_INCOMPATIVEL = "Período mínimo incompatível"
PONTO_EXPERIENCIA_EXIGIDA = "Exige experiência prévia"
ABERTURAS_A_QUALQUER_CURSO = frozenset(
    {"qualquer curso", "qualquer graduacao", "qualquer formacao", "todos os cursos"}
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
    aceitos = [curso for curso in extracao.cursos_aceitos if normalizar_curso(curso)]
    if not aceitos:
        return NivelCompatibilidade.PARCIAL
    if any(mesma_area(curso, perfil.curso) for curso in aceitos):
        return NivelCompatibilidade.COMPATIVEL
    if any(mesmo_curso(curso, perfil.curso) for curso in aceitos):
        return NivelCompatibilidade.COMPATIVEL
    return NivelCompatibilidade.INCOMPATIVEL


def aceita_qualquer_curso(extracao: ExtracaoDaVaga) -> bool:
    return extracao.aceita_qualquer_curso or any(
        normalizar(curso) in ABERTURAS_A_QUALQUER_CURSO for curso in extracao.cursos_aceitos
    )


def vaga_so_para_curso_tecnico(extracao: ExtracaoDaVaga, perfil: Perfil) -> bool:
    if curso_de_nivel_tecnico(perfil.curso) or aceita_qualquer_curso(extracao):
        return False
    cursos = extracao.cursos_aceitos
    return any(curso_de_nivel_tecnico(curso) for curso in cursos) and not any(
        formacao_de_nivel_superior(curso) for curso in cursos
    )


def nivel_do_periodo(extracao: ExtracaoDaVaga, perfil: Perfil) -> NivelCompatibilidade:
    if extracao.experiencia_minima_anos:
        return NivelCompatibilidade.INCOMPATIVEL
    if extracao.periodo_minimo is not None and perfil.periodo < extracao.periodo_minimo:
        return NivelCompatibilidade.INCOMPATIVEL
    if extracao.experiencia_desejavel:
        return NivelCompatibilidade.PARCIAL
    return NivelCompatibilidade.COMPATIVEL


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
    elif niveis.periodo_experiencia is NivelCompatibilidade.INCOMPATIVEL:
        contra.append(PONTO_PERIODO_INCOMPATIVEL)
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
