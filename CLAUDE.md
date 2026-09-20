# Radar de Estágio

Agente de IA que garimpa sites de vagas de estágio todos os dias e entrega, via Telegram,
apenas as oportunidades compatíveis com o perfil do usuário — ranqueadas e explicadas.

Resumo do produto em `docs/funcionalidades.md`, arquitetura detalhada em `docs/arquitetura.md`,
decisões do motor em `docs/decisoes-do-motor.md`, próximos passos em `docs/plano-geral.md`.

## Fase atual: MVP de validação com usuários (Fase 2, em andamento)

Funcionando hoje: vagas da Adzuna (a Gupy saiu em 12/09 pelos termos de uso), banco Supabase com perfis,
vagas, avaliações, envios e eventos de produto por usuário, cadastro web com conta e vínculo
com o Telegram, extração de fatos por IA e pontuação determinística de compatibilidade, entrega da mensagem ranqueada no Telegram,
agendamento diário, deduplicação e histórico entre execuções, ativação operacional registrada
na primeira recomendação entregue e funil instrumentado da landing à primeira recomendação.

Ainda não disponível: painel web de métricas. Jooble está implementado, mas desligado por padrão. O feedback
já molda o ranking na v1 (05/09/2026): "já vi essa" alimenta o filtro de republicação do
usuário, e subárea com 2+ recusas por "não é da minha área" em 30 dias perde o fator de
interesse (teto 65 e aviso próprio), tudo por usuário e sem IA; "pedem demais", "local ou
modalidade" e o reforço positivo de "vaga útil" ficam para a v2, com dados do piloto.

Pendências da Fase 2: validar o produto com estudantes. A cota do Gemini deixou de ser pendência
em 03/09/2026: a extração passou a ser por vaga e reaproveitada entre usuários, então o trabalho
não se repete por usuário. Desde 10/09/2026 a API do Gemini está no plano pago: a cota diária
deixou de ser o limite, e o que pesa é o custo por requisição e o tempo de execução.

## Stack

Python; dependências em `pyproject.toml`. O que o manifesto e o código não dizem sozinhos:

- **Adzuna**: API oficial e gratuita, com chave.
- **Gupy**: desligada desde 12/09/2026. Os termos proíbem agregar vagas e o endpoint usado
  (`employability-portal.gupy.io/api/v1/jobs`) é interno; ver "Termos de uso das fontes". LinkedIn
  está fora de escopo: bloqueia coleta automatizada.
- **Fontes ativas** vêm de `FONTES` (padrão `adzuna`) e são somadas por `ColetorComposto`,
  que ignora uma fonte fora do ar e só falha se nenhuma responder. Fonte nova só entra se a
  validação comprovar cobertura insuficiente.
- **Jooble**: coletor pronto e **desligado por padrão**. A chave gratuita tem 500 requisições
  no total, não por mês, então não ligar em produção sem parceria; a sondagem que mediu
  +35% de cobertura está em `docs/decisoes-do-motor.md`.
- **IA de extração**: Google Gemini (modelos Flash), com dois adapters — Gemini Developer API
  para CI/produção e Antigravity CLI (`agy`) para testes locais. `AVALIADOR` escolhe qual; o
  padrão é `gemini_api` e o GitHub Actions não define a variável, portanto segue nele.
  `AVALIADOR=agy` dispensa `GEMINI_API_KEY` e usa `AGY_MODELO` e `AGY_TIMEOUT_SEGUNDOS`, com o
  comando `agy` autenticado localmente; `python -m radar verificar` mostra o adapter ativo. A IA
  **só extrai fatos da vaga**; quem compara com o perfil e calcula a nota é Python, sem IA.
