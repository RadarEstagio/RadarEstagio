# Desenvolvimento local

Como instalar, configurar, rodar e testar o Radar na sua máquina. Para trabalhar só no código,
basta instalar as dependências e rodar os testes; consultar fontes e enviar mensagens pede
credenciais. As regras de contribuição (commits, testes antes de cada commit, sem comentários no
código) estão no [CLAUDE.md](../CLAUDE.md).

## 1. Instalar

É preciso Git e [uv](https://docs.astral.sh/uv/). O projeto exige Python 3.12 ou superior; o uv
provisiona o Python e não exige ativar o ambiente virtual.

```bash
git clone https://github.com/RadarEstagio/RadarEstagio.git
cd RadarEstagio
uv sync
```

## 2. Configurar o ambiente

```bash
cp .env.example .env
```

Para o primeiro teste, use um bot próprio e deixe `DATABASE_URL` vazio: o Radar usa o
[perfil sintético de exemplo](../radar/domain/perfil_fixo.py), sem histórico.

| Variável | Como preencher |
|---|---|
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Credenciais da [Adzuna](https://developer.adzuna.com/signup); obrigatórias |
| `AVALIADOR` | `gemini_api` para a API direta ou `agy` para o Antigravity CLI local |
| `GEMINI_API_KEY` | Chave do [Google AI Studio](https://aistudio.google.com/app/apikey), obrigatória com `gemini_api` |
| `TELEGRAM_BOT_TOKEN` | Token do bot criado pelo `@BotFather` |
| `TELEGRAM_CHAT_ID` | Seu chat com o bot; obrigatório sem banco. Com banco, é o chat de operação que recebe o resumo |
| `DATABASE_URL` | Vazio para o teste local; conexão Postgres (Session pooler do Supabase) para usar perfis persistidos |

O `.env.example` seleciona `agy`, que exige o CLI instalado e autenticado e lê o modelo de
`AGY_MODELO`. O padrão de `Settings` e o workflow usam `gemini_api`. Jooble exige
`JOOBLE_API_KEY` quando entra em `FONTES`; a Gupy fica fora por causa dos termos. Os demais
parâmetros e padrões estão em [radar/settings.py](../radar/settings.py): o padrão local considera
anúncios dos últimos três dias, e o workflow usa cinco.

No Telegram, crie o bot com `/newbot` no `@BotFather` e envie `/start` a ele. Para descobrir o
chat ID de um bot sem webhook, consulte `getUpdates` e procure `message.chat.id`; com o webhook
ligado, o `getUpdates` para de funcionar e o vínculo segue o
[contrato](contrato-front.md#telegram-e-entrega).

Credenciais ficam no `.env`, ignorado pelo Git. Não coloque tokens ou dados pessoais no perfil
sintético, em commits ou em mensagens do grupo.

## 3. Comandos

Da raiz, `uv run python -m radar` seguido do comando:

| Comando | Comportamento | Efeitos externos |
|---|---|---|
| `verificar` | Confere a configuração e mostra o avaliador ativo; com banco, conta perfis ativos vinculados | Leitura do banco quando configurado |
| `coletar` | Lista os anúncios coletados depois da deduplicação | Fontes e, com banco, perfis |
| `avaliar` | Extrai e pontua até três vagas para o primeiro perfil ativo ou o exemplo | Fontes, banco e IA; não envia mensagens |
| `testar-telegram` | Envia "Radar OK" ao chat configurado | Telegram |
| `testar-local` | Roda com o perfil sintético, sem banco nem histórico, mesmo com banco configurado | Fontes, IA e Telegram |
| `rodar` ou nenhum comando | Atende todos os perfis elegíveis; sem banco, usa o exemplo | Banco, fontes, Telegram e IA quando necessária |
| `rodar --perfil UUID` | Entrega imediata: atende o perfil, se a primeira entrega dele ainda não foi atendida, e todo perfil que ficou pendente | Banco, fontes, Telegram e IA quando necessária |
| `metricas` | Relatório de produto dos últimos 30 dias ([métricas](metricas.md)) | Leitura do banco |
| `julgar --dias 7 --amostra 30 --semente 1 [--gabarito arquivo.json]` | Um segundo modelo julga às cegas uma amostra das entregas recentes | Leitura do banco e IA; não grava nem envia |
| `gabarito --dias 7 --amostra 20 --saida gabarito.json` | Exporta entregas para as pessoas marcarem `relevante` | Leitura do banco e escrita no arquivo |
| `descartes --amostra 30 --saida descartes.json` | Exporta uma amostra do que o pré-filtro cortou, com o motivo | Fontes e banco; escrita no arquivo |

Cuidados:

- **`testar-local`** gera os botões de feedback, mas os tokens não vão para o banco, então o
  webhook não os acha. Teste feedback com envio do fluxo com banco.
- **`rodar --perfil`** recebe `perfis.id`, não `auth.users.id`. Perfil cuja primeira entrega já
  foi atendida não recebe nada: zere `entrega_imediata_atendida_em` antes do teste. A execução
  também atende quem ficou pendente e não é simulação: grava, manda o resumo e roda o apagamento
  das contas cuja carência venceu. Use ambiente de teste para validar exclusão.
- **`julgar`** usa `AVALIADOR` para escolher o provedor, e `JUIZ_MODELO` precisa existir nele: o
  padrão `claude-sonnet-4-6` é para o caminho `agy`, não para a Gemini Developer API. Sem nenhuma
  entrega julgada, imprime o último erro e sai com código 1. Com `--gabarito`, julga só as
  entregas rotuladas e mede a concordância com as pessoas; o juiz só vale como evidência acima de
  75% de concordância.
- **`gabarito` e `descartes`** gravam vagas reais e `perfil_id`: guarde os arquivos fora do Git
  (`gabaritos/`, `gabarito-*.json` e `descartes-*.json` já estão no `.gitignore`) e não
  sobrescreva outro gabarito.
- **Evite rodar `avaliar` e `rodar` repetidamente sem necessidade**: cada execução gasta cota da
  Adzuna e requisições pagas do Gemini.

## 4. Frontend local

O site é HTML, CSS e JavaScript estáticos, sem etapa de build, com Supabase Auth e acesso ao banco
por RLS e RPCs. Para usar seu próprio ambiente, ajuste [web/config.js](../web/config.js):

| Campo | Valor do seu ambiente |
|---|---|
| `supabaseUrl` | URL do seu projeto Supabase |
| `supabasePublishableKey` | Chave publicável ou `anon` desse projeto |
| `telegramBot` | Username, sem `@`, do bot correspondente ao token usado no servidor |
| `turnstileSiteKey` | Site key pública do widget, quando configurado |

O arquivo versionado aponta para o ambiente do Radar; trocar banco e bot exige mudar essas
referências juntas. Senha do banco, `service_role` e secrets ficam no servidor. Migrations,
webhook, URLs do Auth, SMTP e CAPTCHA estão no [guia de publicação](guia-publicacao-e-piloto.md).

```bash
uv run python -m http.server 8000 -d web
```

Abra `http://localhost:8000`; autenticação precisa de HTTP, não do HTML aberto do disco. Sessões
de páginas locais saem do relatório de métricas. O [contrato frontend](contrato-front.md) detalha
cadastro, permissões, eventos e controles da conta, e o `CLAUDE.md` lista as regras que valem ao
mexer no `app.js`.

## 5. Testes e qualidade

Antes de cada commit, as quatro checagens, em comandos separados (pipe engole o código de saída):

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
deno test --config tests/web/deno.json --allow-read --allow-env tests/web/
```

A última precisa do [Deno](https://deno.com/) e roda o site com JSDOM e o banco com PGlite, com
todas as migrations; não testa layout nem entrega real de e-mail. Cada Edge Function tem a própria
suíte e o `deno check`:

```bash
(cd supabase/functions/telegram-webhook && deno test && deno check index.ts)
(cd supabase/functions/ir && deno test && deno check index.ts)
```

Os testes de integração Postgres dependem de `DATABASE_URL_TESTE` e são ignorados sem ele; não use
o banco de produção como banco de teste. Tudo, menos esses, roda no GitHub Actions em todo push
para a `main` e em todo pull request ([Testes](../.github/workflows/testes.yml)).

## 6. Scripts

Ficam em `scripts/` e só rodam à mão, quando a fonte muda:

| Script | Quando rodar |
|---|---|
| `uv run python scripts/gerar_cidades.py` | O IBGE criou município: regera `web/assets/cidades.json` e `radar/domain/regioes_imediatas.json` a partir das APIs do IBGE |
| `uv run --with pillow python scripts/gerar_icones_das_areas.py <pasta>` | Ilustrações novas das áreas: recebe `<área>.jpg\|png\|webp`, tira o fundo branco e grava os WebP em `web/assets/areas/`; as imagens originais não são versionadas |

## 7. Operação

O [workflow diário](../.github/workflows/radar-diario.yml) só tem `workflow_dispatch`: quem
dispara às 07:23 de Brasília é o cron-job.org, e a primeira busca de quem vincula o Telegram vem
da `telegram-webhook`. Para um teste direcionado, abra **Radar diário → Run workflow** e preencha
`perfil` com o `perfis.id` da conta de teste; vazio, atende toda a base elegível. Término verde
não garante vaga compatível: confira o resumo no chat de operação. Banco, deploy, secrets,
webhook, rastreio, cron e reversão estão no [guia de publicação](guia-publicacao-e-piloto.md).
