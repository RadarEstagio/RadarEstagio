import re
import unicodedata

from radar.domain.areas import AREA_DA_SUBAREA, COMPUTACAO, ROTULOS_DAS_SUBAREAS, area_do_curso
from radar.domain.models import (
    AreaDeInteresse,
    ExtracaoDaVaga,
    Modalidade,
    NivelCompatibilidade,
    Perfil,
    ResultadoMatch,
    Vaga,
)
from radar.matching.compatibilidade import (
    NiveisDeCompatibilidade,
    derivar_niveis,
    montar_pontos,
)

PESO_HABILIDADES = 45
PESO_CURSO = 10
PESO_AREA = 10
PESO_PERIODO_EXPERIENCIA = 15
PESO_LOGISTICA = 10
PESO_INTERESSE = 10
LIMITE_FORA_DAS_AREAS_DE_INTERESSE = 65
LIMITE_CURSO_PARCIAL = 75
LIMITE_CURSO_INCOMPATIVEL = 35
AVISO_CURSO_INCOMPATIVEL = "Exige formação de outra área"
AREAS_RECONHECIDAS = frozenset(area.value for area in AreaDeInteresse)
INTERESSE_SEM_AREA_RECONHECIDA = 0.5
INTERESSE_DE_OUTRA_SUBAREA = 0.5
AVISO_FORA_DAS_AREAS_DE_INTERESSE = "Fora das suas áreas de interesse"
AVISO_AREA_RECUSADA = "Área que você recusou nos últimos dias"
PESO_OBRIGATORIAS_QUANDO_MISTAS = 0.8
PESO_DESEJAVEIS_QUANDO_MISTAS = 0.2
PESO_OBRIGATORIAS_COM_PRINCIPAIS = 0.7
PESO_PRINCIPAIS_COM_OBRIGATORIAS = 0.3
PESO_PRINCIPAIS_COM_DESEJAVEIS = 0.8
PESO_DESEJAVEIS_COM_PRINCIPAIS = 0.2
PESO_OBRIGATORIAS_QUANDO_TODAS = 0.6
PESO_PRINCIPAIS_QUANDO_TODAS = 0.3
PESO_DESEJAVEIS_QUANDO_TODAS = 0.1
COBERTURA_NEUTRA_SEM_STACK_DECLARADA = 0.35
SUAVIZACAO_DA_COBERTURA = 1
COEFICIENTES = {
    "compativel": 1.0,
    "parcial": 0.5,
    "incompativel": 0.0,
}
REQUISITOS_FORA_DO_PERFIL_TECNICO = frozenset(
    {
        "apresentacoes",
        "documentos",
        "drive",
        "excel",
        "libreoffice",
        "microsoft365",
        "microsoftoffice",
        "msoffice",
        "office",
        "outlook",
        "pacoteoffice",
        "planilhas",
        "powerpoint",
        "teams",
        "word",
    }
)
PREFIXOS_DE_IDIOMA = ("alemao", "espanhol", "frances", "ingles", "italiano", "mandarim")
QUALIFICADORES_DE_HABILIDADE = re.compile(
    r"\b(?:avancad[oa]s?|intermediari[oa]s?|basic[oa]s?|fluente|nativ[oa]|iniciante|nivel"
    r"|bom|boa|bons|boas|otim[oa]|excelente|solid[oa]|conhecimentos?|dominio|nocoes"
    r"|experiencia|vivencia|habilidades?|em|de|do|da|com|no|na)\b"
)
NIVEL_NAO_INFORMADO = 0
PADROES_DE_NIVEL = (
    (re.compile(r"\b(?:basic[oa]s?|iniciante|nocoes)\b"), 1),
    (re.compile(r"\bintermediari[oa]s?\b"), 2),
    (re.compile(r"\b(?:avancad[oa]s?|fluente|nativ[oa]|dominio)\b"), 3),
)
ALIASES_DE_HABILIDADES = {
    "office365": "office",
    "microsoft365": "office",
    "msoffice": "office",
    "microsoftoffice": "office",
    "pacoteoffice": "office",
    "apresentacoesgoogle": "apresentacoes",
    "cplusplus": "c++",
    "documentosgoogle": "documentos",
    "googleapresentacoes": "apresentacoes",
    "googledocs": "documentos",
    "googledocumentos": "documentos",
    "googledrive": "drive",
    "googleplanilhas": "planilhas",
    "googlesheets": "planilhas",
    "googleslides": "apresentacoes",
    "googleworkspace": "office",
    "gsuite": "office",
    "msexcel": "excel",
    "microsoftexcel": "excel",
    "microsoftoutlook": "outlook",
    "microsoftpowerpoint": "powerpoint",
    "microsoftteams": "teams",
    "microsoftword": "word",
    "planilhasgoogle": "planilhas",
    "cpp": "c++",
    "csharp": "c#",
    "css3": "css",
    "golang": "go",
    "html5": "html",
    "js": "javascript",
    "node": "nodejs",
    "postgres": "postgresql",
    "python3": "python",
    "reactjs": "react",
    "restapi": "rest",
    "ts": "typescript",
    "vuejs": "vue",
}


