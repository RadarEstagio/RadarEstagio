import logging
from datetime import date
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import ValidationError

from radar.domain.areas import subareas_do_curso
from radar.domain.metricas import agrupar_utilidade_por_area
from radar.domain.models import (
    AreaDeInteresse,
    ChaveDaVaga,
    EntregaParaJulgar,
    ExtracaoDaVaga,
    FunilDaCoorte,
    Modalidade,
    Perfil,
    Recomendacao,
    RecusasDoUsuario,
    ResultadoMatch,
    Usuario,
    Vaga,
)
from radar.storage.errors import ErroDeArmazenamento

logger = logging.getLogger(__name__)

RECUSAS_POR_AREA_PARA_DESCONTAR = 2
ESPACO_DA_TRAVA_DE_ATENDIMENTO = 4242
AREAS_CONHECIDAS = frozenset(area.value for area in AreaDeInteresse)

SQL_USUARIOS_ATIVOS = """
    select p.id, p.curso, p.periodo, p.habilidades, p.cidade, p.modalidade, p.telegram_chat_id,
           coalesce(p.areas_de_interesse, '{}'::text[]) as areas_de_interesse,
           coalesce(
             (select max(e.enviada_em) from envios e where e.perfil_id = p.id),
             p.criado_em
           ) as sem_recomendacao_desde,
           p.silencio_avisado_em
    from perfis p
    where p.ativo and p.excluida_em is null and p.telegram_chat_id is not null
    order by p.criado_em
"""

SQL_PERFIS_SEM_VINCULO = (
    "select count(*) from perfis where ativo and excluida_em is null and telegram_chat_id is null"
)

SQL_EXTRACOES_EXISTENTES = """
    select fonte, id_externo, extracao
    from vagas
    where extracao is not null
      and modelo_extracao = %(modelo)s
      and (fonte, id_externo) in (
        select * from unnest(%(fontes)s::text[], %(ids_externos)s::text[])
      )
"""

SQL_GUARDAR_EXTRACAO = """
    update vagas
    set extracao = %(extracao)s, extraida_em = now(), modelo_extracao = %(modelo)s
    where id = %(vaga_id)s
"""

SQL_IDS_ENVIADOS = """
    select v.fonte, v.id_externo
    from envios e
    join vagas v on v.id = e.vaga_id
    where e.perfil_id = %(perfil_id)s
"""

SQL_VAGAS_ENVIADAS_RECENTES = """
    select v.fonte, v.id_externo, v.titulo, v.empresa, v.localizacao, v.descricao, v.url,
           v.publicada_em, v.modalidade
    from envios e
    join vagas v on v.id = e.vaga_id
    where e.perfil_id = %(perfil_id)s
      and e.enviada_em > now() - interval '30 days'
"""

SQL_ENTREGAS_RECENTES = """
    select e.perfil_id, e.enviada_em,
           p.curso, p.periodo, p.habilidades, p.cidade, p.modalidade as modalidade_do_perfil,
           p.areas_de_interesse,
           v.fonte, v.id_externo, v.titulo, v.empresa, v.localizacao, v.descricao, v.url,
           v.publicada_em, v.modalidade,
           a.nota,
           f.nome as feedback, f.propriedades->>'motivo' as motivo_do_feedback
    from envios e
    join perfis p on p.id = e.perfil_id
    join vagas v on v.id = e.vaga_id
    left join avaliacoes a on a.perfil_id = e.perfil_id and a.vaga_id = e.vaga_id
    left join lateral (
        select ev.nome, ev.propriedades
        from eventos_produto ev
        where ev.perfil_id = e.perfil_id
          and ev.vaga_id = e.vaga_id
          and ev.nome in ('vaga_util', 'vaga_irrelevante')
          and ev.ocorrido_em >= e.enviada_em
        order by ev.ocorrido_em desc
        limit 1
    ) f on true
    where e.enviada_em >= now() - make_interval(days => %(dias)s)
    order by e.enviada_em desc
"""

SQL_ULTIMA_RESPOSTA_POR_VAGA = """
    select distinct on (e.vaga_id) e.vaga_id, e.nome, e.propriedades ->> 'motivo' as motivo
    from eventos_produto e
    where e.perfil_id = %(perfil_id)s
      and e.nome in ('vaga_util', 'vaga_irrelevante')
      and e.ocorrido_em > now() - interval '30 days'
    order by e.vaga_id, e.ocorrido_em desc, e.id desc
"""

