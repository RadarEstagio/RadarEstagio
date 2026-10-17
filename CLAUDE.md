# Radar de Estágio

Agente de IA que garimpa sites de vagas de estágio todos os dias e entrega, via Telegram,
apenas as oportunidades compatíveis com o perfil do usuário — ranqueadas e explicadas.

Este arquivo guarda só o que um agente precisa seguir. O índice da documentação é o
`docs/README.md`: o que o produto faz em `docs/funcionalidades.md`, o que falta em
`docs/plano-geral.md`, camadas em `docs/arquitetura.md`, instalação, comandos e testes em
`docs/desenvolvimento.md`.

## Fase atual: MVP de validação com usuários (Fase 2, em andamento)

O produto está no ar em `radarestagio.com`, com entrega diária e feedback por usuário; falta
validá-lo com estudantes. O que funciona e o que ainda não existe estão no catálogo.

## Stack

Python 3.12 com uv (`pyproject.toml`), Supabase (Postgres, Auth e Edge Functions em Deno), site
estático em `web/` no Cloudflare Workers, bot do Telegram que só envia e job diário no GitHub
Actions.

- **Fontes**: só a Adzuna (`FONTES`, padrão `adzuna`), somada por `ColetorComposto`. A Gupy está
  desligada pelos termos e não volta sem autorização; o Jooble está pronto e desligado, e não liga
  em produção sem parceria (a chave tem 500 requisições no total); LinkedIn está fora. Fonte nova
  só entra se a validação comprovar cobertura insuficiente.
- **A IA só extrai fatos da vaga** (Gemini Flash; `AVALIADOR=gemini_api`, o padrão e o do Actions,
  ou `agy` local). Quem compara com o perfil e calcula a nota é Python, sem IA.
