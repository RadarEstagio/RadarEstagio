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

Participação no feedback usa a mesma janela de entregas do período. O denominador é o número de
pares distintos `(perfil_id, vaga_id)` com primeira entrega na janela, inclusive perfis antigos.
O numerador é o número desses pares com uma resposta positiva ou negativa após a entrega, até o
fim da consulta; se houver correção, vale a última por `ocorrido_em` e, em empate, por `id`.
Uma abertura sem resposta não conta, resposta anterior à entrega não conta e zero entregas
aparece como “sem denominador”. O relatório imprime contagens e percentual derivado, sem
persistir percentual.

## Tempo observado até entrega e abertura

Este bloco usa perfis criados na janela do relatório. Para cada perfil, considera a primeira
entrega válida posterior à criação e, depois, a primeira `vaga_aberta` de qualquer par
efetivamente entregue, sempre até o fim da consulta. As diferenças partem de `perfis.criado_em`
e são calculadas em segundos UTC, convertidos para minutos, horas ou dias apenas na
apresentação. O relatório mostra medianas contínuas somente dos casos
observados, a contagem sem entrega e a contagem sem abertura; “sem abertura” inclui quem não
recebeu entrega. Uma mediana indisponível é diferente de duração zero, que é legítima quando os
timestamps coincidem. Isso é tempo observado no piloto, não prazo nem tempo até valor prometido.

## Aquisição: da visita à primeira recomendação

Inclui visita, CTA, três etapas de perfil, conta criada, e-mail confirmado, perfil salvo,
abertura do Telegram, vínculo e primeira recomendação. No novo cadastro, momento, habilidades
e preferências vêm antes do e-mail e da senha; login pede somente a conta e edição não é novo
cadastro. Cada etapa conta identidades distintas cuja **primeira aparição em qualquer evento**
ocorreu nos últimos 30 dias.

A identidade é o usuário explícito, o dono do perfil ou, se ainda anônimo, a sessão. Uma sessão
anônima só é associada a um usuário quando o histórico contém exatamente um dono para ela.
Sessões compartilhadas por duas contas não são atribuídas arbitrariamente à primeira conta.
O cadastro do PR #14 conserva a sessão de origem mesmo com confirmação em outro aparelho.

Visitantes que abandonam antes de criar conta continuam contados. Uma pessoa em aparelhos
anônimos diferentes pode contar como duas sessões; isso não é identificação individual perfeita.
As etapas são contagens de alcance, não um funil estrito que descarte quem pulou uma etapa.
Contas criadas sem perfil ou sem confirmação aparecem em suas respectivas etapas.

### Mapa dos eventos do funil

O relatório mostra a primeira aparição por identidade, não uma conversão sequencial entre
linhas. Eventos do navegador não guardam senha, conteúdo digitado ou replay; eventos de banco
são os marcos autoritativos quando o navegador pode fechar ou perder a conexão.

| Fluxo/etapa visível | Evento existente e condição válida | Emissor | Identidade disponível | Repetição | Leitura no SQL | Limite de interpretação |
|---|---|---|---|---|---|---|
| Visita à landing | `landing_visualizada`, uma vez por armazenamento de sessão | navegador | `sessao_id`; `user_id` se a sessão já estiver autenticada | `sessionStorage` reduz recarga; linhas brutas ainda podem repetir entre sessões | `identificados` + `entradas` + `etapas` | não é pessoa única; sessões anônimas em aparelhos diferentes podem contar separadamente |
| Abertura do cadastro | `cta_cadastro_aberto`, somente clique não autenticado | navegador | sessão ou usuário autenticado disponível | cada clique não autenticado pode gerar linha | `etapas` conta pessoa distinta | mede intenção de abrir, não envio nem conta criada |
| Momento/curso e período | `etapa_perfil_concluida`, avanço após validação do passo | navegador | sessão ou usuário | voltar e avançar pode repetir | `etapas` por identidade | inclui edição; não prova novo cadastro nem habilidade informada |
| Habilidades | `etapa_habilidades_concluida`, avanço após seleção ou opção explícita vazia; somente quantidade | navegador | sessão ou usuário | revisitas podem repetir; `quantidade` não contém valores | `etapas` por identidade | não mede quais habilidades foram digitadas nem conversão |
| Preferências | `etapa_preferencias_concluida`, avanço válido para conta no cadastro ou submit válido na última etapa de edição | navegador | sessão ou usuário | voltar/avançar ou novo submit de edição pode repetir | `etapas` por identidade | inclui edição, exclui login; conclusão independe de criar conta e não comprova salvamento no backend |
| Conta criada | `conta_criada`, inserção de usuário no Auth | trigger do banco | `user_id` | marco autoritativo; não depende da aba | `etapas` por identidade | não prova confirmação de e-mail nem perfil salvo |
| E-mail confirmado | `email_confirmado`, confirmação observada pelo Auth | trigger do banco | `user_id` | marco autoritativo | `etapas` por identidade | não prova vínculo do Telegram ou entrega |
| Perfil salvo | `perfil_salvo`, insert confirmado pelo banco; o navegador mantém um espelho autenticado para ligar sessão | trigger do banco + navegador após persistência | banco: `user_id`/`perfil_id`; web: sessão/usuário | podem existir duas linhas para o mesmo marco; SQL conta identidade distinta | `etapas` por identidade; `0014` liga a sessão de origem nos eventos de banco | não distingue criação de edição; não atribui sucesso antes do retorno do backend |
| Abertura do Telegram | `telegram_aberto`, clique no CTA de vínculo | navegador | sessão ou usuário | cada clique pode repetir | `etapas` por identidade | não confirma vínculo; retorno/abertura externa não é prova de entrega |
| Telegram vinculado | `telegram_vinculado`, mudança confirmada de `telegram_chat_id` | trigger do banco após webhook | `user_id`/`perfil_id` | histórico pode ter revínculos | `etapas` e `perfis_vinculados` | não prova que o job rodou ou que havia vaga compatível |
| Primeira recomendação | `primeira_recomendacao_enviada`, `ativado_em` preenchido | trigger do banco após ativação do perfil | `user_id`/`perfil_id` | somente a transição inicial | `etapas` e coorte de perfis | prova primeira entrega operacional, não abertura nem utilidade |

