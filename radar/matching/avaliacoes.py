import functools
import re
import unicodedata
from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import NamedTuple

from radar.domain.areas import AREA_DA_SUBAREA, COMPUTACAO, ROTULOS_DAS_SUBAREAS, area_do_curso
from radar.domain.models import (
    AreaDeInteresse,
    ChaveDaVaga,
    ExtracaoDaVaga,
    Modalidade,
    NivelCompatibilidade,
    Perfil,
    ResultadoMatch,
    Vaga,
)
from radar.domain.regioes import Proximidade, proximidade
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
LOCALIZACAO_POR_PROXIMIDADE = {
    Proximidade.MESMA_CIDADE: 1.0,
    Proximidade.MESMA_REGIAO: 0.5,
    Proximidade.DISTANTE: 0.0,
}
LIMITE_FORA_DAS_AREAS_DE_INTERESSE = 65
LIMITE_CURSO_PARCIAL = 75
LIMITE_CURSO_INCOMPATIVEL = 35
AVISO_CURSO_INCOMPATIVEL = "Exige formação de outra área"
AREAS_RECONHECIDAS = frozenset(area.value for area in AreaDeInteresse)
INTERESSE_SEM_AREA_RECONHECIDA = 0.5
INTERESSE_DE_OUTRA_SUBAREA = 0.5
AVISO_FORA_DAS_AREAS_DE_INTERESSE = "Fora das suas áreas de interesse"
AVISO_AREA_RECUSADA = "Área que você recusou nos últimos dias"
AVISO_SEM_HABILIDADES_NO_PERFIL = "Nota calculada sem habilidades no seu perfil"
PESO_OBRIGATORIAS_QUANDO_MISTAS = 0.8
PESO_DESEJAVEIS_QUANDO_MISTAS = 0.2
PESO_OBRIGATORIAS_COM_PRINCIPAIS = 0.7
PESO_PRINCIPAIS_COM_OBRIGATORIAS = 0.3
PESO_PRINCIPAIS_COM_DESEJAVEIS = 0.8
PESO_DESEJAVEIS_COM_PRINCIPAIS = 0.2
PESO_OBRIGATORIAS_QUANDO_TODAS = 0.6
PESO_PRINCIPAIS_QUANDO_TODAS = 0.3
PESO_DESEJAVEIS_QUANDO_TODAS = 0.1
COBERTURA_NEUTRA_SEM_STACK_DECLARADA = 0.25
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
SOFT_SKILLS = frozenset(
    {
        "adaptabilidade",
        "aprendizado",
        "aprendizadocontinuo",
        "atencaodetalhes",
        "autonomia",
        "colaboracao",
        "comprometimento",
        "comunicacao",
        "comunicacaoescrita",
        "comunicacaooral",
        "criatividade",
        "curiosidade",
        "dedicacao",
        "empatia",
        "etica",
        "flexibilidade",
        "lideranca",
        "organizacao",
        "pontualidade",
        "proatividade",
        "raciociniologico",
        "relacionamentointerpessoal",
        "resiliencia",
        "responsabilidade",
        "trabalhoequipe",
        "vontadeaprender",
    }
)
PREFIXOS_DE_IDIOMA = ("alemao", "espanhol", "frances", "ingles", "italiano", "mandarim")
QUALIFICADORES_DE_HABILIDADE = re.compile(
    r"\b(?:avancad[oa]s?|intermediari[oa]s?|basic[oa]s?|fluentes?|nativ[oa]s?|iniciantes?|nivel"
    r"|bom|boa|bons|boas|otim[oa]|excelente|solid[oa]|conhecimentos?|dominio|nocoes"
    r"|experiencia|vivencia|habilidades?|em|de|do|da|com|no|na)\b"
)
COMPLEMENTO_ENTRE_PARENTESES = re.compile(r"\([^)]*\)")
NIVEL_NAO_INFORMADO = 0
PADROES_DE_NIVEL = (
    (re.compile(r"\b(?:basic[oa]s?|iniciantes?|nocoes)\b"), 1),
    (re.compile(r"\bintermediari[oa]s?\b"), 2),
    (re.compile(r"\b(?:avancad[oa]s?|fluentes?|nativ[oa]s?|dominio)\b"), 3),
)
BANCOS_DE_DADOS = (
    "SQL",
    "MySQL",
    "PostgreSQL",
    "Postgres",
    "Oracle",
    "SQL Server",
    "MongoDB",
    "SQLite",
    "MariaDB",
    "Redis",
    "DynamoDB",
    "Firebase",
)
BACK_END = (
    "Java",
    "Spring",
    "Spring Boot",
    "Python",
    "Django",
    "Flask",
    "FastAPI",
    "Node",
    "Node.js",
    "Express",
    "NestJS",
    "PHP",
    "Laravel",
    "C#",
    ".NET",
    "Go",
    "Golang",
    "Ruby",
    "Rails",
    "Ruby on Rails",
    "Kotlin",
    "Rust",
)
FRONT_END = (
    "React",
    "JavaScript",
    "TypeScript",
    "HTML",
    "CSS",
    "Vue",
    "Vue.js",
    "Angular",
    "Next.js",
    "Svelte",
    "Tailwind",
    "Sass",
    "Bootstrap",
)
LINGUAGENS = (
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C",
    "C++",
    "C#",
    "Go",
    "Golang",
    "Kotlin",
    "Swift",
    "PHP",
    "Ruby",
    "Rust",
    "Lua",
    "Dart",
    "Scala",
    "R",
    "Lógica de Programação",
)
FERRAMENTAS_DE_ETL = (
    "SQL",
    "Python",
    "Pandas",
    "Airflow",
    "Spark",
    "Databricks",
    "dbt",
    "Talend",
    "Pentaho",
)
NUVENS = ("AWS", "Azure", "GCP", "Google Cloud", "Cloud")
VERSIONAMENTO = ("Git", "GitHub", "GitLab", "Bitbucket")
MOBILE = ("Android", "iOS", "Kotlin", "Swift", "Flutter", "React Native", "Dart")
OFFICE = ("Excel", "Word", "PowerPoint", "Outlook", "Planilhas", "Documentos", "Apresentações")
FERRAMENTAS_DE_DADOS = ("SQL", "Python", "Power BI", "Excel", "Pandas", "Tableau", "Looker", "R")
INTELIGENCIA_ARTIFICIAL = (
    "Machine Learning",
    "Deep Learning",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "NLP",
    "LLM",
)
FAMILIAS_DE_HABILIDADES = {
    "banco de dados": BANCOS_DE_DADOS,
    "bancos de dados": BANCOS_DE_DADOS,
    "BD": BANCOS_DE_DADOS,
    "SGBD": BANCOS_DE_DADOS,
    "banco de dados relacional": BANCOS_DE_DADOS,
    "bancos de dados relacionais": BANCOS_DE_DADOS,
    "back-end": BACK_END,
    "desenvolvimento back-end": BACK_END,
    "front-end": FRONT_END,
    "desenvolvimento front-end": FRONT_END,
    "desenvolvimento web": FRONT_END + BACK_END,
    "web": FRONT_END + BACK_END,
    "programação": LINGUAGENS,
    "lógica de programação": LINGUAGENS,
    "linguagem de programação": LINGUAGENS,
    "linguagens de programação": LINGUAGENS,
    "desenvolvimento de software": LINGUAGENS,
    "desenvolvimento de sistemas": LINGUAGENS,
    "ETL": FERRAMENTAS_DE_ETL,
    "cloud": NUVENS,
    "computação em nuvem": NUVENS,
    "nuvem": NUVENS,
    "versionamento": VERSIONAMENTO,
    "controle de versão": VERSIONAMENTO,
    "mobile": MOBILE,
    "desenvolvimento mobile": MOBILE,
    "Pacote Office": OFFICE,
    "dados": FERRAMENTAS_DE_DADOS,
    "análise de dados": FERRAMENTAS_DE_DADOS,
    "inteligência artificial": INTELIGENCIA_ARTIFICIAL,
    "IA": INTELIGENCIA_ARTIFICIAL,
    "IA generativa": INTELIGENCIA_ARTIFICIAL,
}
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
SEPARADORES_DE_PALAVRAS = re.compile(r"[\s/,;|]+")
FORA_DE_PARENTESES = r"(?![^(]*\))"
SEPARADORES_DE_PARTES = re.compile(
    r"(?:\s+e\s+|\s*[/,;|]\s*|\s+[&+]\s+)" + FORA_DE_PARENTESES, re.IGNORECASE
)
SEPARADORES_DE_ALTERNATIVAS = re.compile(
    r"(?:\s+e\s*/\s*ou\s+|\s+ou\s+)" + FORA_DE_PARENTESES, re.IGNORECASE
)
PALAVRAS_SEM_SIGNIFICADO = frozenset(
    {
        "a",
        "o",
        "as",
        "os",
        "ao",
        "aos",
        "e",
        "ou",
        "dos",
        "das",
        "nos",
        "nas",
        "para",
        "por",
        "pelo",
        "pela",
        "pelos",
        "pelas",
        "sobre",
        "and",
        "of",
        "the",
        "in",
        "for",
        "with",
        "to",
    }
)