- **Telegram**: bot `RadarEstagio_bot`; o job só envia mensagens.
- **Link rastreável**: o link de cada vaga na mensagem passa pela Edge Function `ir`, que registra
  `vaga_aberta` e redireciona para a fonte. O endereço vem de `URL_DE_RASTREIO`; vazio ou sem
  banco, a mensagem volta a apontar direto para a vaga. O banco guarda só a primeira abertura de
  cada envio (ver "Aberturas, pausas e vínculos repetidos").
- **Feedback individual**: o teclado numerado acompanha a mensagem diária. Cada número abre
  título e empresa com uma opção positiva e seis recusas, incluindo `motivo_nota` e
  `motivo_encerrada` ("Vaga encerrada", ver "Vaga fechada na origem"). A última
  resposta por recomendação vale nas métricas; cliques repetidos não multiplicam vagas.
- **Leitura do funil**: `python -m radar metricas` imprime, direto do banco, o funil da coorte dos
  últimos 30 dias, a participação no feedback, as medianas observadas até a primeira entrega e a
  primeira abertura, a utilidade semanal e por área do curso, as contas pausadas por motivo, a
  quebra das recusas por motivo e o custo de extração por usuário ativado. As definições estão em
  `docs/metricas.md`; a consulta fica em `radar/storage/metricas.sql` e o agrupamento por área,
  que é regra de domínio, em `radar/domain/metricas.py`. Mediana é tempo observado, nunca prazo.
- **Entrega imediata**: ao gravar o `chat_id`, a `telegram-webhook` dispara o workflow com o
  input `perfil` e o pipeline atende só quem está pendente (`rodar --perfil <id>`). Vínculo
  entre 06:23 e 07:23 de Brasília espera o diário, `/start` repetido não dispara de novo
  (`0021`) e a marca de atendido só é gravada depois da mensagem. O porquê está em
  `docs/decisoes-do-banco.md`.
- **Agendamento**: o workflow do GitHub Actions só tem `workflow_dispatch`. Quem dispara às
  07:23 de Brasília é um job no cron-job.org chamando a API `dispatches` com fine-grained
  token — o `schedule` nativo ficou 2 dias sem disparar e foi removido.
- **Ações por hash e token só de leitura** (13/09/2026): o job diário recebe os segredos de
  produção, e o dono de uma ação pode mover a tag dela para outro commit. Toda `uses:` aponta para
  o hash de 40 caracteres, e todo workflow declara `permissions: contents: read` no topo; permissão
  maior só no job que precisar, com o motivo no commit. O checkout leva `persist-credentials:
  false`, para o token não ficar no `.git/config` ao alcance do radar e das dependências, e o
  `setup-uv` instala o uv `0.12.5`, o mesmo usado localmente: sem `version:` ele baixaria o mais
  novo, que roda no passo dos segredos. `tests/test_workflows.py` cobra essas regras e guarda em
  `VERSAO_DE_CADA_ACAO` a versão de cada hash, porque o YAML não leva comentário. O Dependabot
  abre um PR semanal das ações, 7 dias depois de cada versão sair, e o teste falha até alguém
  registrar no mapa a versão nova, conferida com `git ls-remote`. A versão do uv o Dependabot não
  toca: sobe à mão, junto com o uv local.
- **Persistência**: PostgreSQL gerenciado (Supabase), opcional. Com `DATABASE_URL` o job lê os
  usuários do banco e guarda vagas, notas e envios; sem ela roda com o perfil fixo e sem
  histórico.
- **Chaves de API**: por variável de ambiente (`.env`, nunca commitado). Os secrets do
  repositório têm os mesmos nomes das variáveis do `.env`.

## Arquitetura

As camadas de `radar/` estão detalhadas em `docs/arquitetura.md`. A regra que o código não
ensina sozinho: **módulos internos dependem de interfaces do `domain/`, nunca de detalhes de
infraestrutura** (API específica, formato de mensagem, driver de banco). `pipeline.py` orquestra
coleta → dedupe → pré-filtro → extração (uma vez, para todos) → pontuação por perfil → entrega,
sem lógica de negócio própria. Fonte nova se
pluga implementando a interface de coleta, sem alterar o restante do sistema. Sem abstrações
prematuras nem código para casos hipotéticos futuros.

