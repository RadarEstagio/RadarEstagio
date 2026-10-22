# Guia de publicação e piloto

Como configurar cada serviço, o que foi conferido no ambiente real e quando. Datas são de
evidência; a fila do que falta está no [plano geral](plano-geral.md). Use sempre o projeto
Supabase **`xrhvjwemmylwbqgluebc`**, da região de São Paulo; o `bnzogphdvpubtkcflcue` não é o
banco do Radar.

## Estado conferido

| Componente | Última conferência | Resultado |
|---|---|---|
| Site | 16/10/2026, `curl -I` | `https://radarestagio.com`, `/termos` e `/privacidade` respondem 200 com os quatro cabeçalhos do `web/_headers`; `/_headers` responde 404; `radarestagio.pages.dev` não resolve |
| Domínio e e-mail | 03/10/2026 | Domínio, site e Email Routing na conta Cloudflare do grupo; `contato@` recriado e testado; Resend "Verified" não reconferido |
| Auth | 05/10/2026 | Site URL `https://radarestagio.com`; Redirect URLs só com `https://radarestagio.com/**` e `http://localhost:8000/**` |
| Turnstile | 03/10/2026 | Widget no site; Supabase recusa pedido sem token (400 `captcha_failed`); expiração do desafio sem teste |
| Migrations | 22/10/2026, `supabase migration list --linked` | `0001` a `0036` aplicadas, iguais às locais (a numeração pula a `0029`) |
| Edge Functions | 17/10/2026, `supabase functions list` e `supabase functions download` | `telegram-webhook` (versão 24) e `ir` (versão 8) publicadas em 08/10 às 13:57, com o código igual ao da `main`; secret `TELEGRAM_CHAT_ID` criado |
| Webhook do Telegram | 17/10/2026, `getWebhookInfo` | `allowed_updates` com `message` e `callback_query`, sem fila nem erro |
| Rastreio | 03/10/2026 | `URL_DA_LANDING` em `https://radarestagio.com`; a `ir` manda token inexistente para o domínio novo |
| Primeira entrega | 05/09/2026 | Do `/start` à mensagem em cerca de quatro minutos; trava por perfil validada com duas conexões no banco real |
| Cadastro no domínio novo | 03/10/2026 | Igor confirmou cadastro e confirmação do e-mail; reenvio, recuperação, entrega, feedback e controles sem teste registrado |

Ao conferir de novo, atualizar a linha com data e comando, e o item correspondente no plano.

## 1. Contato

