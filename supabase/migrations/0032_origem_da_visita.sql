alter table public.eventos_produto
  add constraint origem_da_visita_permitida
  check (
    nome <> 'landing_visualizada' or (
      (propriedades - 'pagina' - 'referrer_dominio' - 'utm_source' - 'utm_medium'
        - 'utm_campaign') = '{}'::jsonb
      and (
        propriedades -> 'referrer_dominio' is null
        or (
          jsonb_typeof(propriedades -> 'referrer_dominio') = 'string'
          and propriedades ->> 'referrer_dominio' ~ '^[a-z0-9._-]{1,40}$'
        )
      )
      and (
        propriedades -> 'utm_source' is null
        or (
          jsonb_typeof(propriedades -> 'utm_source') = 'string'
          and propriedades ->> 'utm_source' ~ '^[a-z0-9._-]{1,24}$'
        )
      )
      and (
        propriedades -> 'utm_medium' is null
        or (
          jsonb_typeof(propriedades -> 'utm_medium') = 'string'
          and propriedades ->> 'utm_medium' ~ '^[a-z0-9._-]{1,24}$'
        )
      )
      and (
        propriedades -> 'utm_campaign' is null
        or (
          jsonb_typeof(propriedades -> 'utm_campaign') = 'string'
          and propriedades ->> 'utm_campaign' ~ '^[a-z0-9._-]{1,24}$'
        )
      )
    )
  ) not valid;
