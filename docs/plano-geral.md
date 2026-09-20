# Plano geral

**Revisado em 19/09/2026** contra o código da `main` e, no Supabase, contra o histórico de
migrations e a lista de funções publicadas. A expansão para diferentes áreas foi autorizada em
08/09 e as entregas locais de cadastro, landing, métricas e pausa (O00–R03) estão concluídas.
Validação com estudantes e decisões externas continuam pendentes de evidência.

Este é o acompanhamento atual do projeto. O plano formal de piloto foi retirado por decisão
do Igor: não há obrigação de recrutar uma coorte, realizar cinco entrevistas, calcular D7
ou cumprir metas de pesquisa antes de divulgar. As métricas existentes continuam disponíveis.

## 1. O que já está feito

- **Expansão local concluída:** limite de sete recomendações, cadastro com perfil antes da
  conta, caminho explícito sem habilidades, sugestões conforme o curso, demonstração
  ilustrativa e FAQ, estados de vínculo sem promessa de busca já executada, participação no
  feedback, medianas observadas, utilidade por área e motivo opcional após a pausa.
  Contratos nas migrations `0017`–`0019`.

- **Cadastro e conta:** formulário em etapas, confirmação entre aparelhos, reenvio, recuperação
  de senha, edição de perfil, consentimento e preferência de e-mails.
- **Controle dos dados:** pausa, retomada, desvínculo, exportação, exclusão com carência de
  60 dias e cancelamento. As 30 migrations, da `0001` à `0031` — a numeração pula a `0029` —,
  constam como aplicadas no `supabase migration list --linked` de 19/09.
- **Telegram:** vínculo por token de uso único, recomendações explicadas e feedback com seis
  opções. Pelo `supabase functions list` de 19/09, `ir` foi republicada em 10/09 e
  `telegram-webhook` em 16/09; o código no ar não foi comparado de novo com o repositório.
- **Primeira entrega:** dispatch por perfil, com exceção entre 06:23 e 07:23 de Brasília.
  Teste registrado de vínculo até mensagem em cerca de quatro minutos; não é garantia de prazo.
- **Concorrência:** trava por perfil e releitura do histórico, testadas com duas conexões.
  Telegram e banco continuam sendo operações separadas.
- **Coleta e ranking:** Adzuna por padrão (Gupy desligada pelos termos), extração de fatos compartilhada, nota em Python,
  deduplicação e personalização v1 por recusas. Jooble pronto, mas desligado por padrão.
- **Mensagens:** listas longas resumidas; desde 09/09, habilidades desejáveis ausentes aparecem
  como “Diferenciais que a vaga cita”, separadas dos requisitos a conferir e sem virar veto.
- **Métricas:** funil, vagas abertas distintas, utilidade semanal e recusas com denominadores.
  Abertura com token real e relatório foram conferidos; falta confirmar o teste de feedback do Igor.
- **Contato e e-mail:** `contato@radarestagio.com` com recebimento confirmado; Resend verificado
  e SMTP salvo. Confirmação e recuperação reais pelo site ainda precisam de teste registrado.
- **Confiabilidade e produto, de 14 a 18/09:** trinta PRs fecharam falhas que derrubavam o
  diário inteiro ou escondiam vagas — erro inesperado de um usuário, resposta malformada do
  Gemini, texto que o Postgres recusa, coleta incompleta, extração com id de outra vaga, listas
  do perfil em mais de uma dimensão — e o código de saída da execução deixou de ficar verde
  quando ninguém recebeu mensagem. Entraram também a pergunta sobre deficiência (`0026`), o
  feedback "Vaga encerrada", o prazo do cadastro que não confirma o e-mail (`0030`) e a
  navegação da conta no celular. O porquê de cada uma está nas
  [decisões do motor](decisoes-do-motor.md) e no `CLAUDE.md`.

Migrations e funções foram conferidas em 19/09. As demais evidências remotas são de 05–06/09
e estão no [guia](guia-publicacao-e-piloto.md); esta revisão não refez esses testes.

## 2. O que falta antes de divulgar

### 1. Confirmar onde o site está publicado

- [x] Confirmado em 09/09 que `radarestagio.pages.dev` serve os arquivos do `main`
  ([guia](guia-publicacao-e-piloto.md)); falta a conta Cloudflare e a forma de publicação.
- [ ] Definir o endereço público final e conferir HTTPS, início, Termos e Privacidade.
      `radarestagio.com` ainda não resolve por HTTP: só tem MX, e os textos legais já apontam
      para ele.