## Decisões técnicas

### Banco de dados: PostgreSQL, não SQLite

SQLite não sobrevive ao GitHub Actions, que destrói a máquina a cada execução, e versionar o
`.db` exporia `chat_id` num repositório público. A escolha é PostgreSQL gerenciado no Supabase,
com `JSONB` para o payload das vagas. As alternativas avaliadas e o porquê de cada recusa estão
na [arquitetura](docs/arquitetura.md).

### Bibliotecas

Sem framework web: a aplicação é um script disparado por cron, não um serviço HTTP.
`psycopg` 3 acessa o PostgreSQL com SQL puro, sem ORM.

`python-telegram-bot` não entra em fase alguma: o bot só envia mensagens (uma requisição
HTTP simples). O `/start` do vínculo e os callbacks de feedback chegam por webhook a uma Edge
Function do Supabase, fora do `radar/`.

### Cadastro no site, não no bot

O cadastro conversacional pelo bot foi substituído por um site com conta. Motivos: dados
de perfil são estruturados (lista de habilidades, período, modalidade) e um formulário é
mais claro que uma conversa; o bot continua sem estado e sem máquina de conversa; o Supabase já
resolve conta (Auth) e banco de uma vez.

A conta ficou por último no formulário: pedir e-mail e senha antes de qualquer valor entregue
cobra o preço antes de mostrar o produto. `signup` só é chamado no envio do último passo, nunca
ao avançar entre etapas, e login e edição continuam com seus próprios passos.

Fluxo: o usuário preenche o perfil no site → cria a conta no último passo → clica no botão do
Telegram, que abre `t.me/RadarEstagio_bot?start=<token>` com um token único da conta →
o Telegram chama o webhook (Edge Function do Supabase) com `/start <token>` → a função
grava o `chat_id` no perfil daquela conta. A partir daí o job diário lê os perfis com
`chat_id` do banco no lugar do `perfil_fixo` e envia uma mensagem por usuário.

O frontend é uma landing estática integrada ao Supabase. O contrato entre o site e o `radar/` é
o schema do banco: o site escreve `perfis`, o `radar/` lê
`perfis` e escreve `vagas` e `avaliacoes`. Nenhum dos dois expõe API para o outro. O
contrato completo para o front está em `docs/contrato-front.md`.

Os pós-mortems do site — volta à aba, armazenamento bloqueado, rascunho por dona, navegação no
celular e ações que conferem a conta mostrada — estão em `docs/contrato-front.md`. As regras que
valem ao mexer no `app.js`:

- **Toda leitura e escrita de `localStorage`/`sessionStorage` fica em `try`**, e a sessão de
  eventos cai para um UUID em memória quando o armazenamento está bloqueado.
- **Esconder a conta é sempre `esconderConta()`**, nunca `hidden = true`: um `<dialog>` aberto com
  `showModal` e escondido trava a página, e no celular não há Esc.
- **Ação da conta que chama o Supabase passa por `recusarSeASessaoMudou`** e filtra pelo
  `contaMostrada`, porque a sessão pode ter trocado em outra aba.
- **O rascunho do cadastro só reabre para a mesma dona**, sem senha nem e-mail, e qualquer troca
  de dona limpa tudo.
- **Curso, cidade e habilidade têm o mesmo teto do banco no `maxlength`**, e habilidade digitada
  nunca é separada por vírgula.

## Regras do projeto (obrigatórias)

- **Nunca usar comentários no código.** Nomes de variáveis/funções/classes devem ser
  autoexplicativos.
- **Código organizado e com arquitetura limpa**, seguindo a separação de camadas acima.
  Sem abstrações prematuras nem código para casos hipotéticos futuros.
