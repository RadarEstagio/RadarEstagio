alter table public.perfis
  add column motivo_pausa text null,
  add constraint perfis_motivo_pausa_check check (
    motivo_pausa in (
      'conseguiu_estagio', 'interrompeu_busca', 'sem_vagas_uteis', 'frequencia', 'outro'
    )
  );

grant update (motivo_pausa) on public.perfis to authenticated;
