# Arquitetura do Radar de Estágio

Como o sistema é organizado, por que foi organizado assim e quais decisões foram tomadas no
caminho. O histórico das mudanças está nos commits e nas PRs do repositório.

## Em uma frase

Um script Python executado no GitHub Actions, diariamente ou após vínculo, coleta vagas,
extrai fatos com IA e pontua por perfil em Python. O frontend usa Supabase Auth e banco;
Edge Functions recebem vínculo/feedback e redirecionam links de vagas. Não há servidor Python permanente.

## O fluxo

```text
fontes → dedupe/pré-filtro → enriquecimento → extração compartilhada
  → trava e histórico por perfil → pontuação → revalidação → Telegram → registro de envio
```

A extração é reaproveitada entre usuários; pontuação e seleção são individuais. A trava
serializa atendimento do mesmo perfil. Banco e envio ao Telegram não são transação única.
O [catálogo](funcionalidades.md) detalha recursos e limites; o [contrato](contrato-front.md)
descreve o cadastro e as RPCs atuais.

## As camadas

```
radar/
  domain/        o centro: entidades e contratos. Não depende de nada.
  collectors/    de onde vêm as vagas (um por fonte + composto) → cumpre ColetorDeVagas
  filtering/     dedupe e regras baratas antes da IA
  matching/      IA: prompt, cliente, lotes    → cumpre ExtratorDeVagas
                 pontuação determinística      → compatibilidade.py, avaliacoes.py
  notification/  formatar e enviar a mensagem  → cumpre Notificador
  storage/       usuários, notas e envios      → cumpre Repositorio (Postgres ou memória)
  pipeline.py    orquestra; sem lógica própria
  __main__.py    linha de comando; monta as peças reais
  settings.py    variáveis de ambiente
```

### `domain/areas.py` — o catálogo de áreas

As 12 áreas vivem em um módulo só, e dele derivam o enum `AreaDeInteresse`, a migration que
restringe `perfis.areas_de_interesse` e o `web/assets/areas.json` que o cadastro consome. Cada
área carrega os cursos que caem nela, os padrões que reconhecem uma vaga sua, os termos de busca
usados na coleta e as subáreas oferecidas no cadastro. O pré-filtro pergunta "essa vaga é da área
do curso desta pessoa?" e a pontuação compara a área extraída da vaga com a do curso.

Desde a revisão de 08/09, menção ao curso do perfil ou abertura a qualquer formação na
descrição impede o veto antecipado por título: a extração e a compatibilidade verificam os
requisitos depois. Nomes de cursos são comparados inteiros, com aliases explícitos e remoção
de prefixos de formação. Um nome desconhecido não herda a área de um trecho do nome.
Quando algum perfil não tem área reconhecida, Adzuna e Jooble fazem busca geral de estágio,
respeitando os limites de paginação existentes; isso não garante cobertura integral.

As notas são recalculadas em Python a cada execução, usando extrações compartilhadas.
Avaliações armazenadas permanecem como registro, mas não alimentam a seleção; isso evita
notas antigas após mudanças de regras ou feedback. O histórico de envios continua impedindo
repetições. Office e idiomas passam a contar na cobertura para cursos fora de computação;
o comportamento anterior de computação permanece.

### `domain/` — o que o sistema *é*

Entidades como `Vaga`, `Perfil`, `Usuario`, `ExtracaoDaVaga`, `Recomendacao` e `ResultadoMatch`, além dos contratos
(`ColetorDeVagas`, `ExtratorDeVagas`, `Notificador`, `RepositorioDeUsuarios`,
`RepositorioDeAvaliacoes`). Nada aqui sabe que Adzuna, Gemini ou Telegram existem.

A regra de dependência é uma só: **tudo aponta para o domínio; o domínio não aponta para
nada.** `collectors/` importa de `domain/`; `domain/` nunca importa de `collectors/`.

### Por que contratos (`Protocol`)?

