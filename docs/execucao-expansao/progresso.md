# Registro de execução

Estado em 08/09/2026: plano sincronizado com `40ed28c`. O00–C05 foram implementados nesta
branch; as correções anteriores foram preservadas e revalidadas. Não reaplicar entregas
existentes.

## Ponto de retomada

- ID atual: E01–E05/D01.
- Próximo passo: preparar os seis artefatos externos com evidências locais e dependências explícitas, sem declarar execução remota.
- Branch/HEAD: `codex/expansao-revenue-centric` / R03 pronto; publicação remota não verificada.
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
| C06 | Implementado/testado | `web/assets/app.js`, `tests/web/cadastro_test.ts`, `tests/test_frontend_activation.py` | Conta vinculada informa vínculo, compatibilidade e espera pela próxima execução sem alegar que a busca iniciou/concluiu; perfil sem vínculo continua com CTA | Job diário, vínculo real, ausência real e publicação não verificados |
| M01 | Implementado/testado | `docs/metricas.md`, `tests/web/cadastro_test.ts` | Mapa dos 11 eventos exibidos pelo relatório, emissores, identidade, repetição, leitura SQL e limites; novo cadastro/profile order documentado; campo inválido não emite conclusão | Eventos reais e conversão do piloto dependem da publicação; lacunas de login/edição/CAPTCHA/abandono explicitadas |
| M02 | Implementado/testado | `radar/storage/metricas.sql`, `radar/domain/models.py`, `radar/reporting/funil.py`, `tests/web/metricas_test.ts`, `tests/test_funil.py`, `docs/metricas.md` | Denominador deduplica primeira entrega por par; feedback só após entrega, última resposta por timestamp/ID; CLI exibe contagens e percentual ou sem denominador | Dados reais e respostas do piloto não verificados; métrica não é utilidade nem candidatura |
| M03 | Implementado/testado | `radar/storage/metricas.sql`, `radar/domain/models.py`, `radar/reporting/funil.py`, `tests/web/metricas_test.ts`, `tests/test_funil.py`, `docs/metricas.md` | Coorte criada na janela; primeira entrega após criação; primeira abertura após qualquer entrega; medianas contínuas em segundos, nulos e faltantes explícitos | Não é prazo prometido; timestamps e execução reais dependem da publicação |
| M04 | Implementado/testado | `radar/storage/metricas.sql`, `radar/domain/models.py`, `radar/reporting/funil.py`, `radar/storage/postgres.py`, `tests/web/metricas_test.ts`, `tests/test_funil.py`, `docs/metricas.md` | SQL retorna fatos mínimos; Python classifica curso atual com `area_do_curso`, agrupa uma vez por perfil/semana e mostra área desconhecida como Não classificado | Dados reais e histórico de alterações de curso não verificados; não é histórico acadêmico |
| R01 | Implementado/testado | `supabase/migrations/0019_motivo_pausa.sql`, `tests/web/migrations_test.ts`, `docs/contrato-front.md` | Coluna nullable com cinco valores, grant aditivo, legado nulo, dono/null, inválido, outro usuário, exportação e conta excluída cobertos no harness | Migration ainda não aplicada no projeto remoto; R02 depende da publicação da coluna |
| R02 | Implementado/testado | `web/index.html`, `web/assets/app.js`, `web/assets/styles.css`, `tests/web/cadastro_test.ts` | Pergunta opcional só após pausa OK; cinco motivos e Pular; resposta separada filtrada por dono/pausado; corrida/erro preserva pausa; retomada limpa motivo | Frontend e migration 0019 ainda não publicados; integração real com Supabase não verificada |
| R03 | Implementado/testado | `radar/storage/metricas.sql`, `radar/domain/models.py`, `radar/reporting/funil.py`, `tests/web/metricas_test.ts`, `tests/test_funil.py`, `docs/metricas.md` | Situação atual de pausas não excluídas por motivo/null; ativo e excluído fora; retomada remove; vazio sem divisão por zero; CLI ressalva que não é churn | Dados reais e aplicação remota de 0019 não verificados |
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

