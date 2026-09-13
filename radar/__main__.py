import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import httpx
from pydantic import ValidationError

from radar.avaliacao.descartes import (
    contar_por_motivo,
    descartes_do_prefiltro,
    exportar_descartes,
)
from radar.avaliacao.factory import criar_juiz
from radar.avaliacao.gabarito import (
    carregar_gabarito,
    exportar_gabarito,
    gravar_gabarito,
    rotulos_fora_da_janela,
    selecionar_do_gabarito,
)
from radar.avaliacao.julgar import julgar_entregas
from radar.collectors.adzuna import LIMITE_POR_MES, CotaDaAdzuna
from radar.collectors.composto import ColetorComposto
from radar.collectors.errors import ErroDeColeta
from radar.collectors.factory import (
    cidades_de_interesse,
    criar_coletor,
    ha_curso_desconhecido,
    termos_de_interesse,
)
from radar.cota import (
    ColetorComRegistroDeUso,
    abrir_cota_da_adzuna,
    reserva_do_diario,
    uso_da_adzuna,
)
from radar.domain.models import Perfil, Usuario
from radar.domain.perfil_fixo import perfil_de_exemplo
from radar.domain.ports import Repositorio
from radar.filtering.duplicatas import remover_duplicatas
from radar.filtering.prefiltro import filtrar
from radar.matching.avaliacoes import pontuar_vagas
from radar.matching.enriquecimento import EnriquecedorDeDescricoes
from radar.matching.errors import ErroDeAvaliacao
from radar.matching.factory import criar_extrator, identidade_da_extracao
from radar.matching.lotes import ExtratorEmLotes
from radar.notification.formatador import (
    formatar_falha_da_execucao,
    formatar_resumo_da_execucao,
)
from radar.notification.telegram import ErroDeNotificacao, NotificadorTelegram
from radar.pipeline import ParametrosDaExecucao, executar, selecionar_usuarios
from radar.reporting.funil import formatar_funil
from radar.reporting.julgamento import formatar_julgamento
from radar.settings import Settings
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.factory import (
    abrir_repositorio,
    abrir_repositorio_de_metricas,
    abrir_repositorio_em_memoria,
)

TIPOS_DE_ERRO_DE_PREENCHIMENTO = frozenset({"missing", "string_too_short"})
TIMEOUT_HTTP_EM_SEGUNDOS = 30
LIMITE_DE_VAGAS_NA_AVALIACAO_MANUAL = 3
DIAS_DA_COORTE = 30
COMANDO_PADRAO = "rodar"
DIAS_DO_JULGAMENTO = 7
AMOSTRA_DO_JULGAMENTO = 30
SEMENTE_DO_JULGAMENTO = 1
AMOSTRA_DO_GABARITO = 20
AMOSTRA_DOS_DESCARTES = 30


def nomes_das_variaveis_nao_preenchidas(erro: ValidationError) -> list[str]:
    return [
        str(detalhe["loc"][0]).upper()
        for detalhe in erro.errors()
        if detalhe["type"] in TIPOS_DE_ERRO_DE_PREENCHIMENTO
    ]


def problemas_da_configuracao(erro: ValidationError) -> list[str]:
    problemas = []
    for detalhe in erro.errors():
        nome = str(detalhe["loc"][0]).upper() if detalhe["loc"] else "configuração"
        if detalhe["type"] in TIPOS_DE_ERRO_DE_PREENCHIMENTO:
            problemas.append(f"{nome}: ausente ou vazia")
            continue
        problemas.append(f"{nome}: {detalhe['msg']}")
    return problemas


def carregar_settings() -> Settings | None:
    try:
        return Settings()
    except ValidationError as erro:
        print("Configuração inválida:", file=sys.stderr)
        for problema in problemas_da_configuracao(erro):
            print(f"  - {problema}", file=sys.stderr)
        return None


