# Auditoria do agendamento diário

Base: `888a716`, 10/09/2026, revisada em 11/09 contra `ebc28f4` depois da revisão do PR #54. Entre
as duas bases entraram o #52 (lote incompleto pede junto o que faltou) e o plano pago do Gemini,
e os dois mudam o G01, o G02 e o G05. As demais referências de código continuam valendo.

Leitura do workflow `radar-diario.yml`, do pipeline, do extrator em lotes e da Edge Function
`telegram-webhook`, confrontada com o histórico real das execuções do workflow entre 26/08 e
10/09 (`gh run list` e `gh run view --log`). Sem alteração de código, sem chamada ao Gemini e sem
envio ao Telegram. A configuração do cron-job.org fica fora do repositório e não foi consultada;
dele só se vê o efeito nos runs.

## Resumo

O disparo é confiável: desde a troca pelo cron-job.org em 28/08, os 13 dias foram disparados entre
07:23:02 e 07:23:04, sem falha nem atraso. A decisão de abandonar o `schedule` nativo está
confirmada pelos dados. Os riscos estão no que acontece depois do disparo.

| ID | Achado | Prioridade |
|---|---|---|
| G01 | Timeout de 15 min sem orçamento de tempo; estourar zera as entregas de todos | crítica |
| G02 | Lote devolve 1 de 10 vagas; repetição em lote entrou no #52, causa em aberto | média |
| G03 | Reexecução no mesmo dia manda segunda mensagem a todos | alta |
| G04 | Execução ausente não gera alerta | alta |
| G05 | Run por perfil em paralelo com o diário extrai as mesmas vagas duas vezes | baixa |
| G06 | Run por perfil coleta vagas para a coorte inteira | média |
| G07 | `if: failure()` pode não cobrir o estouro do timeout | média |
| G08 | O diário executa o `main` sem conferir o schema | baixa |
| G09 | O horário 07:23 vive em lugares que não se conhecem | baixa |
| G10 | Falha do disparo imediato só aparece no log da Edge Function | baixa |

## Evidência: histórico de execuções

Execuções diárias mais longas e a única falha do diário:

| Data | Run | Resultado | Duração |
|---|---|---|---|
| 30/08 | 33306347526 | sucesso | 13,7 min |
| 01/09 | 33497126682 | falha | 0,4 min |
| 08/09 | 34215153327 | sucesso | 11,8 min |
| 09/09 | 34339915721 | sucesso | 12,9 min |
| 10/09 | 34465768648 | sucesso | 7,9 min |

Os diários de 09/09 e 10/09 rodaram com o cache de extração zerado (regras de 08/09 e mudança de
`VERSAO_DA_EXTRACAO`) e ainda no plano gratuito do Gemini, com 20 requisições por minuto:

| | 09/09 | 10/09 |
|---|---|---|
| Coleta até a lista de candidatas | 28 s | 45 s |
| Vagas a extrair | 44 | 38 |
| Requisições feitas (mínimo com lote de 10) | 17 (5) | 15 (4) |
| Esperas de 60 s pela cota | 3 | 2 |
| Extração | 11,6 min | 6,3 min |
| Entrega por usuário | ~16 s | ~17 s |

Nesses dois dias o tempo era dominado pelas esperas de cota. O projeto passou ao plano pago em
10/09, sem hora registrada; o commit que registra o billing é das 15:18. A entrega imediata das
12:10 de 10/09 (34493849791, um perfil; 15:10 em UTC) coletou 957 vagas, extraiu 64 em 25
requisições e não esperou a cota nenhuma vez, mas não dá para afirmar que já estava no plano pago:
a cerca de 3 requisições por minuto, a ausência de espera não prova o plano. O que esse run mede,
em qualquer plano, é a latência: a extração levou ~8,2 min, cerca de 20 s por requisição. Sem as
esperas de cota, esse é o gargalo: a latência de cada chamada, somada em sequência.

## G01 — timeout de 15 min sem orçamento de tempo; estourar zera as entregas

