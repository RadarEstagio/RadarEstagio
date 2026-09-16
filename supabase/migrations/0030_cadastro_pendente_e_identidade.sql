create function public.descartar_cadastro_pendente_ao_reenviar_link()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  delete from public.cadastros_pendentes where user_id = new.id;
  return null;
end;
$$;

revoke all on function public.descartar_cadastro_pendente_ao_reenviar_link() from public, anon, authenticated;

create trigger descartar_cadastro_pendente_ao_reenviar_link
after update of confirmation_sent_at on auth.users
for each row
when (
  old.confirmation_sent_at is not null
  and new.confirmation_sent_at is distinct from old.confirmation_sent_at
  and new.email_confirmed_at is null
)
execute function public.descartar_cadastro_pendente_ao_reenviar_link();