O pipeline não pede "um `ColetorAdzuna`", pede "qualquer coisa com um método
`coletar() -> list[Vaga]`". Consequências práticas:

- **Trocar fonte** (Adzuna → Gupy): nova classe em `collectors/`, resto intocado.
- **Trocar IA** (Gemini → Claude): nova classe em `matching/`, resto intocado.
- **Testar o pipeline**: passa um coletor falso que devolve 3 vagas fixas. Zero rede,
  zero cota.

É isso que a proposta chama de "arquitetura limpa". Na prática significa: **a parte que
muda (infraestrutura) fica na borda; a parte que não muda (domínio) fica no centro.**

### `pipeline.py` — o maestro

```python
def executar(coletor, extrator, notificador, repositorio, parametros, agora):
    unicas = remover_duplicatas(coletor.coletar())
    candidatas = candidatas_de_algum_perfil(unicas, usuarios)
    extracoes = obter_extracoes(extrator, repositorio, candidatas)  # uma vez, para todos
    for usuario in usuarios:  # por usuário, sem IA
        resultados = pontuar_vagas(filtrar(unicas, usuario.perfil), extracoes, usuario.perfil)
        notificador.enviar(usuario.chat_id, formatar_mensagem(ranquear(resultados), agora))
```

Esse é o esqueleto, não o código: faltam a trava por perfil, a releitura do histórico, as
regras objetivas e a revalidação do destinatário antes de enviar. O que o esqueleto mostra é
a forma: o pipeline **recebe** as peças prontas (injeção de dependência) em vez de criá-las.
Quem cria as peças reais é o `__main__.py`; quem cria as falsas são os testes.

Vaga é identificada pelo par `(fonte, id_externo)` em todo dicionário do fluxo, porque o
banco distingue as duas colunas e duas fontes podem repetir o número. Com a chave só no
`id_externo`, a candidata de uma fonte apagava a da outra e o mesmo anúncio saía duas vezes
na mesma mensagem.

## Decisões de arquitetura

### 1. Sem banco de dados na Fase 1

O GitHub Actions cria uma máquina nova a cada execução e a destrói no final. Não há onde
guardar um arquivo entre um dia e outro. Então:

- **SQLite foi descartado** — é um arquivo em disco, não sobreviveria.
- Versionar o `.db` no repositório: repositório público exporia `chat_id` dos usuários,
  e o job precisaria de permissão de escrita.
- `actions/cache`: não é durável, sofre evicção.

Na Fase 1 o filtro por data (`DIAS_RECENTES`) faz o papel de dedupe. Na Fase 2 entrou
**PostgreSQL no Supabase** — que a proposta já previa para o painel web, então adotar
agora evita migrar duas vezes. MySQL foi considerado e não oferece vantagem (JSON pior,
opções gratuitas piores). Ver a decisão 10.

### 2. Sem framework web

É um script disparado por cron, não um serviço HTTP. Flask/FastAPI seriam peso morto.
`httpx` basta para as chamadas que existem: Adzuna, Gupy, Jooble, o enriquecimento da
descrição e o Telegram.

### 3. Extração por vaga, pontuação por perfil

A IA extrai **fatos da vaga**; o Python **compara** esses fatos com cada perfil. A separação
existe por custo: o prompt não contém perfil algum, então uma vaga é extraída **uma vez** e a
extração serve todos os usuários. O custo de IA passou de O(usuários × vagas) para O(vagas), e
o vigésimo usuário não custa nada.

- **Por que Gemini**: camada gratuita, suficiente para validar o produto.
- **Saída estruturada** (`response_schema` + Pydantic): a IA devolve JSON no formato
  `{id_vaga, area_da_vaga, areas_da_vaga, modalidade, cursos_aceitos, aceita_qualquer_curso,
  periodo_minimo, experiencia_minima_anos, experiencia_desejavel, habilidades_obrigatorias,
  habilidades_principais, habilidades_desejaveis, alerta_pegadinha}`. Tudo é fato do anúncio;
  nada depende de candidato. O `id_vaga` é `fonte:id_externo`, porque duas fontes podem usar
  o mesmo número e o banco distingue as duas vagas.
