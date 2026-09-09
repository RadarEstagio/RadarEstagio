# Radar de Estágio — Documento de Definição (Pré-PRD)

> Revisão de 08/09/2026. Este documento foi retirado do repositório em 07/09 na consolidação da
> documentação e volta aqui como registro de definição, hipóteses e evidências para a disciplina.
> Não é o catálogo de funcionalidades nem o backlog: para isso, ver
> [funcionalidades](funcionalidades.md), [plano geral](plano-geral.md) e
> [plano de expansão](plano-expansao-revenue-centric.md). A versão de 02/09/2026 está no Git.

**Status:** base técnica viável e publicada; produto ampliado para qualquer curso; validação com
estudantes ainda não começou

**Atualizado em:** 08/09/2026

**Entrega anterior:** 02/09/2026 (prova técnica entregue). Próxima entrega: a combinar com o professor

**Disciplina:** Métodos e Aplicações de IA (IBM3116), turma 8001

**Professor:** Alvaro Riz

**Integrantes:** Igor Costa, Ian Dias e Miguel Esteves

## 1. Objetivo do documento

Este documento antecede o PRD. Seu objetivo não é transformar toda ideia em requisito, mas
permitir que o grupo decida, com base em evidências, se o Radar de Estágio é viável e qual
produto merece ser especificado depois da validação.

Ele deve servir para:

- tirar dúvidas sobre problema, público, solução, matching, canal e operação;
- separar fatos comprovados de hipóteses e decisões ainda abertas;
- tornar vulnerabilidades visíveis antes que gerem custo ou invalidem a proposta;
- listar oportunidades sem incorporá-las automaticamente ao escopo;
- pedir a priorização das características realmente pertinentes ao problema;
- avaliar viabilidade técnica, financeira, operacional, de prazo, privacidade e produto;
- definir quais evidências autorizam o avanço para um PRD completo.

### 1.1 Como interpretar as afirmações

| Classificação | Significado |
| --- | --- |
| **Comprovado** | Existe código, teste automatizado, execução real ou dado observável. |
| **Parcialmente comprovado** | A base existe, mas falta repetição, volume ou usuário externo. |
| **Hipótese** | É uma expectativa que ainda precisa de teste. |
| **Decisão aberta** | O grupo precisa escolher uma regra antes de medir ou desenvolver. |

O princípio central continua sendo **prova antes de promessa**: cadastro, quantidade de
funcionalidades e volume coletado não demonstram valor sozinhos. O primeiro sinal observável de
valor ocorre quando o estudante abre uma recomendação, e a utilidade só se confirma com feedback
positivo ou candidatura. O vocabulário desses marcos está em [`CONTEXT.md`](../CONTEXT.md).

## 2. Resumo executivo e veredito

O Radar de Estágio reduz o trabalho diário de estudantes que procuram o primeiro estágio. O
sistema coleta vagas da Adzuna e da Gupy, elimina duplicatas e incompatibilidades evidentes,
extrai os fatos de cada anúncio com IA uma única vez, compara as oportunidades com o perfil do
estudante por regras determinísticas e entrega pelo Telegram uma lista curta, ranqueada e
explicada.

O que mudou desde 02/09:

- **O produto deixou de ser só para computação.** Em 08/09 o catálogo de áreas passou a ser a
  fonte única para curso, vaga, banco e site: 12 áreas (computação, direito, administração,
  finanças, marketing, pessoas, comercial, logística, engenharias, saúde, educação e turismo),
  45 subáreas de interesse, 105 nomes de curso reconhecidos e 120 habilidades sugeridas no
  cadastro. A landing, o cadastro, o pré-filtro, a busca nas fontes, o prompt e a nota seguem o
  mesmo catálogo.
- **O site está publicado** em `https://radarestagio.pages.dev` (Cloudflare Pages), com deploy
  automático a partir da `main`. O repositório foi transferido para a organização
  `RadarEstagio/RadarEstagio` em 08/09, com as automações religadas.
- **O ciclo completo está implementado e em operação:** conta, perfil, vínculo com o Telegram,
  primeira entrega logo após o vínculo, entrega diária às 07:23, link rastreado, feedback com
  seis respostas, edição, pausa, desvínculo, exportação e exclusão da conta com arrependimento.
