import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from radar.avaliacao.gabarito import (
    carregar_gabarito,
    exportar_gabarito,
    gravar_gabarito,
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
        (PERFIL, itens[0]["id_externo"]): True,
        (PERFIL, itens[1]["id_externo"]): False,
    }
    assert json.loads(caminho.read_text())[2]["relevante"] is None


def test_seleciona_so_as_entregas_rotuladas_e_mede_a_concordancia():
    entregas = [entrega(n) for n in range(1, 5)]
    rotulos = {(PERFIL, "1"): True, (PERFIL, "2"): False, (PERFIL, "3"): True}

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