Prioridade crítica. `.github/workflows/radar-diario.yml:14`, `radar/pipeline.py:202`,
`radar/pipeline.py:212`, `radar/pipeline.py:223` e `radar/matching/lotes.py:31`.

O desenho transforma um estouro em perda total:

- a extração roda para todos **antes** de qualquer envio (`obter_extracoes`), então um kill
  durante ela deixa todos os usuários sem mensagem;
- `guardar_extracoes` só é chamado depois que `extrator.extrair` devolve tudo, então o kill
  descarta também as extrações já pagas;
- o extrator não tem noção de tempo: só desiste quando o 429 pede espera acima de 120 s
  (`ESPERA_MAXIMA_EM_SEGUNDOS`), o que indica cota diária, não prazo;
- `GenerateContentConfig` (`radar/matching/gemini.py:43`) não define timeout por chamada, então
  uma única chamada pendurada basta para levar o job ao kill.

**Margem revista com o plano pago.** No plano gratuito a margem foi de 1,3 min em 30/08 e de
2,1 min em 09/09, e o job morreria por volta de 55 vagas novas. Sem esperas de cota, o limite
passa a ser a latência: descontados preparo, coleta e entrega, sobram cerca de 13 min, que a
~20 s por requisição comportam perto de 39 requisições. Com o #52 cada lote custa em média um
pouco mais de uma requisição, então o limite fica entre ~150 e ~350 vagas novas num run, conforme
a latência de um lote de 10, que não foi medida separada da das chamadas avulsas.

**Por que a prioridade continua crítica.** O limite subiu, mas as condições para atingi-lo são
frequentes. O cache de extração zerou em três dias seguidos (08, 09 e 10/09) por mudança de prompt
ou de catálogo; um único perfil já teve 66 candidatas às 12:10 de 10/09, antes da busca pela
região imediata, que entrou às 13:43 e amplia a coleta; e as candidatas crescem com a variedade de
cidades e áreas da coorte. Um dia de
cache zerado com alguns usuários de áreas diferentes chega a 150 vagas. A consequência não mudou:
ninguém recebe e, como as extrações não são gravadas, o dia seguinte repete a mesma fila. A
entrega também cresce: a ~17 s por usuário, só ela passa de 15 min perto dos 50 usuários, sem
extração alguma. Como o repositório é público, os minutos do Actions são gratuitos e o limite de
15 min não economiza nada.

Correção esperada:

1. **Prazo no `ExtratorEmLotes`.** Recebe `prazo_em_segundos` e um relógio injetável, no mesmo
   padrão do `esperar`. Antes de começar um lote e antes de cada espera de cota, confere se ainda
   cabe; se não, para e devolve o que já tem, como já faz no caminho da cota diária. Setting nova
   `PRAZO_DA_EXTRACAO_SEGUNDOS`, padrão 600. O resto do pipeline já trata vaga sem extração:
   quem não tem nenhuma aprovada fica para o dia seguinte (`radar/pipeline.py:298`), quem tem
   recebe, e o resumo mostra "vagas sem extração".
2. **Timeout por chamada no Gemini**, com `http_options` em `GenerateContentConfig`. O prazo só é
   conferido entre chamadas; sem timeout, uma chamada lenta atravessa o prazo.
3. **Candidatas intercaladas por usuário** em `candidatas_de_algum_perfil`
   (`radar/pipeline.py:176`). Hoje a ordem é todas as candidatas do usuário mais antigo e depois
   as novas do seguinte, porque a fila segue `order by p.criado_em`
   (`radar/storage/postgres.py:44`). Com prazo, o corte cairia sempre em quem se cadastrou por
   último, o mesmo defeito corrigido em 03/09. Intercalando, o corte se reparte.
4. **Timeout do job em 30 min e do passo do radar em 28 min.** Conta: ~1 min de coleta, até
   10 min de extração e ~17 s por usuário na entrega, o que acomoda cerca de 60 usuários. O
   timeout do passo resolve o G07 junto.

