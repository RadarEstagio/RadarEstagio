import unicodedata
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from radar.domain.areas import AREAS_POR_NOME, SUBAREAS, normalizar


class Modalidade(StrEnum):
    REMOTO = "remoto"
    PRESENCIAL = "presencial"
    HIBRIDO = "hibrido"
    INDIFERENTE = "indiferente"


AreaDeInteresse = StrEnum("AreaDeInteresse", {valor.upper(): valor for valor in SUBAREAS})


class NivelCompatibilidade(StrEnum):
    COMPATIVEL = "compativel"
    PARCIAL = "parcial"
    INCOMPATIVEL = "incompativel"


class Vaga(BaseModel):
    id_externo: str
    fonte: str
    titulo: str
    empresa: str
    localizacao: str
    descricao: str
    url: str
    publicada_em: datetime
    modalidade: Modalidade | None = None
    descricao_completa: bool = True


class ExtracaoDaVaga(BaseModel):
    id_vaga: str
    area_da_vaga: str | None
    areas_da_vaga: list[str] = Field(default_factory=list)
    cursos_aceitos: list[str] = Field(default_factory=list)
    aceita_qualquer_curso: bool = False
    periodo_minimo: int | None = None
    experiencia_minima_anos: int | None = None
    experiencia_desejavel: bool = False
    habilidades_obrigatorias: list[str] = Field(default_factory=list)
    habilidades_principais: list[str] = Field(default_factory=list)
    habilidades_desejaveis: list[str] = Field(default_factory=list)
    modalidade: str | None = None
    alerta_pegadinha: str | None = None

    @field_validator("area_da_vaga", mode="before")
    @classmethod
    def reconhecer_area(cls, valor: object) -> str | None:
        if not isinstance(valor, str):
            return None
        area = normalizar(valor)
        return area if area in AREAS_POR_NOME else None

    def modalidade_reconhecida(self) -> Modalidade | None:
        if not self.modalidade:
            return None
        sem_acentos = (
            unicodedata.normalize("NFKD", self.modalidade).encode("ascii", "ignore").decode("ascii")
        )
        try:
            return Modalidade(sem_acentos.strip().casefold())
        except ValueError:
            return None


class Perfil(BaseModel):
    curso: str
    periodo: int = Field(ge=1)
    habilidades: list[str]
    cidade: str
    modalidade: Modalidade
    areas_de_interesse: list[AreaDeInteresse] = Field(default_factory=list)
    areas_recusadas: list[AreaDeInteresse] = Field(default_factory=list)

    def nome_da_cidade(self) -> str:
        return self.cidade.split(",")[0].strip()


class MotivoDeRecusa(StrEnum):
    NOTA = "motivo_nota"
    AREA = "motivo_area"
    EXIGENCIA = "motivo_exigencia"
    LOGISTICA = "motivo_logistica"
    REPETIDA = "motivo_repetida"


class BotaoDeFeedback(BaseModel):
    rotulo: str = Field(min_length=1)
    dados: str = Field(min_length=1, max_length=64)


class PerguntaDeFeedback(BaseModel):
    texto: str = Field(min_length=1)
    linhas_de_botoes: list[list[BotaoDeFeedback]] = Field(min_length=1)


class Usuario(BaseModel):
    id: UUID
    perfil: Perfil
    chat_id: str = Field(min_length=1)
    sem_recomendacao_desde: datetime | None = None
    silencio_avisado_em: datetime | None = None


class ResultadoMatch(BaseModel):
    vaga: Vaga
    nota: int = Field(ge=0, le=100)
    requisitos_atendidos: list[str] = Field(default_factory=list)
    requisitos_nao_atendidos: list[str] = Field(default_factory=list)
    requisitos_tecnicos_analisados: bool = False
    pontos_a_favor: list[str] = Field(default_factory=list)
    pontos_contra: list[str] = Field(default_factory=list)
    avisos_objetivos: list[str] = Field(default_factory=list)
    alerta_pegadinha: str | None = None


class RecusasDoUsuario(BaseModel):
    areas: list[AreaDeInteresse] = Field(default_factory=list)
    vagas_repetidas: list[Vaga] = Field(default_factory=list)


class Recomendacao(BaseModel):
    resultado: ResultadoMatch
    token: UUID = Field(default_factory=uuid4)


class UtilidadeSemanal(BaseModel):
    semana: str
    parcial: bool
    ativados: int
    com_utilidade: int

    def percentual(self) -> float | None:
        return 100 * self.com_utilidade / self.ativados if self.ativados else None


class UtilidadePorArea(BaseModel):
    semana: str
    parcial: bool
    area: str
    ativados: int
    com_utilidade: int

    def percentual(self) -> float | None:
        if not self.ativados:
            return None
        return 100 * self.com_utilidade / self.ativados


class FatoUtilidadeSemanal(BaseModel):
    semana: str
    parcial: bool
    perfil_id: str
    curso: str
    com_utilidade: bool


class PausaAtual(BaseModel):
    motivo: str
    total: int


class RecusasPorGrupo(BaseModel):
    grupo: str
    entregas: int
    recusas: int
    recusas_da_nota: int


class FunilDaCoorte(BaseModel):
    etapas: dict[str, int] = Field(default_factory=dict)
    utilidade_semanal: list[UtilidadeSemanal] = Field(default_factory=list)
    utilidade_por_area: list[UtilidadePorArea] = Field(default_factory=list)
    pausas_atuais: list[PausaAtual] = Field(default_factory=list)
    recusas_por_grupo: list[RecusasPorGrupo] = Field(default_factory=list)
    dias: int = Field(ge=1)
    perfis_criados: int
    perfis_vinculados: int
    perfis_ativados: int
    perfis_com_vaga_aberta: int
    perfis_com_vaga_util: int
    perfis_com_candidatura: int
    vagas_enviadas: int
    vagas_abertas: int
    vagas_uteis: int
    vagas_irrelevantes: int
    candidaturas: int
    vagas_extraidas: int
    recomendacoes_elegiveis_feedback: int = 0
    recomendacoes_com_feedback: int = 0
    perfis_na_coorte: int = 0
    perfis_sem_entrega: int = 0
    mediana_segundos_ate_entrega: float | None = None
    perfis_sem_abertura: int = 0
    mediana_segundos_ate_abertura: float | None = None
    recusas_por_motivo: dict[str, int] = Field(default_factory=dict)

    def vagas_extraidas_por_ativado(self) -> float | None:
        if not self.perfis_ativados:
            return None
        return self.vagas_extraidas / self.perfis_ativados