- **Repositório GitHub público.**
- **Claude/IA nunca deve aparecer como contribuidor, autor ou co-autor.** Commits usam
  exclusivamente a identidade git já configurada do usuário — nunca incluir assinatura,
  menção ou "Co-Authored-By" de Claude/Anthropic nos commits.
- **Commits atômicos**: cada commit representa uma mudança coesa e completa. Sempre
  seguir o ciclo `git add` → `git commit` → `git push` ao final de um commit.
- **Commits pequenos, fatiados por decisão**: uma mudança que atravessa camadas vira uma
  sequência de commits (o refactor do módulo em um, a etapa nova do pipeline em outro, a
  religação da CLI em outro, migration e docs separados), nunca um commit único
  multi-assunto. Os testes de cada fatia entram no commit da própria fatia.
- **Suíte verde antes de cada commit**: rodar `uv run pytest -q` em um comando separado e
  conferir o resultado; nunca encadear teste e commit com pipe no meio (`pytest | tail`
  engole o código de saída e deixa commit passar com teste quebrado).
- **Conventional Commits** (conventionalcommits.org) em toda mensagem de commit:
  - Formato da primeira linha: `tipo(escopo): descrição`. Escopo é opcional e nomeia a
    camada ou módulo afetado (`collectors`, `settings`, `ci`...).
  - Tipos: `feat` (funcionalidade nova), `fix` (correção), `docs`, `test`, `refactor`
    (sem mudar comportamento), `perf`, `style` (formatação), `build` (dependências),
    `ci` (GitHub Actions), `chore` (manutenção que não se encaixa nos demais).
  - Descrição em português, minúscula, no presente do indicativo, sem ponto final,
    até 72 caracteres. Ex.: `feat(collectors): adiciona coletor da Adzuna`.
  - Corpo opcional, separado por linha em branco, explicando o *porquê* da mudança.
  - Mudança incompatível: `!` após o tipo/escopo (`feat(settings)!: ...`) e rodapé
    `BREAKING CHANGE: <explicação>`.
- **`.gitignore` sempre atualizado**: nunca commitar segredos (`.env`), bancos locais,
  ambientes virtuais ou artefatos de build.
- **Decisão nova é registrada no documento dono**, nunca aqui: motor e extração em
  `docs/decisoes-do-motor.md`, banco e funções em `docs/decisoes-do-banco.md`, site em
  `docs/contrato-front.md`, publicação no guia, pendência no plano geral. O `CLAUDE.md` só
  recebe o que um agente precisa **seguir**, em até cinco linhas, com link para o registro.
  Sem essa regra o arquivo volta a crescer: passou de 618 linhas em 13/09 para 2.126 em 18/09,
  sempre por relato de correção.

## Estado do projeto

O catálogo atual está em `docs/funcionalidades.md`. Abaixo
só o conhecimento operacional que não dá para reconstituir lendo o código.

### Termos de uso das fontes (12/09/2026)

Leitura dos termos no texto original. As medições da cota, da coleta resiliente e do
enriquecimento estão em `docs/decisoes-do-motor.md`. O que obriga:

- **Adzuna, uso 1.** Os termos permitem "Publishing Adzuna ad listings" sem prazo. O teste de
  14 dias e a proibição de agregação ("vacancy counts, average salaries") estão no parágrafo de
  "Any other use". O Radar publica anúncios com link para a página da Adzuna (o `redirect_url`,
  com o nosso app id), então cai no uso 1. Confirmação por escrito pedida no e-mail à Adzuna.
- **Atribuição em cada anúncio exibido**: "Jobs by Adzuna", com "Jobs" ligado a adzuna.com.br e
  "Adzuna" sendo o logo, também com link, em pelo menos 116×23 px. No Telegram vai o texto com
  os dois links, porque mensagem de texto não tem imagem (aprovação pedida no e-mail). No site
  vai o selo com `web/assets/adzuna-logo.png`, o logo oficial servido pelo site de
  desenvolvedores da Adzuna; no tema escuro ele ganha fundo branco, sem mudar as cores.
