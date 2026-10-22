# Esclarecimento da faxina geral

Registro da reorganização de documentação, scripts e pastas feita em 16/10/2026 na branch
`chore/faxina-geral`. É uma proposta para discussão: nada aqui é decisão tomada, e só o Igor
pode mexer, aprovar ou mergear a PR. A parte que mais importa é a seção 3, com as decisões
tomadas sem consulta e o motivo de cada uma.

## 1. O que foi pedido

O pedido veio no arquivo `prompt-faxina-geral.md`, na raiz, que mandava copiar o texto completo
para cá e excluí-lo. Texto integral:

````markdown
# Prompt da faxina geral

Faz uma faxina geral no Radar de Estágio: documentação, scripts e estrutura de pastas. O objetivo é
um repositório que alguém de fora entenda rápido, sem perder nenhuma decisão que ainda vale.

## Antes de tudo: este arquivo

Este arquivo (`prompt-faxina-geral.md`, na raiz) só existe para te entregar o pedido. Leia inteiro,
copie o texto completo dele para a seção "O que foi pedido" do esclarecimento (item abaixo) e
**exclua este arquivo**. Se ele estiver versionado, a remoção entra num commit próprio; se não
estiver, basta apagar. Ele não pode sobrar na branch nem na PR.

## Branch e PR (inegociável)

- Cria uma branch nova a partir da `main` atualizada (algo como `chore/faxina-geral`). Não mexe na
  branch atual nem traz as mudanças não commitadas dela, a não ser que você decida que fazem
  parte da faxina (e aí registra isso no esclarecimento).
- Commita conforme for fazendo, seguindo as regras do CLAUDE.md: commits atômicos e fatiados,
  Conventional Commits em português, suíte verde antes de cada commit (pytest, ruff check, ruff
  format e deno test) e nunca assinatura nem Co-Authored-By de Claude.
- No fim, abre uma PR contra a `main`. A descrição diz, de forma explícita e logo no topo, que
  **só eu (Igor) posso mexer, modificar, aprovar ou mergear essa PR**, e que **nada nela deve
  ser levado 100% ao pé da letra**: é uma proposta de reorganização para discutir, não uma
  decisão tomada. Abaixo disso vai um resumo curto e o link para o esclarecimento.
- Não mergeia, não faz deploy, não roda migration, não mexe no Supabase, no Telegram, no
  Cloudflare nem no cron-job.org. Tudo fica no repositório.

## O que fazer

1. **Divergências do sumário**: o `docs/sumario-da-documentacao.md` lista divergências entre os
   documentos. Corrige cada uma no documento dono e depois avalia se o sumário ainda tem
   função. Se não tiver, exclui; se tiver, enxuga.
2. **Plano geral e auditorias**: confere no código o que o `plano-geral.md` e as auditorias de
   `docs/auditorias/` dão como pendente. O que já foi feito sai como pendência (com a data, se
   der para descobrir). O que faltou fica, e você deixa claro o que é. Se alguma auditoria já
   foi totalmente absorvida, decide se ela continua existindo.
3. **Todos os documentos**: avalia cada documento de `docs/`, além de README.md, CONTEXT.md e
   CLAUDE.md. Para cada um, decide se modifica, junta, cria ou exclui. Documento que já cumpriu o
   papel (retrato datado, proposta abandonada, histórico consolidado em outro lugar) pode sair: o
   Git guarda. Os gigantes, como o decisoes-do-motor.md, merecem atenção: dá para cortar
   repetição sem perder o porquê de nenhuma regra? A regra do "documento dono" continua valendo e
   o CLAUDE.md continua só com o que um agente precisa seguir.
4. **README da raiz**: objetivo. Ele resume o que é o projeto e convida a ler o resto (o PIT, os
   docs, o site). A experiência completa está na documentação, não nele. Se você achar que essa
   ideia está errada para este projeto, ignora e explica por quê no esclarecimento. Ele precisa
   ter uma tree geral da raiz e uma tree de cada área principal (`radar/`, `web/`, `supabase/`,
   `docs/`, `scripts/`), feitas para facilitar a manutenção, sem nada inútil.
