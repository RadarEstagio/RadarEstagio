# Protocolo de execução autônoma

## Missão e ponto de entrada

Quando o usuário pedir para implementar o plano, execute a fila inteira do índice
`docs/plano-expansao-revenue-centric.md`, uma tarefa por vez, sem pedir ao usuário que escolha
o próximo ID. Termine a tarefa, teste, registre e continue. Se o usuário limitar o pedido a
um ID, execute apenas esse ID. A segmentação limita o tamanho de cada mudança, não a autonomia.

Leia primeiro `CLAUDE.md`, `CONTEXT.md`, o índice e este protocolo. Procure `AGENTS.md`
aplicável. Depois leia apenas a ficha ativa e seus arquivos de entrada. Caminhos nas fichas
são relativos à raiz. Use `rg`; se indisponível, use `grep`/`find`.

## Preparação e base

1. Execute `git status --short`, `git log -5 --oneline` e `git fetch origin` quando houver rede.
   Compare com `origin/main`. A base revisada é `40ed28c`; nenhum SHA documental é ordem para voltar a uma versão antiga.
2. Preserve trabalho local de outras pessoas. Não faça reset, limpeza ou push forçado.
   Use uma branch de trabalho baseada na main atual; se a árvore estiver suja, mantenha o
   trabalho preservado e escolha checkout/worktree seguro. Não reabra uma branch já mergeada
   por conveniência nem crie um novo repositório.
3. Confira se cada entrega já existe: código prevalece sobre status documental desatualizado.
   Se existir, valide e marque, sem reaplicar migration ou duplicar teste/componente.
4. Rode a linha de base apropriada e registre falhas preexistentes separadamente. Uma falha
   introduzida pelo trabalho deve ser corrigida antes de encerrar sua tarefa.

## Ciclo por tarefa

- Selecione o primeiro ID não concluído na ordem dos blocos do índice cujas dependências
  de código estejam implementadas. A posição da ficha no arquivo não muda essa ordem.
- Declare brevemente o comportamento a alterar. Leia símbolos/testes relevantes, não o repo inteiro.
- Implemente o menor conjunto coeso de mudanças que atende à ficha. Arquivos citados são pontos
  de entrada; ajustar contrato/teste diretamente afetado é permitido. Não refatorar partes alheias.
- Para comportamento, cálculo ou banco, adicione regressões observáveis e confirme o resultado.
  Para copy, verifique visualmente sem criar teste que só repete a frase.
- Atualize o índice e `progresso.md`, registre verificações e eventual publicação pendente.
- Se commits estiverem autorizados, use Conventional Commits em português e as regras de
  commit/push do projeto; não misture IDs independentes nem arquivos alheios. Push da branch
  não significa deploy, e este plano não pede merge automático na main.
- Continue o próximo ID. Não encerre a execução apenas porque um lote está pronto.

## Limites e decisões já resolvidas

Manter HTML/CSS/JS estático, Python e Supabase. Usuários recebem **até cinco vagas**; sete é
somente configuração de teste local. Não introduzir framework, dashboard, checkout, outra fonte,
recompensa ou pesos por área sem a tarefa específica. Não reintroduzir cache de notas.

Migrations novas são incrementais. Escolher o próximo número disponível, sem editar 0001–0017.
Não escrever comentários no código. Não enfraquecer Auth, RLS, consentimento ou CAPTCHA.
Não salvar senha em storage, evento, log ou fixture de dados reais. Não imprimir segredos.

As decisões técnicas fechadas nas fichas podem ser implementadas sem nova confirmação. Uma
preferência estética opcional não bloqueia a fila. Se houver contradição material com código
mais recente, registre o fato, adapte preservando o objetivo e teste; pergunte somente se a
resolução depender de regra de negócio que não foi definida.

## Dependências externas sem paralisar o trabalho

O escopo executável tem 16 tarefas O00–R03 e seis fichas E01–E05/D01 de evidência/decisão.
Para essas seis, produza os documentos preparatórios descritos mesmo sem contas externas.
Preencha dados comprovados; marque o resto como “não verificado”, “não medido” ou “decisão da
equipe”. Não preencher lacunas com estatísticas fictícias nem transformar hipótese em resultado.

Falta de acesso bloqueia só a operação dependente, não outra tarefa local. Agrupe pendências
externas e prossiga. Autorização já dada na sessão vale; não pedir de novo por rotina. Se for
necessário obter uma decisão para cobrança, gasto, divulgação ou acesso, primeiro prepare o
resultado concreto revisável. Não enviar mensagens a terceiros sem autorização explícita.

## Verificações

- Python direcionado: `uv run pytest -q` seguido dos caminhos reais de teste da ficha.
- Python completo antes de commit: `uv run pytest -q`, em comando separado; conferir exit code.
- Lint: `uv run ruff check .` e `uv run ruff format --check .`.
- Web/banco isolado: `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/`.
- Funções alteradas: ler seu `deno.json` e executar a tarefa/ comando definido no diretório;
  não supor que a configuração da raiz resolve imports. Se funções não mudaram, não repetir.
- Diff: `git diff --check`; corrigir erros novos. Não reformatar referências de skills alheias.

