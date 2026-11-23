import math
import time
from collections.abc import Callable

JANELA_DE_UM_MINUTO_EM_SEGUNDOS = 60


class CotaEsgotada(Exception):
    pass


class CotaDeRequisicoes:
    def __init__(
        self,
        saldo: float = math.inf,
        limite_por_minuto: int | None = None,
        relogio: Callable[[], float] = time.monotonic,
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        self._saldo = saldo
        self._limite_por_minuto = limite_por_minuto
        self._relogio = relogio
        self._esperar = esperar
        self._momentos: list[float] = []
        self.requisicoes = 0
        self.esgotada = False

    def reservar(self) -> None:
        if self.requisicoes >= self._saldo:
            self.esgotada = True
            raise CotaEsgotada
        agora = self._recentes()
        limite = self._limite_por_minuto
        if limite is not None and len(self._momentos) >= limite:
            self._esperar(JANELA_DE_UM_MINUTO_EM_SEGUNDOS - (agora - self._momentos[-limite]))
            agora = self._recentes()
        self._momentos.append(agora)
        self.requisicoes += 1

    def esgotar(self) -> None:
        self._saldo = self.requisicoes
        self.esgotada = True

    def _recentes(self) -> float:
        agora = self._relogio()
        self._momentos = [
            momento
            for momento in self._momentos
            if agora - momento < JANELA_DE_UM_MINUTO_EM_SEGUNDOS
        ]
        return agora
