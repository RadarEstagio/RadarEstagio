import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import pytest
from google import genai
from google.genai import errors, types

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.matching.errors import (
    AvaliadorIndisponivel,
    CotaDeAvaliacaoExcedida,
    ErroDeAvaliacao,
    ErroTemporarioDeAvaliacao,
    FalhaInternaDoAvaliador,
)
from radar.matching.extracao import ExtracoesDeVagas
from radar.matching.gemini import ExtratorGemini, gerar_json
from radar.matching.lotes import (
    ESPERA_PADRAO_EM_SEGUNDOS,
    MARGEM_DE_ESPERA_EM_SEGUNDOS,
    ExtratorEmLotes,
)
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


PADRAO_DO_ID_NO_PROMPT = re.compile(r"Vaga id=(\S+)")
HTML_DE_PROXY = "<html><body><h1>502 Bad Gateway</h1></body></html>"


def cliente_do_sdk(responder: Callable[[httpx.Request], httpx.Response]) -> genai.Client:
    transporte = httpx.MockTransport(responder)
    return genai.Client(
        api_key="gemini-de-teste",
        http_options=types.HttpOptions(httpx_client=httpx.Client(transport=transporte)),
    )


def ids_no_prompt(requisicao: httpx.Request) -> list[str]:
    corpo = json.loads(requisicao.content)
    return PADRAO_DO_ID_NO_PROMPT.findall(corpo["contents"][0]["parts"][0]["text"])


def envelope_com_texto(texto: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": texto}], "role": "model"}}]}


def extraindo_as_vagas_do_prompt(requisicao: httpx.Request) -> httpx.Response:
    extracoes = [extracao(id_vaga) for id_vaga in ids_no_prompt(requisicao)]
    return httpx.Response(200, json=envelope_com_texto(json.dumps({"extracoes": extracoes})))


def corpo_200(corpo: str | bytes) -> Callable[[httpx.Request], httpx.Response]:
    conteudo = corpo.encode() if isinstance(corpo, str) else corpo
    return lambda requisicao: httpx.Response(
        200, headers={"content-type": "text/html"}, content=conteudo
    )


def test_resposta_valida_pelo_sdk_vira_extracoes():
    extrator = ExtratorGemini(settings_de_teste(), cliente_do_sdk(extraindo_as_vagas_do_prompt))

    extracoes = extrator.extrair([vaga_exemplo(1), vaga_exemplo(2)])

    assert [item.id_vaga for item in extracoes] == ["adzuna:1", "adzuna:2"]


@pytest.mark.parametrize(
    "corpo",
    [
        pytest.param(HTML_DE_PROXY, id="html-de-proxy"),
        pytest.param('{"candidates": [{"content": {"parts": [{"text": "', id="json-cortado"),
        pytest.param("   ", id="so-espacos"),
        pytest.param(b"\xff\xfe{", id="bytes-invalidos"),
    ],
)
def test_corpo_200_que_nao_e_json_e_indisponibilidade_temporaria(corpo: str | bytes):
    extrator = ExtratorGemini(settings_de_teste(), cliente_do_sdk(corpo_200(corpo)))

    with pytest.raises(AvaliadorIndisponivel, match="não é JSON") as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida | FalhaInternaDoAvaliador)


def envelope_valido() -> dict:
    return envelope_com_texto(json.dumps({"extracoes": [extracao("adzuna:1")]}))


def corpo_json_200(envelope: object) -> Callable[[httpx.Request], httpx.Response]:
    return lambda requisicao: httpx.Response(200, json=envelope)


@pytest.mark.parametrize(
    "envelope",
    [
        pytest.param({"candidates": [{"content": {"parts": [{"text": 5}]}}]}, id="texto-numero"),
        pytest.param({"candidates": [{"content": {"parts": "x"}}]}, id="partes-texto"),
        pytest.param({"candidates": [{"content": "x"}]}, id="conteudo-texto"),
        pytest.param({**envelope_valido(), "usageMetadata": "x"}, id="uso-texto"),
        pytest.param({"candidates": 5}, id="candidatos-numero"),
        pytest.param({"candidates": [5]}, id="candidato-numero"),
        pytest.param(5, id="corpo-numero"),
        pytest.param(True, id="corpo-booleano"),
    ],
)
def test_envelope_fora_do_formato_da_api_e_indisponibilidade_temporaria(envelope: object):
    extrator = ExtratorGemini(settings_de_teste(), cliente_do_sdk(corpo_json_200(envelope)))

    with pytest.raises(AvaliadorIndisponivel, match="fora do formato da API") as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida | FalhaInternaDoAvaliador)


@pytest.mark.parametrize(
    "envelope",
    [
        pytest.param(
            {"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"}}, id="pedido-barrado"
        ),
        pytest.param({"candidates": [{"finishReason": "SAFETY"}]}, id="resposta-barrada"),
        pytest.param(
            {"candidates": [{"content": {"role": "model"}, "finishReason": "MAX_TOKENS"}]},
            id="sem-partes",
        ),
        pytest.param({"candidates": []}, id="sem-candidatos"),
    ],
)
def test_envelope_sem_texto_segue_como_erro_do_lote_que_se_divide(envelope: dict):
    extrator = ExtratorGemini(settings_de_teste(), cliente_do_sdk(corpo_json_200(envelope)))

    with pytest.raises(ErroDeAvaliacao, match="resposta vazia") as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, ErroTemporarioDeAvaliacao)