Gravar a extração a cada lote foi considerado e descartado: com o prazo, o processo sempre chega
a `guardar_extracoes` antes do kill, e gravar por lote exigiria um callback atravessando a
interface `ExtratorDeVagas` para cobrir um caso que o prazo já evita. Com o plano pago, extrair
lotes em paralelo passa a ser a alavanca direta do tempo; fica fora desta proposta até medir a
latência por lote (G02) e o limite de requisições do plano. Nenhuma das mudanças mexe no prompt,
então `VERSAO_DA_EXTRACAO` continua a mesma e nada é reextraído.

Regressões: prazo esgotado antes de um lote devolve o que já foi extraído; prazo esgotado antes de
uma espera de cota não espera; prazo não interrompe a extração uma a uma no meio de um resultado
já recebido; o corte por prazo reparte vagas extraídas entre usuários.

## G02 — lote devolve 1 de 10 vagas

Prioridade média, parcialmente resolvido pelo #52. `radar/matching/lotes.py:48`.

Nos três runs com cache zerado de 09 e 10/09, lotes voltaram com 1 de 10 extrações: um em cada
diário e dois dos sete lotes da entrega imediata das 12:10 de 10/09. As 9 que faltavam foram
extraídas sozinhas sem nenhum "Vaga … ignorada" no log, então as vagas não têm problema: a falha
é do modo em lote, e é sistemática. Não é sempre o primeiro lote: em 10/09 às 07:23 foi o
primeiro, mas às 12:10 o aviso saiu 1,5 min após o início, quando já tinham passado alguns lotes.
Até o #52, cada lote assim custava 10 requisições em vez de 1.

O que o #52 (mergeado em 10/09 às 17:23) resolveu:

- o lote incompleto registra as ids que faltaram, as devolvidas sem vaga do lote e as repetidas
  (`registrar_resposta_incompleta`), o que separa as duas hipóteses: modelo que omite vagas ou
  modelo que altera o `id_vaga`;
- as faltantes são pedidas juntas uma vez antes de ir uma a uma. A repetição é protegida: só
  acontece quando a resposta veio curta e só com ids do lote, e é descartada inteira se voltar com
  id fora do que faltou ou repetido. Custa no máximo uma requisição a mais por lote incompleto; o
  run das 12:10 teria feito cerca de 9 requisições em vez de 25, se as repetições voltassem
  completas.

A correção entrou antes do diagnóstico, ao contrário do que a primeira versão desta auditoria
recomendava, e a proteção acima justifica a inversão.

Ainda em aberto:

- **A causa.** Nenhum run rodou depois do #52; o próximo lote incompleto registra as ids e diz
  qual das duas hipóteses vale.
- **Registro do fim de cada lote, com a duração.** Lote bem-sucedido não deixa linha no log. Com o
  plano pago, a duração de cada chamada é o número que falta para fechar a margem do G01 e para
  decidir sobre lotes em paralelo.

## G03 — reexecução no mesmo dia manda segunda mensagem a todos

Prioridade alta. `radar/storage/postgres.py:34` e `radar/pipeline.py:176`.

`SQL_USUARIOS_ATIVOS` não filtra quem já foi atendido hoje, e `ids_ja_enviadas` só impede repetir
a mesma vaga. Um re-run manual ou um disparo duplo manda a cada usuário uma segunda leva (as vagas
8 a 14 do ranking) ou um segundo "nada compatível hoje".

Consequência operacional: não existe recuperação segura. Depois de uma falha parcial, o operador
não pode reexecutar sem incomodar quem já recebeu, e não dá para ter agendador de reserva. Na
falha de 01/09 ninguém reexecutou e o dia ficou perdido.

Correção esperada: registrar por perfil a data (em horário de Brasília) do último atendimento,
incluindo a mensagem de "nada compatível", que hoje não deixa linha em `envios`; o diário pula
quem já foi atendido na data. Exige migration. O run por perfil também marca a data, o que evita
duas mensagens para quem vincula de madrugada e recebe de novo às 07:23.

