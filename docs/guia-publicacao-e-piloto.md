# Guia de publicação e piloto

**Consolidado em 09/09/2026, sem nova consulta remota.** Há evidências datadas de deploy
parcial: migrations `0014`–`0016` aplicadas e reconciliadas em 06/09 (seção 9), `ir` e
`telegram-webhook` publicadas. O endereço `https://radarestagio.pages.dev` foi registrado
em 08/09; a versão efetivamente servida e o domínio final precisam de conferência.
Os textos legais continuam em revisão, sem vigência. A seção 12 concentra a publicação da
expansão; os registros anteriores abaixo não comprovam o estado atual dos serviços.

Conferido no ambiente remoto em 06/09, nesta revisão:

- `supabase functions list`: `ir` e `telegram-webhook` **ativas**, publicadas em 05/09 às 21:13 e
  21:15 UTC. O código no ar foi baixado com `supabase functions download` e comparado arquivo a
  arquivo com o do repositório: **idêntico** nas duas. Confirma que a versão publicada carrega o
  feedback de seis opções, a resposta que não devolve 500 depois de gravar e a `navegacao.ts` que
  preserva o link de conta pausada.
- Objetos das `0014`–`0016` presentes: as três colunas de consentimento, `cadastros_pendentes`,
  as quatro funções da `0014`, `baixar_meus_dados` e `verificar_perfil_da_interacao`.
- `validar_cadastro_radar` no ar é a versão que valida o **formato** da data, não a que tinha
  `2026-09-05` cravado: o deploy pegou o commit posterior à correção.
- `getWebhookInfo`: `allowed_updates` com `message` e `callback_query`, sem fila pendente e sem
  último erro.
- `supabase migration list --linked`: as `0014`–`0016` não constavam como aplicadas. Corrigido no
  mesmo dia com `migration repair`; a coluna `remote` das três agora traz a própria versão.

Estado registrado na atualização de 05/09 à noite, sem repetir os testes remotos nesta revisão:

- Contato funcionando; combinar a rotina de resposta com Ian e Miguel.
- Resend verificado e SMTP salvo; falta validar confirmação e recuperação reais.
- `URL_DE_RASTREIO` criada no GitHub; `URL_DA_LANDING` aponta para `https://radarestagio.pages.dev` (08/09/2026).
- Token real validou redirecionamento 302 e registro de `vaga_aberta`.
- Primeira entrega real após `/start` em cerca de quatro minutos, sem requisições de IA.
- Trava por perfil implementada e validada com duas conexões no banco real.
- Relatório conferido com dados reais; feedback ainda zerado naquele teste.
- Hospedagem, retornos finais do Auth, Turnstile e cadastro completo continuam pendentes.
- A transferência para `RadarEstagio/RadarEstagio` foi confirmada em 08/09; conferir se
  Cloudflare, cron e dispatch do webhook usam a organização, conforme o registro em `CLAUDE.md`.

Verificação de 09/09 à noite, contra o site publicado e o projeto real:

- Os arquivos publicados são os do `main`; a página carrega sem erro de console no Chrome.
- `signup` pelo mesmo pedido que o site faz, com e-mail real: conta criada, confirmação enviada
  em 1 segundo, `cadastros_pendentes` com o perfil e `conta_criada` registrado pelo gatilho.
  Com `@example.com` o Auth devolve 500 "Error sending confirmation email": o SMTP recusa o
  domínio, não é falha do fluxo.
- Anônimo não lê `perfis` (401) nem chama `concluir_meu_cadastro` (401). Webhook do bot sem
  fila e sem erro; `ir` e `telegram-webhook` respondem.
- O último cadastro completo (08/09 01:12) levou 33 s até confirmar e 18 s até vincular o
  Telegram. Nenhum cadastro pendente ficou para trás.
- O clique no link de confirmação confirmou a conta e criou o perfil, mas o Auth redirecionou
  para `https://radarestagio.com`, que não resolve: o Site URL apontava para um domínio ainda
  não associado ao Pages. Correção e valores certos na seção 5.
- Continua pendente: Turnstile (`turnstileSiteKey` vazio em `web/config.js` e proteção por
  captcha desligada no Auth, então o cadastro sem captcha passa). Sem evento de falha no passo
  da conta, não dá para saber por que duas sessões concluíram as etapas e não criaram conta.

