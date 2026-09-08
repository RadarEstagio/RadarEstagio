import re
import unicodedata
from dataclasses import dataclass

COMPUTACAO = "computacao"


@dataclass(frozen=True)
class Area:
    nome: str
    cursos: tuple[str, ...]
    titulo: str
    exclusao: str
    descricao: str
    termos_de_busca: tuple[str, ...]
    subareas: tuple[tuple[str, str], ...]


AREAS = (
    Area(
        nome=COMPUTACAO,
        cursos=(
            "computacao",
            "engenharia de software",
            "sistemas de informacao",
            "analise e desenvolvimento de sistemas",
            "analise de sistemas",
            "desenvolvimento de sistemas",
            "sistemas para internet",
            "ciencia de dados",
            "engenharia de dados",
            "banco de dados",
            "tecnologia da informacao",
            "informatica",
            "redes de computadores",
            "seguranca da informacao",
            "jogos digitais",
            "inteligencia artificial",
        ),
        titulo=(
            r"ti|t\.i\.?|tech|tecnologia|software|desenvolvimento|desenvolvedor[a]?|dev"
            r"|developer|programacao|programador[a]?|dados|data|sistemas?|computacao|informatica"
            r"|infra(?:estrutura)?|redes|seguranca da informacao|cyber\w*|cloud|devops"
            r"|machine learning|inteligencia artificial|ia|front-?end|back-?end|full-?stack"
            r"|qa|testes?|suporte|help-? ?desk|banco de dados|sql|python|java(?:script)?|web"
            r"|mobile|analytics|bi|business intelligence|produto|ux|ui|automacao|rpa|digital"
            r"|inovacao|engenharia de software|ciencia da computacao|sistemas de informacao"
            r"|ciencia de dados|analise de sistemas"
        ),
        exclusao=(
            r"ti|t\.i\.?|desenvolvedor[a]?|developer|programacao|programador[a]?"
            r"|engenharia de software|ciencia da computacao|sistemas de informacao"
            r"|analise de sistemas|desenvolvimento de (?:software|sistemas|aplicacoes)"
            r"|software|android|ios|front-?end|back-?end|full-?stack|devops|cyber\w*"
            r"|banco de dados|seguranca da informacao|help-? ?desk"
        ),
        descricao=(
            r"tecnologia da informacao|ciencia da computacao|engenharia de software"
            r"|engenharia da computacao|sistemas de informacao"
            r"|analise e desenvolvimento de sistemas"
            r"|ciencia de dados|analise de dados|engenharia de dados|banco de dados"
            r"|desenvolvimento de (?:software|sistemas|aplicacoes|aplicativos|web)|programacao"
            r"|programador[a]?|desenvolvedor[a]?|linguagem de programacao|python|java(?:script)?"
            r"|sql|suporte tecnico|help-? ?desk|infraestrutura de ti|redes de computadores"
            r"|seguranca da informacao|machine learning|inteligencia artificial|power bi|devops"
            r"|cloud|front-?end|back-?end|full-?stack"
        ),
        termos_de_busca=(
            "desenvolvimento",
            "software",
            "TI",
            "dados",
            "sistemas",
            "programação",
            "computação",
            "informática",
            "tecnologia",
        ),
        subareas=(
            ("desenvolvimento_web", "Desenvolvimento web"),
            ("desenvolvimento_mobile", "Desenvolvimento mobile"),
            ("dados_ia", "Dados e IA"),
            ("infraestrutura_redes", "Infraestrutura e redes"),
            ("seguranca", "Segurança"),
            ("suporte_tecnico", "Suporte técnico"),
            ("qa_testes", "QA e testes"),
        ),
    ),
    Area(
        nome="direito",
        cursos=("direito",),
        titulo=r"juridic[ao]|direito|advocacia|contencioso|societario|compliance",
        exclusao=r"juridic[ao]|direito|compliance",
        descricao=r"direito|juridic[ao]|advocacia|contencioso|peticao|escritorio de advocacia",
        termos_de_busca=("direito", "jurídico", "advocacia"),
        subareas=(
            ("direito_contencioso", "Contencioso"),
            ("direito_societario", "Societário e contratos"),
            ("direito_trabalhista", "Trabalhista"),
            ("compliance", "Compliance"),
        ),
    ),
    Area(
        nome="administracao",
        cursos=("administracao", "gestao", "processos gerenciais", "secretariado"),
        titulo=(
            r"administrativ[ao]|administracao|backoffice|back-?office"
            r"|processos administrativos|gestao|planejamento|pmo"
        ),
        exclusao=r"backoffice|back-?office|processos administrativos",
        descricao=r"administracao|rotinas administrativas|processos administrativos",
        termos_de_busca=("administração", "administrativo", "gestão"),
        subareas=(
            ("rotinas_administrativas", "Rotinas administrativas"),
            ("gestao_de_projetos", "Gestão de projetos"),
            ("processos_e_qualidade", "Processos e qualidade"),
        ),
    ),
    Area(
        nome="financas",
        cursos=("economia", "ciencias contabeis", "contabilidade", "atuaria", "financas"),
        titulo=(
            r"financeir[ao]|financas|contabil|contabilidade|fiscal|controladoria|tesouraria"
            r"|atuari\w*|auditoria|economi\w*|credito|cobranca|faturamento"
        ),
        exclusao=r"financeir[ao]|contabil|contabilidade|atuari\w*|auditoria",
        descricao=(
            r"financeir[ao]|contabil|contabilidade|fiscal|controladoria|tesouraria|auditoria"
            r"|economia|conciliacao bancaria|contas a pagar|contas a receber"
        ),
        termos_de_busca=("financeiro", "contábil", "economia", "controladoria"),
        subareas=(
            ("financeiro", "Financeiro"),
            ("contabil_fiscal", "Contábil e fiscal"),
            ("controladoria_auditoria", "Controladoria e auditoria"),
            ("mercado_financeiro", "Mercado financeiro"),
        ),
    ),
    Area(
        nome="marketing",
        cursos=("marketing", "publicidade", "propaganda", "jornalismo", "comunicacao", "design"),
        titulo=(
            r"marketing|endomarketing|comunicacao|imprensa|midias sociais|redes sociais"
            r"|publicidade|propaganda|conteudo|branding|crm|inteligencia de mercado"
        ),
        exclusao=(r"marketing|endomarketing|comunicacao|imprensa|crm|inteligencia de mercado"),
        descricao=(
            r"marketing|comunicacao|midias sociais|redes sociais|publicidade|propaganda"
            r"|producao de conteudo|branding|assessoria de imprensa"
        ),
        termos_de_busca=("marketing", "comunicação", "publicidade"),
        subareas=(
            ("marketing_digital", "Marketing digital"),
            ("conteudo_e_redes", "Conteúdo e redes sociais"),
            ("comunicacao_institucional", "Comunicação institucional"),
            ("design_grafico", "Design gráfico"),
        ),
    ),
    Area(
        nome="pessoas",
        cursos=("psicologia", "recursos humanos", "gestao de pessoas"),
        titulo=(
            r"recursos humanos|rh|recrutamento e selecao|r&s|people|departamento pessoal"
            r"|treinamento e desenvolvimento|psicologia"
        ),
        exclusao=(
            r"recursos humanos|rh|recrutamento e selecao|r&s|people|psicologia"
            r"|treinamento e desenvolvimento"
        ),
        descricao=(
            r"recursos humanos|recrutamento e selecao|departamento pessoal|gestao de pessoas"
            r"|treinamento e desenvolvimento|psicologia"
        ),
        termos_de_busca=("recursos humanos", "recrutamento", "psicologia"),
        subareas=(
            ("recrutamento_e_selecao", "Recrutamento e seleção"),
            ("departamento_pessoal", "Departamento pessoal"),
            ("treinamento_e_desenvolvimento", "Treinamento e desenvolvimento"),
        ),
    ),
    Area(
        nome="comercial",
        cursos=("comercio exterior", "relacoes internacionais", "negocios"),
        titulo=(
            r"comercial|vendas|pre-?vendas?|inside sales|trade|comercio exterior|exportacao"
            r"|importacao|relacionamento com o cliente"
        ),
        exclusao=r"comercial|vendas|pre-?vendas?|comercio exterior",
        descricao=r"comercial|vendas|prospeccao|comercio exterior|atendimento ao cliente",
        termos_de_busca=("comercial", "vendas", "comércio exterior"),
        subareas=(
            ("vendas", "Vendas"),
            ("atendimento_ao_cliente", "Atendimento ao cliente"),
            ("comercio_exterior", "Comércio exterior"),
        ),
    ),
    Area(
        nome="logistica",
        cursos=("logistica", "transportes"),
        titulo=r"logistic[ao]|suprimentos|supply|compras|estoque|almoxarifado",
        exclusao=r"logistic[ao]",
        descricao=r"logistica|suprimentos|supply chain|compras|controle de estoque|almoxarifado",
        termos_de_busca=("logística", "suprimentos", "compras"),
        subareas=(
            ("suprimentos_e_compras", "Suprimentos e compras"),
            ("estoque_e_armazem", "Estoque e armazém"),
            ("transporte_e_distribuicao", "Transporte e distribuição"),
        ),
    ),
    Area(
        nome="engenharias",
        cursos=(
            "engenharia civil",
            "engenharia mecanica",
            "engenharia eletrica",
            "engenharia quimica",
            "engenharia ambiental",
            "engenharia de producao",
            "arquitetura",
        ),
        titulo=(
            r"eletronic[ao]|eletrotecnic[ao]|eletric[ao]|mecanic[ao]|mecatronic[ao]|civil"
            r"|quimic[ao]|ambiental|manufatura|producao|manutencao|obras"
            r"|arquitetura e urbanismo|design de interiores|embalagens|seguranca do trabalho"
        ),
        exclusao=(
            r"eletronic[ao]|eletrotecnic[ao]|mecanic[ao]|civil|quimic[ao]|ambiental|manufatura"
            r"|producao|arquitetura e urbanismo|design de interiores|embalagens"
        ),
        descricao=(
            r"engenharia (?:civil|mecanica|eletrica|quimica|ambiental|de producao)|manufatura"
            r"|autocad|obras|manutencao industrial|seguranca do trabalho"
        ),
        termos_de_busca=("engenharia", "produção", "manutenção"),
        subareas=(
            ("engenharia_civil", "Engenharia civil"),
            ("engenharia_mecanica", "Engenharia mecânica"),
            ("engenharia_eletrica", "Engenharia elétrica"),
            ("engenharia_de_producao", "Engenharia de produção"),
            ("meio_ambiente_e_seguranca", "Meio ambiente e segurança"),
        ),
    ),
    Area(
        nome="saude",
        cursos=(
            "medicina",
            "enfermagem",
            "fisioterapia",
            "nutricao",
            "farmacia",
            "biomedicina",
            "odontologia",
            "educacao fisica",
            "biologia",
        ),
        titulo=(
            r"fisioterapia|enfermagem|nutricao|farmacia|biomedicina|odontologia|laboratorio"
            r"|clinic[ao]|hospitalar"
        ),
        exclusao=r"fisioterapia|enfermagem|nutricao|farmacia|laboratorio",
        descricao=r"enfermagem|fisioterapia|nutricao|farmacia|laboratorio|area da saude|clinica",
        termos_de_busca=("saúde", "enfermagem", "laboratório"),
        subareas=(
            ("assistencia_a_saude", "Assistência à saúde"),
            ("laboratorio_e_pesquisa", "Laboratório e pesquisa"),
            ("saude_publica", "Saúde pública"),
        ),
    ),
    Area(
        nome="educacao",
        cursos=("pedagogia", "letras", "historia", "geografia", "licenciatura"),
        titulo=r"pedagogia|docencia|professor[a]?|monitoria|educacional",
        exclusao=r"pedagogia",
        descricao=r"pedagogia|docencia|acompanhamento pedagogico|material didatico",
        termos_de_busca=("pedagogia", "educação", "ensino"),
        subareas=(
            ("docencia_e_monitoria", "Docência e monitoria"),
            ("coordenacao_pedagogica", "Coordenação pedagógica"),
            ("producao_de_material", "Produção de material didático"),
        ),
    ),
    Area(
        nome="turismo",
        cursos=("turismo", "hotelaria", "gastronomia", "eventos"),
        titulo=r"turismo|hotelaria|gastronomia|eventos|hospitalidade",
        exclusao=r"turismo|hotelaria|gastronomia",
        descricao=r"turismo|hotelaria|gastronomia|organizacao de eventos",
        termos_de_busca=("turismo", "hotelaria", "eventos"),
        subareas=(
            ("eventos", "Eventos"),
            ("hotelaria", "Hotelaria"),
            ("gastronomia", "Gastronomia"),
        ),
    ),
)