- **A comparação é determinística** (`matching/compatibilidade.py`): `cursos_aceitos` vira
  compatível/parcial/incompatível contra o catálogo de cursos de `domain/areas.py`;
  `periodo_minimo` e `experiencia_minima_anos` viram o nível de período; os pontos a favor e
  contra são montados da comparação, não escritos pela IA. Mesmos dados, mesma nota, sempre.
- **Pontuação no Python** (`matching/avaliacoes.py`): habilidades valem 45 pontos, curso 10,
  área 10, período/experiência 15, logística 10 e áreas de interesse 10. A cobertura das
  habilidades usa nomes normalizados e famílias explícitas de requisitos genéricos:
  SQL pode atender “banco de dados”, mas Java não atende JavaScript. Quando nem o perfil nem a
  vaga são de computação, um requisito também é atendido por palavras inteiras ("Contratos"
  atende "revisão de contratos"). Requisito composto ("Excel e Power BI") exige todas as partes,
  "ou" é alternativa, e requisito repetido só conta se todas as versões forem atendidas. O nível
  exigido é comparado com o maior nível que o perfil declara entre nome, família e palavras.
  Desde 09/09, a cobertura neutra sem stack é 0,25; Office, idiomas e soft skills ficam
  fora da cobertura apenas para computação. Desejáveis ausentes aparecem como
  “Diferenciais que a vaga cita”, separados dos requisitos a conferir, sem virar veto.
- **A extração fica em `vagas.extracao`** (JSONB). Reexecução no mesmo dia, usuário novo
  entrando ou coorte crescendo não gastam cota de novo.
- **Temperatura 0**: os mesmos dados tendem a produzir a mesma extração.
- **Trocar de modelo** é uma variável de ambiente (`GEMINI_MODELO`). Trocar de provedor é
  um adapter novo em `matching/`.
- **Dois adapters** implementam a mesma interface: `ExtratorGemini`, pela Developer API,
  e `ExtratorAgy`, pelo Antigravity CLI local. `AVALIADOR=gemini_api|agy` escolhe qual usar.
- O adapter AGY roda em diretório temporário, com sandbox, timeout e JSON Schema; o fluxo do
  domínio recebe as mesmas `ExtracaoDaVaga` em ambos os casos.

### 4. Pré-filtro por regras antes da IA

Regras baratas (regex) cortam o óbvio — "Desenvolvedor Sênior", "5 anos de experiência" —
antes de gastar cota e tempo de IA. A IA fica para o julgamento fino.

Regex não lê negação sozinho: "não exigimos 2 anos de experiência" descartava a vaga pela
menção. A negação passou a valer dentro da mesma frase, e só dentro dela, para que um "não"
da frase anterior não libere a exigência seguinte.

Cortar antes da IA economiza cota e também esconde erro: quem só julga a vaga entregue nunca
vê a boa vaga que sumiu aqui. `python -m radar descartes` grava uma amostra do que o
pré-filtro cortou, com o motivo de cada corte, no mesmo formato do gabarito. A amostra cobre
um motivo diferente por vez antes de repetir, senão o motivo mais frequente tomaria a lista.

### 5. Extração em lotes com tolerância a falhas

O problema: a cota do Gemini varia por modelo e plano. Uma chamada por vaga multiplica custo,
latência e risco de limite, além de poder interromper uma execução com volume alto.

A solução é em duas camadas, separadas de propósito:

```
ExtratorEmLotes  (matching/lotes.py)   — sabe dividir, tentar de novo, desistir
      │  usa
      ▼
ExtratorGemini/ExtratorAgy             — sabem falar com seu mecanismo. Só isso.
```