SQL_AREAS_RECUSADAS = f"""
    with ultima_resposta as ({SQL_ULTIMA_RESPOSTA_POR_VAGA})
    select area
    from ultima_resposta r
    join vagas v on v.id = r.vaga_id,
         jsonb_array_elements_text(v.extracao -> 'areas_da_vaga') area
    where r.nome = 'vaga_irrelevante'
      and r.motivo = 'motivo_area'
    group by area
    having count(distinct r.vaga_id) >= %(limiar)s
"""

SQL_VAGAS_RECUSADAS_COMO_REPETIDAS = f"""
    with ultima_resposta as ({SQL_ULTIMA_RESPOSTA_POR_VAGA})
    select v.fonte, v.id_externo, v.titulo, v.empresa, v.localizacao, v.descricao, v.url,
           v.publicada_em, v.modalidade
    from ultima_resposta r
    join vagas v on v.id = r.vaga_id
    where r.nome = 'vaga_irrelevante'
      and r.motivo = 'motivo_repetida'
"""

SQL_GUARDAR_VAGA = """
    insert into vagas
      (fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em, modalidade)
    values
      (%(fonte)s, %(id_externo)s, %(titulo)s, %(empresa)s, %(localizacao)s, %(descricao)s,
       %(url)s, %(publicada_em)s, %(modalidade)s)
    on conflict (fonte, id_externo) do update set
      descricao = case
        when length(excluded.descricao) > length(vagas.descricao) then excluded.descricao
        else vagas.descricao
      end,
      modalidade = coalesce(excluded.modalidade, vagas.modalidade)
    returning id
"""

SQL_GUARDAR_AVALIACAO = """
    insert into avaliacoes
      (perfil_id, vaga_id, nota, requisitos_atendidos, requisitos_nao_atendidos,
       requisitos_tecnicos_analisados, pontos_a_favor, pontos_contra, alerta_pegadinha, modelo)
    values
      (%(perfil_id)s, %(vaga_id)s, %(nota)s, %(requisitos_atendidos)s,
       %(requisitos_nao_atendidos)s, %(requisitos_tecnicos_analisados)s,
       %(pontos_a_favor)s, %(pontos_contra)s, %(alerta_pegadinha)s, %(modelo)s)
    on conflict (perfil_id, vaga_id) do update set
      nota = excluded.nota,
      requisitos_atendidos = excluded.requisitos_atendidos,
      requisitos_nao_atendidos = excluded.requisitos_nao_atendidos,
      requisitos_tecnicos_analisados = excluded.requisitos_tecnicos_analisados,
      pontos_a_favor = excluded.pontos_a_favor,
      pontos_contra = excluded.pontos_contra,
      alerta_pegadinha = excluded.alerta_pegadinha,
      modelo = excluded.modelo
"""

SQL_GUARDAR_ENVIO = """
    insert into envios (perfil_id, vaga_id, token)
    values (%(perfil_id)s, %(vaga_id)s, %(token)s)
    on conflict (perfil_id, vaga_id) do nothing
"""

SQL_REGISTRAR_ATIVACAO = """
    update perfis
    set ativado_em = now()
    where id = %(perfil_id)s and ativado_em is null
    returning ativado_em
"""

SQL_ZERAR_FALHAS_DE_ENVIO = """
    update perfis
    set falhas_de_envio = 0
    where id = %(perfil_id)s and falhas_de_envio > 0
"""

SQL_CONTAR_FALHA_DE_ENVIO = """
    update perfis
    set falhas_de_envio = falhas_de_envio + 1
    where id = %(perfil_id)s
    returning falhas_de_envio
"""

SQL_PAUSAR = """
    update perfis
    set ativo = false, atualizado_em = now()
    where id = %(perfil_id)s and ativo
"""

SQL_SESSOES_DAS_CONTAS_EXCLUIDAS = """
    select distinct e.sessao_id
    from eventos_produto e
    join perfis p on p.user_id = e.user_id
    where e.sessao_id is not null
      and p.excluida_em is not null
      and p.excluida_em < now() - make_interval(days => %(dias)s)
"""

SQL_APAGAR_EVENTOS_ANONIMOS = """
    delete from eventos_produto
    where sessao_id = any(%(sessoes)s::uuid[])
      and user_id is null
"""

SQL_APAGAR_CONTAS_EXCLUIDAS = """
    delete from auth.users
    where id in (
      select user_id from perfis
      where excluida_em is not null
        and excluida_em < now() - make_interval(days => %(dias)s)
    )
"""

SQL_REGISTRAR_AVISO_DE_SILENCIO = """
    update perfis
    set silencio_avisado_em = now()
    where id = %(perfil_id)s
"""

