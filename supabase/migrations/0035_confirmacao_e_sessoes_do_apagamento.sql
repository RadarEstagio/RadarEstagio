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
