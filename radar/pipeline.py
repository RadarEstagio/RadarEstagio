import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field

from radar.domain.models import (
    ChaveDaVaga,
    ExtracaoDaVaga,
    Perfil,
    Recomendacao,
    RecusasDoUsuario,
    ResultadoMatch,
    Usuario,
    Vaga,
)
from radar.domain.ports import ColetorDeVagas, ExtratorDeVagas, Notificador, Repositorio
from radar.filtering.duplicatas import remover_duplicatas, remover_republicacoes_de
from radar.filtering.prefiltro import filtrar
from radar.matching.avaliacoes import pontuar_vagas
from radar.matching.regras import aplicar_regras_objetivas
from radar.notification.formatador import (
    formatar_mensagem,
    formatar_mensagem_sem_vagas,
    formatar_pergunta_de_feedback,
)
from radar.notification.telegram import ErroDeNotificacao
from radar.storage.errors import ErroDeArmazenamento

logger = logging.getLogger(__name__)

Pontuador = Callable[[list[Vaga], dict[ChaveDaVaga, ExtracaoDaVaga], Perfil], list[ResultadoMatch]]
Enriquecedor = Callable[[list[Vaga]], list[Vaga]]


def manter_descricoes_como_estao(vagas: list[Vaga]) -> list[Vaga]:
    return vagas


class ParametrosDaExecucao(BaseModel):
    modelo: str
    quantidade: int = Field(ge=1)
    nota_minima: int = Field(ge=0, le=100)
    falhas_ate_pausar: int = Field(ge=1)
    dias_de_silencio_ate_avisar: int = Field(ge=1)
    dias_ate_apagar_conta_excluida: int = Field(ge=1)
    url_de_rastreio: str = ""


class RevalidacaoDeDestinatarios:
    def __init__(self, repositorio: Repositorio) -> None:
        self.repositorio = repositorio
        self.falhas: set[UUID] = set()

    def permite(self, usuario: Usuario) -> bool:
        try:
            return self.repositorio.pode_entregar(usuario)
        except ErroDeArmazenamento as erro:
            self.falhas.add(usuario.id)
            logger.warning("destinatário %s não pôde ser revalidado: %s", usuario.id, erro)
            return False


class ResumoDaExecucao(BaseModel):
    usuarios: int
    usuarios_com_falha_de_revalidacao: int = 0
    usuarios_sem_entrega_por_falha_de_revalidacao: int = 0
    vagas_coletadas: int
    vagas_unicas: int
    vagas_candidatas: int
    vagas_extraidas_agora: int
    vagas_sem_extracao: int = 0
    extracoes_nao_gravadas: int = 0
    enviadas_por_usuario: dict[UUID, list[Recomendacao]]

    def atendidos(self) -> int:
        return len(self.enviadas_por_usuario)

    def vagas_enviadas(self) -> int:
        return sum(len(selecionadas) for selecionadas in self.enviadas_por_usuario.values())