O adapter selecionado recebe uma lista de vagas, faz **uma** chamada, devolve os resultados que
conseguiu casar por id. Não sabe o que é "tentar de novo".

`ExtratorEmLotes` embrulha qualquer extrator e aplica a estratégia:

| Situação | O que faz |
|---|---|
| 14 vagas, lote de 10 | 2 chamadas |
| lote de 10 falha (JSON quebrado, erro 500) | divide em 5 + 5, tenta cada; repete até isolar a vaga com problema |
| modelo esqueceu de responder 1 vaga | extrai só ela |
| esqueceu mesmo sozinha | ignora e registra |
| cota excedida (HTTP 429) | espera o "retry in Ns" e repete o mesmo lote; acima de 120 s desiste e envia o que já tem |
| avaliador fora do ar (502, 503, 504) | espera e repete o **mesmo** lote, sem dividir |

Por que separar: a estratégia de resiliência não tem nada a ver com o mecanismo de IA.
`ExtratorEmLotes` embrulha os dois adapters sem conhecer Gemini API ou AGY.

### 6. Formatar ≠ enviar

`formatador.py` é uma função pura: lista de resultados entra, texto sai. Testa sem rede.
`telegram.py` só faz o POST. O formato da mensagem já mudou três vezes; o envio, nenhuma.

### 7. Erros com nome

Cada camada tem sua exceção: `ErroDeColeta`, `ErroDeAvaliacao` (e a filha
`CotaDeAvaliacaoExcedida`), `ErroDeNotificacao`. Todas com mensagem limpa e **sem vazar
chave de API** no traceback (`raise ... from None`). O `__main__` captura as três e sai
com código 1 — o GitHub Actions fica vermelho e mostra o motivo em uma linha.

### 8. Configuração só por variável de ambiente

`Settings` (pydantic-settings) lê do `.env` local ou do ambiente do CI — o código não sabe a
diferença. Adzuna e Telegram são obrigatórios; `GEMINI_API_KEY` é condicional ao adapter.
O restante tem padrão. O `.env`
nunca é commitado; no GitHub as mesmas variáveis vêm dos secrets.

### 9. Várias fontes somadas, com dedupe sem banco

A Adzuna devolve descrição truncada e raramente informa modalidade; a Gupy tem API interna
(sem chave) com `workplaceType` estruturado e descrição completa. As duas são somadas por
`ColetorComposto` (`collectors/composto.py`), que cumpre `ColetorDeVagas` como qualquer
coletor: o pipeline não sabe quantas fontes existem. Uma fonte fora do ar vira `warning`; só
falha se nenhuma responder. `FONTES` liga e desliga fontes sem mexer no código.

A mesma vaga pode chegar pelas duas. `filtering/duplicatas.py` agrupa por título + empresa
normalizados e fica com a versão **mais completa**: quem informa modalidade ganha; empate →
descrição mais longa. Não precisa de IA para isso — é a mesma vaga, a nota seria a mesma; o
que muda é a informação que chega ao extrator.

`Vaga.modalidade` é opcional: a Gupy preenche, a Adzuna não. O pré-filtro decide pelo campo
quando existe e só recorre a regex no texto quando a fonte não informa.

A chave de duplicata inclui a cidade. Sem ela, duas vagas presenciais da mesma empresa com o
mesmo título em cidades diferentes viravam uma só, e essa etapa roda antes do filtro por
perfil: quem era de Recife perdia a vaga de Recife para a de São Paulo, sem erro na execução.
A segunda etapa, a de republicações, continua comparando o início da descrição dentro da
mesma cidade.

Para decidir se a vaga é alcançável, a cidade da vaga e a do perfil passam por
`domain/regioes.py`, que devolve mesma cidade, mesma região imediata do IBGE ou distante. Mesma
região conta como a cidade no pré-filtro e na trava de modalidade, e vale metade na logística.
O mapa vem de `domain/regioes_imediatas.json`, gerado do IBGE por `scripts/gerar_cidades.py`; o
estado da vaga é lido nos formatos das fontes e, sem estado, o nome decide quando só existe num
estado.

