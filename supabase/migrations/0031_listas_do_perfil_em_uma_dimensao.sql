alter table public.perfis
  add constraint perfis_areas_de_interesse_em_uma_dimensao
    check (coalesce(array_ndims(areas_de_interesse), 1) = 1),
  add constraint perfis_habilidades_em_uma_dimensao
    check (coalesce(array_ndims(habilidades), 1) = 1);
