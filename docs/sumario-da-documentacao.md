# Sumário da documentação

**Retrato de 10/10/2026.** Leitura dos 24 arquivos de documentação do repositório: `CLAUDE.md`,
`README.md`, `CONTEXT.md` e os 21 de `docs/`, inclusive as três auditorias. Datas e números são os
que cada documento registra; este sumário não confere código nem o ambiente remoto, salvo onde
indicado. Não é o documento dono de assunto algum: o estado vigente está no dono de cada tema, no
[índice](README.md). Quando as divergências do fim forem corrigidas nos donos, remova-as daqui.

## Em uma frase

Todo dia às 07:23 (Brasília) o Radar coleta estágios da Adzuna, extrai fatos de cada anúncio com
Gemini, pontua em Python por perfil e entrega até 7 recomendações explicadas no Telegram. Roda em
produção desde 28/08/2026 e é tecnicamente maduro. O que os documentos dizem que falta é prova de
que estudantes de fora do grupo o acham útil.

## Mapa dos documentos

| Documento | O que contém | Estado |
|---|---|---|
| [`CLAUDE.md`](../CLAUDE.md), [`CONTEXT.md`](../CONTEXT.md) | Regras de contribuição e fatos operacionais; vocabulário (ativação operacional × de produto, vaga útil, candidatura declarada) | Vivos. O `CLAUDE.md` voltou a 413 linhas depois de chegar a 2.126 |
| [`README.md`](../README.md), [`docs/README.md`](README.md) | Instalação, CLI e testes; índice com um "documento dono" por assunto | Vivos; 1 trecho defasado no README |
| [`funcionalidades.md`](funcionalidades.md) | Catálogo: 24 itens para quem usa, 22 para operação, comandos, o que não existe | Carimbo de 19/09, com conteúdo até 05/10 |
| [`plano-geral.md`](plano-geral.md) | Fonte única de pendências e decisões | Revisado em 19/09, com hospedagem de 03 a 05/10 |
| [`arquitetura.md`](arquitetura.md) | Camadas, 11 decisões, custo de IA, viés conhecido do ranking | Estável |
| [`decisoes-do-motor.md`](decisoes-do-motor.md) | Por que cada regra de coleta, pré-filtro, nota e mensagem existe, com a medição | O mais recente (09/10); 1.517 linhas |
| [`decisoes-do-banco.md`](decisoes-do-banco.md) | Schema, migrations, webhook, resumo de operação, limites aceitos | Até a `0035` (08/10) |
| [`contrato-front.md`](contrato-front.md) | Contrato site↔banco, D01 em aberto, pós-mortems do site | Até a `0035` (08/10), com nota de 09/10 sobre a atribuição em texto no chat de exemplo |
| [`metricas.md`](metricas.md) | Eventos, denominadores, utilidade semanal, pergunta do dia seguinte | 05/10 |
| [`guia-publicacao-e-piloto.md`](guia-publicacao-e-piloto.md) | Configuração, evidências datadas, reversão, roteiro de teste | 19/09 mais 03 a 08/10 |
| [`termos-de-uso.md`](termos-de-uso.md), [`politica-de-privacidade.md`](politica-de-privacidade.md) | Versão `2026-10-08` | Em vigor desde 08/10 |
| [`pre-prd.md`](pre-prd.md) | Retrato de 08/09: hipóteses H1 a H7, riscos, viabilidade | Congelado de propósito |
| [`pit-do-grupo.md`](pit/pit-do-grupo.md) | Entrega AP1 (IBM3116), medida em 28 e 30/09 | É o que vale para a apresentação |
| [`ideias-icones-3d-das-areas.md`](ideias-icones-3d-das-areas.md) | Proposta de trocar os 12 ícones de linha da landing por ilustrações 3D: objeto por área, prompt-base, arquivos, mudanças no site, 5 decisões do Igor | Em análise (10/10); nada implementado nem decidido |
| [`frentes-externas.md`](frentes-externas.md) | Procedimentos e tabelas com "não medido" | Quase vazios por falta de dado externo |
| [`auditorias/`](auditorias/) (3) | Agendamento (10/09, G01 a G10); Revenue-Centric Design (10/09, 16 achados); acompanhamento de 05/10 | Datadas, não atualizadas |

## Como funciona

