from radar.domain.metricas import agrupar_utilidade_por_area
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
        "recomendacoes_elegiveis_feedback": 10,
        "recomendacoes_com_feedback": 3,
        "perfis_na_coorte": 3,
        "perfis_sem_entrega": 1,
        "mediana_segundos_ate_entrega": 120,
        "perfis_sem_abertura": 2,
        "mediana_segundos_ate_abertura": 300,
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


def test_mostra_participacao_no_feedback_a_partir_das_contagens():
    texto = formatar_funil(funil())

    assert "Respostas: 3 de 10 recomendações (30.0%)" in texto


def test_feedback_sem_entregas_mostra_ausencia_de_denominador():
    texto = formatar_funil(funil(recomendacoes_elegiveis_feedback=0, recomendacoes_com_feedback=0))

    assert "Respostas: 0 de 0 recomendações (sem denominador)" in texto


def test_agrega_utilidade_por_area_do_curso_atual_sem_duplicar_perfil():
    grupos = agrupar_utilidade_por_area(
        [
            {
                "semana": "2026-09-07",
                "parcial": False,
                "perfil_id": "1",
                "curso": "Computação",
                "com_utilidade": True,
            },
            {
                "semana": "2026-09-07",
                "parcial": False,
                "perfil_id": "2",
                "curso": "Ciência da Computação",
                "com_utilidade": False,
            },
            {
                "semana": "2026-09-07",
                "parcial": False,
                "perfil_id": "3",
                "curso": "Direito",
                "com_utilidade": True,
            },
            {
                "semana": "2026-09-07",
                "parcial": False,
                "perfil_id": "4",
                "curso": "Curso livre",
                "com_utilidade": False,
            },
        ]
    )

    assert [grupo.model_dump() for grupo in grupos] == [
        {
            "semana": "2026-09-07",
            "parcial": False,
            "area": "computacao",
            "ativados": 2,
            "com_utilidade": 1,
        },
        {
            "semana": "2026-09-07",
            "parcial": False,
            "area": "direito",
            "ativados": 1,
            "com_utilidade": 1,
        },
        {
            "semana": "2026-09-07",
            "parcial": False,
            "area": "Não classificado",
            "ativados": 1,
            "com_utilidade": 0,
        },
    ]


def test_relatorio_mostra_utilidade_por_area_e_ressalva_curso_atual():
    texto = formatar_funil(
        funil(
            utilidade_por_area=[
                {
                    "semana": "2026-09-07",
                    "parcial": False,
                    "area": "computacao",
                    "ativados": 2,
                    "com_utilidade": 1,
                },
                {
                    "semana": "2026-09-07",
                    "parcial": False,
                    "area": "direito",
                    "ativados": 1,
                    "com_utilidade": 1,
                },
                {
                    "semana": "2026-09-07",
                    "parcial": False,
                    "area": "Não classificado",
                    "ativados": 1,
                    "com_utilidade": 0,
                },
            ]
        )
    )

    assert "Utilidade semanal por área — agrupado pelo curso atual:" in texto
    assert "2026-09-07 · computacao: 1/2 — 50.0%" in texto
    assert "2026-09-07 · direito: 1/1 — 100.0%" in texto
    assert "2026-09-07 · Não classificado: 0/1 — 0.0%" in texto
    assert "Mudança de curso pode mudar agrupamentos passados" in texto


def test_relatorio_mostra_situacao_atual_das_contas_pausadas():
    texto = formatar_funil(
        funil(
            pausas_atuais=[
                {"motivo": "conseguiu_estagio", "total": 1},
                {"motivo": "sem_vagas_uteis", "total": 1},
                {"motivo": "sem_motivo", "total": 2},
            ]
        )
    )

    pausas = texto.split("Contas pausadas — situação atual:")[1]

    assert "conseguiu_estagio" in pausas
    assert "sem_vagas_uteis" in pausas
    assert "Não informado" in pausas
    assert "sem_motivo" not in pausas
    assert "Este quadro não é histórico mensal de churn." in texto


def test_relatorio_indica_quando_nao_ha_contas_pausadas():
    texto = formatar_funil(funil(pausas_atuais=[]))

    assert "nenhuma conta pausada" in texto


def test_mostra_mediana_e_faltantes_sem_chamar_isso_de_prazo():
    texto = formatar_funil(funil())

    assert "Tempo observado — não é prazo prometido:" in texto
    assert "Até primeira entrega: 2.0 min (2 observados; 1 sem entrega)" in texto
    assert "Até primeira abertura: 5.0 min (1 observado; 2 sem abertura)" in texto


def test_mediana_longa_aparece_em_unidade_legivel():
    texto = formatar_funil(
        funil(mediana_segundos_ate_entrega=0, mediana_segundos_ate_abertura=90000)
    )

    assert "Até primeira entrega: 0 s" in texto
    assert "Até primeira abertura: 1.0 d" in texto


def test_tempo_sem_observacoes_fica_indisponivel():
    texto = formatar_funil(
        funil(
            perfis_na_coorte=2,
            perfis_sem_entrega=2,
            mediana_segundos_ate_entrega=None,
            perfis_sem_abertura=2,
            mediana_segundos_ate_abertura=None,
        )
    )

    assert "Até primeira entrega: indisponível (0 observados; 2 sem entrega)" in texto
    assert "Até primeira abertura: indisponível (0 observados; 2 sem abertura)" in texto


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
            recomendacoes_elegiveis_feedback=0,
            recomendacoes_com_feedback=0,
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


def test_recusas_sem_entregas_exibem_ausencia_de_denominador():
    texto = formatar_funil(
        funil(
            recusas_por_grupo=[
                {
                    "grupo": "sem_extracao",
                    "entregas": 0,
                    "recusas": 0,
                    "recusas_da_nota": 0,
                }
            ]
        )
    )
    assert "0/0 recusas (sem denominador)" in texto