SQL_REQUISICOES_DA_FONTE = """
    select coalesce(sum(requisicoes), 0)
    from uso_das_fontes
    where fonte = %(fonte)s and dia >= %(desde)s
"""

SQL_REGISTRAR_REQUISICOES_DA_FONTE = """
    insert into uso_das_fontes (fonte, dia, requisicoes)
    values (%(fonte)s, %(dia)s, %(requisicoes)s)
    on conflict (fonte, dia)
    do update set requisicoes = uso_das_fontes.requisicoes + excluded.requisicoes
"""

SQL_FUNIL_DA_COORTE = Path(__file__).with_name("metricas.sql").read_text()


class RepositorioPostgres:
    def __init__(self, conexao: psycopg.Connection) -> None:
        self._conexao = conexao

    def listar_ativos(self) -> list[Usuario]:
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                linhas = cursor.execute(SQL_USUARIOS_ATIVOS).fetchall()
                sem_vinculo = cursor.execute(SQL_PERFIS_SEM_VINCULO).fetchone()["count"]
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler os perfis: {descrever(erro)}") from erro
        if sem_vinculo:
            logger.info("%d perfis ativos ainda sem Telegram vinculado", sem_vinculo)
        return [converter_em_usuario(linha) for linha in linhas]

    def pode_entregar(self, usuario: Usuario) -> bool:
        try:
            with self._conexao.cursor() as cursor:
                return cursor.execute(
                    "select exists(select 1 from perfis where id = %s and ativo "
                    "and excluida_em is null and telegram_chat_id = %s)",
                    (usuario.id, usuario.chat_id),
                ).fetchone()[0]
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao conferir destinatário: {descrever(erro)}"
            ) from erro

    def extracoes_existentes(
        self, vagas: list[Vaga], modelo: str
    ) -> dict[ChaveDaVaga, ExtracaoDaVaga]:
        if not vagas:
            return {}
        parametros = {
            "modelo": modelo,
            "fontes": [vaga.fonte for vaga in vagas],
            "ids_externos": [vaga.id_externo for vaga in vagas],
        }
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                linhas = cursor.execute(SQL_EXTRACOES_EXISTENTES, parametros).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler as extrações: {descrever(erro)}") from erro
        return dict(filter(None, (interpretar_extracao(linha) for linha in linhas)))

    def guardar_extracoes(self, extracoes: list[tuple[Vaga, ExtracaoDaVaga]], modelo: str) -> None:
        if not extracoes:
            return
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                for vaga, extracao in extracoes:
                    vaga_id = guardar_vaga(cursor, vaga)
                    cursor.execute(
                        SQL_GUARDAR_EXTRACAO,
                        {
                            "vaga_id": vaga_id,
                            "extracao": Jsonb(extracao.model_dump(mode="json")),
                            "modelo": modelo,
                        },
                    )
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao gravar as extrações: {descrever(erro)}") from erro

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]:
        try:
            with self._conexao.cursor() as cursor:
                linhas = cursor.execute(SQL_IDS_ENVIADOS, {"perfil_id": usuario.id}).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler os envios: {descrever(erro)}") from erro
        return {(fonte, id_externo) for fonte, id_externo in linhas}

    def vagas_enviadas_recentemente(self, usuario: Usuario) -> list[Vaga]:
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                linhas = cursor.execute(
                    SQL_VAGAS_ENVIADAS_RECENTES, {"perfil_id": usuario.id}
                ).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao ler as vagas enviadas: {descrever(erro)}"
            ) from erro
        return [converter_em_vaga_enviada(linha) for linha in linhas]

    def travar_atendimento(self, usuario: Usuario) -> None:
        try:
            self._conexao.execute(
                "select pg_advisory_lock(%(espaco)s, hashtext(%(perfil)s))",
                {"espaco": ESPACO_DA_TRAVA_DE_ATENDIMENTO, "perfil": str(usuario.id)},
            )
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao travar o atendimento: {descrever(erro)}") from erro

    def liberar_atendimento(self, usuario: Usuario) -> None:
        try:
            self._conexao.execute(
                "select pg_advisory_unlock(%(espaco)s, hashtext(%(perfil)s))",
                {"espaco": ESPACO_DA_TRAVA_DE_ATENDIMENTO, "perfil": str(usuario.id)},
            )
        except psycopg.Error as erro:
            logger.warning("trava do perfil %s não foi liberada: %s", usuario.id, descrever(erro))

    def recusas_do_usuario(self, usuario: Usuario) -> RecusasDoUsuario:
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                areas = cursor.execute(
                    SQL_AREAS_RECUSADAS,
                    {"perfil_id": usuario.id, "limiar": RECUSAS_POR_AREA_PARA_DESCONTAR},
                ).fetchall()
                repetidas = cursor.execute(
                    SQL_VAGAS_RECUSADAS_COMO_REPETIDAS, {"perfil_id": usuario.id}
                ).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler as recusas: {descrever(erro)}") from erro
        return RecusasDoUsuario(
            areas=[
                AreaDeInteresse(linha["area"])
                for linha in areas
                if linha["area"] in AREAS_CONHECIDAS
            ],
            vagas_repetidas=[converter_em_vaga_enviada(linha) for linha in repetidas],
        )

    def guardar_avaliacoes(
        self, usuario: Usuario, avaliadas: list[ResultadoMatch], modelo: str
    ) -> None:
        if not avaliadas:
            return
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                for resultado in avaliadas:
                    vaga_id = guardar_vaga(cursor, resultado.vaga)
                    guardar_avaliacao(cursor, usuario.id, vaga_id, resultado, modelo)
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao gravar avaliações: {descrever(erro)}") from erro

    def registrar_envios(self, usuario: Usuario, enviadas: list[Recomendacao]) -> None:
        if not enviadas:
            return
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                for recomendacao in enviadas:
                    vaga_id = guardar_vaga(cursor, recomendacao.resultado.vaga)
                    guardar_envio(cursor, usuario.id, vaga_id, recomendacao.token)
                ativado_agora = registrar_ativacao(cursor, usuario.id)
                cursor.execute(SQL_ZERAR_FALHAS_DE_ENVIO, {"perfil_id": usuario.id})
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao gravar envios: {descrever(erro)}") from erro
        if ativado_agora:
            logger.info("Perfil %s ativado pela primeira entrega relevante", usuario.id)

    def registrar_falha_de_envio(self, usuario: Usuario) -> int:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                return cursor.execute(
                    SQL_CONTAR_FALHA_DE_ENVIO, {"perfil_id": usuario.id}
                ).fetchone()[0]
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao contar a falha de envio: {descrever(erro)}"
            ) from erro

    def apagar_contas_excluidas(self, dias_de_carencia: int) -> int:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                sessoes = [
                    linha[0]
                    for linha in cursor.execute(
                        SQL_SESSOES_DAS_CONTAS_EXCLUIDAS, {"dias": dias_de_carencia}
                    ).fetchall()
                ]
                if sessoes:
                    cursor.execute(SQL_APAGAR_EVENTOS_ANONIMOS, {"sessoes": sessoes})
                cursor.execute(SQL_APAGAR_CONTAS_EXCLUIDAS, {"dias": dias_de_carencia})
                return cursor.rowcount
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao apagar contas excluídas: {descrever(erro)}"
            ) from erro

    def registrar_aviso_de_silencio(self, usuario: Usuario) -> None:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                cursor.execute(SQL_REGISTRAR_AVISO_DE_SILENCIO, {"perfil_id": usuario.id})
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao gravar o aviso de silêncio: {descrever(erro)}"
            ) from erro

    def requisicoes_da_fonte_desde(self, fonte: str, desde: date) -> int:
        try:
            with self._conexao.cursor() as cursor:
                return cursor.execute(
                    SQL_REQUISICOES_DA_FONTE, {"fonte": fonte, "desde": desde}
                ).fetchone()[0]
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao ler o uso da fonte {fonte}: {descrever(erro)}"
            ) from erro

    def registrar_requisicoes_da_fonte(self, fonte: str, dia: date, requisicoes: int) -> None:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                cursor.execute(
                    SQL_REGISTRAR_REQUISICOES_DA_FONTE,
                    {"fonte": fonte, "dia": dia, "requisicoes": requisicoes},
                )
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao gravar o uso da fonte {fonte}: {descrever(erro)}"
            ) from erro

    def entregas_recentes(self, dias: int) -> list[EntregaParaJulgar]:
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                linhas = cursor.execute(SQL_ENTREGAS_RECENTES, {"dias": dias}).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler as entregas: {descrever(erro)}") from erro
        return [converter_em_entrega(linha) for linha in linhas]

    def funil_da_coorte(self, dias: int) -> FunilDaCoorte:
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                totais = cursor.execute(SQL_FUNIL_DA_COORTE, {"dias": dias}).fetchone()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler o funil: {descrever(erro)}") from erro
        totais = dict(totais)
        fatos = totais.pop("utilidade_semanal_fatos", [])
        totais["utilidade_por_area"] = agrupar_utilidade_por_area(fatos)
        return FunilDaCoorte(dias=dias, **totais)

    def pausar(self, usuario: Usuario) -> None:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                cursor.execute(SQL_PAUSAR, {"perfil_id": usuario.id})
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao pausar o perfil: {descrever(erro)}") from erro