- **Fluxo:** fontes → deduplicação → pré-filtro → enriquecimento → extração compartilhada → trava
  por perfil → nota → revalidação do destinatário → Telegram → registro do envio.
- **Decisão central:** a IA só lê o anúncio e devolve fatos, nunca vê o perfil; o Python compara e
  calcula a nota. A nota é determinística e a extração custa por vaga, não por usuário (4
  requisições de IA atenderam 4 usuários em 28/09).
- **Nota (0 a 100):** habilidades 45, período e experiência 15, curso 10, área 10, logística 10,
  interesse 10. Corte de envio em 40. Tetos: curso incompatível ou período abaixo do mínimo 35,
  outro campo 65, outra cidade 30, descrição truncada 60.
- **Infra:** GitHub Actions só com `workflow_dispatch` (o cron-job.org dispara às 07:23 e o vínculo
  do Telegram dispara a primeira busca), Supabase em `sa-east-1` (Postgres, Auth e as Edge
  Functions `ir` e `telegram-webhook`), site estático no Cloudflare Workers em `radarestagio.com`.
  O contrato entre site e motor é o schema do banco.
- **Regras que o código não ensina:** ausência de dado não é veto; não ajustar peso sem
  `vaga_irrelevante` real; falha nova se procura com o teste que a reproduz antes de mexer; o juiz
  automático mede, não ranqueia.
- **Fontes:** só a Adzuna. A Gupy saiu em 12/09 pelos termos; a Jooble está pronta e desligada
  (a chave tem 500 requisições no total).

## Números registrados

| Indicador | Valor | Registro |
|---|---|---|
| Funil do dia | 733 anúncios → 35 candidatas por perfil → 7 entregues | PIT, 28/09 |
| Pessoas recebendo | 4 (6 perfis, 113 visitas em 30 dias) | PIT, 30/09 |
| Abertura de vaga | ~3% (14 aberturas em 535 recomendações, 30 dias) | Auditoria, 05/10 |
| Feedback | 6 respostas em 750 recomendações (0,8%); 1 de fora da equipe | Auditoria, 05/10 |
| Vaga útil ou candidatura | 0 desde 31/08 | Auditoria, 05/10 |
| Cadastro → primeira lista | Mediana de 1,7 min | PIT |
| Custo de extração | R$ 0,066 por lote de 10; ~R$ 14 em 30 dias (estimativa, sem fatura) | Auditoria, 05/10 |
| Banco | 19,3 MB de 500 MB (3,9%), ~0,2 MB por dia | Decisões do banco, 08/10 |
| Testes | 2.020 | PIT |

## O que está aberto

**Antes de divulgar** ([plano geral](plano-geral.md), seção 2):

- No domínio novo, só cadastro e confirmação de e-mail foram confirmados (03/10). O checklist de
  reenvio, recuperação de senha, entrega, feedback e controles da conta segue desmarcado.
- Proteção contra tráfego abusivo no Cloudflare (Bot Fight Mode, limite por IP, alertas) e
  conferência das cotas de Supabase e Resend.
- Forma de pagamento da conta do grupo no Cloudflare (renovação em 04/09/2027), zona antiga na
  conta pessoal, proteção da `main` desligada e 32 branches mescladas para apagar.
- Pedir a colegas que usem, com um `utm_source` por canal.

**Confiabilidade** ([auditoria do agendamento](auditorias/2026-09-10-agendamento-diario.md)):
reexecutar o diário reenvia a todos (G03); não há alerta se o cron não disparar (G04); o token do
cron vence em 09/09/2027. O gabarito humano (20 entregas) segue sem rótulo, então o juiz
automático não está validado (precisa de 75% ou mais de concordância).

**Produto:**

- A pergunta do dia seguinte ("Me candidatei", "Não serviu", "Ainda vou ver"; `0033`) precisa de
  migration, função e código publicados. A leitura da taxa de resposta está marcada para 19/10.
- Dos 16 achados RCD, o plano lista como não implementados: prévia real antes da conta, "Suas
  vagas", retorno no fim do estágio, mensagem com três destaques e frequência semanal.
- ICP do piloto e congelamento do motor sem caso de usuário não têm decisão registrada.
- Ilustrações 3D no lugar dos ícones das áreas: proposta em análise, com 5 decisões do Igor
  pendentes (escopo, ferramenta de imagem, nome visível, tile pastel, carrossel).