def gzip_corrompido(requisicao: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        headers={"content-encoding": "gzip", "content-type": "application/json"},
        content=b"isto nao e gzip",
    )


def redirect_sem_fim(requisicao: httpx.Request) -> httpx.Response:
    return httpx.Response(302, headers={"location": "https://exemplo.invalido/de-novo"})


def cliente_que_segue_redirect(responder: Callable[[httpx.Request], httpx.Response]):
    return genai.Client(
        api_key="gemini-de-teste",
        http_options=types.HttpOptions(
            httpx_client=httpx.Client(
                transport=httpx.MockTransport(responder), follow_redirects=True
            )
        ),
    )


@pytest.mark.parametrize(
    ("cliente", "trecho"),
    [
        pytest.param(
            lambda: cliente_do_sdk(gzip_corrompido), "Falha de rede", id="gzip-corrompido"
        ),
        pytest.param(
            lambda: cliente_que_segue_redirect(redirect_sem_fim),
            "Falha de rede",
            id="redirect-sem-fim",
        ),
        pytest.param(
            lambda: cliente_do_sdk(
                corpo_json_200({"candidates": [{"content": {"parts": {"text": "oi"}}}]})
            ),
            "fora do formato da API",
            id="partes-objeto",
        ),
    ],
)
def test_resposta_que_o_sdk_nao_consegue_ler_e_indisponibilidade_temporaria(
    cliente: Callable[[], genai.Client], trecho: str
):
    extrator = ExtratorGemini(settings_de_teste(), cliente())

    with pytest.raises(AvaliadorIndisponivel, match=trecho) as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida | FalhaInternaDoAvaliador)


def test_erro_ao_montar_o_pedido_nao_vira_indisponibilidade():
    cliente = cliente_do_sdk(corpo_json_200(envelope_valido()))

    with pytest.raises(TypeError):
        gerar_json(cliente, MODELO_DE_TESTE, "prompt", ExtracoesDeVagas, None)


def test_erro_de_corpo_que_nao_e_json_mostra_o_inicio_do_corpo():
    extrator = ExtratorGemini(settings_de_teste(), cliente_do_sdk(corpo_200(HTML_DE_PROXY)))

    with pytest.raises(AvaliadorIndisponivel, match="502 Bad Gateway"):
        extrator.extrair([vaga_exemplo()])


class RespostasEmSequencia:
    def __init__(self, *respostas: Callable[[httpx.Request], httpx.Response]) -> None:
        self._respostas = list(respostas)
        self.lotes: list[list[str]] = []
        self.segundos = 0.0

    def __call__(self, requisicao: httpx.Request) -> httpx.Response:
        self.lotes.append(ids_no_prompt(requisicao))
        self.segundos += 30
        responder = self._respostas.pop(0) if len(self._respostas) > 1 else self._respostas[0]
        return responder(requisicao)

    def esperar(self, segundos: float) -> None:
        self.segundos += segundos


def test_corpo_que_nao_e_json_espera_e_repete_o_mesmo_lote_sem_dividir():
    respostas = RespostasEmSequencia(corpo_200(HTML_DE_PROXY), extraindo_as_vagas_do_prompt)
    esperas: list[float] = []
    em_lotes = ExtratorEmLotes(
        ExtratorGemini(settings_de_teste(), cliente_do_sdk(respostas)), 10, esperar=esperas.append
    )

    extraidas = em_lotes.extrair([vaga_exemplo(1), vaga_exemplo(2)])

    assert [item.id_vaga for item in extraidas] == ["adzuna:1", "adzuna:2"]
    assert respostas.lotes == [["adzuna:1", "adzuna:2"], ["adzuna:1", "adzuna:2"]]
    assert esperas == [ESPERA_PADRAO_EM_SEGUNDOS + MARGEM_DE_ESPERA_EM_SEGUNDOS]


def test_corpo_que_nao_e_json_persistente_para_sem_dividir_nem_furar_o_prazo():
    respostas = RespostasEmSequencia(extraindo_as_vagas_do_prompt, corpo_200(HTML_DE_PROXY))
    em_lotes = ExtratorEmLotes(
        ExtratorGemini(settings_de_teste(), cliente_do_sdk(respostas)),
        10,
        esperar=respostas.esperar,
        prazo_em_segundos=600,
        timeout_da_chamada_em_segundos=120,
        relogio=lambda: respostas.segundos,
    )

    extraidas = em_lotes.extrair([vaga_exemplo(numero) for numero in range(1, 31)])

    assert [item.id_vaga for item in extraidas] == [f"adzuna:{numero}" for numero in range(1, 11)]
    assert all(len(lote) == 10 for lote in respostas.lotes)
    assert respostas.segundos <= 600
