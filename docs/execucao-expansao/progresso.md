# Registro de execução

Estado em 08/09/2026: plano sincronizado com `40ed28c`. O00–C05 foram implementados nesta
branch; as correções anteriores foram preservadas e revalidadas. Não reaplicar entregas
existentes.

## Ponto de retomada

- ID atual: C06.
- Próximo passo: alinhar estados pós-cadastro e mensagens de ausência de vagas à observabilidade real.
- Branch/HEAD: `codex/expansao-revenue-centric` / L02 pronto para commit.
- Alterações locais preexistentes: inventariar e preservar.
- Bloqueios reais: nenhum identificado para iniciar O00.

## Entregas

| ID | Estado | Arquivos/commit | Verificações e resultado | Pendência externa |
|---|---|---|---|---|
| O00 | Implementado/testado | `.github/workflows/radar-diario.yml` | `QUANTIDADE_VAGAS_ENVIADAS` mudou de 7 para 5; Python já tinha padrão 5 | Workflow versionado nesta branch; nenhuma execução remota verificada |
| C01 | Implementado/testado | `supabase/migrations/0018_habilidades_vazias.sql`, `tests/web/migrations_test.ts`, `docs/contrato-front.md` | Harness aplicou 0001–0017, inseriu perfil legado, aplicou 0018 e passou cadastro vazio, update do dono, rejeições, RLS e preservação | Migration ainda não aplicada em projeto remoto; publicação requer C02 antes e C03 depois |
| C02 | Implementado/testado | `radar/domain/models.py`, `tests/test_models.py`, `tests/test_avaliacoes.py`, `tests/test_storage_postgres.py` | Perfil vazio válido; `None` inválido; pontuação finita em Computação/Direito sem requisito dado como atendido; limites de curso/modalidade preservados; leitura Postgres coberta (teste ignorado sem `DATABASE_URL_TESTE`) | Python compatível localmente; publicação deve preceder C01 remoto |
| C03 | Implementado/testado | `web/index.html`, `web/assets/app.js`, `web/assets/styles.css`, `tests/web/cadastro_test.ts` | Atalho explícito libera `[]`, validação/payload preservam vazio, edição reabre vazio, remoção da última habilidade exige escolha nova, Enter continua adicionando, erro de rede preserva dados e eventos não gravam estado extra | C01 remoto e frontend ainda não publicados; visual 1280 px inspecionado no Safari local; 375 px pendente por falta de viewport responsivo disponível |
| C04 | Implementado/testado | `web/assets/app.js`, `web/index.html`, `web/assets/styles.css`, `tests/web/cadastro_test.ts` | Curso desconhecido não recebe sugestões de outra área; falha de catálogo limpa botões, avisa e preserva seleção; respostas antigas não vencem curso/sessão atuais | Catálogo remoto/publicação não verificados; JSON local continua gerado pelo catálogo único |
| C05 | Implementado/testado | `web/assets/app.js`, `web/index.html`, `tests/web/cadastro_test.ts` | Novo cadastro percorre perfil e só pede conta no fim; login continua só na conta; edição pula conta; rascunho sobrevive à troca de modo; envio duplicado é ignorado | Publicação e CAPTCHA real não verificados; viewport exato de 375 px pendente |
| L01 | Implementado/testado | `web/index.html`, `tests/test_product_copy.py` | Hero, SEO/social, CTA e condição do piloto usam a promessa multiarea com até cinco recomendações explicadas no Telegram; alegações antigas de IA/tecnologia foram removidas | Clique autenticado coberto por teste local; publicação e viewport exato de 375 px não verificados |
| L02 | Implementado/testado | `web/index.html`, `tests/test_product_copy.py` | Demo visível como exemplo fictício usa nota, fonte/data, requisitos atendidos e a conferir; marcas são fontes/tecnologias; FAQ cobre cobertura, vínculo, ausência, candidatura e conta | Abertura nativa de FAQ verificada no Safari local; publicação e viewport exato de 375 px não verificados |
| Demais IDs locais | Não iniciado | — | Executar na ordem do índice | — |

