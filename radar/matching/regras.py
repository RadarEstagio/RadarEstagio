from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Vaga
from radar.domain.publico import PublicoDaVaga, grupos_da_vaga_afirmativa, publico_da_vaga
from radar.domain.regioes import Proximidade, proximidade

LIMITE_MODALIDADE_INCOMPATIVEL = 30
AVISO_MODALIDADE_INCOMPATIVEL = "Nota limitada a 30: modalidade incompatível"
AVISO_PRESENCA_EM_OUTRA_CIDADE = "Nota limitada a 30: exige presença em outra cidade"
MODALIDADES_COM_PRESENCA = {Modalidade.PRESENCIAL, Modalidade.HIBRIDO}
LIMITE_DESCRICAO_INCOMPLETA = 60
AVISO_DESCRICAO_INCOMPLETA = (
    "Descrição incompleta: requisitos podem estar ausentes; nota limitada a 60"
)
PONTO_DO_PUBLICO_PCD = {
    PublicoDaVaga.EXCLUSIVO_PCD: "Vaga exclusiva para PCD",
    PublicoDaVaga.AFIRMATIVO_COM_PCD: "Vaga afirmativa que inclui PCD",
}
AVISO_EXCLUSIVA_PARA_PCD = "Vaga exclusiva para pessoas com deficiência (PCD)"
AVISO_AFIRMATIVA_SEM_GRUPOS = "Vaga afirmativa: confira no anúncio a quem ela se destina"
AVISO_AFIRMATIVA_COM_GRUPOS = "Vaga afirmativa: confira se você faz parte de um destes grupos: {}"
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
    pontos_a_favor = list(resultado.pontos_a_favor)
    publico = publico_da_vaga(resultado.vaga)
    prioritaria = perfil.pessoa_com_deficiencia is True and publico in PONTO_DO_PUBLICO_PCD
    if prioritaria and PONTO_DO_PUBLICO_PCD[publico] not in pontos_a_favor:
        pontos_a_favor.insert(0, PONTO_DO_PUBLICO_PCD[publico])
    aviso_do_publico = None if prioritaria else aviso_sobre_o_publico(resultado.vaga, publico)
    if aviso_do_publico and aviso_do_publico not in avisos:
        avisos.append(aviso_do_publico)
    nota_antes_dos_limites = resultado.nota_antes_dos_limites_objetivos
    if nota_antes_dos_limites is None:
        nota_antes_dos_limites = resultado.nota
    return resultado.model_copy(
        update={
            "nota": nota,
            "nota_antes_dos_limites_objetivos": nota_antes_dos_limites,
            "pontos_a_favor": pontos_a_favor,
            "pontos_contra": pontos_contra,
            "avisos_objetivos": avisos,
            "prioritaria_para_pcd": prioritaria,
        }
    )


def aviso_sobre_o_publico(vaga: Vaga, publico: PublicoDaVaga) -> str | None:
    if publico is PublicoDaVaga.GERAL:
        return None
    if publico is PublicoDaVaga.EXCLUSIVO_PCD:
        return AVISO_EXCLUSIVA_PARA_PCD
    grupos = grupos_da_vaga_afirmativa(vaga)
    if grupos is None:
        return AVISO_AFIRMATIVA_SEM_GRUPOS
    return AVISO_AFIRMATIVA_COM_GRUPOS.format(grupos)


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
