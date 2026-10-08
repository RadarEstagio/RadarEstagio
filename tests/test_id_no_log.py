import ast
import logging
from pathlib import Path
from uuid import uuid4

from radar.domain.identificadores import CARACTERES_DO_TRECHO_DO_ID, trecho_do_id
from radar.entrega_imediata import usuarios_a_atender
from radar.pipeline import selecionar_usuarios
from radar.storage.memoria import RepositorioEmMemoria

PASTA_DO_RADAR = Path(__file__).parent.parent / "radar"
ESCRITAS_NO_LOG = {"print"}
NOMES_DE_IDENTIFICADOR = {"apenas_o_perfil", "perfil_id", "usuario_id"}
ENCURTADOR = "trecho_do_id"


def escreve_no_log(no: ast.AST) -> bool:
    if not isinstance(no, ast.Call):
        return False
    if isinstance(no.func, ast.Name):
        return no.func.id in ESCRITAS_NO_LOG
    return (
        isinstance(no.func, ast.Attribute)
        and isinstance(no.func.value, ast.Name)
        and no.func.value.id == "logger"
    )


def e_identificador_inteiro(no: ast.AST) -> bool:
    if isinstance(no, ast.Attribute) and no.attr == "id":
        return True
    return isinstance(no, ast.Name) and no.id in NOMES_DE_IDENTIFICADOR


def ja_encurtado(no: ast.AST) -> bool:
    return isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == ENCURTADOR


def identificadores_inteiros_em(no: ast.AST) -> list[ast.AST]:
    if ja_encurtado(no):
        return []
    return ([no] if e_identificador_inteiro(no) else []) + [
        achado
        for filho in ast.iter_child_nodes(no)
        for achado in identificadores_inteiros_em(filho)
    ]


def escritas_com_identificador_inteiro(arquivo: Path) -> list[str]:
    arvore = ast.parse(arquivo.read_text())
    return [
        f"{arquivo.relative_to(PASTA_DO_RADAR.parent)}:{achado.lineno}"
        for no in ast.walk(arvore)
        if escreve_no_log(no)
        for argumento in no.args
        for achado in identificadores_inteiros_em(argumento)
    ]


def test_trecho_do_id_mostra_so_o_comeco_entre_reticencias():
    identificador = uuid4()

    trecho = trecho_do_id(identificador)

    assert trecho == f"...{str(identificador)[:CARACTERES_DO_TRECHO_DO_ID]}..."
    assert str(identificador) not in trecho
    assert identificador.hex not in trecho


def test_nenhuma_escrita_do_radar_recebe_identificador_inteiro():
    fora_da_regra = [
        escrita
        for arquivo in sorted(PASTA_DO_RADAR.rglob("*.py"))
        for escrita in escritas_com_identificador_inteiro(arquivo)
    ]

    assert fora_da_regra == []


def test_perfil_sem_entrega_imediata_pendente_vai_ao_log_so_pelo_trecho(caplog):
    perfil_id = uuid4()

    with caplog.at_level(logging.WARNING):
        usuarios_a_atender(RepositorioEmMemoria([]), [], perfil_id)

    assert "já atendido" in caplog.text
    assert str(perfil_id) not in caplog.text
    assert perfil_id.hex not in caplog.text
    assert trecho_do_id(perfil_id) in caplog.text


def test_perfil_que_nao_esta_ativo_vai_ao_log_so_pelo_trecho(caplog):
    perfil_id = uuid4()

    with caplog.at_level(logging.WARNING):
        selecionar_usuarios([], perfil_id)

    assert "não está ativo" in caplog.text
    assert str(perfil_id) not in caplog.text
    assert perfil_id.hex not in caplog.text
    assert trecho_do_id(perfil_id) in caplog.text
