from datetime import date
from pathlib import Path

from scripts.vigiar_radar_diario import TITULO_DO_DIARIO, conferir

PASTA_DOS_WORKFLOWS = Path(__file__).parent.parent / ".github/workflows"
HOJE = date(2026, 10, 21)


def execucao(numero, titulo, criada_em, status="completed", conclusao="success"):
    return {
        "run_number": numero,
        "display_title": titulo,
        "created_at": criada_em,
        "status": status,
        "conclusion": conclusao,
    }


def test_dia_sem_execucao_do_diario_avisa_que_o_disparo_nao_chegou():
    execucoes = [execucao(76, TITULO_DO_DIARIO, "2026-10-20T10:23:03Z")]

    em_ordem, situacao = conferir(execucoes, HOJE)

    assert not em_ordem
    assert "nenhum run do diário foi criado em 21/10" in situacao


def test_diario_que_terminou_bem_hoje_deixa_o_vigia_quieto():
    execucoes = [execucao(77, TITULO_DO_DIARIO, "2026-10-21T10:23:03Z")]

    em_ordem, situacao = conferir(execucoes, HOJE)

    assert em_ordem
    assert "#77" in situacao


def test_entrega_imediata_nao_conta_como_o_diario():
    execucoes = [
        execucao(77, "Entrega imediata", "2026-10-21T13:40:00Z"),
        execucao(76, TITULO_DO_DIARIO, "2026-10-20T10:23:03Z"),
    ]

    em_ordem, situacao = conferir(execucoes, HOJE)

    assert not em_ordem
    assert "nenhum run do diário" in situacao


def test_diario_parado_na_fila_avisa_com_o_estado_do_run():
    execucoes = [execucao(77, TITULO_DO_DIARIO, "2026-10-21T10:23:03Z", "queued", None)]

    em_ordem, situacao = conferir(execucoes, HOJE)

    assert not em_ordem
    assert "#77" in situacao
    assert "queued" in situacao


def test_diario_que_falhou_avisa_com_a_conclusao_do_run():
    execucoes = [execucao(77, TITULO_DO_DIARIO, "2026-10-21T10:23:03Z", conclusao="failure")]

    em_ordem, situacao = conferir(execucoes, HOJE)

    assert not em_ordem
    assert "#77" in situacao
    assert "failure" in situacao


def test_diario_reexecutado_que_terminou_bem_vale_mesmo_depois_de_uma_falha():
    execucoes = [
        execucao(78, TITULO_DO_DIARIO, "2026-10-21T11:05:00Z"),
        execucao(77, TITULO_DO_DIARIO, "2026-10-21T10:23:03Z", conclusao="failure"),
    ]

    em_ordem, _ = conferir(execucoes, HOJE)

    assert em_ordem


def test_o_dia_do_run_e_o_de_brasilia_e_nao_o_de_utc():
    execucoes = [execucao(76, TITULO_DO_DIARIO, "2026-10-21T02:30:00Z")]

    em_ordem, situacao = conferir(execucoes, HOJE)

    assert not em_ordem
    assert "nenhum run do diário foi criado em 21/10" in situacao


def test_o_diario_se_nomeia_com_o_titulo_que_o_vigia_procura():
    diario = (PASTA_DOS_WORKFLOWS / "radar-diario.yml").read_text().splitlines()
    nome_do_run = next(linha for linha in diario if linha.startswith("run-name:"))

    assert nome_do_run == (
        f"run-name: ${{{{ inputs.perfil && 'Entrega imediata' || '{TITULO_DO_DIARIO}' }}}}"
    )
