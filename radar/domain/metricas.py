from radar.domain.areas import area_do_curso
from radar.domain.models import FatoUtilidadeSemanal, UtilidadePorArea

AREA_NAO_CLASSIFICADA = "Não classificado"


def agrupar_utilidade_por_area(fatos: list[dict]) -> list[UtilidadePorArea]:
    ativados: dict[tuple[str, bool, str], int] = {}
    com_utilidade: dict[tuple[str, bool, str], int] = {}
    for bruto in fatos:
        fato = FatoUtilidadeSemanal(**bruto)
        chave = (fato.semana, fato.parcial, area_do_curso(fato.curso) or AREA_NAO_CLASSIFICADA)
        ativados[chave] = ativados.get(chave, 0) + 1
        com_utilidade[chave] = com_utilidade.get(chave, 0) + int(fato.com_utilidade)
    return [
        UtilidadePorArea(
            semana=semana,
            parcial=parcial,
            area=area,
            ativados=ativados[(semana, parcial, area)],
            com_utilidade=com_utilidade[(semana, parcial, area)],
        )
        for semana, parcial, area in sorted(
            ativados,
            key=lambda chave: (chave[0], chave[1], chave[2] == AREA_NAO_CLASSIFICADA, chave[2]),
        )
    ]
