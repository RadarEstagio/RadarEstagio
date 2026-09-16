create function public.descartar_eventos_repetidos()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.nome = 'vaga_aberta' then
    perform pg_advisory_xact_lock(
      hashtextextended('vaga_aberta:' || new.perfil_id || ':' || new.vaga_id, 0)
    );
    if exists (
      select 1 from public.eventos_produto
      where nome = 'vaga_aberta' and perfil_id = new.perfil_id and vaga_id = new.vaga_id
    ) then
      return null;
    end if;
  elsif new.nome in ('entregas_pausadas', 'telegram_vinculado') then
    if exists (
      select 1 from public.eventos_produto
      where nome = new.nome and perfil_id = new.perfil_id
        and ocorrido_em > new.ocorrido_em - interval '1 day'
    ) then
      return null;
    end if;
  end if;
  return new;
end;
$$;

create trigger z_descartar_eventos_repetidos
before insert on public.eventos_produto
for each row execute function public.descartar_eventos_repetidos();

revoke all on function public.descartar_eventos_repetidos() from public, anon, authenticated;