- **Limites da Adzuna**: 25 requisições por minuto, 250 por dia, 1.000 por semana e 2.500 por
  mês. `CotaDaAdzuna` segura o ritmo, grava o uso em `uso_das_fontes` (`0020`) e para a coleta
  quando acaba o saldo; a entrega imediata ainda reserva o que o diário vai gastar. Cota zerada
  vira erro de coleta, nunca "nenhuma vaga".
- **Nunca contatar anunciante que veio da Adzuna**: "Any attempt to contact a third party, even
  where they provide listings content, will be considered a breach".
- **Se o acordo acabar**, apagar "all insertion codes and data acquired from Adzuna".
- **Gupy desligada.** Os termos proíbem "aggregate, copy, or duplicate parts of Gupy Recruitment
  and Selection, including expired job opportunities", e o endpoint usado é interno. Era 7% dos
  envios (17 de 252). O coletor fica no código para o caso de autorização; sem ela, não religar.
- **Jooble não é saída sem parceria**: a chave gratuita tem "a total lifetime limit of 500
  requests per key" e devolve só um trecho da descrição.
- **Alternativas medidas.** Greenhouse, Lever e Ashby têm API pública de vagas sem login, mas a
  documentação trata das vagas da própria empresa e não dá licença a terceiros; em 12/09 havia 36
  estágios em 6 empresas brasileiras nesses boards, quase todos em SP e BH. A Adzuna tem programa
  de parceiros ("a sponsored feed of ads for your site… generate more revenue for you"), o
  caminho para receita sem cobrar do estudante.

### Cota e modelo do Gemini

As medições que sustentam lote, prazo, raciocínio e tratamento de erro estão em
`docs/decisoes-do-motor.md`. O que vale saber para operar:

- Padrão `gemini-3.6-flash` (`GEMINI_MODELO`). O `gemini-2.5-flash` foi recusado pela API como
  indisponível para contas novas.
- O projeto está no plano pago desde 10/09/2026. Na cota gratuita, o `gemini-3.6-flash` tinha 20
  requisições por minuto, e os limites variam por modelo, projeto e janela. Por isso a extração vai em lotes (`GEMINI_VAGAS_POR_LOTE`,
  padrão 10), com repartição do lote que falha e espera pelo "retry in Ns" do 429; acima de
  120 s a espera indica cota diária e o job desiste devolvendo o que já tem.
- **A extração cabe num prazo** (`PRAZO_DA_EXTRACAO_SEGUNDOS`, 600) e cada chamada num
  timeout (`GEMINI_TIMEOUT_SEGUNDOS`, 120). Esgotado o prazo, ela para e devolve o que tem, e
  o resumo mostra "vagas sem extração"; o job tem 30 minutos e o passo do radar, 28.
- **A extração não se repete por usuário:** o prompt não tem perfil, então cada vaga é
  extraída uma vez, guardada em `vagas.extracao` com a versão do prompt, e serve todos.
- **`GEMINI_RACIOCINIO=low` é o padrão da extração** (R$ 0,066 por lote de 10, ~12 s); o juiz
  segue no modo padrão. Trocar o nível não invalida o cache.
- **Erro do avaliador tem regra por tipo:** 429 espera a cota, 502/503/504 e resposta que o
  SDK não lê repetem o mesmo lote, 500 repete uma vez e depois divide, e só entra extração
  com id de uma vaga do lote pedido.
- **Evitar rodar `avaliar`/`rodar` repetidamente sem necessidade.**

### Motor de recomendação: regras que não podem quebrar

O porquê de cada regra, com os números medidos, está em `docs/decisoes-do-motor.md`. Antes de
mexer em coleta, pré-filtro, extração, pontuação ou mensagem, ler a seção correspondente.