Use sempre o projeto Supabase **`xrhvjwemmylwbqgluebc`**, da região de São Paulo. O projeto
`bnzogphdvpubtkcflcue` não é o banco do Radar.

## 1. Contato — recebimento testado e funcionando

Igor confirmou o teste em 05/09. O procedimento abaixo fica como referência de configuração.

No Cloudflare, abra **Email Service → Email Routing**, selecione `radarestagio.com` e cadastre
o domínio. Adicione e verifique o e-mail pessoal de destino. Em **Routing Rules**, crie
`contato` → encaminhar para esse destino. Confira os registros DNS propostos antes de salvar.
Envie uma mensagem de outra conta para `contato@radarestagio.com`; confira a caixa e o spam.
[Instruções do Cloudflare](https://developers.cloudflare.com/email-service/get-started/route-emails/).

O encaminhamento resolve o recebimento. Combine com Ian e Miguel quem acompanhará e responderá
as mensagens. O envio automático da confirmação será configurado separadamente no Resend.

**Recebimento concluído.** Combine quem responderá e acompanhará os pedidos.

## 2. Revisar os documentos e combinar a manutenção

Revise com Ian os [Termos](../web/termos.html) e a [Política](../web/privacidade.html).
Miguel também está identificado como responsável pelos dados. Registrem:

- Concordância com a descrição do serviço, dados, fornecedores e retenção de 60 dias.
- Bases legais por finalidade e condições de processamento internacional, logs e backups:
  **redigidas em 08/09/2026** na seção 3, na seção 4 e na seção 6 da Política (Markdown e HTML
  iguais). Falta só a aprovação dos três.
- Quem atenderá solicitações de dados e pedidos de eliminação sem aguardar arrependimento.
- Quem acompanha falhas do job e a rotina de apagamento.
- Quem paga a renovação do domínio, a data e o destino do domínio e das contas ao fim da disciplina.

Proposta de divisão registrada em 08/09/2026 por Ian, **a confirmar por Igor e Miguel**:

| Responsabilidade | Proposta | Por quê |
|---|---|---|
| Responder o `contato@radarestagio.com` e os pedidos de dados e eliminação | Miguel | Já identificado como responsável pelos dados na Política; prazo de resposta combinado: 5 dias úteis |
| Acompanhar o resumo diário das 07:23, falhas do job, cota do Gemini e a rotina de apagamento | Ian | Dono das contas do Actions, do cron-job.org, da Cloudflare e do Supabase |
| Domínio `radarestagio.com`, DNS, e-mail e renovação | Igor | O domínio está na conta pessoal dele; ao fim da disciplina, transferir para quem continuar ou deixar expirar com aviso no site |

Para publicar depois da aprovação, em um único commit: definir a data de vigência nos dois HTML
(`legal-updated` e o `aside.legal-notice`, que sai) e nos dois Markdown, e trocar
`VERSAO_DOS_TERMOS` em `web/assets/app.js` para a mesma data, porque o banco guarda a versão
aceita por cada conta. Confiram também os controles reais descritos no
[contrato frontend](contrato-front.md).

**Concluído quando:** texto final aprovado, contato ativo e responsabilidades confirmadas.

## 3. Configurar Resend e SMTP — pode preparar agora

No Resend, adicione `radarestagio.com` em **Domains**. Copie para o Cloudflare os registros
DNS apresentados, respeitando seus nomes. Preserve os MX de recebimento do contato.
Aguarde a verificação do domínio e crie uma chave de API para envio.

No Supabase, abra **Authentication → Email → SMTP Settings**, habilite SMTP personalizado:

| Campo | Valor |
|---|---|
| Sender name | `Radar de Estágio` |
| Sender email | `contato@radarestagio.com` |
| Host | `smtp.resend.com` |
| Port | `465` |
| Username | `resend` |
| Password | Chave de API do Resend |

Salve a chave diretamente nesse campo. Ela não entra no frontend nem no Git.
[Configuração oficial do Resend](https://resend.com/docs/send-with-supabase-smtp).

Confira os limites de envio tanto no Supabase Auth quanto na conta Resend para comportar
10 a 20 cadastros e seus reenvios. SMTP próprio continua sujeito a limites. Nos templates de
confirmação e recuperação, use português e o nome Radar de Estágio, preservando o link de
ação do Supabase. [SMTP no Supabase](https://supabase.com/docs/guides/auth/auth-smtp).

**Concluído quando:** uma confirmação real chega à conta de teste com o remetente correto.
A tela de recuperação está implementada localmente; falta conferir o fluxo com envio real.

## 4. Hospedar o site e associar o domínio

Primeiro conferir o projeto Pages existente, sua URL e ligação com a organização; não criar
outro projeto para substituir uma integração desconectada. Registrar SHA do deploy e se a
main publica automaticamente. Se não houver projeto, abra **Workers & Pages → Create application →
Pages → Import an existing Git repository** e escolha o repositório do Radar:

| Campo | Valor |
|---|---|
| Production branch | `main` |
| Framework preset | Nenhum |
| Root directory | Raiz do repositório |
| Build command | `exit 0` |
| Build output directory | `web` |

Confira o endereço `*.pages.dev`. Publique somente a pasta `web`.
[HTML estático no Pages](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/).

No projeto Pages, abra **Custom domains** e adicione `radarestagio.com`. Faça a associação
pelo Pages antes de criar registros manualmente. Aguarde domínio e HTTPS ativos. Se usar
`www`, associe-o também e configure seu redirecionamento ao domínio principal.
[Domínios no Pages](https://developers.cloudflare.com/pages/configuration/custom-domains/).

**Concluído quando:** início, Termos e Privacidade abrem em HTTPS, inclusive no celular.
Publicação para conferir não libera o piloto: os bloqueadores da seção 9 continuam valendo.

### Build compatível durante a migração do frontend

A configuração registrada acima continua valendo até a integração da P1 e autorização própria
para alterar o Pages. A preparação adiciona `bash scripts/build-web.sh`, que produz `web/dist`
sem mudar a entrada estática ativa.

Sem `web/package.json`, o script copia somente `index.html`, `termos.html`, `privacidade.html`,
`config.js` e os recursos atuais permitidos de `assets/`: CSS, JavaScript, catálogos e logo da
Adzuna. Arquivos de testes, dependências, relatórios, fontes não listadas e segredos não entram
na saída. O destino é validado e somente `web/dist` pode ser limpo.

Quando `web/package.json` existir, o script exige `package-lock.json`, `vite.config.js` e um
script `build` válido. Ele executa `npm --prefix web ci` e `npm --prefix web run build`; falha de
manifesto, instalação ou build termina com erro e nunca usa o caminho legado. Antes de retornar
sucesso, verifica as três páginas públicas, `config.js`, os catálogos, o logo e a ausência de
links simbólicos ou arquivos proibidos no artefato.

Os testes de P1 exercitam os dois caminhos em projetos temporários e não geram `web/dist` no
checkout. Até a P1 ser integrada e a alteração remota autorizada, mantenha a configuração atual.

Depois de integrar a preparação e obter autorização para a mudança remota, usar como configuração
alvo `bash scripts/build-web.sh` no comando de build e `web/dist` como diretório de saída. Registrar
o SHA e o deployment anterior antes da alteração; validar primeiro um build legado e só então
ativar previews das branches com Vite. Não alterar domínio, Auth, CAPTCHA ou produção como parte
da preparação local.

## 5. Configurar o retorno do Auth

Em **Authentication → URL Configuration**, preencha:

| Campo | Valor |
|---|---|
| Site URL | O endereço em que o site está publicado hoje: `https://radarestagio.pages.dev` enquanto `radarestagio.com` não estiver associado ao Pages |
| Redirect URLs | `https://radarestagio.pages.dev/**` e `https://radarestagio.com/**` |
| Desenvolvimento local | `http://localhost:8000/**` |

O site manda `emailRedirectTo` com a própria origem (`window.location.origin`), então a origem
em uso precisa estar na lista com o curinga `/**`; fora da lista, o Auth ignora o pedido e volta
para o Site URL. Mantenha confirmação de e-mail habilitada. O curinga já cobre
`/?fluxo=recuperar`, usado pela recuperação implementada.
[URLs de retorno do Supabase](https://supabase.com/docs/guides/auth/redirect-urls).

Falha vista em 09/09: o Site URL estava em `https://radarestagio.com` sem o domínio associado
ao Pages (o DNS só tem MX, do e-mail). A conta era confirmada no banco, o perfil era criado,
mas a pessoa caía em "não é possível acessar esse site" e, ao clicar de novo, em
`otp_expired`. Quem confirmou nesse período precisa entrar pelo site com e-mail e senha para
ver o botão do Telegram. Corrigido no painel na mesma noite, com Site URL e Redirect URLs em
`radarestagio.pages.dev`; o cadastro seguinte confirmou e voltou ao site logado, na tela
"Agora, ative as entregas", com o botão do Telegram.

**Concluído quando:** a confirmação volta ao site publicado e mostra o botão do Telegram. O
teste em outro aparelho deve ser repetido após qualquer troca de endereço.

## 6. Preparar Turnstile — ativar a exigência só depois do código

No Cloudflare Turnstile, crie um widget gerenciado para `radarestagio.com`. Adicione outros
hostnames apenas se usados nos testes. Guarde a **site key** pública para o frontend e a
**secret key** para **Authentication → Bot and Abuse Protection → CAPTCHA**, no Supabase.

**A integração está pronta localmente e inerte**, com `turnstileSiteKey` vazio. Preencha essa
chave pública e disponibilize o frontend atualizado antes de exigir CAPTCHA no Supabase.
Depois escolha Turnstile no Supabase, habilite e teste cadastro,
login, reenvio e recuperação, incluindo expiração do desafio.
[CAPTCHA no Supabase](https://supabase.com/docs/guides/auth/auth-captcha).

**Concluído quando:** os fluxos passam com token válido e o servidor recusa token inválido.

## 6.1 Republicar as funções depois das correções de 10/09/2026

As duas Edge Functions mudaram e **precisam de deploy**; sem ele as correções não valem em
produção:

```bash
supabase functions deploy ir
supabase functions deploy telegram-webhook
```

O que muda: `ir` só redireciona para endereço `http`/`https` e cai na landing em qualquer outro
esquema; o vínculo passa a recusar chat de grupo, para que ninguém mande as recomendações de
uma conta para um grupo; corpo que não é JSON devolve 200 em vez de 500, que fazia o Telegram
reenviar em laço; e clique cujo formato a função não reconhece recebe `answerCallbackQuery`,
tirando o relógio do botão nas mensagens antigas.

Nenhum secret muda e o webhook não precisa ser re-registrado. Depois do deploy, confira
`getWebhookInfo` sem `last_error_message` e abra um link de vaga para ver o 302 de sempre.

## 7. Rastreamento publicado — concluir o endereço da landing

| Onde | Nome | Valor |
|---|---|---|
| Supabase → Edge Functions → Secrets | `URL_DA_LANDING` | `https://radarestagio.pages.dev` (trocar pelo domínio próprio quando existir) |
| GitHub → Settings → Secrets and variables → Actions | `URL_DE_RASTREIO` | `https://xrhvjwemmylwbqgluebc.supabase.co/functions/v1/ir` |

Preserve os secrets existentes `TELEGRAM_BOT_TOKEN` e `TELEGRAM_WEBHOOK_SECRET` das funções.
As credenciais de banco das funções são fornecidas pelo ambiente Supabase. Nenhum segredo
entra em `web/config.js`; ali só cabe a chave publicável do projeto.

`ir` e `telegram-webhook` foram publicadas em 05/09. A tabela acima registra a configuração
conhecida: conferir `URL_DA_LANDING` e atualizá-la quando o domínio final for definido.
`supabase/config.toml` já define `verify_jwt = false`
para ambas: o webhook verifica o segredo do Telegram, e `ir` atende os links do navegador.

Confira a configuração do webhook: URL da função, mesmo segredo e `allowed_updates` contendo
`message` e `callback_query`. O plano registra isso como corrigido; não precisa rotacionar
o segredo apenas para republicar.

**Concluído quando:** abrir vaga grava `vaga_aberta`, token inválido volta à landing e cada
feedback grava o evento correto. Links antigos de conta excluída não podem gerar novos eventos.

## 8. Primeira entrega — implementada e validada

A execução sob demanda foi implementada usando `workflow_dispatch` com o input `perfil`.
A Edge Function lê o secret `GITHUB_DISPATCH_TOKEN`, com permissão de Actions para
`RadarEstagio/RadarEstagio`. Sem esse secret, o vínculo funciona e a busca fica para o diário.
O fluxo real levou cerca de quatro minutos no teste registrado. A trava por perfil foi
validada com duas conexões; execuções concorrentes aguardam e releem o histórico.
Confira a validade do token e reconfigure o acesso se o repositório mudar de organização.

Preserve o agendamento do cron-job.org às 07:23 de Brasília. Não adicione outro agendador.

**Concluído quando:** vínculo dispara apenas o perfil vinculado, repetição não duplica envio,
a janela de 06:23 a 07:23 aguarda o diário e os demais perfis continuam atendidos.

## 9. Código e validação antes do piloto

Registro anterior à expansão: migrations `0014`–`0016` aplicadas e funções publicadas;
versão atual do frontend a conferir:

- `0014`: consentimento, versão aceita e perfil criado na confirmação a partir de cópia protegida.
- Cadastro com checkboxes separados, revelar senha e sessão de origem preservada.
- Confirmação entre aparelhos e reenvio com e-mail editável e espera de um minuto.
- Turnstile opcional, recuperação de senha, `0015` para baixar dados e revogação de e-mails.
- Revalidação do destinatário no job e nas funções, com `0016` impedindo novos eventos de vaga
  para contas pausadas, excluídas ou desvinculadas.

Também implementados e testados localmente:
- Feedback individual com seis opções, incluindo positivo e motivo da nota incorreta.
- Funil completo, vagas distintas, utilidade semanal e denominadores das recusas.
- Vocabulário e métricas alinhados; candidatura continua sem emissor por decisão do plano.

O pipeline por perfil, o dispatch e a trava de concorrência foram implementados e validados
conforme o registro acima. Falta testar o cadastro completo pela interface publicada e
registrar respostas positivas e negativas reais no feedback.

As migrations `0013`–`0016` já aplicadas não serão reescritas. Correções futuras devem
entrar em novas migrations pelo histórico do projeto. Depois da integração e revisão final,
retirar os avisos de rascunho das páginas e registrar versão/data coerentes com o aceite.

**As `0014`–`0016` foram aplicadas fora do histórico de migrations, e isso foi corrigido em
06/09.** A conferência encontrou todos os objetos das três no banco — as colunas de consentimento,
`cadastros_pendentes`, as quatro funções da `0014`, `baixar_meus_dados` e
`verificar_perfil_da_interacao` — mas nenhuma registrada em `supabase_migrations.schema_migrations`.
Como o `db push` grava o registro na mesma transação em que aplica, as três aplicadas e nenhuma
registrada indicam que o SQL foi executado direto no banco, sem passar pelo CLI. Os OIDs dos objetos
são sequenciais, então as três rodaram na ordem certa e de uma vez só.

Sem conserto, o `db push` seguinte tentaria reaplicá-las e quebraria no primeiro `add column` de
coluna existente, deixando a migration nova pela metade. `supabase migration repair --status
applied 0014 0015 0016` resolveu, gravando só o registro, sem reexecutar SQL. O histórico foi
conferido depois: as três constam com nome e contagem de comandos, como em qualquer push.

**Conferir `supabase migration list --linked` depois de aplicar e antes do próximo push.**

## 10. Conferência final com conta de teste

Use dados sintéticos e seus próprios endereços e Telegram:

- Cadastro sem aceite é recusado; e-mails opcionais começam desmarcados.
- Cadastro no computador e confirmação no celular recuperam o perfil correto.
- Link expirado, reenvio e login antes da confirmação têm saídas claras.
- Recuperação troca a senha e permite entrar com a nova senha.
- Vínculo, primeira entrega, links e seis opções de feedback funcionam conforme os planos.
- Edição, pausa, retomada, desvínculo e preferência de e-mail persistem após novo login.
- Download contém só os dados do dono, sem credenciais.
- Exclusão interrompe novas entregas/eventos e libera o chat; cancelamento preserva a pausa.
- Apagamento após a carência passa em ambiente de teste com datas controladas, incluindo duas
  contas no mesmo navegador. Não envelheça contas reais para testar.
- Métricas refletem os eventos e não contam cliques repetidos como vagas diferentes.

**Concluído quando:** resultados registrados e falhas corrigidas. Identifique as contas e
sessões de teste para separá-las das métricas do piloto.

## 12. Registro de preparação da expansão — 08/09/2026

### Evidência local consolidada em 09/09

O registro da revisão do PR #22, de 08/09, informa 666 testes Python aprovados e 25
ignorados por dependência de `DATABASE_URL_TESTE`; 52 testes web/banco aprovados; Ruff,
formatação e `git diff --check` aprovados. São resultados históricos da revisão, não testes
executados nesta consolidação ou garantia sobre qualquer SHA posterior.
Não houve inspeção visual naquela revisão. Conferir landing, FAQ, cadastro e conta em
375 px e 1280 px, teclado, foco, Enter e ausência de overflow; JSDOM não verifica layout.
Nenhum desses resultados comprova deploy ou aplicação remota de `0017`–`0019`.

Este registro reúne a evidência disponível no repositório e a diferença entre o código local
da branch `codex/expansao-revenue-centric` e o ambiente remoto. A sessão não teve acesso para
consultar Cloudflare, Supabase, Telegram, cron-job.org ou GitHub; portanto, “não verificado”
é um impedimento explícito, não uma conclusão negativa. A evidência remota abaixo é a já
registrada neste guia em 05–06/09 e não foi repetida como se fosse atual.

| Componente | Versão esperada nesta expansão | Observada/evidência disponível | Data | Resultado e pendência |
|---|---|---|---|---|
| Frontend Cloudflare Pages | `web/` com C03–C06, L01–L02 e R02 | Não verificado remotamente; HTML/CSS/JS testados localmente na branch | 08/09 | Publicar após `0019`; conferir domínio, HTTPS, mobile e retorno do Auth |
| Auth, redirects e CAPTCHA | Código local C05/R02; Redirect URLs e Turnstile conforme seções 5–6 | Configuração remota não consultada; integração local coberta sem provedor real | 08/09 | Equipe deve testar confirmação, recuperação, CAPTCHA válido/expirado e login |
| Migrations | Histórico até `0019_motivo_pausa.sql`; `0018` aceita habilidades vazias e `0019` motivo opcional | Guia registra `0014`–`0016` aplicadas/reparadas em 06/09; `0017`–`0019` não têm evidência remota nesta sessão | 08/09 | Conferir `supabase migration list --linked`; aplicar somente pendentes, nesta ordem |
| Edge Function `ir` | Versão publicada compatível com rastreio atual | Guia registra publicação e comparação de `ir` em 05/09; não reconsultado | 05/09 (registro anterior) | Revalidar somente se secrets/domínio mudarem; não há arquivo de função alterado nesta expansão |
| Edge Function `telegram-webhook` | Vínculo, feedback e segredo preservados | Guia registra publicação e comparação em 05/09; webhook sem erro pendente no registro anterior | 05/09 (registro anterior) | Revalidar `getWebhookInfo`, vínculo e retorno de conta após publicar frontend |
| Rastreio | `URL_DA_LANDING` pública e `URL_DE_RASTREIO` do projeto correto | Guia registra `https://radarestagio.pages.dev` e função do projeto `xrhvjwemmylwbqgluebc`; não reconsultado | 06/09 (registro anterior) | Confirmar domínio final e eventos `vaga_aberta`/feedback sem expor tokens |
| Cron externo | cron-job.org às 07:23 BRT, sem `schedule` nativo | Não verificado nesta sessão; guia manda preservar o cron existente | 08/09 | Responsável a definir deve conferir token, horário e último dispatch; não criar outro agendador |
| Job diário | Workflow com `QUANTIDADE_VAGAS_ENVIADAS=7`, `DIAS_RECENTES=5`, timeout de 15 min | YAML local confere limite de sete; execução remota não verificada | 08/09 | Rodar somente com autorização e conta controlada; confirmar alerta de falha |

### Ordem de publicação preparada

1. Registrar SHA local, SHA remoto, versão observada por componente, data e responsável;
   conferir se o deploy automático exige separar etapas antes do merge. Confirmar os testes
   relevantes à versão escolhida; não publicar documentos legais como vigentes sem a
   revisão de Ian/Miguel.
2. Publicar o Python compatível com perfil sem habilidades e, no Supabase, conferir histórico,
   incluindo a predecessora `0017`, antes de aplicar `0018_habilidades_vazias.sql`.
   Aplicar apenas migrations pendentes; não reaplicar as já registradas.
3. Antes de aplicar a `0018`, conferir os dados existentes: a constraint nova valida na hora e
   exige de 0 a 50 itens de 1 a 100 caracteres, contrato que a coluna original (`cardinality >= 1`)
   nunca impôs no update direto. Uma linha fora do contrato aborta o `db push` no meio. Consulta
   somente leitura, que precisa devolver zero linhas:

   ```sql
   select id from perfis
   where cardinality(habilidades) > 50
      or exists (select 1 from unnest(habilidades) h where length(btrim(h)) not between 1 and 100);
   ```

   Havendo linha, registrar o caso e decidir com o dono do perfil; não corrigir dado por suposição.
4. Aplicar `0019_motivo_pausa.sql` depois de `0018`, conferir grants/RLS e `migration list`.
5. Publicar `web/` com R02 somente depois de a coluna existir no banco; confirmar as URLs do
   Auth e o estado da site key do Turnstile no ambiente escolhido.
6. Publicar/validar as funções apenas se a equipe alterar sua versão ou secrets; a expansão
   local não alterou `supabase/functions`.
7. Rodar o roteiro controlado abaixo com uma conta da equipe, registrar IDs de teste fora das
   métricas do piloto e verificar novamente o limite de sete no workflow sem atender a base inteira.

### Roteiro de verificação controlada

| Passo | Resultado esperado |
|---|---|
| Abrir landing e iniciar cadastro | CTA abre cadastro; nenhuma senha ou habilidade é enviada antes do momento previsto |
| Salvar perfil com ou sem habilidades | Perfil válido; limite de recomendações continua sete |
| Confirmar e-mail em outro aparelho | Perfil aparece após confirmação; não depende de estado local do primeiro aparelho |
| Recuperar senha | Link retorna ao domínio autorizado e permite trocar senha |
| Vincular Telegram | Webhook confirma o perfil; dispatch é só do perfil, respeitando janela do diário |
| Receber recomendações | No máximo sete; abrir link grava `vaga_aberta` e feedback grava evento correto |
| Editar e pausar | Edição preserva contrato; pausa confirma antes da pergunta opcional |
| Responder ou pular motivo | Cinco valores fechados, update separado; “Pular” mantém pausa |
| Retomar | Update ativa e limpa `motivo_pausa`; pergunta não reaparece obrigatoriamente ao reabrir |
| Desvincular, exportar e excluir/cancelar | Controles afetam apenas a conta de teste; exportação não contém token; exclusão bloqueia novas interações |

### Reversão compatível

Se o frontend apresentar erro, reverter o artefato estático para a versão anterior e manter as
migrations aditivas `0018`/`0019`; não editar nem apagar migration aplicada. Se o relatório
R03 precisar ser retirado, usar a versão anterior do código do job/CLI enquanto a coluna
nullable permanece no banco. Corrigir depois em nova migration, se necessário; não executar
`drop column`, apagar dados ou reverter a coluna durante o piloto. A equipe deve registrar o
SHA publicado, horário, responsável e motivo da reversão. Qualquer versão anterior escolhida
para o job deve continuar aceitando habilidades vazias; não restaurar leitor ou constraint
que rejeite perfis já criados. Desativar a entrada nova no frontend antes de uma reversão
que dependa disso. A conferência de dados antes da `0018` foi escolhida para detectar legado
inválido sem corrigir dados pessoais por suposição nem apenas adiar a validação.

### Pendências e responsáveis

- A definir: acesso e aprovação da equipe para publicar a branch e conferir Cloudflare Pages.
- A definir: aplicação remota de `0018` e `0019`, conferência de RLS/grants e `migration list`.
- A definir: Redirect URLs, SMTP/Resend, Turnstile e textos legais vigentes.
- A definir: conta/Telegram de teste, acompanhamento de `contato@radarestagio.com` e confirmação
  do cron-job.org.
- A definir: domínio público final e autorização para qualquer relato de uso.

## 11. Divulgar e ouvir colegas

O plano formal de piloto foi retirado por decisão do Igor em 07/09. Depois de conferir os
fluxos, pedir a alguns colegas que usem e relatem onde travaram e quais vagas serviram.
Não há obrigação de entrevistas, coorte, prazo de duas semanas ou metas de retenção.
A checklist vigente está no [plano geral](plano-geral.md#2-o-que-falta-antes-de-divulgar).