class HabilidadeComparavel(NamedTuple):
    nivel: int
    palavras: frozenset[str]
    alternativas: tuple[tuple[tuple[str, "HabilidadeComparavel"], ...], ...] = ()
    texto: str = ""


def pontuar_vagas(
    vagas: list[Vaga], extracoes: dict[ChaveDaVaga, ExtracaoDaVaga], perfil: Perfil
) -> list[ResultadoMatch]:
    resultados = []
    for vaga in vagas:
        extracao = extracoes.get(vaga.chave())
        if extracao is None:
            continue
        resultados.append(pontuar(vaga, extracao, perfil))
    return resultados


def pontuar(vaga: Vaga, extracao: ExtracaoDaVaga, perfil: Perfil) -> ResultadoMatch:
    vaga = _com_modalidade_extraida(vaga, extracao)
    niveis = derivar_niveis(extracao, perfil)
    requisitos_atendidos, requisitos_nao_atendidos, diferenciais = _classificar_habilidades(
        extracao, perfil
    )
    pontos_a_favor, pontos_contra = montar_pontos(extracao, niveis)
    return ResultadoMatch(
        vaga=vaga,
        nota=_calcular_nota(extracao, niveis, vaga, perfil),
        requisitos_atendidos=requisitos_atendidos,
        requisitos_nao_atendidos=requisitos_nao_atendidos,
        diferenciais_nao_atendidos=diferenciais,
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
    if _nota_sem_habilidades_declaradas(extracao, perfil):
        avisos.append(AVISO_SEM_HABILIDADES_NO_PERFIL)
    return avisos


def _nota_sem_habilidades_declaradas(extracao: ExtracaoDaVaga, perfil: Perfil) -> bool:
    if any(habilidade.strip() for habilidade in perfil.habilidades):
        return False
    return bool(_exigidas_pela_vaga(extracao))


def aviso_de_area_recusada(areas: set[str]) -> str:
    rotulos = ", ".join(ROTULOS_DAS_SUBAREAS[area] for area in sorted(areas))
    return f"{AVISO_AREA_RECUSADA}: {rotulos}"


def _areas_reconhecidas(extracao: ExtracaoDaVaga) -> set[str]:
    return {area.strip().casefold() for area in extracao.areas_da_vaga} & AREAS_RECONHECIDAS


def _compatibilidade_de_habilidades(extracao: ExtracaoDaVaga, perfil: Perfil) -> float:
    habilidades_do_perfil = _habilidades_do_perfil(perfil, extracao)
    computacao = area_do_curso(perfil.curso) == COMPUTACAO
    obrigatorias = _cobertura(extracao.habilidades_obrigatorias, habilidades_do_perfil, computacao)
    principais = _cobertura(extracao.habilidades_principais, habilidades_do_perfil, computacao)
    desejaveis = _cobertura(extracao.habilidades_desejaveis, habilidades_do_perfil, computacao)
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


def _cobertura(
    requisitos: list[str],
    habilidades_do_perfil: Mapping[str, HabilidadeComparavel],
    computacao: bool,
) -> float | None:
    exigencias = _exigencias(requisitos)
    if computacao:
        exigencias = {
            nome: variantes for nome, variantes in exigencias.items() if _conta_para_a_nota(nome)
        }
    if not exigencias:
        return None
    atendidas = [
        nome
        for nome, variantes in exigencias.items()
        if _todas_atendidas(nome, variantes, habilidades_do_perfil)
    ]
    return (SUAVIZACAO_DA_COBERTURA + len(atendidas)) / (SUAVIZACAO_DA_COBERTURA + len(exigencias))


def _exigencias(requisitos: list[str]) -> dict[str, tuple[HabilidadeComparavel, ...]]:
    exigencias: dict[str, tuple[HabilidadeComparavel, ...]] = {}
    for requisito in requisitos:
        if requisito.strip():
            nome = _normalizar_habilidade(requisito)
            exigencias[nome] = (*exigencias.get(nome, ()), _exigencia(requisito))
    return exigencias


def _todas_atendidas(
    nome: str,
    variantes: tuple[HabilidadeComparavel, ...],
    habilidades_do_perfil: Mapping[str, HabilidadeComparavel],
) -> bool:
    return all(_atende(nome, variante, habilidades_do_perfil) for variante in variantes)


@functools.cache
def _exigencia(requisito: str) -> HabilidadeComparavel:
    texto = requisito.strip()
    alternativas = _alternativas(requisito)
    if sum(len(partes) for partes in alternativas) < 2:
        return HabilidadeComparavel(
            nivel_exigido(requisito), _palavras_de_um_nivel(requisito), texto=texto
        )
    com_nivel = tuple(_partes_com_nivel(partes, nivel_exigido) for partes in alternativas)
    niveis = [parte.nivel for alternativa in com_nivel for _, parte in alternativa]
    return HabilidadeComparavel(max(niveis), frozenset(), com_nivel, texto)


def _partes_com_nivel(
    partes: list[str], nivel_citado: Callable[[str], int]
) -> tuple[tuple[str, HabilidadeComparavel], ...]:
    nivel_distribuido = nivel_citado(partes[-1])
    return tuple(
        (
            _normalizar_habilidade(parte),
            HabilidadeComparavel(
                _com_nivel_distribuido(nivel_citado(parte), nivel_distribuido),
                _palavras_de_um_nivel(parte),
            ),
        )
        for parte in partes
    )


def _com_nivel_distribuido(nivel: int, nivel_distribuido: int) -> int:
    return nivel_distribuido if nivel == NIVEL_NAO_INFORMADO else nivel


def _habilidades_do_perfil(
    perfil: Perfil, extracao: ExtracaoDaVaga
) -> Mapping[str, HabilidadeComparavel]:
    compara_palavras = COMPUTACAO not in (area_do_curso(perfil.curso), extracao.area_da_vaga)
    return _habilidades_declaradas(tuple(perfil.habilidades), compara_palavras)


@functools.cache
def _habilidades_declaradas(
    habilidades: tuple[str, ...], compara_palavras: bool
) -> Mapping[str, HabilidadeComparavel]:
    declaradas: dict[str, HabilidadeComparavel] = {}
    for habilidade in (habilidade for habilidade in habilidades if habilidade.strip()):
        alternativas = _alternativas(habilidade)
        if sum(len(partes) for partes in alternativas) < 2:
            palavras = _palavras_de_um_nivel(habilidade) if compara_palavras else frozenset()
            declarada = HabilidadeComparavel(nivel_declarado(habilidade), palavras)
            _declarar(declaradas, _normalizar_habilidade(habilidade), declarada)
            continue
        com_nivel = [
            (nome, parte)
            for partes in alternativas
            for nome, parte in _partes_com_nivel(partes, nivel_declarado)
        ]
        inteira = HabilidadeComparavel(min(parte.nivel for _, parte in com_nivel), frozenset())
        _declarar(declaradas, _normalizar_habilidade(habilidade), inteira)
        for nome, parte in com_nivel:
            palavras = parte.palavras if compara_palavras else frozenset()
            _declarar(declaradas, nome, parte._replace(palavras=palavras))
    return MappingProxyType(declaradas)


def _declarar(
    declaradas: dict[str, HabilidadeComparavel], nome: str, declarada: HabilidadeComparavel
) -> None:
    anterior = declaradas.get(nome)
    if anterior is None or declarada.nivel > anterior.nivel:
        declaradas[nome] = declarada


def _atende(
    nome: str,
    exigencia: HabilidadeComparavel,
    habilidades_do_perfil: Mapping[str, HabilidadeComparavel],
) -> bool:
    if _satisfeita(nome, exigencia, habilidades_do_perfil):
        return True
    return any(
        all(
            _satisfeita(nome_da_parte, parte, habilidades_do_perfil)
            for nome_da_parte, parte in alternativa
        )
        for alternativa in exigencia.alternativas
    )


def _satisfeita(
    nome: str,
    exigencia: HabilidadeComparavel,
    habilidades_do_perfil: Mapping[str, HabilidadeComparavel],
) -> bool:
    nivel_do_perfil = _nivel_no_perfil(nome, exigencia.palavras, habilidades_do_perfil)
    if nivel_do_perfil is None:
        return False
    return exigencia.nivel == NIVEL_NAO_INFORMADO or nivel_do_perfil >= exigencia.nivel


def _nivel_no_perfil(
    nome: str, palavras: frozenset[str], habilidades_do_perfil: Mapping[str, HabilidadeComparavel]
) -> int | None:
    familia = _membros_das_familias().get(nome)
    niveis = [habilidades_do_perfil[nome].nivel] if nome in habilidades_do_perfil else []
    niveis += [
        habilidades_do_perfil[membro].nivel
        for membro in familia or ()
        if membro in habilidades_do_perfil
    ]
    if familia is None:
        niveis += [
            habilidade.nivel
            for habilidade in habilidades_do_perfil.values()
            if _correspondem_por_palavras(palavras, habilidade.palavras)
        ]
    return max(niveis, default=None)


def _correspondem_por_palavras(requisito: frozenset[str], habilidade: frozenset[str]) -> bool:
    if not requisito or not habilidade:
        return False
    return _todas_presentes(requisito, habilidade) or _todas_presentes(habilidade, requisito)


def _todas_presentes(procuradas: frozenset[str], texto: frozenset[str]) -> bool:
    formas_do_texto = {forma for palavra in texto for forma in _formas_da_palavra(palavra)}
    return all(_formas_da_palavra(palavra) & formas_do_texto for palavra in procuradas)


@functools.cache
def _formas_da_palavra(palavra: str) -> frozenset[str]:
    formas = {palavra}
    if palavra.endswith("oes"):
        formas.add(palavra[:-3] + "ao")
    if len(palavra) > 4 and palavra.endswith("ais"):
        formas.add(palavra[:-3] + "al")
    if len(palavra) > 4 and palavra.endswith("eis"):
        formas.update({palavra[:-3] + "el", palavra[:-3] + "il"})
    if len(palavra) > 4 and palavra.endswith("is") and not palavra.endswith(("ais", "eis")):
        formas.add(palavra[:-1] + "l")
    if palavra.endswith("ns"):
        formas.add(palavra[:-2] + "m")
    if palavra.endswith(("res", "zes")):
        formas.add(palavra[:-2])
    if len(palavra) > 3 and palavra.endswith("s") and not palavra.endswith("ss"):
        formas.add(palavra[:-1])
    return frozenset(formas)


@functools.cache
def _membros_das_familias() -> dict[str, frozenset[str]]:
    return {
        _normalizar_habilidade(nome): frozenset(_normalizar_habilidade(m) for m in membros)
        for nome, membros in FAMILIAS_DE_HABILIDADES.items()
    }


def _primeira_nao_atendida(
    nome: str,
    variantes: tuple[HabilidadeComparavel, ...],
    habilidades_do_perfil: Mapping[str, HabilidadeComparavel],
) -> str:
    return next(
        variante.texto
        for variante in variantes
        if not _atende(nome, variante, habilidades_do_perfil)
    )


def nivel_exigido(habilidade: str) -> int:
    return min(_niveis_citados(habilidade), default=NIVEL_NAO_INFORMADO)


def nivel_declarado(habilidade: str) -> int:
    return max(_niveis_citados(habilidade), default=NIVEL_NAO_INFORMADO)


def _niveis_citados(habilidade: str) -> set[int]:
    texto = _normalizar_texto(habilidade)
    return {nivel for padrao, nivel in PADROES_DE_NIVEL if padrao.search(texto)}


def _conta_para_a_nota(requisito_normalizado: str) -> bool:
    if requisito_normalizado in REQUISITOS_FORA_DO_PERFIL_TECNICO | SOFT_SKILLS:
        return False
    return not requisito_normalizado.startswith(PREFIXOS_DE_IDIOMA)


def _classificar_habilidades(
    extracao: ExtracaoDaVaga, perfil: Perfil
) -> tuple[list[str], list[str], list[str]]:
    habilidades_do_perfil = _habilidades_do_perfil(perfil, extracao)
    exigidas = _exigencias(extracao.habilidades_obrigatorias + extracao.habilidades_principais)
    desejaveis = _exigencias(extracao.habilidades_desejaveis)
    variantes_por_nome = {**desejaveis, **exigidas}
    requisitos_atendidos = [
        variantes_por_nome[nome][0].texto
        for nome in {**exigidas, **desejaveis}
        if _todas_atendidas(nome, variantes_por_nome[nome], habilidades_do_perfil)
    ]
    requisitos_nao_atendidos = [
        _primeira_nao_atendida(nome, variantes, habilidades_do_perfil)
        for nome, variantes in exigidas.items()
        if not _todas_atendidas(nome, variantes, habilidades_do_perfil)
    ]
    diferenciais_nao_atendidos = [
        _primeira_nao_atendida(nome, variantes, habilidades_do_perfil)
        for nome, variantes in desejaveis.items()
        if nome not in exigidas and not _todas_atendidas(nome, variantes, habilidades_do_perfil)
    ]
    return requisitos_atendidos, requisitos_nao_atendidos, diferenciais_nao_atendidos


def _exigidas_pela_vaga(extracao: ExtracaoDaVaga) -> list[str]:
    unicas: dict[str, str] = {}
    for habilidade in extracao.habilidades_obrigatorias + extracao.habilidades_principais:
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
    compacta = _compactar(_sem_qualificadores(habilidade))
    return ALIASES_DE_HABILIDADES.get(compacta, compacta)


def _alternativas(habilidade: str) -> list[list[str]]:
    divididas = (
        _juntar_niveis_soltos(
            [parte.strip() for parte in SEPARADORES_DE_PARTES.split(alternativa) if parte.strip()]
        )
        for alternativa in SEPARADORES_DE_ALTERNATIVAS.split(habilidade)
    )
    return [partes for partes in divididas if partes]


def _juntar_niveis_soltos(partes: list[str]) -> list[str]:
    juntas: list[str] = []
    for parte in partes:
        if juntas and not _normalizar_habilidade(parte):
            juntas[-1] = f"{juntas[-1]} {parte}"
        else:
            juntas.append(parte)
    return juntas


def _palavras_de_um_nivel(habilidade: str) -> frozenset[str]:
    if len(_niveis_citados(habilidade)) > 1:
        return frozenset()
    return _palavras(habilidade)


@functools.cache
def _palavras(habilidade: str) -> frozenset[str]:
    palavras = set()
    for palavra in SEPARADORES_DE_PALAVRAS.split(_sem_qualificadores(habilidade)):
        compacta = _compactar(palavra)
        if compacta and compacta not in PALAVRAS_SEM_SIGNIFICADO:
            palavras.add(compacta)
    return frozenset(palavras)


def _sem_qualificadores(habilidade: str) -> str:
    sem_complemento = COMPLEMENTO_ENTRE_PARENTESES.sub(" ", _normalizar_texto(habilidade))
    return QUALIFICADORES_DE_HABILIDADE.sub(" ", sem_complemento)


def _compactar(texto: str) -> str:
    return "".join(caractere for caractere in texto if caractere.isalnum() or caractere in "#+")


def _coeficiente(nivel: NivelCompatibilidade) -> float:
    return COEFICIENTES[nivel.value]


def _compatibilidade_logistica(vaga: Vaga, perfil: Perfil) -> float:
    localizacao = _compatibilidade_de_localizacao(vaga, perfil)
    modalidade = _compatibilidade_de_modalidade(vaga, perfil)
    return (localizacao + modalidade) / 2


def _compatibilidade_de_localizacao(vaga: Vaga, perfil: Perfil) -> float:
    if vaga.modalidade is Modalidade.REMOTO or perfil.modalidade is Modalidade.REMOTO:
        return 1.0
    return LOCALIZACAO_POR_PROXIMIDADE[proximidade(vaga.localizacao, perfil.cidade)]


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
