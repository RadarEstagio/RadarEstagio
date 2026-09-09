# Plano de expansão — índice de execução

Revisado em 08/09/2026 contra a main `40ed28c`, incluindo as duas rodadas de correções
de Ian e a revalidação local. Este SHA identifica a base examinada, não uma versão para
restaurar. Conferir mudanças posteriores antes de executar. Planejamento não comprova deploy.

## Objetivo e decisões mantidas

Atender estudantes de diferentes formações com recomendações de estágio explicadas no
Telegram. Não prometer todos os anúncios existentes nem contratação. A necessidade comum
é reduzir o trabalho de procurar e avaliar oportunidades; a personalização depende de curso,
momento, habilidades, interesses e logística.

O piloto continua informal. Entrevistas, coortes mínimas, D7 e teste A/B não são requisitos
para divulgar. Pagamento, mídia paga, fontes adicionais e novas regras de elegibilidade só
entram nas tarefas específicas, com dados e decisões registrados. O plano não autoriza envio
de mensagens a terceiros. Não há dashboard, candidatura automática ou novo framework nesta fila.

Mecanismos da [skill Revenue-Centric Design](../.agents/skills/revenue-centric-design/SKILL.md):
promessa sustentada por prova (L01–L02), valor antes do pedido e fricção declarativa (C01–C05),
tempo até o valor (M03), retenção por utilidade e jobs-to-be-done (R01–R03), Bullseye (E03),
custo de servir e pagamento como evidência (E04–E05). Swiss Knife filter rege todo o escopo:
cada tarefa precisa reforçar seleção, entrega ou compreensão do valor. Estatísticas da skill
não são metas nem previsões do Radar.

## Foco absoluto e ordem de trabalho

Resultado prioritário: estudante de outra área ou iniciante consegue completar o perfil e
entender recomendações relevantes, sem perder dados nem receber explicações falsas.
Não maximizar quantidade de funcionalidades ou prometer cobertura universal.

| Bloco | IDs, nesta ordem | Resultado necessário para fechar |
|---|---|---|
| 1. Cadastro e confiança | O00 → C01 → C02 → C03 → C04 → C05 | Limite cinco, iniciante aceito de ponta a ponta, navegação e isolamento entre contas preservados |
| 2. Compreensão da entrega | L01 → L02 → C06 | Promessa, demonstração e estados coerentes com o que o sistema sabe |
| 3. Aprendizado | M01 → M02 → M03 → M04 | Eventos interpretáveis, contagens e tempos corretos, utilidade por área sem duplicação |
| 4. Motivo da pausa | R01 → R02 → R03 | Pausa continua livre; resposta opcional é persistida e relatada corretamente |
| 5. Preparação externa | E01 → E02 → E03 → E04 → E05 → D01 | Procedimentos/evidências e decisões pendentes documentados, sem métricas inventadas |

A ordem dos blocos governa a execução local; a ordem de publicação de C01–C03 continua
C02 → C01 → C03. E01 pode ser consultado antes quando for necessário publicar, mas falta de
acesso externo não interrompe outro ID local. Não começar monetização enquanto há trabalho
local de cadastro/confiança pendente. Problema de regressão introduzida tem precedência sobre
novo ID. Achado alheio ao escopo vira pendência reproduzível, não refactor oportunista.

Cada ficha agora inclui passos internos, cenários e fechamento. C05 tem quatro subpassos;
M02–M04 têm exemplos numéricos para conferir o cálculo. Os comandos P/W/B/Q estão definidos
no protocolo, sem exigir que a IA adivinhe nomes de arquivos ou como executar a suíte.

## Já implementado — preservar, não refazer

| Entrega | Evidência no código/commit | Limite ainda existente |
|---|---|---|
| Catálogo de 12 áreas, subáreas, extração e cadastro dinâmico | `radar/domain/areas.py`, `web/assets/areas.json`, migration 0017 | Catálogo não representa todas as formações; aplicação remota da migration não verificada nesta revisão |
| Cursos completos e aliases explícitos | `d24d8a5` | Nomes não reconhecidos ficam sem área; preservar normalização e correspondências controladas atuais, sem substring irrestrita |
| Exceção do pré-filtro quando a descrição menciona curso/qualquer formação | `f2d9b21` | Heurística não comprova elegibilidade; manter avaliação posterior |
| Busca geral para cursos desconhecidos, inclusive grupos mistos | `d57c8ad` | Teto de paginação limita cobertura |
| Recálculo de notas em Python com extrações compartilhadas | `fcfc82d` | Não reintroduzir cache de notas; migração de versões futuras da extração é outra decisão |
| Office e idiomas contam fora de computação | `4930d9e` | Exceção histórica de computação e pesos atuais permanecem |
| Auth, confirmação entre aparelhos, controle da conta e entrega inicial | `web/assets/app.js`, funções Supabase, pipeline | Estado remoto requer verificação; não recriar essas funcionalidades |
| Feedback por vaga, abertura e utilidade semanal | `docs/metricas.md` | Candidatura nova não é capturada; ausência de feedback não é aprovação |

