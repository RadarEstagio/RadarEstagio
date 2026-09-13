import json
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import pytest
from google.genai import errors, types

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.matching.errors import (
    AvaliadorIndisponivel,
    CotaDeAvaliacaoExcedida,
    ErroDeAvaliacao,
    ErroTemporarioDeAvaliacao,
)
from radar.matching.extracao import ExtracoesDeVagas
from radar.matching.gemini import ExtratorGemini
from radar.matching.lotes import ESPERA_PADRAO_EM_SEGUNDOS, ExtratorEmLotes
from radar.matching.prompt import montar_prompt
from radar.settings import Settings

MODELO_DE_TESTE = "modelo-de-teste"


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key="app-key-de-teste",
        gemini_api_key="gemini-de-teste",
        gemini_modelo=MODELO_DE_TESTE,
        telegram_bot_token="token-de-teste",
        telegram_chat_id="123",
    )


def vaga_exemplo(numero: int = 1) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=f"Estágio em Desenvolvimento Python {numero}",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, Rio de Janeiro",
        descricao="Buscamos estudante com Python e SQL. Trabalho remoto.",
        url=f"https://exemplo.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


@dataclass
class RespostaFalsa:
    text: str | None


class ModelsFalso:
    def __init__(self, resposta: RespostaFalsa | Exception) -> None:
        self._resposta = resposta
        self.chamadas: list[dict] = []

    def generate_content(self, **argumentos) -> RespostaFalsa:
        self.chamadas.append(argumentos)
        if isinstance(self._resposta, Exception):
            raise self._resposta
        return self._resposta


class ClienteFalso:
    def __init__(self, resposta: RespostaFalsa | Exception) -> None:
        self.models = ModelsFalso(resposta)


def extrator_com(resposta: RespostaFalsa | Exception) -> tuple[ExtratorGemini, ClienteFalso]:
    cliente = ClienteFalso(resposta)
    return ExtratorGemini(settings_de_teste(), cliente), cliente


def erro_da_api(codigo: int, mensagem: str) -> errors.APIError:
    return errors.APIError(codigo, {"error": {"message": mensagem, "status": "ERRO"}})


def extracao(numero: str, **alteracoes) -> dict:
    dados = {
        "id_vaga": numero,
        "area_da_vaga": "computacao",
        "cursos_aceitos": ["Ciência da Computação"],
        "aceita_qualquer_curso": False,
        "periodo_minimo": None,
        "experiencia_minima_anos": None,
        "habilidades_obrigatorias": [],
        "habilidades_desejaveis": ["Python", "SQL"],
        "alerta_pegadinha": None,
    }
    dados.update(alteracoes)
    return dados


def resposta_com(*extracoes: dict) -> RespostaFalsa:
    return RespostaFalsa(json.dumps({"extracoes": extracoes}))


def test_converte_json_do_gemini_em_extracoes_na_ordem_da_resposta():
    extrator, _ = extrator_com(
        resposta_com(
            extracao(
                "2",
                area_da_vaga="direito",
                cursos_aceitos=["Engenharia Elétrica"],
                periodo_minimo=6,
                habilidades_obrigatorias=["Java"],
                habilidades_desejaveis=[],
                alerta_pegadinha="Exige pleno.",
            ),
            extracao("1"),
        )
    )

    extracoes = extrator.extrair([vaga_exemplo(1), vaga_exemplo(2)])

    assert [item.id_vaga for item in extracoes] == ["2", "1"]
    assert extracoes[0].area_da_vaga == "direito"
    assert extracoes[0].cursos_aceitos == ["Engenharia Elétrica"]
    assert extracoes[0].periodo_minimo == 6
    assert extracoes[0].habilidades_obrigatorias == ["Java"]
    assert extracoes[0].alerta_pegadinha == "Exige pleno."
    assert extracoes[1].habilidades_desejaveis == ["Python", "SQL"]
    assert extracoes[1].alerta_pegadinha is None