def guardar_vaga(cursor: psycopg.Cursor, vaga: Vaga) -> int:
    parametros = vaga.model_dump(mode="json", exclude={"modalidade"})
    parametros["publicada_em"] = vaga.publicada_em
    parametros["modalidade"] = vaga.modalidade.value if vaga.modalidade else None
    return cursor.execute(SQL_GUARDAR_VAGA, parametros).fetchone()[0]


def guardar_avaliacao(
    cursor: psycopg.Cursor, perfil_id: UUID, vaga_id: int, resultado: ResultadoMatch, modelo: str
) -> None:
    cursor.execute(
        SQL_GUARDAR_AVALIACAO,
        {
            "perfil_id": perfil_id,
            "vaga_id": vaga_id,
            "nota": resultado.nota,
            "requisitos_atendidos": resultado.requisitos_atendidos,
            "requisitos_nao_atendidos": resultado.requisitos_nao_atendidos,
            "requisitos_tecnicos_analisados": resultado.requisitos_tecnicos_analisados,
            "pontos_a_favor": resultado.pontos_a_favor,
            "pontos_contra": resultado.pontos_contra,
            "alerta_pegadinha": resultado.alerta_pegadinha,
            "modelo": modelo,
        },
    )


def guardar_envio(cursor: psycopg.Cursor, perfil_id: UUID, vaga_id: int, token: UUID) -> None:
    cursor.execute(SQL_GUARDAR_ENVIO, {"perfil_id": perfil_id, "vaga_id": vaga_id, "token": token})