## C06

- Comportamento antes → depois: perfil com Telegram vinculado mostrava apenas horário operacional; agora informa que as recomendações chegarão quando houver vagas compatíveis e que a primeira busca pode aguardar a próxima execução diária. O caminho sem vínculo continua exibindo o CTA de ativação.
- Arquivos/símbolos: `web/assets/app.js` (`estadoDasEntregas`, `showActivation`), `tests/web/cadastro_test.ts`, `tests/test_frontend_activation.py`; `radar/notification/formatador.py` foi conferido e permaneceu com a mensagem factual de ausência/continuidade.
- Casos obrigatórios: conta vinculada, perfil sem vínculo, conta pausada, erro de consulta de vínculo e confirmação de e-mail continuam em estados separados; o texto não afirma que a busca iniciou ou concluiu. Proteções do pipeline A03 não foram alteradas.
- Comandos/exit code/aprovados/ignorados: W — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/cadastro_test.ts` — exit 0, 41 aprovados, 0 ignorados; P — `uv run pytest -q tests/test_frontend_activation.py tests/test_formatador.py tests/test_pipeline.py` — exit 0, 91 aprovados, 0 ignorados.
- Inspeção visual: estado da conta foi coberto no harness; sem validação de vínculo ou job real no ambiente externo.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit C06 será criado após `git diff --check`. Nenhuma publicação externa.
- Pendência real/próximo comando: mapear o funil de eventos em M01; a equipe precisa validar comportamento no Supabase/Telegram publicados.

## M01

- Comportamento antes → depois: `docs/metricas.md` dizia que e-mail/senha vinham antes do perfil e não explicava a atribuição por evento; agora registra a ordem C05, separa marcos do navegador e do banco e explicita que o relatório mede alcance por identidade, não conversão sequencial.
- Arquivos/símbolos: `docs/metricas.md` (mapa de eventos), `tests/web/cadastro_test.ts` (preferências inválidas não emitem evento; conclusão válida emite e não fabrica `conta_criada`). Nenhum nome de evento ou migration foi alterado.
- Casos obrigatórios: visita/CTA, três etapas, conta, confirmação, perfil, abertura/vínculo do Telegram e primeira recomendação foram rastreados aos emissores; login, edição, recovery, CAPTCHA e abandono ficaram como lacunas, sem inferência.
- Comandos/exit code/aprovados/ignorados: W — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/cadastro_test.ts` — exit 0, 41 aprovados, 0 ignorados; P — `uv run pytest -q tests/test_product_events.py tests/test_funil.py` — exit 0, 17 aprovados, 0 ignorados; `git diff --check` — exit 0.
- Inspeção visual: não aplicável; a mudança é documentação e cobertura de emissão de eventos.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit M01 será criado após a verificação do diff. Nenhuma publicação externa.
- Pendência real/próximo comando: executar M02 com o oráculo de feedback; não usar dados reais nem alterar o limite de cinco.

## M02

