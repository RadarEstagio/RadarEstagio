from radar.domain.models import Modalidade, Perfil, ResultadoMatch
from radar.domain.regioes import Proximidade, proximidade

LIMITE_MODALIDADE_INCOMPATIVEL = 30
AVISO_MODALIDADE_INCOMPATIVEL = "Nota limitada a 30: modalidade incompatível"
AVISO_PRESENCA_EM_OUTRA_CIDADE = "Nota limitada a 30: exige presença em outra cidade"
MODALIDADES_COM_PRESENCA = {Modalidade.PRESENCIAL, Modalidade.HIBRIDO}
LIMITE_DESCRICAO_INCOMPLETA = 60
AVISO_DESCRICAO_INCOMPLETA = (
    "Descrição incompleta: requisitos podem estar ausentes; nota limitada a 60"
)
TERMOS_DE_MODALIDADE = (
    "modalidade",
    "presencial",
    "híbrido",
    "hibrido",
    "híbrida",
    "hibrida",
    "remoto",
    "remota",
)


def aplicar_regras_objetivas(
    resultados: list[ResultadoMatch], perfil: Perfil
) -> list[ResultadoMatch]:
    return [aplicar_regras_ao_resultado(resultado, perfil) for resultado in resultados]


def aplicar_regras_ao_resultado(resultado: ResultadoMatch, perfil: Perfil) -> ResultadoMatch:
    limite, aviso = limite_de_modalidade(resultado, perfil)
    nota = min(resultado.nota, limite)
    avisos = list(resultado.avisos_objetivos)
    if nota < resultado.nota and aviso not in avisos:
        avisos.append(aviso)
    if not resultado.vaga.descricao_completa:
        nota = min(nota, LIMITE_DESCRICAO_INCOMPLETA)
        if AVISO_DESCRICAO_INCOMPLETA not in avisos:
            avisos.append(AVISO_DESCRICAO_INCOMPLETA)
    pontos_contra = [ponto for ponto in resultado.pontos_contra if not descreve_modalidade(ponto)]
    return resultado.model_copy(
        update={
            "nota": nota,
            "pontos_contra": pontos_contra,
            "avisos_objetivos": avisos,
        }
    )


def limite_de_modalidade(resultado: ResultadoMatch, perfil: Perfil) -> tuple[int, str]:
    modalidade = resultado.vaga.modalidade
    if modalidade not in MODALIDADES_COM_PRESENCA:
        return 100, ""
    if perfil.modalidade is Modalidade.REMOTO:
        return LIMITE_MODALIDADE_INCOMPATIVEL, AVISO_MODALIDADE_INCOMPATIVEL
    if perfil.modalidade is not Modalidade.PRESENCIAL and fora_da_regiao(resultado, perfil):
        return LIMITE_MODALIDADE_INCOMPATIVEL, AVISO_PRESENCA_EM_OUTRA_CIDADE
    return 100, ""


def fora_da_regiao(resultado: ResultadoMatch, perfil: Perfil) -> bool:
    return proximidade(resultado.vaga.localizacao, perfil.cidade) is Proximidade.DISTANTE


def descreve_modalidade(ponto: str) -> bool:
    normalizado = ponto.casefold()
    return any(termo in normalizado for termo in TERMOS_DE_MODALIDADE)