def verificar_configuracao(settings: Settings) -> None:
    print("Configuração carregada com sucesso.")
    print(f"Avaliador: {settings.avaliador}")
    print(f"Fontes: {', '.join(settings.fontes_selecionadas())}")
    print(f"Dias recentes: {settings.dias_recentes}")
    print(f"Vagas enviadas por execução: {settings.quantidade_vagas_enviadas}")
    print(f"Nota mínima para entrar na mensagem: {settings.nota_minima}")
    if not settings.usa_banco():
        print("Banco: nenhum (perfil fixo)")
        return
    with abrir_repositorio(settings) as repositorio:
        usuarios = repositorio.listar_ativos()
    print(f"Banco: conectado, {len(usuarios)} usuários ativos com Telegram vinculado")


def coletar(settings: Settings) -> None:
    usuarios = listar_usuarios(settings)
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        coletadas = montar_coletor(settings, cliente_http, usuarios).coletar()
    vagas = remover_duplicatas(coletadas)
    print(f"{len(coletadas)} vagas coletadas, {len(vagas)} após remover duplicatas")
    for vaga in vagas:
        modalidade = vaga.modalidade.value if vaga.modalidade else "modalidade não informada"
        print(
            f"- [{vaga.fonte}] {vaga.titulo} | {vaga.empresa} | {vaga.localizacao} | {modalidade}"
        )
        print(f"  {vaga.url}")


def perfil_para_avaliar(usuarios: list[Usuario]) -> Perfil:
    if usuarios:
        return usuarios[0].perfil
    return perfil_de_exemplo()


def avaliar(settings: Settings) -> None:
    usuarios = listar_usuarios(settings)
    perfil = perfil_para_avaliar(usuarios)
    print(f"Perfil usado: {perfil.curso}, {perfil.periodo}º período, {perfil.cidade}")
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        coletadas = montar_coletor(settings, cliente_http, usuarios).coletar()
        vagas = filtrar(remover_duplicatas(coletadas), perfil)
        selecionadas = EnriquecedorDeDescricoes(cliente_http).enriquecer(
            vagas[:LIMITE_DE_VAGAS_NA_AVALIACAO_MANUAL]
        )
        print(
            f"{len(vagas)} vagas após o pré-filtro; "
            f"extraindo {len(selecionadas)} com {settings.avaliador}"
        )
        extracoes = montar_extrator(settings).extrair(selecionadas)
    resultados = pontuar_vagas(
        selecionadas, {extracao.id_vaga: extracao for extracao in extracoes}, perfil
    )
    for resultado in resultados:
        vaga = resultado.vaga
        print(f"- [{resultado.nota:3d}] {vaga.titulo} | {vaga.empresa} | {vaga.localizacao}")
        print(f"  Atende: {', '.join(resultado.requisitos_atendidos) or '-'}")
        print(f"  Não atende: {', '.join(resultado.requisitos_nao_atendidos) or '-'}")
        print(f"  A favor: {', '.join(resultado.pontos_a_favor) or '-'}")
        print(f"  Contra: {', '.join(resultado.pontos_contra) or '-'}")
        for aviso in resultado.avisos_objetivos:
            print(f"  Aviso: {aviso}")
        if resultado.alerta_pegadinha:
            print(f"  Alerta: {resultado.alerta_pegadinha}")


def metricas(settings: Settings) -> None:
    with abrir_repositorio_de_metricas(settings) as repositorio:
        print(formatar_funil(repositorio.funil_da_coorte(DIAS_DA_COORTE)))


def julgar(
    settings: Settings, dias: int, amostra: int, semente: int, gabarito: Path | None = None
) -> None:
    with abrir_repositorio_de_metricas(settings) as repositorio:
        entregas = repositorio.entregas_recentes(dias)
    rotulos = carregar_gabarito(gabarito) if gabarito else None
    if rotulos is not None:
        entregas = selecionar_do_gabarito(entregas, rotulos)
        amostra = len(entregas)
        avisar_rotulos_fora_da_janela(rotulos, entregas, dias)
    resultado = julgar_entregas(
        entregas, criar_juiz(settings), amostra, semente, settings.juiz_modelo, dias
    )
    print(formatar_julgamento(resultado, rotulos))
    if resultado.nada_foi_julgado():
        raise ErroDeAvaliacao(
            "Nenhuma entrega foi julgada. Último erro do avaliador: "
            f"{resultado.ultimo_erro or 'não informado'}"
        )


