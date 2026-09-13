from datetime import date

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
        self._dias_sem_extracao: dict[ChaveDaVaga, tuple[date, int]] = {}

    def listar_ativos(self) -> list[Usuario]:
        return list(self._usuarios)

    def pode_entregar(self, usuario: Usuario) -> bool:
        return any(u.id == usuario.id and u.chat_id == usuario.chat_id for u in self._usuarios)

    def extracoes_existentes(
        self, vagas: list[Vaga], modelo: str
    ) -> dict[ChaveDaVaga, ExtracaoDaVaga]:
        return {}

    def guardar_extracoes(self, extracoes: list[tuple[Vaga, ExtracaoDaVaga]], modelo: str) -> None:
        for vaga, _ in extracoes:
            self._dias_sem_extracao.pop(vaga.chave(), None)

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

    def registrar_vagas_sem_extracao(
        self, vagas: list[Vaga], dia: date
    ) -> dict[ChaveDaVaga, int] | None:
        dias: dict[ChaveDaVaga, int] = {}
        for vaga in vagas:
            ultimo_dia, contagem = self._dias_sem_extracao.get(vaga.chave(), (None, 0))
            if ultimo_dia != dia:
                contagem += 1
            self._dias_sem_extracao[vaga.chave()] = (dia, contagem)
            dias[vaga.chave()] = contagem
        return dias

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


class RepositorioDoModoLocal(RepositorioEmMemoria):
    def registrar_vagas_sem_extracao(
        self, vagas: list[Vaga], dia: date
    ) -> dict[ChaveDaVaga, int] | None:
        return None
