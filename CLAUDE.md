# Radar de Estágio

Agente de IA que garimpa sites de vagas de estágio todos os dias e entrega, via Telegram,
apenas as oportunidades compatíveis com o perfil do usuário — ranqueadas e explicadas.

Resumo do produto em `docs/funcionalidades.md`, arquitetura detalhada em `docs/arquitetura.md`,
próximos passos em `docs/plano-geral.md`.

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
  O "hoje" da cota é o dia em UTC, que vira às 21h de Brasília.
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

### Pontuação: por que os pesos são estes

Pesos em `matching/avaliacoes.py`. O que motivou cada trava:

- **Cobertura de requisitos suavizada**, `(1+atendidas)/(1+exigidas)`: requisito ausente do
  perfil vale como incerteza ("não informado"), nunca como veto. As travas de 60/70 pontos por
  habilidade ausente foram removidas em 31/08/2026 porque enterravam vagas boas (EPE Ciência de
  Dados a 48 por "faltar Power BI") enquanto anúncios sem stack ocupavam o topo.
- **Vaga que não declara stack** recebe cobertura neutra de 0.25 (~nota 65): entregável, atrás
  de vaga com boa parte dos requisitos batidos, mas não de *qualquer* vaga com requisito batido:
  quem atende 1 de 8 ou mais tem cobertura menor (2/9 < 0.25). Era 0.35 até 09/09/2026, quando a
  mensagem do Igor mostrou anúncio mudo em 75 acima de vaga em que ele batia MySQL e SQL (69).
- **Vaga sem nenhum requisito atendido não passa da neutra** (10/09/2026). Com um requisito só,
  a suavização dava 0.5 a quem não atendia nada, o dobro da vaga sem stack. A Monte Carlo
  (obrigatório Excel, que não conta em computação, e desejável Power BI) tirava 75 para os dois
  estudantes de Engenharia de Software sem atender nada: na execução de 10/09 ficou em 7º e 9º,
  sem ser enviada, e entre as candidatas não enviadas estava em 1º e 2º. Agora, se nenhum
  requisito que conta na nota é atendido, em nenhuma das listas, a cobertura fica no máximo em
  0.25; quem atende ao menos um segue a fórmula. O teto nunca sobe nota e não é peso novo: é
  coerência com a cobertura neutra, como a troca de 0.35 por 0.25. Office e idioma atendidos em
  computação continuam fora da conta e não tiram a vaga do teto. Medido nas 119 extrações da
  versão atual contra 18 perfis (6 reais e 12 do catálogo): 300 de 2.142 pares caem, 9 abaixo
  da nota mínima. Nas candidatas das últimas 48 h ainda não enviadas dos 4 perfis reais com
  candidatas, saem das 7 primeiras 9 vagas, todas sem requisito atendido; entram 9, seis que
  batem algo do perfil e três sem requisito atendido que ganham pelos outros fatores (curso,
  área, interesse). O teto é da vaga inteira, não de cada lista: obrigatória não atendida com
  desejável atendido continua valendo 0.5 com peso 80%, e a Colégio IPA, que pede "Suporte" e
  cita "Programação", tira 75. Por lista, os pares com nota 70 ou mais sem obrigatória atendida
  cairiam de 15 para 8, mas mudaria também vaga com todas as obrigatórias batidas e um
  desejável faltando; fica para decidir com `vaga_irrelevante`.
- **"Planilhas" é família atendida por Excel** (10/09/2026). Era membro de Pacote Office, não
  nome de família, então Excel não atendia "planilhas" (7 extrações), "planilhas eletrônicas"
  nem "Google Sheets". Com o teto acima, a vaga de Administração que pedia só "planilhas
  eletrônicas" caía de 65 para 54 para a estudante que tem Excel; agora sobe para 75, e 39
  pares da medição acima sobem por isso. Custo aceito: "Controle de planilhas" no perfil deixa
  de atender "planilhas" por palavras, porque a família decide sozinha o requisito que nomeia.
  Seguem abertos: "Pacote Office" no perfil não atende "Excel" (56 extrações; é a única
  habilidade de Office que o catálogo sugere para Direito, Saúde e Educação), e Excel não atende
  "informática" nem "microinformática" (2 extrações cada).
- **Requisito genérico é atendido por habilidade da mesma família** (09/09/2026): "banco de
  dados" por SQL/MySQL/Postgres, "back-end" por Java/Spring/Django/Node, "front-end" por
  React/HTML/CSS/JS, "programação" por qualquer linguagem, "ETL", "cloud", "versionamento",
  "mobile", "pacote Office", "análise de dados" e "IA" idem (`FAMILIAS_DE_HABILIDADES`). O nível
  exigido continua valendo contra o melhor membro presente. Antes, um perfil com SQL, MySQL,
  Java e Spring via zero atendidos em "banco de dados, front-end, back-end, ETL".
- **Soft skill não conta na cobertura de computação** (09/09/2026), como Office e idiomas:
  anúncio cuja única habilidade era "comunicação" ganhava cobertura 0.5 e nota 75. Fora de
  computação continua contando, porque "Comunicação" e "Organização" são habilidades sugeridas
  no cadastro dessas áreas.
- **Desejáveis que faltam aparecem na mensagem** (09/09/2026) como "Diferenciais que a vaga
  cita", logo abaixo dos requisitos a conferir. Só 39% dos anúncios reais listam desejáveis, com
  3 ou 4 itens, então a linha custa ~150 caracteres numa mensagem de 7 vagas. Continuam sem
  virar veto e sem entrar em "a conferir"; o peso de 20% nas habilidades é o de sempre. O rótulo
  é "diferenciais", não "não atendidos", pelo mesmo motivo do "a conferir" do Igor.
- **Idiomas e pacote Office não contam na cobertura** (ninguém os cadastra no perfil), mas
  seguem visíveis na lista de requisitos. As variantes normalizam antes da comparação
  (03/09/2026): "Microsoft Excel" vira `excel` e "Google Sheets" vira `planilhas`. Antes só o
  nome exato era ignorado e a variante pesava — uma vaga de dados caiu para 68 penalizada por
  Google Docs, Drive e Excel. A normalização é por alias, não por pedaço de palavra, para
  `WordPress` não virar `Word`.