def avisar_rotulos_fora_da_janela(rotulos: dict, selecionadas: list, dias: int) -> None:
    fora = rotulos_fora_da_janela(rotulos, selecionadas)
    if not fora:
        return
    print(
        f"{fora} de {len(rotulos)} rótulos do gabarito estão fora das entregas dos últimos "
        f"{dias} dias e não serão julgados; use --dias maior para incluí-los.",
        file=sys.stderr,
    )


def gabarito(settings: Settings, dias: int, amostra: int, semente: int, saida: Path) -> None:
    with abrir_repositorio_de_metricas(settings) as repositorio:
        entregas = repositorio.entregas_recentes(dias)
    itens = exportar_gabarito(entregas, amostra, semente)
    gravar_gabarito(itens, saida)
    print(f'{len(itens)} entregas gravadas em {saida}; preencha "relevante" com true ou false')


def descartes(settings: Settings, amostra: int, semente: int, saida: Path) -> None:
    usuarios = listar_usuarios(settings)
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        coletadas = montar_coletor(settings, cliente_http, usuarios).coletar()
    vagas = remover_duplicatas(coletadas)
    descartados = descartes_do_prefiltro(vagas, usuarios)
    print(f"{len(vagas)} vagas únicas para {len(usuarios)} perfis")
    for motivo, total in contar_por_motivo(descartados).items():
        print(f"  {motivo}: {total}")
    itens = exportar_descartes(descartados, amostra, semente)
    gravar_gabarito(itens, saida)
    print(f'{len(itens)} descartes gravados em {saida}; preencha "descarte_correto"')


def testar_telegram(settings: Settings) -> None:
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        NotificadorTelegram(settings.telegram_bot_token, cliente_http).enviar(
            settings.telegram_chat_id, "Radar OK"
        )
    print(f"Mensagem enviada para o chat {settings.telegram_chat_id}")


def listar_usuarios(settings: Settings) -> list[Usuario]:
    with abrir_repositorio(settings) as repositorio:
        return repositorio.listar_ativos()


def montar_coletor(
    settings: Settings,
    cliente_http: httpx.Client,
    usuarios: list[Usuario],
    cota: CotaDaAdzuna | None = None,
) -> ColetorComposto:
    cidades = cidades_de_interesse(usuarios)
    termos = termos_de_interesse(usuarios)
    busca_geral = ha_curso_desconhecido(usuarios)
    return criar_coletor(
        settings, cliente_http, datetime.now(UTC), cidades, termos, busca_geral, cota
    )


def montar_extrator(settings: Settings) -> ExtratorEmLotes:
    return ExtratorEmLotes(
        criar_extrator(settings),
        settings.gemini_vagas_por_lote,
        prazo_em_segundos=settings.prazo_da_extracao_segundos,
        timeout_da_chamada_em_segundos=settings.gemini_timeout_segundos,
    )


def url_de_rastreio_utilizavel(settings: Settings) -> str:
    if not settings.usa_banco():
        return ""
    return settings.url_de_rastreio.strip()


