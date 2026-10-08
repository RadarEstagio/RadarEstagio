revoke all on table public.vagas from public, anon, authenticated;
revoke all on table public.envios from public, anon, authenticated;
revoke all on table public.avaliacoes from public, anon, authenticated;

revoke all on sequence public.vagas_id_seq from public, anon, authenticated;
revoke all on sequence public.avaliacoes_id_seq from public, anon, authenticated;
revoke all on sequence public.eventos_produto_id_seq from public, anon, authenticated;

alter table public.eventos_produto
  add constraint pagina_da_visita_permitida
  check (
    nome <> 'landing_visualizada' or (
      propriedades -> 'pagina' is null
      or (
        jsonb_typeof(propriedades -> 'pagina') = 'string'
        and propriedades ->> 'pagina' ~ '^/[A-Za-z0-9._:/-]{0,19}$'
      )
    )
  ) not valid;
