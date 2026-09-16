create function public.descartar_cadastro_dos_metadados()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.raw_user_meta_data := new.raw_user_meta_data - 'cadastro_radar';
  return new;
end;
$$;

revoke all on function public.descartar_cadastro_dos_metadados() from public, anon, authenticated;

create trigger a_descartar_cadastro_dos_metadados
before update on auth.users
for each row
when (new.raw_user_meta_data ? 'cadastro_radar')
execute function public.descartar_cadastro_dos_metadados();

update auth.users
set raw_user_meta_data = raw_user_meta_data - 'cadastro_radar'
where raw_user_meta_data ? 'cadastro_radar';