def executar(
    coletor: ColetorDeVagas,
    extrator: ExtratorDeVagas,
    notificador: Notificador,
    repositorio: Repositorio,
    parametros: ParametrosDaExecucao,
    agora: datetime,
    pontuador: Pontuador = pontuar_vagas,
    enriquecer: Enriquecedor = manter_descricoes_como_estao,
    apenas_o_perfil: UUID | None = None,
) -> ResumoDaExecucao:
    apagar_contas_no_prazo(repositorio, parametros.dias_ate_apagar_conta_excluida)
    usuarios = selecionar_usuarios(repositorio.listar_ativos(), apenas_o_perfil)
    coletadas = coletor.coletar()
    unicas = remover_duplicatas(coletadas)
    candidatas = enriquecer(candidatas_de_algum_perfil(unicas, usuarios, repositorio))
    unicas = substituir_enriquecidas(unicas, candidatas)
    logger.info(
        "%d vagas coletadas, %d únicas, %d candidatas de algum perfil, %d usuários",
        len(coletadas),
        len(unicas),
        len(candidatas),
        len(usuarios),
    )
    extracoes, balanco = obter_extracoes(extrator, repositorio, candidatas, parametros.modelo)
    enviadas_por_usuario: dict[UUID, list[Recomendacao]] = {}
    revalidacao = RevalidacaoDeDestinatarios(repositorio)
    for usuario in usuarios:
        selecionadas = atender_usuario(
            usuario,
            unicas,
            extracoes,
            notificador,
            repositorio,
            parametros,
            agora,
            pontuador,
            revalidacao,
        )
        if selecionadas is not None:
            enviadas_por_usuario[usuario.id] = selecionadas
    return ResumoDaExecucao(
        usuarios=len(usuarios),
        usuarios_com_falha_de_revalidacao=len(revalidacao.falhas),
        usuarios_sem_entrega_por_falha_de_revalidacao=len(
            revalidacao.falhas - enviadas_por_usuario.keys()
        ),
        vagas_coletadas=len(coletadas),
        vagas_unicas=len(unicas),
        vagas_candidatas=len(candidatas),
        vagas_extraidas_agora=balanco.extraidas_agora,
        vagas_sem_extracao=balanco.sem_extracao,
        extracoes_nao_gravadas=balanco.nao_gravadas,
        enviadas_por_usuario=enviadas_por_usuario,
    )


def substituir_enriquecidas(unicas: list[Vaga], candidatas: list[Vaga]) -> list[Vaga]:
    por_chave = {vaga.chave(): vaga for vaga in candidatas}
    return [por_chave.get(vaga.chave(), vaga) for vaga in unicas]


def apagar_contas_no_prazo(repositorio: Repositorio, dias_de_carencia: int) -> None:
    try:
        apagadas = repositorio.apagar_contas_excluidas(dias_de_carencia)
    except ErroDeArmazenamento as erro:
        logger.warning("contas excluídas não foram apagadas: %s", erro)
        return
    if apagadas:
        logger.info("%d contas apagadas após %d dias de carência", apagadas, dias_de_carencia)


def com_areas_recusadas(usuario: Usuario, recusas: RecusasDoUsuario) -> Usuario:
    escolhidas = set(usuario.perfil.areas_de_interesse)
    recusadas = [area for area in recusas.areas if area not in escolhidas]
    if not recusadas:
        return usuario
    perfil = usuario.perfil.model_copy(update={"areas_recusadas": recusadas})
    return usuario.model_copy(update={"perfil": perfil})


def selecionar_usuarios(usuarios: list[Usuario], apenas_o_perfil: UUID | None) -> list[Usuario]:
    if apenas_o_perfil is None:
        return usuarios
    escolhidos = [usuario for usuario in usuarios if usuario.id == apenas_o_perfil]
    if not escolhidos:
        logger.warning("perfil %s não está ativo ou não tem Telegram vinculado", apenas_o_perfil)
    return escolhidos


def candidatas_de_algum_perfil(
    vagas: list[Vaga], usuarios: list[Usuario], repositorio: Repositorio
) -> list[Vaga]:
    aprovadas: dict[ChaveDaVaga, Vaga] = {}
    for usuario in usuarios:
        ja_enviadas = ids_ja_enviadas_ou_nenhum(repositorio, usuario)
        for vaga in filtrar(vagas, usuario.perfil):
            if vaga.chave() not in ja_enviadas:
                aprovadas.setdefault(vaga.chave(), vaga)
    return list(aprovadas.values())


def ids_ja_enviadas_ou_nenhum(repositorio: Repositorio, usuario: Usuario) -> set[tuple[str, str]]:
    try:
        return repositorio.ids_ja_enviadas(usuario)
    except ErroDeArmazenamento as erro:
        logger.warning("envios do usuário %s não puderam ser lidos: %s", usuario.id, erro)
        return set()


class BalancoDaExtracao(BaseModel):
    extraidas_agora: int = 0
    sem_extracao: int = 0
    nao_gravadas: int = 0


