# Guia de publicação e piloto

**Revisado em 19/09/2026, com a hospedagem e o endereço atualizados em 03/10/2026.** Em 19/09,
`supabase migration list --linked` mostrou as 30 migrations (`0001`–`0031`, a numeração pula a
`0029`) aplicadas, e `supabase functions list` mostrou `ir` republicada em 10/09 e
`telegram-webhook` em 16/09. As demais seções guardam evidências datadas e não foram
reconsultadas depois dessas datas.

### Hospedagem e endereço público (03/10/2026)

Conferido por terminal (`curl`, `dig`, `whois`) e pelos painéis, na conta Cloudflare do grupo:

- **Domínio na conta do grupo.** `radarestagio.com` saiu da conta pessoal do Igor pela opção
  "Move to another account" do Registrar, depois de a conta do grupo cadastrar o domínio como site;
  sem isso o painel recusa com "Gaining account must first add the domain as a website". O
  registrador segue o Cloudflare, os nameservers passaram a `dexter` e `walk.ns.cloudflare.com` e a
  validade é 04/09/2027, com renovação automática ligada.
- **Site no Workers, não mais no Pages.** O PR #117 trouxe o `wrangler.jsonc`, que aponta a pasta
  `web/` como arquivos estáticos, sem etapa de build. O projeto `radarestagio` na conta do grupo
  foi criado a partir da `main` (build `#8c1bc853`, comando de deploy `npx wrangler deploy`) e
  responde em `radarestagio.estagioradar.workers.dev`. A conexão com o GitHub exigiu um owner da
  organização liberando o repositório no app Cloudflare Workers and Pages.
- **Endereço final no ar.** `https://radarestagio.com` responde 200 com certificado válido, e
  `/termos` e `/privacidade` também. `www` é um registro A com proxy e uma regra que redireciona
  com 301 para o domínio principal, preservando caminho e query. "Always Use HTTPS" está ligado,
  e `http://` redireciona para `https://` nos dois nomes. O HSTS segue desligado.
- **E-mail preservado.** MX do Email Routing e do `send`, SPF e DKIM do Cloudflare e do Resend
  continuam respondendo. A regra `contato@radarestagio.com` não acompanhou a mudança de conta:
  foi recriada com o mesmo destino de antes, e o teste de entrega chegou. O Resend como "Verified"
  no painel não foi reconferido.
- **Supabase.** O Site URL é `https://radarestagio.com`, e os Redirect URLs levam
  `https://radarestagio.com/**` e `http://localhost:8000/**` (conferido em 05/10). O secret
  `URL_DA_LANDING` está em `https://radarestagio.com`: a `ir` redireciona token inexistente e
  chamada sem token para o domínio novo. O GitHub Actions não tem `URL_DA_LANDING`.
- **Cadastro no domínio novo.** O Igor confirmou o cadastro com a confirmação do e-mail voltando
  ao site. Reenvio, recuperação de senha, entrega, feedback e controles da conta seguem sem teste
  registrado.