Regressões: segundo `rodar` no mesmo dia não envia nada a quem já recebeu; quem ficou sem entrega
por falha continua elegível no segundo run; a virada do dia segue o fuso de Brasília.

## G04 — execução ausente não gera alerta

Prioridade alta. Já registrado como pendência em `docs/plano-geral.md`.

O único sinal de que o diário não rodou é a falta do resumo das 07:23, e alguém precisa perceber
o silêncio. O ponto único de falha é grande: a conta do cron-job.org é do Ian, a configuração dele
(URL, corpo da requisição, fuso, avisos de falha) não está no repositório e o token vence em
09/09/2027.

Correção esperada: um dead man's switch. O run avisa um serviço de monitoramento ao terminar e o
serviço alerta se o aviso não chegar até as 08:00. Outra opção é um workflow vigia com `schedule`
às 09:00 que confere pela API se houve run no dia; como vigia, a falta de confiabilidade do
`schedule` pesa pouco, porque o alerta só falha se os dois falharem juntos. Um agendador de
reserva que **execute** o radar só é seguro depois do G03. Registrar a configuração do
cron-job.org no guia de publicação, sem o token.

## G05 — run por perfil em paralelo com o diário extrai as mesmas vagas duas vezes

Prioridade baixa (era média no plano gratuito).
`supabase/functions/telegram-webhook/entrega_imediata.ts:3` e `:4`.

A janela em que o vínculo espera o diário vai de 06:23 a 07:23, a hora **anterior** a ele, e
serve para economizar um run. A sobreposição acontece **durante** o diário. Quem vincula nesse
intervalo dispara um run por perfil em paralelo, e o workflow não tem `concurrency`. A trava
`pg_advisory_lock` por perfil (`radar/storage/postgres.py:322`) evita duas mensagens à mesma
pessoa.

No plano gratuito os dois runs disputavam a mesma cota de 20 requisições por minuto e empurravam o
diário para o timeout. No plano pago não há cota compartilhada a disputar; o custo que sobra é
extrair e pagar as mesmas vagas duas vezes, porque o cache só é gravado no fim de cada run (G01).

Estender a janela até as 08:00 **não** resolve: o diário lê a lista de usuários ao começar, então
quem vincula entre 07:23 e 08:00 esperaria o dia seguinte inteiro. A opção viável é um grupo de
`concurrency` comum ao diário e aos runs por perfil, com `cancel-in-progress: false`, que enfileira
o run por perfil. Limite conhecido: o GitHub mantém um só run pendente por grupo, então um segundo
vínculo durante o mesmo diário cancela o pendente do primeiro, que passa a receber no dia
seguinte. Com o custo atual, não vale fazer antes dos demais.

## G06 — run por perfil coleta vagas para a coorte inteira

Prioridade média. `radar/__main__.py:267` e `radar/pipeline.py:167`.

`executar_fluxo` monta o coletor com `repositorio.listar_ativos()`; o filtro por perfil só vem
depois, em `selecionar_usuarios`. Dois runs por perfil mostram o efeito: o de 07/09 às 22:13
(34175940414) coletou 545 vagas e o de 10/09 às 12:10 (34493849791) coletou 957, cada um de todas
as cidades e termos da coorte para atender uma pessoa. Cada vínculo custa uma coleta completa na
Adzuna (até 10 páginas por região), e esse custo cresce com o número de cidades e com a busca pela
região imediata.

Correção esperada: montar o coletor com os usuários já selecionados. Regressão: `rodar --perfil`
consulta só a cidade e os termos daquele perfil.

## G07 — `if: failure()` pode não cobrir o estouro do timeout

Prioridade média. `.github/workflows/radar-diario.yml:48`.

O GitHub trata o estouro de `timeout-minutes` do job como cancelamento, e a documentação não diz
se `failure()` vale nesse caso. Nenhum run chegou ao timeout, então não há evidência real. O aviso
existe justamente para o kill que o Python não consegue reportar.

