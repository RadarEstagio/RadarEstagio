from radar.domain.models import FunilDaCoorte

LARGURA_DO_ROTULO = 26


def formatar_funil(funil: FunilDaCoorte) -> str:
    linhas = [
        f"Funil da coorte — perfis criados nos últimos {funil.dias} dias",
        "",
        etapa("Perfis criados", funil.perfis_criados, funil.perfis_criados),
        etapa("Telegram vinculado", funil.perfis_vinculados, funil.perfis_criados),
        etapa("Primeira recomendação", funil.perfis_ativados, funil.perfis_criados),
        etapa("Abriram uma vaga", funil.perfis_com_vaga_aberta, funil.perfis_criados),
        etapa("Encontraram vaga útil", funil.perfis_com_vaga_util, funil.perfis_criados),
        etapa("Iniciaram candidatura", funil.perfis_com_candidatura, funil.perfis_criados),
        "",
        etapa("Vagas enviadas", funil.vagas_enviadas, funil.vagas_enviadas),
        etapa("Aberturas", funil.vagas_abertas, funil.vagas_enviadas),
        etapa("Úteis (união de sinais)", funil.vagas_uteis, funil.vagas_enviadas),
        etapa("Marcadas como irrelevantes", funil.vagas_irrelevantes, funil.vagas_enviadas),
        etapa("Candidaturas", funil.candidaturas, funil.vagas_enviadas),
        "",
        "Motivo da recusa:",
    ]
    linhas.extend(linhas_dos_motivos(funil))
    linhas.extend(["", linha_do_custo(funil)])
    etapas = [
        "landing_visualizada",
        "cta_cadastro_aberto",
        "etapa_perfil_concluida",
        "etapa_habilidades_concluida",
        "etapa_preferencias_concluida",
        "conta_criada",
        "email_confirmado",
        "perfil_salvo",
        "telegram_aberto",
        "telegram_vinculado",
        "primeira_recomendacao_enviada",
    ]
    aquisicao = ["Aquisição — primeira aparição no período (inclui sessões sem conta)"]
    aquisicao.extend(f"  {nome}: {funil.etapas.get(nome, 0)}" for nome in etapas)
    linhas.extend(["", "Utilidade semanal — semanas de Brasília; todos os ativados:"])
    for semana in funil.utilidade_semanal:
        percentual = semana.percentual()
        taxa = "sem denominador" if percentual is None else f"{percentual:.1f}%"
        parcial = " (em andamento)" if semana.parcial else ""
        linhas.append(
            f"  {semana.semana}{parcial}: {semana.com_utilidade}/{semana.ativados} — {taxa}"
        )
    linhas.extend(["", "Recusas por tecnologias declaradas — entregas no período:"])
    for grupo in funil.recusas_por_grupo:
        linhas.append(
            f"  {grupo.grupo}: {grupo.recusas}/{grupo.entregas} recusas "
            f"({100 * grupo.recusas / grupo.entregas:.1f}%); "
            f"nota: {grupo.recusas_da_nota}/{grupo.entregas}"
        )
    linhas.append("Candidatura: sem captura no piloto; contagem apenas de registros históricos.")
    return "\n".join(aquisicao + [""] + linhas)


def etapa(rotulo: str, valor: int, total: int) -> str:
    return f"{rotulo:<{LARGURA_DO_ROTULO}}{valor:>5}{proporcao(valor, total)}"


def proporcao(valor: int, total: int) -> str:
    if not total or valor == total:
        return ""
    return f"  ({round(100 * valor / total)}%)"


def linhas_dos_motivos(funil: FunilDaCoorte) -> list[str]:
    if not funil.recusas_por_motivo:
        return ["  nenhuma recusa registrada"]
    return [
        f"  {motivo:<{LARGURA_DO_ROTULO}}{total:>3}"
        for motivo, total in funil.recusas_por_motivo.items()
    ]


def linha_do_custo(funil: FunilDaCoorte) -> str:
    extraidas = funil.vagas_extraidas
    por_ativado = funil.vagas_extraidas_por_ativado()
    if por_ativado is None:
        return f"Custo: {extraidas} vagas extraídas, nenhum usuário ativado no período"
    return f"Custo: {extraidas} vagas extraídas, {por_ativado:.1f} por usuário ativado"