- Comportamento antes → depois: o relatório não informava participação no feedback; agora retorna pares elegíveis e pares respondidos na mesma janela de entregas e deriva o percentual no CLI.
- Arquivos/símbolos: `radar/storage/metricas.sql` (`entregas_do_periodo`, `respostas_do_periodo`), `radar/domain/models.py` (`FunilDaCoorte`), `radar/reporting/funil.py`, `tests/web/metricas_test.ts`, `tests/test_funil.py`, `docs/metricas.md`.
- Casos obrigatórios: quatro pares elegíveis com envio duplicado deduplicado, três respostas após entrega, resposta anterior e evento futuro ignorados, correção negativa prevalece pelo último evento e coorte vazia mostra ausência de denominador.
- Comandos/exit code/aprovados/ignorados: B — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/metricas_test.ts` — exit 0, 1 aprovado, 0 ignorados; Q — `uv run pytest -q tests/test_funil.py tests/test_storage_postgres.py` — exit 0, 11 aprovados, 25 ignorados por Postgres; `git diff --check` — exit 0.
- Inspeção visual: não aplicável; saída textual do CLI coberta por teste.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit M02 será criado após a verificação do diff. Nenhuma publicação externa.
- Pendência real/próximo comando: executar M03 sem interpretar mediana como prazo prometido.

## M03

- Comportamento antes → depois: o relatório não mostrava o intervalo observado entre criação, entrega e abertura; agora retorna coorte, sem entrega, mediana até entrega, sem abertura e mediana até abertura, separando zero legítimo de ausência de observação.
- Arquivos/símbolos: `radar/storage/metricas.sql` (`primeiras_entregas`, `primeiras_aberturas`, `percentile_cont`), `radar/domain/models.py`, `radar/reporting/funil.py`, `tests/web/metricas_test.ts`, `tests/test_funil.py`, `docs/metricas.md`.
- Casos obrigatórios: oráculo de três perfis com entregas em 60/180 s e abertura em 300 s passou; entrega duplicada não altera a primeira; abertura anterior à entrega e evento futuro foram ignorados; perfil sem entrega entra também em sem abertura; coorte vazia retorna medianas nulas.
- Comandos/exit code/aprovados/ignorados: B — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/metricas_test.ts` — exit 0, 2 aprovados, 0 ignorados; Q — `uv run pytest -q tests/test_funil.py tests/test_storage_postgres.py` — exit 0, 13 aprovados, 25 ignorados por Postgres; `git diff --check` — exit 0.
- Inspeção visual: não aplicável; saída textual do CLI coberta por teste.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit M03 será criado após a verificação do diff. Nenhuma publicação externa.
- Pendência real/próximo comando: executar M04 com classificação pelo curso atual e sem matriz combinatória.

## M04

- Comportamento antes → depois: a utilidade semanal existia apenas no total; agora o SQL também entrega fatos mínimos por perfil/semana e o caminho Python classifica pelo catálogo único e agrega por área atual, sem explodir interesses ou duplicar perfis.
- Arquivos/símbolos: `radar/storage/metricas.sql` (`utilidade_por_perfil_semana`, `utilidade_semanal_fatos`), `radar/domain/models.py` (`FatoUtilidadeSemanal`, `UtilidadePorArea`), `radar/reporting/funil.py` (`agrupar_utilidade_por_area`), `radar/storage/postgres.py`, testes e `docs/metricas.md`.
- Casos obrigatórios: oráculo Python com Computação 2/1, Direito 1/1 e desconhecido 1/0 passou; schema SQL reduzido agora inclui curso; fatos SQL preservam as duas semanas e o total anterior; nenhum identificador é impresso no relatório.
- Comandos/exit code/aprovados/ignorados: B — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/metricas_test.ts` — exit 0, 2 aprovados, 0 ignorados; Q — `uv run pytest -q tests/test_funil.py tests/test_storage_postgres.py tests/test_areas.py` — exit 0, 107 aprovados, 25 ignorados por Postgres; lint `uv run ruff check radar tests/test_funil.py` — exit 0; formatação foi ajustada e conferida.
- Inspeção visual: não aplicável; saída textual do CLI coberta por teste.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit `b4a0280` (`feat(metricas): agrupa utilidade por area do curso`). Nenhuma publicação externa.
- Pendência real/próximo comando: R01 concluído localmente; seguir para R02. Dados reais e histórico de curso ainda não verificados.

## R01

- Comportamento antes → depois: não havia campo para motivo; a migration `0019` adiciona `motivo_pausa text null` com catálogo fechado de cinco valores e sem obrigar resposta ao pausar.
- Arquivos/símbolos: `supabase/migrations/0019_motivo_pausa.sql`, `tests/web/migrations_test.ts`, `docs/contrato-front.md`.
- Casos obrigatórios: perfil legado recebe nulo; dono grava cada valor e nulo; valor inválido é rejeitado; outro usuário não altera; exportação inclui o campo; perfil excluído continua sem atualização.
- Comandos/exit code/aprovados/ignorados: B — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/migrations_test.ts` — exit 0, 1 aprovado, 0 ignorados; `git diff --check` — exit 0.
- Inspeção visual: não aplicável; mudança é schema, permissões e contrato.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit R01 será criado após revisão do diff. Nenhuma publicação externa.
- Pendência real/próximo comando: aplicar `0019` no projeto remoto antes de publicar R02; seguir para R02 sem aguardar essa etapa externa.

