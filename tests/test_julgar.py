from datetime import UTC, datetime
from uuid import UUID

from radar.avaliacao.julgar import TAMANHO_DO_LOTE, amostrar, julgar_entregas
from radar.avaliacao.prompt import apenas_das_vagas
from radar.domain.models import (
    EntregaParaJulgar,
    Julgamento,
    Modalidade,
    Perfil,
    ProblemaJulgado,
    ResultadoDoJulgamento,
    Vaga,
)
from radar.matching.errors import AvaliadorIndisponivel
from radar.reporting.julgamento import formatar_julgamento

PERFIL_A = UUID(int=1)
PERFIL_B = UUID(int=2)


def perfil(curso: str = "Engenharia de Software") -> Perfil:
    return Perfil(
        curso=curso,
        periodo=4,
        habilidades=["Python"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.HIBRIDO,
    )


def entrega(
    numero: int,
    perfil_id: UUID = PERFIL_A,
    nota: int | None = 80,
    feedback: str | None = None,
) -> EntregaParaJulgar:
    return EntregaParaJulgar(
        perfil_id=perfil_id,
        perfil=perfil("Direito" if perfil_id == PERFIL_B else "Engenharia de Software"),
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
        nota_do_radar=nota,
        feedback=feedback,
    )


class JuizFalso:
    def __init__(
        self,
        relevantes: set[str] = frozenset(),
        falhar_em: set[str] = frozenset(),
        omitir: set[str] = frozenset(),
    ):
        self.chamadas: list[tuple[str, list[str]]] = []
        self._relevantes = relevantes
        self._falhar_em = falhar_em
        self._omitir = omitir

    def julgar(self, perfil: Perfil, vagas: list[Vaga]) -> list[Julgamento]:
        ids = [vaga.id_externo for vaga in vagas]
        self.chamadas.append((perfil.curso, ids))
        if self._falhar_em & set(ids):
            raise AvaliadorIndisponivel("HTTP 503")
        julgamentos = [
            Julgamento(
                id_vaga=vaga.identidade(),
                relevante=vaga.id_externo in self._relevantes,
                nota_juiz=90 if vaga.id_externo in self._relevantes else 20,
                problema=ProblemaJulgado.NENHUM
                if vaga.id_externo in self._relevantes
                else ProblemaJulgado.OUTRA_AREA,
                motivo="motivo",
            )
            for vaga in vagas
            if vaga.id_externo not in self._omitir
        ]
        return apenas_das_vagas(julgamentos, vagas)


def test_julga_por_perfil_em_lotes_e_reune_os_resultados():
    entregas = [entrega(n) for n in range(1, TAMANHO_DO_LOTE + 2)] + [entrega(20, PERFIL_B)]
    juiz = JuizFalso(relevantes={"1", "20"})

    resultado = julgar_entregas(entregas, juiz, amostra=100, semente=1, modelo="m", dias=7)

    assert [curso for curso, _ in juiz.chamadas] == [
        "Engenharia de Software",
        "Engenharia de Software",
        "Direito",
    ]
    assert len(juiz.chamadas[0][1]) == TAMANHO_DO_LOTE
    assert len(resultado.julgadas) == len(entregas)
    assert resultado.sem_julgamento == 0
    assert resultado.entregas_no_periodo == len(entregas)
    assert resultado.amostradas == len(entregas)


def test_amostra_e_reprodutivel_e_menor_que_o_total():
    entregas = [entrega(n) for n in range(1, 31)]

    primeira = amostrar(entregas, 5, semente=7)
    segunda = amostrar(entregas, 5, semente=7)

    assert [e.vaga.id_externo for e in primeira] == [e.vaga.id_externo for e in segunda]
    assert len(primeira) == 5
    assert amostrar(entregas, 50, semente=7) == entregas


def test_lote_que_falha_e_id_omitido_contam_como_sem_julgamento():
    entregas = [entrega(1), entrega(2), entrega(3, PERFIL_B)]
    juiz = JuizFalso(relevantes={"1"}, falhar_em={"3"}, omitir={"2"})

    resultado = julgar_entregas(entregas, juiz, amostra=100, semente=1, modelo="m", dias=7)

    assert [item.entrega.vaga.id_externo for item in resultado.julgadas] == ["1"]
    assert resultado.sem_julgamento == 2


def test_relatorio_mede_relevancia_concordancia_e_reprovadas_com_nota_alta():
    entregas = [
        entrega(1, feedback="vaga_util"),
        entrega(2, feedback="vaga_irrelevante"),
        entrega(3, feedback="vaga_util"),
        entrega(4, nota=95),
        entrega(5, PERFIL_B, nota=None),
    ]
    resultado = julgar_entregas(
        entregas,
        JuizFalso(relevantes={"1", "2", "5"}),
        amostra=100,
        semente=1,
        modelo="juiz-x",
        dias=7,
    )

    texto = formatar_julgamento(resultado)

    assert "Juiz: juiz-x — 5 de 5 entregas dos últimos 7 dias julgadas" in texto
    assert "Relevantes segundo o juiz: 3/5 (60%)" in texto
    assert "Engenharia de Software (00000000): 2/4 relevantes" in texto
    assert "Direito (00000000): 1/1 relevantes" in texto
    assert "outra_area" in texto and "nenhum" in texto
    assert "1/3 concordam (33%)" in texto
    assert "discorda: Estágio 2 · pessoa disse vaga_irrelevante · juiz relevante" in texto
    assert "discorda: Estágio 3 · pessoa disse vaga_util · juiz irrelevante" in texto
    assert " 95 · 09/09 · Estágio 4 · outra_area: motivo" in texto
    assert "Radar —" in texto


def test_relatorio_sem_julgadas_e_sem_feedback():
    vazio = ResultadoDoJulgamento(modelo="m", dias=7, entregas_no_periodo=0, amostradas=0)
    assert "Nenhuma entrega julgada." in formatar_julgamento(vazio)

    resultado = julgar_entregas([entrega(1)], JuizFalso(relevantes={"1"}), 10, 1, "m", 7)
    texto = formatar_julgamento(resultado)
    assert "nenhuma entrega julgada tem feedback registrado" in texto
    assert "Reprovadas pelo juiz com nota do Radar ≥ 70:\n  nenhuma" in texto
