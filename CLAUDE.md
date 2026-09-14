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
- **Jooble**: coletor pronto e **desligado por padrão** (05/09/2026). API oficial gratuita de
  `br.jooble.org` (a chave é regional: a do site global só devolve vaga dos EUA) que enxerga
  InfoJobs, Empregos.com.br, Pandape e Sólides. Sondagem de 05/09 no Rio: 368 vagas baixadas,
  33 passam no pré-filtro, **19 inéditas** frente a Adzuna+Gupy (HStern, FI Group, v(dev)) —
  ~+35% de cobertura. O snippet de ~290 caracteres marca `descricao_completa=False`, então a
  vaga respeita o teto de 60: preenche dia fraco sem roubar o topo. **Não ligar em produção sem
  parceria**: a chave gratuita tem 500 requisições no total, não por mês, e cada execução faz
  várias (12/09/2026). Upgrade futuro se a fonte se provar: enriquecedor específico do InfoJobs
  (40% das vagas dela) destrava a descrição completa.
- **IA de extração**: Google Gemini (modelos Flash), com dois adapters — Gemini Developer API
  para CI/produção e Antigravity CLI (`agy`) para testes locais. `AVALIADOR` escolhe qual; o
  padrão é `gemini_api` e o GitHub Actions não define a variável, portanto segue nele.
  `AVALIADOR=agy` dispensa `GEMINI_API_KEY` e usa `AGY_MODELO` e `AGY_TIMEOUT_SEGUNDOS`, com o
  comando `agy` autenticado localmente; `python -m radar verificar` mostra o adapter ativo. A IA
  **só extrai fatos da vaga**; quem compara com o perfil e calcula a nota é Python, sem IA.
- **Telegram**: bot `RadarEstagio_bot`; o job só envia mensagens.
- **Link rastreável**: o link de cada vaga na mensagem passa pela Edge Function `ir`, que registra
  `vaga_aberta` e redireciona para a fonte. O endereço vem de `URL_DE_RASTREIO`; vazio ou sem
  banco, a mensagem volta a apontar direto para a vaga.
- **Feedback individual**: o teclado numerado acompanha a mensagem diária. Cada número abre
  título e empresa com uma opção positiva e cinco recusas, incluindo `motivo_nota`. A última
  resposta por recomendação vale nas métricas; cliques repetidos não multiplicam vagas.
- **Leitura do funil**: `python -m radar metricas` imprime, direto do banco, o funil da coorte dos
  últimos 30 dias, a participação no feedback, as medianas observadas até a primeira entrega e a
  primeira abertura, a utilidade semanal e por área do curso, as contas pausadas por motivo, a
  quebra das recusas por motivo e o custo de extração por usuário ativado. As definições estão em
  `docs/metricas.md`; a consulta fica em `radar/storage/metricas.sql` e o agrupamento por área,
  que é regra de domínio, em `radar/domain/metricas.py`. Mediana é tempo observado, nunca prazo.
- **Entrega imediata (fase D, 05/09/2026)**: ao gravar o `chat_id`, a `telegram-webhook`
  dispara o workflow com o input `perfil` e o pipeline atende só o recém-vinculado
  (`rodar --perfil <id>`), sem tocar os demais. Vínculo entre 06:23 e 07:23 de Brasília
  espera o diário. Usa o endpoint de `workflow_dispatch` porque o token existente
  (`GITHUB_DISPATCH_TOKEN` nos secrets do Supabase) tem permissão de Actions, não de
  conteúdo — o `repository_dispatch` do plano exigiria token novo. Com as extrações
  compartilhadas, a primeira entrega pode não exigir IA; novas vagas elegíveis ainda consomem cota. Sem o token, o vínculo
  segue normal e a primeira busca fica para o diário.
  **Disparo único e sem entrega perdida (13/09/2026).** Antes, todo `/start` disparava o
  workflow, até de quem já estava vinculado, e duas execuções rodavam juntas dividindo a cota. A
  `0021` criou `perfis.entrega_imediata_disparada_em`, que o webhook reivindica numa única
  atualização antes de disparar (`/start` repetido e desvincular e vincular de novo não disparam),
  e `entrega_imediata_atendida_em`, gravada pela execução que atende. O workflow tem
  `concurrency: radar-diario` sem cancelar a execução em andamento, mas o GitHub guarda só **uma**
  execução na espera: a nova cancela a que esperava, e a cancelada nunca começa, então nem o
  passo `if: cancelled()` roda. Por isso `rodar --perfil X` atende X e todo perfil com disparo e
  sem atendimento, reivindicados num único `update … returning`, e o diário marca como atendidos
  todos os que atende. Disparo recusado pelo GitHub deixa a pessoa pendente para a próxima
  execução, imediata ou diária. `rodar --perfil` de perfil já atendido não faz nada: para testar
  com conta da equipe, zerar `entrega_imediata_atendida_em` antes. O backfill marcou as duas
  colunas de quem já tinha vínculo ou ativação. Publicação: `db push` antes do merge, porque o
  `rodar` do `main` passa a exigir as colunas, e o deploy da `telegram-webhook` depois. Se uma
  execução ainda estiver rodando às 07:23, um disparo imediato pode substituir o diário na fila;
  começar a janela às 05:53 fecharia esse caso, e fica como decisão de produto.
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

