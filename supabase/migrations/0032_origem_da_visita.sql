alter table public.eventos_produto
  add constraint origem_da_visita_permitida
  check (
    nome <> 'landing_visualizada' or (
      (propriedades - 'pagina' - 'host' - 'referrer_dominio' - 'utm_source' - 'utm_medium'
        - 'utm_campaign') = '{}'::jsonb
      and (
        propriedades -> 'host' is null
        or (
          jsonb_typeof(propriedades -> 'host') = 'string'
          and propriedades ->> 'host' ~ '^[a-z0-9._-]{1,30}$'
        )
      )
      and (
        propriedades -> 'referrer_dominio' is null
        or (
          jsonb_typeof(propriedades -> 'referrer_dominio') = 'string'
          and propriedades ->> 'referrer_dominio' ~ '^[a-z0-9._-]{1,36}$'
        )
      )
      and (
        propriedades -> 'utm_source' is null
        or (
          jsonb_typeof(propriedades -> 'utm_source') = 'string'
          and propriedades ->> 'utm_source' ~ '^[a-z0-9._-]{1,20}$'
        )
      )
      and (
        propriedades -> 'utm_medium' is null
        or (
          jsonb_typeof(propriedades -> 'utm_medium') = 'string'
          and propriedades ->> 'utm_medium' ~ '^[a-z0-9._-]{1,16}$'
        )
      )
      and (
        propriedades -> 'utm_campaign' is null
        or (
          jsonb_typeof(propriedades -> 'utm_campaign') = 'string'
          and propriedades ->> 'utm_campaign' ~ '^[a-z0-9._-]{1,20}$'
        )
      )
    )
  ) not valid;
