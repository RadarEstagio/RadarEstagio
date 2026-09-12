create table public.uso_das_fontes (
  fonte text not null,
  dia date not null,
  requisicoes integer not null default 0 check (requisicoes >= 0),
  primary key (fonte, dia)
);
alter table public.uso_das_fontes enable row level security;
revoke all on public.uso_das_fontes from public, anon, authenticated;