- **Agendamento**: o workflow diário só tem `workflow_dispatch`, disparado às 07:23 de Brasília
  pelo cron-job.org. Não adicionar `schedule` nem outro agendador
  ([guia, seção 12](docs/guia-publicacao-e-piloto.md#12-agendamento-tokens-e-ci-do-github)).
- **Workflows**: toda `uses:` aponta para o hash de 40 caracteres, todo workflow declara
  `permissions: contents: read`, o checkout leva `persist-credentials: false` e o `setup-uv` fixa
  a versão do uv local. Hash novo entra em `VERSAO_DE_CADA_ACAO` (`tests/test_workflows.py`),
  conferido com `git ls-remote`. O porquê está no guia, seção 12.
- **Chaves de API** só por variável de ambiente (`.env`, nunca commitado); os secrets do
  repositório têm os mesmos nomes.

## Arquitetura

As camadas de `radar/` estão detalhadas em `docs/arquitetura.md`. A regra que o código não
ensina sozinho: **módulos internos dependem de interfaces do `domain/`, nunca de detalhes de
infraestrutura** (API específica, formato de mensagem, driver de banco). `pipeline.py` orquestra
coleta → dedupe → pré-filtro → extração (uma vez, para todos) → pontuação por perfil → entrega,
sem lógica de negócio própria. Fonte nova se
pluga implementando a interface de coleta, sem alterar o restante do sistema. Sem abstrações
prematuras nem código para casos hipotéticos futuros.

## Decisões técnicas

- **PostgreSQL no Supabase, não SQLite**: o Actions destrói a máquina a cada execução, e
  versionar o `.db` exporia `chat_id` num repositório público. Alternativas na
  [arquitetura](docs/arquitetura.md).
- **Sem framework web nem ORM**: o motor é um script disparado por cron, e `psycopg` 3 acessa o
  banco com SQL puro. `python-telegram-bot` não entra: o bot só envia, e o `/start` e os botões
  chegam por webhook a uma Edge Function, fora do `radar/`.
- **Cadastro no site, não no bot**, com a conta no último passo: `signup` só no envio do último
  passo, nunca ao avançar entre etapas. O site e o `radar/` só conversam pelo schema do banco,
  sem API de um para o outro ([contrato frontend](docs/contrato-front.md)).

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
- **Curso que o catálogo não reconhece nunca apaga área salva**, e sair da conta limpa o que a
  conta desenhou, inclusive o `href` do Telegram, que leva o `token_vinculo`.

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
  `docs/contrato-front.md`, publicação no guia, pendência no plano geral, dado de cobertura,
  custo ou oferta em `docs/frentes-externas.md`. Sumário ou retrato de estado não vira documento
  novo: corrija o dono, porque cópia de estado diverge (16/10). O `CLAUDE.md` só
  recebe o que um agente precisa **seguir**, em até cinco linhas, com link para o registro.
  Sem essa regra o arquivo volta a crescer: passou de 618 linhas em 13/09 para 2.126 em 18/09,
  sempre por relato de correção.

## Regras de operação

### Fontes e Gemini

A leitura dos termos está em `docs/frentes-externas.md`; as medições do Gemini, em
`docs/decisoes-do-motor.md`.

- **Cada anúncio da Adzuna exibido leva a atribuição** "Jobs by Adzuna", com os dois links (no
  site, o logo `web/assets/adzuna-logo.png`). Nunca contatar anunciante que veio dela, e, se o
  acordo acabar, apagar todo dado obtido dela.
- **A cota da Adzuna passa por `CotaDaAdzuna`** (25 por minuto, 250 por dia): cota zerada vira
  erro de coleta, nunca "nenhuma vaga".
- **Evitar rodar `avaliar`/`rodar` repetidamente sem necessidade**: gasta cota da Adzuna e
  requisições pagas do Gemini.

### Motor de recomendação: regras que não podem quebrar

O porquê de cada regra, com os números medidos, está em `docs/decisoes-do-motor.md`. Antes de
mexer em coleta, pré-filtro, extração, pontuação ou mensagem, ler a seção correspondente.

- **Não ajustar peso da nota sem `vaga_irrelevante` real.** Pesos em `matching/avaliacoes.py`.
- **Ausência não é veto.** Requisito ausente do perfil vale como incerteza, e lista vazia de
  habilidades significa "não informou". Requisito de nível básico é atendido pela habilidade
  declarada sem nível; de intermediário para cima, o perfil precisa declarar nível igual ou maior.
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

### Supabase, Telegram e Cloudflare

O porquê de cada item está em `docs/decisoes-do-banco.md`; configuração e conferências, no
[guia de publicação](docs/guia-publicacao-e-piloto.md).

- Projeto ativo: **`xrhvjwemmylwbqgluebc` (`sa-east-1`)**. O `bnzogphdvpubtkcflcue`
  (`us-east-2`) foi criado por engano: não usar, nem remover sem confirmar que nada aponta para ele.
- **Nunca alterar tabela pelo painel do Supabase**, só por migration nova em
  `supabase/migrations/`. Conferir `supabase migration list --linked` depois de aplicar e antes do
  próximo push: SQL rodado fora do CLI quebra o push seguinte.
- **Tabela e sequência novas fazem `revoke all` de `anon` e `authenticated`**: nascem com o grant
  largo do Supabase, e `TRUNCATE` fica fora da RLS. Propriedade nova de evento web ou campo novo
  do perfil tem regra de tipo e tamanho no banco, não só no JavaScript.
- **Exclusão de conta é em duas etapas e nunca escreve em `ativo`**, que é só da pausa:
  `excluir_minha_conta()` marca `excluida_em`, a sessão não é encerrada e o job apaga depois de 60
  dias. A sessão de uma conta é a que o banco atribuiu (`0035`), nunca o `sessao_id` do navegador.
- **Sem retenção em `vagas` nem em `avaliacoes`**: apagar vaga cascateia `envios` e derruba
  dedupe, funil e exportação do titular.
- **Edge Functions**: o tratamento fica em `servidor.ts`, com as dependências por parâmetro e
  teste em `servidor_test.ts`; o `index.ts` é só a fiação. `REPOSITORIO` em `entrega_imediata.ts`
  é constante: trocar de repositório exige commit e `supabase functions deploy`.
- **Webhook do Telegram**: o `TELEGRAM_WEBHOOK_SECRET` tem o mesmo valor no `setWebhook`, nos
  secrets do Supabase e nos `.env`, e o registro leva `allowed_updates=["message","callback_query"]`.
  Depois de mexer, conferir `getWebhookInfo`. `token_vinculo` é de uso único e rotaciona no
  vínculo e no desvínculo.
- **Site**: o `name` do `wrangler.jsonc` é o do projeto no Cloudflare, senão o build falha; trocar
  o endereço exige Site URL, Redirect URLs e `URL_DA_LANDING` juntos (guia, seção 4).
- **O token do cron-job.org vence em 09/09/2027**: vencido, o diário para sem avisar ninguém.
- `domain/perfil_fixo.py` é um perfil **sintético**, usado só sem `DATABASE_URL`. O repositório é
  público: nunca colocar ali dados reais de ninguém.