- **Não ajustar peso da nota sem `vaga_irrelevante` real.** Pesos em `matching/avaliacoes.py`.
- **Ausência não é veto.** Requisito ausente do perfil vale como incerteza, e lista vazia de
  habilidades significa "não informou". Requisito com nível exige que o perfil declare nível
  igual ou maior.
- **Computação não compara habilidade por palavras** (nem perfil nem vaga); família explícita
  decide sozinha o requisito que nomeia. Office, idiomas e soft skills ficam fora da cobertura
  só em computação. SQL e os bancos relacionais se atendem nos dois sentidos.
- **Curso e período são decididos pelo Python**, com o catálogo: a IA só extrai `cursos_aceitos`
  e `periodo_minimo`. Cursos da mesma área só se equivalem onde a área declara
  `cursos_intercambiaveis` (só computação); perfil abaixo do período mínimo fica em 35.
- **`domain/areas.py` é o catálogo único.** `AreaDeInteresse`, a migration `0017` e
  `web/assets/areas.json` derivam dele; mexeu, regere. A normalização de curso tem paridade entre
  Python e site (`tests/fixtures/cursos_normalizados.json`): mudou `normalizarTexto`, teste curso
  e cidade.
- **Vaga exclusiva para PCD não vai para quem respondeu que não é**, e quem é PCD recebe
  primeiro a exclusiva e a afirmativa que o inclui. A resposta é dado sensível: não entra em
  evento, log, prompt nem export.
- **Análise incompleta não vira "nenhuma vaga compatível".** Candidata sem extração segura a
  mensagem daquele usuário, com o teto de dias da `0022`; coleta incompleta segura também.
- **Só entra extração com o id de uma vaga do lote pedido**, e id repetido derruba as duas
  cópias. Mudar prompt ou catálogo muda `VERSAO_DA_EXTRACAO` e reextrai as candidatas; notas são
  recalculadas em toda execução, sem cache de notas.
- **Vaga é `(fonte, id_externo)` em todo o fluxo**, a chave de duplicata inclui a cidade com o
  estado, e empresa sem nome leva a descrição na chave.
- **Mesma região imediata do IBGE vale como a cidade** no pré-filtro e metade na logística.
- **A conexão do banco abre em `autocommit`.** Não voltar ao padrão sem mover a fronteira da
  transação junto.
- **Entrega:** até 7 vagas (`QUANTIDADE_VAGAS_ENVIADAS`); texto da fonte é cortado depois do
  escape; a data da mensagem é a de Brasília; só HTTP 403 e o 400 que nomeia o destinatário
  contam como falha de envio do usuário; "Vaga encerrada" tira a vaga de todos só com abertura
  anterior e dentro do teto por perfil.
- **Execução que não se relata não é verde:** sem resumo no chat de operação, ou com ninguém
  atendido por falha de verdade, o processo sai com código 1.
- **O juiz (`julgar`) mede, não ranqueia.** Abaixo de 75% de concordância com o gabarito humano,
  o número dele é ruído.
- **Falha nova se procura escrevendo o teste que a reproduz antes de mexer no código.**

### Transferência para a organização (08/09/2026)

O repositório saiu de `babue0/RadarEstagio` para `RadarEstagio/RadarEstagio`. Commits, autores,
issues e PRs foram preservados, e o GitHub redireciona o endereço antigo — o que quebra é a
ligação das automações, porque cada uma guardava o dono no nome:

- **cron-job.org**: mudam a URL **e o token**. Token fine-grained é preso ao dono, então o antigo
  para de enxergar o repositório mesmo com a URL certa. O teste bem-sucedido responde **204 No
  Content** com corpo vazio; 404 é token apontando para a conta pessoal e 403 é falta de
  `Actions: Read and write`.
- **Entrega imediata**: `REPOSITORIO` em `entrega_imediata.ts` é constante, então exige commit
  **e** `supabase functions deploy telegram-webhook` — trocar só o `GITHUB_DISPATCH_TOKEN` não
  basta.