- [ ] Confirmar se mudanças na `main` atualizam o frontend automaticamente. O pré-PRD registrou
      que sim em 08/09 e o check "Cloudflare Pages" roda em cada pull request, mas o deploy de
      produção a partir da `main` não foi conferido.

A conversa sobre publicação no Pages não confirma que ela terminou. Por isso, o estado aqui
é **a confirmar**, e não “não hospedado em lugar nenhum”. O domínio continua na conta do Igor;
a transferência para `RadarEstagio/RadarEstagio` foi confirmada em 08/09 e o PR #21 foi
integrado à main. A configuração de cada automação ainda deve ser verificada. Combinar acesso e administração sem compartilhar senhas.

### 2. Conectar o endereço ao cadastro

- [x] Site URL corrigido para o endereço publicado em 09/09, depois do cadastro de ponta a
      ponta ter caído em `radarestagio.com` ([guia](guia-publicacao-e-piloto.md), seção 5).
- [ ] Trocar a `URL_DA_LANDING` provisória pelo endereço escolhido.
- [ ] Configurar Turnstile no frontend e no Supabase e testar o desafio; hoje
      `turnstileSiteKey` está vazio e o captcha do Auth está desligado.

Não reaplicar as migrations já registradas nem republicar funções só para repetir etapas
concluídas. Se o código ou o repositório mudar, atualizar as integrações afetadas.

### 3. Testar com uma conta da equipe

- [ ] Cadastro, confirmação, reenvio e recuperação de senha.
- [ ] Vínculo, entrega de recomendações, abertura e feedback positivo/negativo.
- [ ] Edição, pausa/retomada, exportação, exclusão e cancelamento.

Para feedback, usar envio persistido no banco: `testar-local` gera tokens que o webhook não
encontra. `rodar --perfil` recebe `perfis.id` e exige `DATABASE_URL` configurada para atender
um perfil real. Não colocar essa conexão no frontend. Anotar os erros encontrados e corrigir
os bloqueadores antes de convidar outras pessoas.

### 4. Concluir os textos e combinar a manutenção

- [ ] Igor, Ian e Miguel revisarem Termos e Política e resolverem as passagens pendentes.
- [ ] Definir versão/vigência e sincronizar Markdown e páginas HTML.
- [ ] Combinar quem responde ao contato, acompanha falhas e paga a renovação do domínio.

As páginas seguem como rascunhos até essa revisão; a implementação não aprova os textos.

### 5. Pedir para alguns colegas usarem

- [ ] Enviar o site quando o fluxo estiver funcionando.
- [ ] Perguntar onde travaram, se alguma vaga serviu e se as mensagens ficaram claras.
- [ ] Anotar problemas concretos e escolher o próximo ajuste com a equipe.

Sem quantidade mínima, roteiro obrigatório de entrevista, prazo de duas semanas ou metas
formais. Consultar as métricas quando ajudarem a entender um problema; não é necessário criar
um dashboard ou novas consultas para começar essa conversa.

## 2.1 Rodada de confiabilidade (10/09/2026)

Uma revisão externa apontou defeitos no núcleo do produto, e eles foram corrigidos com teste
que reproduz cada falha. O detalhe operacional está no [CLAUDE.md](../CLAUDE.md); a decisão de
arquitetura, em [arquitetura.md](arquitetura.md). Em resumo: fronteira de transação, identidade
da vaga por fonte e id, deduplicação que preserva cidade, prompt preservando o nível da
habilidade, recusa corrigida deixando de penalizar, negação no pré-filtro de experiência, falha
temporária de entrega não pausando conta, travessão no nome do curso, suítes rodando em pull
request e versão fixa do cliente supabase.

O que essa rodada deliberadamente não fez, e continua pendente:

- **Pesos da nota.** A regra de não recalibrar sem `vaga_irrelevante` real continua valendo. O
  que mudou foi a explicação: perfil sem habilidade cadastrada agora recebe um aviso na
  mensagem em vez de uma nota alta sem ressalva.
- **Detectar execução ausente.** Se o cron externo não disparar, nada avisa: o passo
  `if: failure()` do workflow só cobre execução que começou. Falta escolher onde esse alerta
  mora, e a opção mais simples é o próprio cron-job.org avisar por e-mail quando falhar.