Login, recuperação, edição de perfil, CAPTCHA, erro de rede e abandono não têm eventos próprios.
Não são inferidos a partir de silêncio. Se forem necessários, a tarefa futura deve especificar
`login_sucesso` ou `perfil_editado`, propriedades não pessoais e a regra de identidade/RLS antes
de alterar o catálogo; este ID não cria esses eventos.

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

O mesmo cálculo também é agrupado por `area_do_curso` em Python usando o curso atual do
perfil. O SQL retorna apenas semana, parcialidade, identificador interno, curso e sinal de
utilidade; o relatório não imprime o identificador. Cada perfil entra uma vez em cada semana
em que está no denominador. Curso não reconhecido fica em “Não classificado”. A soma dos grupos
reproduz o total semanal, mas a alteração posterior do curso pode mudar a leitura de semanas
passadas; isso não é histórico acadêmico.

Ativação operacional é a primeira recomendação entregue (`perfis.ativado_em`). Ativação de
produto é a primeira abertura observada; criar conta ou receber aviso sem vaga não ativa.
O apagamento definitivo pode remover dados históricos e mudar agregados; não há arquivo
permanente de métricas individuais fora da retenção declarada. O denominador semanal lê os
perfis que ainda existem: apagar um perfil ativado pode mudar o percentual de uma semana
passada. Comparações em reuniões devem registrar a data da consulta; semanas anteriores
não são snapshots imutáveis.

## Contas pausadas — situação atual

O relatório também mostra perfis não excluídos com `ativo=false`, agrupados por
`motivo_pausa`. O denominador inclui quem não respondeu, exibido como “Não informado”, e a
soma das categorias fecha com o total de contas pausadas no momento da consulta. Uma conta
retomada sai do quadro; uma pausa técnica sem resposta não recebe uma intenção presumida.

Esse quadro não é churn mensal, não reconstrói pausas anteriores e não permite inferir
tendência histórica. `conseguiu_estagio` permanece separado de `sem_vagas_uteis`; a coluna
guarda somente o motivo atual e pode voltar a nulo na retomada.

## Recusas com denominador

Outro bloco considera **todas as recomendações entregues nos últimos 30 dias**, inclusive a
perfis antigos. Separa anúncios sem extração, sem tecnologias obrigatórias, com uma ou duas,
e com três ou mais. O grupo vem da extração guardada, não da nota do ranking.

Cada grupo mostra entregas, recusas/entregas e recusas por `motivo_nota`/entregas. Usa a última
resposta de cada par depois da entrega, até agora. Ausência de feedback permanece no denominador;
ela não é classificada como aprovação. Esses números permitem comparar grupos sem confundir
maior volume entregue com maior rejeição. Não ajustar pesos só por uma contagem bruta.

## Custo e limites

Decisões preservadas da revisão de 08/09: `vagas_enviadas` conta linhas de envio da coorte,
enquanto `recomendacoes_elegiveis_feedback` deduplica pares e inclui perfis antigos. Os números
podem divergir; não mudar um denominador para igualar os dois. `semanais` deriva de
`utilidade_por_perfil_semana`, e as recusas reutilizam `respostas_do_periodo`, evitando duas
definições concorrentes do mesmo cálculo. A classificação por área fica no domínio.

Na apresentação, durações abaixo de 60 segundos usam segundos inteiros; abaixo de uma hora,
minutos; abaixo de um dia, horas; depois, dias, com uma casa decimal nessas três unidades.
O cálculo continua em segundos. Pausa sem resposta usa “Não informado”; essa decisão não
alterou o rótulo `sem_motivo` das recusas, que pertencem a outra métrica.

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