def obter_extracoes(
    extrator: ExtratorDeVagas, repositorio: Repositorio, candidatas: list[Vaga], modelo: str
) -> tuple[dict[ChaveDaVaga, ExtracaoDaVaga], BalancoDaExtracao]:
    try:
        extracoes = dict(repositorio.extracoes_existentes(candidatas, modelo))
    except ErroDeArmazenamento as erro:
        logger.warning("extrações guardadas não puderam ser lidas: %s", erro)
        extracoes = {}
    pendentes = [vaga for vaga in candidatas if vaga.chave() not in extracoes]
    logger.info("%d extrações reaproveitadas, %d vagas a extrair", len(extracoes), len(pendentes))
    novas = extrator.extrair(pendentes)
    vagas_por_identidade = {vaga.identidade(): vaga for vaga in pendentes}
    guardadas = []
    for extracao in novas:
        vaga = vagas_por_identidade.get(extracao.id_vaga)
        if vaga is None or vaga.chave() in extracoes:
            continue
        extracoes[vaga.chave()] = extracao
        guardadas.append((vaga, extracao))
    nao_gravadas = 0
    try:
        repositorio.guardar_extracoes(guardadas, modelo)
    except ErroDeArmazenamento as erro:
        nao_gravadas = len(guardadas)
        logger.warning("extrações não foram gravadas: %s", erro)
    sem_extracao = len(pendentes) - len(guardadas)
    if sem_extracao:
        logger.warning(
            "%d de %d vagas pendentes ficaram sem extração", sem_extracao, len(pendentes)
        )
    return extracoes, BalancoDaExtracao(
        extraidas_agora=len(guardadas), sem_extracao=sem_extracao, nao_gravadas=nao_gravadas
    )


def atender_usuario(
    usuario: Usuario,
    vagas: list[Vaga],
    extracoes: dict[ChaveDaVaga, ExtracaoDaVaga],
    notificador: Notificador,
    repositorio: Repositorio,
    parametros: ParametrosDaExecucao,
    agora: datetime,
    pontuador: Pontuador,
    revalidacao: RevalidacaoDeDestinatarios,
) -> list[Recomendacao] | None:
    try:
        repositorio.travar_atendimento(usuario)
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s ficou sem mensagem: %s", usuario.id, erro)
        return None
    try:
        return atender_usuario_travado(
            usuario,
            vagas,
            extracoes,
            notificador,
            repositorio,
            parametros,
            agora,
            pontuador,
            revalidacao,
        )
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s ficou sem mensagem: %s", usuario.id, erro)
        return None
    finally:
        repositorio.liberar_atendimento(usuario)


def atender_usuario_travado(
    usuario: Usuario,
    vagas: list[Vaga],
    extracoes: dict[ChaveDaVaga, ExtracaoDaVaga],
    notificador: Notificador,
    repositorio: Repositorio,
    parametros: ParametrosDaExecucao,
    agora: datetime,
    pontuador: Pontuador,
    revalidacao: RevalidacaoDeDestinatarios,
) -> list[Recomendacao] | None:
    ja_enviadas = repositorio.ids_ja_enviadas(usuario)
    recusas = repositorio.recusas_do_usuario(usuario)
    usuario = com_areas_recusadas(usuario, recusas)
    candidatas = [
        vaga
        for vaga in filtrar(vagas, usuario.perfil)
        if vaga.chave() not in ja_enviadas
    ]
    candidatas = remover_republicacoes_de(
        candidatas,
        repositorio.vagas_enviadas_recentemente(usuario) + recusas.vagas_repetidas,
    )
    novas = aplicar_regras_objetivas(
        pontuador(candidatas, extracoes, usuario.perfil), usuario.perfil
    )
    sem_extracao = len(candidatas) - len(novas)
    selecionadas = selecionar(novas, parametros.quantidade, parametros.nota_minima)
    if not selecionadas and sem_extracao:
        logger.warning(
            "usuário %s ficou sem mensagem: %d das %d vagas pendentes estão sem extração",
            usuario.id,
            sem_extracao,
            len(candidatas),
        )
        return None
    logger.info(
        "usuário %s: %d candidatas, %d avaliadas agora, %d enviadas",
        usuario.id,
        len(candidatas),
        len(novas),
        len(selecionadas),
    )
    if not revalidacao.permite(usuario):
        return None
    gravar_avaliacoes(repositorio, usuario, novas, parametros.modelo)
    if not selecionadas:
        avisar_que_nao_houve_vaga(notificador, repositorio, usuario, parametros, agora, revalidacao)
        return None
    if not revalidacao.permite(usuario):
        return None
    try:
        pergunta = formatar_pergunta_de_feedback(selecionadas)
        pergunta.texto = (
            formatar_mensagem(selecionadas, agora.date(), parametros.url_de_rastreio)
            + "\n\n"
            + pergunta.texto
        )
        notificador.enviar_pergunta(usuario.chat_id, pergunta)
    except ErroDeNotificacao as erro:
        logger.warning("usuário %s ficou sem mensagem: %s", usuario.id, erro)
        pausar_apos_falhas_seguidas(repositorio, usuario, parametros.falhas_ate_pausar)
        return None
    try:
        repositorio.registrar_envios(usuario, selecionadas)
    except ErroDeArmazenamento as erro:
        logger.warning(
            "usuário %s: mensagem enviada, mas o envio não foi gravado: %s", usuario.id, erro
        )
    return selecionadas


