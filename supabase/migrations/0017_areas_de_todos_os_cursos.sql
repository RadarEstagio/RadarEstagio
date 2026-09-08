alter table public.perfis
  drop constraint perfis_areas_de_interesse_validas;

alter table public.perfis
  add constraint perfis_areas_de_interesse_validas
    check (
      areas_de_interesse is null
      or areas_de_interesse <@ array[
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
      ]::text[]
    );

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
  perform (cadastro->>'versao_dos_termos')::date;
  if jsonb_typeof(perfil->'curso') is distinct from 'string'
    or length(btrim(perfil->>'curso')) not between 2 and 200
    or jsonb_typeof(perfil->'cidade') is distinct from 'string'
    or length(btrim(perfil->>'cidade')) not between 2 and 120
    or coalesce(perfil->>'periodo', '') !~ '^[1-9][0-9]?$'
    or coalesce(perfil->>'modalidade', '') not in ('remoto', 'presencial', 'hibrido', 'indiferente') then
    raise exception 'perfil inválido' using errcode = '22023';
  end if;
  foreach lista in array array['habilidades', 'areas_de_interesse'] loop
    if jsonb_typeof(perfil->lista) is distinct from 'array' then
      raise exception 'lista inválida' using errcode = '22023';
    end if;
    if jsonb_array_length(perfil->lista) > 50 or exists (
      select 1 from jsonb_array_elements(perfil->lista) item
      where jsonb_typeof(item) <> 'string' or length(btrim(item #>> '{}')) not between 1 and 100
    ) then
      raise exception 'lista inválida' using errcode = '22023';
    end if;
  end loop;
  if jsonb_array_length(perfil->'habilidades') = 0 or exists (
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
