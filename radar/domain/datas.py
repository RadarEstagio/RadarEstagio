from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

FUSO_DA_ENTREGA = ZoneInfo("America/Sao_Paulo")


def data_local(momento: datetime) -> date:
    return momento.astimezone(FUSO_DA_ENTREGA).date()


def data_de_publicacao(publicada_em: datetime) -> date:
    em_utc = publicada_em.astimezone(UTC)
    if em_utc.time() == time(0):
        return em_utc.date()
    return data_local(publicada_em)