A proposta original previa SQLite. Foi descartado por incompatibilidade com o modelo de
execução escolhido: o GitHub Actions provisiona uma máquina nova a cada execução e a
destrói ao terminar. SQLite é um arquivo em disco e não teria onde persistir entre as
execuções diárias.

As alternativas para contornar isso foram avaliadas e rejeitadas:

- Versionar o arquivo `.db` no repositório exigiria permissão de escrita para o job,
  incharia o histórico com blobs binários e — como o repositório é público — exporia
  perfis e `chat_id` de Telegram dos usuários a partir da Fase 2.
- `actions/cache` não é armazenamento durável: sofre evicção, e perder o histórico
  significa reenviar vagas já vistas.

A escolha é PostgreSQL gerenciado no **Supabase**, que a própria proposta já previa para
a fase do painel web — adotá-lo na Fase 2 evita duas migrações. `JSONB` acomoda o payload
cru das vagas e a saída estruturada da IA sem exigir mudança de schema a cada alteração
das fontes.

MySQL foi considerado e não oferece vantagem neste caso: suporte a JSON mais limitado e
opções gerenciadas gratuitas piores que as de PostgreSQL.

A Fase 1 não usava banco. O Passo 9 (Fase 2) adicionou o Supabase como opcional: tabelas
`perfis`, `vagas`, `avaliacoes`, `envios` e `eventos_produto`, todas com RLS; `perfis` limita
o usuário à própria linha e `eventos_produto` limita o navegador ao catálogo web permitido.
O pipeline só conhece `Repositorio`; a falha de leitura dos usuários é a única fatal,
erros ao enviar ou gravar de um usuário viram aviso. Revalidação indisponível bloqueia a mensagem daquele destinatário por
privacidade e aparece no resumo de operação; os demais usuários continuam. Nunca alterar tabela pelo painel — só
por migration em `supabase/migrations/`.

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

**Conta no site: volta à aba e botão de pausa (13/09/2026).** Voltar à aba (`focus`) só consulta
o banco com a tela de ativação à mostra e o link do Telegram visível
(`aguardandoVinculoDoTelegram`), e a condição é conferida de novo quando a consulta termina, com
sucesso ou erro. Antes, depois da ativação, toda volta à aba redesenhava a conta: descartava a
edição em andamento, sumia com a pergunta do motivo da pausa e escondia a confirmação sem
fechá-la. Um `<dialog>` aberto com `showModal` e escondido continua modal e trava a página, e no
celular não há Esc; por isso esconder a conta é sempre `esconderConta()`, que passa por
`fecharConfirmacao`, nunca `hidden = true`. O botão de pausa guarda a ação que mostrou
(`data-acao`), e o update leva `.eq("ativo", ...)` e devolve a linha (`select(COLUNAS_DO_PERFIL)`),
que desenha a conta sem leitura extra. Zero linhas significa que a conta mudou em outro lugar
(outro aparelho, pausa automática, exclusão): nada é invertido, o perfil é relido e a pessoa é
avisada. Antes, "Pausar entregas" com a conta já pausada retomava as entregas e apagava o
motivo. O JSDOM não implementa `showModal`: os testes o simulam e conferem `open`, `hidden` e se
`close()` foi chamado. O card de preços fala só da Adzuna, e
`test_card_de_precos_nao_promete_duas_fontes_de_vagas` impede que "duas fontes" volte.

**Armazenamento bloqueado e conta que não carrega (13/09/2026).** Com o armazenamento bloqueado
(modo privado, bloqueador), `eventSessionId` e `clearPendingProfile` lançavam exceção e o `signUp`
nunca era chamado. Toda leitura e escrita de `localStorage`/`sessionStorage` do site fica em `try`,
e a sessão de eventos vira um UUID em memória na página, o mesmo no cadastro e nos eventos. O
cliente do Supabase não precisa de armazenamento: o auth-js testa o `localStorage` com `try` e, se
falha, guarda a sessão em memória (conferido no código do 2.112.4 e do 2.114.0, iguais nesse
ponto; o 2.116.0 não pôde ser baixado). Custo aceito: a sessão some ao recarregar, o tema não é
lembrado e `landing_visualizada` conta toda carga. Falha ao ler sessão ou perfil deixou de virar
"Sua conta foi criada, mas o perfil ainda não foi salvo", que quem tinha perfil via com a sessão
velha ou sem rede: agora abre o login com "Não conseguimos carregar sua conta", e o aviso de perfil
pendente só sai quando o perfil foi lido e não existe (`contaSemPerfil`). A visita comum à landing
não lê mais o perfil, que era descartado. O erro de "Minha conta" na ativação vai para
`#success-message`, porque o formulário fica escondido nessa tela.

