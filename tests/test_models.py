import json
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from radar.domain.models import ExtracaoDaVaga, Modalidade, Perfil, ResultadoMatch, Usuario, Vaga
from radar.domain.perfil_fixo import perfil_de_exemplo


def vaga_exemplo() -> Vaga:
    return Vaga(
        id_externo="123",
        fonte="adzuna",
        titulo="Estágio em Desenvolvimento",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, RJ",
        descricao="Vaga de estágio para desenvolvimento web.",
        url="https://exemplo.com/vaga/123",
        publicada_em=datetime(2026, 8, 25, 8, 0),
    )


def test_vaga_nasce_sem_modalidade_informada():
    assert vaga_exemplo().modalidade is None


def test_vaga_aceita_modalidade_informada_pela_fonte():
    vaga = vaga_exemplo().model_copy(update={"modalidade": Modalidade.REMOTO})
    assert vaga.modalidade is Modalidade.REMOTO


def test_resultado_match_aceita_nota_nos_limites():
    for nota in (0, 100):
        resultado = ResultadoMatch(vaga=vaga_exemplo(), nota=nota)
        assert resultado.nota == nota


@pytest.mark.parametrize("nota", [-1, 101])
def test_resultado_match_rejeita_nota_fora_do_intervalo(nota):
    with pytest.raises(ValidationError):
        ResultadoMatch(vaga=vaga_exemplo(), nota=nota)


def test_resultado_match_alerta_pegadinha_e_opcional():
    resultado = ResultadoMatch(vaga=vaga_exemplo(), nota=80)
    assert resultado.alerta_pegadinha is None


def test_perfil_rejeita_modalidade_invalida():
    with pytest.raises(ValidationError):
        Perfil(
            curso="Engenharia de Software",
            periodo=4,
            habilidades=["Python"],
            cidade="Rio de Janeiro, RJ",
            modalidade="qualquer",
        )


def test_perfil_aceita_lista_de_habilidades_vazia():
    perfil = Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=[],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.REMOTO,
    )

    assert perfil.habilidades == []


def test_perfil_rejeita_habilidades_nulas():
    with pytest.raises(ValidationError):
        Perfil(
            curso="Engenharia de Software",
            periodo=4,
            habilidades=None,
            cidade="Rio de Janeiro, RJ",
            modalidade=Modalidade.REMOTO,
        )


def test_perfil_de_exemplo_e_valido():
    perfil = perfil_de_exemplo()
    assert perfil.modalidade is Modalidade.PRESENCIAL
    assert perfil.periodo >= 1
    assert perfil.habilidades
    assert perfil.nome_da_cidade() == "Rio de Janeiro"


def test_usuario_exige_chat_id_preenchido():
    with pytest.raises(ValidationError):
        Usuario(id=uuid4(), perfil=perfil_de_exemplo(), chat_id="")


def test_modalidade_reconhecida_aceita_acentos_e_caixa():
    extracao = ExtracaoDaVaga(id_vaga="1", area_da_vaga="computacao", modalidade="Híbrido")

    assert extracao.modalidade_reconhecida() is Modalidade.HIBRIDO


def test_modalidade_desconhecida_ou_ausente_vira_nenhuma():
    sem = ExtracaoDaVaga(id_vaga="1", area_da_vaga="computacao")
    invalida = ExtracaoDaVaga(id_vaga="1", area_da_vaga="computacao", modalidade="a combinar")

    assert sem.modalidade_reconhecida() is None
    assert invalida.modalidade_reconhecida() is None


@pytest.mark.parametrize("periodo", [0, -1, 13, 2028])
def test_periodo_minimo_fora_da_faixa_de_periodos_vira_nenhum(periodo):
    extracao = ExtracaoDaVaga.model_validate(
        {"id_vaga": "1", "area_da_vaga": "computacao", "periodo_minimo": periodo}
    )

    assert extracao.periodo_minimo is None


@pytest.mark.parametrize("periodo", [1, 7, 12])
def test_periodo_minimo_plausivel_e_mantido(periodo):
    extracao = ExtracaoDaVaga.model_validate(
        {"id_vaga": "1", "area_da_vaga": "computacao", "periodo_minimo": periodo}
    )

    assert extracao.periodo_minimo == periodo


def test_extracao_guardada_antes_do_registro_da_descricao_lida_fica_sem_origem():
    antiga = ExtracaoDaVaga.model_validate({"id_vaga": "1", "area_da_vaga": "computacao"})
    registrada = antiga.model_copy(update={"descricao_completa": False})

    assert antiga.descricao_completa is None
    assert ExtracaoDaVaga.model_validate(registrada.model_dump(mode="json")) == registrada


