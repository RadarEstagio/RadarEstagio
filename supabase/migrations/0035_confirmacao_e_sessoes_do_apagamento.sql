create or replace function public.processar_cadastro_radar()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  pendente public.cadastros_pendentes;
begin
  if tg_op = 'INSERT' and new.raw_user_meta_data ? 'cadastro_radar' then
    perform public.validar_cadastro_radar(new.raw_user_meta_data->'cadastro_radar');
    insert into public.cadastros_pendentes (user_id, cadastro)
      values (new.id, new.raw_user_meta_data->'cadastro_radar');
    update public.eventos_produto
      set sessao_id = (new.raw_user_meta_data->'cadastro_radar'->>'sessao_id')::uuid
      where user_id = new.id and nome = 'conta_criada' and origem = 'banco';
  end if;
  if new.email_confirmed_at is not null then
    select * into pendente from public.cadastros_pendentes where user_id = new.id for update;
    if found then
      begin
        perform public.criar_perfil_do_cadastro(new.id, pendente.cadastro, pendente.recebido_em);
      exception
        when others then
          null;
      end;
      delete from public.cadastros_pendentes where user_id = new.id;
      update auth.users set raw_user_meta_data = raw_user_meta_data - 'cadastro_radar'
        where id = new.id;
    end if;
  end if;
  return new;
end;
$$;

create or replace function public.apagar_minha_conta_sem_perfil()
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
      select e.sessao_id from public.eventos_produto e
      where e.user_id = dono and e.origem = 'banco' and e.sessao_id is not null
        and not exists (
          select 1 from public.eventos_produto alheio
          where alheio.sessao_id = e.sessao_id
            and alheio.user_id is not null and alheio.user_id <> dono
        )
    );
  delete from auth.users where id = dono;
end;
$$;
