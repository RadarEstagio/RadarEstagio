select e.token, v.titulo, v.empresa
from envios e
join vagas v on v.id = e.vaga_id
join eventos_produto aberta
  on aberta.perfil_id = e.perfil_id
  and aberta.vaga_id = e.vaga_id
  and aberta.nome = 'vaga_aberta'
where e.perfil_id = %(perfil_id)s
  and e.pergunta_do_dia_seguinte_em is null
  and aberta.ocorrido_em >= e.enviada_em
  and (aberta.ocorrido_em at time zone 'America/Sao_Paulo')::date = %(hoje)s::date - 1
  and not exists (
    select 1
    from eventos_produto resposta
    where resposta.perfil_id = e.perfil_id
      and resposta.vaga_id = e.vaga_id
      and resposta.nome in ('vaga_util', 'vaga_irrelevante', 'candidatura_iniciada')
      and resposta.ocorrido_em >= e.enviada_em
  )
  and not exists (
    select 1
    from envios perguntado
    where perguntado.perfil_id = e.perfil_id
      and (perguntado.pergunta_do_dia_seguinte_em at time zone 'America/Sao_Paulo')::date
        = %(hoje)s::date
  )
order by aberta.ocorrido_em desc, aberta.id desc
limit 1
