from datetime import UTC, date, datetime
from uuid import UUID

from radar.avaliacao.descartes import DescarteDoPreFiltro, exportar_descartes
from radar.avaliacao.gabarito import exportar_gabarito
from radar.avaliacao.prompt import descrever_vagas
from radar.domain.datas import data_de_publicacao, data_local
from radar.domain.models import (
    EntregaJulgada,
    EntregaParaJulgar,
    Julgamento,
    Modalidade,
    Perfil,
    ProblemaJulgado,
    ResultadoDoJulgamento,
    Usuario,
    Vaga,
)
from radar.reporting.julgamento import formatar_julgamento

AS_22H_DE_09_09_EM_BRASILIA = datetime(2026, 9, 10, 1, 0, tzinfo=UTC)
DIA_EM_BRASILIA = "09/09"


def perfil() -> Perfil:
    return Perfil(
        curso="Direito",
        periodo=3,
        habilidades=["Redação"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )


def vaga_da_noite() -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio Jurídico",
        empresa="Escritório",
        localizacao="Rio de Janeiro, RJ",
        descricao="Estágio para estudantes de Direito.",
        url="https://exemplo.com/1",
        publicada_em=AS_22H_DE_09_09_EM_BRASILIA,
    )


def entrega_da_noite() -> EntregaParaJulgar:
    return EntregaParaJulgar(
        perfil_id=UUID(int=1),
        perfil=perfil(),
        vaga=vaga_da_noite(),
        enviada_em=AS_22H_DE_09_09_EM_BRASILIA,
        nota_do_radar=80,
    )


def test_data_local_devolve_o_dia_de_brasilia():
    assert data_local(AS_22H_DE_09_09_EM_BRASILIA) == date(2026, 9, 9)


def test_data_de_publicacao_com_hora_usa_brasilia():
    assert data_de_publicacao(AS_22H_DE_09_09_EM_BRASILIA) == date(2026, 9, 9)


def test_data_de_publicacao_sem_hora_mantem_o_dia_informado_pela_fonte():
    assert data_de_publicacao(datetime(2026, 9, 10, tzinfo=UTC)) == date(2026, 9, 10)


def test_prompt_do_juiz_mostra_a_publicacao_no_dia_de_brasilia():
    assert f"publicada em: {DIA_EM_BRASILIA}/2026" in descrever_vagas([vaga_da_noite()])


def test_exportacao_de_descartes_grava_a_publicacao_no_dia_de_brasilia():
    usuario = Usuario(id=UUID(int=1), perfil=perfil(), chat_id="1")
    descartes = [DescarteDoPreFiltro(usuario, vaga_da_noite(), "fora_da_area_do_curso")]

    item = exportar_descartes(descartes, amostra=1, semente=1)[0]

    assert item["publicada_em"] == "2026-09-09"


def test_exportacao_do_gabarito_grava_a_entrega_no_dia_de_brasilia():
    item = exportar_gabarito([entrega_da_noite()], amostra=1, semente=1)[0]

    assert item["enviada_em"] == "2026-09-09"


def test_relatorio_do_juiz_mostra_a_entrega_no_dia_de_brasilia():
    reprovada = EntregaJulgada(
        entrega=entrega_da_noite(),
        julgamento=Julgamento(
            id_vaga="adzuna:1",
            relevante=False,
            nota_juiz=10,
            problema=ProblemaJulgado.OUTRA_AREA,
            motivo="outra formação",
        ),
    )
    resultado = ResultadoDoJulgamento(
        modelo="m", dias=7, entregas_no_periodo=1, amostradas=1, julgadas=[reprovada]
    )

    assert f" · {DIA_EM_BRASILIA} · " in formatar_julgamento(resultado)
