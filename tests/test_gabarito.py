import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from radar.avaliacao.gabarito import (
    carregar_gabarito,
    exportar_gabarito,
    gravar_gabarito,
    rotulos_fora_da_janela,
    selecionar_do_gabarito,
)
from radar.avaliacao.julgar import julgar_entregas
from radar.domain.models import EntregaParaJulgar, Modalidade, Perfil, Vaga
from radar.reporting.julgamento import formatar_julgamento
from radar.storage.errors import ErroDeArmazenamento
from tests.test_julgar import JuizFalso

PERFIL = UUID(int=1)


def entrega(numero: int) -> EntregaParaJulgar:
    return EntregaParaJulgar(
        perfil_id=PERFIL,
        perfil=Perfil(
            curso="Direito",
            periodo=3,
            habilidades=["Redação"],
            cidade="Rio de Janeiro, RJ",
            modalidade=Modalidade.REMOTO,
        ),
        vaga=Vaga(
            id_externo=str(numero),
            fonte="adzuna",
            titulo=f"Estágio {numero}",
            empresa="Empresa",
            localizacao="Rio de Janeiro, RJ",
            descricao="d",
            url=f"https://exemplo.com/{numero}",
            publicada_em=datetime(2026, 9, 9, tzinfo=UTC),
        ),
        enviada_em=datetime(2026, 9, 9, 10, tzinfo=UTC),
        nota_do_radar=70,
    )


def test_exporta_amostra_com_campos_para_rotular_e_le_de_volta(tmp_path: Path):
    caminho = tmp_path / "gabarito.json"
    itens = exportar_gabarito([entrega(n) for n in range(1, 6)], amostra=3, semente=1)

    assert len(itens) == 3
    assert itens[0]["relevante"] is None
    assert set(itens[0]) >= {"perfil_id", "id_externo", "titulo", "url", "nota_do_radar"}

    itens[0]["relevante"] = True
    itens[1]["relevante"] = False
    gravar_gabarito(itens, caminho)
    rotulos = carregar_gabarito(caminho)

    assert rotulos == {
        (PERFIL, "adzuna", itens[0]["id_externo"]): True,
        (PERFIL, "adzuna", itens[1]["id_externo"]): False,
    }
    assert json.loads(caminho.read_text())[2]["relevante"] is None


def test_seleciona_so_as_entregas_rotuladas_e_mede_a_concordancia():
    entregas = [entrega(n) for n in range(1, 5)]
    rotulos = {
        (PERFIL, "adzuna", "1"): True,
        (PERFIL, "adzuna", "2"): False,
        (PERFIL, "adzuna", "3"): True,
    }

    escolhidas = selecionar_do_gabarito(entregas, rotulos)
    resultado = julgar_entregas(escolhidas, JuizFalso(relevantes={"1", "2"}), 10, 1, "m", 7)
    texto = formatar_julgamento(resultado, rotulos)

    assert [e.vaga.id_externo for e in escolhidas] == ["1", "2", "3"]
    assert "Concordância com o gabarito humano:\n  1/3 concordam (33%)" in texto
    assert "discorda: Estágio 2 · pessoas disseram irrelevante · juiz (nenhum)" in texto
    assert "discorda: Estágio 3 · pessoas disseram relevante · juiz (outra_area)" in texto


def test_sem_gabarito_o_relatorio_nao_menciona_humanos():
    resultado = julgar_entregas([entrega(1)], JuizFalso(relevantes={"1"}), 10, 1, "m", 7)

    assert "gabarito" not in formatar_julgamento(resultado)
    assert "nenhuma entrega julgada está no gabarito" in formatar_julgamento(resultado, {})


def test_gabarito_ausente_ou_quebrado_vira_erro_claro(tmp_path: Path):
    with pytest.raises(ErroDeArmazenamento, match="não encontrado"):
        carregar_gabarito(tmp_path / "nao-existe.json")

    quebrado = tmp_path / "quebrado.json"
    quebrado.write_text("{isso nao e json")
    with pytest.raises(ErroDeArmazenamento, match="JSON"):
        carregar_gabarito(quebrado)

    sem_campos = tmp_path / "sem-campos.json"
    sem_campos.write_text('[{"titulo": "x", "relevante": true}]')
    with pytest.raises(ErroDeArmazenamento, match="perfil_id"):
        carregar_gabarito(sem_campos)


def test_conta_os_rotulos_que_ficaram_fora_da_janela_de_dias():
    rotulos = {
        (UUID(int=1), "adzuna", "1"): True,
        (UUID(int=1), "adzuna", "2"): False,
        (UUID(int=2), "adzuna", "3"): True,
    }

    assert rotulos_fora_da_janela(rotulos, []) == 3
    assert rotulos_fora_da_janela(rotulos, [entrega(1)]) == 2


def test_gabarito_inteiro_dentro_da_janela_nao_gera_aviso():
    rotulos = {(UUID(int=1), "adzuna", "1"): True}

    assert rotulos_fora_da_janela(rotulos, [entrega(1)]) == 0


def entrega_de(numero: int, fonte: str) -> EntregaParaJulgar:
    base = entrega(numero)
    return base.model_copy(update={"vaga": base.vaga.model_copy(update={"fonte": fonte})})


def test_rotulo_fora_da_janela_nao_some_quando_duas_fontes_repetem_o_id():
    rotulos = {(PERFIL, "adzuna", "1"): True, (PERFIL, "adzuna", "2"): False}
    dentro = [entrega_de(1, "adzuna"), entrega_de(1, "gupy")]

    assert rotulos_fora_da_janela(rotulos, dentro) == 1


def test_contagem_de_rotulos_fora_nunca_fica_negativa():
    rotulos = {(PERFIL, "adzuna", "1"): True}
    dentro = [entrega_de(1, "adzuna"), entrega_de(1, "gupy")]

    assert rotulos_fora_da_janela(rotulos, dentro) == 0


def test_rotulos_fora_mais_rotulos_com_entrega_somam_o_gabarito():
    rotulos = {(PERFIL, "adzuna", str(n)): True for n in range(1, 6)}
    dentro = [entrega_de(1, "adzuna"), entrega_de(1, "gupy"), entrega_de(3, "adzuna")]
    com_entrega = {e.chave() for e in dentro}

    assert rotulos_fora_da_janela(rotulos, dentro) + len(com_entrega & rotulos.keys()) == 5


def test_rotulo_de_uma_fonte_nao_seleciona_a_vaga_de_outra_com_o_mesmo_id():
    rotulos = {(PERFIL, "adzuna", "1"): True}
    entregas = [entrega_de(1, "adzuna"), entrega_de(1, "gupy")]

    escolhidas = selecionar_do_gabarito(entregas, rotulos)

    assert [e.vaga.fonte for e in escolhidas] == ["adzuna"]


def test_relatorio_aplica_o_rotulo_humano_a_uma_entrega_so():
    entregas = [entrega_de(1, "adzuna"), entrega_de(1, "gupy")]
    rotulos = {(PERFIL, "adzuna", "1"): True}
    resultado = julgar_entregas(entregas, JuizFalso(relevantes={"1"}), 10, 1, "m", 7)

    assert "1/1 concordam" in formatar_julgamento(resultado, rotulos)


def test_item_do_gabarito_sem_a_fonte_vira_erro_claro(tmp_path: Path):
    arquivo = tmp_path / "gabarito-antigo.json"
    arquivo.write_text(
        json.dumps([{"perfil_id": str(PERFIL), "id_externo": "1", "relevante": True}])
    )

    with pytest.raises(ErroDeArmazenamento, match="fonte"):
        carregar_gabarito(arquivo)