Nos testes de migration, conferir que o harness aplica também as migrations novas. Executar
schema anterior → inserir perfil preexistente → aplicar migration → testar leitura/escrita,
rejeições e propriedade dos dados. Não substituir esse teste por busca de texto no SQL.

Interface: inspecionar 375 px e 1280 px, foco de teclado, Enter e ausência de overflow nas
áreas modificadas. JSDOM não é prova de layout. Se navegador não estiver disponível, declarar
verificação visual pendente, completar os testes disponíveis e seguir outras tarefas locais.

Não mudar expectativas só para a suíte passar. Não reportar teste ignorado como executado.
Ao fim da fila, rodar Python completo, web/banco, lint e formatação na versão final. Repetir
verificação adicional somente se houver mudanças, falhas ou dúvidas materiais novas.

## Comandos nomeados nas fichas

Executar a partir da raiz. As letras são atalhos documentais, não comandos shell definidos.
Rodar somente a bateria necessária à tarefa, além do Python completo obrigatório antes de commit.

| Código | Comando exato | Uso |
|---|---|---|
| P | `uv run pytest -q tests/test_models.py tests/test_avaliacoes.py tests/test_storage_postgres.py` | Leitura e pontuação de perfil |
| W | `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/cadastro_test.ts` | Fluxos de cadastro/conta |
| B | `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/migrations_test.ts` | Migration e escrita com permissões |
| Q-SQL | `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/metricas_test.ts` | SQL das métricas com banco isolado |
| Q-Python | `uv run pytest -q tests/test_funil.py tests/test_storage_postgres.py` | Modelo, conversão e relatório |

“Rodar Q” significa executar Q-SQL e Q-Python, conferindo os dois resultados. O harness SQL
de métricas cria schema reduzido próprio; ao adicionar colunas, atualizar esse schema. O harness
de migrations tem outro propósito e precisa aplicar migrations reais. Um não substitui o outro.
Testes Postgres ignorados por ausência de ambiente continuam pendentes, mesmo com os demais verdes.

## Tamanho de trabalho e fechamento de um ID

As subseções numeradas são passos internos da mesma tarefa. Executar e verificar um passo
antes do seguinte, sem abrir mudanças de outro ID. Se o contexto ficar curto, registrar
subpasso exato, arquivos alterados, testes executados e próximo comando em `progresso.md`.
Não marcar um ID concluído apenas porque seu primeiro subpasso foi implementado.

Registro mínimo por ID:

- Antes → depois observado, arquivos e símbolos alterados.
- Cenários da matriz: resultado por caso e teste que o demonstra.
- Comandos, exit code, aprovados/ignorados e inspeção visual quando aplicável.
- Commit/branch, dependência de publicação e qualquer limitação ainda real.

Critério objetivo: todas as linhas obrigatórias da ficha passaram ou há bloqueio explicitamente
registrado. Caso sintético comprova comportamento, não frequência do problema em produção.
Não relaxar contrato nem mudar expectativa de teste para mascarar falha encontrada.

## Publicação e compatibilidade

Implementar não exige publicar. Nunca disparar o job para toda a base para testar código.
Operações reais seguem E01, conta apropriada e autorização existente da sessão.

C01–C03 são tarefas separadas no código, mas formam uma entrega compatível.
Ordem de implementação local: C01 → C02 → C03. C01 prepara a migration sem aplicá-la
remotamente. Ordem de publicação obrigatória (diferente da fila local):

1. Disponibilizar Python que aceita arrays vazios (C02), ainda compatível com banco antigo.
2. Aplicar migration de C01, preservando todos os perfis e permissões.
3. Disponibilizar frontend C03 que passa a permitir explicitamente o caminho vazio.

Não inverter essa sequência e deixar job antigo ler um perfil que não consegue interpretar.
Para R01–R02: coluna/permissão no banco primeiro; frontend que escreve o motivo depois.
Não executar rollback restaurando restrição que rejeita dados novos. Se precisar reverter,
primeiro desativar entrada nova no frontend e manter leitores compatíveis; documentar caso a caso.
Se deploy automático for detectado, preparar as etapas compatíveis antes de merge/publicação.

## Continuidade e retomada

Atualize `docs/execucao-expansao/progresso.md` ao concluir cada ID e antes de perder contexto.
Na retomada: leia o registro, confira Git e recomece do primeiro ID ainda aberto. Não repetir
testes já registrados para a mesma versão sem motivo. Falha interrompida fica como “Em execução”,
com comando/erro e próximo passo. Registro sem evidência não é conclusão.

## Condição de término

A execução local está concluída quando os 16 IDs O00–R03 estão implementados e verificados,
os seis artefatos E01–E05/D01 foram preparados com dados/decisões faltantes identificados,
e a suíte final foi registrada. Se houver bloqueio real em um ID local, concluir os demais
e relatar exatamente esse impedimento, sem afirmar implementação completa.

A resposta final deve separar: implementado/testado; publicado/verificado remotamente;
pendências externas. Informar commits/branch se existirem e o próximo passo concreto. Não
confundir o término da implementação com validação de mercado ou comprovação de cobertura.