**Negócio e externo:**

- Pagador, preço e oferta (E05), cobertura por área (E02, a matriz não tem nenhuma linha real),
  custos (E04, sem faturas), aquisição (E03, nada enviado) e a decisão D01 sobre formação.
- A Adzuna não tem resposta registrada sobre o uso 1 nem sobre ler a página do anúncio. Essa
  leitura alimentou 88% das vagas da Adzuna enviadas entre 05 e 12/09.

## Riscos que os documentos destacam

1. **Sem sinal de utilidade.** Sem `vaga_util` nem candidatura, a nota não pode ser recalibrada e a
   utilidade semanal é 0 por construção. O PIT chama de "o risco que decide o projeto" e diz que
   "não é técnico".
2. **Esforço fora do gargalo.** A auditoria de 05/10 conta 309 commits desde 13/09 (cerca de 87 de
   documentação e 58 de correção do motor) e 2 perfis criados em 25 dias. Nenhum dos 16 achados
   tinha sido tratado naquela data.
3. **Fonte única.** Termos da Adzuna (atribuição, 2.500 requisições por mês, anúncio truncado em
   500 caracteres, vaga encerrada continua listada); uma mudança de termo atinge o serviço inteiro.
4. **Pessoa única.** Igor responde ao contato, lê o resumo diário e paga o domínio. Actions,
   cron-job.org e Supabase estão em contas pessoais.
5. **Modelo de negócio.** O estudante é pagador improvável (CIEE, Nube e alertas dos portais são
   gratuitos para ele). A leitura da Lei do Estágio foi corrigida em 29/09: a vedação do art. 5º,
   §2º alcança agentes de integração e o Radar não é um, então o que limita é o mercado.

## Divergências entre os documentos

Análise por comparação entre os arquivos; o item 6 foi conferido também no código.

1. **Seis × sete opções de feedback.** `funcionalidades.md` (título e lista de "As seis
   respostas"), `plano-geral.md` seção 1 e o guia seção 9 dizem seis. `metricas.md`, `CLAUDE.md`, o
   PIT e o item 14 do próprio catálogo contam sete, com "Vaga encerrada".
2. **Endereço antigo.** O cabeçalho, a seção 3 e a seção 9 do PIT e a mensagem de divulgação de
   `aquisicao-e-prova.md` ainda apontam para `radarestagio.pages.dev` e Cloudflare Pages. Esse
   domínio deixou de resolver em 05/10, e o PIT é o documento da apresentação. Ele também diz em
   aberto a divisão de responsabilidades que o guia registra como combinada em 02/10.
3. **Estado desatualizado.** `funcionalidades.md` ("Estado de disponibilização") ainda lista
   domínio, Turnstile e revisão dos textos como pendentes, e o `README.md` diz que Termos e
   Privacidade "seguem em revisão". O plano e o guia os dão como feitos (03/10 e 02/10, com a
   versão em vigor desde 08/10).
4. **Carimbos de data.** `docs/README.md`, `funcionalidades.md`, `plano-geral.md` e o guia dizem
   "revisado em 19/09", mas trazem material de 03 a 08/10. O último registro remoto é de 19/09 (30
   migrations, até a `0031`). As `0032` a `0035` e os deploys das funções de 05/10 e 08/10 aparecem
   com ordem de publicação, sem registro de que foram aplicados.
5. **Status dos achados RCD em três lugares.** O estado de 13/09 no `plano-geral.md` seção 2.4, a
   tabela de 05/10 (RCD-09 e RCD-14 "abertos") e `funcionalidades.md` e `decisoes-do-banco.md`, que
   já os descrevem como implementados. Não há um quadro único e atual.
6. **Carrossel das áreas.** A ideia 6 de `ideias-icones-3d-das-areas.md` propõe grade estática e
   "carrossel fora", sem dizer que a faixa de hoje já anda: no código há `.areas-marquee` e um laço
   de `requestAnimationFrame` que desacelera e pausa com o ponteiro ou o foco do teclado, como
   registra o `contrato-front.md` (07 e 08/10). A proposta desfaz essa decisão sem citá-la.

O índice manda ter um documento dono por assunto e os demais só linkarem, justamente porque "cópia
de estado diverge". As divergências acima estão nas cópias de estado que ficaram fora dessa regra.