AREAS_POR_NOME = {area.nome: area for area in AREAS}
SUBAREAS = tuple(valor for area in AREAS for valor, _ in area.subareas)
ROTULOS_DAS_SUBAREAS = {valor: rotulo for area in AREAS for valor, rotulo in area.subareas}
PADROES_DE_TITULO = {area.nome: re.compile(rf"\b(?:{area.titulo})\b") for area in AREAS}
PADROES_DE_EXCLUSAO = {area.nome: re.compile(rf"\b(?:{area.exclusao})\b") for area in AREAS}
PADROES_DE_DESCRICAO = {area.nome: re.compile(rf"\b(?:{area.descricao})\b") for area in AREAS}


def normalizar(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acentos.casefold().split())


def area_do_curso(curso: str) -> str | None:
    normalizado = normalizar(curso)
    if not normalizado:
        return None
    candidatas = [
        (len(nome), area.nome) for area in AREAS for nome in area.cursos if nome in normalizado
    ]
    if not candidatas:
        return None
    return max(candidatas)[1]


def titulo_e_da_area(titulo: str, area: str | None) -> bool:
    padrao = PADROES_DE_TITULO.get(area or "")
    return padrao is not None and padrao.search(titulo) is not None


def descricao_e_da_area(descricao: str, area: str | None) -> bool:
    padrao = PADROES_DE_DESCRICAO.get(area or "")
    return padrao is not None and padrao.search(descricao) is not None


def titulo_e_de_outra_area(titulo: str, area: str | None) -> bool:
    return any(
        nome != area and padrao.search(titulo) is not None
        for nome, padrao in PADROES_DE_EXCLUSAO.items()
    )


def termos_de_busca(areas: set[str]) -> tuple[str, ...]:
    escolhidas = [area for area in AREAS if area.nome in areas]
    return tuple(termo for area in escolhidas for termo in area.termos_de_busca)


def subareas_do_curso(curso: str) -> tuple[tuple[str, str], ...]:
    area = area_do_curso(curso)
    return AREAS_POR_NOME[area].subareas if area else ()