@pytest.mark.parametrize(
    ("lida_completa", "completa_hoje", "leu_menos"),
    [
        (False, True, True),
        (False, False, False),
        (True, True, False),
        (True, False, False),
        (None, True, False),
        (None, False, False),
    ],
)
def test_extracao_so_leu_menos_se_foi_feita_sobre_a_cortada_e_hoje_ha_a_completa(
    lida_completa, completa_hoje, leu_menos
):
    extracao = ExtracaoDaVaga(
        id_vaga="adzuna:1", area_da_vaga="computacao", descricao_completa=lida_completa
    )
    vaga = Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio",
        empresa="Empresa",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url="https://exemplo.com/1",
        publicada_em=datetime(2026, 9, 16),
        descricao_completa=completa_hoje,
    )

    assert extracao.leu_menos_que(vaga) is leu_menos


NUL = "\x00"
PRIMEIRA_METADE_DO_EMOJI = chr(0xD83D)
SEGUNDA_METADE_DO_EMOJI = chr(0xDE00)


def vaga_com(**campos: str) -> Vaga:
    return Vaga(**(vaga_exemplo().model_dump() | campos))


def test_vaga_recebida_perde_nul_e_metade_solta_de_emoji_em_todos_os_textos():
    vaga = vaga_com(
        id_externo=f"123{NUL}",
        titulo=f"Estágio{NUL} em Dados",
        empresa=f"Empresa {SEGUNDA_METADE_DO_EMOJI}Exemplo",
        localizacao=f"Rio de Janeiro, RJ{NUL}",
        descricao=f"Descrição cortada no emoji {PRIMEIRA_METADE_DO_EMOJI}",
        url=f"https://exemplo.com/vaga/123{NUL}",
    )

    assert vaga.id_externo == "123"
    assert vaga.titulo == "Estágio em Dados"
    assert vaga.empresa == "Empresa Exemplo"
    assert vaga.localizacao == "Rio de Janeiro, RJ"
    assert vaga.descricao == "Descrição cortada no emoji "
    assert vaga.url == "https://exemplo.com/vaga/123"


def test_limpeza_da_vaga_nao_mexe_em_emoji_acento_travessao_nem_html():
    texto = "Estágio – Dados — IA & <b>remoto</b> 😀 ação ’ � \t\n fim"
    vaga = vaga_com(titulo=texto, empresa=texto, localizacao=texto, descricao=texto)

    assert (vaga.titulo, vaga.empresa, vaga.localizacao, vaga.descricao) == (texto,) * 4
    assert vaga.chave() == vaga_exemplo().chave() == ("adzuna", "123")
    assert vaga.identidade() == "adzuna:123"


def test_as_duas_metades_de_um_emoji_viram_o_emoji_inteiro():
    vaga = vaga_com(descricao=f"Vaga {PRIMEIRA_METADE_DO_EMOJI}{SEGUNDA_METADE_DO_EMOJI} aberta")

    assert vaga.descricao == "Vaga 😀 aberta"


def test_extracao_da_ia_perde_nul_e_metade_solta_de_emoji_em_todos_os_textos():
    extracao = ExtracaoDaVaga.model_validate(
        {
            "id_vaga": f"adzuna:1{NUL}",
            "area_da_vaga": "computacao",
            "areas_da_vaga": [f"dados_ia{NUL}"],
            "cursos_aceitos": [f"Ciência da Computação{PRIMEIRA_METADE_DO_EMOJI}"],
            "habilidades_obrigatorias": [f"Python{NUL}", "SQL"],
            "habilidades_principais": [f"Excel {SEGUNDA_METADE_DO_EMOJI}avançado"],
            "habilidades_desejaveis": [f"Inglês{NUL} fluente"],
            "modalidade": f"remoto{NUL}",
            "alerta_pegadinha": f"Exige experiência {PRIMEIRA_METADE_DO_EMOJI}",
        }
    )

    assert extracao.id_vaga == "adzuna:1"
    assert extracao.areas_da_vaga == ["dados_ia"]
    assert extracao.cursos_aceitos == ["Ciência da Computação"]
    assert extracao.habilidades_obrigatorias == ["Python", "SQL"]
    assert extracao.habilidades_principais == ["Excel avançado"]
    assert extracao.habilidades_desejaveis == ["Inglês fluente"]
    assert extracao.modalidade == "remoto"
    assert extracao.alerta_pegadinha == "Exige experiência "


def test_nul_escapado_no_json_da_ia_nao_chega_a_extracao():
    resposta = json.dumps(
        {"id_vaga": "adzuna:1", "area_da_vaga": None, "habilidades_obrigatorias": [f"C#{NUL}"]}
    )

    extracao = ExtracaoDaVaga.model_validate_json(resposta)

    assert extracao.habilidades_obrigatorias == ["C#"]


def test_limpeza_da_extracao_nao_mexe_em_emoji_acento_nem_simbolo():
    textos = ["C# & .NET", "Inglês — avançado", "Comunicação 😀", "<Excel> ’ �"]
    extracao = ExtracaoDaVaga(
        id_vaga="adzuna:1",
        area_da_vaga=None,
        cursos_aceitos=textos,
        habilidades_obrigatorias=textos,
        alerta_pegadinha=textos[1],
    )

    assert extracao.cursos_aceitos == textos
    assert extracao.habilidades_obrigatorias == textos
    assert extracao.alerta_pegadinha == textos[1]
