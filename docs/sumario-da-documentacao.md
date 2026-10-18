# Sumário da documentação

**Retrato de 17/10/2026.** Visão de conjunto dos documentos do repositório, para não se perder
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
| [`CLAUDE.md`](../CLAUDE.md) | Regras de contribuição e de operação que um agente precisa seguir | Enxugado em 17/10 para cerca de 200 linhas; o que era relato ou medição foi para os donos |
| [`CONTEXT.md`](../CONTEXT.md) | Vocabulário: ativação operacional × de produto, vaga útil, candidatura declarada | Estável |
| [`README.md`](../README.md) | O que é o projeto, fluxo, tecnologias e a tree de cada área | 16/10 |
| [`docs/README.md`](README.md) | Índice, com um documento dono por assunto | 16/10 |
| [`funcionalidades.md`](funcionalidades.md) | Catálogo do que o produto faz para quem usa e para quem opera, e o que não existe | 16/10, com a conferência de 17/10 |
| [`plano-geral.md`](plano-geral.md) | Fonte única de pendências e decisões, quadro dos 16 achados RCD, hipóteses H1 a H7 | 16/10, com a conferência de 17/10 |
| [`arquitetura.md`](arquitetura.md) | Camadas, contratos e 11 decisões técnicas | Estável; as regras do motor são links |
| [`decisoes-do-motor.md`](decisoes-do-motor.md) | Por que cada regra de coleta, pré-filtro, extração, nota e mensagem existe, com a medição | Índice na ordem do pipeline; 1.583 linhas |
| [`decisoes-do-banco.md`](decisoes-do-banco.md) | Schema, migrations, webhook, resumo de operação, limites aceitos | Até a `0035` (08/10) |
| [`contrato-front.md`](contrato-front.md) | Contrato site↔banco, D01 em aberto, pós-mortems do site | Até a `0035` e as ilustrações de 15/10 |
| [`metricas.md`](metricas.md) | Eventos, denominadores, utilidade semanal, pergunta do dia seguinte | 05/10 |
| [`desenvolvimento.md`](desenvolvimento.md) | Instalação, variáveis, comandos da CLI, testes e scripts | Criado em 16/10 |
| [`guia-publicacao-e-piloto.md`](guia-publicacao-e-piloto.md) | Configuração de cada serviço, tabela do estado conferido, roteiro de teste | Supabase e Telegram conferidos em 17/10 |
| [`frentes-externas.md`](frentes-externas.md) | Termos das fontes, cobertura (E02), aquisição (E03), custos (E04) e oferta (E05) | Quase tudo "não medido" por falta de dado externo |
| [`termos-de-uso.md`](termos-de-uso.md), [`politica-de-privacidade.md`](politica-de-privacidade.md) | Versão `2026-10-08`, igual aos HTML de `web/` | Em vigor desde 08/10 |
| [`pit/`](pit/pit-do-grupo.md) | Entrega AP1 (IBM3116), medida em 28 e 30/09, com apresentação, pptx e telas | Endereço corrigido em 16/10; números de setembro |
| [`auditorias/`](auditorias/) (3) | Agendamento (10/09, G01 a G10); Revenue-Centric Design (10/09, 16 achados); acompanhamento de 05/10 | Datadas, não atualizadas |
| [`esclarecimento-da-faxina.md`](esclarecimento-da-faxina.md) | O pedido, o que mudou e as decisões da reorganização de 16 e 17/10 | Registro para a revisão da PR #153 |

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
| Testes | 2.127 em Python, 304 do site e do banco, 85 e 16 das Edge Functions | Suíte local, 17/10 |

## O que está aberto

**Antes de divulgar** ([plano geral](plano-geral.md#2-o-que-falta-antes-de-divulgar)):

- No domínio novo, só cadastro e confirmação de e-mail foram confirmados (03/10). O checklist de
  reenvio, recuperação de senha, entrega, feedback e controles da conta segue desmarcado, assim
  como abrir o site no celular e testar a expiração do Turnstile.
- Proteção contra tráfego abusivo no Cloudflare (Bot Fight Mode, limite por IP, alertas) e
  conferência das cotas de Supabase e Resend.
- Forma de pagamento da conta do grupo no Cloudflare (renovação em 04/09/2027), zona antiga na
  conta pessoal e a decisão sobre a proteção da `main`.
- Pedir a colegas que usem, com um `utm_source` por canal.

**Confiabilidade** ([plano geral](plano-geral.md#5-confiabilidade-e-qualidade-do-motor)):
reexecutar o diário reenvia a todos (G03); não há alerta se o cron não disparar (G04); o token do
cron vence em 09/09/2027. O gabarito humano (20 entregas) segue sem rótulo, então o juiz
automático não está validado (precisa de 75% ou mais de concordância).

**Produto:**

- A pergunta do dia seguinte ("Me candidatei", "Não serviu", "Ainda vou ver") está no ar: a
  `0033` está aplicada e a função, publicada em 08/10. A leitura da taxa de resposta está
  combinada para 19/10.
- Dos 16 achados RCD, o plano lista como não implementados: prévia real antes da conta, "Suas
  vagas", retorno no fim do estágio, mensagem com três destaques e frequência semanal.
- ICP do piloto e congelamento do motor sem caso de usuário não têm decisão registrada.

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