def executar_fluxo(
    settings: Settings,
    cliente_http: httpx.Client,
    repositorio: Repositorio,
    apenas_o_perfil: UUID | None = None,
) -> None:
    notificador = NotificadorTelegram(settings.telegram_bot_token, cliente_http)
    extrator = montar_extrator(settings)
    agora = datetime.now(UTC)
    try:
        ativos = repositorio.listar_ativos()
        usuarios_da_coleta = selecionar_usuarios(ativos, apenas_o_perfil)
        if apenas_o_perfil is not None and not usuarios_da_coleta:
            print(f"Perfil {apenas_o_perfil} sem entrega a fazer; coleta não executada")
            return
        reserva = reserva_do_diario(ativos) if apenas_o_perfil is not None else 0
        cota = abrir_cota_da_adzuna(repositorio, agora, reserva)
        coletor = montar_coletor(settings, cliente_http, usuarios_da_coleta, cota)
        resumo = executar(
            ColetorComRegistroDeUso(coletor, repositorio, cota, agora),
            extrator,
            notificador,
            repositorio,
            ParametrosDaExecucao(
                modelo=identidade_da_extracao(settings),
                quantidade=settings.quantidade_vagas_enviadas,
                nota_minima=settings.nota_minima,
                falhas_ate_pausar=settings.falhas_de_envio_ate_pausar,
                dias_de_silencio_ate_avisar=settings.dias_de_silencio_ate_avisar,
                dias_ate_apagar_conta_excluida=settings.dias_ate_apagar_conta_excluida,
                url_de_rastreio=url_de_rastreio_utilizavel(settings),
            ),
            agora,
            enriquecer=EnriquecedorDeDescricoes(cliente_http).enriquecer,
            apenas_o_perfil=apenas_o_perfil,
        )
    except (ErroDeColeta, ErroDeAvaliacao, ErroDeNotificacao, ErroDeArmazenamento) as erro:
        avisar_operacao(settings, notificador, formatar_falha_da_execucao(agora, str(erro)))
        raise
    uso = uso_da_adzuna(repositorio, agora)
    print(
        f"{resumo.vagas_enviadas()} vagas enviadas para {resumo.atendidos()} usuários "
        f"em {extrator.requisicoes} requisições ao avaliador; "
        f"{resumo.usuarios_com_falha_de_revalidacao} usuários com falha de revalidação, "
        f"{resumo.usuarios_sem_entrega_por_falha_de_revalidacao} sem entrega por essa falha; "
        f"{resumo.vagas_sem_extracao} vagas sem extração, "
        f"{resumo.extracoes_nao_gravadas} extrações não gravadas; "
        f"{cota.requisicoes} requisições à Adzuna"
    )
    avisar_operacao(
        settings,
        notificador,
        formatar_resumo_da_execucao(
            agora,
            resumo.usuarios,
            resumo.atendidos(),
            resumo.vagas_enviadas(),
            resumo.vagas_coletadas,
            extrator.requisicoes,
            resumo.usuarios_com_falha_de_revalidacao,
            resumo.usuarios_sem_entrega_por_falha_de_revalidacao,
            resumo.vagas_sem_extracao,
            resumo.extracoes_nao_gravadas,
            adzuna_hoje=uso[0] if uso else None,
            adzuna_no_mes=uso[1] if uso else None,
            adzuna_limite=LIMITE_POR_MES,
            adzuna_esgotada=cota.esgotada,
            coletas_incompletas=coletor.incompletas,
        ),
    )


def avisar_operacao(settings: Settings, notificador: NotificadorTelegram, texto: str) -> None:
    if not settings.telegram_chat_id.strip():
        return
    try:
        notificador.enviar(settings.telegram_chat_id, texto)
    except ErroDeNotificacao as erro:
        print(f"Resumo da execução não foi entregue: {erro}", file=sys.stderr)


def rodar(settings: Settings, apenas_o_perfil: UUID | None = None) -> None:
    with (
        httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http,
        abrir_repositorio(settings) as repositorio,
    ):
        executar_fluxo(settings, cliente_http, repositorio, apenas_o_perfil)


def testar_local(settings: Settings) -> None:
    print("Modo local: banco e histórico ignorados; todas as vagas serão avaliadas novamente.")
    with (
        httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http,
        abrir_repositorio_em_memoria(settings) as repositorio,
    ):
        executar_fluxo(settings, cliente_http, repositorio)


COMANDOS = {
    "verificar": verificar_configuracao,
    "coletar": coletar,
    "avaliar": avaliar,
    "metricas": metricas,
    "testar-telegram": testar_telegram,
    "testar-local": testar_local,
    "rodar": rodar,
}