def pontuar_vagas(
    vagas: list[Vaga], extracoes: dict[str, ExtracaoDaVaga], perfil: Perfil
) -> list[ResultadoMatch]:
    resultados = []
    for vaga in vagas:
        extracao = extracoes.get(vaga.id_externo)
        if extracao is None:
            continue
        resultados.append(pontuar(vaga, extracao, perfil))
    return resultados


def pontuar(vaga: Vaga, extracao: ExtracaoDaVaga, perfil: Perfil) -> ResultadoMatch:
    vaga = _com_modalidade_extraida(vaga, extracao)
    niveis = derivar_niveis(extracao, perfil)
    requisitos_atendidos, requisitos_nao_atendidos = _classificar_habilidades(extracao, perfil)
    pontos_a_favor, pontos_contra = montar_pontos(extracao, niveis)
    return ResultadoMatch(
        vaga=vaga,
        nota=_calcular_nota(extracao, niveis, vaga, perfil),
        requisitos_atendidos=requisitos_atendidos,
        requisitos_nao_atendidos=requisitos_nao_atendidos,
        requisitos_tecnicos_analisados=True,
        avisos_objetivos=_avisos_objetivos(extracao, niveis, perfil),
        pontos_a_favor=_juntar_sem_repetir(pontos_a_favor),
        pontos_contra=_juntar_sem_repetir(pontos_contra),
        alerta_pegadinha=extracao.alerta_pegadinha,
    )


def _com_modalidade_extraida(vaga: Vaga, extracao: ExtracaoDaVaga) -> Vaga:
    if vaga.modalidade is not None:
        return vaga
    extraida = extracao.modalidade_reconhecida()
    if extraida is None:
        return vaga
    return vaga.model_copy(update={"modalidade": extraida})


def _calcular_nota(
    extracao: ExtracaoDaVaga, niveis: NiveisDeCompatibilidade, vaga: Vaga, perfil: Perfil
) -> int:
    interesse = _compatibilidade_de_interesse(extracao, perfil)
    nota = (
        PESO_HABILIDADES * _compatibilidade_de_habilidades(extracao, perfil)
        + PESO_CURSO * _coeficiente(niveis.curso)
        + PESO_AREA * _coeficiente(niveis.area)
        + PESO_PERIODO_EXPERIENCIA * _coeficiente(niveis.periodo_experiencia)
        + PESO_LOGISTICA * _compatibilidade_logistica(vaga, perfil)
        + PESO_INTERESSE * interesse
    )
    nota = min(nota, _limite_por_interesse(extracao, perfil, interesse))
    nota = min(nota, _limite_por_curso(niveis))
    return int(nota + 0.5)


def _limite_por_interesse(extracao: ExtracaoDaVaga, perfil: Perfil, interesse: float) -> float:
    if interesse == 0.0:
        return LIMITE_FORA_DAS_AREAS_DE_INTERESSE
    if perfil.areas_de_interesse and not _areas_reconhecidas(extracao):
        return LIMITE_FORA_DAS_AREAS_DE_INTERESSE
    return 100.0


def _limite_por_curso(niveis: NiveisDeCompatibilidade) -> float:
    if niveis.curso is NivelCompatibilidade.INCOMPATIVEL:
        return LIMITE_CURSO_INCOMPATIVEL
    if niveis.curso is NivelCompatibilidade.PARCIAL:
        return LIMITE_CURSO_PARCIAL
    return 100.0


def _compatibilidade_de_interesse(extracao: ExtracaoDaVaga, perfil: Perfil) -> float:
    areas_da_vaga = _areas_reconhecidas(extracao)
    if _area_recusada(areas_da_vaga, perfil):
        return 0.0
    if not perfil.areas_de_interesse:
        return 1.0
    if not areas_da_vaga:
        return INTERESSE_SEM_AREA_RECONHECIDA
    interesses = {area.value for area in perfil.areas_de_interesse}
    if areas_da_vaga & interesses:
        return 1.0
    if _mesmo_campo(areas_da_vaga, interesses):
        return INTERESSE_DE_OUTRA_SUBAREA
    return 0.0


def _mesmo_campo(areas_da_vaga: set[str], interesses: set[str]) -> bool:
    campos_da_vaga = {AREA_DA_SUBAREA[area] for area in areas_da_vaga}
    campos_de_interesse = {AREA_DA_SUBAREA[area] for area in interesses}
    return bool(campos_da_vaga & campos_de_interesse)


