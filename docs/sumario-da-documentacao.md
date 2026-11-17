# Sumário da documentação

**Retrato de 17/10/2026, atualizado em 22/10.** Visão de conjunto dos documentos do repositório, para não se perder
entre eles. Datas e números são os que cada documento registra. Não é o documento dono de assunto
algum: o estado vigente está no dono de cada tema, listado no [índice](README.md). Quem muda um
dono atualiza a linha dele aqui; divergência encontrada entre documentos entra no fim, até ser
corrigida no dono.

## Em uma frase

Todo dia às 07:23 (Brasília) o Radar coleta estágios da Adzuna, extrai fatos de cada anúncio com
Gemini, pontua em Python por perfil e entrega até 7 recomendações explicadas no Telegram. Roda em
produção desde 28/08/2026 e é tecnicamente maduro. O que os documentos dizem que falta é prova de
que estudantes de fora do grupo o acham útil.

## Mapa dos documentos

| Documento | O que contém | Estado |
|---|---|---|
| [`CLAUDE.md`](../CLAUDE.md) | Regras de contribuição e de operação que um agente precisa seguir | Enxugado em 17/10 para cerca de 200 linhas; o que era relato ou medição foi para os donos. Ganhou em 22/10 o vigia, o segundo disparo e o resumo do raciocínio; o trecho "Fontes" mudou em 16/11 com a Jooble e em 17/11 com o descarte da vaga sem origem |
| [`CONTEXT.md`](../CONTEXT.md) | Vocabulário: ativação operacional × de produto, vaga útil, candidatura declarada | Estável |
| [`README.md`](../README.md) | O que é o projeto, fluxo, tecnologias e a tree de cada área | 16/10; `filtering/` com o corte por origem e `cota.py` com a Jooble em 16/11 |
| [`docs/README.md`](README.md) | Índice, com um documento dono por assunto | 16/10 |
| [`funcionalidades.md`](funcionalidades.md) | Catálogo do que o produto faz para quem usa e para quem opera, e o que não existe | 16/10, com a conferência de 17/10; falhas de entrega em 15/11; corte por origem e Jooble opcional refeita em 16/11; no mesmo dia, páginas da Adzuna não lidas no resumo e `gupy` recusada em `FONTES`; em 17/11, página lida para toda vaga da Adzuna e descarte da sem origem |
| [`plano-geral.md`](plano-geral.md) | Fonte única de pendências e decisões, quadro dos 16 achados RCD, hipóteses H1 a H7 | 16/10, com as conferências de 17 e 22/10; G03, G04 e RCD-15 fechados; ideia do painel por usuário em 26/10 (seção 6); acesso sem login conferido em 15/10 (seção 2.3); pausa sem motivo e `my_chat_member` abertos em 15/11 e limites do corte do emprego.pt e da Jooble em 16/11 (seção 5), revistos no mesmo dia: falha inteira de fonte, duplicata entre fontes, chave e data da Jooble fechadas, e o que era "1 a 2 vagas por dia" trocado pelo que foi contado; Jooble nas pendências externas em 16/11 (seção 4); limites do corte revistos em 17/11 (seção 5) |
| [`arquitetura.md`](arquitetura.md) | Camadas, contratos e 11 decisões técnicas | Estável; as regras do motor são links; o fluxo ganhou o corte por origem em 16/11, também pelo domínio que a Jooble informa; na decisão 9, a fonte que falha inteira entra no resumo, a cópia da Jooble perde na duplicata e `gupy` é recusada em `FONTES`; em 17/11, a vaga da Adzuna sem origem sai junto |
| [`decisoes-do-motor.md`](decisoes-do-motor.md) | Por que cada regra de coleta, pré-filtro, extração, nota e mensagem existe, com a medição | Índice na ordem do pipeline; 1.984 linhas, com o resumo do raciocínio de 19/10, o bot bloqueado de 15/11 e, de 16/11, os anúncios vencidos do emprego.pt e a Jooble (busca enxuta, cota de 100 por dia, corte da Gupy pela origem). Revisto no mesmo dia: o contado separado do estimado no emprego.pt, a medição de base do diário, as páginas não lidas no resumo, a fonte que falha inteira, a duplicata entre fontes e o coletor rodado uma vez contra a API real. Em 17/11, toda vaga da Adzuna com a página lida (a `/land/ad/` em `/details/`) e a sem origem descartada, substituindo a falha aberta |
| [`decisoes-do-banco.md`](decisoes-do-banco.md) | Schema, migrations, webhook, resumo de operação, limites aceitos | Até a `0036` (21/10, dia do atendimento); em 17/11, o trecho da `/land/ad/` passou ao passado |
| [`contrato-front.md`](contrato-front.md) | Contrato site↔banco, D01 em aberto, pós-mortems do site | Até a `0035`, as ilustrações de 15/10 e a landing de 19/10 (pincelada, cartão único de preço, "fase de testes") |
| [`metricas.md`](metricas.md) | Eventos, denominadores, utilidade semanal, pergunta do dia seguinte | 05/10 |
| [`desenvolvimento.md`](desenvolvimento.md) | Instalação, variáveis, comandos da CLI, testes e scripts | Criado em 16/10; Jooble nas variáveis e nos cuidados em 16/11, com `gupy` recusada em `FONTES` |
| [`guia-publicacao-e-piloto.md`](guia-publicacao-e-piloto.md) | Configuração de cada serviço, tabela do estado conferido, roteiro de teste | Supabase e Telegram conferidos em 17/10, migrations em 22/10; dois disparos do cron e vigia desde 21/10; ligar a Jooble por secret e variável em 16/11 (seção 12), sem conferência no GitHub: o passo de conferência diz o que olhar no resumo e no log, e o comportamento da variável no Actions não foi conferido em execução real |
| [`frentes-externas.md`](frentes-externas.md) | Termos das fontes, cobertura (E02), aquisição (E03), custos (E04) e oferta (E05) | Quase tudo "não medido" por falta de dado externo; origem dentro da Adzuna e página do anúncio em 16/11; no mesmo dia, termos da Jooble relidos (100 requisições por dia), duas fontes recusadas (Google for Jobs por raspagem e TheirStack), a medição de base do diário de 16/11 e o coletor da Jooble rodado uma vez contra a API real |
| [`termos-de-uso.md`](termos-de-uso.md), [`politica-de-privacidade.md`](politica-de-privacidade.md) | Versão `2026-10-08`, igual aos HTML de `web/` | Em vigor desde 08/10 |
| [`pit/`](pit/pit-do-grupo.md) | Entrega AP1 (IBM3116), medida em 28 e 30/09, com apresentação, pptx e telas | Endereço corrigido em 16/10; números de setembro; nota de 16/11 sobre o limite de requisições da Jooble |
| [`auditorias/`](auditorias/) (3) | Agendamento (10/09, G01 a G10); Revenue-Centric Design (10/09, 16 achados); acompanhamento de 05/10 | Datadas, não atualizadas |
| [`esclarecimento-da-faxina.md`](esclarecimento-da-faxina.md) | O pedido, o que mudou e as decisões da reorganização de 16 e 17/10 | Registro para a revisão da PR #153 |

