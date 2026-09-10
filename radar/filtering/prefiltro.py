import re
import unicodedata

from radar.domain.areas import (
    area_do_curso,
    descricao_e_da_area,
    normalizar_curso,
    precedido_de_contexto_de_formacao,
    titulo_e_da_area,
    titulo_e_de_outra_area,
)
from radar.domain.models import Modalidade, Perfil, Vaga

PADRAO_ESTAGIO = re.compile(r"\bestagi|\bintern(?:ship)?s?\b")
PADRAO_SENIORIDADE = re.compile(r"\b(?:pleno|senior|especialista|coordenador)\b")
PADRAO_ENSINO_MEDIO = re.compile(
    r"\b(?:jovem|menor) aprendiz\b|\b(?:estudantes?|alunos?|para) (?:d[eo] )?ensino medio\b"
    r"|^\W*estagio\W+(?:de |em )?ensino medio\b|\bnivel medio\b"
)
PADRAO_TAMBEM_SUPERIOR = re.compile(r"\b(?:superior|graduacao|universitari[oa]s?|faculdade)\b")
PADRAO_POS_GRADUACAO = re.compile(
    r"\b(?:mestrado|doutorado|mestrand[oa]s?|doutorand[oa]s?|pos-?graduacao|pos-?graduand[oa]s?)\b"
)
PADRAO_ANOS_DE_EXPERIENCIA = re.compile(
    r"(\d+)\s*\+?\s*anos?\s+(?:de\s+)?experiencia"
    r"|experiencia\s+(?:minima\s+)?(?:de\s+)?(\d+)\s*\+?\s*anos?"
)
PADRAO_QUALQUER_FORMACAO = re.compile(
    r"\b(?:qualquer|todos os|todas as)\s+(?:cursos?|formacao|formacoes|graduacao|graduacoes)"
    r"\b(?!\s+(?:de|da|do|das|dos|em|na|no)\b)"
)
PADRAO_TRABALHO_REMOTO = re.compile(r"\b(?:remoto|remota|remote|home\s*office)\b")
PADRAO_TRABALHO_PRESENCIAL = re.compile(r"\b(?:presencial(?:mente)?|hibrid[oa]|hybrid|on-?site)\b")
PADRAO_EXPERIENCIA_DISPENSADA = re.compile(
    r"\bnao\s+(?:\w+\s+){0,3}?(?:exig\w*|ped\w*|precis\w*|requer\w*|necessari\w*)"
    r"|\bsem\s+(?:a\s+)?necessidade\b"
    r"|\bdispensa\w*\b"
)
ANOS_DE_EXPERIENCIA_QUE_DESCARTAM = range(2, 10)
PALAVRAS_ANTES_DA_EXIGENCIA = 8


def normalizar(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acentos.casefold()


def nao_e_estagio(vaga: Vaga) -> bool:
    return PADRAO_ESTAGIO.search(normalizar(vaga.titulo)) is None


def exige_senioridade(vaga: Vaga) -> bool:
    return PADRAO_SENIORIDADE.search(normalizar(vaga.titulo)) is not None


def exige_pos_graduacao(vaga: Vaga) -> bool:
    return PADRAO_POS_GRADUACAO.search(normalizar(vaga.titulo)) is not None


def exige_ensino_medio(vaga: Vaga) -> bool:
    titulo = normalizar(vaga.titulo)
    if PADRAO_TAMBEM_SUPERIOR.search(titulo):
        return False
    return PADRAO_ENSINO_MEDIO.search(titulo) is not None


def fora_da_area_do_curso(vaga: Vaga, perfil: Perfil) -> bool:
    area = area_do_curso(perfil.curso)
    titulo = normalizar(vaga.titulo)
    descricao = normalizar(vaga.descricao)
    if aceita_qualquer_formacao(descricao) or menciona_o_curso(descricao, perfil.curso):
        return False
    if area is None:
        return titulo_e_de_outra_area(titulo, None)
    if titulo_e_da_area(titulo, area):
        return False
    if titulo_e_de_outra_area(titulo, area):
        return True
    return not descricao_e_da_area(descricao, area)


def aceita_qualquer_formacao(descricao: str) -> bool:
    return PADRAO_QUALQUER_FORMACAO.search(descricao) is not None


def menciona_o_curso(descricao: str, curso_do_perfil: str) -> bool:
    curso = normalizar_curso(curso_do_perfil)
    if not curso:
        return False
    return any(
        precedido_de_contexto_de_formacao(descricao, ocorrencia.start())
        for ocorrencia in re.finditer(rf"\b{re.escape(curso)}\b", descricao)
    )


def exige_anos_de_experiencia(vaga: Vaga) -> bool:
    texto = normalizar(f"{vaga.titulo} {vaga.descricao}")
    anos_exigidos = (
        int(grupo)
        for ocorrencia in PADRAO_ANOS_DE_EXPERIENCIA.finditer(texto)
        if not exigencia_negada(texto, ocorrencia.start())
        for grupo in ocorrencia.groups()
        if grupo
    )
    return any(anos in ANOS_DE_EXPERIENCIA_QUE_DESCARTAM for anos in anos_exigidos)


def exigencia_negada(texto: str, posicao: int) -> bool:
    inicio_da_frase = texto.rfind(". ", 0, posicao) + 1
    anteriores = texto[inicio_da_frase:posicao].split()[-PALAVRAS_ANTES_DA_EXIGENCIA:]
    return PADRAO_EXPERIENCIA_DISPENSADA.search(" ".join(anteriores)) is not None


def localizacao_incompativel(vaga: Vaga, perfil: Perfil) -> bool:
    mesma_cidade = cidade(perfil.cidade) == cidade(vaga.localizacao)
    if perfil.modalidade is Modalidade.PRESENCIAL:
        return not mesma_cidade
    return not mesma_cidade and not admite_remoto(vaga)


def admite_remoto(vaga: Vaga) -> bool:
    if vaga.modalidade is not None:
        return vaga.modalidade is Modalidade.REMOTO
    texto = normalizar(f"{vaga.titulo} {vaga.descricao}")
    return PADRAO_TRABALHO_REMOTO.search(texto) is not None


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


MOTIVOS_DE_DESCARTE = (
    ("nao_e_estagio", lambda vaga, perfil: nao_e_estagio(vaga)),
    ("exige_senioridade", lambda vaga, perfil: exige_senioridade(vaga)),
    ("exige_pos_graduacao", lambda vaga, perfil: exige_pos_graduacao(vaga)),
    ("exige_ensino_medio", lambda vaga, perfil: exige_ensino_medio(vaga)),
    ("fora_da_area_do_curso", fora_da_area_do_curso),
    ("exige_anos_de_experiencia", lambda vaga, perfil: exige_anos_de_experiencia(vaga)),
    ("localizacao_incompativel", localizacao_incompativel),
    ("modalidade_incompativel", modalidade_incompativel),
)


def motivo_do_descarte(vaga: Vaga, perfil: Perfil) -> str | None:
    for motivo, descarta in MOTIVOS_DE_DESCARTE:
        if descarta(vaga, perfil):
            return motivo
    return None


def deve_descartar(vaga: Vaga, perfil: Perfil) -> bool:
    return motivo_do_descarte(vaga, perfil) is not None


def filtrar(vagas: list[Vaga], perfil: Perfil) -> list[Vaga]:
    return [vaga for vaga in vagas if not deve_descartar(vaga, perfil)]