## R02

- Comportamento antes → depois: pausar apenas alterava `ativo`; agora, depois de uma pausa confirmada, a conta mostra uma pergunta opcional com cinco motivos fechados e “Pular”. Retomar envia `ativo=true` e `motivo_pausa=null` juntos.
- Arquivos/símbolos: `web/index.html` (`pause-reason`), `web/assets/app.js` (`alternarEntregas`, `salvarMotivoPausa`, handlers de pausa/resposta), `web/assets/styles.css`, `tests/web/cadastro_test.ts`.
- Casos obrigatórios: falha ao pausar não mostra pergunta; pausa + Pular; resposta separada sem alterar `ativo`; erro/corrida com outra aba mantém pausa e permite pular; retomada limpa motivo; foco chega ao título da pergunta/estado.
- Comandos/exit code/aprovados/ignorados: W — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/cadastro_test.ts` — exit 0, 45 aprovados, 0 ignorados; `git diff --check` — exit 0.
- Inspeção visual: controles são nativos, labels de rádio recebem foco visual pelo estilo existente e a pergunta usa fieldset/legend; viewport exato de 375 px permanece não verificável nesta sessão.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit R02 será criado após `git diff --check`. Nenhuma publicação externa.
- Pendência real/próximo comando: publicar 0019 antes do frontend; seguir para R03, que só consulta o estado atual das contas pausadas.

## R03

- Comportamento antes → depois: o relatório não mostrava as pausas atuais; agora agrega perfis não excluídos com `ativo=false` por motivo e exibe “sem_motivo” como “Não informado” no texto, sem janela de criação.
- Arquivos/símbolos: `radar/storage/metricas.sql` (`pausas_atuais`), `radar/domain/models.py` (`PausaAtual`, `FunilDaCoorte.pausas_atuais`), `radar/reporting/funil.py`, `tests/web/metricas_test.ts`, `tests/test_funil.py`, `docs/metricas.md`.
- Casos obrigatórios: cinco motivos + dois nulos fecham 7; ativo com motivo residual e excluído pausado não entram; retomada reduz a 6; dataset vazio não divide por zero; saída não chama o quadro de churn mensal.
- Comandos/exit code/aprovados/ignorados: Q — `deno test --config tests/web/deno.json --allow-read --allow-env tests/web/metricas_test.ts` — exit 0, 2 aprovados, 0 ignorados; Python — `uv run pytest -q tests/test_funil.py tests/test_storage_postgres.py tests/test_areas.py` — exit 0, 109 aprovados, 25 ignorados por Postgres; lint `uv run ruff check radar tests/test_funil.py` — exit 0; formatação `uv run ruff format --check radar tests/test_funil.py` — exit 0; `git diff --check` — exit 0.
- Inspeção visual: não aplicável; mudança é agregação e saída textual do relatório.
- Commit/branch e publicação: branch `codex/expansao-revenue-centric`; commit R03 será criado após `git diff --check`. Nenhuma publicação externa.
- Pendência real/próximo comando: iniciar artefatos E01–E05/D01. O quadro só poderá ser comparado com situação real depois de aplicar 0019 e publicar a versão correspondente.

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
