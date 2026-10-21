import json
import os
import sys
import urllib.request
from datetime import date, datetime
from zoneinfo import ZoneInfo

TITULO_DO_DIARIO = "Radar diário"
FUSO_DE_BRASILIA = ZoneInfo("America/Sao_Paulo")
EXECUCOES_CONSULTADAS = 30
TIMEOUT_DA_CONSULTA_EM_SEGUNDOS = 30
CONCLUSOES_SEM_FALHA = frozenset({"success", "skipped"})


def data_em_brasilia(instante: str) -> date:
    return datetime.fromisoformat(instante).astimezone(FUSO_DE_BRASILIA).date()


def diarios_do_dia(execucoes: list[dict], dia: date) -> list[dict]:
    return [
        execucao
        for execucao in execucoes
        if execucao["display_title"] == TITULO_DO_DIARIO
        and data_em_brasilia(execucao["created_at"]) == dia
    ]


def conferir(execucoes: list[dict], dia: date) -> tuple[bool, str]:
    diarios = diarios_do_dia(execucoes, dia)
    dia_formatado = f"{dia:%d/%m}"
    bem_sucedido = next((diario for diario in diarios if diario["conclusion"] == "success"), None)
    falhas = [
        diario
        for diario in diarios
        if diario["status"] == "completed" and diario["conclusion"] not in CONCLUSOES_SEM_FALHA
    ]
    if bem_sucedido is not None and not falhas:
        return (
            True,
            f"o diário de {dia_formatado} terminou bem no run #{bem_sucedido['run_number']}",
        )
    if bem_sucedido is not None:
        falha = falhas[0]
        momento = "depois" if bem_sucedido["run_number"] > falha["run_number"] else "antes"
        return (
            False,
            f"o run #{falha['run_number']} do diário terminou com {falha['conclusion']}; "
            f"o run #{bem_sucedido['run_number']} terminou bem {momento}",
        )
    if not diarios:
        return (
            False,
            f"nenhum run do diário foi criado em {dia_formatado}; "
            "o disparo do cron-job.org não chegou ao GitHub",
        )
    ultimo = diarios[0]
    if ultimo["status"] != "completed":
        return False, f"o run #{ultimo['run_number']} do diário ainda está em {ultimo['status']}"
    return False, f"o run #{ultimo['run_number']} do diário terminou com {ultimo['conclusion']}"


def buscar_execucoes(repositorio: str, token: str) -> list[dict]:
    pedido = urllib.request.Request(
        f"https://api.github.com/repos/{repositorio}/actions/workflows/radar-diario.yml/runs"
        f"?per_page={EXECUCOES_CONSULTADAS}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(pedido, timeout=TIMEOUT_DA_CONSULTA_EM_SEGUNDOS) as resposta:
        return json.load(resposta)["workflow_runs"]


def main() -> int:
    execucoes = buscar_execucoes(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    em_ordem, situacao = conferir(execucoes, datetime.now(FUSO_DE_BRASILIA).date())
    print(situacao)
    return 0 if em_ordem else 1


if __name__ == "__main__":
    sys.exit(main())
