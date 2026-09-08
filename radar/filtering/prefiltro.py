import re
import unicodedata

from radar.domain.areas import (
    area_do_curso,
    descricao_e_da_area,
    normalizar_curso,
    titulo_e_da_area,
    titulo_e_de_outra_area,
)
from radar.domain.models import Modalidade, Perfil, Vaga

PADRAO_ESTAGIO = re.compile(r"\bestagi|\bintern(?:ship)?s?\b")
PADRAO_SENIORIDADE = re.compile(r"\b(?:pleno|senior|especialista|coordenador)\b")
PADRAO_ANOS_DE_EXPERIENCIA = re.compile(
    r"(\d+)\s*\+?\s*anos?\s+(?:de\s+)?experiencia"
    r"|experiencia\s+(?:minima\s+)?(?:de\s+)?(\d+)\s*\+?\s*anos?"
)
PADRAO_TRABALHO_REMOTO = re.compile(r"\b(?:remoto|remota|remote|home\s*office)\b")
PADRAO_TRABALHO_PRESENCIAL = re.compile(r"\b(?:presencial(?:mente)?|hibrid[oa]|hybrid|on-?site)\b")
ANOS_DE_EXPERIENCIA_QUE_DESCARTAM = range(2, 10)


def normalizar(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acentos.casefold()


def nao_e_estagio(vaga: Vaga) -> bool:
    return PADRAO_ESTAGIO.search(normalizar(vaga.titulo)) is None


def exige_senioridade(vaga: Vaga) -> bool:
    return PADRAO_SENIORIDADE.search(normalizar(vaga.titulo)) is not None


def fora_da_area_do_curso(vaga: Vaga, perfil: Perfil) -> bool:
    area = area_do_curso(perfil.curso)
    if area is None:
        return False
    descricao = normalizar(vaga.descricao)
    curso = normalizar_curso(perfil.curso)
    if curso and re.search(rf"\b{re.escape(curso)}\b", descricao):
        return False
    if re.search(
        r"\b(?:qualquer curso|qualquer formacao|qualquer graduacao|todas as areas)\b", descricao
    ):
        return False
    titulo = normalizar(vaga.titulo)
    if titulo_e_de_outra_area(titulo, area):
        return True
    if titulo_e_da_area(titulo, area):
        return False
    return not descricao_e_da_area(normalizar(vaga.descricao), area)


def exige_anos_de_experiencia(vaga: Vaga) -> bool:
    texto = normalizar(f"{vaga.titulo} {vaga.descricao}")
    anos_mencionados = (
        int(grupo)
        for ocorrencia in PADRAO_ANOS_DE_EXPERIENCIA.finditer(texto)
        for grupo in ocorrencia.groups()
        if grupo
    )
    return any(anos in ANOS_DE_EXPERIENCIA_QUE_DESCARTAM for anos in anos_mencionados)


def localizacao_incompativel(vaga: Vaga, perfil: Perfil) -> bool:
    if perfil.modalidade is not Modalidade.PRESENCIAL:
        return False
    return cidade(perfil.cidade) != cidade(vaga.localizacao)


def cidade(localizacao: str) -> str:
    return normalizar(localizacao.split(",")[0]).strip()


def modalidade_incompativel(vaga: Vaga, perfil: Perfil) -> bool:
    if perfil.modalidade is not Modalidade.REMOTO:
        return False
    if vaga.modalidade is not None:
        return vaga.modalidade is not Modalidade.REMOTO
    texto = normalizar(f"{vaga.titulo} {vaga.descricao}")
    exige_presenca = PADRAO_TRABALHO_PRESENCIAL.search(texto) is not None
    admite_remoto = PADRAO_TRABALHO_REMOTO.search(texto) is not None
    return exige_presenca and not admite_remoto


def deve_descartar(vaga: Vaga, perfil: Perfil) -> bool:
    return (
        nao_e_estagio(vaga)
        or exige_senioridade(vaga)
        or fora_da_area_do_curso(vaga, perfil)
        or exige_anos_de_experiencia(vaga)
        or localizacao_incompativel(vaga, perfil)
        or modalidade_incompativel(vaga, perfil)
    )


def filtrar(vagas: list[Vaga], perfil: Perfil) -> list[Vaga]:
    return [vaga for vaga in vagas if not deve_descartar(vaga, perfil)]