### 10. Banco atrás de interface, com objeto nulo

O `pipeline.py` fala com um `Repositorio` (`domain/ports.py`) e nunca com o Postgres. Há
duas implementações em `storage/`: `RepositorioPostgres` (SQL puro com `psycopg`, sem ORM)
e `RepositorioEmMemoria`, que devolve o perfil fixo e não guarda nada. `abrir_repositorio`
escolhe pela presença de `DATABASE_URL`. O pipeline tem um único caminho: não existe
`if banco` em lugar nenhum fora da factory.

Regras para não afetar quem já usa:

- **Ler usuários é a única falha fatal.** Erro ao enviar para um usuário ou ao gravar depois
  do envio vira `warning` e o job segue para o próximo. Enviar é o produto; gravar é otimização.
- **Avaliação gravada antes do envio.** `guardar_avaliacoes` roda antes de chamar o Telegram e
  `registrar_envios` roda depois: uma falha de entrega não descarta o que a IA já custou, e o
  dia seguinte não reavalia as mesmas vagas.
- **Todo dia tem mensagem, mas nenhuma é vazia.** Sem vaga aprovada, o estudante recebe que
  nada compatível apareceu e que a busca volta amanhã: silêncio total pareceria serviço morto.
  A mensagem antiga só dizia "nenhuma vaga compatível hoje"; a de agora diz o que acontece a
  seguir. Depois de `DIAS_DE_SILENCIO_ATE_AVISAR` dias sem nenhuma recomendação, e no máximo
  uma vez por período, a mesma mensagem ganha um parágrafo sugerindo ampliar cidade ou
  modalidade — parágrafo, não segunda mensagem, para não notificar duas vezes no mesmo dia.
- **Falhas seguidas pausam o perfil.** Cada erro de envio incrementa `perfis.falhas_de_envio`;
  ao atingir `FALHAS_DE_ENVIO_ATE_PAUSAR` o perfil sai de `ativo`, emitindo `entregas_pausadas`.
  Um envio bem-sucedido zera a contagem. Sem isso, quem bloqueia o bot vira custo diário eterno.
- **Transação por operação**: as avaliações de um usuário entram juntas ou não entram, e o mesmo
  vale para os envios e a ativação. A conexão é aberta em `autocommit`, então cada bloco
  `transaction()` confirma sozinho ao terminar. Sem isso, a primeira consulta abriria uma
  transação implícita, os blocos virariam savepoints dentro dela e nada ficaria visível para
  outra conexão até o processo fechar: a mensagem chegaria ao estudante antes de o token do
  envio existir para o webhook, e a trava do perfil seria liberada antes da confirmação.
- **Schema versionado** em `supabase/migrations/`, aplicado com `supabase db push`. É o
  contrato com o site: ninguém altera tabela pelo painel.
- **RLS** em todas as tabelas. `perfis` e `eventos_produto` têm policy: cada usuário lê e
  edita a própria linha, e `eventos_produto` aceita apenas os eventos web permitidos para a
  sessão ou usuário atual. As demais ficam sem policy, o que já bloqueia o cliente. O job usa a string de conexão do Postgres, que
  ignora RLS, e ela só existe no `.env` e nos secrets.
- **Conexão pelo Session pooler** do Supabase: o runner do Actions só tem IPv4.
- **Toda execução se reporta.** Ao terminar, o job manda ao chat de operação
  (`TELEGRAM_CHAT_ID`) quantos usuários estavam ativos, quantos receberam recomendação, quantas
  vagas saíram e quantas requisições o extrator consumiu. Um erro conhecido vira aviso de falha
  antes de derrubar o processo; um kill por timeout, que o Python não consegue reportar, é
  coberto pelo passo `if: failure()` do workflow, que manda o link do run. O disparo é externo
  (cron-job.org): sem esse retorno, dois dias parados passam despercebidos, como já aconteceu.