**Segunda auditoria da conta (13/09/2026).** Propriedades de evento cabem em 256 bytes: a `0023`
(branch `fix/eventos-e-reserva`) recusa evento web acima disso, e `landing_visualizada` levava o
caminho inteiro da URL. `propriedadesDoEvento` corta cada texto em 40 pontos de código, porque o
pior caractere escapado no JSON tem 6 bytes (40 × 6 mais `{"pagina": ""}` dá 254); o corte é por
ponto de código para não partir emoji, que o `jsonb` recusaria. Evento novo com dois textos exige
refazer a conta, e o teste com URL de 1.000 caracteres confere todos os `registerEvent`.
`closeSignup` fecha a confirmação antes de sair da conta, porque voltar no histórico deixava o
`<dialog>` modal aberto. Envio do perfil e exclusão sem perfil se travam até a resposta, senão a
exclusão ganhava a corrida e o erro do envio ia para o formulário escondido. A exclusão sem perfil
tem mensagens próprias (`55000`, `42501`, rede), não as do cadastro.

**Perfil, habilidades e rascunho (13/09/2026).** Os textos que o navegador grava no perfil têm teto
no banco (`0025`): curso 200, cidade 120, habilidade 100 e listas de 50 itens. São os tetos que
`validar_cadastro_radar` já cobrava desde a `0014`, agora também no `update` direto e sobre o texto
cru (espaços nas pontas furavam o `btrim`); mantê-los evita que um cadastro pendente, validado antes,
falhe na confirmação do e-mail. A folga vem dos catálogos: o maior curso sugerido tem 37 caracteres,
84 com o maior prefixo e sufixo que a normalização conhece, e a maior cidade do IBGE tem 36. O site
limita a digitação com o mesmo `maxlength` e cobra na etapa o mínimo de 2 no curso, porque o
navegador só marca texto curto que a pessoa digitou. O teste de coerência compara com o site os
checks, os dois números de cada texto em `validar_cadastro_radar` e o limite das listas da `0018`, e
exige que perfil e cadastro aceitem todas as subáreas de um curso; lendo só os checks, mudar a
validação do cadastro passava. Habilidade digitada nunca é separada por vírgula: cada item na tela é
um item no banco. O envio partia o campo oculto por vírgula, então "Pacote Office (Word, Excel)"
virava dois pedaços e 50 itens na tela viravam mais de 50 no banco, que recusava. Separar ao adicionar
exigiria copiar no site as regras com que o Python já parte a habilidade composta (parênteses, " e ",
nível da última parte). O corte de 100 é por ponto de código, como em `propriedadesDoEvento`: o
`slice` partia emoji e o Postgres recusava o JSON. O limite de 50 vale também para a sugerida e para
Continuar, que antes passavam sem aviso. Fechar o diálogo (Esc, X, clique fora, voltar) não apaga o
rascunho: ele fica na memória da página, sem armazenamento, e reabre na mesma etapa, mas sem senha nem
e-mail e só para a mesma dona. Senha e e-mail saem porque identificam a pessoa, e quem reabre já
refaz a etapa da conta por causa da senha. O rascunho guarda a dona (`donoDoRascunho`): o id do
usuário da sessão, ou visitante. Qualquer troca de dona limpa tudo: ao reabrir, na volta do link, ao
completar o perfil, ao ler a conta e depois de um login. Só o `signUp` feito do rascunho o adota,
porque é a mesma pessoa se cadastrando; se ele espera a confirmação do e-mail, a sessão que chega com
esse e-mail também o mantém (`emailDoCadastroEnviado`). Login pelo diálogo e sessão vinda de outra aba
nunca adotam. Sessão que falha ao renovar limpa o rascunho de conta, porque não se sabe quem é a dona.
E nada do formulário é gravado numa conta que não é a dona: antes da edição, do `concluir_meu_cadastro`
e da troca de conta, a sessão atual precisa ser a dona, senão o formulário é limpo e aparece "Sua
sessão mudou". Em duas abas, a edição de A aberta aqui era gravada na conta de B que entrou na outra;
o `main` faz o mesmo. Logout, exclusão e o "Entrar" do cabeçalho seguem limpando. Custo aceito: na
mesma aba, quem abre o cadastro depois de um visitante vê o curso, a cidade e as habilidades dele até
entrar numa conta; depois do envio, reabrir mostra o que foi enviado.

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

## Estado do projeto

