alter table public.perfis
  add column entrega_imediata_disparada_em timestamptz;

update public.perfis as perfil
set entrega_imediata_disparada_em = now()
where perfil.telegram_chat_id is not null
  or perfil.ativado_em is not null
  or exists (
    select 1
    from public.eventos_produto as evento
    where evento.perfil_id = perfil.id
      and evento.nome = 'telegram_vinculado'
  );

revoke insert, update on table public.perfis from public, anon, authenticated;
grant update (
  curso, periodo, habilidades, cidade, modalidade, areas_de_interesse,
  ativo, motivo_pausa, aceita_emails, atualizado_em
) on table public.perfis to authenticated;
