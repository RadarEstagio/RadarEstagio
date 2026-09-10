import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from google.genai import errors

from radar.avaliacao.agy import JuizAgy
from radar.avaliacao.gemini import JuizGemini
from radar.avaliacao.prompt import (
    LIMITE_DA_DESCRICAO,
    apenas_das_vagas,
    montar_prompt_do_juiz,
)
from radar.domain.models import (
    AreaDeInteresse,
    Julgamento,
    Modalidade,
    Perfil,
    ProblemaJulgado,
    Vaga,
)
from radar.matching.errors import CotaDeAvaliacaoExcedida, ErroDeAvaliacao
from radar.settings import Settings

MODELO_DO_JUIZ = "juiz-de-teste"


def settings_de_teste(avaliador: str = "agy") -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key="app-key-de-teste",
        avaliador=avaliador,
        gemini_api_key="gemini-de-teste",
        juiz_modelo=MODELO_DO_JUIZ,
        telegram_bot_token="token-de-teste",
        telegram_chat_id="123",
    )


def perfil() -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python", "SQL"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.HIBRIDO,
        areas_de_interesse=[AreaDeInteresse("dados_ia")],
    )


def vaga(numero: int, descricao: str = "Estágio com Python e SQL.") -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=f"Estágio {numero}",
        empresa="Empresa",
        localizacao="Rio de Janeiro, RJ",
        descricao=descricao,
        url=f"https://exemplo.com/{numero}",
        publicada_em=datetime(2026, 9, 9, tzinfo=UTC),
    )


def julgamento(numero: int, relevante: bool = True) -> dict:
    return {
        "id_vaga": f"adzuna:{numero}",
        "relevante": relevante,
        "nota_juiz": 80 if relevante else 20,
        "problema": "nenhum" if relevante else "outra_area",
        "motivo": "porque sim",
    }


def test_prompt_do_juiz_descreve_perfil_e_vagas_sem_a_nota_do_radar():
    prompt = montar_prompt_do_juiz(perfil(), [vaga(1), vaga(2)])

    assert "Engenharia de Software" in prompt
    assert "Python, SQL" in prompt
    assert "Dados e IA" in prompt
    assert "id: adzuna:1" in prompt and "id: adzuna:2" in prompt
    assert "Nota" not in prompt
    assert "híbrido" in prompt.casefold() or "hibrido" in prompt


def test_prompt_do_juiz_trata_perfil_sem_habilidades_como_nao_informado():
    sem_habilidades = perfil().model_copy(update={"habilidades": [], "areas_de_interesse": []})

    prompt = montar_prompt_do_juiz(sem_habilidades, [vaga(1)])

    assert "ainda não informadas" in prompt
    assert "não informadas" in prompt


def test_prompt_do_juiz_corta_descricao_longa():
    longa = vaga(1, descricao="x" * (LIMITE_DA_DESCRICAO + 500))

    prompt = montar_prompt_do_juiz(perfil(), [longa])

    assert "x" * LIMITE_DA_DESCRICAO + " […]" in prompt
    assert "x" * (LIMITE_DA_DESCRICAO + 1) not in prompt


def test_apenas_das_vagas_ignora_ids_inventados_e_repeticoes():
    julgamentos = [
        Julgamento(id_vaga="adzuna:2", relevante=True, nota_juiz=90),
        Julgamento(id_vaga="adzuna:9", relevante=False, nota_juiz=10),
        Julgamento(id_vaga="adzuna:2", relevante=False, nota_juiz=5),
        Julgamento(id_vaga="adzuna:1", relevante=False, nota_juiz=30),
    ]

    filtrados = apenas_das_vagas(julgamentos, [vaga(1), vaga(2)])

    assert [(j.id_vaga, j.nota_juiz) for j in filtrados] == [("adzuna:1", 30), ("adzuna:2", 90)]


@dataclass
class ExecutorFalso:
    envelope: dict
    returncode: int = 0
    chamadas: list[list[str]] = field(default_factory=list)

    def __call__(self, args, **kwargs):
        self.chamadas.append(list(args))
        return subprocess.CompletedProcess(args, self.returncode, json.dumps(self.envelope), "")


def test_juiz_agy_usa_o_modelo_do_juiz_e_devolve_os_julgamentos():
    executor = ExecutorFalso(
        {
            "status": "SUCCESS",
            "structured_output": {"julgamentos": [julgamento(1), julgamento(2, False)]},
        }
    )

    resultado = JuizAgy(settings_de_teste(), executor=executor).julgar(perfil(), [vaga(1), vaga(2)])

    argumentos = executor.chamadas[0]
    assert argumentos[argumentos.index("--model") + 1] == MODELO_DO_JUIZ
    assert "julgamentos" in argumentos[argumentos.index("--json-schema") + 1]
    assert [(j.id_vaga, j.relevante, j.problema) for j in resultado] == [
        ("adzuna:1", True, ProblemaJulgado.NENHUM),
        ("adzuna:2", False, ProblemaJulgado.OUTRA_AREA),
    ]


def test_juiz_agy_sem_vagas_nao_chama_o_processo():
    executor = ExecutorFalso({"status": "SUCCESS", "structured_output": {"julgamentos": []}})

    assert JuizAgy(settings_de_teste(), executor=executor).julgar(perfil(), []) == []
    assert executor.chamadas == []


def test_juiz_agy_propaga_falha_do_processo_como_erro_de_avaliacao():
    executor = ExecutorFalso({"status": "ERROR", "error": "modelo indisponível"})

    with pytest.raises(ErroDeAvaliacao, match="AGY falhou"):
        JuizAgy(settings_de_teste(), executor=executor).julgar(perfil(), [vaga(1)])


def test_juiz_agy_rejeita_problema_fora_do_catalogo():
    executor = ExecutorFalso(
        {
            "status": "SUCCESS",
            "structured_output": {"julgamentos": [{**julgamento(1), "problema": "sei la"}]},
        }
    )

    with pytest.raises(ErroDeAvaliacao, match="saída estruturada inválida"):
        JuizAgy(settings_de_teste(), executor=executor).julgar(perfil(), [vaga(1)])


class ClienteFalso:
    def __init__(self, texto: str | None = None, erro: Exception | None = None) -> None:
        self.chamadas: list[dict] = []
        self.models = SimpleNamespace(generate_content=self._gerar)
        self._texto = texto
        self._erro = erro

    def _gerar(self, **kwargs):
        self.chamadas.append(kwargs)
        if self._erro:
            raise self._erro
        return SimpleNamespace(text=self._texto)


def test_juiz_gemini_usa_o_modelo_do_juiz_e_interpreta_o_json():
    cliente = ClienteFalso(json.dumps({"julgamentos": [julgamento(1)]}))

    resultado = JuizGemini(settings_de_teste("gemini_api"), cliente).julgar(perfil(), [vaga(1)])

    assert cliente.chamadas[0]["model"] == MODELO_DO_JUIZ
    assert resultado[0].nota_juiz == 80


def test_juiz_gemini_traduz_cota_excedida():
    cliente = ClienteFalso(erro=errors.APIError(429, {"error": {"message": "retry in 7s"}}))

    with pytest.raises(CotaDeAvaliacaoExcedida):
        JuizGemini(settings_de_teste("gemini_api"), cliente).julgar(perfil(), [vaga(1)])