- **Rotular os descartes.** `python -m radar descartes` já exporta a amostra com o motivo, mas
  ninguém preencheu `descarte_correto` ainda. Sem isso, continuamos medindo só a qualidade do
  que foi entregue.
- **Preencher o gabarito humano.** As 20 entregas do primeiro gabarito (em `gabaritos/`, fora do Git) seguem com
  `relevante` nulo, então o juiz automático ainda não foi validado.
- **Frontend em um arquivo só.** `web/assets/app.js` passa de 1.500 linhas com estado
  compartilhado; a recomendação dessa revisão foi separar responsabilidades sem trocar de
  framework. A migração para React foi descartada em 13/09; ver a seção 2.3.

## 2.2 Auditoria do agendamento diário (10/09/2026)

A auditoria está em
[auditorias/2026-09-10-agendamento-diario.md](auditorias/2026-09-10-agendamento-diario.md), com
dez achados numerados e o histórico real das execuções. O disparo externo é confiável: 13 de 13
dias no horário desde 28/08. O risco está no que acontece depois dele. Estado conferido no código
em 19/09:

- **G01 e G07 — resolvidos no PR #57.** Prazo da extração (`PRAZO_DA_EXTRACAO_SEGUNDOS`), timeout
  por chamada, candidatas intercaladas por usuário e timeouts de 30 min no job e 28 no passo.
- **G06 — resolvido.** O run por perfil coleta só para os usuários que vai atender.
- **G03 — aberto: não reenviar a quem já foi atendido no dia.** A consulta dos usuários ativos
  não filtra quem já recebeu hoje, então reexecutar o diário manda segunda mensagem a todos. A
  #68 cobre só a entrega imediata (`entrega_imediata_atendida_em`). Sem essa marca não existe
  recuperação segura depois de uma falha parcial nem agendador de reserva. Exige migration.
- **G04 — aberto: detectar execução ausente**, o mesmo item da rodada de confiabilidade acima.
- **G02 — aberto: registrar o fim de cada lote com a duração.** A omissão de vagas pelo modelo
  foi identificada em 11/09; falta a duração por lote para medir o raciocínio `low`.
- **G05, G08, G09 e G10 — abertos, prioridade baixa.** O G10 é o mais visível: falha do disparo
  da primeira busca só aparece no log da Edge Function.

## 2.3 Migração do frontend para React (12/09/2026)

**Estado: descartada em 13/09/2026.** O site continua em JavaScript puro, sem build: o
Cloudflare Pages segue servindo `web/` direto e correções do cadastro e da conta vão no
`app.js`.