def _area_recusada(areas_da_vaga: set[str], perfil: Perfil) -> bool:
    recusadas = {area.value for area in perfil.areas_recusadas}
    return bool(areas_da_vaga & recusadas)


def _avisos_objetivos(
    extracao: ExtracaoDaVaga, niveis: NiveisDeCompatibilidade, perfil: Perfil
) -> list[str]:
    avisos = []
    recusadas = _areas_reconhecidas(extracao) & {area.value for area in perfil.areas_recusadas}
    if recusadas:
        avisos.append(aviso_de_area_recusada(recusadas))
    elif _compatibilidade_de_interesse(extracao, perfil) == 0.0 and perfil.areas_de_interesse:
        avisos.append(AVISO_FORA_DAS_AREAS_DE_INTERESSE)
    if niveis.curso is NivelCompatibilidade.INCOMPATIVEL:
        avisos.append(AVISO_CURSO_INCOMPATIVEL)
    return avisos


def aviso_de_area_recusada(areas: set[str]) -> str:
    rotulos = ", ".join(ROTULOS_DAS_SUBAREAS[area] for area in sorted(areas))
    return f"{AVISO_AREA_RECUSADA}: {rotulos}"


def _areas_reconhecidas(extracao: ExtracaoDaVaga) -> set[str]:
    return {area.strip().casefold() for area in extracao.areas_da_vaga} & AREAS_RECONHECIDAS


def _compatibilidade_de_habilidades(extracao: ExtracaoDaVaga, perfil: Perfil) -> float:
    obrigatorias = _cobertura(extracao.habilidades_obrigatorias, perfil)
    principais = _cobertura(extracao.habilidades_principais, perfil)
    desejaveis = _cobertura(extracao.habilidades_desejaveis, perfil)
    if obrigatorias is not None and principais is not None and desejaveis is not None:
        return (
            PESO_OBRIGATORIAS_QUANDO_TODAS * obrigatorias
            + PESO_PRINCIPAIS_QUANDO_TODAS * principais
            + PESO_DESEJAVEIS_QUANDO_TODAS * desejaveis
        )
    if obrigatorias is not None and principais is not None:
        return (
            PESO_OBRIGATORIAS_COM_PRINCIPAIS * obrigatorias
            + PESO_PRINCIPAIS_COM_OBRIGATORIAS * principais
        )
    if obrigatorias is not None and desejaveis is not None:
        return (
            PESO_OBRIGATORIAS_QUANDO_MISTAS * obrigatorias
            + PESO_DESEJAVEIS_QUANDO_MISTAS * desejaveis
        )
    if principais is not None and desejaveis is not None:
        return (
            PESO_PRINCIPAIS_COM_DESEJAVEIS * principais
            + PESO_DESEJAVEIS_COM_PRINCIPAIS * desejaveis
        )
    if obrigatorias is not None:
        return obrigatorias
    if principais is not None:
        return principais
    if desejaveis is not None:
        return desejaveis
    return COBERTURA_NEUTRA_SEM_STACK_DECLARADA


def _cobertura(requisitos: list[str], perfil: Perfil) -> float | None:
    exigencias = _niveis_exigidos(requisitos)
    if area_do_curso(perfil.curso) == COMPUTACAO:
        exigencias = {nome: nivel for nome, nivel in exigencias.items() if _conta_para_a_nota(nome)}
    if not exigencias:
        return None
    niveis_do_perfil = _niveis_do_perfil(perfil)
    atendidas = [
        nome for nome, nivel in exigencias.items() if _atende(nome, nivel, niveis_do_perfil)
    ]
    return (SUAVIZACAO_DA_COBERTURA + len(atendidas)) / (SUAVIZACAO_DA_COBERTURA + len(exigencias))


def _niveis_exigidos(requisitos: list[str]) -> dict[str, int]:
    exigencias: dict[str, int] = {}
    for requisito in requisitos:
        if requisito.strip():
            nome = _normalizar_habilidade(requisito)
            nivel = _nivel_exigido(requisito)
            exigencias[nome] = min(exigencias.get(nome, nivel), nivel)
    return exigencias


def _niveis_do_perfil(perfil: Perfil) -> dict[str, int]:
    niveis: dict[str, int] = {}
    for habilidade in perfil.habilidades:
        if habilidade.strip():
            nome = _normalizar_habilidade(habilidade)
            niveis[nome] = max(niveis.get(nome, NIVEL_NAO_INFORMADO), _nivel_declarado(habilidade))
    return niveis


