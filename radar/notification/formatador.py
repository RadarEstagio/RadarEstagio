import re
from datetime import datetime
from html import escape
from urllib.parse import urlsplit

from radar.domain.datas import data_de_publicacao, data_local
from radar.domain.models import (
    BotaoDeFeedback,
    MotivoDeRecusa,
    PerguntaDeFeedback,
    Recomendacao,
    Vaga,
)

LIMITE_DE_CARACTERES_DO_TELEGRAM = 4096
MAXIMO_DE_PONTOS_EXIBIDOS = 3
LIMITE_DO_TITULO = 120
LIMITE_DA_EMPRESA = 80
LIMITE_DA_LOCALIZACAO = 80
LIMITE_DO_REQUISITO = 60
LIMITE_DO_PONTO = 80
LIMITE_DO_AVISO = 120
LIMITE_DO_ALERTA = 160
RETICENCIAS = "…"
PADRAO_ENTIDADE_INCOMPLETA = re.compile(r"&[#a-zA-Z0-9]*$")
PADRAO_DE_ESPACOS = re.compile(r"\s+")
MAXIMO_DE_REQUISITOS_EXIBIDOS = 8
SEPARADOR_ENTRE_VAGAS = "\n\n───────────────\n\n"
PARAMETRO_DO_TOKEN = "t"
PREFIXO_DE_SUBDOMINIO_IGNORADO = "www."
NUMEROS_POR_LINHA = 5
ACAO_DE_RECUSA = "feedback"
FONTE_ADZUNA = "adzuna"
URL_DA_ADZUNA = "https://www.adzuna.com.br"
PROPORCAO_DE_ALERTA_DA_COTA = 0.8
ATRIBUICAO_DA_ADZUNA = f'<a href="{URL_DA_ADZUNA}">Jobs</a> by <a href="{URL_DA_ADZUNA}">Adzuna</a>'
TEXTO_DA_PERGUNTA = "Deixe seu feedback 👇"
ROTULOS_DE_MOTIVO = {
    MotivoDeRecusa.NOTA: "A nota não fez sentido",
    MotivoDeRecusa.AREA: "Não é da minha área",
    MotivoDeRecusa.EXIGENCIA: "Pedem demais",
    MotivoDeRecusa.LOGISTICA: "Local ou modalidade",
    MotivoDeRecusa.REPETIDA: "Já vi essa",
}
ROTULOS_MODALIDADE = {
    "remoto": "Remoto",
    "presencial": "Presencial",
    "hibrido": "Híbrido",
    "indiferente": "Indiferente",
}


def escapar_limitado(texto: str, limite: int) -> str:
    escapado = escape(PADRAO_DE_ESPACOS.sub(" ", texto).strip())
    if len(escapado) <= limite:
        return escapado
    cortado = PADRAO_ENTIDADE_INCOMPLETA.sub("", escapado[:limite])
    return cortado.rstrip() + RETICENCIAS


def ranquear(recomendacoes: list[Recomendacao]) -> list[Recomendacao]:
    return sorted(recomendacoes, key=lambda recomendacao: recomendacao.resultado.nota, reverse=True)


def formatar_mensagem(
    recomendacoes: list[Recomendacao], momento: datetime, url_de_rastreio: str = ""
) -> str:
    ranqueadas = ranquear(recomendacoes)
    blocos = [
        formatar_vaga(posicao, recomendacao, url_de_rastreio)
        for posicao, recomendacao in enumerate(ranqueadas, start=1)
    ]
    return cabecalho(momento) + "\n\n" + SEPARADOR_ENTRE_VAGAS.join(blocos)


def formatar_pergunta_de_feedback(recomendacoes: list[Recomendacao]) -> PerguntaDeFeedback:
    ranqueadas = ranquear(recomendacoes)
    numeros = [
        BotaoDeFeedback(rotulo=str(posicao), dados=f"{ACAO_DE_RECUSA}:{recomendacao.token}")
        for posicao, recomendacao in enumerate(ranqueadas, start=1)
    ]
    linhas = [
        numeros[inicio : inicio + NUMEROS_POR_LINHA]
        for inicio in range(0, len(numeros), NUMEROS_POR_LINHA)
    ]
    return PerguntaDeFeedback(texto=TEXTO_DA_PERGUNTA, linhas_de_botoes=linhas)


def formatar_motivos_da_recusa(token: str) -> list[list[BotaoDeFeedback]]:
    return [
        [BotaoDeFeedback(rotulo=rotulo, dados=f"{motivo.value}:{token}")]
        for motivo, rotulo in ROTULOS_DE_MOTIVO.items()
    ]