## O00

- Comportamento antes → depois: o workflow sobrescrevia a configuração com 7; diário e dispatch por perfil agora recebem 5.
- Arquivos/símbolos: `.github/workflows/radar-diario.yml`, `radar/settings.py` conferido; padrão Python continua 5.
- Casos obrigatórios: busca textual confirmou um único override de produção; nenhum parâmetro de fonte, cron ou filtro foi alterado.
- Comandos/exit code: `git diff --check` será executado no fechamento do commit; inspeção YAML/diff concluída. Pipeline real não foi executado.
- Inspeção visual: não aplicável.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit após a verificação final do ID. Sem deploy/publicação remota.
- Pendência real/próximo comando: nenhuma no código local; iniciar C01 e manter a sequência de publicação C02 → migration C01 → frontend C03.

## C01

- Comportamento antes → depois: `perfis.habilidades` exigia pelo menos um item e a RPC rejeitava lista vazia; `0018` aceita lista vazia e mantém validação de 0–50 strings não vazias, inclusive no update direto.
- Arquivos/símbolos: `supabase/migrations/0018_habilidades_vazias.sql`, `tests/web/migrations_test.ts`, `docs/contrato-front.md`.
- Casos obrigatórios: cadastro via confirmação com `[]` salvo; update do dono com `[]`; array nulo, elemento nulo, item em branco e 51 itens rejeitados; update de outro usuário sem alteração; perfil legado com `Excel` preservado.
- Comandos/exit code/aprovados/ignorados: `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/migrations_test.ts` — exit 0, 1 aprovado, 0 ignorados.
- Inspeção visual: não aplicável.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit C01 após a suíte Python completa. Migration não aplicada remotamente.
- Pendência real/próximo comando: disponibilizar C02 antes de aplicar `0018`; seguir para C02.

## C02

- Comportamento antes → depois: `Perfil` rejeitava lista vazia; agora aceita `[]` como único estado sem habilidades informado, mantendo a lista obrigatória e rejeitando `None`.
- Arquivos/símbolos: `radar/domain/models.py`, `tests/test_models.py`, `tests/test_avaliacoes.py`, `tests/test_storage_postgres.py`; a fórmula de `pontuar` não foi alterada.
- Casos obrigatórios: perfis iniciantes de Computação e Direito tiveram notas finitas de 0–100, nenhum requisito foi marcado como atendido, e os limites de curso/modalidade continuaram ativos; perfil legado segue coberto pela suíte existente.
- Comandos/exit code/aprovados/ignorados: P — `uv run pytest -q tests/test_models.py tests/test_avaliacoes.py tests/test_storage_postgres.py` — exit 0, 66 aprovados, 25 ignorados por ambiente Postgres; `uv run pytest -q tests/test_compatibilidade.py` — exit 0, 57 aprovados.
- Inspeção visual: não aplicável.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit C02 após `uv run pytest -q`. Disponibilização remota não verificada.
- Pendência real/próximo comando: publicar C02 antes da migration C01; seguir para C03.

## C03