O catálogo atual está em `docs/funcionalidades.md`. Abaixo
só o conhecimento operacional que não dá para reconstituir lendo o código.

### Termos de uso das fontes (12/09/2026)

Leitura dos termos no texto original, depois do alerta do Igor. O que vale para o Radar:

- **Adzuna, uso 1.** Os termos permitem "Publishing Adzuna ad listings" sem prazo. O teste de
  14 dias e a proibição de agregação ("vacancy counts, average salaries") estão no parágrafo de
  "Any other use". O Radar publica anúncios com link para a página da Adzuna (o `redirect_url`,
  com o nosso app id), então cai no uso 1. Confirmação por escrito pedida no e-mail à Adzuna.
- **Atribuição em cada anúncio exibido**: "Jobs by Adzuna", com "Jobs" ligado a adzuna.com.br e
  "Adzuna" sendo o logo, também com link, em pelo menos 116×23 px. No Telegram vai o texto com
  os dois links, porque mensagem de texto não tem imagem (aprovação pedida no e-mail). No site
  vai o selo com `web/assets/adzuna-logo.png`, o logo oficial servido pelo site de
  desenvolvedores da Adzuna; no tema escuro ele ganha fundo branco, sem mudar as cores.
- **Limites**: 25 requisições por minuto, 250 por dia, 1.000 por semana e 2.500 por mês.
  `CotaDaAdzuna` segura o ritmo, conta cada chamada (tentativas incluídas) e para a coleta quando
  acaba o saldo do dia, dos últimos 7 dias ou do mês, devolvendo o que já trouxe. O uso fica em
  `uso_das_fontes` (migration 0020) e o resumo diário mostra o mês e avisa a partir de 80%. Banco
  sem a tabela ou fora do ar não derruba a execução: a cota segue sem saldo e o log avisa. Em
  12/09 a coleta fazia ~18 requisições por execução (10 páginas no Brasil, 8 no Rio), ~540 por
  mês só com o diário; cada cidade nova soma até 10. `rodar` e `testar-local` usam a cota;
  `coletar` e `avaliar` respeitam o limite por minuto, mas não gravam o uso. A entrega imediata
  (`rodar --perfil`) coleta só para o perfil atendido e não pode gastar a reserva do diário:
  10 páginas × (1 + cidades de busca) × buscas, calculada pelos usuários ativos (20 em 12/09).
  Sem essa reserva, vínculos feitos entre 21h e 07:23 esgotavam o dia antes do diário. Cota
  zerada antes da primeira busca vira erro de coleta e aviso de operação, nunca "nenhuma vaga".
  O "hoje" da cota é o dia em UTC, que vira às 21h de Brasília. **Depois que o diário do dia UTC
  roda, a reserva sai do saldo do dia (13/09/2026).** Antes ela valia o dia inteiro, e a entrega
  imediata da tarde recebia saldo zero com o dia sobrando. O diário que termina grava em
  `uso_das_fontes` a linha `adzuna:diario` do dia com o que gastou (zero também conta); achando
  essa linha, a imediata desconta a reserva só da semana e do mês, que ainda protegem o diário de
  amanhã. Registro, não horário, porque o cron pode atrasar ou falhar: sem a linha (diário que
  falhou, não rodou ou registro ilegível) a reserva continua, e entre 21h e 07:23 o dia UTC já é
  o do próximo diário. A linha também mostra o gasto real do diário contra a reserva estimada.
  Só grava a linha a execução sem `--perfil` que começa a partir das 09:23 UTC (06:23 de
  Brasília), o início da janela do diário na `telegram-webhook`; um teste confere que os dois
  valores não se afastam. Antes, um `rodar` manual às 22h de Brasília, para refazer um diário que
  falhou, marcava o dia UTC seguinte e as imediatas da madrugada gastavam a reserva do diário das
  07:23, que ficava sem cota. A janela, e não a hora gravada, porque dispensa coluna nova e já é
  regra do produto: entre 06:23 e 07:23 o webhook não dispara imediata.
- **Coleta resiliente (13/09/2026).** Com pelo menos uma vaga em mãos, falha numa página tardia
  da Adzuna (429 ou 5xx depois das tentativas, rede, resposta 200 com corpo inválido) para a
  coleta sem novas requisições e levanta `ColetaIncompleta` com o que já veio; o `ColetorComposto`
  aproveita essas vagas e o resumo diário mostra "⚠️ Coleta da Adzuna incompleta: <motivo>". Antes,
  uma página ruim jogava fora tudo. Sem nenhuma vaga continua erro de coleta e aviso de operação,
  inclusive quando a falha é na primeira região e as outras responderiam. Corpo que não é JSON,
  sem `results` ou com `results` fora de lista vira `ErroDeColeta`, nunca exceção crua; item que
  não converte é pulado com aviso. Num dia de coleta incompleta, ou de cota esgotada no meio, quem
  fica sem vaga selecionada tem a mensagem segurada: "nenhuma vaga compatível" afirmaria algo
  sobre uma busca que não aconteceu. O pipeline recebe isso por `executar(coleta_incompleta=...)`
  e não sabe de quais regiões cada perfil depende, então a retenção vale para todos. O uso da
  cota é gravado por `ColetorComRegistroDeUso` assim que a coleta termina, com sucesso ou erro;
  só um kill durante a própria coleta perde a contagem. A Adzuna busca as cidades antes da busca
  nacional: com saldo curto, a entrega imediata gasta na cidade da pessoa, e quem perde é o perfil
  remoto, que depende da nacional e fica com a mensagem segurada. Com saldo sobrando, o conjunto
  de vagas é o mesmo. Falha ao ler os usuários também gera aviso de operação.
