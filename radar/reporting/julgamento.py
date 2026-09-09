from collections import Counter
from statistics import median

from radar.domain.models import EntregaJulgada, ResultadoDoJulgamento

FEEDBACK_POSITIVO = "vaga_util"
FEEDBACK_NEGATIVO = "vaga_irrelevante"
LIMITE_DE_EXEMPLOS = 5
NOTA_ALTA_DO_RADAR = 70


def formatar_julgamento(resultado: ResultadoDoJulgamento) -> str:
    linhas = [
        f"Juiz: {resultado.modelo} — {len(resultado.julgadas)} de {resultado.entregas_no_periodo} "
        f"entregas dos últimos {resultado.dias} dias julgadas "
        f"(amostra de {resultado.amostradas}; {resultado.sem_julgamento} sem julgamento)",
        "",
    ]
    if not resultado.julgadas:
        linhas.append("Nenhuma entrega julgada.")
        return "\n".join(linhas)
    linhas.extend(linhas_gerais(resultado.julgadas))
    linhas.extend(["", "Por perfil:"])
    linhas.extend(linhas_por_perfil(resultado.julgadas))
    linhas.extend(["", "Problemas apontados pelo juiz:"])
    linhas.extend(linhas_de_problemas(resultado.julgadas))
    linhas.extend(["", "Concordância com o feedback das pessoas:"])
    linhas.extend(linhas_de_concordancia(resultado.julgadas))
    linhas.extend(["", f"Reprovadas pelo juiz com nota do Radar ≥ {NOTA_ALTA_DO_RADAR}:"])
    linhas.extend(linhas_de_reprovadas(resultado.julgadas))
    return "\n".join(linhas)


def linhas_gerais(julgadas: list[EntregaJulgada]) -> list[str]:
    relevantes = sum(item.julgamento.relevante for item in julgadas)
    return [
        f"Relevantes segundo o juiz: {relevantes}/{len(julgadas)} "
        f"({percentual(relevantes, len(julgadas))})",
        f"Mediana da nota do juiz: {median(item.julgamento.nota_juiz for item in julgadas):.0f}"
        f" · mediana da nota do Radar: {mediana_do_radar(julgadas)}",
    ]


def linhas_por_perfil(julgadas: list[EntregaJulgada]) -> list[str]:
    grupos: dict[str, list[EntregaJulgada]] = {}
    for item in julgadas:
        chave = f"{item.entrega.perfil.curso} ({str(item.entrega.perfil_id)[:8]})"
        grupos.setdefault(chave, []).append(item)
    return [
        f"  {chave}: {sum(i.julgamento.relevante for i in itens)}/{len(itens)} relevantes"
        f" · juiz {median(i.julgamento.nota_juiz for i in itens):.0f}"
        f" · Radar {mediana_do_radar(itens)}"
        for chave, itens in grupos.items()
    ]


def linhas_de_problemas(julgadas: list[EntregaJulgada]) -> list[str]:
    contagem = Counter(item.julgamento.problema.value for item in julgadas)
    return [f"  {problema:<14}{total:>4}" for problema, total in contagem.most_common()]


def linhas_de_concordancia(julgadas: list[EntregaJulgada]) -> list[str]:
    com_feedback = [
        item for item in julgadas if item.entrega.feedback in (FEEDBACK_POSITIVO, FEEDBACK_NEGATIVO)
    ]
    if not com_feedback:
        return ["  nenhuma entrega julgada tem feedback registrado"]
    concordam = [item for item in com_feedback if concorda(item)]
    linhas = [
        f"  {len(concordam)}/{len(com_feedback)} concordam "
        f"({percentual(len(concordam), len(com_feedback))})"
    ]
    for item in [i for i in com_feedback if not concorda(i)][:LIMITE_DE_EXEMPLOS]:
        linhas.append(
            f"  discorda: {item.entrega.vaga.titulo[:50]} · pessoa disse {item.entrega.feedback}"
            f" · juiz {'relevante' if item.julgamento.relevante else 'irrelevante'}"
            f" ({item.julgamento.problema.value}): {item.julgamento.motivo}"
        )
    return linhas


def linhas_de_reprovadas(julgadas: list[EntregaJulgada]) -> list[str]:
    reprovadas = [
        item
        for item in julgadas
        if not item.julgamento.relevante
        and item.entrega.nota_do_radar is not None
        and item.entrega.nota_do_radar >= NOTA_ALTA_DO_RADAR
    ]
    if not reprovadas:
        return ["  nenhuma"]
    return [
        f"  {item.entrega.nota_do_radar:>3} · {item.entrega.vaga.titulo[:50]}"
        f" · {item.julgamento.problema.value}: {item.julgamento.motivo}"
        for item in sorted(reprovadas, key=lambda i: -(i.entrega.nota_do_radar or 0))[
            :LIMITE_DE_EXEMPLOS
        ]
    ]


def concorda(item: EntregaJulgada) -> bool:
    return item.julgamento.relevante == (item.entrega.feedback == FEEDBACK_POSITIVO)


def mediana_do_radar(itens: list[EntregaJulgada]) -> str:
    notas = [item.entrega.nota_do_radar for item in itens if item.entrega.nota_do_radar is not None]
    return f"{median(notas):.0f}" if notas else "—"


def percentual(parte: int, total: int) -> str:
    return f"{100 * parte / total:.0f}%" if total else "—"
