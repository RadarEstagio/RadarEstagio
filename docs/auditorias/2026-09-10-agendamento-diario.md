# Auditoria do agendamento diário

Base: `888a716`, 10/09/2026. Leitura do workflow `radar-diario.yml`, do pipeline, do extrator em
lotes e da Edge Function `telegram-webhook`, confrontada com o histórico real das 33 execuções do
workflow entre 26/08 e 10/09 (`gh run list` e `gh run view --log`). Sem alteração de código, sem
chamada ao Gemini e sem envio ao Telegram. A configuração do cron-job.org fica fora do repositório
e não foi consultada; dele só se vê o efeito nos runs.

## Resumo

O disparo é confiável: desde a troca pelo cron-job.org em 28/08, os 13 dias foram disparados entre
07:23:02 e 07:23:04, sem falha nem atraso. A decisão de abandonar o `schedule` nativo está
confirmada pelos dados. Os riscos estão no que acontece depois do disparo.

| ID | Achado | Prioridade |
|---|---|---|
| G01 | Timeout de 15 min sem orçamento de tempo; estourar zera as entregas de todos | crítica |
| G02 | Primeiro lote devolve 1 de 10 vagas e dobra as requisições | alta |
| G03 | Reexecução no mesmo dia manda segunda mensagem a todos | alta |
| G04 | Execução ausente não gera alerta | alta |
| G05 | Run por perfil pode rodar em paralelo com o diário | média |
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

Onde o tempo foi gasto nos dois dias de cache zerado (09/09 depois das regras de 08/09; 10/09
depois da mudança de `VERSAO_DA_EXTRACAO`):

| | 09/09 | 10/09 |
|---|---|---|
| Coleta até a lista de candidatas | 28 s | 45 s |
| Vagas a extrair | 44 | 38 |
| Requisições feitas (mínimo com lote de 10) | 17 (5) | 15 (4) |
| Esperas de 60 s pela cota | 3 | 2 |
| Extração | 11,6 min | 6,3 min |
| Entrega por usuário | ~16 s | ~17 s |

Os piores dias são justamente os que seguem uma mudança de prompt ou de catálogo, porque o cache
de extração recomeça do zero.

## G01 — timeout de 15 min sem orçamento de tempo; estourar zera as entregas

Prioridade crítica. `.github/workflows/radar-diario.yml:14`, `radar/pipeline.py:202`,
`radar/pipeline.py:212`, `radar/pipeline.py:223` e `radar/matching/lotes.py:31`.

A margem até o timeout foi de 1,3 min em 30/08 e de 2,1 min em 09/09. O desenho transforma um
estouro em perda total:

- a extração roda para todos **antes** de qualquer envio (`obter_extracoes`), então um kill
  durante ela deixa todos os usuários sem mensagem;
- `guardar_extracoes` só é chamado depois que `extrator.extrair` devolve tudo, então o kill
  descarta também a cota já gasta;
- o extrator não tem noção de tempo: só desiste quando o 429 pede espera acima de 120 s
  (`ESPERA_MAXIMA_EM_SEGUNDOS`), o que indica cota diária, não prazo.

Cenário: mudança de prompt com uma coorte que traz 60 ou mais vagas novas. O job morre por volta
dos 15 min, ninguém recebe, e no dia seguinte a mesma fila é reextraída e morre de novo. A entrega
também cresce: a ~17 s por usuário, só ela passa de 15 min perto dos 50 usuários, sem extração
alguma. Como o repositório é público, os minutos do Actions são gratuitos e o limite de 15 min
não economiza nada.

Correção esperada:

1. **Prazo no `ExtratorEmLotes`.** Recebe `prazo_em_segundos` e um relógio injetável, no mesmo
   padrão do `esperar`. Antes de começar um lote e antes de cada espera de cota, confere se ainda
   cabe; se não, para e devolve o que já tem, como já faz no caminho da cota diária. Setting nova
   `PRAZO_DA_EXTRACAO_SEGUNDOS`, padrão 600. O resto do pipeline já trata vaga sem extração:
   quem não tem nenhuma aprovada fica para o dia seguinte (`radar/pipeline.py:298`), quem tem
   recebe, e o resumo mostra "vagas sem extração".
2. **Timeout por chamada no Gemini.** O prazo só é conferido entre chamadas e
   `GenerateContentConfig` (`radar/matching/gemini.py:43`) não define `http_options`; sem
   timeout explícito, uma chamada lenta atravessa o prazo.
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
interface `ExtratorDeVagas` para cobrir um caso que o prazo já evita. Nenhuma das mudanças mexe no
prompt, então `VERSAO_DA_EXTRACAO` continua a mesma e nada é reextraído.

Regressões: prazo esgotado antes de um lote devolve o que já foi extraído; prazo esgotado antes de
uma espera de cota não espera; prazo não interrompe a extração uma a uma no meio de um resultado
já recebido; o corte por prazo reparte vagas extraídas entre usuários.

## G02 — primeiro lote devolve 1 de 10 vagas

Prioridade alta, por ser a maior alavanca de tempo. `radar/matching/lotes.py:59`.

