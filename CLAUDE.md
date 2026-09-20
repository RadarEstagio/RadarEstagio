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
  sem atendimento, e o diário também marca como atendidos os que atende. Disparo recusado pelo
  GitHub deixa a pessoa pendente para a próxima execução, imediata ou diária. `rodar --perfil` de
  perfil já atendido não faz nada: para testar com conta da equipe, zerar
  `entrega_imediata_atendida_em` antes. O backfill marcou as duas
  colunas de quem já tinha vínculo ou ativação. Publicação: `db push` antes do merge, porque o
  `rodar` do `main` passa a exigir as colunas, e o deploy da `telegram-webhook` depois. Se uma
  execução ainda estiver rodando às 07:23, um disparo imediato pode substituir o diário na fila;
  começar a janela às 05:53 fecharia esse caso, e fica como decisão de produto.
  **A marca só vem depois da mensagem (16/09/2026).** Até aqui `rodar --perfil` reivindicava os
  pendentes num `update … returning` e o diário marcava todos os ativos, os dois antes de coletar.
  Adzuna fora do ar, cota do dia sem saldo, mensagem segurada (vaga sem extração, coleta
  incompleta), exceção ou kill deixavam a pessoa sem a primeira mensagem até o diário, e
  `rodar --perfil` de novo respondia "sem entrega a fazer". Num dia de divulgação, esgotada a cota
  do dia, cada imediata falhava sem requisição alguma e marcava todos os pendentes. Agora a
  seleção só lê (`entregas_imediatas_pendentes`) e o pipeline grava `entrega_imediata_atendida_em`
  de cada perfil logo depois de atendê-lo, ainda com a trava do perfil. Conta como atendido quem
  recebeu a mensagem das vagas (inteira ou só parte), a de nenhuma vaga compatível ou a recusa
  definitiva do Telegram (403, bot bloqueado, chat inexistente): repetir na mesma hora não muda a
  resposta, e o diário segue tentando e pausa depois de `FALHAS_DE_ENVIO_ATE_PAUSAR`. Falha
  temporária do Telegram, mensagem segurada, falha ao ler o histórico, destinatário que não se
  revalida, erro de coleta, exceção e kill deixam a pessoa pendente para a próxima execução,
  imediata ou diária, e o histórico de envios impede repetir vaga. Falha ao marcar vira aviso no
  log. A reivindicação saiu, e não entrou coluna nova: as execuções do workflow já são seriais pela
  `concurrency`, e uma reivindicação que sobrevivesse a kill precisaria de prazo gravado. O que
  ela ainda protegia era o `rodar --perfil` manual contra o banco de produção junto com uma
  imediata do workflow; isso ficou com a revalidação do destinatário, que na entrega imediata
  (`RepositorioDaEntregaImediata`) confere, dentro da trava do perfil, se ele continua pendente.
  Limites: o diário não faz essa conferência, então um `rodar` manual durante o diário pode mandar
  uma segunda mensagem (outras vagas ou "nenhuma vaga compatível") a quem estava pendente, o que
  antes só acontecia se o manual começasse primeiro; kill entre o envio e a marca, ou marca que
  falha, faz a próxima execução mandar outra mensagem a essa pessoa. Publicação: sem migration e
  sem ordem; a `telegram-webhook` não muda.
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

**Navegação da conta no celular (16/09/2026).** A conta mostra um painel por vez
(`mostrarSecaoDaConta`), e os links de `.account-nav` são o único caminho para Entregas, Dados e
acesso e Privacidade. A regra que escondia a navegação até 860px vinha de quando as seções apareciam
juntas; depois da troca para um painel por vez, no celular não havia como pausar, sair, baixar os
dados, desvincular o Telegram ou excluir a conta. Agora ela é uma barra horizontal abaixo da marca,
de borda a borda e com rolagem própria, dentro do cabeçalho grudado, que cresce uma linha de 44px.
A barra lateral vira grade para a barra ocupar a linha inteira, e a navegação leva
`contain: inline-size`: sem isso a largura dos links entra no cálculo das colunas da marca e do
"Voltar ao site" e pode quebrar o botão em duas linhas. O JSDOM não avalia media query, então
`test_navegacao_da_conta_segue_visivel_no_celular_com_as_quatro_secoes` lê o CSS e recusa regra de
tela estreita que esconda a navegação ou os links. Limite aceito: quem abre a conta direto numa
seção pelo endereço (`#account-privacy-panel`) pode ver o item ativo cortado na borda direita até
rolar a barra; o título da página já diz a seção.

