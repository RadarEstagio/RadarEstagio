# Métricas de produto

A leitura continua em `uv run python -m radar metricas`, com `DATABASE_URL` configurada e
janela de 30 dias. A consulta executada está em `radar/storage/metricas.sql`; não há uma
segunda cópia de SQL neste documento. Esta etapa foi validada com dados sintéticos em
PostgreSQL isolado. Conferir os números reais depois da publicação das funções.

## Feedback por recomendação

A mensagem diária termina com “Deixe seu feedback 👇” e um número por recomendação, na
mesma ordem das vagas. Se exceder o tamanho do Telegram, o teclado fica na última parte.
Não é enviada uma notificação separada só para solicitar feedback.

O número abre uma mensagem com título, empresa e seis opções:

| Opção | Evento | Motivo |
|---|---|---|
| 👍 Essa serviu | `vaga_util` | — |
| 👎 A nota não fez sentido | `vaga_irrelevante` | `motivo_nota` |
| 👎 Não é da minha área | `vaga_irrelevante` | `motivo_area` |
| 👎 Pedem demais | `vaga_irrelevante` | `motivo_exigencia` |
| 👎 Local ou modalidade | `vaga_irrelevante` | `motivo_logistica` |
| 👎 Já vi essa | `vaga_irrelevante` | `motivo_repetida` |

Responder fecha somente a pergunta aberta; a mensagem diária e seus links permanecem.
O número pode ser aberto novamente para corrigir a resposta. Essa permanência é intencional;
toques repetidos podem abrir várias perguntas da mesma vaga ao mesmo tempo. Não há bloqueio
de pergunta já aberta nesta versão. Botões antigos de recusa abrem
as novas opções; “Todas serviram” antigo não vira feedback positivo retroativamente.

O webhook exige conta ativa, não excluída, com o chat da interação ainda vinculado. A função
`ir` mantém a navegação para contas pausadas ou desvinculadas sem registrar abertura; exclusão
bloqueia navegação e registro. `HEAD` não registra abertura. Nenhuma destas regras foi relaxada.

Depois de gravar a resposta, falhas ao apagar a pergunta ou confirmar o clique são registradas
no log, mas o webhook retorna 200. Falha de persistência retorna 500 para permitir nova tentativa.
Isso evita retries causados por operações cosméticas; não garante processamento único diante
de reentrega independente ou perda da resposta HTTP após o insert.

Não foi necessário mudar o catálogo de eventos. Repetições de entrega do webhook ou do clique
podem produzir mais de uma linha bruta; as métricas não contam essas linhas como recomendações
adicionais. Eventos não são apagados ao mudar a resposta.

## Aquisição: da visita à primeira recomendação

Inclui visita, CTA, três etapas, conta criada, e-mail confirmado, perfil salvo, abertura do
Telegram, vínculo e primeira recomendação. O formulário pede e-mail e senha antes das três
etapas e esse passo não emite evento próprio: quem desiste nele aparece como CTA aberto sem
`etapa_perfil_concluida`. Cada etapa conta identidades distintas cuja
**primeira aparição em qualquer evento** ocorreu nos últimos 30 dias.

A identidade é o usuário explícito, o dono do perfil ou, se ainda anônimo, a sessão. Uma sessão
anônima só é associada a um usuário quando o histórico contém exatamente um dono para ela.
Sessões compartilhadas por duas contas não são atribuídas arbitrariamente à primeira conta.
O cadastro do PR #14 conserva a sessão de origem mesmo com confirmação em outro aparelho.

Visitantes que abandonam antes de criar conta continuam contados. Uma pessoa em aparelhos
anônimos diferentes pode contar como duas sessões; isso não é identificação individual perfeita.
As etapas são contagens de alcance, não um funil estrito que descarte quem pulou uma etapa.
Contas criadas sem perfil ou sem confirmação aparecem em suas respectivas etapas.

## Resultado dos perfis novos

