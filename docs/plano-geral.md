# Plano geral

**Revisado em 16/10/2026** contra o código da `main` e o GitHub; migrations, Edge Functions e
webhook do Telegram conferidos em 17/10, só leitura. O Cloudflare e o cron-job.org não foram
reconsultados nesta revisão. É a fonte única de
pendências e decisões da equipe; os outros documentos linkam aqui em vez de repetir estado.

O plano formal de piloto foi retirado por decisão do Igor em 07/09: não há obrigação de recrutar
uma coorte, fazer cinco entrevistas, calcular D7 ou cumprir metas de pesquisa antes de divulgar.

## 1. O que já está feito

- **Produto para qualquer curso** (expansão de 08/09): 12 áreas, cadastro com perfil antes da
  conta, caminho sem habilidades, sugestões conforme o curso, até sete recomendações,
  demonstração ilustrativa e FAQ.
- **Cadastro e conta:** formulário em etapas, confirmação entre aparelhos, reenvio, recuperação
  de senha, edição, consentimento, preferência de e-mails, pausa com motivo opcional, retomada,
  desvínculo, exportação e exclusão com 60 dias para desfazer.
- **Telegram:** vínculo por token de uso único, recomendações explicadas, feedback com sete
  opções e, desde 05/10, a pergunta do dia seguinte e a mensagem livre encaminhada à equipe.
- **Primeira entrega:** disparo por perfil ao vincular, exceto entre 06:23 e 07:23 de Brasília;
  a marca de atendido só é gravada depois da mensagem.
- **Coleta e ranking:** Adzuna (Gupy desligada pelos termos em 12/09, Jooble pronto e desligado),
  extração compartilhada por vaga, nota em Python e personalização v1 por recusas.
- **Confiabilidade:** as falhas que derrubavam o diário inteiro ou escondiam vagas, de 08 a
  18/09 e da auditoria de 07/10, foram fechadas com o teste que as reproduz; o porquê de cada uma
  está nas [decisões do motor](decisoes-do-motor.md) e nas [do banco](decisoes-do-banco.md).
- **Métricas:** funil da visita à primeira recomendação, visitas por origem (`0032`, 05/10),
  utilidade semanal e por área e recusas com denominador.
- **Endereço e hospedagem:** `radarestagio.com` no Cloudflare Workers, na conta do grupo, desde
  03/10; Site URL e Redirect URLs do Auth e `URL_DA_LANDING` apontam para ele; o Pages antigo foi
  apagado em 05/10. Os cabeçalhos de segurança do `web/_headers` estão no ar (conferido com
  `curl -I` em 16/10).