- **Nunca contatar anunciante que veio da Adzuna**: "Any attempt to contact a third party, even
  where they provide listings content, will be considered a breach".
- **Se o acordo acabar**, apagar "all insertion codes and data acquired from Adzuna".
- **Pendente, a descrição completa.** O enriquecimento lê a página do anúncio no site da Adzuna
  (`adzuna.com.br/details/...`), fora da API. Os termos da API mandam seguir os termos gerais do
  site, que bloqueia robôs e não pôde ser lido (403). 88% das vagas da Adzuna enviadas entre 05 e
  12/09 usaram esse texto. A pergunta foi para o e-mail; se a resposta for não, o enriquecimento
  sai e a extração passa a ler só os 500 caracteres da API.
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

- Padrão `gemini-3.6-flash` (`GEMINI_MODELO`). O `gemini-2.5-flash` foi recusado pela API como
  indisponível para contas novas.
- O projeto está no plano pago desde 10/09/2026. Na cota gratuita, o `gemini-3.6-flash` tinha 20
  requisições por minuto, e os limites variam por modelo, projeto e janela. Por isso a extração vai em lotes (`GEMINI_VAGAS_POR_LOTE`,
  padrão 10), com repartição do lote que falha e espera pelo "retry in Ns" do 429; acima de
  120 s a espera indica cota diária e o job desiste devolvendo o que já tem.
- **A extração tem prazo** (11/09/2026, G01 e G07 da auditoria do agendamento). Ela roda antes
  de qualquer envio e só é gravada no fim, então um kill do job durante ela deixava todos sem
  mensagem e jogava fora o que já tinha sido pago, e o dia seguinte repetia a mesma fila.
  `PRAZO_DA_EXTRACAO_SEGUNDOS` (padrão 600) é conferido antes de cada requisição e de cada espera
  de cota; esgotado, a extração para e segue com o que tem, e o resumo mostra "vagas sem
  extração". A conferência **reserva o tempo da própria chamada**, então uma requisição só começa
  se couber inteira no prazo: sem isso, três repetições de 120 s mais as esperas furavam os 600 s
  e o run podia terminar com zero extrações. Cada chamada leva `GEMINI_TIMEOUT_SEGUNDOS`
  (padrão 120, extrator e juiz), e tanto o timeout quanto falha de rede (`httpx.TransportError`,
  que cobre conexão recusada e queda no meio da resposta) viram indisponibilidade, tratada como o
  504: espera e repete o mesmo lote dentro do prazo. Antes só o timeout era tratado, e um
  `ConnectError` derrubava a execução inteira sem resumo de operação. As candidatas vão para a
  extração intercaladas por usuário, para o corte não cair sempre em quem entrou por último. O job
  tem 30 minutos e o passo do radar 28. Números que sustentam os valores, medidos no diário de
  11/09: ~27 s por requisição (93 vagas em 11 requisições) e ~21 s por usuário na entrega, o que
  acomoda cerca de 40 usuários. Dois limites conhecidos: o timeout do `httpx` é por operação de
  socket, não por chamada, então resposta que chega devagar sem parar não o estoura; e o
  enriquecimento das descrições roda antes da extração sem orçamento algum, então uma Adzuna lenta
  ainda pode levar o job ao kill.
