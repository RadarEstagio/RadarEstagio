alter table public.perfis
  add column pessoa_com_deficiencia boolean;

grant update (pessoa_com_deficiencia) on public.perfis to authenticated;

create or replace function public.validar_cadastro_radar(cadastro jsonb)
returns void
language plpgsql
set search_path = ''
as $$
declare
  perfil jsonb := cadastro->'perfil';
  lista text;
begin
  if jsonb_typeof(cadastro) is distinct from 'object'
    or cadastro->'aceitou_termos' is distinct from 'true'::jsonb
    or jsonb_typeof(cadastro->'versao_dos_termos') is distinct from 'string'
    or coalesce(cadastro->>'versao_dos_termos', '') !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
    or jsonb_typeof(cadastro->'aceita_emails') is distinct from 'boolean'
    or jsonb_typeof(perfil) is distinct from 'object' then
    raise exception 'cadastro ou aceite inválido' using errcode = '22023';
  end if;
  if exists (
    select 1 from jsonb_object_keys(cadastro) chave
    where chave not in ('perfil', 'aceitou_termos', 'aceita_emails', 'versao_dos_termos', 'sessao_id')
  ) or exists (
    select 1 from jsonb_object_keys(perfil) chave
    where chave not in ('curso', 'periodo', 'habilidades', 'cidade', 'modalidade', 'areas_de_interesse',
      'pessoa_com_deficiencia')
  ) then
    raise exception 'campo de cadastro inválido' using errcode = '22023';
  end if;
  perform (cadastro->>'versao_dos_termos')::date;
  if jsonb_typeof(perfil->'curso') is distinct from 'string'
    or length(btrim(perfil->>'curso')) not between 2 and 200
    or length(perfil->>'curso') > 200
    or jsonb_typeof(perfil->'cidade') is distinct from 'string'
    or length(btrim(perfil->>'cidade')) not between 2 and 120
    or length(perfil->>'cidade') > 120
    or coalesce(perfil->>'periodo', '') !~ '^[1-9][0-9]?$'
    or coalesce(perfil->>'modalidade', '') not in ('remoto', 'presencial', 'hibrido', 'indiferente')
    or coalesce(jsonb_typeof(perfil->'pessoa_com_deficiencia'), 'null') not in ('boolean', 'null') then
    raise exception 'perfil inválido' using errcode = '22023';
  end if;
  foreach lista in array array['habilidades', 'areas_de_interesse'] loop
    if jsonb_typeof(perfil->lista) is distinct from 'array' then
      raise exception 'lista inválida' using errcode = '22023';
    end if;
    if jsonb_array_length(perfil->lista) > 50 or exists (
      select 1 from jsonb_array_elements(perfil->lista) item
      where jsonb_typeof(item) <> 'string'
        or length(btrim(item #>> '{}')) not between 1 and 100
        or length(item #>> '{}') > 100
    ) then
      raise exception 'lista inválida' using errcode = '22023';
    end if;
  end loop;
  if exists (
    select 1 from jsonb_array_elements_text(perfil->'areas_de_interesse') area
    where area not in (
      'desenvolvimento_web', 'desenvolvimento_mobile', 'dados_ia', 'infraestrutura_redes',
      'seguranca', 'suporte_tecnico', 'qa_testes', 'direito_contencioso', 'direito_societario',
      'direito_trabalhista', 'compliance', 'rotinas_administrativas', 'gestao_de_projetos',
      'processos_e_qualidade', 'financeiro', 'contabil_fiscal', 'controladoria_auditoria',
      'mercado_financeiro', 'marketing_digital', 'conteudo_e_redes',
      'comunicacao_institucional', 'design_grafico', 'recrutamento_e_selecao',
      'departamento_pessoal', 'treinamento_e_desenvolvimento', 'vendas',
      'atendimento_ao_cliente', 'comercio_exterior', 'suprimentos_e_compras',
      'estoque_e_armazem', 'transporte_e_distribuicao', 'engenharia_civil',
      'engenharia_mecanica', 'engenharia_eletrica', 'engenharia_de_producao',
      'meio_ambiente_e_seguranca', 'assistencia_a_saude', 'laboratorio_e_pesquisa',
      'saude_publica', 'docencia_e_monitoria', 'coordenacao_pedagogica',
      'producao_de_material', 'eventos', 'hotelaria', 'gastronomia'
    )
  ) then
    raise exception 'habilidades ou áreas inválidas' using errcode = '22023';
  end if;
  if coalesce(cadastro->>'sessao_id', '') !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then
    raise exception 'sessão de cadastro inválida' using errcode = '22023';
  end if;
end;
$$;

create or replace function public.criar_perfil_do_cadastro(dono uuid, cadastro jsonb, recebido_em timestamptz)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  perfil jsonb := cadastro->'perfil';
begin
  perform public.validar_cadastro_radar(cadastro);
  insert into public.perfis (user_id, curso, periodo, habilidades, cidade, modalidade,
    areas_de_interesse, pessoa_com_deficiencia, aceita_emails, termos_aceitos_em, versao_dos_termos)
  values (dono, btrim(perfil->>'curso'), (perfil->>'periodo')::int,
    array(select btrim(x) from jsonb_array_elements_text(perfil->'habilidades') x),
    btrim(perfil->>'cidade'), perfil->>'modalidade',
    array(select x from jsonb_array_elements_text(perfil->'areas_de_interesse') x),
    case jsonb_typeof(perfil->'pessoa_com_deficiencia')
      when 'boolean' then (perfil->>'pessoa_com_deficiencia')::boolean
    end,
    (cadastro->>'aceita_emails')::boolean, recebido_em, cadastro->>'versao_dos_termos')
  on conflict (user_id) do nothing;
  update public.eventos_produto set sessao_id = (cadastro->>'sessao_id')::uuid
  where user_id = dono and origem = 'banco'
    and nome in ('conta_criada', 'email_confirmado', 'perfil_salvo') and sessao_id is null;
end;
$$;
