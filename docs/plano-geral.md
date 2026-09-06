# Plano geral


> Atualização de execução — 05/09 à noite: migrations `0014`–`0016` **aplicadas** no projeto
> remoto e conferidas objeto a objeto; `telegram-webhook` (feedback de seis opções) e `ir`
> **publicadas**; `URL_DA_LANDING` provisória aponta para o repositório até a landing subir e
> `URL_DE_RASTREIO` foi criada nos secrets do GitHub — `vaga_aberta` já registra (validado com
> token real, 302 até a vaga e evento no funil). A **proteção contra envios concorrentes** foi
> implementada (advisory lock por perfil, execução concorrente espera e relê o histórico) e
> validada com duas conexões no banco real. A entrega imediata foi **validada no ambiente
> real** em 05/09: `/start` → workflow → mensagem em ~4 minutos, com zero requisição de IA.
> `python -m radar metricas` foi conferido com os dados reais (funil coerente; feedback zerado
> porque os botões estrearam hoje). Entre as pendências técnicas estão as que dependem da landing publicada: hospedar o
> frontend, Site URL/Redirect no Auth, Turnstile e o teste do fluxo de cadastro completo.
> Resend foi verificado e o SMTP salvo pelo Igor, mas a entrega real de e-mail não foi testada.

**Atualizado em:** 06/09/2026

As validações remotas abaixo foram registradas na atualização de 05/09 à noite; não foram
reexecutadas nesta revisão documental. Revisão dos documentos e piloto continuam pendentes.

O que existe, o que falta e em que ordem. Os detalhes de cada frente moram nos documentos
apontados na seção 6; aqui é o mapa que amarra os três planos que hoje vivem separados.

## 1. Onde estamos

Cadastro, privacidade, feedback, métricas e entrega imediata estão na `main`. Banco e Edge
Functions foram atualizados; o frontend ainda aguarda hospedagem.

| | Estado |
|---|---|
| Job diário | funcionando; entrega vaga todo dia às 07:23 |
| Custo de IA | resolvido para coorte homogênea: a mesma vaga não é reextraída. Perfil de cidade ou área nova **amplia o conjunto elegível** — medir antes do piloto |
| Landing | **não hospedada em lugar nenhum** |
| Edge Function `telegram-webhook` | republicada em 05/09 com feedback individual |
| Edge Function `ir` | publicada em 05/09; redirecionamento e evento validados |
| Webhook do Telegram | `allowed_updates` já inclui `callback_query`, corrigido em 04/09 |
| Painel da conta | código na `main`; migrations `0013`–`0016` aplicadas; frontend não hospedado |
| Exclusão em duas etapas | pronta e aplicada: marca, para de entregar, apaga em 60 dias |
| Domínio | **comprado** (Cloudflare Registrar), ainda não apontado para lugar nenhum |
| Confirmação de e-mail | Resend verificado e SMTP salvo; falta validar confirmação e recuperação reais |

O próximo bloco é publicação do frontend, configuração, revisão dos documentos e validação
integrada. Falhas encontradas nessa validação podem exigir novas correções de código.

## 2. O funil, evento por evento

| Evento | Quem grava | Funciona hoje |
|---|---|---|
| `landing_visualizada` | site | sim, mas ninguém visita: não há hospedagem |
| `cta_cadastro_aberto` | site | idem |
| `etapa_perfil_concluida` | site | idem |
| `etapa_habilidades_concluida` | site | idem |
| `etapa_preferencias_concluida` | site | idem |
| `conta_criada` | gatilho | sim |
| `email_confirmado` | gatilho | sim |
| `perfil_salvo` | gatilho e site | sim |
| `telegram_aberto` | site | idem à landing |
| `telegram_vinculado` | gatilho | sim |
| `primeira_recomendacao_enviada` | gatilho | sim |
| `vaga_aberta` | função `ir` | sim — publicada em 05/09, com `URL_DE_RASTREIO` criada |
| `vaga_irrelevante` | webhook | sim — republicada em 05/09 com o feedback |
| `vaga_util` | webhook, botão “Essa serviu” | emissor publicado; validar resposta real |
| `candidatura_iniciada` | ninguém | **não existe emissor** |

## 3. North Star e feedback individual