## Como funciona

- **Fluxo:** fontes → deduplicação → pré-filtro → enriquecimento → corte por origem → extração compartilhada → trava
  por perfil → nota → revalidação do destinatário → Telegram → registro do envio.
- **Decisão central:** a IA só lê o anúncio e devolve fatos, nunca vê o perfil; o Python compara e
  calcula a nota. A nota é determinística e a extração custa por vaga, não por usuário (4
  requisições de IA atenderam 4 usuários em 28/09).
- **Nota (0 a 100):** habilidades 45, período e experiência 15, curso 10, área 10, logística 10,
  interesse 10. Corte de envio em 40. Tetos: curso incompatível ou período abaixo do mínimo 35,
  outro campo 65, outra cidade 30, descrição truncada 60.
- **Infra:** GitHub Actions só com `workflow_dispatch` (o cron-job.org dispara às 07:23 e às 07:58,
  o vínculo do Telegram dispara a primeira busca e um vigia confere às 09:13 se o diário terminou bem), Supabase em `sa-east-1` (Postgres, Auth e as Edge
  Functions `ir` e `telegram-webhook`), site estático no Cloudflare Workers em `radarestagio.com`.
  O contrato entre site e motor é o schema do banco.
- **Regras que o código não ensina:** ausência de dado não é veto; não ajustar peso sem
  `vaga_irrelevante` real; falha nova se procura com o teste que a reproduz antes de mexer; o juiz
  automático mede, não ranqueia.
