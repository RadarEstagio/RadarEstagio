create function public.apagar_minha_conta_sem_perfil()
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  dono uuid := auth.uid();
begin
  if dono is null then
    raise exception 'sem sessão' using errcode = '42501';
  end if;
  perform 1 from auth.users where id = dono for update;
  if not found then
    return;
  end if;
  if exists (select 1 from public.perfis where user_id = dono) then
    raise exception 'conta com perfil usa excluir_minha_conta' using errcode = '55000';
  end if;
  delete from public.eventos_produto
  where user_id is null
    and sessao_id in (
      select sessao_id from public.eventos_produto
      where user_id = dono and sessao_id is not null
    );
  delete from auth.users where id = dono;
end;
$$;

revoke all on function public.apagar_minha_conta_sem_perfil() from public, anon;
grant execute on function public.apagar_minha_conta_sem_perfil() to authenticated;