- **Duas revisões adversariais** (08/09, à tarde e ao fim da tarde) encontraram e corrigiram
  nove falhas no motor: perdas no pré-filtro, viés de TI no prompt, cota do Gemini derrubando
  a execução, nível "básico" satisfazendo requisito "avançado", mensagem de "nenhuma vaga
  compatível" enviada com extração pela metade, entre outras. Cada correção entrou com um teste
  que reproduzia a falha antes de corrigir.

Em 08/09/2026 a suíte tem **638 testes passando, 24 ignorados** sem PostgreSQL de teste e **36
testes de interface** em Deno. As migrations `0001` a `0017` estão registradas como aplicadas no
banco remoto.

O banco de produção, consultado em 08/09, tem 2 perfis ativos (os do próprio grupo, ambos de
computação), 415 vagas guardadas, 202 extrações, 304 avaliações e 154 recomendações entregues
em 12 dias consecutivos, de 28/08 a 08/09. Nenhum estudante externo ao grupo se cadastrou
ainda.

### Veredito atual

> **O Radar é viável como MVP acadêmico e está pronto para o piloto informal. Ainda não está
> comprovado como produto de uso recorrente, e a expansão para outros cursos ainda não foi
> testada com um único estudante desses cursos.**

O piloto formal (coorte, cinco entrevistas, D7) foi retirado em 07/09 por decisão do Igor. A
elaboração de um PRD completo continua dependendo de quatro provas ausentes:

1. cobertura útil das fontes durante vários dias, agora **por área** e não só para computação;
2. concordância aceitável entre o ranking e o julgamento de estudantes das áreas novas;
3. ativação operacional de usuários externos até a primeira recomendação;
4. ativação de produto e ação útil após a entrega, como abertura, feedback positivo ou
   candidatura.

## 3. Problema, público e limite da proposta

### 3.1 Problema

Procurar estágio exige acompanhamento frequente de diferentes portais. Muitos anúncios não
combinam com curso, período, habilidades, localização ou modalidade do estudante, e as melhores
oportunidades podem fechar rapidamente.

O estudante repete três trabalhos:

1. procurar vagas em fontes diferentes;
2. eliminar anúncios irrelevantes;
3. interpretar requisitos para escolher onde investir atenção.

As consequências esperadas são tempo perdido, candidaturas tardias e abandono da rotina de
busca. A frequência e a intensidade dessas dores ainda precisam ser confirmadas com estudantes
externos ao grupo.

### 3.2 Público

- universitários no Brasil, de qualquer curso coberto pelo catálogo de 12 áreas;
- em busca do primeiro estágio;
- com perfil mínimo de curso, período, habilidades, cidade e modalidade;
- dispostos a testar o Telegram como canal de entrega.