### 11. Eventos de produto com fonte autoritativa

`eventos_produto` concentra o funil em um catálogo fechado. A landing registra visita, CTA,
etapas e abertura do Telegram com um UUID de sessão sem dados pessoais. Gatilhos do Postgres
registram conta criada, confirmação de e-mail, perfil salvo, Telegram vinculado, primeira
recomendação e pausa, porque esses marcos não devem depender do navegador permanecer aberto.

A sessão anônima é ligada ao usuário por um evento autenticado de `perfil_salvo`. Consultas usam
a primeira ocorrência de cada nome, pois o gatilho autoritativo e o navegador podem registrar o
mesmo marco. Os eventos de clique, utilidade e candidatura permanecem reservados até existirem
interações reais no Telegram; o contrato não fabrica comportamento futuro.

## Como cada ferramenta se encaixa

| Ferramenta | Papel | Por que essa |
|---|---|---|
| `uv` | Python + dependências + lock | rápido, instala o Python sozinho, `uv.lock` garante versões iguais em toda máquina |
| `ruff` | lint + formatação | uma ferramenta só, rápida, sem discussão de estilo |
| `pytest` + `pytest-httpx` | testes; simula HTTP | testar coletor e notificador sem rede |
| `pydantic` | entidades + validação do JSON da IA | fatores inválidos não entram no cálculo da nota |
| `pydantic-settings` | `.env` → objeto tipado | erro claro quando falta variável |
| `httpx` | Adzuna e Telegram | simples, moderno, fácil de simular |
| `google-genai` | Gemini | SDK oficial com saída estruturada |
| GitHub Actions | executa o workflow manual | repositório público, sem servidor dedicado |
| cron-job.org | dispara o workflow diariamente | substitui o `schedule` nativo que falhou em testes |

## Regras do repositório

