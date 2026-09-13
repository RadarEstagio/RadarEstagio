class ErroDeAvaliacao(Exception):
    pass


class ErroTemporarioDeAvaliacao(ErroDeAvaliacao):
    def __init__(self, mensagem: str, aguardar_segundos: float | None = None) -> None:
        super().__init__(mensagem)
        self.aguardar_segundos = aguardar_segundos


class CotaDeAvaliacaoExcedida(ErroTemporarioDeAvaliacao):
    pass


class AvaliadorIndisponivel(ErroTemporarioDeAvaliacao):
    pass


class FalhaInternaDoAvaliador(AvaliadorIndisponivel):
    pass