def registrar_ativacao(cursor: psycopg.Cursor, perfil_id: UUID) -> bool:
    return cursor.execute(SQL_REGISTRAR_ATIVACAO, {"perfil_id": perfil_id}).fetchone() is not None


def interpretar_extracao(linha: dict) -> tuple[ChaveDaVaga, ExtracaoDaVaga] | None:
    try:
        chave = (linha["fonte"], linha["id_externo"])
        return chave, ExtracaoDaVaga.model_validate(linha["extracao"])
    except ValidationError:
        logger.info("extração guardada da vaga %s está em formato antigo", linha["id_externo"])
        return None


def converter_em_entrega(linha: dict) -> EntregaParaJulgar:
    return EntregaParaJulgar(
        perfil_id=linha["perfil_id"],
        perfil=Perfil(
            curso=linha["curso"],
            periodo=linha["periodo"],
            habilidades=linha["habilidades"],
            cidade=linha["cidade"],
            modalidade=Modalidade(linha["modalidade_do_perfil"]),
            areas_de_interesse=areas_do_campo_do_curso(linha["curso"], linha["areas_de_interesse"]),
        ),
        vaga=converter_em_vaga_enviada(linha),
        enviada_em=linha["enviada_em"],
        nota_do_radar=linha["nota"],
        feedback=linha["feedback"],
        motivo_do_feedback=linha["motivo_do_feedback"],
    )


def converter_em_vaga_enviada(linha: dict) -> Vaga:
    modalidade = linha["modalidade"]
    return Vaga(
        id_externo=linha["id_externo"],
        fonte=linha["fonte"],
        titulo=linha["titulo"],
        empresa=linha["empresa"],
        localizacao=linha["localizacao"],
        descricao=linha["descricao"],
        url=linha["url"],
        publicada_em=linha["publicada_em"],
        modalidade=Modalidade(modalidade) if modalidade else None,
    )


def areas_do_campo_do_curso(curso: str, areas: list[str]) -> list[AreaDeInteresse]:
    permitidas = {valor for valor, _ in subareas_do_curso(curso)}
    return [AreaDeInteresse(area) for area in areas if area in permitidas]


def converter_em_usuario(linha: dict) -> Usuario:
    return Usuario(
        id=linha["id"],
        perfil=Perfil(
            curso=linha["curso"],
            periodo=linha["periodo"],
            habilidades=linha["habilidades"],
            cidade=linha["cidade"],
            modalidade=Modalidade(linha["modalidade"]),
            areas_de_interesse=areas_do_campo_do_curso(linha["curso"], linha["areas_de_interesse"]),
        ),
        chat_id=linha["telegram_chat_id"],
        sem_recomendacao_desde=linha["sem_recomendacao_desde"],
        silencio_avisado_em=linha["silencio_avisado_em"],
    )


def descrever(erro: psycopg.Error) -> str:
    return type(erro).__name__
