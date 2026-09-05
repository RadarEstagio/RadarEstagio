from radar.domain.models import FunilDaCoorte
from radar.reporting.funil import formatar_funil


def funil(**mudancas) -> FunilDaCoorte:
    padrao = {
        "dias": 30,
        "perfis_criados": 12,
        "perfis_vinculados": 10,
        "perfis_ativados": 9,
        "perfis_com_vaga_aberta": 6,
        "perfis_com_vaga_util": 4,
        "perfis_com_candidatura": 3,
        "vagas_enviadas": 57,
        "vagas_abertas": 19,
        "vagas_uteis": 11,
        "vagas_irrelevantes": 7,
        "candidaturas": 3,
        "vagas_extraidas": 210,
        "recusas_por_motivo": {"motivo_exigencia": 4, "motivo_area": 2, "sem_motivo": 1},
    }
    return FunilDaCoorte(**{**padrao, **mudancas})


def test_mostra_cada_etapa_com_a_proporcao_sobre_os_perfis_criados():
    texto = formatar_funil(funil())

    assert "perfis criados nos últimos 30 dias" in texto
    assert "Telegram vinculado" in texto
    assert "(83%)" in texto
    assert "Primeira recomendação" in texto
    assert "(75%)" in texto
    assert "Abriram uma vaga" in texto
    assert "(50%)" in texto


def test_mostra_o_volume_de_vagas_com_a_proporcao_sobre_as_enviadas():
    texto = formatar_funil(funil())

    assert "Vagas enviadas" in texto
    assert "Aberturas" in texto
    assert "(33%)" in texto
    assert "Candidaturas" in texto


def test_quebra_as_recusas_por_motivo_na_ordem_recebida():
    texto = formatar_funil(funil())

    assert texto.index("motivo_exigencia") < texto.index("motivo_area")
    assert texto.index("motivo_area") < texto.index("sem_motivo")


def test_coorte_sem_recusa_diz_isso_em_vez_de_lista_vazia():
    texto = formatar_funil(funil(recusas_por_motivo={}))

    assert "nenhuma recusa registrada" in texto


def test_custo_e_dividido_pelos_usuarios_ativados():
    texto = formatar_funil(funil())

    assert "210 vagas extraídas" in texto
    assert "23.3 por usuário ativado" in texto


def test_custo_sem_ativados_nao_divide_por_zero():
    texto = formatar_funil(funil(perfis_ativados=0, perfis_com_vaga_aberta=0))

    assert "nenhum usuário ativado no período" in texto


def test_coorte_vazia_nao_calcula_proporcao():
    texto = formatar_funil(
        funil(
            perfis_criados=0,
            perfis_vinculados=0,
            perfis_ativados=0,
            perfis_com_vaga_aberta=0,
            perfis_com_vaga_util=0,
            perfis_com_candidatura=0,
            vagas_enviadas=0,
            vagas_abertas=0,
            vagas_uteis=0,
            vagas_irrelevantes=0,
            candidaturas=0,
            vagas_extraidas=0,
            recusas_por_motivo={},
        )
    )

    assert "%" not in texto


def test_utilidade_semanal_exibe_denominador_e_semana_incompleta():
    dados = funil(
        utilidade_semanal=[
            {"semana": "2026-09-07", "parcial": True, "ativados": 4, "com_utilidade": 1},
            {"semana": "2026-08-31", "parcial": False, "ativados": 0, "com_utilidade": 0},
        ]
    )
    texto = formatar_funil(dados)
    assert "2026-09-07 (em andamento): 1/4 — 25.0%" in texto
    assert "2026-08-31: 0/0 — sem denominador" in texto
    assert "sem captura no piloto" in texto