Verificação Python na base `40ed28c`: 649 aprovados, 24 ignorados; lint e formatação
aprovados na árvore das correções. Web/banco: 36 aprovados em `a87f9fc`, antes das duas
correções Python; não confundir essa execução com verificação web no SHA final. Isso não substitui testar uma alteração nova.
Os testes Python ignorados dependem de ambiente adicional; não registrar como executados.

## Correções atuais que a fila deve preservar

| Comportamento | Evidência | Verificação relevante |
|---|---|---|
| Sugestões por área já vêm do catálogo único; curso desconhecido usa sugestões gerais atualmente | `Area.habilidades`, `catalogo_do_site`, `montarHabilidadesDoCurso` | `tests/test_areas_do_front.py`, `tests/web/cadastro_test.ts`; C04 descreve somente o restante |
| Termos genéricos não anulam cursos específicos; abertura explícita continua aceita | `c2d6f96` | `tests/test_compatibilidade.py` |
| Nível desconhecido não comprova nível exigido; requisito sem nível aceita habilidade conhecida | `40ed28c` | `tests/test_avaliacoes.py`, `tests/test_formatador.py` |
| Falha de uma extração não descarta sucessos nem repete lote inteiro já processado | `25d5d06` | `tests/test_lotes.py` |
| Busca parcialmente processada não vira aviso de nenhuma vaga compatível | `7a4586e` | `tests/test_pipeline.py` |
| Anúncio entregue a todos é excluído antes da extração; histórico é relido sob trava antes do envio | `48994b4` | `tests/test_pipeline.py` |
| Logout e troca de conta limpam interesses do perfil anterior | `7cf547b` | `tests/web/cadastro_test.ts` |

Detalhes e limites dos cenários: [auditoria datada](auditorias/2026-09-08-expansao-adversarial.md).
C02–C05 devem preservar essas regras. L02 e C06 devem usar a mensagem atual “Requisitos a
conferir no seu perfil”, sem transformar informação ausente em incapacidade comprovada.

## Como pedir a implementação ao Codex

Este é o ponto de entrada único. A divisão em IDs serve para executar mudanças pequenas em
sequência; **não é necessário enviar um prompt por ID**. O Codex deve continuar autonomamente
até terminar o escopo local, preparar os artefatos externos e registrar limitações reais.

Prompt pronto para copiar:

> Leia `docs/plano-expansao-revenue-centric.md` e siga
> `docs/execucao-expansao/00-protocolo.md`. Implemente o plano completo, executando um ID por
> vez na ordem de dependências e continuando automaticamente após cada entrega. Confira o
> código atual para não refazer o que já existe. Preserve as decisões fechadas nas fichas,
> em especial o limite de cinco recomendações para usuários. Teste as mudanças e registre o
> progresso em `docs/execucao-expansao/progresso.md`. Prepare os documentos das tarefas externas
> com evidências disponíveis e explicite o que depende da equipe, sem bloquear as demais.
> Não pare na primeira tarefa nem somente em planejamento. Ao terminar, entregue o resumo de
> implementação, verificações e pendências reais; não declare deploy ou validação sem evidência.

Leia [o protocolo](execucao-expansao/00-protocolo.md) antes de começar. As fichas são o contrato
de cada entrega. O [registro de progresso](execucao-expansao/progresso.md) permite retomar com
contexto novo sem reiniciar a fila. Um pedido explicitamente limitado a um ID continua válido.

## Fila e dependências

P0: funcionamento e compatibilidade. P1: compreensão, cadastro e utilidade. P2: aprendizado,
aquisição e sustentabilidade. “Pronta” significa especificada, não implementada. “Parcial” indica código existente com ajustes definidos na ficha. “Externa”
significa que a conclusão exige evidência/acesso ou decisão da equipe.