A ampliação de público foi autorizada em 08/09 pelo [plano de expansão](plano-expansao-revenue-centric.md).
Curso fora do catálogo continua sendo atendido: recebe busca geral, títulos genéricos ("Programa
de Estágio") e nota parcial de curso, sem ser descartado. Trainee, vagas júnior, bolsas,
expansão internacional e recrutadores seguem fora.

### 3.3 Trabalho que o produto pretende resolver

> "Mostre, sem eu precisar procurar todos os dias, quais vagas recentes merecem minha atenção e
> explique por quê."

O Radar não se candidata pelo estudante, não garante contratação, não substitui os portais e não
é um chatbot genérico. Sua proposta de valor é a combinação de recorrência, filtro, ranking
explicável e entrega proativa.

## 4. Hipótese central e promessas

Se um estudante informar seu perfil uma vez e o Radar monitorar vagas, remover oportunidades
incompatíveis, explicar a compatibilidade e notificá-lo proativamente, então ele gastará menos
tempo procurando e poderá se candidatar mais cedo às vagas relevantes.

| Promessa | O que precisa ser observado | Situação em 08/09 |
| --- | --- | --- |
| Economia de tempo | Tempo de busca antes e depois ou relato consistente de redução | Hipótese |
| Relevância | Proporção de recomendações julgadas úteis | Mensurável (feedback no Telegram); zero respostas até agora |
| Velocidade | Intervalo entre publicação, entrega e abertura | Mensurável; entrega após vínculo observada em ~4 min em 05/09 |
| Confiança | Compreensão da nota e concordância com a justificativa | Não validada externamente |
| Recorrência | Retorno ou permanência no serviço após a primeira entrega | Mensurável (utilidade semanal); sem denominador externo |

## 5. Solução definida para o MVP

### 5.1 Experiência desejada

O usuário cria uma conta, informa curso, período, cidade, modalidade, habilidades e subáreas de
interesse da sua área, e vincula o Telegram. O Radar executa diariamente e entrega até sete
vagas novas com nota igual ou superior ao limite configurado. Cada vaga contém:

- título, empresa, localização, modalidade, fonte e data;
- nota de compatibilidade de 0 a 100;
- requisitos atendidos e não informados, pontos a favor e contra gerados da comparação;
- alerta de possível inconsistência quando a IA a detecta;
- link rastreado para a oportunidade e um teclado numerado para dar feedback.

Produção envia até **7 vagas** (workflow desde 03/09; o padrão do código é 5) com nota mínima
**40**, ambos configuráveis; a landing passou a prometer "até sete" em 08/09. Em dia sem vaga
adequada, o estudante recebe um aviso curto; após 7 dias seguidos sem recomendação, o mesmo
aviso ganha um parágrafo sugerindo ampliar cidade ou modalidade.

### 5.2 Jornada e definição de ativação

```text
landing → cadastro → perfil → confirmação de e-mail → Telegram vinculado
        → primeira entrega (minutos) → entrega diária → vaga aberta → vaga útil ou candidatura
```

Os dois marcos seguem [`CONTEXT.md`](../CONTEXT.md): **ativação operacional** é a primeira
recomendação entregue (`perfis.ativado_em`); **ativação de produto** é a primeira abertura de uma
vaga recomendada, registrada pela Edge Function `ir`. Conta criada, formulário concluído e Telegram
vinculado são etapas necessárias, mas não representam nenhum dos dois marcos.

O funil está instrumentado da landing ao feedback. `python -m radar metricas` imprime, direto do
banco, aquisição, coorte, utilidade semanal, recusas por motivo e custo de extração; as
definições estão em [`metricas.md`](metricas.md).

### 5.3 Escopo implementado

Catálogo completo em [funcionalidades](funcionalidades.md). Em resumo:

- coleta combinada de Adzuna e Gupy, tolerando falha parcial; Jooble pronto e desligado;
- busca dirigida pelos termos das áreas dos cursos cadastrados, somada a uma busca geral quando
  algum curso não é reconhecido; Adzuna com 10 páginas por região;
- deduplicação dentro da coleta, entre fontes e contra republicações dos últimos 30 dias;
- pré-filtro determinístico por área do curso antes da IA, com precedência documentada;
- extração de fatos por vaga, compartilhada entre todos os usuários e guardada com versão do
  prompt; Gemini API no CI e Antigravity em testes locais;
- nota calculada em Python, recalculada em toda execução; a IA não decide nota;
- mensagem ranqueada no Telegram, link rastreado, feedback com seis respostas e personalização
  v1 por recusas ("já vi essa" e "não é da minha área");
- cadastro web em etapas com catálogo de áreas por curso, confirmação entre aparelhos, reenvio,
  recuperação de senha, consentimento e preferência de e-mails;
- edição, pausa e retomada, desvínculo, exportação, exclusão com carência de 60 dias e
  cancelamento;
- primeira entrega disparada pelo vínculo; execução diária disparada externamente;
- resumo de operação de cada execução no chat da equipe, incluindo vagas sem extração;
- múltiplos usuários com trava por perfil e revalidação do destinatário antes do envio.

### 5.4 Ainda não disponível

- painel web de métricas (o relatório é por linha de comando);
- captura de candidatura (acontece na fonte);
- campanha de e-mails opcionais;
- domínio próprio no site (o `radarestagio.com` recebe só o e-mail de contato);
- Turnstile ativo (integração pronta, inerte sem chave);
- Jooble em produção;
- textos legais aprovados pelos responsáveis.

## 6. Definição do matching

A IA interpreta a descrição e devolve fatos estruturados: área e subáreas da vaga, cursos
aceitos, habilidades obrigatórias, principais e desejáveis, período, experiência, modalidade e
alerta de pegadinha. O Python aplica a fórmula:

\[
N = 45H + 10C + 10A + 15P + 10L + 10I
\]

Em que cada fator varia de 0 a 1:

- **H — habilidades:** cobertura dos requisitos explícitos da vaga;
- **C — curso:** incompatível, parcial ou compatível;
- **A — área:** área da vaga comparada com a área do curso;
- **P — período/experiência:** incompatível, parcial ou compatível;
- **L — logística:** média de localização e modalidade;
- **I — interesse:** subáreas da vaga comparadas com as escolhidas no perfil.

Regras vigentes em 08/09:

- **Cobertura suavizada**, `(1+atendidas)/(1+exigidas)`: requisito ausente do perfil vale como
  incerteza, nunca como veto. Vaga sem stack declarada recebe cobertura neutra de 0,35.
- Obrigatórias, principais e desejáveis têm pesos distintos dentro de H (80/20 quando há
  obrigatórias e desejáveis; 60/30/10 quando há as três).
- **Nível declarado precisa cobrir o exigido** (08/09): "Inglês básico" não atende "Inglês
  fluente" nem "Excel básico" atende "Excel avançado". O nome é comparado sem o qualificador.
  Requisito sem nível aceita a habilidade conhecida; requisito com nível exige que o perfil
  declare o seu: "Excel" no perfil não comprova "Excel avançado". Por isso a mensagem chama a
  lista de "Requisitos a conferir no seu perfil", e não de requisitos não atendidos.
- Idiomas e pacote Office ficam fora da cobertura **só para perfis de computação**; nas demais
  formações contam como qualquer requisito.
- Tecnologias comparadas por nome normalizado e exato (Java ≠ JavaScript).
- **Curso**: incompatível limita a 35 (sai da mensagem); parcial limita a 75. Quem decide é o
  catálogo: cursos da mesma área só são equivalentes onde a área declara
  `cursos_intercambiaveis` (só computação). Curso genérico aceito pelo anúncio ("Engenharia")
  vale para o curso específico do perfil ("Engenharia Civil"). Só abertura explícita a qualquer
  formação ("qualquer curso", "todos os cursos") libera todo mundo; termo vago como "Ensino
  Superior" não comprova elegibilidade sozinho nem anula os cursos específicos que o anúncio cita.
- **Interesse** tem três níveis: subárea marcada vale cheio; outra subárea do mesmo campo vale
  metade e não avisa; vaga de outro campo zera, limita a 65 e avisa. Perfil sem interesses não
  é penalizado. Subárea com duas ou mais recusas "não é da minha área" em 30 dias perde o fator.
- Vaga presencial ou híbrida para perfil remoto tem nota limitada a 30.
- Vaga com descrição incompleta (fonte truncada) tem nota limitada a 60.

O histórico das calibrações de 31/08 (cobertura neutra, remoção das travas de 60/70) está na
versão anterior deste documento e em [`arquitetura.md`](arquitetura.md), junto com o viés
conhecido: anúncio que declara uma tecnologia só tira 100 quando é atendido. Nenhum peso foi
alterado por opinião; a regra é não ajustar sem `vaga_irrelevante` real.

## 7. Arquitetura e operação atuais

| Componente | Uso | Evidência ou ressalva |
| --- | --- | --- |
| Python e uv | Pipeline, regras e ambiente reproduzível | 638 testes passando, 24 ignorados sem PostgreSQL |
| Deno | Testes do cadastro (DOM simulado) e Edge Functions | 36 testes de interface |
| Adzuna | Fonte oficial de vagas | API autenticada; 4.988 vagas disponíveis pelos termos das 12 áreas (08/09) |
| Gupy | Segunda fonte | Endpoint público interno, sem garantia contratual |
| Jooble | Terceira fonte, desligada | Sondagem de 05/09: +19 vagas inéditas no Rio (~35%) |
| Gemini API (`gemini-3.6-flash`) | Extração de fatos no Actions | Cota gratuita de 20 requisições/min; incidente às 16:13 de 08/09 |
| Antigravity (`agy`) | Extração local para desenvolvimento | Não disponível no Actions |
| Telegram Bot API | Entrega, feedback e resumo de operação | 154 entregas reais em 12 dias |
| PostgreSQL/Supabase | Perfis, vagas, extrações, avaliações, envios e eventos | `0001`–`0017` aplicadas e conferidas com `migration list` |
| Edge Functions `ir` e `telegram-webhook` | Link rastreado, vínculo, feedback e primeira entrega | Publicadas em 05/09; `REPOSITORIO` atualizado na transferência |
| Cloudflare Pages | Site em `radarestagio.pages.dev` | Deploy automático a partir da `main`, confirmado em 08/09 |
| Resend/SMTP | E-mails de confirmação e recuperação | Domínio verificado; fluxo real ainda sem teste registrado |
| GitHub Actions | Execução do pipeline | Só `workflow_dispatch`; limite de 15 minutos |
| cron-job.org | Disparo diário às 07:23 BRT | Token fine-grained da organização; **vence em 09/09/2027** |

O agendamento nativo do GitHub deixou de executar durante dois dias e foi removido; o disparo
externo resolve, mas é uma dependência a mais. A transferência para a organização mostrou que
cada automação guardava o dono no nome: cron, Edge Function e Cloudflare tiveram que ser
religados um a um.

## 8. Evidências e lacunas

### 8.1 Comprovado

| Fato | Evidência (08/09/2026) |
| --- | --- |
| Entrega diária funciona sem intervenção | 154 recomendações em 12 dias consecutivos (28/08–08/09), todas pelo disparo das 07:23 ou pelo vínculo |
| Primeira entrega após o vínculo | ~4 minutos do `/start` à mensagem, sem requisição de IA (05/09) |
| Abertura rastreada | 6 eventos `vaga_aberta` reais; redirecionamento 302 validado com token |
| Extração compartilhada não cresce com usuários | 202 extrações servem os dois perfis; teste `test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas` |
| Cobertura ampliada por área | Rio com quatro áreas: 699 vagas coletadas contra ~400; cada curso ganhou de 65% a 120% mais candidatas (08/09) |
| Pré-filtro não perde título legítimo | Zero títulos com marcador forte da própria área perdidos nos dados reais após a precedência nova |
| Controle dos dados | Edição, pausa, desvínculo, exportação, exclusão e cancelamento implementados e testados |
| Cadastro por qualquer curso | Áreas e habilidades sugeridas montadas pelo catálogo; site e Python aplicam a mesma normalização de curso |
| Landing recebe visitas | 30 sessões nos últimos 30 dias, 5 abriram o cadastro |

### 8.2 Parcialmente comprovado

- funil completo até a primeira recomendação: só com os 2 perfis do grupo;
- cobertura das áreas novas: medida em quantidade de candidatas, não em relevância julgada;
- matching fora de computação: testado com perfis sintéticos de direito, administração,
  economia, engenharia civil, química e outros, em dados reais, mas sem julgamento humano;
- feedback: mecanismo validado tecnicamente, **zero respostas** registradas;
- primeira entrega após a transferência da organização: ainda não reexecutada com vínculo real.

### 8.3 Ainda não comprovado

- que o problema é frequente e importante para estudantes externos ao grupo;
- que Adzuna e Gupy entregam vagas relevantes na maioria dos dias **em cada área**;
- que a nota concorda com estudantes das áreas novas (as listas de habilidades por área foram
  escritas pelo grupo e não passaram por revisão de quem é da área);
- que o Telegram é aceito como canal de uso recorrente;
- que usuários concluem cadastro e vínculo sem ajuda;
- que recomendações geram abertura ou candidatura;
- que a cota gratuita do Gemini sustenta a primeira execução com muitas áreas: em 09/09 o cache
  de extração recomeça do zero pela mudança de prompt.

## 9. Hipóteses e testes de baixo custo

O piloto é informal: os limites abaixo não são metas obrigatórias, e sim sinais combinados para
ler os resultados sem escolher um critério conveniente depois. Com pouco volume, observação e
conversa produzem sinal melhor que teste A/B.

| Hipótese | Teste mínimo | Sinal proposto |
| --- | --- | --- |
| H1 — A busca manual é uma dor relevante | Conversar com colegas que usaram por uma semana | A maioria relata busca repetitiva e quer delegar a triagem |
| H2 — O matching orienta a triagem | 20 vagas por área, avaliadores da área sem ver a nota | Concordância de ao menos 75% com a decisão majoritária |
| H3 — As fontes têm cobertura útil por área | Ler o resumo diário por 7 dias com perfis de áreas distintas | Ao menos 1 recomendação relevante em 5 de 7 dias por perfil |
| H4 — Telegram é um canal aceitável | Colegas vinculam o bot e recebem uma entrega | Quase todos concluem sem considerar o canal uma barreira |
| H5 — A entrega gera ação útil | 2 semanas com link rastreado e feedback | Metade abre uma vaga; parte sinaliza "essa serviu" |
| H6 — A operação cabe nos limites | Resumo de cada execução (duração, requisições, vagas sem extração) | 6 de 7 execuções sem falha permanente e dentro de 15 minutos |
| H7 — A expansão não degrada computação | Comparar entregas dos perfis de computação antes e depois de 08/09 | Recusas "não é da minha área" não sobem |

## 10. Dúvidas e decisões

### 10.1 Já respondidas pela implementação

| Dúvida | Resposta atual |
| --- | --- |
| Dia sem vaga: mensagem ou silêncio? | Mensagem curta; após 7 dias, com sugestão de ampliar preferências. Se alguma candidata ficou sem extração, silêncio, porque a conclusão seria falsa. |
| A nota mínima 40 é adequada? | Mantida; nenhuma recusa real para revisar. |
| A mesma régua serve para todas as áreas? | Sim, com o catálogo decidindo curso, área e interesse; a única regra específica é a exclusão de Office/idiomas em computação. |
| Clique e feedback entram ou são simulados? | Implementados: link rastreado e seis respostas no Telegram. |
| Qual política para editar, pausar e excluir? | Tudo pelo site; exclusão com 60 dias de carência e cancelamento. |
| Como evitar repetição entre dias? | Histórico de envios e comparação com republicações dos últimos 30 dias. |
| A extração cresce com os usuários? | Não: uma extração por vaga, compartilhada e guardada com versão do prompt. |
| O produto é só para computação? | Não mais: 12 áreas desde 08/09, por decisão registrada no plano de expansão. |
| Monetização? | Planejamento futuro (P2); o piloto continua gratuito. |

### 10.2 Decisões ainda abertas

1. Habilitar billing no Gemini ou aceitar a cota gratuita, sabendo que a primeira execução com
   muitas áreas pode estourar 20 requisições por minuto e deixar vagas sem extração?
2. Ligar a Jooble em produção (+35% de cobertura no Rio, descrição curta) ou esperar sinal de
   falta de vaga em alguma área?
3. Quem da área revisa as listas de habilidades sugeridas e as subáreas de cada uma das 11 áreas
   novas?
4. Domínio próprio para o site ou manter `pages.dev` durante o piloto?
5. Textos de termos e privacidade: quem aprova, e com que vigência?
6. Quem responde o `contato@`, acompanha o resumo diário e renova domínio e token do cron?
7. Ativar o Turnstile antes de divulgar?
8. Quais evidências o professor espera na próxima entrega: arquitetura, demonstração, métricas
   ou validação com estudantes?
9. O plano de expansão do Igor (tarefas O00 e L01) previa reduzir a produção para cinco; Ian
   decidiu em 08/09 manter sete e alinhar a landing. Confirmar com o Igor e ajustar o plano.

## 11. Vulnerabilidades e riscos

| Vulnerabilidade | Impacto | Situação em 08/09 | Mitigação ou decisão necessária |
| --- | --- | --- | --- |
| Cota gratuita do Gemini | Alto | Estouro real às 16:13 de 08/09: 0 de 36 vagas extraídas | Espera e repetição do mesmo lote, resumo denuncia "vagas sem extração"; decidir billing (10.2.1) |
| Reextração total em 09/09 | Alto | Cache versionado por prompt recomeça do zero | Acompanhar o resumo das 07:23; vagas sem extração voltam no dia seguinte |
| Matching errado nas áreas novas | Alto | Sem julgamento humano; nove falhas corrigidas por revisão adversarial | H2 por área e revisão das listas por quem é da área |
| Cobertura irregular por área | Alto | Medida em quantidade, não em relevância | H3 com perfis de áreas distintas |
| Mudança no endpoint da Gupy | Alto | Risco permanente | Coletor isolado; Adzuna continua sozinha |
| Job exceder 15 minutos | Médio | Mais áreas e 10 páginas por região aumentam a coleta | Medir duração no resumo; reduzir páginas se necessário |
| Token do cron vencer | Alto | Vence em 09/09/2027; o radar para sem aviso | Registrar renovação com antecedência |
| Não observar ação após a mensagem | Alto | Feedback implementado, zero respostas | Convidar colegas e ler o relatório |
| Abandono entre site e Telegram | Alto | 5 aberturas de cadastro para 2 contas, todas do grupo | Observar colegas cadastrando |
| Vagas expiradas ou enganosas | Médio | Fonte e data visíveis; alerta de pegadinha | Feedback "a nota não fez sentido" |
| Republicação por outra fonte com descrição curta | Baixo | Sabido, não corrigido | Aceitar até aparecer caso real |
| Banco aceita subárea de outro curso | Baixo | Mitigado ao carregar o perfil | Validar no banco quando houver tempo |
| Dependência de serviços gratuitos | Médio | Adequado ao piloto | Registrar custo por execução no resumo |
| Crescimento de escopo | Alto | Plano de expansão tem 9 frentes | Aplicar o filtro da seção 12 |

## 12. Oportunidades e características pertinentes

Toda característica nova gera custo de manutenção, suporte, documentação, privacidade e carga
cognitiva. Antes de aprová-la, o grupo deve responder:

1. Ela reforça diretamente a promessa de encontrar vagas relevantes mais cedo?
2. Ela reduz uma incerteza importante deste documento?
3. Existe um teste manual ou menor que produza a mesma evidência?
4. Qual é o custo permanente, além do desenvolvimento inicial?
5. Qual item atual pode ser adiado para abrir espaço?

Das oportunidades listadas em 02/09, entraram: link rastreado, feedback, mensagem de dia sem
vagas, editar perfil, pausar e retomar, excluir conta. As que continuam abertas:

| Característica | Problema ou hipótese atendida | Menor versão útil | Recomendação atual |
| --- | --- | --- | --- |
| Convidar colegas de outros cursos | Valida a expansão (H2, H3, H7) | Enviar o site para 3–5 pessoas de áreas distintas | Aprovar agora |
| Revisão das listas por área | Reduz erro de matching nas áreas novas | Uma pessoa de cada área lê subáreas e habilidades | Aprovar agora |
| Jooble em produção | Cobertura em dias fracos | Ligar por variável de ambiente | Só se H3 falhar em alguma área |
| Motivo opcional da pausa | Separa saída por sucesso de insatisfação | Uma pergunta ao pausar | Adiar até haver pausas reais |
| Histórico de vagas para o estudante | Recuperar oportunidades | Lista das últimas recomendações | Adiar até H5 |
| Páginas de landing por área | Aquisição segmentada | Exemplos por área na mesma página | Adiar até haver demanda |
| Alertas instantâneos | Reduz tempo até candidatura | Regra para notas muito altas | Adiar |
| Lacunas de competências | Planejamento de estudos | Resumo de requisitos recorrentes ausentes | Adiar |
| Painel web de métricas | Leitura sem terminal | Relatório atual já responde | Adiar |
| Oferta paga | Sustentabilidade | Frente P2 do plano de expansão | Só após evidência de utilidade |
| Aplicação automática | Remove decisão e amplia riscos | — | Rejeitar |
| Scraping do LinkedIn | Volume com risco de bloqueio | — | Rejeitar |

## 13. Análise de viabilidade

| Dimensão | Avaliação | Evidência | Condição restante |
| --- | --- | --- | --- |
| Técnica | **Favorável** | Ciclo completo em produção há 12 dias; expansão implementada com catálogo único | Acompanhar a primeira execução com reextração total |
| Financeira | **Favorável no piloto** | Serviços gratuitos suportam o volume; custo não cresce com usuários | Decidir billing do Gemini antes de ampliar áreas ativas |
| Operacional | **Favorável com ressalvas** | Automação, resumo diário e alertas de vagas sem extração | Observar 7 dias após a expansão; renovação de token registrada |
| Prazo | **Favorável** | Entrega de 02/09 realizada; expansão e publicação concluídas em 08/09 | Combinar a próxima entrega |
| Privacidade | **Favorável** | Token de uso único, RLS, exportação e exclusão implementadas | Aprovar os textos legais |
| Produto | **Inconclusiva** | Só o grupo usa; zero feedback; nenhum perfil fora de computação | Colegas de áreas distintas usando por uma semana |

### 13.1 Decisão de continuidade

O projeto continua como **piloto informal com expansão de público**, conforme decidido em
07–08/09. Não deve ser declarado produto validado antes de estudantes externos, de mais de uma
área, receberem recomendações e responderem ao feedback.

### 13.2 Critérios para avançar ao PRD

- a execução das 07:23 concluir por 7 dias após a expansão sem vagas sem extração persistentes;
- ao menos um perfil externo em três áreas diferentes ativado operacionalmente;
- feedback real registrado (positivo ou negativo) em número suficiente para ler as recusas por
  motivo;
- H2 aplicado em pelo menos duas áreas fora de computação;
- listas de subáreas e habilidades revisadas por pessoas das áreas;
- decisões 1, 5 e 6 da seção 10.2 tomadas;
- os critérios acadêmicos da próxima entrega confirmados.

Se cobertura, confiança ou um dos marcos de ativação falhar em alguma área, o resultado não é
"construir tudo": o grupo deve identificar a causa, testar a menor correção possível e reavaliar.

## 14. Próximos passos

1. **09/09, 07:23:** ler o resumo da primeira execução com o cache zerado; conferir requisições,
   duração e "vagas sem extração".
2. **Igor e Miguel:** apontar a cópia local para `RadarEstagio/RadarEstagio`; retestar a primeira
   entrega vinculando um Telegram real.
3. **Antes de divulgar** ([plano geral](plano-geral.md#2-o-que-falta-antes-de-divulgar)):
   conferir Site URL e redirects do Auth, decidir o Turnstile, testar cadastro, confirmação e
   recuperação com conta da equipe, revisar termos e privacidade.
4. **Convidar colegas** de ao menos três áreas distintas; anotar onde travaram e se alguma vaga
   serviu.
5. **Revisar as listas** de subáreas e habilidades por área com quem é da área.
6. **Decidir** billing do Gemini e Jooble com os dados da primeira semana.
7. **Próxima entrega:** apresentar a expansão, as evidências da seção 8 e as hipóteses ainda
   abertas, sem apresentar prova técnica como validação de produto.

## 15. Perguntas prioritárias para a próxima reunião

1. A conclusão "viável e publicado, produto ainda não validado, expansão ainda não testada com
   ninguém das áreas novas" representa o entendimento do grupo?
2. Quem convida colegas de quais áreas, e até quando?
3. Billing do Gemini: aceitar vagas sem extração em dias de pico ou pagar?
4. Quem revisa subáreas e habilidades de cada área?
5. Quais três evidências serão mostradas ao professor na próxima entrega?
6. Domínio próprio, Turnstile e textos legais entram antes de divulgar?
7. Qual risco impediria a continuidade para o PRD?

---

**Síntese final:** a implementação demonstra viabilidade técnica, operacional e de prazo, com o
ciclo completo em produção e o produto aberto a qualquer curso. A decisão de produto permanece
condicionada a estudantes externos, de mais de uma área, receberem recomendações relevantes,
abrirem vagas e responderem ao feedback.