Nos dois dias um lote registrou "9 vagas sem extração no lote; extraindo uma a uma". Em 10/09 foi
o primeiro, 20 s depois do início. Em 09/09 o log não permite dizer qual: a primeira chamada levou
429 quatro segundos após o início, e lote bem-sucedido não deixa linha, então há 3 min sem
registro até o aviso. Nos dois dias as 9 foram extraídas sozinhas sem nenhum "Vaga … ignorada"
no log, então as vagas não têm problema: a falha é do modo em lote. Isso transforma 1 requisição em 10 e é o que
provoca as esperas de cota. Se o lote voltasse inteiro, 09/09 teria feito cerca de 5 requisições
em vez de 17, e a extração cairia de 11,6 para uns 3 minutos.

Causa não diagnosticada. O log só conta as faltantes e não separa duas hipóteses: o modelo
devolveu 1 item só, ou devolveu 10 com o `id_vaga` alterado. O prompt pede o id "copiado sem
alteração", mas nada confere o que volta. A repetição em dois dias seguidos, sempre no primeiro
lote, aponta para algo sistemático e não para acaso.

Correção esperada: registrar no log os `id_vaga` devolvidos que não casaram com nenhuma vaga do
lote, e registrar também o fim de cada lote bem-sucedido, para que o log mostre qual lote falhou.
Se for id alterado, a correção é no casamento; se for omissão, reenviar as faltantes em lote antes
de extrair uma a uma. Não corrigir antes do diagnóstico.

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

## G05 — run por perfil pode rodar em paralelo com o diário

Prioridade média. `supabase/functions/telegram-webhook/entrega_imediata.ts:3` e `:4`.

A janela em que o vínculo espera o diário vai de 06:23 a 07:23, a hora **anterior** a ele, e
serve para economizar um run. A sobreposição acontece **durante** o diário, que roda das 07:23 até
cerca de 07:37 nos dias de cache zerado. Quem vincula nesse intervalo dispara um run por perfil em
paralelo; os dois disputam a mesma cota de 20 requisições por minuto do Gemini e extraem as mesmas
vagas, porque o cache só é gravado no fim (G01). O workflow não tem `concurrency`. A trava
`pg_advisory_lock` por perfil (`radar/storage/postgres.py:322`) evita duas mensagens à mesma
pessoa, mas não resolve a disputa de cota.

Estender a janela até as 08:00 **não** resolve: o diário lê a lista de usuários ao começar, então
quem vincula entre 07:23 e 08:00 esperaria o dia seguinte inteiro. A opção viável é um grupo de
`concurrency` comum ao diário e aos runs por perfil, com `cancel-in-progress: false`, que enfileira
o run por perfil. Limite conhecido: o GitHub mantém um só run pendente por grupo, então um segundo
vínculo durante o mesmo diário cancela o pendente do primeiro, que passa a receber no dia
seguinte. Com o G01 e o G02 resolvidos, a sobreposição dura poucos minutos; a prioridade cai.

## G06 — run por perfil coleta vagas para a coorte inteira

Prioridade média. `radar/__main__.py:267` e `radar/pipeline.py:167`.

`executar_fluxo` monta o coletor com `repositorio.listar_ativos()`; o filtro por perfil só vem
depois, em `selecionar_usuarios`. O run por perfil de 07/09 às 22:13 (34175940414) coletou 545
vagas de todas as cidades e termos da coorte para atender uma pessoa. Cada vínculo custa uma coleta
completa na Adzuna (até 10 páginas por região), e esse custo cresce com o número de cidades.

Correção esperada: montar o coletor com os usuários já selecionados. Regressão: `rodar --perfil`
consulta só a cidade e os termos daquele perfil.

## G07 — `if: failure()` pode não cobrir o estouro do timeout

Prioridade média. `.github/workflows/radar-diario.yml:48`.

O GitHub trata o estouro de `timeout-minutes` do job como cancelamento, e a documentação não diz
se `failure()` vale nesse caso. Não verificado na prática: nenhum run chegou ao timeout. O aviso
existe justamente para o kill que o Python não consegue reportar.

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
- Comportamento de `failure()` quando o job estoura `timeout-minutes` (G07).
- Validade do `GITHUB_DISPATCH_TOKEN` (G10).
- Causa da perda de 9 vagas num lote (G02), e em 09/09 qual lote foi.
- Por que a primeira chamada de 09/09 já recebeu 429, quatro segundos após o início, sem outro
  run em andamento. Pode ser um limite diferente do de requisições por minuto.

## Ordem sugerida

1. G01 e G07: prazo da extração, timeout por chamada, candidatas intercaladas e timeouts do
   workflow. É o único achado capaz de zerar as entregas de todos.
2. G02: log dos ids não casados; a correção vem depois do diagnóstico.
3. G03: não reenviar a quem já foi atendido no dia.
4. G04: alerta de execução ausente.
5. G06: coleta só dos usuários do run por perfil.
6. G05, G08, G09 e G10.

Fatiamento previsto para o item 1, um commit por decisão: prazo no extrator com os testes; setting
e timeout por chamada; intercalação das candidatas com o teste; timeouts do workflow; `CLAUDE.md`.
