from datetime import date
from uuid import UUID

from radar.domain.models import (
    ChaveDaVaga,
    EntregaParaJulgar,
    ExtracaoDaVaga,
    Recomendacao,
    RecusasDoUsuario,
    ResultadoMatch,
    Usuario,
    Vaga,
)


class RepositorioEmMemoria:
    def __init__(self, usuarios: list[Usuario]) -> None:
        self._usuarios = usuarios
        self._uso: dict[tuple[str, date], int] = {}

    def listar_ativos(self) -> list[Usuario]:
        return list(self._usuarios)

    def pode_entregar(self, usuario: Usuario) -> bool:
        return any(u.id == usuario.id and u.chat_id == usuario.chat_id for u in self._usuarios)

    def reivindicar_entregas_imediatas(self, perfil_id: UUID) -> set[UUID]:
        return {usuario.id for usuario in self._usuarios if usuario.id == perfil_id}

    def marcar_entregas_imediatas_atendidas(self, perfis: list[UUID]) -> None:
        return None

    def extracoes_existentes(
        self, vagas: list[Vaga], modelo: str
    ) -> dict[ChaveDaVaga, ExtracaoDaVaga]:
        return {}

    def guardar_extracoes(self, extracoes: list[tuple[Vaga, ExtracaoDaVaga]], modelo: str) -> None:
        return None

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]:
        return set()

    def vagas_enviadas_recentemente(self, usuario: Usuario) -> list[Vaga]:
        return []

    def recusas_do_usuario(self, usuario: Usuario) -> RecusasDoUsuario:
        return RecusasDoUsuario()

    def travar_atendimento(self, usuario: Usuario) -> None:
        return None

    def liberar_atendimento(self, usuario: Usuario) -> None:
        return None

    def guardar_avaliacoes(
        self, usuario: Usuario, avaliadas: list[ResultadoMatch], modelo: str
    ) -> None:
        return None

    def registrar_envios(self, usuario: Usuario, enviadas: list[Recomendacao]) -> None:
        return None

    def registrar_falha_de_envio(self, usuario: Usuario) -> int:
        return 0

    def apagar_contas_excluidas(self, dias_de_carencia: int) -> int:
        return 0

    def registrar_aviso_de_silencio(self, usuario: Usuario) -> None:
        return None

    def pausar(self, usuario: Usuario) -> None:
        return None

    def entregas_recentes(self, dias: int) -> list[EntregaParaJulgar]:
        return []

    def requisicoes_da_fonte_desde(self, fonte: str, desde: date) -> int:
        return sum(
            requisicoes
            for (origem, dia), requisicoes in self._uso.items()
            if origem == fonte and dia >= desde
        )

    def registrar_requisicoes_da_fonte(self, fonte: str, dia: date, requisicoes: int) -> None:
        self._uso[(fonte, dia)] = self._uso.get((fonte, dia), 0) + requisicoes
