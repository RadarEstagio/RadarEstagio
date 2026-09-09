# Radar de Estágio

Busca vagas de estágio, extrai fatos com IA e calcula em Python a compatibilidade com cada
perfil. Entrega até sete recomendações explicadas no Telegram quando encontra oportunidades
compatíveis. A candidatura acontece na fonte da vaga.

O estudante preenche o perfil no site, cria a conta e confirma o e-mail, depois vincula o
Telegram. Pode editar o perfil, pausar entregas, exportar dados e solicitar exclusão da conta.
O piloto é gratuito. A disponibilidade de cada recurso depende da versão publicada;
o [guia de publicação](docs/guia-publicacao-e-piloto.md) registra evidências e pendências.

[Documentação](docs/README.md) · [Funcionalidades](docs/funcionalidades.md) ·
[Pendências](docs/plano-geral.md)

## Como funciona

1. Adzuna e Gupy fornecem anúncios; Jooble é uma fonte opcional, desligada por padrão.
2. O pipeline remove duplicatas e aplica filtros de formação, localização e outros requisitos.
3. A IA extrai fatos dos anúncios em lotes; extrações compatíveis são reaproveitadas entre perfis.
4. Python recalcula as notas, seleciona até sete vagas e prepara as explicações.
5. O Telegram entrega as recomendações e recebe feedback; o banco preserva o histórico.

O padrão local considera anúncios dos últimos **três dias**. O workflow usa **cinco dias**.
A extração compartilhada evita repetir trabalho por usuário, mas lotes, retries, anúncios
novos e mudanças na versão da extração podem exigir novas chamadas de IA. Quantidade de
vagas não equivale a quantidade de requisições.

## Início rápido local

Para trabalhar apenas no código, basta instalar as dependências e executar os testes.
Para consultar fontes e enviar mensagens, configure suas credenciais nos passos seguintes.

### 1. Instalar