- **Turnstile e deploy automático (03/10/2026).** O widget gerenciado, criado na conta do grupo,
  tem a site key no `web/config.js` (PR #120). Depois do merge, o Workers Builds publicou a
  `main` sozinho em cerca de 30 segundos, com o check verde, e o `config.js` no ar passou a trazer
  a chave. O widget aparece no login. Com o captcha ligado no Supabase, `/auth/v1/token` sem
  token responde 400 `captcha_failed`. O Igor confirmou que login, cadastro e recuperação de
  senha passaram com o widget, sem o detalhe por fluxo. O check "Workers Builds" falhava em 0 s
  nos PRs: o build de branch roda `wrangler preview`, que exige `"previews": {}` no
  `wrangler.jsonc`. O PR #122 acrescentou o bloco e o check passou.
- **Pages antigo apagado (05/10/2026).** O Cloudflare recusou apagar o projeto pelo painel
  ("too many deployments"). O Ian apagou os deployments pela API do Cloudflare, com um token
  temporário de permissão Pages Edit, depois apagou o projeto e revogou o token. Conferido por
  terminal: `radarestagio.pages.dev` deixou de resolver, e `radarestagio.com`, `/termos`,
  `/privacidade`, `www` (301), o MX do e-mail e a `ir` (302 para o domínio novo) seguem
  respondendo, com os 4 checks verdes na `main`.
- **Ainda aberto.** Forma de pagamento da conta do grupo para a renovação; zona antiga na conta
  pessoal, que não se apaga até ficar no estado "Moved". Os Redirect URLs do Supabase já estavam
  sem o `pages.dev` em 05/10.

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

O encaminhamento resolve o recebimento: Igor responde as mensagens (ver "Responsabilidades
combinadas" na seção 2). O envio automático da confirmação será configurado separadamente no
Resend.

**Recebimento concluído.** Igor responde e acompanha os pedidos.

## 2. Revisar os documentos e combinar a manutenção

Igor, Ian e Miguel são os responsáveis pelos dados nos [Termos](../web/termos.html) e na
[Política](../web/privacidade.html). A revisão fechou em 02/10/2026:

- Descrição do serviço, dados, fornecedores e retenção de 60 dias: mantidas como estavam.
- Bases legais por finalidade e condições de processamento internacional, logs e backups:
  redigidas em 08/09/2026 (seções 3, 4 e 6 da Política), sem passagem pendente.
- **Vigência:** em vigor hoje está a versão `2026-10-08`, desde 08/10/2026, nos dois HTML, nos
  dois Markdown e em `VERSAO_DOS_TERMOS` de `web/assets/app.js`; a revisão de 02/10 entrou como
  `2026-10-02`, e as versões seguintes estão nos itens abaixo. O aviso de rascunho saiu das
  páginas. O banco só aceita a versão como data (`AAAA-MM-DD`), e cada conta guarda a que
  aceitou. Contas que aceitaram `2026-09-05` continuam válidas: o piloto ainda não começou e não
  há aceite a renovar.
- **Versão `2026-10-05`:** a Política passa a dizer que a equipe lê as mensagens enviadas ao bot,
  encaminhadas ao chat de operação pela `telegram-webhook`, com a base legal (art. 7º, V) e o que
  a exclusão da conta não apaga. Os Termos só trocam a data. Contas que aceitaram `2026-10-02`
  continuam válidas: nenhuma finalidade nova exige consentimento.
- **Versão `2026-10-08`:** a Política passa a nomear os endereços que o navegador contata ao
  abrir qualquer página — `fonts.googleapis.com`, `fonts.gstatic.com`, `cdn.jsdelivr.net` e
  `challenges.cloudflare.com` — e inclui o jsDelivr na infraestrutura fora do Brasil; o porquê
  está no [contrato frontend](contrato-front.md). Os Termos só trocam a data. Contas que
  aceitaram `2026-10-05` continuam válidas, pela mesma regra das versões anteriores: nenhuma
  finalidade nova exige consentimento, o tratamento descrito já acontecia e o que mudou foi a
  transparência sobre ele. O texto de 07/10 sobre o tema guardado no navegador entrou sem trocar
  a versão, e esta corrige isso: mudança de texto legal muda a versão.

### Responsabilidades combinadas (02/10/2026)

- **Contato e pedidos de dados:** Igor responde `contato@radarestagio.com`, que encaminha para o
  e-mail dele, e atende pedidos de dados e eliminação em até 5 dias úteis, sem esperar o prazo de
  arrependimento.
- **Falhas do diário e rotina de apagamento:** Igor lê o resumo que cada execução envia ao chat de
  operação. Execução que sai com código 1 ou resumo que não chega é investigada no mesmo dia.
- **Domínio:** Igor paga a renovação de `radarestagio.com`, que desde 03/10/2026 está na conta
  Cloudflare do grupo, junto do site e do Email Routing. As contas do
  Actions, do cron-job.org e do Supabase seguem em contas pessoais do grupo; ao fim da disciplina,
  transferir para quem continuar ou deixar o domínio expirar com aviso no site.

Para alterar uma versão futura, no mesmo commit: nova data nos dois HTML (`legal-updated` e o
parágrafo final da seção de mudanças), nos dois Markdown, em `VERSAO_DOS_TERMOS`, na linha de
vigência acima, em `docs/README.md` e no item desta seção no [plano geral](plano-geral.md).
Confiram os controles reais descritos no [contrato frontend](contrato-front.md).

**Concluído em 02/10/2026:** textos em vigor, hoje na versão `2026-10-08`, contato ativo e
responsabilidades registradas.

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

Desde 03/10/2026 o site roda no **Workers com arquivos estáticos**, na conta Cloudflare do grupo,
que também tem o domínio. O `wrangler.jsonc` da raiz aponta a pasta `web/`; não há etapa de build.
O Pages que o grupo usava antes estava na conta do Ian e foi apagado em 05/10/2026. Projeto Pages
com muitos deployments não se apaga pelo painel: é preciso apagar os deployments pela API
(`DELETE .../pages/projects/<nome>/deployments/<id>?force=true`) antes.

Para criar o projeto de novo, na conta do grupo: **Workers & Pages → Create application → Connect
GitHub** e escolha o repositório do Radar. O app Cloudflare Workers and Pages precisa estar
instalado na organização com acesso ao repositório, e isso só um owner da organização faz.

| Campo | Valor |
|---|---|
| Project name | `radarestagio`, igual ao `name` do `wrangler.jsonc`, senão o build falha |
| Production branch | `main` |
| Build command | em branco |
| Deploy command | `npx wrangler deploy` |
| Root directory | `/` |

Confira o endereço `*.workers.dev`. O `uv sync` que aparece no log é do Cloudflare ao achar o
`pyproject.toml`: não leva segredo, porque o build não tem variáveis.

O domínio entra por **Settings → Domains & Routes → Add Domain** (`radarestagio.com`). O `www` não
se associa ao Worker: ele recebe um registro A `192.0.2.1` com proxy e uma regra em **Rules →
Redirect Rules** (modelo "Redirect from WWW to root", 301, preservando a query). Em **SSL/TLS →
Edge Certificates**, ligue "Always Use HTTPS" e deixe o HSTS desligado. Não altere os MX e os TXT
do e-mail.

### Cabeçalhos de resposta do site (08/10/2026)

Até 07/10 o site respondia sem nenhum cabeçalho de segurança: `curl -I https://radarestagio.com`
devolvia só `content-type`, `cache-control`, `nel`, `report-to`, `server`, `cf-ray` e `alt-svc`.
O Workers com arquivos estáticos lê `web/_headers`, que não vai para o ar como arquivo, e ele passa
a mandar em `/*`:

| Cabeçalho | Valor | O que protege |
|---|---|---|
| `X-Frame-Options` | `DENY` | Clickjacking: sem ele, qualquer origem embutia o site num iframe e cobria o painel da conta, que tem "Excluir conta" a um clique e a confirmação desenhada na própria página |
| `Content-Security-Policy` | `frame-ancestors 'none'` | A mesma proteção, na forma que os navegadores atuais leem; só restringe quem pode embutir o site, nunca o que a página carrega |
| `X-Content-Type-Options` | `nosniff` | Impede o navegador de adivinhar o tipo de uma resposta e tratar `assets/areas.json` ou `assets/cidades.json` como script ou HTML |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | A URL de confirmação e a de recuperação do Auth, com o que vem na query, deixam de sair no `Referer` para o Google Fonts, o jsDelivr e o Turnstile; a origem continua indo nos links da Adzuna, que a atribuição pede |

Nada embute o site hoje, então `DENY` não custa nada: o widget do Turnstile é um iframe **dentro**
da nossa página, e `frame-ancestors` restringe o contrário disso.

Ficou de fora, com o porquê:

- **A CSP que restringe carregamento** (`script-src`, `style-src`, `connect-src`, `font-src`,
  `frame-src`). As origens que a página usa hoje, conferidas no código: `'self'` (`config.js`,
  `assets/app.js`, `assets/styles.css`, `assets/areas.json`, `assets/cidades.json`,
  `assets/adzuna-logo.png`), `https://cdn.jsdelivr.net` (o `@supabase/supabase-js@2.116.0` do
  `index.html`), `https://challenges.cloudflare.com` (o `turnstile/v0/api.js` que o `app.js`
  injeta, mais o iframe do widget), `https://fonts.googleapis.com` (folha) com
  `https://fonts.gstatic.com` (arquivos das fontes) e o host do Supabase que está no
  `web/config.js`. Três coisas seguram a lista: o script de tema no `<head>` das três páginas é
  inline, o que obriga `'unsafe-inline'` — e com ele a CSP deixa de barrar o XSS, que é o motivo
  dela — ou um hash que quebra calado a cada edição daquela linha; o Turnstile não dá para
  exercitar numa cópia local, porque o `config.js` local vai sem site key e o widget nem carrega,
  então o que ele injeta só apareceria em produção, onde um erro de CSP derruba login, cadastro e
  recuperação de senha de uma vez; e o host do Supabase mora no `config.js` enquanto a CSP moraria
  no `_headers`, de modo que trocar de projeto passaria a exigir os dois arquivos juntos. O
  caminho é publicar antes como `Content-Security-Policy-Report-Only`, abrir login, cadastro e
  recuperação no site publicado e ler o console, e só então trocar para o cabeçalho que bloqueia.
- **HSTS**, que segue desligado pela decisão registrada acima, com "Always Use HTTPS" ligado no
  lugar.

**Conferir depois do deploy**, porque o `_headers` só vale quando o Workers publica:
`curl -I https://radarestagio.com`, `/termos` e `/privacidade` têm de trazer os quatro cabeçalhos,
e `curl -I https://radarestagio.com/_headers` tem de responder 404. Se o arquivo for servido como
texto e os cabeçalhos não aparecerem, a versão do wrangler do build não leu o `_headers`.
`tests/test_cabecalhos_do_site.py` só garante o arquivo no repositório; quem responde é a
publicação.

**Concluído quando:** início, Termos e Privacidade abrem em HTTPS, inclusive no celular, e uma
mudança na `main` publica sozinha, o que foi exercitado em 03/10 com o PR #120. A publicação sozinha não libera
o piloto: os bloqueadores da seção 9 continuam valendo.

## 5. Configurar o retorno do Auth

Em **Authentication → URL Configuration**, preencha:

| Campo | Valor |
|---|---|
| Site URL | `https://radarestagio.com`, sem barra no final e sem curinga (desde 03/10/2026) |
| Redirect URLs | `https://radarestagio.com/**`; o `www` não entra, porque redireciona com 301 para o domínio |
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

No Cloudflare Turnstile, **na conta do grupo**, crie um widget gerenciado com os hostnames
`radarestagio.com`, `www.radarestagio.com` e `localhost` (testes locais). O widget que existia na
conta pessoal é de outro projeto e não serve. Guarde a **site key** pública para o frontend e a
**secret key** para **Authentication → Bot and Abuse Protection → CAPTCHA**, no Supabase.

**Ligado em 03/10/2026.** O site manda o token nas quatro chamadas que o Supabase exige
(cadastro, login, reenvio da confirmação e recuperação de senha), com teste de cada uma em
`tests/web/cadastro_test.ts`. A ordem importa: (1) a site key vai para `web/config.js`; (2) o site
publicado precisa mostrar o widget; (3) só então o CAPTCHA é ligado no Supabase, em
**Authentication → Attack Protection**, com a secret key. Ligado antes, todo cadastro, login,
reenvio e recuperação falham até o site publicar a chave, que é o que aconteceu por cerca de dez
minutos em 03/10, entre a ativação no Supabase e o merge do PR #120. A secret key vive só no
Supabase, nunca no repositório. Falta testar a expiração do desafio.
[CAPTCHA no Supabase](https://supabase.com/docs/guides/auth/auth-captcha).

**Concluído quando:** os fluxos passam com token válido e o servidor recusa o pedido sem token, o que foi conferido em 03/10.

## 6.1 Republicar as funções depois das correções de 10/09/2026

**Feito.** Pelo `supabase functions list` de 19/09, `ir` foi republicada em 10/09 e
`telegram-webhook` em 16/09, depois dos commits que mudaram o vínculo e o feedback. O código no ar não foi comparado com o
repositório nessa conferência. O procedimento fica como referência:

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
| Supabase → Edge Functions → Secrets | `URL_DA_LANDING` | `https://radarestagio.com` (desde 03/10/2026; `supabase secrets list` mostra só o hash do valor) |
| Supabase → Edge Functions → Secrets | `TELEGRAM_CHAT_ID` | o mesmo chat de operação do `.env` e do Actions; a `telegram-webhook` encaminha a ele as mensagens livres (a criar antes de publicar a função, ver `decisoes-do-banco.md`) |
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
- Vocabulário e métricas alinhados; a candidatura só tem emissor na pergunta do dia seguinte (05/10/2026).

O pipeline por perfil, o dispatch e a trava de concorrência foram implementados e validados
conforme o registro acima. Falta testar o cadastro completo pela interface publicada e
registrar respostas positivas e negativas reais no feedback.

As migrations `0013`–`0016` já aplicadas não serão reescritas. Correções futuras devem
entrar em novas migrations pelo histórico do projeto. Os avisos de rascunho
saíram das páginas em 02/10/2026, com versão e data coerentes com o aceite.

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
- Vínculo, primeira entrega, links e sete opções de feedback funcionam conforme os planos.
  A conta de teste recebe vagas reais: "Vaga encerrada" depois de abrir o link tira a vaga de
  todos por 30 dias, se estiver entre as três primeiras marcações da conta nesse período, mesmo
  que a conta seja pausada ou desvinculada depois. Confira esse botão só numa vaga que esteja
  mesmo fechada, ou toque no número de novo e escolha outra opção logo depois, ainda com a conta
  ativa e vinculada, o que desfaz a marcação.
- Edição, pausa, retomada, desvínculo e preferência de e-mail persistem após novo login.
- Download contém só os dados do dono, sem credenciais.
- Exclusão interrompe novas entregas/eventos e libera o chat; cancelamento preserva a pausa.
- Apagamento após a carência passa em ambiente de teste com datas controladas, incluindo duas
  contas no mesmo navegador. Não envelheça contas reais para testar.
- Métricas refletem os eventos e não contam cliques repetidos como vagas diferentes.

**Concluído quando:** resultados registrados e falhas corrigidas. Identifique as contas e
sessões de teste para separá-las das métricas do piloto.

## 11. Divulgar e ouvir colegas

O plano formal de piloto foi retirado por decisão do Igor em 07/09. Depois de conferir os
fluxos, pedir a alguns colegas que usem e relatem onde travaram e quais vagas serviram.
Não há obrigação de entrevistas, coorte, prazo de duas semanas ou metas de retenção.
A checklist vigente está no [plano geral](plano-geral.md#2-o-que-falta-antes-de-divulgar).

## 12. Registro de preparação da expansão — 08/09/2026

**Atualização de 19/09:** as `0018` e `0019`, pendentes neste registro, e as seguintes até a
`0031` constam como aplicadas; o job tem 30 minutos desde o #57. A tabela abaixo continua sendo
o retrato de 08/09.

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
- A definir: Redirect URLs, SMTP/Resend e Turnstile. Textos legais em vigor na versão
  `2026-10-08` (ver seção 2).
- A definir: conta/Telegram de teste e confirmação do cron-job.org. Igor acompanha
  `contato@radarestagio.com` desde 02/10/2026.
- A definir: domínio público final e autorização para qualquer relato de uso.
