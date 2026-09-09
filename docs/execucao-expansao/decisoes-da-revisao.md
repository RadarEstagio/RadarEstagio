# Decisões tomadas na revisão do PR #22

Registrado em 08/09/2026, sobre a branch `codex/expansao-revenue-centric` depois de a fila
O00–R03 estar entregue. A revisão comparou o PR com o plano e as fichas; estas são as decisões
que **eu tomei** ao corrigir os achados, não decisões da equipe. Cada uma tem a alternativa
descartada e como desfazer, porque nenhuma delas foi combinada antes.

O que continua dependendo do Igor está em [decisões pendentes](#o-que-nao-decidi) no fim.

Verificação depois de todas elas: `uv run pytest -q` 666 aprovados e 25 ignorados;
`deno test --config tests/web/deno.json --allow-read --allow-env tests/web/` 52 aprovados;
`uv run ruff check .` e `uv run ruff format --check .` aprovados; `git diff --check` limpo.
Nada foi publicado, nenhuma migration foi aplicada remotamente e nenhuma tela foi inspecionada.

## Decisões visíveis para o estudante

### Habilidade digitada é cortada em 100 caracteres, sem aviso

A `0018` passou a exigir de 1 a 100 caracteres por item também no update direto, e o formulário
não limitava nada: quem digitasse mais receberia erro cru do Postgres ao salvar. Escolhi
`maxlength="100"` no campo mais recorte no `addCustomSkill`, que é o comportamento nativo de um
input — o texto simplesmente para de entrar.

- Alternativa descartada: mostrar erro no campo ao ultrapassar. Interrompe quem está digitando
  para uma regra que ninguém precisa conhecer.
- Onde: `web/index.html`, `addCustomSkill` em `web/assets/app.js`.
- Reverter: tirar o `maxlength` e o `slice`; o banco volta a ser o único a recusar.

### A 51ª habilidade é recusada com erro no campo

Aqui o corte silencioso não serve: apagar a habilidade que a pessoa acabou de escolher, sem
dizer nada, esconde uma escolha dela. O erro aparece no próprio campo, com o mesmo componente
das outras validações.

- Onde: `addCustomSkill` e `profileFromForm` em `web/assets/app.js`; teste em
  `tests/web/cadastro_test.ts`.
- Limite: o `profileFromForm` também recusa acima de 50 no envio, porque a lista pode chegar
  cheia de um perfil salvo antes da regra.

### O cartão da landing diz "Publicada hoje"

A data fixa "08/09/2026" envelhece em uma semana, justo na parte que demonstra vaga recente.

- Alternativa descartada: calcular a data por JS. Cria script para um cartão estático que já é
  declarado como exemplo ilustrativo.
- Onde: `web/index.html`.

## Decisões de métrica e relatório

### Pausa sem resposta aparece como "Não informado"

O SQL agrupa em `sem_motivo` e o relatório imprimia esse valor cru, enquanto a ficha R03 e
`docs/metricas.md` prometem "Não informado" — o rótulo que separa quem não respondeu de quem
escolheu um motivo.

- Decisão de escopo junto: **não** uniformizei o `sem_motivo` das recusas de vaga. É outra
  métrica, com outro denominador, e mexer nela seria alterar leitura fora do escopo da revisão.
- Onde: `rotulo_da_pausa` em `radar/reporting/funil.py`.

### Mediana convertida para minutos, horas ou dias na apresentação

"86400.0 s" obriga quem lê o relatório a converter de cabeça. O cálculo continua em segundos,
como a ficha M03 exige; só a impressão muda. Faixas escolhidas: abaixo de 60 s em segundos
inteiros, abaixo de 1 h em minutos, abaixo de 1 dia em horas, daí em dias, sempre com uma casa.

- Alternativa descartada: sempre a maior unidade cabível com duas casas. Perde a leitura rápida
  de "2.0 min".
- Onde: `duracao_legivel` em `radar/reporting/funil.py`.

### `vagas_enviadas` continua contando linha de envio, não par único

`recomendacoes_elegiveis_feedback` deduplica o par `(perfil, vaga)` e cobre todos os perfis;
`vagas_enviadas` conta linhas e só a coorte. Os dois números aparecem no mesmo relatório e
podem divergir. Mantive assim porque a ficha M02 proíbe mudar o significado de `vagas_enviadas`
para acomodar a métrica nova, e `docs/metricas.md` explica a diferença.

- Se um dia incomodar, a decisão é de produto, não de código: escolher qual dos dois é "vagas
  entregues" no relatório e aposentar o outro.

## Decisões de arquitetura

### A utilidade semanal passou a ter uma definição só

`semanais` calculava a utilidade da semana em subconsultas próprias e as CTEs de M04
recalculavam a mesma coisa para os fatos por área. Fiz `semanais` derivar de
`utilidade_por_perfil_semana`, então a soma por área e o total semanal são o mesmo cálculo.

- Por que assim: o fechamento de M04 é "a soma dos grupos reproduz o total semanal". Duas
  definições paralelas transformam esse fechamento em coincidência que um dia deixa de valer.
- Custo aceito: `semanais` depende de uma CTE definida depois na cláusula `with`, então a ordem
  dos blocos mudou. A consulta ficou com uma dependência a mais entre CTEs.
- Onde: `radar/storage/metricas.sql`; a igualdade virou asserção em `tests/web/metricas_test.ts`.

### `recusas_do_periodo` removida

Era cópia palavra por palavra de `respostas_do_periodo` — mesma janela, mesma deduplicação,
mesmo desempate. `grupos` passou a usar a que ficou.

### A agregação por área foi para `domain/`

`radar/storage/postgres.py` importava `radar/reporting/funil.py`, o que inverte as camadas:
classificar curso em área usa `area_do_curso` e é regra de domínio, não apresentação.

- Escolha: módulo novo `radar/domain/metricas.py`, em vez de acrescentar a função a
  `domain/models.py` (que guarda entidades) ou a `domain/areas.py` (que é o catálogo).
- O repositório continua agregando antes de devolver o funil, como a ficha M04 pede; só a
  dependência mudou de `reporting` para `domain`.

### `Field()` vazio removido de `Perfil.habilidades`

Sobrou da retirada do `min_length`. `Field()` sem argumento não declara nada.

## Decisões de publicação

### Conferir os dados antes de aplicar a `0018`

A constraint nova valida na hora e cobra um contrato que a coluna original (`cardinality >= 1`)
nunca impôs no update direto. Uma linha antiga fora do contrato aborta o `db push` no meio.
Acrescentei ao guia um passo com a consulta somente leitura que precisa devolver zero linhas.

- Alternativa descartada: criar a constraint como `not valid`. Adia a validação sem resolver,
  e o `validate constraint` falharia igual depois.
- Alternativa descartada: corrigir o dado na própria migration. A ficha C01 manda registrar o
  caso e não corrigir por suposição — o dado é de uma pessoa real.
- Onde: seção "Ordem de publicação preparada" em `docs/guia-publicacao-e-piloto.md`, passo 3;
  a numeração seguinte foi reajustada.

### Nada foi aplicado, publicado ou disparado

Não apliquei migration, não publiquei frontend, não chamei API de fonte, não disparei workflow
e não enviei mensagem de teste. Tudo isso depende de acesso e autorização que não são meus.

## Decisões de documentação e registro

### `docs/funcionalidades.md` sincronizado

Os itens 01, 02, 17 e 21 descreviam o produto anterior: conta antes do perfil, habilidade
obrigatória, pausa sem pergunta e relatório com quatro blocos. É o documento que o `CLAUDE.md`
aponta como estado atual, então desatualizado ele ensina o contrário do que existe.

### `CLAUDE.md` atualizado em três pontos

Fluxo do cadastro (conta no último passo), fim do fallback `HABILIDADES_GERAIS` para curso
desconhecido e a lista completa do que o `metricas` imprime, com o apontamento de que o
agrupamento por área é regra de domínio.

### Inspeção visual saiu do `progresso.md`

O registro afirmava ter conferido landing, cadastro e FAQ no Safari em 1280 px. Não houve
navegador nessa execução. Troquei por pendência explícita.

- Por que: verificação declarada sem evidência é pior que pendência aberta — a equipe deixa de
  olhar a tela achando que alguém já olhou.

### A revisão virou seção no `progresso.md`, sem reabrir ID

Nenhum ID voltou a "pendente". As correções entraram como uma tabela própria, porque a fila já
tinha sido fechada e o registro serve para retomar com contexto novo.

### Corpo do PR corrigido

Dizia 665 testes Python e 49 web; hoje são 666 e 52. Acrescentei a lista das correções.

## Decisões de escopo: o que deliberadamente não fiz

| Não fiz | Por quê |
|---|---|
| Voltar o limite para cinco | Você confirmou sete no app e nos testes; o PR já estava consistente |
| Rodar `deno fmt` no `app.js` | O arquivo já não era limpo antes desta branch; formatar tudo criaria um diff enorme e alheio à revisão |
| Uniformizar `sem_motivo` nas recusas de vaga | Outra métrica, outro denominador, fora do escopo |
| Mexer em peso, nota mínima, fontes, cron ou filtros | O plano proíbe sem dado do piloto |
| Reescrever `showActivation` como função de um chamador só | Simplificação sem defeito associado |
| Criar evento novo de funil para login ou edição | M01 manda registrar a lacuna, não ampliar o schema |
| Destravar os 25 testes ignorados | Dependem de `DATABASE_URL_TESTE`; ligar banco de teste é decisão de ambiente |

## Decisões de processo

- **Commits sem `Co-Authored-By`.** A regra do `CLAUDE.md` é que Claude nunca apareça como
  autor ou coautor. Se preferir o contrário, é uma linha por commit.
- **Quatorze commits fatiados por decisão**, cada um com o teste da própria fatia, seguindo a
  regra do projeto em vez de um commit único de revisão.
- **Suíte completa rodada antes de cada commit**, em comando separado.
- **Uma exceção à granularidade**: o ajuste de indentação e a linha em branco dupla do
  `app.js` entraram no commit `fix(web): limita habilidade ao que o banco aceita`, por serem do
  mesmo arquivo e triviais.

## O que não decidi

Continua com você, e está detalhado no [guia de publicação](../guia-publicacao-e-piloto.md),
na [hipótese comercial](../hipotese-comercial.md), na
[aquisição e prova](../aquisicao-e-prova.md) e na seção D01 do
[contrato do frontend](../contrato-front.md):

1. Aplicar as migrations e em que momento; o que fazer se a consulta de conferência devolver linha.
2. Revisão dos textos legais com Ian e Miguel, e os cinco pontos ainda abertos nos rascunhos.
3. Quem responde o contato, quem confere o cron e quem executa o roteiro controlado.
4. Canal de divulgação, responsável, URL final e aprovação do texto da mensagem.
5. Janela e acesso para preencher a cobertura (E02) e as faturas dos custos (E04).
6. Os oito campos da oferta (E05) e as quatro perguntas do contrato acadêmico (D01).