Como verificar sem esperar um timeout real (sugestão da revisão do PR #54): um workflow descartável
com `timeout-minutes: 1`, um passo `sleep 120` e um passo `if: failure()` mostra em dois minutos
se o aviso dispara. Como `workflow_dispatch` só vale para workflow presente no branch padrão, o
teste roda por `push` numa branch descartável, apagada depois.

Correção esperada: `timeout-minutes` no passo do radar, abaixo do timeout do job, para que o passo
falhe e `failure()` valha; ou `if: failure() || cancelled()`. A primeira opção entra com o G01.

## G08 — o diário executa o `main` sem conferir o schema

Prioridade baixa. Run 33497126682.

Em 01/09 o diário caiu com `Falha ao ler as avaliações: UndefinedColumn`: o código chegou ao
`main` antes da migration ser aplicada. Os dois usuários da época ficaram sem mensagem e o próximo
run foi o de 02/09. O conserto é a ordem de publicação (migration antes do merge), já descrita no
guia; uma conferência de schema no início do run só trocaria a falha por uma mensagem mais clara.

## G09 — o horário 07:23 vive em lugares que não se conhecem

Prioridade baixa. O horário está no cron-job.org (fora do repositório), na janela em UTC de
`entrega_imediata.ts`, nos termos de uso e nas páginas. Mudar o horário no cron-job.org não quebra
teste algum e deixa a janela da entrega imediata errada em silêncio. `REPOSITORIO` e `ref: "main"`
também são constantes, o que já custou um deploy na transferência para a organização.

Correção esperada: registrar no guia de publicação que horário, janela e textos mudam juntos, e a
configuração exata do cron-job.org.

## G10 — falha do disparo imediato só aparece no log da Edge Function

Prioridade baixa. `supabase/functions/telegram-webhook/entrega_imediata.ts:38` e `:41`.

Resposta diferente de 2xx ou erro de rede vira `console.error`, que ninguém lê. O usuário fica sem
a primeira busca até o próximo diário, que pode estar a 21 horas, sem saber por quê. A validade do
`GITHUB_DISPATCH_TOKEN` não está documentada, ao contrário da do token do cron.

Correção esperada: avisar o chat de operação quando o disparo falhar e registrar a validade do
token no guia.

## Conferido e correto

- Disparo externo: 13 de 13 dias no horário desde 28/08, com três segundos de variação.
- O input `perfil` chega ao comando por variável de ambiente e é validado como UUID pelo argparse,
  então não há injeção no shell.
- A trava por perfil relê os envios depois de adquirida, e a conexão em `autocommit` confirma os
  envios antes de liberar a trava.
- Toda execução que termina se reporta ao chat de operação, com vagas sem extração e extrações não
  gravadas.
- `DIAS_RECENTES: "5"` dá folga para um ou dois dias sem execução sem perder vagas.

## Não verificado

- Configuração do cron-job.org: URL, corpo, fuso e se os avisos de falha estão ligados.
- Comportamento de `failure()` quando o job estoura `timeout-minutes` (G07); o teste descrito lá
  fecha a questão em dois minutos.
- Validade do `GITHUB_DISPATCH_TOKEN` (G10).
- Causa da perda de 9 vagas por lote (G02), que o log do #52 deve mostrar no próximo run.
- Latência de um lote de 10 separada da das chamadas avulsas, que define a margem do G01.

## Ordem sugerida

1. G01 e G07: prazo da extração, timeout por chamada, candidatas intercaladas e timeouts do
   workflow, com o teste do G07 antes. É o único achado capaz de zerar as entregas de todos.
2. G03: não reenviar a quem já foi atendido no dia.
3. G04: alerta de execução ausente.
4. G02: registro do fim de cada lote com a duração; ler o log do #52 no próximo lote incompleto.
5. G06: coleta só dos usuários do run por perfil.
6. G05, G08, G09 e G10.

Fatiamento previsto para o item 1, um commit por decisão: prazo no extrator com os testes; setting
e timeout por chamada; intercalação das candidatas com o teste; timeouts do workflow; `CLAUDE.md`.
