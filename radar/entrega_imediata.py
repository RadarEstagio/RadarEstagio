import logging
from typing import Any
from uuid import UUID

from radar.domain.models import Usuario
from radar.domain.ports import Repositorio
from radar.storage.errors import ErroDeArmazenamento

logger = logging.getLogger(__name__)


def usuarios_a_atender(
    repositorio: Repositorio, ativos: list[Usuario], apenas_o_perfil: UUID | None
) -> list[Usuario]:
    if apenas_o_perfil is None:
        marcar_como_atendidos(repositorio, ativos)
        return ativos
    reivindicados = repositorio.reivindicar_entregas_imediatas(apenas_o_perfil)
    if apenas_o_perfil not in reivindicados:
        logger.warning("perfil %s já atendido, inativo ou sem Telegram vinculado", apenas_o_perfil)
    return [usuario for usuario in repositorio.listar_ativos() if usuario.id in reivindicados]


def marcar_como_atendidos(repositorio: Repositorio, atendidos: list[Usuario]) -> None:
    try:
        repositorio.marcar_entregas_imediatas_atendidas([usuario.id for usuario in atendidos])
    except ErroDeArmazenamento as erro:
        logger.warning("entregas imediatas não foram marcadas como atendidas: %s", erro)


class RepositorioDosAtendidos:
    def __init__(self, repositorio: Repositorio, atendidos: list[Usuario]) -> None:
        self._repositorio = repositorio
        self._atendidos = atendidos

    def listar_ativos(self) -> list[Usuario]:
        return list(self._atendidos)

    def __getattr__(self, nome: str) -> Any:
        return getattr(self._repositorio, nome)