def _atende(nome: str, nivel_exigido: int, niveis_do_perfil: dict[str, int]) -> bool:
    if nome not in niveis_do_perfil:
        return False
    nivel_do_perfil = niveis_do_perfil[nome]
    if nivel_exigido == NIVEL_NAO_INFORMADO:
        return True
    return nivel_do_perfil >= nivel_exigido


def _perfil_atende(habilidade: str, niveis_do_perfil: dict[str, int]) -> bool:
    return _atende(_normalizar_habilidade(habilidade), _nivel_exigido(habilidade), niveis_do_perfil)


def _nivel_exigido(habilidade: str) -> int:
    return min(_niveis_citados(habilidade), default=NIVEL_NAO_INFORMADO)


def _nivel_declarado(habilidade: str) -> int:
    return max(_niveis_citados(habilidade), default=NIVEL_NAO_INFORMADO)


def _niveis_citados(habilidade: str) -> set[int]:
    texto = _normalizar_texto(habilidade)
    return {nivel for padrao, nivel in PADROES_DE_NIVEL if padrao.search(texto)}


def _conta_para_a_nota(requisito_normalizado: str) -> bool:
    if requisito_normalizado in REQUISITOS_FORA_DO_PERFIL_TECNICO:
        return False
    return not requisito_normalizado.startswith(PREFIXOS_DE_IDIOMA)


def _classificar_habilidades(
    extracao: ExtracaoDaVaga, perfil: Perfil
) -> tuple[list[str], list[str]]:
    niveis_do_perfil = _niveis_do_perfil(perfil)
    requisitos_atendidos = [
        habilidade
        for habilidade in _juntar_habilidades_da_vaga(extracao)
        if _perfil_atende(habilidade, niveis_do_perfil)
    ]
    requisitos_nao_atendidos = [
        habilidade
        for habilidade in _exigidas_pela_vaga(extracao)
        if not _perfil_atende(habilidade, niveis_do_perfil)
    ]
    return requisitos_atendidos, requisitos_nao_atendidos


def _exigidas_pela_vaga(extracao: ExtracaoDaVaga) -> list[str]:
    unicas: dict[str, str] = {}
    for habilidade in extracao.habilidades_obrigatorias + extracao.habilidades_principais:
        if habilidade.strip():
            unicas.setdefault(_normalizar_habilidade(habilidade), habilidade.strip())
    return list(unicas.values())


def _juntar_habilidades_da_vaga(extracao: ExtracaoDaVaga) -> list[str]:
    habilidades = (
        extracao.habilidades_obrigatorias
        + extracao.habilidades_principais
        + extracao.habilidades_desejaveis
    )
    unicas: dict[str, str] = {}
    for habilidade in habilidades:
        if habilidade.strip():
            unicas.setdefault(_normalizar_habilidade(habilidade), habilidade.strip())
    return list(unicas.values())


def _juntar_sem_repetir(*grupos: list[str]) -> list[str]:
    unicos: dict[str, str] = {}
    for item in (item for grupo in grupos for item in grupo):
        if item.strip():
            unicos.setdefault(_normalizar_texto(item), item.strip())
    return list(unicos.values())


def _normalizar_habilidade(habilidade: str) -> str:
    normalizada = QUALIFICADORES_DE_HABILIDADE.sub(" ", _normalizar_texto(habilidade))
    compacta = "".join(
        caractere for caractere in normalizada if caractere.isalnum() or caractere in "#+"
    )
    return ALIASES_DE_HABILIDADES.get(compacta, compacta)


def _coeficiente(nivel: NivelCompatibilidade) -> float:
    return COEFICIENTES[nivel.value]


def _compatibilidade_logistica(vaga: Vaga, perfil: Perfil) -> float:
    localizacao = _compatibilidade_de_localizacao(vaga, perfil)
    modalidade = _compatibilidade_de_modalidade(vaga, perfil)
    return (localizacao + modalidade) / 2


def _compatibilidade_de_localizacao(vaga: Vaga, perfil: Perfil) -> float:
    if vaga.modalidade is Modalidade.REMOTO or perfil.modalidade is Modalidade.REMOTO:
        return 1.0
    cidade_da_vaga = _normalizar_texto(vaga.localizacao.split(",")[0])
    cidade_do_perfil = _normalizar_texto(perfil.nome_da_cidade())
    return 1.0 if cidade_da_vaga == cidade_do_perfil else 0.0


def _compatibilidade_de_modalidade(vaga: Vaga, perfil: Perfil) -> float:
    if vaga.modalidade is None:
        return 0.5
    if perfil.modalidade is Modalidade.INDIFERENTE or vaga.modalidade is perfil.modalidade:
        return 1.0
    if perfil.modalidade is Modalidade.PRESENCIAL and vaga.modalidade is Modalidade.HIBRIDO:
        return 0.5
    return 0.0


def _normalizar_texto(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acentos.casefold().strip()