- **Raciocínio da extração em `low`** (11/09/2026, `GEMINI_RACIOCINIO`). O `gemini-3.6-flash`
  pensa por padrão e o raciocínio é cobrado como saída: numa requisição real de 10 vagas foram
  4.902 tokens de raciocínio para 2.655 de resposta, cerca de 60% do custo (R$ 0,15 por lote, a
  US$ 0,75 e 3,75 por milhão e R$ 5,10). Teste com 50 vagas de 11/09 contra as extrações
  gravadas: repetir o modo padrão concordou em 90% dos campos, que é o ruído do próprio modelo;
  `low` em 88%; `minimal` em 82%. O top 7 dos 4 perfis reais mudou em `low` o mesmo que no
  padrão repetido, fora uma vaga de Direito, e em `minimal` mudou mais. `minimal` ainda devolveu
  um lote inteiro de 10 vagas vazias, sem habilidade nem curso, que o extrator não detecta e o
  cache guardaria, por isso ficou de fora. `low` custa R$ 0,066 por lote e leva ~12 s contra
  ~30 s; o padrão devolveu 1 de 10 num dos cinco lotes (o mesmo lote incompleto do diário de
  11/09) e `low` devolveu 10 de 10 em todos. Ponto a acompanhar: pegadinha. A gravada tinha 3 em
  41 vagas, o padrão repetido achou 1 e `low` nenhuma. `GEMINI_RACIOCINIO=padrao` volta ao
  comportamento anterior sem mudar código; o nível não entra na identidade da extração, então
  trocá-lo não reextrai o que está no cache. Vale só para a extração: o juiz segue no padrão.
- **A extração não é repetida por usuário** (03/09/2026, formulação revista em 10/09). Isso não
  é o mesmo que dizer que o custo total independe da coorte: mais usuários trazem mais cidades e
  mais áreas, e portanto mais vagas novas para extrair, além de mais consultas, pontuação,
  gravações, envios e suporte. O que não cresce é o trabalho repetido sobre a **mesma** vaga.
  O prompt não contém perfil, então cada vaga é extraída uma vez e a extração serve todos. Ela fica em `vagas.extracao` (JSONB), de
  modo que reexecução no mesmo dia ou usuário novo entrando não gastam cota. Antes eram cerca de
  6 requisições por usuário por dia: 20 estudantes estouravam a cota e o job morria no timeout de
  15 minutos, sempre deixando sem mensagem quem entrou por último, porque a fila é ordenada por
  `criado_em`. O resumo de cada execução informa quantas requisições foram gastas, e
  `test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas` impede que a propriedade se perca.
- **Lote incompleto pede junto o que faltou** (10/09/2026). Em 10/09, 3 de 13 lotes voltaram com
  1 de 10 extrações, e as 9 que faltavam iam uma a uma, cada chamada levando de novo a instrução
  de 9.170 caracteres. Agora, se a resposta traz parte do lote, só com ids do lote, e faltam 2 ou
  mais, as que faltaram vão juntas numa requisição, uma vez, e o que ainda faltar segue uma a
  uma. Lote que volta vazio segue uma a uma, porque repeti-lo mandaria o mesmo prompt; resposta
  com id fora do lote ou repetido também. A repetição que falha com erro não temporário, ou volta
  com id fora do que faltou ou repetido, é descartada inteira e segue uma a uma; com 429 ou 503
  ela espera e se repete como qualquer lote, e a cota diária interrompe a extração como antes.
  Custo: cada chamada de 2 ou mais vagas que volta incompleta gera no máximo 1 requisição a mais
  que antes, sem contar as novas tentativas após 429/503. Num lote dividido por erro cada parte
  conta, então um lote de 10 pode passar de +1. Em caracteres de entrada, a repetição de 9 vagas
  tem de 17% a 34% das 9 chamadas avulsas (descrições de 500 a 3.000 caracteres), e é esse o
  acréscimo quando ela volta sem nada. Fuzz de 6.000 cenários contra a versão anterior, sem erro
  temporário: nenhuma vaga a menos e o limite nunca violado. Limites aceitos: o descarte não pega
  troca de ids entre as vagas que faltaram, e a extração errada iria para o cache compartilhado,
  como já pode acontecer na primeira chamada de qualquer lote; e erro temporário persistente só
  na repetição para a execução mais cedo que antes. Os logs `Lote de N vagas voltou com M
  extrações` e `Repetição de N vagas ...` registram os ids que faltaram, os devolvidos sem vaga e
  os repetidos: ainda não se sabe se o modelo devolve um item só ou copia os ids errado.
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
  só em computação.
- **Curso é decidido pelo Python**, com o catálogo: a IA só extrai `cursos_aceitos`. Cursos da
  mesma área só se equivalem onde a área declara `cursos_intercambiaveis` (só computação).
- **`domain/areas.py` é o catálogo único.** `AreaDeInteresse`, a migration `0017` e
  `web/assets/areas.json` derivam dele; mexeu, regere. A normalização de curso tem paridade entre
  Python e site (`tests/fixtures/cursos_normalizados.json`): mudou `normalizarTexto`, teste curso
  e cidade.
- **Análise incompleta não vira "nenhuma vaga compatível".** Candidata sem extração segura a
  mensagem daquele usuário.
- **Mudar prompt ou catálogo muda `VERSAO_DA_EXTRACAO`** e reextrai as candidatas. Notas são
  recalculadas em toda execução; não reintroduzir cache de notas.