- Comportamento antes → depois: a etapa exigia uma habilidade; agora oferece “Ainda não quero informar habilidades”, libera a próxima etapa com `[]`, mantém a escolha ao voltar e exige nova escolha quando a última habilidade é removida.
- Arquivos/símbolos: `web/index.html`, `web/assets/app.js` (`continuarSemHabilidades`, `validateStep`, `profileFromForm`, `preencherFormularioCom`, `renderSkills`), `web/assets/styles.css`, `tests/web/cadastro_test.ts`.
- Casos obrigatórios: novo cadastro vazio até o payload; edição de perfil salvo com `[]`; adicionar/remover última habilidade; Enter; logout/nova inscrição; erro de rede com dados preservados. O teste também confirma que o booleano não aparece nos eventos.
- Comandos/exit code/aprovados/ignorados: W — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/cadastro_test.ts` — exit 0, 36 aprovados, 0 ignorados.
- Inspeção visual: Safari local em viewport de desktop (~1280 px), landing e modal/foco inicial conferidos; foco migra para e-mail e o botão novo é nativo. Verificação exata a 375 px não foi possível porque não havia viewport responsivo/browser controlável disponível; CSS de `@media (max-width: 760px)` foi revisado.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit C03 após suíte Python completa. Frontend não publicado.
- Pendência real/próximo comando: aplicar C01 somente depois de C02 publicado e C03 depois da migration; seguir para C04.

## C04

- Comportamento antes → depois: curso desconhecido recebia `habilidades_gerais`; agora recebe somente entrada livre e o caminho vazio. Falha do JSON limpa sugestões sem apagar seleção e exibe aviso discreto. Requisições antigas são ignoradas por identidade do formulário, curso e número da requisição.
- Arquivos/símbolos: `web/assets/app.js` (`montarHabilidadesDoCurso`, `montarAreasDoCurso`, invalidação assíncrona), `web/index.html` (`skills-catalog-notice`), `web/assets/styles.css`, `tests/web/cadastro_test.ts`.
- Casos obrigatórios: Direito/Computação preservam sugestões existentes; curso desconhecido sem sugestões; catálogo indisponível com seleção preservada; duas trocas rápidas terminam no curso atual; logout/nova inscrição continuam limpando estado de áreas. Item livre e atalho de C03 continuam disponíveis.
- Comandos/exit code/aprovados/ignorados: W — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/cadastro_test.ts` — exit 0, 38 aprovados, 0 ignorados; `uv run pytest -q tests/test_areas_do_front.py` — exit 0, 1 aprovado.
- Inspeção visual: aviso usa `role=status`, não altera o payload e mantém foco/entrada nativos; viewport exato de 375 px continua não verificável nesta sessão.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit C04 após suíte Python completa. Nenhuma publicação externa.
- Pendência real/próximo comando: publicar catálogo/JSON junto do frontend quando a equipe executar a sequência; seguir para C05.

## C05