- **Fontes:** só a Adzuna. A Gupy saiu em 12/09 pelos termos. Desde 16/11 a vaga que a Adzuna
  recebe do emprego.pt, que mantém com candidatura ativa anúncios brasileiros vencidos, é cortada
  antes da extração: em 15/11 eram 20 das 29 enviadas. A Jooble está pronta e desligada: o limite
  de 500 requisições no total não aparece na documentação da API modificada em 11/11/2026, que dá
  100 requisições por dia; a busca é só "estágio" por região, a vaga com origem na Gupy ou no
  LinkedIn é descartada no coletor, e a fonte liga pela variável `FONTES` do repositório.

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
| Testes | 2.169 em Python, 304 do site e do banco, 85 e 16 das Edge Functions | Suíte local, 22/10 |

## O que está aberto

**Antes de divulgar** ([plano geral](plano-geral.md#2-o-que-falta-antes-de-divulgar)):

- No domínio novo, só cadastro e confirmação de e-mail foram confirmados (03/10). O checklist de
  reenvio, recuperação de senha, entrega, feedback e controles da conta segue desmarcado, assim
  como abrir o site no celular e testar a expiração do Turnstile.
- Proteção contra tráfego abusivo no Cloudflare (Bot Fight Mode, limite por IP, alertas) e
  conferência das cotas de Supabase e Resend.
- Acesso sem login: nada pessoal está exposto, mas ficaram quatro pontos a investigar (duas
  funções sem `revoke`, `sessao_id` livre e teto anônimo esgotável, permissões padrão do Supabase
  e canais públicos do Realtime).
- Forma de pagamento da conta do grupo no Cloudflare (renovação em 04/09/2027), zona antiga na
  conta pessoal e a decisão sobre a proteção da `main`.
- Pedir a colegas que usem, com um `utm_source` por canal.

**Confiabilidade** ([plano geral](plano-geral.md#5-confiabilidade-e-qualidade-do-motor)):
G03 e G04 foram fechados em 21/10: reexecutar o diário pula quem já recebeu a mensagem do dia, e o
vigia avisa se o diário não terminou bem. Seguem abertos G02 (duração de cada lote) e, com
prioridade baixa, G05, G08, G09 e G10. Do bot bloqueado (15/11) ficaram a pausa automática sem
motivo e o webhook sem `my_chat_member`. Do corte do emprego.pt (16/11, revisto em 17/11, quando toda
vaga da Adzuna passou a ter a página lida e a sem origem passou a sair) ficaram a leitura de
`/details/` das vagas `/land/ad/` pelo runner, ainda não confirmada, e o volume diário, que deve
cair; quanto, e se a Jooble repõe, não foi medido.
Da Jooble (16/11) ficaram a busca no país com `location` vazio, aceita numa única execução de
16/11, fora da documentação, e o trecho que não é reconhecido como vaga já enviada pela Adzuna;
a fonte que falha por inteiro passou a aparecer no resumo de operação. O token do cron vence em 09/09/2027. O gabarito humano (20 entregas) segue sem rótulo, então o juiz
automático não está validado (precisa de 75% ou mais de concordância).

**Produto:**

- A pergunta do dia seguinte ("Me candidatei", "Não serviu", "Ainda vou ver") está no ar: a
  `0033` está aplicada e a função, publicada em 08/10. A leitura da taxa de resposta está
  combinada para 19/10.
- Dos 16 achados RCD, o plano lista como não implementados: prévia real antes da conta, "Suas
  vagas", retorno no fim do estágio, mensagem com três destaques e frequência semanal.
- ICP do piloto e congelamento do motor sem caso de usuário não têm decisão registrada.
- Painel de métricas por usuário: três caminhos descritos no
  [plano geral](plano-geral.md#painel-de-métricas-por-usuário-ideia-de-26102026-sem-decisão), sem
  decisão; o recomendado é o HTML local `radar painel`.

**Negócio e externo:**

- Pagador, preço e oferta (E05), cobertura por área (E02, a matriz não tem nenhuma linha real),
  custos (E04, sem faturas), aquisição (E03, nada enviado) e a decisão D01 sobre formação.
- A Adzuna não tem resposta registrada sobre o uso 1 nem sobre ler a página do anúncio. Essa
  leitura alimentou 88% das vagas da Adzuna enviadas entre 05 e 12/09, e desde 16/11 o corte do
  emprego.pt também depende dela.
- A Jooble não está ligada. Faltam a pergunta por escrito à Jooble sobre banco, Telegram e IA,
  que os textos dela não permitem nem proíbem; o secret `JOOBLE_API_KEY` e depois a variável
  `FONTES` no GitHub; e, com a fonte ligada, a medição da cobertura real. Sobre as sondagens de
  16/11, o pré-filtro aprovou 3 vagas de computação, 8 de Direito e 14 de Administração na
  primeira página do Rio em 5 dias, medição parcial. Numa única execução do coletor contra a API
  real, no mesmo dia, com Rio de Janeiro e país, foram 578 vagas únicas, e passaram no pré-filtro,
  para perfis presenciais sintéticos, 6 de Engenharia de Software, 9 de Direito e 17 de
  Administração.

## Riscos que os documentos destacam

1. **Sem sinal de utilidade.** Sem `vaga_util` nem candidatura, a nota não pode ser recalibrada e a
   utilidade semanal é 0 por construção. O PIT chama de "o risco que decide o projeto" e diz que
   "não é técnico".
2. **Esforço fora do gargalo.** A auditoria de 05/10 conta 309 commits desde 13/09 (cerca de 87 de
   documentação e 58 de correção do motor) e 2 perfis criados em 25 dias.
3. **Fonte única.** Termos da Adzuna (atribuição, 2.500 requisições por mês, anúncio truncado em
   500 caracteres, vaga encerrada continua listada); uma mudança de termo atinge o serviço inteiro.
4. **Pessoa única.** Igor responde ao contato, lê o resumo diário e paga o domínio. Actions,
   cron-job.org e Supabase estão em contas pessoais.
5. **Modelo de negócio.** O estudante é pagador improvável (CIEE, Nube e alertas dos portais são
   gratuitos para ele). A leitura da Lei do Estágio foi corrigida em 29/09: a vedação do art. 5º,
   §2º alcança agentes de integração e o Radar não é um, então o que limita é o mercado.

## Divergências entre os documentos

Nenhuma aberta em 17/10. As seis do retrato de 10/10 (opções de feedback, endereço antigo, estado
desatualizado, carimbos, estado dos achados RCD e carrossel das áreas) foram corrigidas nos donos;
o que mudou em cada uma está no [esclarecimento da faxina](esclarecimento-da-faxina.md#as-seis-divergências-do-sumário).
Divergência nova entra aqui, com os documentos envolvidos, e sai quando o dono for corrigido.
