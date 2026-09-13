alter table public.vagas
  add column dias_sem_extracao smallint not null default 0 check (dias_sem_extracao >= 0),
  add column ultimo_dia_sem_extracao date;