def gravar_avaliacoes(
    repositorio: Repositorio, usuario: Usuario, novas: list[ResultadoMatch], modelo: str
) -> None:
    try:
        repositorio.guardar_avaliacoes(usuario, novas, modelo)
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s: avaliações não foram gravadas: %s", usuario.id, erro)


def avisar_que_nao_houve_vaga(
    notificador: Notificador,
    repositorio: Repositorio,
    usuario: Usuario,
    parametros: ParametrosDaExecucao,
    agora: datetime,
    revalidacao: RevalidacaoDeDestinatarios,
) -> None:
    dias = dias_de_silencio_a_relatar(usuario, agora, parametros.dias_de_silencio_ate_avisar)
    if not revalidacao.permite(usuario):
        return
    try:
        notificador.enviar(usuario.chat_id, formatar_mensagem_sem_vagas(agora.date(), dias))
    except ErroDeNotificacao as erro:
        logger.warning("usuário %s ficou sem a mensagem do dia: %s", usuario.id, erro)
        pausar_apos_falhas_seguidas(repositorio, usuario, parametros.falhas_ate_pausar)
        return
    if dias is None:
        return
    logger.info("usuário %s avisado de %d dias sem recomendação", usuario.id, dias)
    try:
        repositorio.registrar_aviso_de_silencio(usuario)
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s: aviso de silêncio não foi gravado: %s", usuario.id, erro)


def dias_de_silencio_a_relatar(usuario: Usuario, agora: datetime, limite: int) -> int | None:
    if not silencio_prolongado(usuario, agora, limite):
        return None
    return (agora - usuario.sem_recomendacao_desde).days


def silencio_prolongado(usuario: Usuario, agora: datetime, dias: int) -> bool:
    if usuario.sem_recomendacao_desde is None:
        return False
    limite = agora - timedelta(days=dias)
    if usuario.sem_recomendacao_desde > limite:
        return False
    return usuario.silencio_avisado_em is None or usuario.silencio_avisado_em <= limite


def pausar_apos_falhas_seguidas(
    repositorio: Repositorio, usuario: Usuario, falhas_ate_pausar: int
) -> None:
    try:
        falhas = repositorio.registrar_falha_de_envio(usuario)
        if falhas < falhas_ate_pausar:
            return
        repositorio.pausar(usuario)
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s: falha de envio não registrada: %s", usuario.id, erro)
        return
    logger.warning("usuário %s pausado após %d falhas seguidas de envio", usuario.id, falhas)


def selecionar(
    resultados: list[ResultadoMatch], quantidade: int, nota_minima: int
) -> list[Recomendacao]:
    aprovados = [resultado for resultado in resultados if resultado.nota >= nota_minima]
    return [Recomendacao(resultado=resultado) for resultado in ranquear(aprovados)[:quantidade]]


def ranquear(resultados: list[ResultadoMatch]) -> list[ResultadoMatch]:
    return sorted(resultados, key=lambda resultado: resultado.nota, reverse=True)
