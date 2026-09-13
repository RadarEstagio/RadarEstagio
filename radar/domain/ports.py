from datetime import date
from typing import Protocol
from uuid import UUID

from radar.domain.models import (
    ChaveDaVaga,
    EntregaParaJulgar,
    ExtracaoDaVaga,
    FunilDaCoorte,
    Julgamento,
    Perfil,
    PerguntaDeFeedback,
    Recomendacao,
    RecusasDoUsuario,
    ResultadoMatch,
    Usuario,
    Vaga,
)


class ColetorDeVagas(Protocol):
    def coletar(self) -> list[Vaga]: ...


class ExtratorDeVagas(Protocol):
    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]: ...


class Notificador(Protocol):
    def enviar(self, chat_id: str, texto: str) -> None: ...

    def enviar_pergunta(self, chat_id: str, pergunta: PerguntaDeFeedback) -> None: ...


class RepositorioDeUsuarios(Protocol):
    def listar_ativos(self) -> list[Usuario]: ...

    def pode_entregar(self, usuario: Usuario) -> bool: ...

    def reivindicar_entregas_imediatas(self, perfil_id: UUID) -> set[UUID]: ...

    def marcar_entregas_imediatas_atendidas(self, perfis: list[UUID]) -> None: ...


class RepositorioDeAvaliacoes(Protocol):
    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]: ...

    def vagas_enviadas_recentemente(self, usuario: Usuario) -> list[Vaga]: ...

    def recusas_do_usuario(self, usuario: Usuario) -> RecusasDoUsuario: ...

    def travar_atendimento(self, usuario: Usuario) -> None: ...

    def liberar_atendimento(self, usuario: Usuario) -> None: ...

    def extracoes_existentes(
        self, vagas: list[Vaga], modelo: str
    ) -> dict[ChaveDaVaga, ExtracaoDaVaga]: ...

    def guardar_extracoes(
        self, extracoes: list[tuple[Vaga, ExtracaoDaVaga]], modelo: str
    ) -> None: ...

    def guardar_avaliacoes(
        self, usuario: Usuario, avaliadas: list[ResultadoMatch], modelo: str
    ) -> None: ...

    def registrar_envios(self, usuario: Usuario, enviadas: list[Recomendacao]) -> None: ...

    def registrar_falha_de_envio(self, usuario: Usuario) -> int: ...

    def apagar_contas_excluidas(self, dias_de_carencia: int) -> int: ...

    def registrar_aviso_de_silencio(self, usuario: Usuario) -> None: ...

    def pausar(self, usuario: Usuario) -> None: ...

    def requisicoes_da_fonte_desde(self, fonte: str, desde: date) -> int: ...

    def registrar_requisicoes_da_fonte(self, fonte: str, dia: date, requisicoes: int) -> None: ...


class RepositorioDeMetricas(Protocol):
    def funil_da_coorte(self, dias: int) -> FunilDaCoorte: ...

    def entregas_recentes(self, dias: int) -> list[EntregaParaJulgar]: ...


class JuizDeRecomendacoes(Protocol):
    def julgar(self, perfil: Perfil, vagas: list[Vaga]) -> list[Julgamento]: ...


class Repositorio(RepositorioDeUsuarios, RepositorioDeAvaliacoes, Protocol): ...