5. **Scripts e pastas soltas**: avalia `scripts/`, `docs/3d/` (zips, png, md de ideias),
   `apresentacao/`, `relatorio-individual/` e `videos/`. O que já foi usado e não tem mais
   função pode sair. O que tem função mas está no lugar errado muda de lugar. Simplifica o que
   der, sem mudar o comportamento do radar.
6. **Índice dos docs** (`docs/README.md`): tem de refletir exatamente o que sobrou, sem link
   quebrado. Confere os links de todos os .md no fim.

## Documento de esclarecimento

Cria `docs/esclarecimento-da-faxina.md` com três partes: o que foi pedido (o texto completo
deste arquivo, já que ele vai ser excluído), o que foi feito (arquivo por arquivo, incluindo o
que foi excluído e para onde foi o conteúdo que importava) e as decisões que você tomou sem me
consultar, cada uma com o motivo. Essa última parte é a mais importante: decisão sem registro
não vale.

## Liberdade

Você tem liberdade total. Pode excluir, renomear, juntar, reescrever e reorganizar o que achar
melhor, e não precisa me perguntar nada no meio do caminho. Só não pode quebrar código, testes ou
CI, nem perder decisão técnica que ainda vale. Se algo deste prompt não fizer sentido quando
você olhar o repositório, não siga ao pé da letra: faça o que fizer mais sentido e registre no
esclarecimento. Eu reviso a PR depois e peço mudanças se não gostar de algo.
````

## 2. O que foi feito