Este bloco usa **perfis criados nos últimos 30 dias**, distinto da aquisição acima. Inclui
as recomendações entregues a esses perfis e interações posteriores às entregas, até agora.
Vínculo histórico não desaparece porque alguém desvinculou o Telegram depois.

Uma recomendação é o par `(perfil_id, vaga_id)`. Três cliques na mesma vaga contam como uma
abertura. Para feedback, vale a última resposta do par por instante e, em empate, ID do evento.
Uma resposta negativa corrigida para positiva deixa de contar como recusa, e vice-versa.

Vagas úteis formam a união de feedback positivo vigente e candidatura atribuída histórica,
sem duplicar quem tem os dois sinais. **Candidatura não tem emissor no piloto**; o relatório
explicita essa limitação. A definição conceitual de vaga útil permanece no `CONTEXT.md`.

## Utilidade semanal — North Star

Cada linha cobre uma semana civil de segunda a segunda no fuso `America/Sao_Paulo`.
As semanas que intersectam os 30 dias são mostradas completas; a atual é identificada como
“em andamento”. Eventos futuros são ignorados.

- Denominador: todos os perfis com ativação operacional até o fim da semana (ou até agora,
  na semana atual), inclusive perfis antigos, pausados ou desvinculados. Não restringir a
  quem recebeu mensagem naquela semana, o que esconderia perda de cobertura e retenção.
- Numerador: perfis desse denominador com ao menos uma recomendação útil sinalizada na semana.
  Para respostas contraditórias dentro da semana vale a última; candidatura histórica também
  compõe a união. Recomendação enviada antes da semana pode receber feedback nela.
- A utilidade não é carregada automaticamente para a semana seguinte. Uma correção na semana
  seguinte não reescreve o resultado fechado da anterior.
- Sem ativados, o relatório mostra “sem denominador”, em vez de interpretar como 0%.

Ativação operacional é a primeira recomendação entregue (`perfis.ativado_em`). Ativação de
produto é a primeira abertura observada; criar conta ou receber aviso sem vaga não ativa.
O apagamento definitivo pode remover dados históricos e mudar agregados; não há arquivo
permanente de métricas individuais fora da retenção declarada. O denominador semanal lê os
perfis que ainda existem: apagar um perfil ativado pode mudar o percentual de uma semana
passada. Comparações em reuniões devem registrar a data da consulta; semanas anteriores
não são snapshots imutáveis.

## Recusas com denominador

Outro bloco considera **todas as recomendações entregues nos últimos 30 dias**, inclusive a
perfis antigos. Separa anúncios sem extração, sem tecnologias obrigatórias, com uma ou duas,
e com três ou mais. O grupo vem da extração guardada, não da nota do ranking.

Cada grupo mostra entregas, recusas/entregas e recusas por `motivo_nota`/entregas. Usa a última
resposta de cada par depois da entrega, até agora. Ausência de feedback permanece no denominador;
ela não é classificada como aprovação. Esses números permitem comparar grupos sem confundir
maior volume entregue com maior rejeição. Não ajustar pesos só por uma contagem bruta.

## Custo e limites

O custo mostrado é um indicador de uso: vagas extraídas no período por perfil novo com ativação
operacional na coorte. Não é valor monetário nem número de requisições ao Gemini; o resumo de
execução informa requisições separadamente. Extrações compartilhadas também atendem perfis
antigos, portanto o indicador não atribui custo individual.

Os testes cobrem banco vazio, abandono, confirmação, sessão compartilhada, cliques repetidos,
feedback corrigido, união com candidatura, perfis antigos, limite semanal de Brasília e
entregas sem resposta. Segundo o registro de 05/09 à noite, o relatório foi conferido com
os dados reais e a abertura foi validada com token real. O feedback estava zerado nessa
conferência; falta validar respostas positivas e negativas reais e o funil completo após
publicar a landing. Essa conferência inicial não substitui a medição durante o piloto.