def test_envia_prompt_de_lote_modelo_e_schema_json_ao_gemini():
    extrator, cliente = extrator_com(RespostaFalsa('{"extracoes": []}'))
    vagas = [vaga_exemplo(1), vaga_exemplo(2)]

    extrator.extrair(vagas)

    chamada = cliente.models.chamadas[0]
    assert chamada["model"] == MODELO_DE_TESTE
    assert chamada["contents"] == montar_prompt(vagas)
    assert chamada["config"].response_mime_type == "application/json"
    assert chamada["config"].response_schema is ExtracoesDeVagas
    assert chamada["config"].temperature == 0


def test_lista_vazia_nao_chama_o_modelo():
    extrator, cliente = extrator_com(RespostaFalsa(None))

    assert extrator.extrair([]) == []
    assert cliente.models.chamadas == []


def test_extracao_de_vaga_desconhecida_e_devolvida_para_o_pipeline_descartar():
    extrator, _ = extrator_com(resposta_com(extracao("1"), extracao("999")))

    extracoes = extrator.extrair([vaga_exemplo(1)])

    assert [item.id_vaga for item in extracoes] == ["1", "999"]


@pytest.mark.parametrize(
    "texto",
    [
        "isso não é json",
        '{"extracoes": [{"id_vaga": "1", "area_de_tecnologia": "talvez"}]}',
        '{"extracoes": [{"id_vaga": "1"}]}',
        '{"area_da_vaga": "computacao", "cursos_aceitos": ["formato antigo"]}',
        "",
        None,
    ],
)
def test_resposta_invalida_levanta_erro_de_avaliacao(texto: str | None):
    extrator, _ = extrator_com(RespostaFalsa(texto))

    with pytest.raises(ErroDeAvaliacao):
        extrator.extrair([vaga_exemplo()])


def test_erro_da_api_levanta_erro_de_avaliacao_com_status():
    extrator, _ = extrator_com(erro_da_api(400, "pedido inválido"))

    with pytest.raises(ErroDeAvaliacao, match="400") as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, ErroTemporarioDeAvaliacao)


@pytest.mark.parametrize("codigo", [500, 502, 503, 504])
def test_avaliador_fora_do_ar_e_erro_temporario_e_nao_cota(codigo: int):
    extrator, _ = extrator_com(erro_da_api(codigo, "sobrecarga"))

    with pytest.raises(AvaliadorIndisponivel, match=str(codigo)) as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida)


def erro_interno() -> errors.ServerError:
    return errors.ServerError(
        500, {"error": {"code": 500, "message": "An internal error has occurred."}}
    )


class ExtratorComErroInterno:
    def __init__(self, problematicas: set[str], persistente: bool) -> None:
        self._problematicas = problematicas
        self._persistente = persistente
        self._ja_falhou = False
        self.segundos = 0.0

    def extrair(self, lote: list[Vaga]) -> list[ExtracaoDaVaga]:
        self.segundos += 30
        ids = [item.identidade() for item in lote]
        if self._problematicas & set(ids) and (self._persistente or not self._ja_falhou):
            self._ja_falhou = True
            ExtratorGemini(settings_de_teste(), ClienteFalso(erro_interno())).extrair(lote)
        return [ExtracaoDaVaga(id_vaga=id_vaga, area_da_vaga="computacao") for id_vaga in ids]


def extrair_30_vagas_com_erro_interno(problematicas: set[str], persistente: bool = True):
    interno = ExtratorComErroInterno(problematicas, persistente)
    esperas: list[float] = []

    def esperar(segundos: float) -> None:
        esperas.append(segundos)
        interno.segundos += segundos

    em_lotes = ExtratorEmLotes(
        interno,
        10,
        esperar=esperar,
        prazo_em_segundos=600,
        timeout_da_chamada_em_segundos=120,
        relogio=lambda: interno.segundos,
    )
    extraidas = em_lotes.extrair([vaga_exemplo(numero) for numero in range(1, 31)])
    return extraidas, em_lotes.requisicoes, esperas, interno.segundos


