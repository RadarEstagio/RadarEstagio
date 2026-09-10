import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
AMBIENTE_MINIMO = {
    "ADZUNA_APP_ID": "id",
    "ADZUNA_APP_KEY": "chave",
    "TELEGRAM_BOT_TOKEN": "token",
    "TELEGRAM_CHAT_ID": "1",
    "AVALIADOR": "agy",
}


def test_cli_oferece_fluxo_local_sem_banco():
    processo = subprocess.run(
        [sys.executable, "-m", "radar", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert processo.returncode == 0
    assert "testar-local" in processo.stdout
    assert "sem banco ou histórico" in processo.stdout


def test_cli_oferece_o_julgamento_por_segundo_modelo():
    processo = subprocess.run(
        [sys.executable, "-m", "radar", "julgar", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert processo.returncode == 0
    assert "--dias" in processo.stdout
    assert "--amostra" in processo.stdout


def test_julgar_recusa_amostra_zero():
    processo = subprocess.run(
        [sys.executable, "-m", "radar", "julgar", "--amostra", "0"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert processo.returncode == 2
    assert "maior que zero" in processo.stderr


def rodar_verificar(fora_do_repositorio: Path, **variaveis: str) -> subprocess.CompletedProcess:
    ambiente = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(RAIZ),
        **AMBIENTE_MINIMO,
        **variaveis,
    }
    return subprocess.run(
        [sys.executable, "-m", "radar", "verificar"],
        capture_output=True,
        text=True,
        check=False,
        cwd=fora_do_repositorio,
        env=ambiente,
    )


def test_configuracao_invalida_diz_qual_e_o_problema(tmp_path):
    processo = rodar_verificar(tmp_path, AVALIADOR="gemini_api", GEMINI_API_KEY="")

    assert processo.returncode == 1
    assert "Configuração inválida" in processo.stderr
    assert "GEMINI_API_KEY" in processo.stderr


def test_quantidade_de_vagas_zero_e_recusada_antes_de_coletar(tmp_path):
    processo = rodar_verificar(tmp_path, QUANTIDADE_VAGAS_ENVIADAS="0")

    assert processo.returncode == 1
    assert "QUANTIDADE_VAGAS_ENVIADAS" in processo.stderr


def test_configuracao_valida_passa_na_verificacao(tmp_path):
    processo = rodar_verificar(tmp_path)

    assert processo.returncode == 0
    assert "Configuração carregada com sucesso." in processo.stdout