**Ações da conta conferem a conta mostrada (16/09/2026).** As ações de "Minha conta" usavam a sessão
atual, e o auth-js relê a sessão do armazenamento a cada `getSession`. Com a conta de A na tela e B
entrando em outra aba, Excluir marcava B e soltava o Telegram dele, Desvincular soltava o de B, pausa,
motivo e e-mails gravavam na linha de B, Cancelar exclusão e Baixar meus dados agiam sobre B, e a conta
sem perfil de A apagava B na hora. A página guarda o id da conta desenhada (`contaMostrada`):
`showAccount` o lê da própria linha, e por isso `COLUNAS_DO_PERFIL` traz `user_id`; a conta sem perfil o
lê da sessão que a abriu. Toda ação da conta que chama o Supabase (editar, pausar e retomar, motivo,
e-mails, desvincular, excluir, cancelar a exclusão, baixar os dados e apagar a conta sem perfil) passa
antes por `recusarSeASessaoMudou`: com outra conta na sessão nada é chamado e `recusarPorTrocaDeSessao`
leva ao login com "Sua sessão mudou". É a mesma saída do rascunho de outra dona, que passou a usar
`abrirLogin` e por isso esconde a conta, a confirmação e o "Excluir minha conta" da conta sem perfil.
Sessão ausente segue como antes. Os `update` filtram por `contaMostrada`, não pelo id lido da sessão, e
uma troca entre a conferência e a requisição não grava em B, porque o RLS não deixa o token de B
alcançar a linha de A. As RPCs agem sobre `auth.uid()` e não têm esse fecho: a janela é a de uma
leitura de sessão. Ficam de fora de propósito o "Minha conta" da ativação e a volta à aba, que releem e
desenham a conta da sessão atual, e "Sair da conta", que encerra a sessão que estiver no navegador
(o `signOut` global também revoga as outras sessões dessa conta). Controle novo da conta que chame o
Supabase precisa da conferência, e teste que clica num controle da conta precisa desenhá-la antes
(`?conta`), senão a ação é recusada.

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
  **Anúncio `/land/ad/` não é pedido (14/09/2026).** Parte das vagas vem com `redirect_url`
  `/land/ad/<id>`, que dá 403 sempre, e a mesma vaga em `/details/` também: são 41 no banco desde
  28/08, nenhuma completada, e eram todas as falhas do enriquecimento nos diários de 12 a 14/09
  (19, 18 e 18). O enriquecimento as pula pelo caminho da URL, sem requisição, e o log só conta
  quantas; elas seguem com a trava de 60. No empate que a trava cria, o ranking desempata pela
  nota antes dos limites objetivos (`nota_antes_dos_limites_objetivos`, só em memória): em 14/09
  a Vettore, 81 antes da trava, ficou fora da mensagem de Administração atrás de vagas de 61 e 65
  presas no mesmo 60. O desempate só vale entre notas finais iguais: a vaga presa em 60 segue
  atrás de qualquer vaga com 61 ou mais, mas passa à frente de vaga completa que tirou 60 por
  mérito, porque 81 antes da trava vence 60.
  **A trava segue o que a extração leu (16/09/2026).** A trava de 60 e a linha "Requisitos
  técnicos: não informados na descrição" liam a `descricao_completa` da vaga do dia, mas a
  extração vem do cache e pode ter sido feita noutro dia. Extraída sobre os 500 caracteres da API
  num dia em que o enriquecimento falhou, a vaga perdia a trava quando a página chegava, sem a IA
  ter lido o anúncio; extraída sobre a página, era travada à toa no dia em que o enriquecimento
  falhava. A extração guarda agora `descricao_completa` no próprio JSONB, gravado pelo pipeline
  com a vaga do momento da extração, e `pontuar` o aplica à vaga avaliada, como já fazia com a
  modalidade extraída. O campo é `SkipJsonSchema`: fica fora do formato pedido à IA e do hash, e
  `VERSAO_DA_EXTRACAO` segue `7efdbc95`. Extração feita sobre a cortada volta à IA uma vez quando
  a vaga chega completa (`leu_menos_que`); se a nova não vier (prazo, cota, resposta vazia), a
  antiga segue valendo com a trava, sem contar como vaga sem extração nem segurar a mensagem.
  Sem migration. Medido em 16/09, só leitura: nenhuma das 566 extrações da versão atual tem o
  registro. Das 550 da Adzuna, 96 são de descrição curta que a API já dá inteira, 33 guardam o
  texto cortado (30 `/land/ad/`, que nunca completam) e 421 guardam a página. Nessas 421 o banco
  não diz o que a IA leu, porque `vagas.descricao` fica com o texto mais longo já visto e não há
  histórico: 222 têm item extraído que só aparece depois do 550º caractere da página, 199 não dão
  sinal para lado nenhum, e nenhum dos 5 casos mais suspeitos, conferidos à mão, mostrou leitura
  cortada. Travar as antigas com a página guardada pegaria 141 dos 189 envios de 7 dias, os que
  têm nota acima de 60; reextraí-las seriam até 421 vagas de uma vez (~43 lotes, ~8 min, colado
  no prazo de 600 s) para achar pouco ou nada. Por isso a extração antiga sem registro segue a
  descrição de hoje, como antes: no deploy nenhuma nota muda e nada volta à IA, e o defeito fica
  só no legado, que sai com as vagas vencendo ou na próxima troca de versão. Daqui em diante a
  reextração quase não roda: fora do `/land/ad/`, 3 das 550 extrações de 10 a 16/09 ficaram com o
  texto cortado. O caso que ela cobre é uma queda do enriquecimento, que antes deixaria a coorte
  do dia sem trava para sempre e agora a devolve à IA no dia seguinte (22 a 94 vagas por dia com
  a página guardada no período, de 3 a 10 lotes). Limites: se o enriquecimento sair, as extrações
  feitas sobre a página seguem sem trava até a vaga vencer, e descartá-las pede trocar a versão;
  e 2 vagas com o texto cortado guardado foram pontuadas sem trava, sinal de que a descrição
  completa do dia era mais curta que a da API, então quem lê `vagas.descricao` (o `julgar`, a
  medição acima) pode ver outro texto que o lido pela IA.
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