- Sem comentários no código; nomes autoexplicativos.
- Commits atômicos em [Conventional Commits](https://www.conventionalcommits.org), em
  português: `feat(matching): adiciona extrator em lotes`.
- `.env` e segredos nunca commitados.
- Toda funcionalidade com teste; a suíte roda sem chave e sem internet.

## Custo de IA por usuário

A extração compartilhada é o que torna a coorte do piloto viável na cota gratuita. Antes, cada
perfil reavaliava as mesmas vagas: 20 estudantes no primeiro dia pediam cerca de 120 requisições
contra um limite de 20 por minuto, e o job morria no timeout antes de atender a fila inteira —
sempre pelos usuários mais recentes, porque a fila é ordenada por `criado_em`.

Agora o número de requisições depende só de quantas vagas novas passaram no pré-filtro de algum
perfil. O resumo de cada execução (decisão 10) informa esse número, e o teste
`test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas` impede que a propriedade se perca.

## Estado e evolução

Banco, múltiplos usuários, cadastro, controle da conta, feedback, métricas e entrega após
vínculo estão implementados. O cadastro é validado e criado pelo banco após confirmação;
a interface edita campos permitidos e chama RPCs para operações protegidas. As Edge Functions
tratam vínculo, feedback e navegação. Jooble existe como fonte opcional, desligada por padrão.

O [catálogo](funcionalidades.md) detalha as capacidades. Publicação e validação estão no
[guia](guia-publicacao-e-piloto.md), e as pendências no [plano geral](plano-geral.md).
Novos adapters devem cumprir os contratos do domínio; medir cobertura, custo e comportamento
antes de ativá-los no piloto.

## O contrato entre a extração e a nota

A IA e o pontuador são etapas separadas, e a fronteira entre elas já falhou em silêncio: o
pontuador distingue proficiência ("Excel básico" não atende "Excel avançado") enquanto o
prompt mandava apagar o nível da habilidade. Cada etapa passava nos próprios testes, porque
o teste do pontuador montava a extração à mão, com o nível que o extrator na prática não
entregava. Um requisito avançado chegava como "Excel" e era dado por atendido.

O prompt agora manda preservar o nível quando o anúncio o declara, e
`tests/test_contrato_extracao_pontuacao.py` cobre o par: os exemplos de nível citados no
prompt precisam ser reconhecidos pelo pontuador, e apagar o nível precisa mudar a nota.
Teste de etapa isolada não cobre esse tipo de falha; contrato entre etapas, sim.

Mudar o prompt muda `VERSAO_DA_EXTRACAO` e invalida o cache: a execução seguinte reextrai as
candidatas. É o preço de corrigir o formato do que está guardado.

## Viés conhecido do ranking

### Correções e limites preservados da auditoria de 08/09

Síntese consolidada em 09/09 a partir da auditoria e da revisão do PR #22. Os cenários
A01–A06 foram registrados como corrigidos localmente; isso não mede sua frequência real
nem certifica produção. A01 foi fechado em `c2d6f96`; a lacuna final de A04 em `40ed28c`.

| Caso | Regra preservada | Referência de regressão |
|---|---|---|
| A01 — lista mista de cursos | “Enfermagem, áreas afins” não libera Direito; termos genéricos não anulam curso específico e, sozinhos, não comprovam elegibilidade | `tests/test_compatibilidade.py` |
| A02 — erro em item de lote | Acumular extrações válidas e repetir só pendências; falha temporária não descarta sucessos anteriores | `tests/test_lotes.py` |
| A03 — extração parcial | Candidata sem extração impede concluir que não há vaga compatível; aprovadas disponíveis podem ser entregues | `tests/test_pipeline.py` |
| A04 — proficiência | Básico ou nível desconhecido não comprova avançado; requisito sem nível aceita habilidade conhecida, preservando aliases e exceção de computação | `tests/test_avaliacoes.py`, `tests/test_formatador.py` |
| A05 — troca de sessão | Limpar interesses no logout/troca de conta; preservar restauração intencional na edição da mesma conta | `tests/web/cadastro_test.ts` |
| A06 — histórico antes da IA | Extrair apenas candidatas ainda úteis a algum perfil; manter trava e releitura antes de enviar. Falha de leitura não autoriza envio | `tests/test_pipeline.py` |

Na revisão do PR #22, a agregação por área foi colocada em `radar/domain/metricas.py`:
classificar curso é regra de domínio e `storage` não deve importar `reporting`. O repositório
agrega antes de devolver o funil; entidades e catálogo não recebem essa responsabilidade.
As decisões de cálculo e apresentação estão em [Métricas](metricas.md).

Limites ainda registrados: republicação entre fontes com descrição curta pode passar pela
deduplicação; extração/enriquecimento chaveados só por `id_externo` têm risco de colisão entre
fontes, sem colisão real demonstrada nesta auditoria; banco aceita subárea de outro curso,
mitigada no carregamento; Jooble multiplica consultas por termo e permanece opcional.
Novos casos devem entrar na [matriz de cobertura](cobertura-estagios.md), com entrada,
esperado, observado e teste por causa. Não reabrir os seis bugs apenas por ler o relatório antigo.

### Calibração pendente

Em 03/09/2026, um anúncio com uma tecnologia declarada e atendida recebia 100, enquanto
outro com cinco e três atendidas recebia 85. A cobertura suavizada
`(1 + atendidas) / (1 + exigidas)` pode favorecer anúncios pouco detalhados.
Isso é calibração, distinto dos bugs de normalização de habilidades já corrigidos.

Antes de mudar pesos, investigar exemplos reais de `vaga_irrelevante`, especialmente
`motivo_nota`, comparando recusas com entregas por grupo. As habilidades declaradas estão
em `vagas.extracao`. Limitar a nota de anúncios com poucos requisitos ou considerar a
densidade de requisitos na cobertura são alternativas ainda não implementadas.