No Cloudflare, abra **Email Service → Email Routing**, selecione `radarestagio.com`, adicione e
verifique o e-mail pessoal de destino e crie em **Routing Rules** a regra `contato` →
encaminhar. Confira os registros DNS propostos antes de salvar e teste mandando uma mensagem de
outra conta para `contato@radarestagio.com`.
[Instruções do Cloudflare](https://developers.cloudflare.com/email-service/get-started/route-emails/).

A regra não acompanha uma mudança de conta: em 03/10 foi recriada com o mesmo destino na conta do
grupo. O envio da confirmação é configurado à parte, no Resend (seção 3).

## 2. Revisar os documentos e combinar a manutenção

Igor, Ian e Miguel são os responsáveis pelos dados nos [Termos](../web/termos.html) e na
[Política](../web/privacidade.html). A revisão fechou em 02/10/2026, e o aviso de rascunho saiu
das páginas.

- **Vigência:** em vigor está a versão `2026-10-08`, desde 08/10/2026, nos dois HTML, nos dois
  Markdown e em `VERSAO_DOS_TERMOS` de `web/assets/app.js`. O banco só aceita a versão como data
  (`AAAA-MM-DD`), e cada conta guarda a que aceitou. Aceites de versões anteriores continuam
  válidos: nenhuma versão até hoje acrescentou finalidade que exija consentimento novo.
- **`2026-10-02`:** primeira versão revisada.
- **`2026-10-05`:** a Política diz que a equipe lê as mensagens enviadas ao bot, encaminhadas ao
  chat de operação, com a base legal (art. 7º, V) e o que a exclusão da conta não apaga.
- **`2026-10-08`:** a Política nomeia os endereços que o navegador contata ao abrir qualquer
  página (`fonts.googleapis.com`, `fonts.gstatic.com`, `cdn.jsdelivr.net` e
  `challenges.cloudflare.com`) e inclui o jsDelivr na infraestrutura fora do Brasil; o porquê
  está no [contrato frontend](contrato-front.md). O texto de 07/10 sobre o tema guardado no
  navegador entrou sem trocar a versão, e esta corrige isso: mudança de texto legal muda a versão.

Para uma versão futura, no mesmo commit: nova data nos dois HTML (`legal-updated` e o parágrafo
final da seção de mudanças), nos dois Markdown, em `VERSAO_DOS_TERMOS` e na linha de vigência
acima. `tests/test_product_copy.py` confere que HTML e Markdown dizem o mesmo, frase a frase.

### Responsabilidades combinadas (02/10/2026)

- **Contato e pedidos de dados:** Igor responde `contato@radarestagio.com` e atende pedidos de
  dados e eliminação em até 5 dias úteis, sem esperar o prazo de arrependimento.
- **Falhas do diário e rotina de apagamento:** Igor lê o resumo que cada execução envia ao chat de
  operação. Execução que sai com código 1 ou resumo que não chega é investigada no mesmo dia.
- **Domínio:** Igor paga a renovação de `radarestagio.com` (04/09/2027), que desde 03/10/2026
  está na conta Cloudflare do grupo. Actions, cron-job.org e Supabase seguem em contas pessoais
  do grupo; ao fim da disciplina, transferir para quem continuar ou deixar o domínio expirar com
  aviso no site.

## 3. Configurar Resend e SMTP

No Resend, adicione `radarestagio.com` em **Domains**, copie para o Cloudflare os registros DNS
apresentados, preservando os MX do contato, espere a verificação e crie uma chave de API.

No Supabase, **Authentication → Email → SMTP Settings**, com SMTP personalizado:

| Campo | Valor |
|---|---|
| Sender name | `Radar de Estágio` |
| Sender email | `contato@radarestagio.com` |
| Host | `smtp.resend.com` |
| Port | `465` |
| Username | `resend` |
| Password | Chave de API do Resend |

A chave fica só nesse campo, nunca no frontend nem no Git.
[Configuração oficial do Resend](https://resend.com/docs/send-with-supabase-smtp). Confira os
limites de envio no Supabase Auth e no Resend e use templates em português com o nome Radar de
Estágio, preservando o link de ação. [SMTP no Supabase](https://supabase.com/docs/guides/auth/auth-smtp).
Domínio de teste como `@example.com` faz o Auth responder 500 "Error sending confirmation email":
é o SMTP recusando o domínio, não falha do fluxo.

**Concluído quando:** uma confirmação e uma recuperação reais chegam à conta de teste com o
remetente correto.

## 4. Hospedar o site e associar o domínio

Desde 03/10/2026 o site roda no **Workers com arquivos estáticos**, na conta Cloudflare do grupo,
que também tem o domínio. O `wrangler.jsonc` da raiz aponta a pasta `web/`; não há etapa de build.
O Pages anterior, na conta do Ian, foi apagado em 05/10/2026. Projeto Pages com muitos
deployments não se apaga pelo painel: é preciso apagar os deployments pela API
(`DELETE .../pages/projects/<nome>/deployments/<id>?force=true`) antes.

Para criar o projeto de novo, na conta do grupo: **Workers & Pages → Create application → Connect
GitHub** e escolha o repositório. O app Cloudflare Workers and Pages precisa estar instalado na
organização com acesso ao repositório, e isso só um owner da organização faz.

| Campo | Valor |
|---|---|
| Project name | `radarestagio`, igual ao `name` do `wrangler.jsonc`, senão o build falha |
| Production branch | `main` |
| Build command | em branco |
| Deploy command | `npx wrangler deploy` |
| Root directory | `/` |

O build de branch roda `wrangler preview`, que exige `"previews": {}` no `wrangler.jsonc` (PR
#122). O `uv sync` que aparece no log é do Cloudflare ao achar o `pyproject.toml` e não leva
segredo, porque o build não tem variáveis. Um merge na `main` publica sozinho em cerca de 30
segundos (conferido com o PR #120).

O domínio entra por **Settings → Domains & Routes → Add Domain** (`radarestagio.com`). O `www` não
se associa ao Worker: ele recebe um registro A `192.0.2.1` com proxy e uma regra em **Rules →
Redirect Rules** (modelo "Redirect from WWW to root", 301, preservando a query). Em **SSL/TLS →
Edge Certificates**, ligue "Always Use HTTPS" e deixe o HSTS desligado. Não altere os MX e os TXT
do e-mail. Para mudar o domínio de conta, a conta que recebe precisa cadastrá-lo antes como site
("Gaining account must first add the domain as a website"), e a zona antiga só se apaga depois de
aparecer como "Moved".

Trocar o endereço do site exige Site URL e Redirect URLs (seção 5) e `URL_DA_LANDING` (seção 7)
juntos.

### Cabeçalhos de resposta do site (08/10/2026)

O Workers com arquivos estáticos lê `web/_headers`, que não vai para o ar como arquivo, e manda
em `/*`:

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
  `frame-src`). As origens que a página usa hoje: `'self'` (`config.js`, `assets/app.js`,
  `assets/styles.css`, `assets/areas.json`, `assets/cidades.json`, `assets/adzuna-logo.png` e as
  ilustrações de `assets/areas/`), `https://cdn.jsdelivr.net` (o `@supabase/supabase-js@2.116.0`
  do `index.html`), `https://challenges.cloudflare.com` (o `turnstile/v0/api.js` que o `app.js`
  injeta, mais o iframe do widget), `https://fonts.googleapis.com` com `https://fonts.gstatic.com`
  e o host do Supabase que está no `web/config.js`. Três coisas seguram a lista: o script de tema
  no `<head>` das três páginas é inline, o que obriga `'unsafe-inline'` — e com ele a CSP deixa de
  barrar o XSS, que é o motivo dela — ou um hash que quebra calado a cada edição daquela linha; o
  Turnstile não dá para exercitar numa cópia local, porque o `config.js` local vai sem site key e
  o widget nem carrega, então o que ele injeta só apareceria em produção, onde um erro de CSP
  derruba login, cadastro e recuperação de senha de uma vez; e o host do Supabase mora no
  `config.js` enquanto a CSP moraria no `_headers`, de modo que trocar de projeto passaria a
  exigir os dois arquivos juntos. O caminho é publicar antes como
  `Content-Security-Policy-Report-Only`, abrir login, cadastro e recuperação no site publicado e
  ler o console, e só então trocar para o cabeçalho que bloqueia.
- **HSTS**, desligado, com "Always Use HTTPS" ligado no lugar.

**Conferir depois de cada deploy que mexa no `_headers`:** `curl -I https://radarestagio.com`,
`/termos` e `/privacidade` trazem os quatro cabeçalhos, e `curl -I
https://radarestagio.com/_headers` responde 404. Se o arquivo for servido como texto e os
cabeçalhos não aparecerem, a versão do wrangler do build não leu o `_headers`.
`tests/test_cabecalhos_do_site.py` só garante o arquivo no repositório.

## 5. Configurar o retorno do Auth

Em **Authentication → URL Configuration**:

| Campo | Valor |
|---|---|
| Site URL | `https://radarestagio.com`, sem barra no final e sem curinga |
| Redirect URLs | `https://radarestagio.com/**`; o `www` não entra, porque redireciona com 301 para o domínio |
| Desenvolvimento local | `http://localhost:8000/**` |

O site manda `emailRedirectTo` com a própria origem (`window.location.origin`), então a origem em
uso precisa estar na lista com o curinga `/**`; fora da lista, o Auth ignora o pedido e volta para
o Site URL. O curinga já cobre `/?fluxo=recuperar`, usado pela recuperação. Mantenha a confirmação
de e-mail habilitada. [URLs de retorno do Supabase](https://supabase.com/docs/guides/auth/redirect-urls).

Falha vista em 09/09: o Site URL apontava para um domínio ainda sem site. A conta era confirmada e
o perfil criado, mas a pessoa caía em "não é possível acessar esse site" e, ao clicar de novo, em
`otp_expired`. Depois de qualquer troca de endereço, repetir a confirmação em outro aparelho.

**Concluído quando:** a confirmação volta ao site publicado e mostra o botão do Telegram.

## 6. Turnstile

No Cloudflare Turnstile, **na conta do grupo**, crie um widget gerenciado com os hostnames
`radarestagio.com`, `www.radarestagio.com` e `localhost`. A **site key** pública vai para
`web/config.js` e a **secret key** para o Supabase, em **Authentication → Attack Protection**
(CAPTCHA). A secret key nunca entra no repositório.

A ordem importa: (1) a site key vai para `web/config.js`; (2) o site publicado precisa mostrar o
widget; (3) só então o CAPTCHA é ligado no Supabase. Ligado antes, cadastro, login, reenvio e
recuperação falham até o site publicar a chave, o que aconteceu por cerca de dez minutos em
03/10. O site manda o token nas quatro chamadas, com teste de cada uma em
`tests/web/cadastro_test.ts`. [CAPTCHA no Supabase](https://supabase.com/docs/guides/auth/auth-captcha).

## 7. Rastreamento e Edge Functions

| Onde | Nome | Valor |
|---|---|---|
| Supabase → Edge Functions → Secrets | `URL_DA_LANDING` | `https://radarestagio.com` (`supabase secrets list` mostra só o hash) |
| Supabase → Edge Functions → Secrets | `TELEGRAM_CHAT_ID` | o mesmo chat de operação do `.env` e do Actions; a `telegram-webhook` encaminha a ele as mensagens livres e precisa dele antes de ser republicada |
| Supabase → Edge Functions → Secrets | `GITHUB_DISPATCH_TOKEN` | token com permissão de Actions em `RadarEstagio/RadarEstagio`, para a entrega imediata (seção 8) |
| GitHub → Settings → Secrets and variables → Actions | `URL_DE_RASTREIO` | `https://xrhvjwemmylwbqgluebc.supabase.co/functions/v1/ir` |

Preserve os secrets `TELEGRAM_BOT_TOKEN` e `TELEGRAM_WEBHOOK_SECRET` das funções; as credenciais
de banco delas vêm do ambiente do Supabase. Nenhum segredo entra em `web/config.js`.

O `TELEGRAM_WEBHOOK_SECRET` vive em três lugares que precisam do mesmo valor: o `setWebhook` no
Telegram, os secrets do Supabase e os `.env` locais. Divergência vira 401 silencioso em todo
update: em 04 e 05/09/2026 um re-registro usou o segredo de um `.env` dessincronizado, e cliques e
vínculos se perderam por cerca de 12 horas. O `setWebhook` leva
`allowed_updates=["message","callback_query"]`: o registro original só aceitava `message`, e o
Telegram descartava os cliques dos botões de feedback antes de chegarem à função (corrigido em
04/09/2026). Ao mexer no webhook, conferir `getWebhookInfo`: `last_error_message` vazio e
`pending_update_count` zerando. Com o webhook ativo, `getUpdates` deixa de funcionar nesse bot.
`supabase/config.toml` define `verify_jwt = false` para as duas: o webhook confere o segredo do
Telegram, e a `ir` atende links do navegador.

Republicar depois de mudar o código de uma função:

```bash
supabase functions deploy ir
supabase functions deploy telegram-webhook
```

Nenhum secret muda e o webhook não precisa ser re-registrado. Depois do deploy, confira
`getWebhookInfo` sem `last_error_message`, com `allowed_updates` contendo `message` e
`callback_query`, e abra um link de vaga para ver o 302 de sempre.

**Concluído quando:** abrir vaga grava `vaga_aberta`, token inválido volta à landing, cada
feedback grava o evento certo e link antigo de conta excluída não gera evento.

## 8. Primeira entrega

O vínculo dispara `workflow_dispatch` com o input `perfil`, lendo o `GITHUB_DISPATCH_TOKEN`. Sem
ele, o vínculo funciona e a busca fica para o diário. Confira a validade do token e reconfigure o
acesso se o repositório mudar de organização (`REPOSITORIO` em `entrega_imediata.ts` é
constante). Os disparos do diário pelo cron-job.org e o vigia estão na seção 12.

**Concluído quando:** o vínculo dispara só o perfil vinculado, repetir não duplica envio, a janela
de 06:23 a 07:23 espera o diário e os demais perfis continuam atendidos.

## 9. Migrations

Toda mudança de banco entra em migration nova, aplicada com `supabase db push`; migration já
aplicada nunca é reescrita. Antes de aplicar, ler a "Publicação" da decisão correspondente nas
[decisões do banco](decisoes-do-banco.md): ela diz se vai antes ou depois do merge e quando o push
pede `--include-all`. **Conferir `supabase migration list --linked` depois de aplicar e antes do
próximo push**: SQL rodado fora do CLI não entra no histórico e quebra o push seguinte, como em
06/09 com as `0014` a `0016`.

## 10. Conferência final com conta de teste

Use dados sintéticos e seus próprios endereços e Telegram:

- Cadastro sem aceite é recusado; e-mails opcionais começam desmarcados.
- Cadastro no computador e confirmação no celular recuperam o perfil correto.
- Link expirado, reenvio e login antes da confirmação têm saídas claras.
- Recuperação troca a senha e permite entrar com a nova senha.
- Vínculo, primeira entrega, links e as sete opções de feedback funcionam, e a pergunta do dia
  seguinte chega depois de uma abertura sem resposta. A conta de teste recebe vagas reais:
  "Vaga encerrada" depois de abrir o link tira a vaga de todos por 30 dias, se estiver entre as
  três primeiras marcações da conta nesse período, mesmo que a conta seja pausada ou desvinculada
  depois. Confira esse botão só numa vaga que esteja mesmo fechada, ou toque no número de novo e
  escolha outra opção logo depois, com a conta ativa e vinculada, o que desfaz a marcação.
- Mensagem livre ao bot recebe "Recebemos sua mensagem" e chega ao chat de operação.
- Edição, pausa com motivo, retomada, desvínculo e preferência de e-mail persistem após novo login.
- Download contém só os dados do dono, sem credenciais.
- Exclusão interrompe entregas e eventos e libera o chat; cancelamento preserva a pausa.
- Apagamento após a carência passa em ambiente de teste com datas controladas, incluindo duas
  contas no mesmo navegador. Não envelheça contas reais para testar.
- Métricas refletem os eventos e não contam cliques repetidos como vagas diferentes.
- Landing, FAQ, cadastro e conta em 375 px e 1280 px, com teclado, foco e sem overflow; o JSDOM
  não verifica layout.

Para `rodar --perfil` com uma conta já atendida, zere `entrega_imediata_atendida_em` antes.
Abra o site com `?utm_source=equipe` e anote as contas de teste, para separá-las das métricas.

**Concluído quando:** resultados registrados no [plano](plano-geral.md#22-testar-com-uma-conta-da-equipe)
e falhas corrigidas.

## 11. Divulgar e ouvir colegas

Depois de conferir os fluxos, pedir a alguns colegas que usem e relatem onde travaram e quais
vagas serviram, com um `utm_source` por canal. Não há obrigação de entrevistas, coorte, prazo ou
metas de retenção. A checklist vigente está no
[plano geral](plano-geral.md#2-o-que-falta-antes-de-divulgar).

## 12. Agendamento, tokens e CI do GitHub

O [workflow diário](../.github/workflows/radar-diario.yml) só tem `workflow_dispatch`: o
`schedule` nativo ficou dois dias sem disparar e foi removido. Quem dispara é o cron-job.org, que
chama a API `dispatches` com token fine-grained.

O diário é disparado por **dois jobs no cron-job.org** (21/10/2026), porque o serviço não tem retry
próprio. Os dois são iguais, e o segundo nasceu como clone do primeiro (Actions → Clone), para o
token não precisar ser copiado à mão. A configuração, sem o token:

| Campo | `RadarEstagio` | `RadarEstagio (reforço)` |
|---|---|---|
| URL | `https://api.github.com/repos/RadarEstagio/RadarEstagio/actions/workflows/radar-diario.yml/dispatches` | a mesma |
| Horário | todo dia às 07:23, fuso `America/Sao_Paulo` | todo dia às 07:58, mesmo fuso |
| Método, cabeçalhos e corpo | os que a API de `dispatches` exige (`POST`, token fine-grained, `ref` da `main`), conferidos pelo `204` de 20/10; a aba Advanced não foi aberta para não expor o token | os mesmos, pelo clone |
| Timeout | 30 s, o teto do plano gratuito | o mesmo |
| Resposta de sucesso | `204 No Content` | a mesma |

O segundo disparo é seguro desde o G03: quem já recebeu a mensagem do dia de Brasília fica de fora,
e se todos já receberam o diário termina sem coletar e sem avisar o chat de operação. Nos dias de
falha ele atende só quem ficou sem mensagem. Às 07:58 o primeiro run já passou do teto de 30
minutos, então o segundo não fica pendente na `concurrency`, onde uma entrega imediata o cancelaria.
Mudar o horário de um dos jobs exige conferir a janela da entrega imediata (G09). Não adicione um
terceiro agendador sem rever essa conta. Os dois jobs usam o mesmo token, que vence em 09/09/2027.

O vigia não é agendador de reserva (21/10/2026). `vigia-do-radar-diario.yml` roda às 09:13 de
Brasília pelo `schedule` do Actions, confere pela API se houve run do diário concluído com
sucesso no dia e, se não houve, avisa o chat de operação com o estado encontrado e o link para
rodar o diário à mão. Ele só lê. O diário e a entrega imediata se distinguem pelo `run-name`
("Radar diário" e "Entrega imediata"), porque a API de runs não devolve os inputs. Para
testar, rode o vigia pelo botão *Run workflow*: num dia sem diário ele fica vermelho e avisa.
Limite conhecido: o GitHub desliga o `schedule` de repositório público depois de 60 dias sem
atividade, e o cron-job.org continuaria disparando sem vigia; reative em Actions se o projeto
parar. Motivo: em 21/10/2026 o cron-job.org deu timeout no disparo, nenhum run nasceu e o
único aviso foi o e-mail dele na caixa pessoal de quem tem a conta.

Na transferência de `babue0/RadarEstagio` para `RadarEstagio/RadarEstagio` (08/09/2026), commits,
autores, issues e PRs foram preservados e o GitHub redireciona o endereço antigo; o que quebrou foi
a ligação das automações, porque cada uma guardava o dono no nome:

- **cron-job.org**: mudam a URL **e o token**. Token fine-grained é preso ao dono, então o antigo
  para de enxergar o repositório mesmo com a URL certa. O teste bem-sucedido responde **204 No
  Content** com corpo vazio; 404 é token apontando para a conta pessoal e 403 é falta de
  `Actions: Read and write`.
- **Antes de gerar os tokens**, a organização precisa liberar tokens fine-grained (Settings →
  Personal access tokens). Sem isso o token nasce válido e a API responde 404, sem dizer por quê.
- **Entrega imediata**: trocar só o `GITHUB_DISPATCH_TOKEN` não basta, porque `REPOSITORIO` em
  `entrega_imediata.ts` é constante (seção 8).
- Os secrets do Actions sobreviveram à transferência. O token do cron **vence em 09/09/2027**:
  quando vencer, os dois disparos param e só o vigia das 09:13 avisa.

**Ações por hash e token só de leitura (13/09/2026).** O job diário recebe os segredos de
produção, e o dono de uma ação pode mover a tag dela para outro commit. Por isso toda `uses:`
aponta para o hash de 40 caracteres e todo workflow declara `permissions: contents: read` no topo;
permissão maior só no job que precisar, com o motivo no commit. O checkout leva
`persist-credentials: false`, para o token não ficar no `.git/config` ao alcance do radar e das
dependências, e o `setup-uv` instala o uv `0.12.5`, o mesmo usado localmente: sem `version:` ele
baixaria o mais novo, que roda no passo dos segredos. `tests/test_workflows.py` cobra essas regras
e guarda em `VERSAO_DE_CADA_ACAO` a versão de cada hash, porque o YAML não leva comentário. O
Dependabot abre um PR semanal das ações, 7 dias depois de cada versão sair, e o teste falha até
alguém registrar no mapa a versão nova, conferida com `git ls-remote`. A versão do uv o Dependabot
não toca: sobe à mão, junto com o uv local.
