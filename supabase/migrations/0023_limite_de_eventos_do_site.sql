alter table public.eventos_produto
  add constraint propriedades_do_site_curtas
  check (origem <> 'web' or octet_length(propriedades::text) <= 256) not valid;

create table public.eventos_do_site_por_hora (
  hora timestamptz not null,
  anonimo boolean not null,
  total integer not null check (total >= 0),
  primary key (hora, anonimo)
);
alter table public.eventos_do_site_por_hora enable row level security;
revoke all on public.eventos_do_site_por_hora from public, anon, authenticated;

create function public.limitar_eventos_do_site()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  hora_atual timestamptz := date_trunc('hour', now(), 'UTC');
  total_na_hora integer;
begin
  if new.origem <> 'web' then
    return new;
  end if;
  if new.sessao_id is not null and (
    select count(*) from public.eventos_produto
    where sessao_id = new.sessao_id and origem = 'web'
      and ocorrido_em > now() - interval '1 hour'
  ) >= 60 then
    raise exception 'limite de eventos da sessão atingido' using errcode = 'PT429';
  end if;
  if new.user_id is not null and (
    select count(*) from public.eventos_produto
    where user_id = new.user_id and origem = 'web'
      and ocorrido_em > now() - interval '1 hour'
  ) >= 60 then
    raise exception 'limite de eventos da conta atingido' using errcode = 'PT429';
  end if;
  delete from public.eventos_do_site_por_hora where hora < hora_atual - interval '1 day';
  insert into public.eventos_do_site_por_hora as contagem (hora, anonimo, total)
  values (hora_atual, new.user_id is null, 1)
  on conflict (hora, anonimo) do update set total = contagem.total + 1
  returning contagem.total into total_na_hora;
  if total_na_hora > 600 then
    raise exception 'limite de eventos do site nesta hora atingido' using errcode = 'PT429';
  end if;
  return new;
end;
$$;

create trigger limitar_eventos_do_site
before insert on public.eventos_produto
for each row execute function public.limitar_eventos_do_site();

revoke all on function public.limitar_eventos_do_site() from public, anon, authenticated;