def configurar_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("google_genai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def inteiro_positivo(valor: str) -> int:
    numero = int(valor)
    if numero < 1:
        raise argparse.ArgumentTypeError("precisa ser um inteiro maior que zero")
    return numero


def main() -> None:
    parser = argparse.ArgumentParser(prog="radar", description="Radar de Estágio")
    subcomandos = parser.add_subparsers(dest="comando")
    comando_rodar = subcomandos.add_parser(
        "rodar", help="executa o fluxo completo e envia a mensagem (padrão)"
    )
    comando_rodar.add_argument(
        "--perfil", type=UUID, default=None, help="atende somente o perfil informado"
    )
    subcomandos.add_parser(
        "verificar", help="confere se as variáveis de ambiente estão preenchidas"
    )
    subcomandos.add_parser(
        "coletar", help="busca vagas reais nas fontes configuradas e imprime título e URL"
    )
    subcomandos.add_parser(
        "avaliar", help="coleta, pré-filtra e avalia algumas vagas com o avaliador configurado"
    )
    subcomandos.add_parser(
        "metricas", help="imprime o funil da coorte e o custo de extração do período"
    )
    comando_julgar = subcomandos.add_parser(
        "julgar",
        help="pede a um segundo modelo que julgue uma amostra das entregas recentes",
    )
    comando_julgar.add_argument("--dias", type=inteiro_positivo, default=DIAS_DO_JULGAMENTO)
    comando_julgar.add_argument("--amostra", type=inteiro_positivo, default=AMOSTRA_DO_JULGAMENTO)
    comando_julgar.add_argument("--semente", type=int, default=SEMENTE_DO_JULGAMENTO)
    comando_julgar.add_argument(
        "--gabarito", type=Path, default=None, help="julga só as entregas rotuladas no arquivo"
    )
    comando_gabarito = subcomandos.add_parser(
        "gabarito", help="exporta uma amostra de entregas para as pessoas rotularem"
    )
    comando_gabarito.add_argument("--dias", type=inteiro_positivo, default=DIAS_DO_JULGAMENTO)
    comando_gabarito.add_argument("--amostra", type=inteiro_positivo, default=AMOSTRA_DO_GABARITO)
    comando_gabarito.add_argument("--semente", type=int, default=SEMENTE_DO_JULGAMENTO)
    comando_gabarito.add_argument("--saida", type=Path, required=True)
    comando_descartes = subcomandos.add_parser(
        "descartes",
        help="exporta uma amostra do que o pré-filtro descartou, para as pessoas rotularem",
    )
    comando_descartes.add_argument(
        "--amostra", type=inteiro_positivo, default=AMOSTRA_DOS_DESCARTES
    )
    comando_descartes.add_argument("--semente", type=int, default=SEMENTE_DO_JULGAMENTO)
    comando_descartes.add_argument("--saida", type=Path, required=True)
    subcomandos.add_parser("testar-telegram", help='envia "Radar OK" para o chat configurado')
    subcomandos.add_parser(
        "testar-local",
        help="executa o fluxo completo sem banco ou histórico e envia ao Telegram",
    )
    argumentos = parser.parse_args()

    configurar_logging()
    settings = carregar_settings()
    if settings is None:
        sys.exit(1)

    nome_do_comando = argumentos.comando or COMANDO_PADRAO
    try:
        if nome_do_comando == "rodar":
            rodar(settings, getattr(argumentos, "perfil", None))
        elif nome_do_comando == "julgar":
            julgar(
                settings,
                argumentos.dias,
                argumentos.amostra,
                argumentos.semente,
                argumentos.gabarito,
            )
        elif nome_do_comando == "descartes":
            descartes(settings, argumentos.amostra, argumentos.semente, argumentos.saida)
        elif nome_do_comando == "gabarito":
            gabarito(
                settings, argumentos.dias, argumentos.amostra, argumentos.semente, argumentos.saida
            )
        else:
            COMANDOS[nome_do_comando](settings)
    except (ErroDeColeta, ErroDeAvaliacao, ErroDeNotificacao, ErroDeArmazenamento) as erro:
        print(erro, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