def formatar_mensagem_sem_vagas(momento: datetime, dias_de_silencio: int | None = None) -> str:
    mensagem = (
        f"{cabecalho(momento)}\n\n"
        "Nenhuma vaga nova compatível com o seu perfil hoje.\n"
        "O Radar volta a procurar amanhã de manhã."
    )
    if dias_de_silencio is None:
        return mensagem
    return (
        f"{mensagem}\n\n"
        f"Já são {dias_de_silencio} dias sem nenhuma recomendação. "
        "Perfis presenciais restritos a uma cidade recebem menos vagas do que perfis "
        "que também aceitam remoto ou híbrido."
    )


def cabecalho(momento: datetime) -> str:
    return f"📡 <b>Radar de Estágio</b> — {data_local(momento):%d/%m/%Y}"


def formatar_milhar(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


def formatar_resumo_da_execucao(
    momento: datetime,
    usuarios: int,
    atendidos: int,
    vagas_enviadas: int,
    vagas_coletadas: int,
    requisicoes: int,
    falhas_de_revalidacao: int = 0,
    sem_entrega_por_revalidacao: int = 0,
    vagas_sem_extracao: int = 0,
    extracoes_nao_gravadas: int = 0,
    adzuna_hoje: int | None = None,
    adzuna_no_mes: int | None = None,
    adzuna_limite: int | None = None,
    adzuna_esgotada: bool = False,
) -> str:
    linhas = [
        f"🛠️ <b>Radar — execução de {data_local(momento):%d/%m/%Y}</b>",
        f"Usuários ativos: {usuarios}",
        f"Receberam recomendação: {atendidos}",
        f"Vagas enviadas: {vagas_enviadas}",
        f"Vagas coletadas: {vagas_coletadas}",
        f"Requisições ao avaliador: {requisicoes}",
        f"Usuários com falha de revalidação: {falhas_de_revalidacao}",
        f"Sem entrega por falha de revalidação: {sem_entrega_por_revalidacao}",
    ]
    if vagas_sem_extracao:
        linhas.append(f"⚠️ Vagas sem extração (cota ou avaliador fora): {vagas_sem_extracao}")
    if extracoes_nao_gravadas:
        linhas.append(f"⚠️ Extrações não gravadas no banco: {extracoes_nao_gravadas}")
    if adzuna_hoje is not None and adzuna_no_mes is not None and adzuna_limite:
        linhas.append(
            f"Requisições à Adzuna: {formatar_milhar(adzuna_hoje)} hoje, "
            f"{formatar_milhar(adzuna_no_mes)} de {formatar_milhar(adzuna_limite)} no mês "
            f"({round(100 * adzuna_no_mes / adzuna_limite)}%)"
        )
        if adzuna_no_mes >= PROPORCAO_DE_ALERTA_DA_COTA * adzuna_limite:
            linhas.append(f"⚠️ Adzuna passou de {PROPORCAO_DE_ALERTA_DA_COTA:.0%} do limite mensal")
    if adzuna_esgotada:
        linhas.append("⚠️ Cota da Adzuna esgotada: a coleta parou antes do fim")
    return "\n".join(linhas)


def formatar_falha_da_execucao(momento: datetime, erro: str) -> str:
    return f"🛠️ <b>Radar — execução de {data_local(momento):%d/%m/%Y} falhou</b>\n{escape(erro)}"


def formatar_vaga(posicao: int, recomendacao: Recomendacao, url_de_rastreio: str = "") -> str:
    resultado = recomendacao.resultado
    vaga = resultado.vaga
    linhas = [
        f"<b>{posicao}. {escapar_limitado(vaga.titulo, LIMITE_DO_TITULO)}</b>"
        f" — {escapar_limitado(vaga.empresa, LIMITE_DA_EMPRESA)}",
        f"📍 {escapar_limitado(vaga.localizacao, LIMITE_DA_LOCALIZACAO)}"
        f" · {escape(rotulo_modalidade(vaga))}",
        f"🏷️ {rotulo_da_origem(vaga)}"
        f" · Publicada em {data_de_publicacao(vaga.publicada_em):%d/%m/%Y}",
        f"⭐ <b>Nota {resultado.nota}/100</b>",
    ]
    if resultado.requisitos_atendidos:
        linhas.append(
            f"✅ <b>Requisitos atendidos:</b> {formatar_requisitos(resultado.requisitos_atendidos)}"
        )
    if resultado.requisitos_nao_atendidos:
        linhas.append(
            "🔎 <b>Requisitos a conferir no seu perfil:</b> "
            f"{formatar_requisitos(resultado.requisitos_nao_atendidos)}"
        )
    if resultado.diferenciais_nao_atendidos:
        linhas.append(
            "✨ <b>Diferenciais que a vaga cita:</b> "
            f"{formatar_requisitos(resultado.diferenciais_nao_atendidos)}"
        )
    if (
        resultado.requisitos_tecnicos_analisados
        and vaga.descricao_completa
        and not resultado.requisitos_atendidos
        and not resultado.requisitos_nao_atendidos
    ):
        linhas.append("ℹ️ <b>Requisitos técnicos:</b> não informados na descrição")
    if resultado.pontos_a_favor:
        linhas.append(f"✅ {formatar_pontos(resultado.pontos_a_favor)}")
    if resultado.pontos_contra:
        linhas.append(f"❌ {formatar_pontos(resultado.pontos_contra)}")
    for aviso in resultado.avisos_objetivos:
        linhas.append(f"⚠️ {escapar_limitado(aviso, LIMITE_DO_AVISO)}")
    if resultado.alerta_pegadinha:
        linhas.append(f"⚠️ {escapar_limitado(resultado.alerta_pegadinha, LIMITE_DO_ALERTA)}")
    destino = url_de_abertura(recomendacao, url_de_rastreio)
    linhas.append(f'🔗 <a href="{escape(destino)}">Ver vaga em {escape(dominio_da_vaga(vaga))}</a>')
    return "\n".join(linhas)


def url_de_abertura(recomendacao: Recomendacao, url_de_rastreio: str) -> str:
    if not url_de_rastreio:
        return recomendacao.resultado.vaga.url
    return f"{url_de_rastreio}?{PARAMETRO_DO_TOKEN}={recomendacao.token}"


def dominio_da_vaga(vaga: Vaga) -> str:
    dominio = urlsplit(vaga.url).hostname or vaga.fonte
    return dominio.removeprefix(PREFIXO_DE_SUBDOMINIO_IGNORADO)


def rotulo_modalidade(vaga: Vaga) -> str:
    if vaga.modalidade is None:
        return "Modalidade não informada"
    return ROTULOS_MODALIDADE[vaga.modalidade.value]


def rotulo_da_origem(vaga: Vaga) -> str:
    if vaga.fonte == FONTE_ADZUNA:
        return ATRIBUICAO_DA_ADZUNA
    return f"Fonte: {escape(rotulo_fonte(vaga.fonte))}"


def rotulo_fonte(fonte: str) -> str:
    return fonte.replace("_", " ").title()


def formatar_pontos(pontos: list[str]) -> str:
    selecionados = pontos[:MAXIMO_DE_PONTOS_EXIBIDOS]
    return " · ".join(escapar_limitado(ponto, LIMITE_DO_PONTO) for ponto in selecionados)


def formatar_requisitos(requisitos: list[str]) -> str:
    exibidos = " · ".join(
        escapar_limitado(requisito, LIMITE_DO_REQUISITO)
        for requisito in requisitos[:MAXIMO_DE_REQUISITOS_EXIBIDOS]
    )
    ocultos = len(requisitos) - MAXIMO_DE_REQUISITOS_EXIBIDOS
    if ocultos <= 0:
        return exibidos
    return f"{exibidos} · e mais {ocultos}"


def recomendacoes_por_parte(
    partes: list[str], recomendacoes: list[Recomendacao]
) -> list[list[Recomendacao]]:
    ranqueadas = ranquear(recomendacoes)
    grupos = []
    inicio = 0
    for parte in partes:
        quantidade = parte.count(SEPARADOR_ENTRE_VAGAS) + 1
        grupos.append(ranqueadas[inicio : inicio + quantidade])
        inicio += quantidade
    return grupos


def dividir_em_mensagens(texto: str) -> list[str]:
    if len(texto) <= LIMITE_DE_CARACTERES_DO_TELEGRAM:
        return [texto]
    mensagens: list[str] = []
    atual = ""
    for bloco in texto.split(SEPARADOR_ENTRE_VAGAS):
        candidato = bloco if not atual else atual + SEPARADOR_ENTRE_VAGAS + bloco
        if len(candidato) > LIMITE_DE_CARACTERES_DO_TELEGRAM and atual:
            mensagens.append(atual)
            atual = bloco
        else:
            atual = candidato
    mensagens.append(atual)
    return mensagens