A migração chegou a ser feita e testada. O plano (#62) e o script de build compatível (#64)
entraram na `main` e saíram depois da decisão; a #66 (Vite, lint, Vitest e CI) e a #67
(cadastro, autenticação e conta em React) foram fechadas sem merge. Motivos: na Fase 2 a prioridade é validar com
estudantes e o estudante não via diferença (24 de 28 telas idênticas pixel a pixel), enquanto o
custo era real: 156 KB de JavaScript e CSS com gzip contra 84 KB, uma pilha Node/npm para manter,
troca do build no Pages e cada correção do `app.js` refeita em dobro até o merge.

Retomar só se surgirem telas interativas grandes, como o painel web de métricas.

## 2.4 Auditoria Revenue-Centric Design (10/09/2026)

A auditoria está em
[auditorias/2026-09-10-revenue-centric-design.md](auditorias/2026-09-10-revenue-centric-design.md),
com 16 achados e um plano em nove passos (seção 7). Nenhum achado virou tarefa até 13/09. Estado
conferido no código nessa data, para a equipe decidir o que entra:

- **Textos que prometem mais que a prova (RCD-08, 14, 15 e 16), correção de minutos.** A landing
  diz "100% automático" e "Vagas que atendem seu perfil"; a faixa de prova é "ADZUNA GEMINI
  TELEGRAM"; o bot promete vagas "todos os dias de manhã"; a última etapa do cadastro diz "Comece
  pela sua conta", com progresso que começa em 0%; o cartão de preço diz "A definir"; "Sobre"
  leva ao CTA final.
- **Mensagem livre ao bot (RCD-09).** Recebe resposta automática e não chega à equipe.
- **Feedback sem sinal (RCD-01).** A pergunta continua no fim da mensagem ("Deixe seu feedback
  👇"), sem "Me candidatei"; candidatura segue sem emissor.
- **Distribuição sem origem (RCD-04).** A visita não guarda `referrer` nem `utm_source`, e as
  sessões da equipe entram no funil.
- **Não implementados (RCD-05, 06, 07, 12 e 13):** prévia com vagas reais antes da conta,
  "Suas vagas" na conta, retorno perto do fim do estágio, mensagem com três destaques e
  frequência semanal como alternativa à pausa.
- **Pagador (RCD-02).** Restrição da Lei do Estágio registrada na
  [hipótese comercial](hipotese-comercial.md) em 13/09; consulta jurídica e conversas com
  possíveis pagadores pendentes.
- **Foco (RCD-03 e RCD-10).** Congelar ajuste de regra do motor sem caso vindo de usuário e
  definir o ICP do piloto são decisões da equipe, ainda sem registro.

## 3. Limitações e decisões que continuam valendo

- **Candidatura:** acontece na fonte; o Radar não se candidata e não captura novas candidaturas.
- **Feedback:** última resposta conta nas métricas, mas pode haver eventos brutos repetidos e
  perguntas simultâneas. Mensagem enviada sem gravação pode deixar token órfão.
- **Histórico:** exclusões definitivas podem alterar métricas de semanas passadas.
- **Ranking:** a v1 usa repetição e recusas de área. Os outros motivos não mudam pesos
  automaticamente; investigar exemplos antes de recalibrar.
- **IA:** reuso reduz trabalho repetido; novos anúncios, cidades e áreas podem exigir extrações.
- **Fora do trabalho imediato:** cobrança, plano formal de pesquisa, D7, campanhas de e-mail
  e exclusão automática por abandono. Medianas de entrega e abertura já estão implementadas;
  são tempos observados, não promessa de prazo. Monetização permanece uma hipótese futura.
- **Jooble:** ativação opcional, com chave e configuração próprias; não bloqueia a divulgação.
- **Histórico Git e skills:** permanecem conforme decisões registradas em 05/09. Não há nova
  autorização para reescrever histórico ou remover recursos de terceiros.

## 4. Pendências externas da expansão

Os IDs abaixo são referências históricas. Atualizar o estado geral aqui e a evidência no
documento indicado; não manter uma segunda fila no antigo registro de execução.

| Frente | Estado e próximo passo | Documento responsável |
|---|---|---|
| E01 — publicação e jornada | Conferir versões, migrations, deploy automático, Auth, SMTP, CAPTCHA, cron e jornada com conta da equipe; inspecionar 375 px e 1280 px | [Guia](guia-publicacao-e-piloto.md) |
| E02 — cobertura | Escolher janela, acesso e responsável; coletar amostra e separar erro técnico, desconhecido e descarte legítimo | [Cobertura](cobertura-estagios.md) |
| E03 — aquisição | Após verificar a jornada, confirmar canal, URL, responsável e mensagem; obter autorização antes de divulgar relato | [Aquisição e prova](aquisicao-e-prova.md) |
| E04 — custos | Reunir faturas, uso e horas de suporte em uma janela comum; custos desconhecidos não são zero | [Custos](custos-operacao.md) |
| E05 — oferta | Após cobertura e custos, decidir oferta, pagador, preço, duração, renovação, cancelamento, aceite e provedor; checkout é tarefa posterior | [Hipótese comercial](hipotese-comercial.md) |
| D01 — formação | Usar casos de cobertura para decidir escala acadêmica, correlatos, aliases e cursos fora do catálogo; preservar contrato atual até decisão | [Contrato](contrato-front.md#elegibilidade-acadêmica--decisão-d01-em-aberto) |

Os responsáveis continuam a confirmar; a proposta de divisão está na seção 2 do guia.
E02–E05/D01 não criam metas formais nem impedem o piloto informal depois da conferência
operacional. Não há autorização de cobrança ou disparo de mensagens implícita nesta fila.

## 5. Onde consultar os detalhes

- [Funcionalidades](funcionalidades.md): o que usuários e desenvolvedores podem fazer.
- [Guia de publicação](guia-publicacao-e-piloto.md): configuração e evidências datadas.
- [Cadastro e privacidade](contrato-front.md): decisões dessa frente.
- [Revisão dos textos](guia-publicacao-e-piloto.md#2-revisar-os-documentos-e-combinar-a-manutenção): pendências dos responsáveis.
- [Métricas](metricas.md): definições e limites das consultas existentes.
- [Arquitetura](arquitetura.md) e [contrato frontend](contrato-front.md): implementação.
- [Índice](README.md): documentos mantidos. O histórico dos planos antigos está no Git.
