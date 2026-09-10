from datetime import UTC, datetime
from uuid import UUID

from radar.avaliacao.descartes import (
    contar_por_motivo,
    descartes_do_prefiltro,
    exportar_descartes,
)
from radar.domain.models import Modalidade, Perfil, Usuario, Vaga


def vaga(numero: int, titulo: str, localizacao: str = "Rio de Janeiro, RJ") -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=titulo,
        empresa=f"Empresa {numero}",
        localizacao=localizacao,
        descricao="Vaga para estudantes.",
        url=f"https://exemplo.com/{numero}",
        publicada_em=datetime(2026, 9, 9, tzinfo=UTC),
        modalidade=Modalidade.PRESENCIAL,
    )


def usuario(numero: int = 1, curso: str = "Engenharia de Software") -> Usuario:
    return Usuario(
        id=UUID(int=numero),
        perfil=Perfil(
            curso=curso,
            periodo=4,
            habilidades=["Python"],
            cidade="Rio de Janeiro, RJ",
            modalidade=Modalidade.PRESENCIAL,
        ),
        chat_id=str(numero),
    )


def test_cada_descarte_carrega_o_motivo_do_pre_filtro():
    vagas = [
        vaga(1, "Estágio Sênior em Python"),
        vaga(2, "Estágio em Enfermagem"),
        vaga(3, "Analista de Sistemas"),
        vaga(4, "Estágio em Desenvolvimento", localizacao="Recife, PE"),
    ]

    descartes = descartes_do_prefiltro(vagas, [usuario()])

    assert [(descarte.vaga.id_externo, descarte.motivo) for descarte in descartes] == [
        ("1", "exige_senioridade"),
        ("2", "fora_da_area_do_curso"),
        ("3", "nao_e_estagio"),
        ("4", "localizacao_incompativel"),
    ]


def test_vaga_aprovada_nao_entra_nos_descartes():
    descartes = descartes_do_prefiltro([vaga(1, "Estágio em Desenvolvimento")], [usuario()])

    assert descartes == []


def test_um_descarte_por_perfil_afetado():
    vagas = [vaga(1, "Estágio em Enfermagem")]

    descartes = descartes_do_prefiltro(vagas, [usuario(1), usuario(2, curso="Enfermagem")])

    assert [descarte.usuario.id for descarte in descartes] == [UUID(int=1)]


def test_contagem_por_motivo_ordena_do_mais_frequente_para_o_menos():
    vagas = [
        vaga(1, "Estágio Sênior"),
        vaga(2, "Estágio para Especialista"),
        vaga(3, "Analista de Sistemas"),
    ]

    assert contar_por_motivo(descartes_do_prefiltro(vagas, [usuario()])) == {
        "exige_senioridade": 2,
        "nao_e_estagio": 1,
    }


def test_amostra_cobre_motivos_diferentes_antes_de_repetir_o_mesmo():
    vagas = [vaga(numero, "Estágio Sênior") for numero in range(1, 21)]
    vagas.append(vaga(99, "Analista de Sistemas"))

    itens = exportar_descartes(descartes_do_prefiltro(vagas, [usuario()]), amostra=2, semente=1)

    assert {item["motivo_do_descarte"] for item in itens} == {
        "exige_senioridade",
        "nao_e_estagio",
    }


def test_exportacao_sai_pronta_para_rotular_a_mao():
    descartes = descartes_do_prefiltro([vaga(1, "Estágio em Enfermagem")], [usuario()])

    item = exportar_descartes(descartes, amostra=10, semente=1)[0]

    assert item["descarte_correto"] is None
    assert item["motivo_do_descarte"] == "fora_da_area_do_curso"
    assert item["curso"] == "Engenharia de Software"
    assert item["titulo"] == "Estágio em Enfermagem"
    assert item["url"] == "https://exemplo.com/1"


def test_amostra_com_a_mesma_semente_devolve_os_mesmos_descartes():
    vagas = [vaga(numero, "Estágio Sênior") for numero in range(1, 30)]
    descartes = descartes_do_prefiltro(vagas, [usuario()])

    primeira = exportar_descartes(descartes, amostra=5, semente=7)
    segunda = exportar_descartes(descartes, amostra=5, semente=7)

    assert primeira == segunda
