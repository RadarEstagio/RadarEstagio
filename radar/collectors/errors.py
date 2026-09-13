from radar.domain.models import Vaga


class ErroDeColeta(Exception):
    pass


class ColetaIncompleta(ErroDeColeta):
    def __init__(self, motivo: str, vagas: list[Vaga]) -> None:
        super().__init__(motivo)
        self.vagas = vagas