A North Star mede a proporção semanal de estudantes ativados com ao menos uma vaga útil.
O emissor positivo e a consulta semanal estão implementados. A consulta foi conferida com
os dados reais; ainda é necessário validar os resultados com respostas do piloto.

A lacuna original era a ausência de feedback positivo individual. O botão “Todas serviram”
apenas apagava a mensagem. Ele foi substituído pelo fluxo abaixo.

**Decidido em 05/09: o feedback é por vaga, dentro da própria mensagem.** Os números deixam de
significar recusa e passam a abrir o feedback daquela vaga. A mensagem diária termina em "Deixe seu
feedback 👇" com um número por recomendação, e o clique abre uma segunda mensagem, com a vaga e
seis opções:

| Botão | O que grava |
|---|---|
| 👍 Essa serviu | `vaga_util` |
| 👎 A nota não fez sentido | `vaga_irrelevante` · `motivo_nota` |
| 👎 Não é da minha área | `vaga_irrelevante` · `motivo_area` |
| 👎 Pedem demais | `vaga_irrelevante` · `motivo_exigencia` |
| 👎 Local ou modalidade | `vaga_irrelevante` · `motivo_logistica` |
| 👎 Já vi essa | `vaga_irrelevante` · `motivo_repetida` |

**Não precisa de migration**: `vaga_util` já está no enum da `0005` e o motivo vai em
`propriedades`, que é `jsonb` sem restrição de conteúdo. Foi mudança de código, na
`telegram-webhook` e no formatador da mensagem.

`motivo_nota` não existia em nenhuma das duas saídas descartadas e é o ganho menos óbvio da
escolha. Ele é o sinal que a seção 7 da `auditoria-rcd.md` exige para mexer nos pesos do ranking:
a recusa de hoje não distingue "a vaga não serve para mim" de "a vaga serve, a nota é que está
errada", e só a segunda justifica ajustar peso.

**`candidatura_iniciada` fica sem emissor, e isso é deliberado.** O botão "Já me candidatei" saiu
do teclado porque quem se candidata também acha que a vaga serviu — o 👍 cobre a North Star
sozinho. O custo é que **Candidatura atribuída**, definida no `CONTEXT.md`, deixa de ser medível, e
a definição de vaga útil lá ("feedback positivo **ou** início de candidatura") passa a valer só
pela primeira metade. Alinhar o `CONTEXT.md` a isso, ou recuperar a captura junto da pergunta do
dia seguinte, se o piloto mostrar que faz falta.

## 4. O que falta, em ordem

### Fase A — destravar (tudo depende disto)

**O domínio não trava a medição.** O Cloudflare Pages publica em `*.pages.dev`, e a função `ir`
exige apenas que `URL_DA_LANDING` aponte para algum lugar — não para um domínio próprio. Dá para
destravar `vaga_aberta` hoje, sem comprar nada.

O domínio trava outra coisa: o **e-mail**. Sem ele não há endereço de contato para a política de
privacidade nem remetente próprio para o Resend.

```
publicar no *.pages.dev ── URL_DA_LANDING ── deploy da ir ── vaga_aberta
domínio ─┬─ contato@ ───── política de privacidade completa
         └─ Resend ─────── remetente próprio da confirmação
```

1. Publicar a landing no Cloudflare Pages, no endereço provisório
2. Registrar esse endereço em **Site URL e Redirect URLs** do Supabase Auth — sem isso o
   `emailRedirectTo` da confirmação não volta para a página publicada
3. ~~Criar `URL_DA_LANDING` no Supabase e `URL_DE_RASTREIO` nos secrets do GitHub~~ — feito em
   05/09 (`URL_DA_LANDING` provisória aponta para o repositório; trocar quando a landing subir)
4. ~~Publicar a função `ir` e **republicar** a `telegram-webhook` com o feedback~~ — feito em 05/09
5. ~~Comprar o domínio~~ — feito em 05/09. Publicar direto no domínio próprio dispensa refazer os
   passos 2 e 3 depois

Nada disso é código. A migration `0013` **saiu desta fase**: foi reescrita com os 60 dias,
revisada, corrigida e aplicada em 05/09.