- **Turnstile** no cadastro, login, reenvio e recuperação, ligado em 03/10.
- **Textos legais:** Termos e Política revisados por Igor, Ian e Miguel em 02/10, em vigor na
  versão `2026-10-08`. Responsabilidades combinadas em 02/10: Igor responde o contato, lê o
  resumo diário e paga o domínio ([guia](guia-publicacao-e-piloto.md#responsabilidades-combinadas-02102026)).
- **Contato:** `contato@radarestagio.com` recebe; Resend verificado e SMTP salvo.
- **Ilustrações das áreas:** os ícones da faixa viraram ilustrações 3D em 14/10, trocadas por um
  set verde em 15/10 ([contrato frontend](contrato-front.md#hero-lado-a-lado-e-faixa-de-áreas-07102026)).
- **Frontend sem React:** a migração foi feita, testada e descartada em 13/09. O site segue em
  JavaScript puro, sem build; motivos na seção 6.

## 2. O que falta antes de divulgar

### 2.1 Conferir o que foi publicado

Conferido em 17/10 com o CLI do Supabase, só leitura; o resultado está no
[guia](guia-publicacao-e-piloto.md#estado-conferido):

- [x] Migrations `0032` (origem da visita), `0033` (pergunta do dia seguinte), `0034` (grants e
  formato da `pagina`) e `0035` (confirmação e sessões do apagamento) aplicadas.
- [x] `telegram-webhook` e `ir` publicadas em 08/10, com o código igual ao da `main`, e o secret
  `TELEGRAM_CHAT_ID` criado no Supabase.
- [ ] Abrir o site no celular (HTTPS, início, Termos e Privacidade).
- [ ] Testar a expiração do desafio do Turnstile.

### 2.2 Testar com uma conta da equipe

- [x] Cadastro e confirmação do e-mail no domínio novo (Igor, 03/10).
- [ ] Reenvio da confirmação e recuperação de senha.
- [ ] Vínculo, entrega de recomendações, abertura e feedback positivo e negativo.
- [ ] Edição, pausa e retomada, exportação, exclusão e cancelamento.
- [x] Resposta do bot a um Telegram já vinculado a outra conta: diz onde fica "Desvincular o
  Telegram" e o que fazer depois (05/10, `835cfe0`).

Para o feedback, usar envio persistido no banco: `testar-local` gera tokens que o webhook não
encontra. `rodar --perfil` recebe `perfis.id` e exige `DATABASE_URL`. O roteiro completo está no
[guia](guia-publicacao-e-piloto.md#10-conferência-final-com-conta-de-teste). Anotar os erros e
corrigir os bloqueadores antes de convidar outras pessoas.

### 2.3 Proteger o site e o cadastro contra tráfego abusivo

Motivo (03/10/2026): um site alheio em plano gratuito recebeu 126 milhões de requisições para 973
visitas, 99% com erro 4xx, e a hospedagem pausou por estourar o plano. Bot não escolhe o alvo, e
a chave pública do Supabase está no `web/config.js`.

- [x] Turnstile no cadastro e no Auth (03/10).
- [ ] Cloudflare: ligar o Bot Fight Mode e criar uma regra de limite de requisições por IP; o
  Under Attack Mode fica como botão de emergência.
- [ ] Notificações do Cloudflare para pico de tráfego, e conferir em Workers & Pages → Usage que
  os arquivos estáticos não consomem a cota de 100.000 execuções por dia.
- [ ] Supabase: conferir plano, teto de gasto e uso das Edge Functions, principalmente a `ir`,
  que é pública por natureza.
- [ ] Resend: conferir o limite diário de e-mails, para um cadastro em massa não travar a
  confirmação de quem é real.
- [ ] CSP que restringe carregamento, publicada antes como `Content-Security-Policy-Report-Only`
  (o porquê de ter ficado de fora está no [guia](guia-publicacao-e-piloto.md#cabeçalhos-de-resposta-do-site-08102026)).

### 2.4 Contas, CI e branches

- [ ] Apagar a zona antiga na conta pessoal do Igor, depois de ela aparecer como "Moved", e pôr
  forma de pagamento na conta do grupo para a renovação de 04/09/2027.
- [x] O check "Cloudflare Pages" sumiu: o PR #152 (15/10) só tem Workers Builds, `python` e `web`.
- [ ] Decidir sobre a proteção da `main`, ainda desligada em 16/10: exigir os checks `python` e
  `web` antes de mesclar.
- [x] As 63 branches remotas já mescladas foram apagadas e "Automatically delete head branches"
  foi ligado (17/10). Ficaram as dos PRs abertos e as dos fechados sem merge (#42 e #128), que
  têm commits fora da `main`.
- [ ] Renovar o token do cron-job.org antes de 09/09/2027: vencido, o diário para sem avisar.

### 2.5 Pedir para alguns colegas usarem

- [ ] Enviar o site com um `utm_source` por grupo ou canal
  ([frentes externas](frentes-externas.md#e03--aquisição-e-prova-de-utilidade)).
- [ ] Perguntar onde travaram, se alguma vaga serviu e se as mensagens ficaram claras.
- [ ] Anotar problemas concretos e escolher o próximo ajuste com a equipe.

Sem quantidade mínima, roteiro obrigatório de entrevista, prazo ou metas formais.

## 3. Produto: os achados da auditoria Revenue-Centric Design

Quadro único do estado dos 16 achados, conferido no código em 16/10. A
[auditoria de 10/09](auditorias/2026-09-10-revenue-centric-design.md) e o
[acompanhamento de 05/10](auditorias/2026-10-05-revenue-centric-design.md) são retratos datados e
não são atualizados.

| ID | Achado | Estado em 16/10 |
|---|---|---|
| RCD-01 | Feedback sem sinal | Pergunta do dia seguinte com "Me candidatei", no ar com a `0033` e a função de 08/10 (2.1). Falta ler a taxa de resposta, combinada para 19/10 ([métricas](metricas.md#pergunta-do-dia-seguinte)) |
| RCD-02 | Sem pagador | Leitura da Lei do Estágio corrigida em 29/09; nenhuma conversa com pagador |
| RCD-03 | Esforço fora do gargalo | Aberto; congelar regra do motor sem caso de usuário é decisão da equipe, sem registro |
| RCD-04 | Visita sem origem, equipe no funil | Origem no código desde 05/10 (`0032`); marcar as contas da equipe é proposta sem decisão ([decisões do banco](decisoes-do-banco.md#contas-da-equipe-fora-do-funil-proposta-de-05102026)) |
| RCD-05 | Valor só depois de três trocas de contexto | Aberto: não há prévia com vagas reais antes da conta |
| RCD-06 | Conta sem nada acumulado | Aberto: não há "Suas vagas" na conta |
| RCD-07 | Trabalho episódico | Aberto: não há retorno perto do fim do estágio |
| RCD-08 | Promessa maior que a prova | Parcial: saíram "100% automático", a faixa de fornecedores e o "todos os dias de manhã" do bot; a lista de diferenciais do hero ainda diz "Vagas que atendem seu perfil" (`web/index.html`) |
| RCD-09 | Bot responde "use o botão do site" a tudo | Feito: a mensagem livre é encaminhada ao chat de operação, na função publicada em 08/10 (2.1) |
| RCD-10 | ICP difuso | Sem decisão registrada |
| RCD-11 | Nada diferencia de um alerta gratuito | Aberto |
| RCD-12 | Mensagem densa | Aberto: não há mensagem com três destaques |
| RCD-13 | Só existe pausar tudo | Aberto: não há frequência semanal |
| RCD-14 | Progresso em 0% e "Comece pela sua conta" | Feito em 05/10 (`35816a0`): progresso a partir de 20% e "Último passo: crie sua conta para ativar seu Radar" |
| RCD-15 | Cartão "A definir" | Aberto: o cartão "Depois do piloto" segue com "A definir" (`web/index.html`) |
| RCD-16 | "Sobre" leva ao CTA final | Aberto: o item do menu aponta para `#sobre`, que é o CTA final |

## 4. Pendências externas

Os IDs vêm do plano de expansão de 08/09 e servem de referência. Estado aqui, evidência no
documento indicado.

| Frente | Estado e próximo passo | Documento responsável |
|---|---|---|
| E01 — publicação e jornada | Seção 2: testar com conta da equipe, a expiração do Turnstile e inspecionar 375 px e 1280 px | [Guia](guia-publicacao-e-piloto.md) |
| E02 — cobertura | Escolher janela, acesso e responsável; coletar amostra e separar erro técnico, desconhecido e descarte legítimo | [Frentes externas](frentes-externas.md#e02--cobertura-de-estágios) |
| E03 — aquisição | Depois da jornada verificada, confirmar canal, responsável e mensagem; obter autorização antes de divulgar relato | [Frentes externas](frentes-externas.md#e03--aquisição-e-prova-de-utilidade) |
| E04 — custos | Reunir faturas, uso e horas de suporte numa janela comum; custo desconhecido não é zero | [Frentes externas](frentes-externas.md#e04--custos-da-operação) |
| E05 — oferta | Depois de cobertura e custos, decidir oferta, pagador, preço e provedor; checkout é tarefa posterior | [Frentes externas](frentes-externas.md#e05--hipótese-comercial) |
| D01 — formação | Usar os casos de cobertura para decidir escala acadêmica, correlatos, aliases e cursos fora do catálogo | [Contrato](contrato-front.md#elegibilidade-acadêmica--decisão-d01-em-aberto) |
| Adzuna | Sem resposta registrada ao e-mail que pede confirmação do uso 1, aprovação da atribuição em texto e permissão para ler a página do anúncio, que alimentou 88% das vagas enviadas de 05 a 12/09. Se a leitura for recusada, o enriquecimento sai | [Decisões do motor](decisoes-do-motor.md#enriquecimento-a-descrição-completa-da-adzuna) |

Nenhuma dessas frentes cria meta formal nem impede o piloto informal depois da conferência
operacional. Não há autorização de cobrança ou disparo de mensagens implícita nesta fila.

## 5. Confiabilidade e qualidade do motor

Da [auditoria do agendamento](auditorias/2026-09-10-agendamento-diario.md) (10/09), conferida no
código em 16/10: G01 e G07 resolvidos no PR #57 (prazo da extração, timeouts de 30 e 28 min), G06
resolvido (a entrega imediata coleta só para quem atende). Continuam abertos:

- **G03 — não reenviar a quem já foi atendido no dia.** A consulta dos ativos não filtra quem
  recebeu hoje, então reexecutar o diário manda segunda mensagem a todos. Sem essa marca não há
  recuperação segura depois de falha parcial nem agendador de reserva. Exige migration.
- **G04 — detectar execução ausente.** Se o cron externo não disparar, nada avisa: o passo
  `if: failure()` só cobre execução que começou. A opção mais simples é o cron-job.org avisar por
  e-mail quando falhar.
- **G02 — registrar a duração de cada lote.** Os logs dizem quantas extrações cada lote devolveu,
  não quanto tempo levou; falta isso para medir o raciocínio `low` e a margem do prazo.
- **G05, G08, G09 e G10**, prioridade baixa. O G10 é o mais visível: falha do disparo da
  primeira busca só aparece no log da Edge Function.

Qualidade das recomendações:

- **Pesos da nota.** Não recalibrar sem `vaga_irrelevante` real; o viés conhecido e as
  alternativas estão nas [decisões do motor](decisoes-do-motor.md#viés-conhecido-do-ranking-03092026).
- **Gabarito humano.** As 20 entregas do primeiro gabarito (em `gabaritos/`, fora do Git) seguem
  com `relevante` nulo, então o juiz automático não foi validado (precisa de 75% de concordância).
- **Descartes.** `python -m radar descartes` exporta a amostra do pré-filtro, mas ninguém
  preencheu `descarte_correto`.
- **Abertas desde a quarta rodada (09/09):** refiltrar depois do enriquecimento as vagas que o
  pré-filtro cortou recuperaria os ~7% de vagas remotas que só dizem isso depois dos 500
  caracteres da Adzuna; "Banco de Talentos" não é vaga aberta e chega como estágio.
- **Frase de preferência lida como período mínimo** esconde a vaga de quem está antes do período;
  a correção é uma frase no prompt, adiada porque troca `VERSAO_DA_EXTRACAO` e reextrai o cache.
- **Frontend num arquivo só.** `web/assets/app.js` tem 2.367 linhas com estado compartilhado; a
  recomendação de 10/09 foi separar responsabilidades sem trocar de framework.

## 6. Hipóteses de validação

Vindas do pré-PRD de 08/09, que saiu em 16/10. O piloto é informal: são sinais combinados para
ler os resultados sem escolher o critério depois, não metas.

| Hipótese | Teste mínimo | Sinal proposto |
|---|---|---|
| H1 — A busca manual é uma dor relevante | Conversar com colegas que usaram por uma semana | A maioria relata busca repetitiva e quer delegar a triagem |
| H2 — O matching orienta a triagem | 20 vagas por área, avaliadas por pessoas da área sem ver a nota; o mesmo gabarito valida o juiz automático | Concordância de ao menos 75% com a decisão majoritária, das pessoas e do juiz |
| H3 — As fontes têm cobertura útil por área | Ler o resumo diário por 7 dias com perfis de áreas distintas | Ao menos 1 recomendação relevante em 5 de 7 dias por perfil |
| H4 — Telegram é um canal aceitável | Colegas vinculam o bot e recebem uma entrega | Quase todos concluem sem considerar o canal uma barreira |
| H5 — A entrega gera ação útil | 2 semanas com link rastreado, feedback e pergunta do dia seguinte | Metade abre uma vaga; parte sinaliza "Essa serviu" ou "Me candidatei" |
| H6 — A operação cabe nos limites | Resumo de cada execução (duração, requisições, vagas sem extração) | 6 de 7 execuções sem falha permanente e dentro de 28 minutos |
| H7 — A expansão não degrada computação | Comparar as entregas de computação antes e depois de 08/09 | Recusas "não é da minha área" não sobem |

Também do pré-PRD, e ainda sem dono: as listas de subáreas e habilidades sugeridas de cada área
foram escritas pela equipe e precisam ser lidas por alguém da área; e ligar a Jooble só faz
sentido se H3 falhar em alguma área.

Antes de aprovar uma característica nova, responder: ela reforça a promessa de achar vagas
relevantes mais cedo? Reduz uma incerteza deste plano? Existe teste manual ou menor que dê a mesma
evidência? Qual o custo permanente? O que pode ser adiado para abrir espaço?

## 7. Limitações e decisões que continuam valendo

- **Candidatura:** acontece na fonte; o Radar não se candidata e só registra a declaração "Me
  candidatei" da pergunta do dia seguinte.
- **Feedback:** a última resposta conta nas métricas, mas pode haver eventos brutos repetidos e
  perguntas simultâneas. Mensagem enviada sem gravação pode deixar token órfão.
- **Histórico:** exclusões definitivas podem alterar métricas de semanas passadas.
- **Ranking:** a v1 usa repetição e recusas de área. Os outros motivos não mudam pesos
  automaticamente; investigar exemplos antes de recalibrar.
- **Vaga encerrada:** o Radar não detecta que uma vaga fechou, porque a Adzuna segue listando o
  anúncio e conferir a origem exigiria seguir o link dela de forma automática. O que existe é a
  janela de coleta (`dias_recentes`) e o feedback "Vaga encerrada"
  ([decisões do motor](decisoes-do-motor.md#vaga-fechada-na-origem-16092026)). Quem recebe a vaga
  no mesmo envio de quem a marcou não é protegido. Encurtar a janela não pegaria o caso medido em
  16/09 e perderia vagas válidas; só reavaliar com dados do piloto.
- **IA:** o reuso evita trabalho repetido; anúncios, cidades e áreas novos podem exigir extrações.
- **Fora do trabalho imediato:** cobrança, plano formal de pesquisa, D7, campanhas de e-mail e
  exclusão automática por abandono. Monetização permanece hipótese futura.
- **Frontend em JavaScript puro** (13/09): a migração para React chegou a ser feita (#62, #64,
  #66, #67) e saiu porque o estudante não via diferença (24 de 28 telas idênticas pixel a pixel)
  e o custo era real: 156 KB de JavaScript e CSS com gzip contra 84 KB, uma pilha Node/npm e cada
  correção do `app.js` em dobro. Retomar só com telas interativas grandes, como um painel web de
  métricas.
- **Jooble:** opcional, com chave e configuração próprias; não bloqueia a divulgação.
- **Histórico Git e skills:** permanecem conforme decisões de 05/09. Não há autorização para
  reescrever histórico ou remover recursos de terceiros.
