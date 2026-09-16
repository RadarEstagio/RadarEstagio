import logging
from typing import Any
from uuid import UUID

from radar.domain.models import Usuario
from radar.domain.ports import Repositorio

logger = logging.getLogger(__name__)


def usuarios_a_atender(
    repositorio: Repositorio, ativos: list[Usuario], apenas_o_perfil: UUID | None
) -> list[Usuario]:
    if apenas_o_perfil is None:
        return ativos
    pendentes = repositorio.entregas_imediatas_pendentes(apenas_o_perfil)
    if apenas_o_perfil not in pendentes:
        logger.warning("perfil %s já atendido, inativo ou sem Telegram vinculado", apenas_o_perfil)
    return [usuario for usuario in repositorio.listar_ativos() if usuario.id in pendentes]


class RepositorioDosAtendidos:
    def __init__(self, repositorio: Repositorio, atendidos: list[Usuario]) -> None:
        self._repositorio = repositorio
        self._atendidos = atendidos

    def listar_ativos(self) -> list[Usuario]:
        return list(self._atendidos)

    def __getattr__(self, nome: str) -> Any:
        return getattr(self._repositorio, nome)


class RepositorioDaEntregaImediata(RepositorioDosAtendidos):
    def pode_entregar(self, usuario: Usuario) -> bool:
        if usuario.id not in self._repositorio.entregas_imediatas_pendentes(usuario.id):
            logger.warning(
                "perfil %s deixou de ter entrega imediata pendente durante a execução", usuario.id
            )
            return False
        return self._repositorio.pode_entregar(usuario)


def repositorio_da_execucao(
    repositorio: Repositorio, atendidos: list[Usuario], apenas_o_perfil: UUID | None
) -> RepositorioDosAtendidos:
    if apenas_o_perfil is None:
        return RepositorioDosAtendidos(repositorio, atendidos)
    return RepositorioDaEntregaImediata(repositorio, atendidos)