- **Modalidade extraída preenche a lacuna da fonte** (05/09/2026): a Adzuna não traz
  modalidade estruturada, então a IA extrai o regime declarado no texto ("remoto",
  "hibrido", "presencial", null se o anúncio não diz — nunca deduzido pela cidade). A
  modalidade da fonte prevalece; a extraída vale na logística, na trava de perfil remoto e
  no rótulo da mensagem. Valor fora do vocabulário vira null sem derrubar o lote.
- **Habilidades comparadas por nome normalizado, depois família e, fora de computação, por
  palavras inteiras** (10/09/2026, revisto no mesmo dia depois da auditoria do #41). Só o nome
  exato deixava estudantes fora de computação sem nada atendido: o anúncio de Direito descreve
  atividades ("revisão de contratos", "atendimento ao público") e o perfil cadastra a habilidade
  ("Contratos", "Atendimento"). As duas vagas do Veirano, que descreviam o perfil de um estudante
  de Direito, ficaram fora com 64 e passam a 86. Fora de computação, quando nome e família falham,
  o requisito é atendido se todas as palavras de um estão no outro, nos dois sentidos, com plural
  dobrado; palavra inteira, nunca pedaço, e "análise de dados" não atende "análise de crédito".
  **Nem perfil nem vaga de computação comparam por palavras**: a primeira versão deixou
  `JavaScript` atender "React JS", `SQL` atender "PL/SQL" e `React` atender "React Native", e lá
  os requisitos são nomes de tecnologia, que o nome exato e as famílias já tratam. A trava olhava
  só o curso até a segunda auditoria de 10/09, e um estudante de Estatística com React atendia
  "React Native" (55 → 93); agora olha também a área da vaga. O custo, medido em 22 perfis × 343
  extrações: em vaga de computação, perfil de outro curso perde também correspondência que não é
  técnica ("inglês técnico" ← Inglês, "atendimento ao cliente" ← Atendimento, "manutenção de
  computadores" ← Manutenção); 24 de 7.546 pares perdem requisito atendido, 4 com nota menor
  (−15, −15, −10, −1), nenhum entre as candidatas reais. Vaga com `area_da_vaga` nula não é
  travada: são programas abertos a várias formações, sem falso positivo encontrado. Requisito com " e ", "/", vírgula,
  ";", "|" ou " & "/" + " com espaços exige todas as partes ("Excel e Power BI" não é atendido
  só por Excel; "F&O" e "R&S" não se partem); separador dentro de parênteses não conta. " ou " e
  "e/ou" são alternativas, e basta uma. O nível dito na última parte vale para as partes sem nível,
  dentro da mesma alternativa ("Inglês e Espanhol avançados"); dito só na primeira, não se espalha
  ("Excel avançado e Power BI"), e não atravessa um "ou". Parte que só tem nível se junta à
  anterior, e a faixa vale pelo menor ("Inglês intermediário/avançado" é atendido por
  intermediário). O nome inteiro do requisito composto exige o maior nível das partes, e o da
  habilidade composta do perfil vale pelo menor, contando parte sem nível: "Inglês e Espanhol
  básicos" não atende "Inglês avançado e Espanhol básico", nem "Inglês avançado e Espanhol"
  atende "Inglês e Espanhol avançados". Limite conhecido: nível no plural depois de "ou" ("Inglês
  ou Espanhol avançados") vale só para a última alternativa; não há caso nos dados. Habilidade do
  perfil escrita assim vira várias, pela mesma regra. Requisito que aparece mais de uma vez com o
  mesmo nome só conta como atendido se todas as versões forem, então a ordem em que a IA listou
  não muda a nota, e a mensagem mostra a versão que falta ("a conferir: Excel avançado" para quem
  tem Excel, não "Excel"). O nível é o maior entre nome, família e palavras,
  para que acrescentar habilidade nunca derrube a nota; família decide sozinha o requisito que
  nomeia; alias vale só para o nome inteiro. Risco aceito: habilidade genérica de uma palavra
  ("Organização", "Gestão", "Processos") atende toda atividade que a contém, e requisito de uma
  palavra ("redes", "segurança") é atendido por habilidade que a contenha ("Redes sociais",
  "Segurança do trabalho"); o pré-filtro corta a maior parte desses cruzamentos entre áreas.
- **Área de interesse** (01/09/2026, revisto em 08/09/2026): a IA classifica a vaga em subáreas
  de um catálogo fechado (`AreaDeInteresse`, derivado de `domain/areas.py`) e o fator compara com
  `perfis.areas_de_interesse`. São três níveis: match ganha o fator cheio; **outra subárea do
  mesmo campo do curso vale meio fator e não gera aviso**; vaga de outro campo zera o fator,
  limita a nota a 65 e põe o aviso "Fora das suas áreas de interesse". Vaga sem subárea
  reconhecida também fica com meio fator. Perfil sem interesses não é penalizado, e área recusada
  no Telegram continua zerando. O nível do meio existe porque punir igual quem marcou "Mercado
  financeiro" e recebeu Contabilidade era mentir no aviso e cobrar duas vezes: estar em outro
  campo já pesa em `PESO_AREA`.
- **Curso** (02/09/2026): incompatível limita a 35 (abaixo da nota mínima, sai da mensagem) com
  o aviso "Exige formação de outra área"; parcial limita a 75 — vaga operacional de fundos com
  Excel/Python/SQL chegou a 90 só pela stack genérica. Desde 03/09/2026 quem decide o nível é
  `matching/compatibilidade.py`, com o catálogo de cursos de `domain/areas.py`, e não mais o
  julgamento do modelo: a IA extrai `cursos_aceitos` e o Python compara. Curso aceito da mesma
  área só conta como equivalente quando a área declara `cursos_intercambiaveis` — verdadeiro só
  em computação, onde Ciência da Computação, Engenharia de Software e ADS disputam as mesmas
  vagas. Sem essa trava, Engenharia Civil valia por Engenharia Química e Contábeis por Economia
  (08/09/2026).
- **Pontos a favor e contra são gerados da comparação** (03/09/2026), não escritos pela IA.
  Sobraram "Curso compatível", "Período mínimo incompatível" e "Exige experiência prévia", porque
  as habilidades já aparecem na lista de requisitos e duplicavam. `alerta_pegadinha` continua
  vindo do modelo.
- **Viés conhecido, registrado em 03/09/2026**: anúncio que declara
  uma tecnologia só e é atendido tira 100, enquanto um que declara cinco e atende três tira 85 —
  a suavização dá 1.0 cravado com 1 de 1. Quanto mais honesto o anúncio, pior a nota. As duas
  correções possíveis e o sinal que reverte a decisão estão na seção de viés do ranking de
  `docs/arquitetura.md`. **Não ajustar peso sem `vaga_irrelevante` real.**

### Áreas: uma fonte só para curso, vaga, banco e site (08/09/2026)

`domain/areas.py` é o catálogo único das 12 áreas. Cada área declara os cursos que caem nela,
três padrões de vaga, os termos de busca e as subáreas. Tudo o mais deriva daí, e é por isso que
nada pode ganhar uma lista própria:

- `AreaDeInteresse` (em `domain/models.py`) é **construído** a partir de `SUBAREAS`.
- A migration `0017` foi **gerada** do mesmo catálogo — o `CHECK` de `perfis.areas_de_interesse`
  e a função `validar_cadastro_radar`.
- `web/assets/areas.json` é **arquivo gerado** e serve o cadastro, que monta as áreas conforme o
  curso digitado. Mexeu em `areas.py`, regere; `tests/test_areas_do_front.py` e
  `tests/test_migracao_das_areas.py` quebram se alguma das três listas sair do lugar.

Os padrões são dois de propósito: `titulo` é amplo e responde "essa vaga é da minha área?";
`exclusao` é estreito e responde "essa vaga é inequivocamente de outra?". O padrão `titulo`
compilado inclui automaticamente os nomes de curso e os rótulos de subárea da área — "Estágio em
Engenharia de Alimentos" e "Produção de Material Didático" contam sem lista extra.

Precedência do pré-filtro (`fora_da_area_do_curso`, revista em 08/09/2026 à noite):
1. Descrição que cita o curso do perfil **com contexto de formação** ("cursando X", "estudantes
   de X", "aceita X", "cursos: X") ou que abre a qualquer formação mantém. Sem o contexto, "terá
   direito a vale-transporte" mantinha toda vaga para Direito e "boa comunicação" mantinha tudo
   para Comunicação — 19 de 20 casos falsos numa auditoria. Desde a noite de 08/09 a exigência
   vale também para nome composto ("consultoria em recursos humanos" mantinha tudo para RH), a
   janela é de 24 palavras (listas longas de cursos aceitos) e o contexto não atravessa rótulo
   "campo:" — anúncio de agência traz "formação: não informado … ramo: recursos humanos".
   Desde 10/09/2026 a busca inclui os sinônimos de nome composto que o catálogo converte no
   curso da pessoa (`nomes_do_curso`): quem cursa Ciências Contábeis procurava só "contabilidade"
   e perdia "cursando Administração ou Ciências Contábeis" — 23 vagas reais, mais 2 de Ciências
   Econômicas e 3 de "gestão de RH". Sigla e palavra solta ("si", "ti", "redes") ficam de fora
   porque aparecem em texto comum ("entre si", "redes sociais").
2. Curso sem área conhecida: mantém só título sem marcador forte de área alguma ("Programa de
   Estágio", "Estagiário"). Sem isso, um perfil de Agronomia passava 96% das vagas (641 de 667)
   para a extração.
3. **Sinal da própria área no título vence o veto de outra área.** "Marketing Comercial" é de
   marketing e de comercial; "Direito Civil" era vetado por `civil` de engenharias, "Estágio
   Administrativo Financeiro" por `financeiro`. Com a ordem antiga, 240 de 315 títulos legítimos
   caíam para o próprio dono; com a nova, zero título com marcador forte é perdido nos dados reais.
4. Sem sinal próprio, marcador forte de outra área descarta; título genérico cai para a descrição.

Os padrões de descrição são estreitos de propósito ("rotinas administrativas", não
"administração"; "área comercial", não "comercial"), porque a citação do curso já é tratada com
contexto no passo 1.

### Qualidade da mensagem e do pré-filtro

- `NOTA_MINIMA` (padrão 40) corta vagas fracas da mensagem. Sem aprovadas, o estudante recebe
  que nada compatível apareceu e que a busca volta amanhã: silêncio total pareceria serviço
  morto. Depois de `DIAS_DE_SILENCIO_ATE_AVISAR` dias sem nenhuma recomendação, e no máximo uma
  vez por período, a mesma mensagem ganha um parágrafo sugerindo ampliar cidade ou modalidade —
  parágrafo, e não segunda mensagem, para não notificar duas vezes no mesmo dia.
- `fora_da_area_do_curso` (`domain/areas.py` + `filtering/prefiltro.py`) exige sinal da área do
  curso da pessoa no título ou, se o título for genérico, na descrição; título de outra área
  descarta antes de tudo. Cada área tem dois padrões: `titulo` (amplo, "é da minha área?") e
  `exclusao` (estreito, "é inequivocamente de outra área?"), porque um padrão só derrubaria
  vagas legítimas. Curso sem área conhecida não filtra por área — melhor recomendar demais que
  emudecer o radar.

- O fator de interesse (`PESO_INTERESSE`) tem três níveis: subárea marcada vale cheio, outra
  subárea do mesmo campo do curso vale metade e sem aviso, e vaga de outro campo zera e avisa.
  Punir igual quem marcou "Mercado financeiro" e recebeu uma vaga de Contabilidade era mentir no
  aviso e cobrar duas vezes, já que estar em outra área já pesa em `PESO_AREA`.

### Auditoria adversarial de 08/09/2026 (noite): o que mais mudou

Três revisores independentes e uma medição em produção depois da expansão. Regras que ficaram:

- **Extração e nota.** `area_da_vaga` é normalizada no modelo e vira `None` se não está no
  catálogo — "Computação", "tecnologia" ou "" viravam área alheia (teto 35). O fator de interesse
  decide "mesmo campo" pelas subáreas da vaga contra as dos interesses (`AREA_DA_SUBAREA`), não
  pela área da vaga nem pelo curso: programa aberto a várias formações com subárea de computação
  ganhava aviso falso. O teto de 65 só vale para outro campo, área recusada ou vaga sem subárea
  reconhecida; outra subárea do mesmo campo não é presa a 65. Curso genérico aceito
  ("Engenharia", "Sistemas", "Negócios") vale se estiver inteiro no nome do perfil e o catálogo
  reconhecer o perfil. Qualificadores de nível saem da habilidade ("Excel avançado" → excel;
  "Office 365" → office), senão furavam a exclusão de Office em computação e não casavam fora
  dela.
- **Recusas e histórico.** Recusa no Telegram nunca cancela uma subárea escolhida no cadastro
  (a vaga recusada carrega várias subáreas). `avaliacoes` é upsert: a nota gravada acompanha as
  regras atuais, porque `baixar_meus_dados` a exporta. Subárea de outro campo gravada no banco é
  ignorada ao carregar o perfil; o site só envia as do curso atual e, sem catálogo, repete as
  salvas em vez de apagar.
- **Cache de extração com versão.** `modelo_extracao` guarda `modelo#hash(prompt+formato)` e a
  leitura filtra por ele: mudar prompt ou catálogo invalida o cache sozinho, sem depender de a
  validação rejeitar o formato antigo.
- **Prompt sem viés de TI.** Habilidades são "ferramentas, idiomas e habilidades", com exemplos
  de várias áreas; pegadinha é "área diferente da que o título sugere"; a lista das 12 áreas e as
  subáreas com rótulo vêm do catálogo.
- **Incidente das 16:13 de 08/09.** Primeiro run com o motor novo: cota gratuita do Gemini (20
  requisições) estourou porque 503 dividia o lote e multiplicava requisições; 0 de 36 vagas foram
  extraídas e o run "passou" enviando 13 vagas com notas antigas guardadas. Desde então 502/503/504
  esperam e repetem o **mesmo** lote (`AvaliadorIndisponivel`), e o resumo do Telegram e o stdout
  mostram "vagas sem extração" e "extrações não gravadas" — antes só o log sabia. Com o recálculo
  total do Igor, cota estourada hoje significa **zero envio**, e o resumo tem que denunciar.

As habilidades sugeridas no cadastro vêm do catálogo por área (`Area.habilidades`) e são montadas
ao entrar na etapa de habilidades; a lista de computação é a mesma de antes. Curso sem área
conhecida não recebe sugestão alguma desde a expansão: oferecer `HABILIDADES_GERAIS` a quem o
catálogo não reconhece era sugerir a área errada, e o campo continua no catálogo sem leitor no
site. Habilidade também deixou de ser obrigatória — lista vazia significa "não informou", nunca
incapacidade, e o site limita 50 itens de 100 caracteres porque a `0018` cobra isso no banco.
O aviso "Área que você recusou" nomeia as subáreas pelo rótulo do catálogo.

Sabidos e não corrigidos: republicação por outra fonte com descrição curta pode reenviar;
o banco ainda aceita subárea de outro curso (mitigado ao carregar); a Jooble multiplica
consultas por termo (segue desligada). A chave por `id_externo` sem `fonte` foi corrigida em
10/09/2026, na rodada de confiabilidade.

### Segunda rodada de falhas reproduzidas (08/09/2026, fim de tarde)

Cinco falhas que a auditoria anterior deixou passar, cada uma reproduzida por um teste que
falhava antes da correção:

- **Lote perdia o que já tinha extraído.** A repetição por erro temporário envolvia o lote
  inteiro, inclusive a reextração uma a uma das vagas que o modelo omitiu. Um 429 numa única
  vaga omitida repetia o lote quatro vezes e descartava as extrações certas. Agora só a chamada
  à API é repetida (`_chamar_esperando_a_cota`) e cada lote acumula o resultado antes de a cota
  interromper; divisão do lote continua só para erro não temporário.
- **Nível básico satisfazia requisito avançado.** Tirar o qualificador de nível para comparar o
  nome fazia "Inglês básico" valer por "Inglês fluente" (nota 100). O nome segue comparado sem
  o nível; o requisito só é atendido se o perfil declara nível igual ou maior (básico 1,
  intermediário 2, avançado/fluente/nativo 3). Requisito sem nível aceita a habilidade conhecida;
  requisito com nível exige que o perfil declare o seu (Igor, 08/09 à noite: "Excel" no perfil
  não comprova "Excel avançado"). A lista na mensagem virou "Requisitos a conferir no seu
  perfil". No corpus antigo (só computação) apenas 4 de 202 extrações citam nível; em Direito e
  Administração é o padrão.
- **Falha parcial virava "nenhuma vaga compatível".** O silêncio só valia quando nenhuma
  candidata tinha extração; com parte extraída e nada acima da nota mínima, o usuário recebia
  uma conclusão que o sistema não podia tirar. Qualquer candidata sem extração segura a mensagem
  e volta a ser candidata no dia seguinte.
- **Logout herdava áreas de interesse.** `#logout-account` limpava formulário e habilidades,
  mas não `areasEscolhidas`/`areasSalvas`, e a grade da etapa 4 é remontada a partir delas. O
  mesmo esquecimento vale ao trocar de conta dentro do formulário, onde as salvas eram reserva
  sem catálogo.
- **IA processava vaga já entregue a todos.** As candidatas iam para a extração antes dos
  envios; com o cache versionado por prompt, cada mudança de prompt reextraía o histórico
  inteiro. `candidatas_de_algum_perfil` agora consulta `ids_ja_enviadas` por usuário; falha ao
  lê-los mantém a vaga na extração, nunca o contrário (`atender_usuario_travado` reconsulta e
  segue estrito).

Lição de método: os quatro pontos do Igor e a auditoria anterior foram verificados lendo o
código e rodando a suíte que já existia — que só cobria o que já se sabia. Falha nova se
procura escrevendo o teste que a reproduz **antes** de mexer no código.

### Terceira rodada: auditoria com as vagas reais do banco (08/09/2026, noite)

Feita rodando pré-filtro, normalização de curso e nota sobre as 415 vagas e 202 extrações
guardadas, com 12 perfis sintéticos de áreas distintas, e validando SQL, Telegram e funções com
sondas executáveis. O que mudou:

- **"Tecnologia da Informação" virava `informacao`.** `normalizar_curso` tirava todos os prefixos
  de formação de uma vez, e "tecnologia" + "da" é prefixo. É o nome de curso mais citado nos
  anúncios reais (36 de 202 extrações); anúncio que aceitava só ele ficava incompatível (teto 35)
  para todo estudante de computação. A normalização agora tira um prefixo por vez e para no
  primeiro nome que o catálogo ou os sinônimos conhecem; o site espelha a regra, e
  `tests/fixtures/cursos_normalizados.json` trava a paridade dos dois lados, uma entrada por forma
  de escrever o curso. Entraram sinônimos vistos nos anúncios: Sistemas da Informação, SI, Redes, Data
  Science, T.I, Gestão da TI, Processamento de Dados. Em 10/09/2026 entraram Ciências Jurídicas
  e Ciências Jurídicas e Sociais: a vaga que aceitava só esse nome dava curso incompatível (teto
  35) a quem cursa Direito, e "Estágio em Ciências Jurídicas" caía no pré-filtro porque o padrão
  de direito só aceitava "jurídico"/"jurídica" no singular (achado na mensagem de um estudante de
  Direito do piloto). O plural vale no título e na exclusão, e "jurídica(s)" não conta depois de
  "pessoa(s) ", "pessoa(s)-", "física(s) e " nem "contas " (`JURIDICO_FORA_DE_PESSOA_JURIDICA`):
  "Crédito para Pessoas Jurídicas" é de finanças e "atendimento do público pessoa jurídica" é de
  agência bancária. Na descrição fica o singular, com a mesma trava. A trava só funciona porque o
  pré-filtro usa a normalização do catálogo, que junta espaços: até a segunda auditoria de 10/09
  ele tinha uma `normalizar` própria, e "Pessoas  Jurídicas" com espaço duplo escapava.
- **Termo de área na descrição exige contexto.** Título genérico era mantido por "com direito a
  bolsas" (Direito), "ramo: recursos humanos" na assinatura de agências (RH), "mercado
  financeiro" no blurb da empresa (Economia), "farmácia online" nos benefícios (Saúde). Nos dados
  reais, 7 de 7 vazamentos de Direito e 4 de 4 de RH eram assim. `descricao_e_da_area` aceita o
  termo só depois de contexto de formação ou de atuação ("área de", "rotinas de", "conhecimento
  em"); `menciona_o_curso` exige contexto de formação, inclusive para nome composto. Efeito
  medido: RH 19 → 11 candidatas, Enfermagem 5 → 2, computação 303 → 290, sem perder as listas
  "cursando engenharia mecânica ou produção".
- **Falha ao ler o histórico de um usuário derrubava o run.** `ErroDeArmazenamento` em
  `ids_ja_enviadas`, `recusas_do_usuario` ou `vagas_enviadas_recentemente` subia até `executar`.
  Vira aviso do usuário afetado, como já era para gravar e enviar.
- **Perfil híbrido ou indiferente recebia vaga presencial de outra cidade** (achado numa rodada
  de ponta a ponta com coleta real: pedagogia híbrida do Rio recebeu estágio em Palhoça/SC com
  nota 61 e sem aviso). O pré-filtro só conferia cidade para perfil presencial, e a logística
  vale 5 pontos. Agora, para quem não é remoto, vaga de outra cidade só fica se admite remoto
  (modalidade da fonte ou "remoto"/"home office" no texto); depois da extração, vaga presencial
  ou híbrida em outra cidade fica limitada a 30 com aviso próprio, como já acontecia com perfil
  remoto. Perfil presencial continua exigindo a própria cidade mesmo para vaga remota — desde
  10/09/2026, a própria cidade ou uma da mesma região imediata do IBGE.
- **Estágio de mestrado ou doutorado chegava a graduando.** "Estágio de Mestrado em Economia"
  (EPE) foi a um perfil de Direito com nota 55, só com o alerta de pegadinha. Título com
  mestrado, doutorado ou pós-graduação sai no pré-filtro, como já saía "pleno" e "sênior".
- **Estágio de ensino médio chegava a universitário** (09/09, execução real com 12 perfis):
  "Vaga de estágio para estudantes de ensino médio" foi para Pedagogia com nota 60, porque
  "ensino" é sinal de educação no título. Título de ensino médio, nível médio ou jovem aprendiz
  sai no pré-filtro, exceto quando também diz superior, graduação ou faculdade ("Nível Médio e
  Superior" fica); e "ensino médio" deixou de contar como sinal de educação. Na coleta do dia,
  11 títulos assim entre 983.

Conferido e correto: as 20 constantes SQL e o `metricas.sql` passam por `EXPLAIN` contra o
schema real; mensagem com 7 vagas longas e `<`, `&` nos textos divide em partes abaixo de 4096
com tags fechadas; janela da entrega imediata é 09:23–10:23 UTC (06:23–07:23 de Brasília);
suítes das Edge Functions (8 + 24) e do cadastro (38) verdes; nenhuma ref remota alcança commit
do Claude.

**Sete:** o workflow manda até **7** vagas (`QUANTIDADE_VAGAS_ENVIADAS: "7"`, commit de 03/09,
porque com 5 slots vaga boa saía da janela sem ser enviada). A landing de 08/09 prometia "até
cinco"; Ian decidiu manter 7, a landing passou a dizer "até sete" e o PR #22 do Igor adotou o
mesmo valor no padrão do código, na copy e no plano de expansão.

### Rodada de confiabilidade (10/09/2026)

Correções de uma revisão externa, cada uma com o teste que reproduz a falha antes do conserto.
O que muda para quem opera:

- **A conexão do banco abre em `autocommit`.** Sem isso a primeira consulta abria transação
  implícita e os blocos `transaction()` viravam savepoints: nada era confirmado para outra
  conexão até o processo fechar. A mensagem chegava antes de o token do envio existir para o
  webhook, e a trava do perfil era liberada antes da confirmação. Nunca voltar `autocommit`
  para o padrão sem mover a fronteira da transação junto.
- **Vaga é `(fonte, id_externo)` em todo dicionário do fluxo**, e o `id_vaga` do prompt é
  `fonte:id_externo`. Antes, duas vagas com o mesmo número em fontes distintas viravam uma só e
  o mesmo anúncio era entregue duas vezes. O `id_vaga` guardado nas extrações antigas continua
  sendo só o número; a leitura não usa esse campo, usa as colunas.
- **A chave de duplicata inclui a cidade.** Duas vagas presenciais da mesma empresa e título em
  cidades diferentes viravam uma só antes do filtro por perfil, e quem era da outra cidade
  perdia a vaga em silêncio.
- **O prompt preserva o nível da habilidade.** Ele mandava apagar ("Excel avançado" → "Excel")
  enquanto o pontuador distingue nível desde 08/09, então requisito avançado passava por
  atendido. **Isso mudou `VERSAO_DA_EXTRACAO` de `ace8b756` para `7efdbc95`: a primeira
  execução depois do merge reextrai as candidatas e gasta cota.** Acompanhar o resumo das 07:23.
  `tests/test_contrato_extracao_pontuacao.py` cobre a fronteira; teste de etapa isolada não pega
  esse tipo de falha, porque cada lado passa sozinho.
- **Recusa corrigida deixa de penalizar.** As consultas de recusa por área e de vaga repetida
  liam todo evento negativo, inclusive o que a pessoa depois trocou por "essa serviu". Agora leem
  a última resposta por vaga, como as métricas já faziam. Os testes rodam em PGlite
  (`tests/web/recusas_test.ts`), lendo o SQL direto do `postgres.py`, então não dependem de
  banco de teste.
- **Negação não conta como exigência de experiência**: "não exigimos 2 anos de experiência" era
  descartado antes da IA. A negação vale só dentro da mesma frase.
- **Falha de entrega temporária não pausa mais o perfil.** Só HTTP 403 e o 400 que nomeia o
  destinatário (`chat not found`, bot bloqueado) contam para `falhas_de_envio`. Indisponibilidade
  do Telegram e erro de formatação nosso viram aviso do dia. Além disso, resposta de erro sem
  corpo JSON levantava `JSONDecodeError` de dentro do `except` e derrubava a execução inteira,
  deixando sem mensagem quem vinha depois na fila.
- **Travessão no nome do curso.** O Python descartava caracteres fora do ASCII, então "Letras –
  Português" virava "letras portugues" e ficava sem área, enquanto o site já tratava travessão
  como hífen e gravava os interesses. macOS e iOS trocam " - " por " – " sozinhos. O inverso
  também acontecia: o site só conhecia o "–", e "Direito — Bacharelado" (travessão longo, que o
  macOS põe no lugar de "--") ficava sem área no cadastro e gravava o perfil sem interesses. Desde
  10/09/2026 o `normalizarTexto` do site espelha o `normalizar` do Python: os mesmos cinco traços
  viram hífen, caractere fora do ASCII sai e espaços se juntam; a fixture de paridade tem as formas.
  A mesma função serve a busca de cidade: apagar o que não é ASCII fez o apóstrofo curvo (’ ‘ ʼ)
  sumir ("d’Oeste" virava "doeste"), e as 47 cidades com apóstrofo digitadas assim deixaram de
  ser achadas; com "'" ou "´" continuavam funcionando. A correção fica em `textoDeBusca`, que
  é só da cidade e troca o apóstrofo curvo por espaço antes de normalizar. Pôr a troca em
  `normalizarTexto` quebrava a paridade do curso ("Pedagogia’" ficava sem área no site), e a
  fixture tem essas formas. Mudou `normalizarTexto`, teste a cidade junto com o curso.
- **`python -m radar descartes --amostra 30 --saida arquivo.json`** grava uma amostra do que o
  pré-filtro cortou, com o motivo, para rotular à mão. É o lado que o `julgar` não alcança: ele
  mede a vaga entregue, nunca a boa vaga que sumiu antes da IA.
- **As suítes rodam em pull request** (`.github/workflows/testes.yml`): pytest, ruff e as três
  suítes Deno. Os testes de integração Postgres continuam de fora, porque exigem o schema do
  Supabase.
- **O cliente supabase do site tem versão fixa** (`2.116.0`), não mais `@2`.

Não corrigido de propósito: os pesos da nota. A regra de não recalibrar sem `vaga_irrelevante`
real continua valendo. Perfil sem habilidade cadastrada recebia nota alta sem nada distinguir
compatibilidade observada de informação ausente; a resposta foi um aviso na mensagem
("Nota calculada sem habilidades no seu perfil"), não um peso novo.

### Entrega no Telegram (10/09/2026)

- **Falha no meio da mensagem não apaga o que chegou.** A mensagem de sete vagas vai em várias
  partes; se a segunda falhava, nada era gravado e no dia seguinte tudo voltava. O notificador
  informa quantas partes o Telegram aceitou, `recomendacoes_por_parte` diz quais vagas estavam
  nelas, e só essas entram no histórico. Efeito colateral aceito: o teclado de feedback fica na
  última parte, então vaga entregue numa falha parcial fica sem botão.
- **Texto vindo da fonte tem teto.** A divisão só corta no separador entre vagas, então um bloco
  grande passava de 4096 e o Telegram recusava a mensagem inteira com 400, que ainda contava como
  falha de envio do usuário. Título, empresa, localização, requisitos, pontos, avisos e alerta
  são cortados **depois** do escape, para não partir uma entidade HTML. Pior caso medido: 3216
  caracteres por bloco.
- **A data da mensagem é a de Brasília**, não a do UTC. Entrega imediata entre 21:00 e 23:59
  chegava datada do dia seguinte; o diário das 07:23 nunca mostrou o problema.

### Cidades vizinhas: região imediata do IBGE (10/09/2026)

Quem mora em Niterói trabalha no Rio, mas a cidade era comparada pelo nome exato. Nos 30 dias
anteriores, 448 vagas chegaram como "Rio de Janeiro" e 1 como "Niterói": um perfil presencial de
Niterói praticamente não recebia nada. A Adzuna ainda rotula pela região, e "Estágio TI - Niterói"
veio como Rio de Janeiro.

`domain/regioes.py` classifica vaga × perfil em mesma cidade, mesma região imediata do IBGE ou
distante, lendo `radar/domain/regioes_imediatas.json` (510 regiões, gerado por
`scripts/gerar_cidades.py` junto com a lista do site). O que muda:

- **Mesma região vale como a cidade** no pré-filtro e na trava de 30 para híbrido e indiferente.
- **Na logística vale metade** da cidade, cerca de 2,5 pontos a menos: a própria cidade continua
  na frente, sem enterrar a vizinha.
- **A coleta busca também a maior cidade da região** do perfil (Adzuna `where`),
  senão um perfil de Niterói sozinho dependeria de haver alguém do Rio para as vagas do Rio
  serem coletadas.
- **O juiz recebe as cidades da região** no perfil; sem isso ele marcaria `logistica` na vaga
  do Rio para quem é de Niterói.
- **O estado da vaga é lido nos formatos das fontes** ("Estado do Rio de Janeiro", "Rio de
  Janeiro", "RJ"). Sem estado, vale o nome quando ele só existe num estado; perfil antigo
  "Rio de Janeiro" continua achando a região. Nome igual em estados diferentes deixou de ser a
  mesma cidade.

Limite conhecido: a região imediata do Rio tem 21 municípios e inclui Saquarema e Mangaratiba, a
cerca de 100 km. Se o feedback "local ou modalidade" apontar esses casos, o ajuste é uma lista de
exceções ou a região metropolitana, não voltar ao nome exato.

### Juiz de recomendações: LLM as a judge (09/09/2026)

`python -m radar julgar --dias 7 --amostra 30` pede a um **segundo modelo** que julgue, às
cegas, uma amostra das entregas recentes: para cada vaga enviada, `relevante`, `nota_juiz`,
`problema` (catálogo fechado: outra_area, exige_demais, logistica, repetida, anuncio_fraco,
nenhum) e um motivo. O juiz vê o perfil e o anúncio completo, **nunca a nota do Radar**, para o
julgamento ser independente. O relatório (`reporting/julgamento.py`) traz relevância por perfil,
problemas, concordância com o feedback das pessoas quando existir, e as vagas reprovadas pelo
juiz com nota do Radar acima de 70 — a lista que interessa para revisar regra.

O modelo vem de `JUIZ_MODELO` (padrão `claude-sonnet-4-6`, outra família que a do extrator)
e o adapter segue `AVALIADOR`: `agy` local, sem cota; pela API precisa ser um modelo Gemini. O
comando só lê o banco; nada de nota alterada. Só pontuação por regra em Python decide o que é
enviado — o juiz mede, não ranqueia. Antes de usar o número do juiz como evidência, ele precisa
ser validado contra o gabarito humano de 20 vagas (pré-PRD, H2); abaixo de 75% de concordância
é ruído com cara de número.

Primeira rodada real (09/09, `claude-sonnet-4-6` pelo `agy`, 24 de 168 entregas de 14 dias, 5
minutos): 12 relevantes, mediana do juiz 39 contra 69 do Radar. As cinco reprovadas com nota
alta eram todas de 28 a 31/08, antes das regras de área, interesse e cidade — o relatório mostra
a data de cada uma por isso. Limitação que o juiz expôs: a Adzuna informa a região, não a
cidade ("Estagiário de TI - São Gonçalo" vem como "Rio de Janeiro"); 1 caso em 168 envios,
registrado, sem regra nova.

Desde 10/09/2026 o comando **falha com código 1** quando nenhuma entrega é julgada, imprimindo
o último erro do avaliador. Antes, o padrão `gemini_api` + `claude-sonnet-4-6` devolvia
relatório vazio com código 0, o que parecia execução limpa. O `--gabarito` também avisa quantos
rótulos ficaram fora da janela de `--dias`, em vez de descartá-los em silêncio.

O gabarito humano nasce de `python -m radar gabarito --dias 2 --amostra 20 --saida arquivo.json`:
o arquivo lista as entregas com `relevante: null` para cada pessoa preencher com true ou false;
`julgar --gabarito arquivo.json` julga só essas e imprime a concordância juiz × pessoas. O
primeiro arquivo, com 20 entregas de 08 e 09/09, saiu do Git em 12/09 porque trazia vagas reais e o
`perfil_id` de cada usuário: fica em `gabaritos/`, ignorada, e vai em privado a quem for rotular.

### Quarta rodada: auditoria após a reescrita do `main` (09/09/2026)

O `main` foi reescrito por force push (rebase sobre a PR de estilo e o README). Antes de
auditar, os 13 commits locais foram conferidos por patch-id contra o novo histórico (todos
presentes), o site publicado já servia a nova versão e as quatro suítes passaram. O que a rodada
achou, com coleta real (823 vagas), banco e juiz:

- **Rótulo de subárea entrava no regex de título.** `PADROES_DE_TITULO` junta marcadores, nomes
  de curso e rótulos das subáreas; o rótulo "Segurança" de computação aceitava "Estágio Técnico em
  Segurança do Trabalho" para Engenharia de Software (nota 58, sem menção a curso). Nove títulos
  da coleta, todos de segurança do trabalho. O rótulo virou "Segurança da informação", que já era
  o marcador da área; os outros rótulos só aceitavam títulos coerentes com a área.
- **Contexto de formação atravessava o fim da frase.** "Estagiário na área de gestão financeira
  (Barra). O grupo atende marketing e comunicação" contava "marketing" como curso citado, porque
  "área de" estava a 20 palavras. A janela de contexto (formação e atuação) agora começa no último
  ". " antes do termo. Medido: zero pares (curso, vaga) mudaram em 12 cursos × 823 vagas; só o
  caso encontrado deixa de passar. "; " e quebra de linha não são fronteira porque listas de
  cursos usam os dois.
- **Perfil remoto recebia vaga de outra cidade sem modalidade a 88, sem aviso.** O pré-filtro
  ignorava a cidade para perfil remoto e a logística vale pouco; Administração remota no Rio
  recebeu Fortaleza, Belo Horizonte e Itajaí "modalidade não informada" nas primeiras posições.
  Agora perfil remoto segue a mesma regra do híbrido: vaga de outra cidade só fica se admite remoto.
  Medido para um perfil remoto do Rio em 11 cursos: 947 → 265 candidatas; das 260 descartadas com
  descrição truncada que puderam ser completadas, 18 (7%) citam remoto só no texto completo — a
  mesma limitação que o híbrido já tinha, registrada abaixo. Nenhum usuário atual é remoto.
- **`julgar --gabarito` com arquivo ausente ou inválido** estourava traceback; vira
  `ErroDeArmazenamento` com mensagem e saída 1.

O que foi verificado e não precisou de regra: os 8 envios de outra cidade para perfis presenciais
são todos do run das 07:23 de 08/09, antes da trava das 23:47; o run de 09/09 não tem nenhum. O
juiz (14 de 48 entregas de 2 dias) reprovou com nota alta só casos de 08/09 pela mesma razão,
mais "Estágio em TI" de infraestrutura para Engenharia de Software (subárea de computação; o
interesse do perfil decide) e um anúncio que lista Informática, Computação e ADS sem citar
Engenharia de Software (cursos intercambiáveis por decisão).

Pendências que esta rodada deixou anotadas: (1) refiltrar as candidatas depois do enriquecimento
e antes da extração recuperaria os 7% de vagas remotas que só dizem isso após os 500 caracteres da
Adzuna, sem gastar extração; (2) "Banco de Talentos" não é vaga aberta e chega como estágio;
(3) a Adzuna informa região, não cidade.

### Cobertura das fontes (30/08/2026)

A Adzuna classificava 93% das vagas brasileiras como categoria "Unknown", então `category=it-jobs`
escondia quase tudo (55 vagas em 5 dias no país inteiro). A busca passou a ser por termos, sem
categoria, repetida por cidade de perfil presencial, híbrido ou indiferente (desde 10/09/2026
também pela maior cidade da região imediata do perfil; remoto não acrescenta cidade); a localização vem de
`location.area` (cidade, estado), então bairro não quebra o filtro de cidade. A Gupy deixou de
buscar por termos no título e traz todos os estágios do país e da cidade. Efeito medido: perfil
Rio presencial saiu de 2 para 55 candidatas em um dia.

Paginação da Adzuna (08/09/2026): a busca por termos das áreas cadastradas encontra 4.988 vagas,
mas `LIMITE_DE_PAGINAS_POR_REGIAO` puxava 4 páginas de 50 por região — 4% do disponível, e esse
teto era repartido entre os cursos conforme a base crescia. A página 15 ainda devolve 50 vagas
cheias e relevantes, então o limite subiu para 10. Medido no Rio com quatro áreas: 699 vagas
coletadas contra ~400, e cada curso ganhou de 65% a 120% mais candidatas. Subir páginas é
preferível a buscar por área separadamente: o custo fica plano (10 chamadas por região) em vez de
multiplicar por curso.

Agregadores (Divulga Vagas, BuscarVagas) republicam o mesmo anúncio com "empresa" diferente:
`remover_republicacoes` em `filtering/duplicatas.py` une vagas com mesmo título e cidade cujas 40
primeiras palavras da descrição coincidam em 80% — só o início conta porque a Adzuna trunca a
descrição em 500 caracteres. A mesma regra bloqueia republicação entre dias (04/09/2026): a
candidata é comparada com as vagas enviadas ao usuário nos últimos 30 dias, porque o id novo do
repost furava o anti-repetição por id. Duplicata entre fontes: fica a versão que informa
modalidade e, em empate, a de descrição mais longa.

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


### Correções da revisão de expansão (08/09/2026)

- Cursos passam por correspondência integral após remover prefixos de formação; aliases
  explícitos estão no catálogo e no JSON gerado. Medicina Veterinária fica desconhecida,
  não herda saúde humana; Gestão Financeira tem alias em finanças.
- Perfil sem área reconhecida **soma** uma busca geral (Adzuna sem `what_or`, Jooble com
  "estágio" puro) à busca dirigida dos cursos conhecidos, em vez de substituí-la. Trocar a de
  todos custava 68% das candidatas de computação e 66% das de Direito no Rio (167→54, 116→40),
  porque o `what_or` é o que ordena as 500 primeiras da fatia nacional. Termos de busca são
  palavras soltas: a Adzuna trata `what_or` como OR por palavra, então "recursos humanos" virava
  "recursos" OU "humanos" (1546 vagas contra 1185 da frase); o catálogo usa "recrutamento",
  "rh", "exportação".
- Curso mencionado na descrição com contexto de formação, ou abertura a qualquer formação,
  mantém a vaga para análise mesmo com título de outra área. A compatibilidade de curso é
  decidida após a extração.
- Pontuação é recalculada em Python em toda execução. Notas persistidas não são reutilizadas;
  extrações continuam compartilhadas e histórico de envios continua bloqueando repetição.
- Curso genérico aceito pelo anúncio ("Engenharia", "Química", "Administração") conta como o
  curso específico do perfil quando o nome aceito aparece inteiro dentro do nome do perfil **e**
  o catálogo reconhece o perfil. Sem a segunda condição, "Medicina" valeria para Medicina
  Veterinária — que é desconhecida de propósito. A correspondência integral sozinha marcava
  como incompatível (teto 35) quem estuda Engenharia Civil numa vaga "cursando Engenharia".
- A correspondência integral roda depois de `normalizar_curso`: tira prefixos de formação
  ("Cursando", "Graduação em", "Curso Superior de Tecnologia em"), sufixos ("completo",
  "- Bacharelado", "(Bacharelado)", "/Eletrônica"), aplica sinônimos ("Ciências Econômicas" →
  economia, "ADS", "TI", "RH") e devolve vazio para termo genérico ("Ensino Superior",
  "qualquer curso") — que em `cursos_aceitos` não comprova elegibilidade sozinho. Só abertura explícita
  a qualquer curso libera todas as formações; termos genéricos não anulam cursos específicos. "Licenciatura em X" sem
  alias cai em educação. Prefixos, sufixos, sinônimos e genéricos vão no `areas.json` e o site
  aplica a mesma regra. Nome que ainda não está lá vira área desconhecida: recebe só título
  genérico, busca geral e nota parcial. Ao ver um curso frequente cair nesse caso, o conserto é
  um alias.
- "laboratório" saiu do padrão de exclusão de saúde: vetava "Desenvolvimento de Software para
  Laboratório" para quem é de computação. Continua no padrão positivo, então saúde ainda
  reconhece laboratório como título seu.
- A exclusão de Office e idiomas do cálculo agora se restringe a perfis de computação.
  Nas demais formações, requisitos explícitos contam com a mesma normalização das explicações.
