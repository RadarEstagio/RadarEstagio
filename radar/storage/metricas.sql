with limites as (
  select now() as fim, now() - make_interval(days => %(dias)s) as inicio
), coorte as (
  select p.* from perfis p, limites l where p.criado_em >= l.inicio and p.criado_em <= l.fim
), pausas_atuais as (
  select coalesce(p.motivo_pausa, 'sem_motivo') as motivo, count(*) as total
  from perfis p
  where p.ativo = false and p.excluida_em is null
  group by 1
), eventos as (
  select e.* from eventos_produto e, limites l where e.ocorrido_em <= l.fim
), sessoes as (
  select sessao_id, min(user_id::text) as dono from eventos
  where sessao_id is not null and user_id is not null
  group by sessao_id having count(distinct user_id) = 1
), identificados as (
  select e.*, coalesce('u:' || e.user_id::text, 'u:' || p.user_id::text,
    'u:' || s.dono, 's:' || e.sessao_id::text) as pessoa
  from eventos e left join perfis p on p.id = e.perfil_id
  left join sessoes s on s.sessao_id = e.sessao_id
), entradas as (
  select pessoa, min(ocorrido_em) as entrada from identificados where pessoa is not null group by pessoa
), etapas as (
  select nome, count(distinct e.pessoa) as total from identificados e
  join entradas i using(pessoa), limites l
  where i.entrada >= l.inicio group by nome
), entregas as (
  select e.* from envios e join coorte c on c.id = e.perfil_id, limites l
  where e.enviada_em <= l.fim
), primeiras_entregas as (
  select distinct on(e.perfil_id)
    e.perfil_id, e.vaga_id, e.enviada_em, c.criado_em
  from envios e
  join coorte c on c.id = e.perfil_id, limites l
  where e.enviada_em >= c.criado_em and e.enviada_em <= l.fim
  order by e.perfil_id, e.enviada_em, e.vaga_id
), primeiras_aberturas as (
  select distinct on(t.perfil_id)
    t.perfil_id, e.ocorrido_em
  from entregas t
  join coorte c on c.id = t.perfil_id
  join eventos e on e.perfil_id = t.perfil_id and e.vaga_id = t.vaga_id
  where t.enviada_em >= c.criado_em
    and e.nome = 'vaga_aberta' and e.ocorrido_em >= t.enviada_em
  order by t.perfil_id, e.ocorrido_em, e.id
), interacoes as (
  select e.* from eventos e join entregas t on t.perfil_id = e.perfil_id and t.vaga_id = e.vaga_id
  where e.ocorrido_em >= t.enviada_em
), respostas as (
  select distinct on(perfil_id, vaga_id) * from interacoes
  where nome in ('vaga_util', 'vaga_irrelevante')
  order by perfil_id, vaga_id, ocorrido_em desc, id desc
), uteis as (
  select perfil_id, vaga_id from respostas where nome = 'vaga_util'
  union select perfil_id, vaga_id from interacoes where nome = 'candidatura_iniciada'
), semanas as (
  select semana_inicio as semana,
    semana_inicio at time zone 'America/Sao_Paulo' as de,
    (semana_inicio + interval '1 week') at time zone 'America/Sao_Paulo' as ate
  from limites l, generate_series(
    date_trunc('week', l.inicio at time zone 'America/Sao_Paulo'),
    date_trunc('week', l.fim at time zone 'America/Sao_Paulo'), interval '1 week') semana_inicio
), respostas_de_utilidade_semana as (
  select distinct on (s.semana, e.perfil_id, e.vaga_id)
    s.semana::date as semana, e.perfil_id, e.vaga_id, e.nome
  from semanas s
  join eventos e on e.ocorrido_em >= s.de and e.ocorrido_em < s.ate
  join envios t on t.perfil_id = e.perfil_id and t.vaga_id = e.vaga_id
  where e.nome in ('vaga_util', 'vaga_irrelevante') and e.ocorrido_em >= t.enviada_em
  order by s.semana, e.perfil_id, e.vaga_id, e.ocorrido_em desc, e.id desc
), candidaturas_de_utilidade_semana as (
  select distinct s.semana::date as semana, e.perfil_id
  from semanas s
  join eventos e on e.ocorrido_em >= s.de and e.ocorrido_em < s.ate
  join envios t on t.perfil_id = e.perfil_id and t.vaga_id = e.vaga_id
  where e.nome = 'candidatura_iniciada' and e.ocorrido_em >= t.enviada_em
), utilidade_na_semana as (
  select semana, perfil_id from respostas_de_utilidade_semana where nome = 'vaga_util'
  union
  select semana, perfil_id from candidaturas_de_utilidade_semana
), utilidade_por_perfil_semana as (
  select s.semana::date as semana, s.ate > l.fim as parcial,
    p.id as perfil_id, p.curso,
    exists(
      select 1 from utilidade_na_semana u
      where u.semana = s.semana::date and u.perfil_id = p.id
    ) as com_utilidade
  from semanas s cross join limites l
  join perfis p on p.ativado_em < s.ate and p.ativado_em <= l.fim
), semanais as (
  select s.semana::date as semana, s.ate > l.fim as parcial,
    (select count(*) from utilidade_por_perfil_semana u
      where u.semana = s.semana::date) as ativados,
    (select count(*) from utilidade_por_perfil_semana u
      where u.semana = s.semana::date and u.com_utilidade) as com_utilidade
  from semanas s cross join limites l
), entregas_do_periodo as (
  select distinct on(e.perfil_id, e.vaga_id)
    e.perfil_id, e.vaga_id, e.enviada_em,
    case when v.extracao is null then 'sem_extracao'
      when jsonb_array_length(coalesce(v.extracao->'habilidades_obrigatorias', '[]')) = 0 then 'sem_tecnologias'
      when jsonb_array_length(coalesce(v.extracao->'habilidades_obrigatorias', '[]')) <= 2 then 'uma_ou_duas'
      else 'tres_ou_mais' end as grupo
  from envios e join vagas v on v.id = e.vaga_id, limites l
  where e.enviada_em >= l.inicio and e.enviada_em <= l.fim
  order by e.perfil_id, e.vaga_id, e.enviada_em
), respostas_do_periodo as (
  select distinct on(e.perfil_id, e.vaga_id) e.*
  from eventos e
  join entregas_do_periodo t on t.perfil_id = e.perfil_id and t.vaga_id = e.vaga_id
  where e.nome in ('vaga_util', 'vaga_irrelevante') and e.ocorrido_em >= t.enviada_em
  order by e.perfil_id, e.vaga_id, e.ocorrido_em desc, e.id desc
), grupos as (
  select t.grupo, count(*) as entregas,
    count(*) filter(where r.nome = 'vaga_irrelevante') as recusas,
    count(*) filter(where r.nome = 'vaga_irrelevante' and r.propriedades->>'motivo' = 'motivo_nota') as recusas_da_nota
  from entregas_do_periodo t left join respostas_do_periodo r using(perfil_id, vaga_id)
  group by t.grupo
), motivos as (
  select coalesce(propriedades->>'motivo', 'sem_motivo') as motivo, count(*) as total
  from respostas where nome = 'vaga_irrelevante' group by 1
)
select
  (select count(*) from coorte) as perfis_criados,
  (select count(*) from coorte p where telegram_chat_id is not null or exists(
    select 1 from eventos e where e.perfil_id = p.id and e.nome = 'telegram_vinculado')) as perfis_vinculados,
  (select count(*) from coorte where ativado_em <= (select fim from limites)) as perfis_ativados,
  (select count(distinct perfil_id) from interacoes where nome = 'vaga_aberta') as perfis_com_vaga_aberta,
  (select count(distinct perfil_id) from uteis) as perfis_com_vaga_util,
  (select count(distinct perfil_id) from interacoes where nome = 'candidatura_iniciada') as perfis_com_candidatura,
  (select count(*) from entregas) as vagas_enviadas,
  (select count(distinct (perfil_id, vaga_id)) from interacoes where nome = 'vaga_aberta') as vagas_abertas,
  (select count(*) from uteis) as vagas_uteis,
  (select count(*) from respostas where nome = 'vaga_irrelevante') as vagas_irrelevantes,
  (select count(distinct (perfil_id, vaga_id)) from interacoes where nome = 'candidatura_iniciada') as candidaturas,
  (select count(*) from vagas, limites l where extraida_em >= l.inicio and extraida_em <= l.fim) as vagas_extraidas,
  (select count(*) from entregas_do_periodo) as recomendacoes_elegiveis_feedback,
  (select count(*) from respostas_do_periodo) as recomendacoes_com_feedback,
  (select count(*) from coorte) as perfis_na_coorte,
  (select count(*) from coorte c where not exists(
    select 1 from primeiras_entregas e where e.perfil_id = c.id
  )) as perfis_sem_entrega,
  (select percentile_cont(0.5) within group(order by extract(epoch from (e.enviada_em - e.criado_em))) from primeiras_entregas e) as mediana_segundos_ate_entrega,
  (select count(*) from coorte c where not exists(
    select 1 from primeiras_aberturas a where a.perfil_id = c.id
  )) as perfis_sem_abertura,
  (select percentile_cont(0.5) within group(order by extract(epoch from (a.ocorrido_em - c.criado_em)))
    from primeiras_aberturas a join coorte c on c.id = a.perfil_id) as mediana_segundos_ate_abertura,
  coalesce((select jsonb_object_agg(nome, total) from etapas), '{}') as etapas,
  coalesce((select jsonb_object_agg(motivo, total) from motivos), '{}') as recusas_por_motivo,
  coalesce((select jsonb_agg(to_jsonb(s) order by semana) from semanais s), '[]') as utilidade_semanal,
  coalesce((select jsonb_agg(to_jsonb(u) order by u.semana, u.perfil_id) from utilidade_por_perfil_semana u), '[]') as utilidade_semanal_fatos,
  coalesce((select jsonb_agg(to_jsonb(g) order by grupo) from grupos g), '[]') as recusas_por_grupo,
  coalesce((select jsonb_agg(to_jsonb(p) order by motivo) from pausas_atuais p), '[]') as pausas_atuais