- Comportamento antes → depois: todo cadastro começava na conta; novo cadastro agora começa por momento, habilidades e preferências e pede e-mail, senha, consentimento e CAPTCHA somente no fim. Login continua na conta e edição continua somente no perfil.
- Arquivos/símbolos: `web/assets/app.js` (`passosAtivos`, `atualizarPassosAtivos`, `openSignup`, `setAuthMode`, `form submit`), `web/index.html` (progresso 1 de 4), `tests/web/cadastro_test.ts`.
- Casos obrigatórios: transições não chamam `signup`; alternância login/cadastro preserva curso, habilidades e cidade; logout limpa rascunho; perfil vazio segue aceito; envio duplicado durante autenticação gera uma tentativa; eventos existentes não foram renomeados.
- Comandos/exit code/aprovados/ignorados: W — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/cadastro_test.ts` — exit 0, 40 aprovados, 0 ignorados.
- Inspeção visual: Safari local em desktop (~1280 px) mostrou o novo cadastro abrindo na etapa de perfil, com `Etapa 1 de 4` e foco no curso. A viewport exata de 375 px não foi disponibilizada nesta sessão.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit C05 será criado após a suíte Python completa. Nenhuma publicação externa.
- Pendência real/próximo comando: validar L01 na landing; publicação, CAPTCHA real e viewport móvel continuam dependentes da equipe/ambiente.

## L01

- Comportamento antes → depois: a primeira dobra prometia que as vagas certas chegariam e usava linguagem genérica; agora nomeia curso e momento, oportunidades de diferentes áreas, até cinco recomendações explicadas no Telegram e gratuidade durante o piloto.
- Arquivos/símbolos: `web/index.html` (title, description, Open Graph, Twitter, hero, trust strip, copy de comparação), `tests/test_product_copy.py`.
- Casos obrigatórios: buscas textuais não encontram a promessa antiga, não há “Pare de procurar estágio” nem “A IA compara”, e o CTA conserva `.js-open-signup`, `data-event-origin` e o comportamento de conta existente.
- Comandos/exit code/aprovados/ignorados: `uv run pytest -q tests/test_product_copy.py tests/test_frontend_activation.py` — exit 0, 31 aprovados, 0 ignorados; `git diff --check` — exit 0.
- Inspeção visual: Safari local recarregado em desktop (~1280 px) exibiu o novo título completo, CTA e os dois sinais de confiança sem rolagem horizontal aparente. Viewport exato de 375 px não foi disponibilizado.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit L01 será criado após a verificação do diff. Nenhuma publicação externa.
- Pendência real/próximo comando: alinhar a demonstração e as cinco dúvidas prioritárias em L02; clique com sessão real não foi validado fora do harness.

## L02

- Comportamento antes → depois: o cartão parecia uma vaga real, usava “match” e não mostrava o estado de requisitos a conferir; agora é explicitamente ilustrativo, usa “nota / 100”, fonte/data, requisitos atendidos e a conferir, sem link de candidatura real. A FAQ responde as cinco dúvidas fechadas.
- Arquivos/símbolos: `web/index.html` (demo, faixa de fontes/tecnologias e seis `details`), `tests/test_product_copy.py`.
- Casos obrigatórios: demo não contém texto visível “match”, não apresenta parceiro/depoimento, informa que as fontes não cobrem tudo, explica limite de cinco, dias sem vaga, candidatura na fonte, vínculo do Telegram e edição/pausa da conta.
- Comandos/exit code/aprovados/ignorados: `uv run pytest -q tests/test_product_copy.py tests/test_formatador.py` — exit 0, 46 aprovados, 0 ignorados; `git diff --check` — exit 0.
- Inspeção visual: Safari local com query de cache exibiu o cartão e a FAQ atualizados; abrir “Preciso vincular o Telegram?” por controle nativo mostrou a resposta e estado expandido. Viewport exato de 375 px não foi disponibilizado.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit L02 será criado após a verificação do diff. Nenhuma publicação externa.
- Pendência real/próximo comando: executar C06 e conferir mensagens de sucesso/espera sem alegar execução do job.

Estados: Parcial; Não iniciado; Em execução; Implementado/testado; Preparado, falta evidência externa;
Bloqueado (descrever causa); Publicado/verificado. A coluna de publicação nunca decorre apenas
do status de teste ou merge. Detalhes ficam aqui; estado resumido fica no índice do plano.

## Verificação final

- Python: não executado nesta fila.
- Web/banco: não executado nesta fila.
- Lint/formatação: não executado nesta fila.
- Visual: não executado nesta fila.
- Versões remotas: não verificadas nesta fila.

## Decisões e evidências externas pendentes

Preencher durante E01–E05/D01, com link para os documentos produzidos. Não reproduzir chaves,
tokens, dados pessoais ou informações de conta desnecessárias.

## Referência anterior à execução da fila

Base `40ed28c`: 649 testes Python aprovados e 24 ignorados. Web/banco: 36 aprovados
em `a87f9fc`. Esses resultados são referência, não conclusão das tarefas futuras.

## Modelo de registro por tarefa

Copiar para cada ID em execução; não preencher resultados antes de verificar.

- ID/subpasso:
- Comportamento antes → depois:
- Arquivos/símbolos:
- Casos obrigatórios e teste correspondente:
- Comandos/exit code/aprovados/ignorados:
- Inspeção visual (se aplicável):
- Commit/branch e publicação:
- Pendência real/próximo comando:

A ordem de retomada segue os blocos do índice. Após C05, iniciar L01; a landing vem antes de L02 e C06.