- **Vaga é `(fonte, id_externo)` em todo o fluxo**, e a chave de duplicata inclui a cidade.
- **Mesma região imediata do IBGE vale como a cidade** no pré-filtro e metade na logística.
- **A conexão do banco abre em `autocommit`.** Não voltar ao padrão sem mover a fronteira da
  transação junto.
- **Entrega:** até 7 vagas (`QUANTIDADE_VAGAS_ENVIADAS`); texto da fonte é cortado depois do
  escape; a data da mensagem é a de Brasília; só HTTP 403 e o 400 que nomeia o destinatário
  contam como falha de envio do usuário.
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

- Projeto ativo: **`xrhvjwemmylwbqgluebc` (`sa-east-1`)**. A `DATABASE_URL` do Actions já usa
  esse banco.
- O projeto **`bnzogphdvpubtkcflcue` (`us-east-2`) foi criado por engano e não deve ser usado.**
  Não o remover sem confirmar que nenhum recurso externo ainda aponta para ele.
- **Controle do próprio perfil** (04/09/2026): editar, pausar e retomar são `update` em `perfis`
  pelas colunas já liberadas no `grant`. Desvincular o Telegram e excluir a conta não cabem em
  `grant` — `telegram_chat_id` é do webhook e `auth.users` o cliente não apaga — então são funções
  `security definer` filtrando por `auth.uid()`, na migration `0013`. Desvincular rotaciona o
  `token_vinculo` junto, senão o link antigo continuaria valendo.
- **Exclusão de conta é em duas etapas** (04/09/2026): `excluir_minha_conta()` marca `excluida_em`
  e solta o chat do Telegram, porque a coluna é `unique` e segurá-la reservaria o chat por 60 dias
  contra uma conta nova da própria pessoa. Quem para a entrega é o `excluida_em is null` na consulta
  dos perfis, e a policy de update recusa escrita em perfil marcado. O apagamento
  definitivo vem no job diário, depois de `DIAS_ATE_APAGAR_CONTA_EXCLUIDA`, e leva junto os eventos
  anteriores ao login, que só têm `sessao_id` e nenhuma cascata alcança. A sessão **não** é
  encerrada ao pedir: sem ela a pessoa não voltaria para cancelar.
- **Conta confirmada sem perfil é apagada na hora** (13/09/2026, `0024`). Quem confirmava o e-mail
  e não salvava o perfil ficava com e-mail e senha no Auth sem saída: a exclusão marca
  `perfis.excluida_em` e o job só apaga a partir de `perfis`. `apagar_minha_conta_sem_perfil()` é
  `security definer`, sem argumento, filtrada por `auth.uid()` e executável só por
  `authenticated`; recusa conta com perfil, que segue as duas etapas, e trava a linha do Auth antes
  de conferir, para não correr com um perfil sendo criado. Apaga o que o job apagaria: os eventos
  anônimos das sessões da conta e o usuário do Auth, que leva o resto por cascata. Sem prazo porque
  os 60 dias existem para cancelar sem perder perfil e histórico, e sem perfil não há o que
  preservar; reter o e-mail sem finalidade vai contra a LGPD. Um registro para o job apagar
  exigiria tabela nova e mudança no `radar/`. O site oferece "Excluir minha conta" sob o formulário
  de completar o perfil, com a confirmação de sempre (que saiu de dentro de `#account-state` para
  abrir nesse estado), e encerra a sessão local depois. Publicação: `db push` antes do merge, porque
  o site novo chama a função e o atual não a conhece. Se a `0024` subir antes da `0023`, o push da
  `0023` pede `--include-all`.
- **`ativo` é só da pausa; exclusão não escreve nele** (04/09/2026). O gatilho da `0005` emite
  `entregas_pausadas` em toda transição de `ativo` para `false`, então exclusão entrava no funil
  como pausa; e cancelar, que punha `ativo = true` sem saber o estado anterior, devolvia ao ar quem
  tinha pausado antes de excluir. Marcar em vez de destruir é o que faz cancelar ser desfazer.
- **Nunca alterar tabela pelo painel do Supabase** — só por migration em `supabase/migrations/`.
- **SQL aplicado fora do CLI não entra no histórico de migrations** (06/09/2026): as `0014`–`0016`
  tinham todos os objetos no banco e nenhuma linha em `supabase_migrations.schema_migrations`.
  Como o `db push` grava o registro na mesma transação em que aplica, três aplicadas e nenhuma
  registrada denunciam SQL rodado direto — pelo painel, por `db query` ou por psql. O efeito só
  aparece depois: com a coluna `remote` vazia, o push seguinte tenta reaplicá-las e quebra no
  primeiro `add column` de coluna existente, deixando a migration nova pela metade. Foi
  reconciliado com `supabase migration repair --status applied 0014 0015 0016`, que só grava o
  registro e não reexecuta SQL. **Conferir `supabase migration list --linked` depois de aplicar e
  antes do próximo push** — é o que torna visível a regra de nunca aplicar pelo painel.
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
- **Toda execução se reporta** ao `TELEGRAM_CHAT_ID`, que com banco passa a ser o chat de
  operação: usuários ativos, quantos receberam recomendação, vagas enviadas e requisições. Kill
  por timeout, que o Python não consegue reportar, é coberto pelo passo `if: failure() ||
  cancelled()` do workflow. O passo do radar tem timeout próprio (28 min, abaixo dos 30 do job)
  para o estouro contar como falha do passo: o GitHub trata o estouro do job como cancelamento,
  e a documentação não diz se `failure()` vale nesse caso.