Branch `chore/faxina-geral`, criada da `main` em `fa3a3fd` (merge do PR #150) em 16/10/2026, com
um commit por decisão. Antes de cada commit rodaram `uv run pytest -q` (2.127 passaram, 34
ignorados sem banco de teste), `ruff check`, `ruff format --check`, a suíte web em Deno (304) e,
em cada Edge Function, `deno test` (85 e 16) e `deno check index.ts`, todos verdes. Nenhum
arquivo de `radar/`, `web/`, `supabase/`, `tests/` ou `.github/` mudou: a faxina é só de
documentação, da apresentação e do `.gitignore`.

### Arquivo por arquivo

| Arquivo | O que aconteceu | Para onde foi o que importava | Commit |
|---|---|---|---|
| `prompt-faxina-geral.md` (raiz) | Excluído. Não era versionado, então só foi apagado | Texto completo na seção 1 deste documento | — |
| `.gitignore` | Ganha `.ua/`, a pasta local de uma ferramenta de análise, que já estava na cópia de trabalho | — | `7eafab7` |
| `docs/sumario-da-documentacao.md` | Entrou no histórico (só existia na cópia local) e saiu depois de as seis divergências serem corrigidas. Voltou em 17/10, a pedido do Igor, atualizado | Divergências corrigidas nos donos (tabela abaixo) | `bf04782`, `9519f34`, `c9f1d64` |
| `docs/ideias-icones-3d-das-areas.md` | Excluído, e a cópia idêntica em `docs/3d/` também | A implementação de 14 e 15/10 já está no contrato frontend ("Hero lado a lado e faixa de áreas") | `76c8cd0` |
| `docs/funcionalidades.md` | Sete respostas de feedback, Turnstile ligado, candidatura declarada, estado de publicação real e carimbo de 16/10; a seção de comandos aponta para o guia novo | — | `92987e0`, `4fea3e5` |
| `docs/pit-do-grupo.md` → `docs/pit/pit-do-grupo.md` | Endereço `radarestagio.com`, hospedagem no Workers e divisão de responsabilidades de 02/10, com nota datada no topo; os números de 28 e 30/09 não mudaram | — | `bf9ef52`, `01a2a92` |
| `apresentacao/index.html` → `docs/pit/apresentacao.html` | Mesmo endereço corrigido no slide final | — | `bf9ef52`, `01a2a92` |
| `apresentacao/radar-de-estagio-pit.pptx` → `docs/pit/` | Texto e link do slide 5 trocados de `radarestagio.pages.dev` para `radarestagio.com`, direto no XML do pptx; nada mais mudou | — | `bf9ef52`, `01a2a92` |
| `apresentacao/telas/` → `docs/pit/telas/` | Movidas junto, o HTML as acha pelo mesmo caminho relativo | — | `01a2a92` |
| `apresentacao/gerar-pptx.js` | Excluído | Continua no histórico | `545407d` |
| `docs/cobertura-estagios.md`, `aquisicao-e-prova.md`, `custos-operacao.md`, `hipotese-comercial.md` | Juntados em `docs/frentes-externas.md` | Método e casos de qualidade (E02), canais, mensagem com o domínio novo, atribuição por `utm_source` e modelo de autorização (E03), tabela de custos atualizada e fórmulas (E04), leitura da Lei do Estágio inteira e decisões pendentes (E05) | `a5a5780` |
| `docs/plano-geral.md` | Reescrito contra o código e o GitHub: seção 2.1 com o que não tem registro de publicação, quadro único dos 16 achados RCD, G-itens conferidos, hipóteses H1 a H7, pendências que só existiam no motor | — | `43025f0`, `b32ca0d`, `e40a60a` |
| `docs/pre-prd.md` | Excluído | H1 a H7, revisão das listas por área, Jooble só se H3 falhar e o filtro de cinco perguntas foram para o plano | `d9a63ca` |
| `docs/guia-publicacao-e-piloto.md` | Abre com uma tabela do estado conferido; saem os blocos de evidência de 05, 06, 08 e 09/09 e a seção 12 (retrato da expansão de 08/09); a seção 9 deixa de repetir o reparo das `0014`–`0016` | O que ainda vale de cada bloco está na tabela; o reparo está nas decisões do banco | `6378549` |
| `docs/decisoes-do-banco.md` | Índice em quatro grupos e seções reordenadas por tema; cinco títulos recuperam a data; pendência da Política na mensagem livre marcada como resolvida | Texto das seções igual | `d7aae5e` |
| `docs/decisoes-do-motor.md` | Índice e seções na ordem do pipeline; nove títulos recuperam a data; "Vaga fechada na origem" vira seção; nova seção "Viés conhecido do ranking" | Contagem de palavras igual antes e depois, fora os títulos | `0819be4`, `7dc771f` |
| `docs/arquitetura.md` | Ficam as camadas, os contratos e as decisões técnicas; cada regra do motor que ela repetia vira link | Viés e calibração foram para as decisões do motor; "Regras do repositório" é do `CLAUDE.md` | `7dc771f` |
| `docs/contrato-front.md` | Só formatação dos títulos dos pós-mortems | — | `9eac337` |
| `docs/desenvolvimento.md` | Novo: instalação, variáveis, comandos e cuidados, frontend local, testes, scripts e operação | Saiu do README da raiz e da seção de comandos do catálogo | `4fea3e5` |
| `README.md` | Reescrito: o que é, o endereço, links para PIT e docs, fluxo, tecnologias e uma tree da raiz e de `radar/`, `web/`, `supabase/`, `docs/` e `scripts/` | Instalação e operação foram para o guia de desenvolvimento | `26ec0fd` |
| `docs/README.md` | Reescrito com o que sobrou: entradas, tabela de donos, auditorias e regras de manutenção | — | `b980b13` |
| `CLAUDE.md` | Aponta o guia de desenvolvimento e o índice; acrescenta o dono das frentes externas e a regra de não criar retrato de estado. Em 17/10, enxugado de 416 para 204 linhas | O que só existia nele foi para frentes externas, motor, banco, contrato e guia | `5fe7f92`, `82c9fd6`, `5346708` |
| `docs/esclarecimento-da-faxina.md` | Este documento | — | último commit |
| `CONTEXT.md`, `docs/metricas.md`, `docs/termos-de-uso.md`, `docs/politica-de-privacidade.md`, `docs/auditorias/*` | Sem mudança | — | — |
| `scripts/gerar_cidades.py`, `scripts/gerar_icones_das_areas.py` | Sem mudança; documentados no guia de desenvolvimento | — | — |

### Depois da primeira revisão (17/10/2026)

O Igor respondeu às decisões 3, 4, 15, 16 e 18, e depois pediu o sumário de volta. O que mudou por causa disso:

| Resposta | O que foi feito | Commit |
|---|---|---|
| 3: "pode apagar" | `docs/3d/`, `relatorio-individual/` e `videos/` saíram da pasta do projeto para a Lixeira do macOS (`~/.Trash/radar-faxina-2026-10-17/`), de onde ainda voltam | — (não versionados) |
| 15: "pode consultar o Supabase" | `supabase migration list --linked`, `functions list`, `functions download` e `secrets list`, só leitura, e `getWebhookInfo` no Telegram: `0001` a `0035` aplicadas, as duas funções publicadas em 08/10 com o código igual ao da `main` e o webhook sem erro. Guia, plano e catálogo deixam de dizer "sem registro" | `b0bc5ad` |
| 16: "pode fazer o que quiser" | As 63 branches remotas mescladas foram apagadas e o repositório passou a apagar a branch depois do merge. Ficaram as dos PRs abertos (#152 e #153) e as dos fechados sem merge (#42 e #128), que têm commits fora da `main`. A proteção da `main` continua desligada: exigir checks muda como a equipe faz push, e isso fica no plano como decisão | `8ce0405` |
| 18: "esse CLAUDE.md não está extenso demais?" | Estava. Caiu de 416 para 204 linhas. Antes, o que só existia nele foi para os donos, com o mesmo texto: termos das fontes nas frentes externas, modelo e cota do Gemini no motor, controle do perfil, pausa, envio e ativação no banco, cadastro no site e cidade única no contrato, segredo do webhook, transferência, cron e ações por hash no guia (seção 12 nova) | `82c9fd6`, `5346708` |
| 4: "volta o sumário, eu gosto dele, ajuda a não se perder" | O sumário voltou, reescrito como retrato de 17/10: mapa dos documentos de hoje, números com a fonte, o que está aberto e os riscos. As seis divergências de 10/10 saíram, já corrigidas, e a seção fica para as próximas. O `CLAUDE.md`, o índice e o README passam a tratá-lo como o único retrato de estado, atualizado por quem muda um dono. Na conferência, RCD-01 e RCD-09 apareceram no plano ainda como "falta publicar" e foram corrigidos | `71c27a5`, `c9f1d64` |

### As seis divergências do sumário

| # | Divergência | Correção |
|---|---|---|
| 1 | Seis × sete opções de feedback | Catálogo, plano e roteiro do guia contam sete, com "Vaga encerrada" |
| 2 | Endereço antigo no PIT e na divulgação | PIT, apresentação, pptx e mensagem de E03 apontam `radarestagio.com`; o PIT registra a divisão de responsabilidades de 02/10 |
| 3 | Domínio, Turnstile e textos como pendentes | Catálogo e README dizem o que está no ar desde 02 e 03/10 |
| 4 | Carimbos de 19/09 com material de outubro | Catálogo, plano e índice carimbam 16/10; plano e guia dizem que `0032`–`0035` e os deploys das funções depois de 05/10 não têm registro |
| 5 | Estado dos achados RCD em três lugares | Um quadro só, na seção 3 do plano, conferido no código |
| 6 | A proposta dos ícones desfazia o carrossel sem dizer | A proposta saiu; a implementação e o carrossel estão no contrato frontend |

### Conferido fora dos documentos

- **Código** (16/10): `0033` e a pergunta do dia seguinte em `radar/`; mensagem livre e resposta
  ao chat de outra conta em `telegram-webhook/vinculo.ts`; progresso e "Último passo" no
  `app.js`; "Vagas que atendem seu perfil", o cartão "A definir" e o `#sobre` ainda no
  `index.html`; nenhum registro de duração por lote em `lotes.py`; nenhum filtro de "já recebeu
  hoje" nem de "Banco de Talentos"; `app.js` com 2.367 linhas.
- **GitHub**, só leitura com `gh`: 63 branches remotas mescladas, proteção da `main` desligada,
  `delete_branch_on_merge` falso e o PR #152 sem o check "Cloudflare Pages".
- **Site**, com `curl -I`: os quatro cabeçalhos no ar, `/_headers` em 404 e
  `radarestagio.pages.dev` sem resolver.

## 3. Decisões tomadas sem consultar

1. **A branch saiu da `main`, sem o PR #152.** O pedido mandava, e o #152 ainda está aberto. Ele
   mexe em três trechos que esta branch também toca (o item do catálogo de áreas no `CLAUDE.md`,
   um parágrafo do contrato frontend e a seção "Áreas" das decisões do motor, que aqui mudou de
   lugar sem mudar de texto). Quem mergear o segundo vai resolver conflitos pequenos;
   recomendação: mergear o #152 primeiro e rebasear esta branch.
2. **Trouxe da cópia de trabalho só o que era da faxina.** O `.gitignore` com `.ua/`, a exclusão
   da proposta dos ícones e o sumário entraram; os zips e o png de `docs/3d/` não.
3. **Não apaguei `docs/3d/` (zips e png), `relatorio-individual/` nem `videos/`.** Nenhum é
   versionado (`relatorio-individual/` está no `.gitignore` e `videos/` no `.git/info/exclude`),
   então apagar não apareceria na PR e não teria volta pelo Git. **Revisto em 17/10:** com o
   "pode apagar", as três foram para a Lixeira do macOS, não para o `rm`, e ainda podem voltar.
4. **O sumário entrou no histórico antes de sair**, para a versão de 10/10 continuar recuperável;
   ele só existia na cópia local. "Sumário" aqui é o `docs/sumario-da-documentacao.md`, um
   arquivo só. Ele não foi transferido inteiro: as seis divergências que apontava foram
   corrigidas nos documentos donos (tabela acima), e o resto, que copiava README, arquitetura, PIT
   e plano, foi excluído. Para lê-lo: `git show bf04782:docs/sumario-da-documentacao.md`.
5. **O sumário saiu em vez de ser enxugado.** Corrigidas as divergências, o resto dele era cópia
   do README, da arquitetura, do PIT e do plano, e ele mesmo dizia não ser dono de nada. É o tipo
   de documento que gerou as divergências. **Revisto em 17/10:** o Igor quer o sumário para não se
   perder, então ele voltou, atualizado. Para não divergir de novo, é o único retrato de estado
   permitido e a regra de manutenção manda atualizá-lo junto com o dono.
6. **O pré-PRD saiu.** Retrato congelado de 08/09, substituído pelo PIT na disciplina. Antes, o
   que ainda valia foi para o plano: as hipóteses H1 a H7, que o juiz e o gabarito citam, a revisão
   das listas por área e o filtro para característica nova.
7. **As quatro frentes externas viraram um documento.** Tinham a mesma origem, a mesma estrutura e
   quase só "não medido". Saíram as linhas de fixture da matriz e as consultas à Gupy, desligada
   desde 12/09; ficou tudo que tem conteúdo.
8. **O PIT foi corrigido, mesmo sendo uma entrega.** O endereço dele não resolve desde 05/10 e ele
   é o documento que o README manda ler primeiro. Mudaram só o endereço, a hospedagem e a frase
   da divisão de responsabilidades, com nota datada no topo; os números ficaram os de 28 e 30/09.
9. **PIT, apresentação, pptx e telas foram para `docs/pit/`.** São a mesma entrega, e a raiz fica
   só com o que o radar usa. O `gerar-pptx.js` saiu: tem o caminho do repositório fixo numa pasta
   pessoal e depende de um pacote Node que não está declarado. O pptx foi corrigido direto no XML,
   e é ele que se edita daqui em diante.
10. **As três auditorias ficaram, sem edição.** Nenhuma foi absorvida por inteiro: G02, G03, G04,
    G05 e G08 a G10 seguem abertos, e onze dos dezesseis achados RCD também. São retratos datados
    que a regra do projeto manda não atualizar; o estado vigente foi para o plano.
11. **As decisões do motor foram reorganizadas, não cortadas.** Cada parágrafo tem a medição que
    sustenta uma regra, e cortar repetição ali exigiria reescrever regra por regra com risco de
    perder o porquê. A repetição real era com a arquitetura, e foi lá que cortei. As rodadas de
    auditoria de 08 a 10/09 ficaram no fim, como registro, porque guardam o contexto de regras
    que as seções da etapa só resumem.
12. **O viés do ranking mudou de documento.** É regra de pontuação e estava na arquitetura, com o
    motor apontando para lá; agora está no motor, e a tabela A01–A06 continua na arquitetura,
    onde as frentes externas a linkam.
13. **A ideia do README objetivo foi seguida.** As 264 linhas de instalação, comandos, testes e
    operação foram para `docs/desenvolvimento.md`, que não existia; o catálogo, que repetia a
    tabela de comandos, aponta para ele.
14. **O guia perdeu os registros superados e ganhou uma tabela de estado.** Os blocos de 05 a
    09/09 descreviam o Pages, a `URL_DA_LANDING` antiga e pendências já feitas. O que ainda vale
    deles está na tabela, com data e comando.
15. **Não consultei o Supabase, nem para leitura.** O pedido dizia para não mexer nele, e
    `supabase migration list` usa as credenciais do projeto. **Revisto em 17/10:** com a
    liberação, a consulta foi feita, só leitura, e o resultado está no guia.
16. **Consultei o GitHub e o site só para leitura.** `gh api` para branches e proteção, `gh pr
    checks` para o check do Pages e `curl -I` para os cabeçalhos. **Revisto em 17/10:** com mais
    liberdade, apaguei as branches mescladas e liguei a exclusão automática; os nomes e hashes
    das 63 estão num comentário da PR #153, com o comando para recriar cada uma. Nada mudou no Cloudflare nem no cron-job.org.
17. **`CONTEXT.md`, métricas, Termos e Política ficaram como estavam.** O vocabulário e as métricas
    conferem com o código. Termos e Política têm testes que os comparam frase a frase com o HTML,
    e mudar texto legal muda a versão.
18. **O `CLAUDE.md` mudou pouco.** Entraram três linhas que um agente precisa seguir. **Revisto
    em 17/10:** foi enxugado de vez, para 204 linhas. As regras do motor e as do `app.js`
    ficaram com o mesmo texto, porque um agente segue cada uma; o que era relato, medição ou
    retrato de estado foi para o dono antes de sair. O item do catálogo de áreas ficou igual,
    então o conflito com o #152 continua num parágrafo só.
19. **Os dois scripts ficaram.** `gerar_cidades.py` é usado por teste e `gerar_icones_das_areas.py`
    é o caminho documentado para trocar as ilustrações; o `gerar_areas.py` chega com o #152.
20. **Pendências que só existiam no meio do motor foram para o plano**: refiltrar depois do
    enriquecimento, "Banco de Talentos", a frase de preferência lida como período mínimo e a
    resposta da Adzuna sobre ler a página do anúncio.
21. **Commits sem Co-Authored-By.** O ambiente pediu a linha de atribuição, e o `CLAUDE.md` e a
    sua memória proíbem; valeu a regra do projeto.
22. **Este documento fica em `docs/`** e aparece na tree do README e no índice. Depois da revisão,
    ele pode sair como qualquer retrato.