**O domínio mudou o peso do e-mail.** Enquanto o plano supunha o endereço provisório, o remetente
do Supabase era ruim mas tolerável. Agora que o cadastro pode ir ao ar num domínio próprio, o
limite de poucos e-mails por hora do remetente compartilhado passa a ser o que separa o piloto de
funcionar: numa tarde com 10 a 20 estudantes se cadastrando, a maioria não recebe a confirmação.
Entrar é imune — `signInWithPassword` não passa por e-mail nem por redirect —, mas ninguém entra
antes de se cadastrar.

### Fase B — cadastro, consentimento e documentos

Código concluído e migrations `0014`–`0016` aplicadas. Cadastro com aceite separado,
confirmação entre aparelhos, reenvio, recuperação, exportação e revogação estão implementados.
Faltam publicar o frontend, configurar Turnstile, testar os fluxos integrados e concluir a
revisão dos Termos e da Política. Detalhes em `plano-cadastro-e-privacidade.md`.

### Fase C — fechar a medição

Feedback individual com seis opções publicado. Funil desde a visita, vagas distintas,
utilidade semanal e denominadores das recusas implementados. `vaga_aberta` foi validada
com token real e o relatório foi conferido com os dados existentes. Falta validar feedback
positivo e negativo reais e acompanhar os números do piloto. Candidatura segue sem emissor
por decisão do plano. As definições e limitações estão em `metricas.md`.

### Fase D — entrega imediata

Implementada com `workflow_dispatch` e input `perfil`, em vez do `repository_dispatch`
previsto inicialmente. Usa `GITHUB_DISPATCH_TOKEN` com permissão de Actions. Vínculos entre
06:23 e 07:23 de Brasília aguardam o diário; fora da janela, o webhook solicita a execução.

O fluxo real `/start` → workflow → mensagem foi registrado em cerca de quatro minutos,
sem requisições de IA. O atendimento usa advisory lock por perfil e relê o histórico após
obter a trava; a concorrência foi validada com duas conexões no banco real. Isso serializa
execuções, mas não torna envio ao Telegram e gravação no banco uma operação atômica.

### Fase E — piloto

Descrito no sprint 4 de `auditoria-rcd.md`: 10 a 20 estudantes, duas semanas, cinco entrevistas,
canais identificados. Só faz sentido depois das fases C e D.

## 5. Decisões e limites do escopo

| Assunto | Situação |
|---|---|
| Viés do ranking: anúncio raso tira nota maior | decidido esperar dado do piloto; evidência já registrada na seção 7 da auditoria |
| Dados pessoais no histórico do git | **decidido em 05/09: fica como está.** O perfil real do usuário nº 1 segue legível nos commits de 25/08 a 04/09, mas é curso, período, cidade e stack — sem nome, contato ou credencial. Reescrever obrigaria todo mundo a reclonar para remover dado de baixa sensibilidade. Conferido: nenhum `chat_id`, token ou e-mail de usuário no histórico |
| Apagar conta abandonada | fora do escopo agora; revisitar depois do piloto |
| Sprint 2 (busca imediata após o vínculo) | **decidido em 05/09: entra antes do piloto**, com a janela de 06:23 a 07:23 como exceção. Virou a fase D |
| Remetente do e-mail | **decidido em 05/09: o Resend entra antes do piloto.** Sem remetente próprio o cadastro não sustenta 10 a 20 pessoas na mesma tarde |
| Domínio em nome de quem | **decidido em 05/09: conta pessoal do Igor.** Registrar por escrito quem paga a renovação e o que acontece com o domínio quando a disciplina terminar |
| `.agents/skills` no repositório público | **decidido em 05/09: fica.** Fecha a pendência antiga; as licenças de origem estão no `.agents/skills/README.md` |

O coletor Jooble também está implementado, com testes, mas desligado por padrão. Sua
ativação é opcional e exige chave e configuração no workflow; não bloqueia o piloto.

## 6. Onde está cada coisa

| Documento | Para quê |
|---|---|
| `auditoria-rcd.md` | os catorze achados com situação, os sprints e o viés do ranking |
| `plano-cadastro-e-privacidade.md` | as sete decisões de cadastro, consentimento e LGPD |
| `plano-melhorias-rcd.md` | a estratégia RCD original, de onde tudo saiu |
| `metricas.md` | as consultas do funil e as definições |
| `arquitetura.md` | as camadas e as decisões técnicas |
| `CONTEXT.md` | o vocabulário: o que conta como ativação, vaga útil, candidatura |
