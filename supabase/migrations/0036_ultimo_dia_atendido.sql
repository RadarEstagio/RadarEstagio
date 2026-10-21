alter table public.perfis
  add column ultimo_dia_atendido date;

update public.perfis perfil
set ultimo_dia_atendido = (
  select max((envio.enviada_em at time zone 'America/Sao_Paulo')::date)
  from public.envios envio
  where envio.perfil_id = perfil.id
);