- **Cloudflare Pages**: o app da Cloudflare fica instalado por conta, não segue o repositório. O
  link "Manage" da tela de build passa a dar 404 porque aponta para a instalação da conta
  pessoal. Reconectar é Disconnect e ligar de novo escolhendo a organização, o que instala o app
  nela — **Disconnect não apaga o projeto nem muda a URL**, e criar projeto novo mudaria, o que
  derrubaria o Supabase Auth e o `URL_DA_LANDING`.
- **Antes de gerar os tokens**, a organização precisa liberar tokens fine-grained (Settings →
  Personal access tokens). Sem isso o token nasce válido e a API responde 404, sem dizer por quê.
- Os secrets do Actions sobreviveram à transferência. O token do cron **vence em 09/09/2027**:
  quando vencer, o radar diário para de rodar sem avisar ninguém.

### Supabase e Telegram: fatos operacionais

O porquê de cada decisão de schema, migration e webhook, com as medições, está em
`docs/decisoes-do-banco.md`. Abaixo só o que se usa sem ler a história.

- Projeto ativo: **`xrhvjwemmylwbqgluebc` (`sa-east-1`)**. A `DATABASE_URL` do Actions já usa
  esse banco.
- O projeto **`bnzogphdvpubtkcflcue` (`us-east-2`) foi criado por engano e não deve ser usado.**
  Não o remover sem confirmar que nenhum recurso externo ainda aponta para ele.
- **Exclusão de conta é em duas etapas** (04/09/2026): `excluir_minha_conta()` marca
  `excluida_em` e solta o chat do Telegram; o job apaga depois de
  `DIAS_ATE_APAGAR_CONTA_EXCLUIDA` (60 dias). A sessão não é encerrada ao pedir: sem ela a pessoa
  não voltaria para cancelar. Conta confirmada **sem perfil** usa
  `apagar_minha_conta_sem_perfil()` (`0024`) e é apagada na hora.
- **Cadastro que não confirma o e-mail tem prazo** (`0030`): todo link novo descarta o cadastro
  pendente, e o job apaga o pendente com 2 dias e a conta não confirmada com 30.
- **Conferir `supabase migration list --linked` depois de aplicar e antes do próximo push.** SQL
  rodado fora do CLI não entra no histórico e quebra o push seguinte no primeiro `add column`.
- **NUL e surrogate solto saem na entrada**, nos modelos (`domain/texto.py`): o Postgres recusa
  os dois, e eles derrubavam gravação e envio.
- **Evento web tem teto** (`0023`): 256 bytes de propriedades, 60 por sessão e por conta na
  última hora e teto por hora de 2.400 para visitantes e 900 para contas; acima disso o insert
  falha com `PT429`. Abertura, pausa e vínculo repetidos são descartados pelo gatilho da `0028`,
  ficando a primeira ocorrência.
- **Os textos e as listas do perfil têm teto no banco** (`0025`), validados: curso 200, cidade
  120, cada habilidade 100 e listas de 50 itens, em uma dimensão só (`0031`). Perfil fora do teto
  faz o `db push` falhar inteiro.
- **Toda execução se reporta** ao `TELEGRAM_CHAT_ID`, que com banco é o chat de operação, e o
  resumo traz os avisos do dia. `rodar` sai com código 1 quando o resumo não chega ao chat ou
  quando ninguém foi atendido por falha de verdade; dia legítimo sem vaga e mensagem segurada
  seguem verdes.
- **Controle do próprio perfil** (04/09/2026): editar, pausar e retomar são `update` em `perfis`
  pelas colunas já liberadas no `grant`. Desvincular o Telegram e excluir a conta não cabem em
  `grant` — `telegram_chat_id` é do webhook e `auth.users` o cliente não apaga — então são funções
  `security definer` filtrando por `auth.uid()`, na migration `0013`. Desvincular rotaciona o
  `token_vinculo` junto, senão o link antigo continuaria valendo.