- **Cada linha de `envios` tem um `token` único**, gerado em Python antes do envio porque a
  mensagem precisa do link antes de a linha existir. Envio que falha ao ser gravado deixa um token
  órfão, e a Edge Function `ir` trata isso redirecionando para a landing.
- Ativação operacional = primeira entrega bem-sucedida com ao menos uma recomendação;
  `perfis.ativado_em` é gravado uma única vez, na transação dos `envios`. `docs/metricas.md`
  separa esse marco da ativação de produto.
- `domain/perfil_fixo.py` é um perfil **sintético** (`perfil_de_exemplo`), usado só quando não há
  `DATABASE_URL`. O repositório é público: nunca colocar ali dados reais de ninguém.
- **Eventos do site têm limite no banco** (13/09/2026, migration `0023`). A chave pública deixava
  inserir em `eventos_produto` sem fim, trocando de `sessao_id` a cada requisição e com 4 KB de
  propriedades, e banco cheio no plano gratuito fica só leitura, o que para cadastro, vínculo e
  diário. Evento `web` agora tem propriedades de até 256 bytes, no máximo 60 por sessão e 60 por
  conta na última hora e um teto por hora de 2.400 para visitantes e 900 para contas
  (`teto_de_eventos_do_site_por_hora`, contados em `eventos_do_site_por_hora`); acima disso o
  insert falha com `PT429` (HTTP 429 no PostgREST) e o site só avisa no console. O teto é o que
  limita o tamanho, porque limite só por sessão se fura trocando de sessão. Ele comporta um dia de
  divulgação: 150 cadastros numa hora, cada um com ~10 eventos anônimos (funil com idas e voltas)
  e 6 de conta, mais 3 curiosos por cadastro com landing e CTA; o primeiro teto, 600, perdia
  metade dos eventos anônimos de uma turma de 150. Pior caso sob abuso contínuo: 79.200 linhas por
  dia, de 440 a 490 bytes cada com índices, ~35 MB por dia, o que enche 500 MB em ~2 semanas. Por
  isso o resumo de operação mostra os eventos do site das últimas 24 h e avisa quando algum teto
  foi atingido; banco sem a tabela ou leitura que falha só gera aviso no log. Eventos do banco e do
  Telegram não passam pelo gatilho. Custo aceito: sob abuso, os eventos anônimos legítimos daquela
  hora se perdem e o funil conta visitantes falsos até o teto. Deduplicar marcos por sessão ficou
  de fora, porque o funil já conta pessoas distintas. O check de 256 bytes é `not valid`: não
  confere as linhas antigas, mas barra `update` futuro de linha web antiga maior que isso; hoje
  nada atualiza linha web. A `0023` pode ir ao banco antes do merge: o site atual já grava dentro
  dos limites.
- **Textos do perfil têm teto no banco** (13/09/2026, migration `0025`). Uma conta comum gravava
  210 mil caracteres em `perfis.curso` por `update` direto, e o cadastro guardava em
  `cadastros_pendentes` qualquer chave extra do JSON. Os checks de `perfis` são **validados**, não
  `not valid` como o da `0023`: `perfis` é atualizado todo dia pelo job e pelo webhook, às vezes em
  lote, e um check `not valid` deixaria uma linha antiga acima do teto derrubar esses updates longe
  da migration. Validado, um perfil acima do teto faz o `db push` falhar inteiro, sem aplicar nada,
  e o erro nomeia a constraint: corrigir a linha e repetir. `validar_cadastro_radar` passou a
  recusar chave desconhecida no cadastro e no perfil; todas as versões do site mandaram só as
  conhecidas. Grants e policies não mudam; a função nova do check fica com o grant padrão, como a
  `habilidades_do_perfil_validas` da `0018`, e precisa dele: o check roda com o papel de quem grava,
  e sem `execute` o update do próprio dono falha. Pode ir ao banco antes do merge: o site atual já limita
  cidade e habilidade e o cadastro já passava pela validação; só um curso de mais de 200 caracteres
  digitado na edição seria recusado, com a mensagem genérica de erro. Continua sem teto nosso o
  `raw_user_meta_data` do Auth, que o navegador escreve pelo `signUp` e pelo `updateUser`.