@pytest.mark.parametrize(
    ("problematica", "requisicoes_esperadas"), [("adzuna:1", 10), ("adzuna:15", 12)]
)
def test_erro_interno_persistente_divide_o_lote_e_perde_so_a_vaga_problematica(
    problematica: str, requisicoes_esperadas: int
):
    extraidas, requisicoes, esperas, _ = extrair_30_vagas_com_erro_interno({problematica})

    assert len(extraidas) == 29
    assert problematica not in {item.id_vaga for item in extraidas}
    assert requisicoes == requisicoes_esperadas
    assert len(esperas) == 1
    assert esperas[0] < ESPERA_PADRAO_EM_SEGUNDOS


def test_erro_interno_passageiro_repete_o_mesmo_lote_sem_dividir():
    extraidas, requisicoes, esperas, _ = extrair_30_vagas_com_erro_interno(
        {"adzuna:1"}, persistente=False
    )

    assert len(extraidas) == 30
    assert requisicoes == 4
    assert len(esperas) == 1
    assert esperas[0] < ESPERA_PADRAO_EM_SEGUNDOS


def test_erro_interno_em_toda_chamada_nao_passa_do_prazo_da_extracao():
    todas = {f"adzuna:{numero}" for numero in range(1, 31)}

    extraidas, _, _, segundos = extrair_30_vagas_com_erro_interno(todas)

    assert extraidas == []
    assert segundos <= 600


def test_cada_chamada_leva_o_timeout_configurado_em_milissegundos():
    extrator, cliente = extrator_com(RespostaFalsa('{"extracoes": []}'))

    extrator.extrair([vaga_exemplo()])

    assert cliente.models.chamadas[0]["config"].http_options.timeout == 120_000


def test_chamada_que_estoura_o_timeout_e_indisponibilidade_temporaria():
    extrator, _ = extrator_com(httpx.ReadTimeout("tempo esgotado"))

    with pytest.raises(AvaliadorIndisponivel, match="120 s") as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida)


def test_cota_excedida_levanta_erro_especifico():
    extrator, _ = extrator_com(erro_da_api(429, "quota"))

    with pytest.raises(CotaDeAvaliacaoExcedida) as capturado:
        extrator.extrair([vaga_exemplo()])
    assert capturado.value.aguardar_segundos is None


def test_cota_excedida_le_o_tempo_de_espera_da_mensagem():
    mensagem = "You exceeded your current quota.\nPlease retry in 15.319626475s."
    extrator, _ = extrator_com(erro_da_api(429, mensagem))

    with pytest.raises(CotaDeAvaliacaoExcedida) as capturado:
        extrator.extrair([vaga_exemplo()])
    assert capturado.value.aguardar_segundos == pytest.approx(15.32, abs=0.01)


def test_prompt_identifica_todas_as_vagas_sem_citar_candidato():
    prompt = montar_prompt([vaga_exemplo(1), vaga_exemplo(2)])

    assert "Vagas (2)" in prompt
    assert "Vaga id=adzuna:1" in prompt
    assert "Vaga id=adzuna:2" in prompt
    assert "Estágio em Desenvolvimento Python 2" in prompt
    assert "cursos_aceitos" in prompt
    assert "periodo_minimo" in prompt
    assert "alerta_pegadinha" in prompt
    assert "habilidades_obrigatorias" in prompt
    assert "habilidades_desejaveis" in prompt


def test_extracao_pede_raciocinio_baixo_por_padrao():
    extrator, cliente = extrator_com(RespostaFalsa('{"extracoes": []}'))

    extrator.extrair([vaga_exemplo()])

    config = cliente.models.chamadas[0]["config"]
    assert config.thinking_config.thinking_level == types.ThinkingLevel.LOW


def test_raciocinio_padrao_deixa_o_modelo_decidir():
    settings = settings_de_teste().model_copy(update={"gemini_raciocinio": "padrao"})
    cliente = ClienteFalso(RespostaFalsa('{"extracoes": []}'))

    ExtratorGemini(settings, cliente).extrair([vaga_exemplo()])

    assert cliente.models.chamadas[0]["config"].thinking_config is None


def test_falha_de_rede_e_indisponibilidade_temporaria():
    extrator, _ = extrator_com(httpx.ConnectError("conexão recusada"))

    with pytest.raises(AvaliadorIndisponivel, match="Falha de rede") as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida)