| ID | Tarefa | Prioridade | Estado | Depende de | Especificação |
|---|---|---|---|---|---|
| O00 | Restaurar limite de cinco no workflow | P0 | Implementado/testado | — | [Entrega](execucao-expansao/01-landing-e-cadastro.md#o00) |
| C01 | Permitir habilidades vazias no banco | P0 | Implementado/testado | — | [Cadastro](execucao-expansao/01-landing-e-cadastro.md#c01) |
| C02 | Aceitar perfil iniciante no Python | P0 | Implementado/testado | C01 | [Cadastro](execucao-expansao/01-landing-e-cadastro.md#c02) |
| C03 | Oferecer caminho sem habilidades no site | P1 | Implementado/testado | C02 | [Cadastro](execucao-expansao/01-landing-e-cadastro.md#c03) |
| C04 | Concluir sugestões existentes e fallback | P1 | Implementado/testado | C03 | [Cadastro](execucao-expansao/01-landing-e-cadastro.md#c04) |
| C05 | Colocar conta após o perfil | P1 | Implementado/testado | C03 | [Cadastro](execucao-expansao/01-landing-e-cadastro.md#c05) |
| L01 | Corrigir promessa e copy da landing | P1 | Implementado/testado | O00 | [Landing](execucao-expansao/01-landing-e-cadastro.md#l01) |
| L02 | Demonstração fiel e dúvidas frequentes | P1 | Implementado/testado | L01 | [Landing](execucao-expansao/01-landing-e-cadastro.md#l02) |
| C06 | Explicar vínculo, espera e ausência de vagas | P1 | Pronta | — | [Cadastro](execucao-expansao/01-landing-e-cadastro.md#c06) |
| M01 | Mapear eventos e lacunas do cadastro | P1 | Pendente | C05 | [Métricas](execucao-expansao/02-metricas-e-retencao.md#m01) |
| M02 | Participação no feedback | P1 | Pronta | — | [Métricas](execucao-expansao/02-metricas-e-retencao.md#m02) |
| M03 | Tempo até entrega e abertura | P1 | Pronta | — | [Métricas](execucao-expansao/02-metricas-e-retencao.md#m03) |
| M04 | Utilidade por área do curso | P1 | Pendente | M02 | [Métricas](execucao-expansao/02-metricas-e-retencao.md#m04) |
| R01 | Persistir motivo opcional da pausa | P1 | Pronta | — | [Retenção](execucao-expansao/02-metricas-e-retencao.md#r01) |
| R02 | Perguntar motivo após pausar | P1 | Pendente | R01 | [Retenção](execucao-expansao/02-metricas-e-retencao.md#r02) |
| R03 | Relatar motivos de pausa | P1 | Pendente | R02 | [Retenção](execucao-expansao/02-metricas-e-retencao.md#r03) |
| E01 | Verificar publicação e jornada real | P0 | Externa | Versão a publicar definida | [Operação](execucao-expansao/03-evidencias-e-decisoes.md#e01) |
| E02 | Registrar cobertura e casos de qualidade | P1 | Externa | Acesso às fontes/dados | [Cobertura](execucao-expansao/03-evidencias-e-decisoes.md#e02) |
| E03 | Escolher canal e obter prova real | P2 | Externa | E01 | [Aquisição](execucao-expansao/03-evidencias-e-decisoes.md#e03) |
| E04 | Levantar custos da operação | P2 | Externa | Dados de custo disponíveis | [Economia](execucao-expansao/03-evidencias-e-decisoes.md#e04) |
| E05 | Definir oferta e teste de pagamento | P2 | Externa | E02, E04, decisão da equipe | [Economia](execucao-expansao/03-evidencias-e-decisoes.md#e05) |
| D01 | Resolver elegibilidade e formatos acadêmicos | P1 | Decisão | Casos de E02 | [Decisões](execucao-expansao/03-evidencias-e-decisoes.md#d01) |

Sequência obrigatória de implementação local: **O00 → C01 → C02 → C03 → C04 → C05 → L01 →
L02 → C06 → M01 → M02 → M03 → M04 → R01 → R02 → R03**. Depois preparar os seis artefatos
externos. Acesso/decisão ausente não autoriza inventar resultados nem bloqueia outro documento.

## Pontos do plano anterior que mudaram

- A expansão básica e as correções do PR #21 estão concluídas no código; não são o primeiro lote.
- Recálculo atual substitui o pedido genérico de versionar notas. Não invalidar dados ou reenviar vagas.
- Decisão explícita do Igor: usuários recebem até **5** recomendações; **7** era teste local.
  O00 corrige o workflow ainda configurado em sete; L01 comunica até cinco. O parâmetro local
  continua configurável para testes sem alterar o workflow de produção.
- Formações sem semestres, interesses entre grandes áreas e equivalência de cursos precisam de
  contrato específico (D01). Não resolver com defaults inventados ou curso automaticamente equivalente.
- Frequência, pesos por área, fontes novas, páginas por curso, indicação com recompensa e planos
  comerciais ficam condicionados às evidências de E02–E05. Não são trabalho implícito de interface.
- O repositório já está na organização `RadarEstagio/RadarEstagio`; verificar integrações, não refazer transferência.

## Registro de conclusão

Após cada tarefa, atualizar o estado resumido neste índice e os detalhes em
`execucao-expansao/progresso.md`. Estados e condição final são definidos no protocolo.
Preparar um documento externo não equivale a validar seus dados ou publicar uma funcionalidade.

| ID | Commit/arquivos | Verificação executada | Estado externo/limites |
|---|---|---|---|
| Base atual | `40ed28c` | 649 Python; 36 web em `a87f9fc`; ver limites acima | Deploy e utilidade por área não confirmados nesta revisão |
