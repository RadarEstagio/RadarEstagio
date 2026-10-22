# Radar de Estágio

Agente que garimpa vagas de estágio todos os dias e manda pelo Telegram só as que combinam com o
perfil de cada estudante, com nota de 0 a 100 e o motivo de cada uma. A IA lê o anúncio e
extrai os fatos; a nota é calculada em Python, por regras que dão sempre o mesmo resultado para a
mesma vaga e o mesmo perfil. A candidatura acontece na fonte da vaga.

Em produção desde 28/08/2026 e gratuito durante o piloto: **[radarestagio.com](https://radarestagio.com)**.
Projeto da disciplina Métodos e Aplicações de IA (IBM3116), de Igor Costa, Ian Dias e Miguel
Esteves.

## Por onde seguir

- **[PIT](docs/pit/pit-do-grupo.md)**: o problema, a solução, os números medidos, os riscos e a
  viabilidade, em uma leitura. A [apresentação](docs/pit/apresentacao.html) acompanha.
- **[Funcionalidades](docs/funcionalidades.md)**: o que o produto faz hoje e seus limites.
- **[Arquitetura](docs/arquitetura.md)**: como o código é organizado e por quê.
- **[Desenvolvimento local](docs/desenvolvimento.md)**: instalar, configurar, rodar e testar.
- **[Plano geral](docs/plano-geral.md)**: o que falta e o que está decidido.
- **[Sumário da documentação](docs/sumario-da-documentacao.md)**: o mapa dos documentos, os números
  e o que está aberto, para não se perder.
- **[Índice da documentação](docs/README.md)**: todos os documentos e o dono de cada assunto.

## Como funciona

```text
Adzuna → deduplicação → pré-filtro → extração por IA (uma vez por vaga, para todos)
       → nota em Python por perfil → até 7 vagas no Telegram → feedback e histórico
```

O estudante preenche o perfil no site, cria a conta no último passo e vincula o Telegram; a
primeira lista chega em minutos e as seguintes todo dia às 07:23 de Brasília. O site e o motor não
conversam por API: o contrato entre eles é o schema do banco.

| Peça | Tecnologia |
|---|---|
| Motor | Python 3.12, executado pelo GitHub Actions e disparado pelo cron-job.org |
| Fonte de vagas | API oficial da Adzuna |
| Extração | Google Gemini Flash, com saída validada por schema |
| Banco e conta | Supabase (PostgreSQL com RLS, Auth e Edge Functions em Deno) |
| Site | HTML, CSS e JavaScript sem build, no Cloudflare Workers |
| Entrega | Bot do Telegram |

## Estrutura

```text
.
├── radar/          motor em Python: coleta, filtro, extração, nota e entrega
├── web/            site estático: landing, cadastro e conta
├── supabase/       migrations do banco e Edge Functions
├── tests/          testes Python, fixtures e testes do site e do banco em Deno
├── scripts/        geradores de dados do site e o vigia do diário
├── docs/           documentação, PIT e auditorias
├── .github/        CI, diário, vigia e Dependabot
├── CLAUDE.md       regras de contribuição e fatos operacionais
├── CONTEXT.md      vocabulário do produto
├── pyproject.toml  dependências Python (uv)
└── wrangler.jsonc  publicação do site no Cloudflare
```

### `radar/`

O `domain/` é o centro e não depende de nada; os outros módulos dependem das interfaces dele.

```text
radar/
├── __main__.py         CLI: monta as peças reais e chama o pipeline
├── pipeline.py         orquestra coleta → dedupe → pré-filtro → extração → nota → entrega
├── entrega_imediata.py primeira entrega de quem acabou de vincular o Telegram
├── cota.py             limites de requisição da Adzuna
├── settings.py         variáveis de ambiente
├── domain/             entidades, interfaces, catálogo de áreas (areas.py), regiões do IBGE e público da vaga
├── collectors/         Adzuna, Jooble e Gupy (desligadas) e o composto que soma as fontes
├── filtering/          deduplicação e pré-filtro antes da IA
├── matching/           extração em lotes (Gemini ou agy), enriquecimento, compatibilidade e nota
├── notification/       formatação e envio ao Telegram
├── storage/            Postgres, modo em memória e as consultas SQL de métricas
├── reporting/          relatórios de métricas e do juiz no terminal
└── avaliacao/          juiz automático, gabarito e amostra de descartes
```

### `web/`

```text
web/
├── index.html                landing, cadastro e conta
├── termos.html, privacidade.html
├── config.js                 URL e chave pública do Supabase, bot e site key do Turnstile
├── _headers                  cabeçalhos de segurança servidos pelo Cloudflare
└── assets/
    ├── app.js, styles.css
    ├── areas.json            gerado por scripts/gerar_areas.py
    ├── cidades.json          gerado por scripts/gerar_cidades.py
    ├── areas/                ilustrações das 12 áreas
    └── adzuna-logo.png       atribuição exigida pela Adzuna
```

### `supabase/`

```text
supabase/
├── config.toml
├── migrations/               schema, permissões e funções do banco, numerados (0001 a 0035)
└── functions/
    ├── telegram-webhook/     vínculo, feedback, mensagem livre e disparo da primeira entrega
    ├── ir/                   link rastreável que registra a abertura e redireciona
    └── _shared/              quem pode interagir: conta ativa, não excluída e chat vinculado
```

Em cada função, `servidor.ts` trata a requisição e tem teste; o `index.ts` só liga as peças.

### `docs/`

```text
docs/
├── README.md                    índice e dono de cada assunto
├── sumario-da-documentacao.md   mapa dos documentos, números e o que está aberto
├── funcionalidades.md           o que o produto faz
├── plano-geral.md               pendências e decisões
├── arquitetura.md               camadas e decisões técnicas
├── decisoes-do-motor.md         por que cada regra de coleta, filtro, extração e nota existe
├── decisoes-do-banco.md         por que o schema, as migrations e as funções são assim
├── contrato-front.md            contrato entre o site e o banco
├── metricas.md                  eventos e cálculo do relatório
├── desenvolvimento.md           desenvolvimento local
├── guia-publicacao-e-piloto.md  configuração dos serviços e evidências
├── frentes-externas.md          cobertura, aquisição, custos e oferta
├── termos-de-uso.md, politica-de-privacidade.md
├── esclarecimento-da-faxina.md  registro da reorganização de 16/10/2026
├── auditorias/                  revisões datadas
└── pit/                         PIT, apresentação e telas
```

### `scripts/`

```text
scripts/
├── gerar_areas.py            web/assets/areas.json a partir de radar/domain/areas.py
├── gerar_cidades.py          municípios e regiões imediatas do IBGE para o site e o motor
├── gerar_icones_das_areas.py ilustrações das áreas em WebP para a landing
└── vigiar_radar_diario.py    confere se o diário do dia terminou bem, rodado pelo vigia
```

## Início rápido

```bash
uv sync
uv run pytest -q
```

Para rodar com fontes e Telegram de verdade, siga o [guia de desenvolvimento](docs/desenvolvimento.md).