É necessário Git e [uv](https://docs.astral.sh/uv/). O projeto exige Python 3.12 ou superior;
o uv pode provisionar o Python e não exige ativação manual do ambiente virtual.

```bash
git clone https://github.com/RadarEstagio/RadarEstagio.git
cd RadarEstagio
uv sync
```

### 2. Configurar o ambiente

Copie o modelo se ainda não tiver um `.env`:

```bash
cp .env.example .env
```

Edite o arquivo local. Para o primeiro teste, use um bot próprio e deixe `DATABASE_URL`
vazio: o Radar usará o [perfil sintético de exemplo](radar/domain/perfil_fixo.py), sem histórico.

| Variável | Como preencher |
|---|---|
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Credenciais da [Adzuna](https://developer.adzuna.com/signup); exigidas pela configuração atual |
| `AVALIADOR` | `gemini_api` para API direta ou `agy` para Antigravity CLI local |
| `GEMINI_API_KEY` | Chave do [Google AI Studio](https://aistudio.google.com/app/apikey), obrigatória com `gemini_api` |
| `TELEGRAM_BOT_TOKEN` | Token do bot criado pelo `@BotFather` no Telegram |
| `TELEGRAM_CHAT_ID` | Seu chat com o bot; obrigatório no modo local sem banco |
| `DATABASE_URL` | Vazio para o teste local; conexão Postgres para usar perfis persistidos |

O `.env.example` seleciona `agy`. Se usar a API direta, altere para `AVALIADOR=gemini_api`
e preencha a chave. O padrão de `Settings` e o workflow usam `gemini_api`.
Para `agy`, é necessário ter o CLI instalado e autenticado; o modelo vem de `AGY_MODELO`.
Gupy não exige chave; Jooble exige `JOOBLE_API_KEY` quando incluído em `FONTES`.

No Telegram, crie o bot com `/newbot` no `@BotFather` e envie `/start` ao seu novo bot.
Para descobrir o chat ID de um bot sem webhook, consulte `getUpdates` na API do Telegram
e procure o campo `message.chat.id`. Bots com webhook usam o fluxo de vínculo descrito
no [contrato](docs/contrato-front.md#telegram-e-entrega).

Credenciais ficam no `.env`, ignorado pelo Git. Não coloque tokens ou dados pessoais no
perfil sintético, em commits ou em mensagens do grupo.

### 3. Conferir e executar

```bash
uv run python -m radar verificar
uv run python -m radar coletar
```

O primeiro comando valida a configuração; se houver `DATABASE_URL`, também consulta o banco.
O segundo consulta fontes reais e lista anúncios, sem enviar mensagens.

Para testar o bot e depois o fluxo local completo:

```bash
uv run python -m radar testar-telegram
uv run python -m radar testar-local
```

Esses dois comandos enviam mensagens ao `TELEGRAM_CHAT_ID`. O fluxo completo também usa IA.
`testar-local` ignora banco e histórico, mesmo se houver conexão configurada, e exige chat ID.
Os botões de feedback desse modo não funcionam como no ambiente persistido: seus tokens não
são gravados no banco.

## Comandos

Execute a partir da raiz, com `uv run python -m radar` seguido do comando:

| Comando | Comportamento | Efeitos externos |
|---|---|---|
| `verificar` | Confere configuração e, com banco, conta perfis ativos vinculados | Leitura do banco quando configurado |
| `coletar` | Lista anúncios coletados após deduplicação | Consulta fontes e, com banco, perfis |
| `avaliar` | Extrai e pontua até três vagas; usa o primeiro perfil ativo disponível ou o exemplo | Consulta fontes, banco quando configurado e IA; não envia mensagens |
| `testar-telegram` | Envia “Radar OK” ao chat configurado | Envio real ao Telegram |
| `testar-local` | Executa com perfil sintético, sem banco nem histórico | Fontes, IA e Telegram |
| `rodar --perfil UUID` | Direciona o atendimento a um perfil ativo vinculado | Banco, fontes, Telegram e IA quando necessária |
| `rodar` ou nenhum comando | Executa para todos os perfis elegíveis; sem banco, usa o exemplo | Banco quando configurado, fontes, Telegram e IA quando necessária |
| `metricas` | Imprime o relatório de produto dos últimos 30 dias | Leitura do banco; exige `DATABASE_URL` |
| `julgar --dias 7 --amostra 30 --semente 1` | Pede a um segundo modelo que avalie uma amostra das entregas recentes | Leitura do banco e chamada de IA com perfil e anúncios; não grava nem envia mensagens |

`julgar` exige `DATABASE_URL` e usa `AVALIADOR` para escolher o provedor. Configure
`JUIZ_MODELO` com um modelo disponível nesse provedor: o padrão `claude-sonnet-4-6` é
destinado ao caminho AGY, não à Gemini Developer API. `--dias` e `--amostra` aceitam
inteiros positivos; a semente torna a seleção reproduzível para a mesma lista de entregas.
O julgamento é uma estimativa do modelo, não validação feita por estudantes.

Para uma verificação com conta da equipe, use `rodar --perfil UUID` com `DATABASE_URL`
e substitua `UUID` por `perfis.id`, não por `auth.users.id`.
Esse argumento limita os destinatários das recomendações, mas não transforma o pipeline em
simulação: ainda há persistência, resumo operacional e rotina de apagamento de contas cuja
carência venceu. Use ambiente de teste para validar exclusão.

Com banco, `TELEGRAM_CHAT_ID` recebe o resumo operacional e pode ficar vazio para omitir
esse resumo no Python. Sem banco, o chat ID é obrigatório.

## Frontend local

O site usa HTML, CSS e JavaScript estáticos, com Supabase Auth e acesso ao banco por RLS/RPCs.
Não há etapa de build. O perfil é preenchido antes da conta, e o banco preserva uma cópia
protegida até a confirmação, inclusive entre aparelhos; não depende de perfil no `localStorage`.

Para desenvolver com seu próprio ambiente, ajuste os campos de [web/config.js](web/config.js):

| Campo | Valor do seu ambiente |
|---|---|
| `supabaseUrl` | URL do seu projeto Supabase |
| `supabasePublishableKey` | Chave publicável ou `anon` desse mesmo projeto |
| `telegramBot` | Username, sem `@`, do bot correspondente ao token usado no servidor |
| `turnstileSiteKey` | Site key pública do widget, quando configurado |

O arquivo versionado aponta para o ambiente do Radar. Criar bot e banco próprios exige
trocar essas referências em conjunto. Senha do banco, `service_role` e secrets ficam no
servidor. Siga o [guia](docs/guia-publicacao-e-piloto.md) para migrations, webhook,
URLs autorizadas do Auth, SMTP e CAPTCHA antes de testar cadastro e vínculo.

```bash
uv run python -m http.server 8000 -d web
```

Abra `http://localhost:8000`; autenticação precisa de HTTP, não de abrir o HTML diretamente.
O [contrato frontend](docs/contrato-front.md) detalha cadastro, permissões, eventos e controles
da conta. Termos e Privacidade seguem em revisão até aprovação e sincronização da vigência.

## Testes e qualidade

A suíte Python padrão e o lint não precisam de chaves de serviços:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Os testes de integração Postgres dependem de `DATABASE_URL_TESTE` e são ignorados quando o
ambiente não está disponível. Não use o banco de produção como banco de teste.

Com [Deno](https://deno.com/) instalado, execute os testes do frontend e banco isolado:

```bash
deno test --config tests/web/deno.json --allow-read --allow-env tests/web/
```

Essa suíte usa JSDOM e PGlite; não testa layout nem entrega real de e-mails.
Os testes das Edge Functions usam a configuração do próprio diretório. A partir da raiz:

```bash
(cd supabase/functions/telegram-webhook && deno test)
(cd supabase/functions/ir && deno test)
```

Inspeção visual e jornada publicada têm roteiro próprio no guia de publicação.

## Configuração e operação

Os parâmetros e valores padrão estão em [radar/settings.py](radar/settings.py), e o modelo de
ambiente em [.env.example](.env.example). Entre eles: fontes, modelos, tamanho dos lotes,
nota mínima, limite de recomendações, pausa por falhas e carência de exclusão.
Com banco, `URL_DE_RASTREIO` habilita links pela função `ir`; vazio ou no modo sem banco,
usa links diretos para a fonte.

O [workflow](.github/workflows/radar-diario.yml) recebe disparos do cron-job.org às 07:23 de
Brasília, conforme a configuração operacional registrada. O código não usa `schedule`
nativo. O workflow configura cinco dias de anúncios, até sete recomendações e timeout de
15 minutos; isso não é promessa de tempo até receber uma mensagem.

Para um teste direcionado pelo GitHub Actions, abra **Radar diário → Run workflow** e
preencha `perfil` com o `perfis.id` da conta de teste. Deixar esse campo vazio executa o
fluxo para toda a base elegível quando há banco. Confira logs e resumo do run para saber
se houve entrega; término do job não garante existência de vaga compatível.

Banco, deploy, secrets, webhook, rastreio, cron e reversão são tratados no
[guia de publicação e piloto](docs/guia-publicacao-e-piloto.md). Para o ambiente compartilhado,
confira o projeto existente e o histórico de migrations antes de aplicar mudanças.
O [plano geral](docs/plano-geral.md) é o acompanhamento das pendências.

## Estrutura

```text
radar/
  domain/        entidades, catálogo de áreas, regras de domínio e interfaces
  collectors/    Adzuna, Gupy, Jooble opcional e composição de fontes
  filtering/     deduplicação e pré-filtro antes da IA
  matching/      extração em lotes, enriquecimento e pontuação determinística
  avaliacao/     julgamento de entregas por um segundo modelo
  notification/  formatação e envio ao Telegram
  reporting/     apresentação das métricas no terminal
  storage/       persistência Postgres, modo em memória e consultas de métricas
  pipeline.py    orquestra coleta, seleção, extração, pontuação e entrega
  __main__.py    comandos da CLI
supabase/
  migrations/    schema e permissões versionados
  functions/     webhook do Telegram e redirecionamento rastreável ir
tests/           testes Python, fixtures e testes web/banco em Deno
web/             site estático com cadastro e controles da conta
docs/            documentação de produto, arquitetura e operação
```

## Referências

- [Índice](docs/README.md): papel de cada documento e consolidação dos históricos.
- [Funcionalidades](docs/funcionalidades.md): capacidades e limites do produto.
- [Arquitetura](docs/arquitetura.md): camadas, matching e decisões técnicas.
- [Métricas](docs/metricas.md): eventos, denominadores e interpretação do relatório.
- [Vocabulário](CONTEXT.md): conceitos do produto.
- [Regras do projeto](CLAUDE.md): orientações para contribuição e manutenção.