- **`ativo` é só da pausa; exclusão não escreve nele** (04/09/2026). O gatilho da `0005` emite
  `entregas_pausadas` em toda transição de `ativo` para `false`, então exclusão entrava no funil
  como pausa; e cancelar, que punha `ativo = true` sem saber o estado anterior, devolvia ao ar quem
  tinha pausado antes de excluir. Marcar em vez de destruir é o que faz cancelar ser desfazer.
- **Nunca alterar tabela pelo painel do Supabase** — só por migration em `supabase/migrations/`.
- **O perfil aceita uma cidade e uma modalidade.** `cidades_aceitas` e `modalidades_aceitas`
  existiram sem leitor nem escritor e saíram na migration `0012` (04/09/2026); só voltam junto da
  tela que as escreva, e se o piloto mostrar que alguém quer mais de uma cidade. Desde 10/09/2026
  a cidade é escolhida na lista de municípios do IBGE (`web/assets/cidades.json`, gerada por
  `scripts/gerar_cidades.py`) e gravada como `Nome, UF`; a regra é do site, o banco não a cobra.
- Com o webhook do `/start` ativo, **`getUpdates` deixa de funcionar nesse bot**.
- O `TELEGRAM_WEBHOOK_SECRET` vive em três lugares que precisam do MESMO valor: o
  `setWebhook` no Telegram, os secrets do Supabase (`supabase secrets set`) e os `.env`
  locais. Divergência vira 401 silencioso em todo update (aconteceu em 04-05/09/2026: um
  re-registro usou o segredo de um `.env` dessincronizado e cliques/vínculos se perderam
  por ~12 h). Ao mexer no webhook, conferir `getWebhookInfo` depois: `last_error_message`
  vazio e `pending_update_count` zerando.
- O `setWebhook` precisa de `allowed_updates=["message","callback_query"]` (corrigido em
  04/09/2026): o registro original só aceitava `message` e o Telegram descartava os cliques
  dos botões de feedback antes de chegarem à função. Ao re-registrar o webhook, sempre
  repassar os dois tipos. Botão de mensagem do `testar-local` nunca funciona: o token do
  envio não é gravado no banco no modo local.
- **`token_vinculo` é de uso único**: o webhook grava o `chat_id` e troca o token na mesma
  atualização, então link vazado não vincula o chat de outra pessoa. O token que o site leu antes
  do clique deixa de valer depois do vínculo.
- Pendência externa: configurar o redirect do Auth para `http://localhost:8000`.
- No pipeline, a falha de leitura dos usuários é a única fatal; erros ao enviar ou gravar de um
  usuário viram aviso. Falhas de revalidação são contadas por usuário no resumo e bloqueiam a
  mensagem afetada; o resumo distingue quem ficou sem entrega de quem já recebeu antes da falha.
- **A avaliação é gravada antes do envio** e os `envios` depois: falha do Telegram não descarta o
  que a IA já custou. Falhas seguidas incrementam `perfis.falhas_de_envio` e, ao atingir
  `FALHAS_DE_ENVIO_ATE_PAUSAR`, o perfil sai de `ativo` emitindo `entregas_pausadas`.
- **Cada linha de `envios` tem um `token` único**, gerado em Python antes do envio porque a
  mensagem precisa do link antes de a linha existir. Envio que falha ao ser gravado deixa um token
  órfão, e a Edge Function `ir` trata isso redirecionando para a landing.
- Ativação operacional = primeira entrega bem-sucedida com ao menos uma recomendação;
  `perfis.ativado_em` é gravado uma única vez, na transação dos `envios`. `docs/metricas.md`
  separa esse marco da ativação de produto.
- `domain/perfil_fixo.py` é um perfil **sintético** (`perfil_de_exemplo`), usado só quando não há
  `DATABASE_URL`. O repositório é público: nunca colocar ali dados reais de ninguém.
