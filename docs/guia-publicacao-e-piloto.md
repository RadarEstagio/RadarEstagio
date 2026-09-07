# Guia de publicação e piloto

**Atualizado em 06/09/2026.** O deploy foi parcial: os objetos das migrations `0014`–`0016`
estão no banco — mas **fora do histórico de migrations**, o que precisa ser reconciliado antes do
próximo push (seção 9) — e `ir` e `telegram-webhook` estão publicadas. O frontend continua sem
hospedagem e os documentos continuam como rascunhos, sem vigência.

Conferido no ambiente remoto em 06/09, nesta revisão:

- `supabase functions list`: `ir` e `telegram-webhook` **ativas**, publicadas em 05/09 às 21:13 e
  21:15 UTC — depois do merge do feedback de seis opções, às 18:35 UTC, então a versão no ar
  já o contém.
- Objetos das `0014`–`0016` presentes: as três colunas de consentimento, `cadastros_pendentes`,
  as quatro funções da `0014`, `baixar_meus_dados` e `verificar_perfil_da_interacao`.
- `validar_cadastro_radar` no ar é a versão que valida o **formato** da data, não a que tinha
  `2026-09-05` cravado: o deploy pegou o commit posterior à correção.
- `getWebhookInfo`: `allowed_updates` com `message` e `callback_query`, sem fila pendente e sem
  último erro.
- `supabase migration list --linked`: as `0014`–`0016` **não constam** como aplicadas. É a
  pendência da seção 9.

Estado registrado na atualização de 05/09 à noite, sem repetir os testes remotos nesta revisão:

- Contato funcionando; combinar a rotina de resposta com Ian e Miguel.
- Resend verificado e SMTP salvo; falta validar confirmação e recuperação reais.
- `URL_DE_RASTREIO` criada no GitHub; `URL_DA_LANDING` provisória aponta para o repositório.
- Token real validou redirecionamento 302 e registro de `vaga_aberta`.
- Primeira entrega real após `/start` em cerca de quatro minutos, sem requisições de IA.
- Trava por perfil implementada e validada com duas conexões no banco real.
- Relatório conferido com dados reais; feedback ainda zerado naquele teste.
- Hospedagem, retornos finais do Auth, Turnstile e cadastro completo continuam pendentes.
- Organização compartilhada no GitHub foi proposta; transferência ainda não confirmada.

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
- Bases legais por finalidade e condições de processamento internacional, logs e backups,
  conferidas nos serviços contratados; esses pontos ainda estão abertos nos rascunhos.
- Quem atenderá solicitações de dados e pedidos de eliminação sem aguardar arrependimento.
- Quem acompanha falhas do job e a rotina de apagamento.
- Quem paga a renovação do domínio, a data e o destino do domínio e das contas ao fim da disciplina.

Não retire o aviso de revisão antes de resolver as passagens pendentes e implementar as
promessas. Use a [lista de revisão](revisao-cadastro-e-privacidade.md).

**Concluído quando:** texto final revisado, contato ativo e responsabilidades registradas.

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

Quando as alterações estiverem no GitHub, abra **Workers & Pages → Create application →
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

## 5. Configurar o retorno do Auth

Em **Authentication → URL Configuration**, preencha:

| Campo | Valor |
|---|---|
| Site URL | `https://radarestagio.com` |
| Redirect URLs | `https://radarestagio.com` e `https://radarestagio.com/` |
| Desenvolvimento local | `http://localhost:8000` e `http://localhost:8000/` |

Inclua o endereço provisório exato se testar confirmação nele. Mantenha confirmação de e-mail
habilitada. Inclua também `https://radarestagio.com/?fluxo=recuperar` e, para teste local,
`http://localhost:8000/?fluxo=recuperar`, usados pela recuperação implementada.
[URLs de retorno do Supabase](https://supabase.com/docs/guides/auth/redirect-urls).

**Concluído quando:** a confirmação volta ao domínio correto. O teste em outro aparelho
deve ser repetido após aplicar a `0014` e publicar o frontend atualizado.

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

## 7. Rastreamento publicado — concluir o endereço da landing

| Onde | Nome | Valor |
|---|---|---|
| Supabase → Edge Functions → Secrets | `URL_DA_LANDING` | `https://radarestagio.com` |
| GitHub → Settings → Secrets and variables → Actions | `URL_DE_RASTREIO` | `https://xrhvjwemmylwbqgluebc.supabase.co/functions/v1/ir` |

Preserve os secrets existentes `TELEGRAM_BOT_TOKEN` e `TELEGRAM_WEBHOOK_SECRET` das funções.
As credenciais de banco das funções são fornecidas pelo ambiente Supabase. Nenhum segredo
entra em `web/config.js`; ali só cabe a chave publicável do projeto.

`ir` e `telegram-webhook` foram publicadas em 05/09. A tabela acima mostra os valores finais:
troque `URL_DA_LANDING`, hoje apontada provisoriamente para o repositório, quando o site subir. `supabase/config.toml` já define `verify_jwt = false`
para ambas: o webhook verifica o segredo do Telegram, e `ir` atende os links do navegador.

Confira a configuração do webhook: URL da função, mesmo segredo e `allowed_updates` contendo
`message` e `callback_query`. O plano registra isso como corrigido; não precisa rotacionar
o segredo apenas para republicar.

**Concluído quando:** abrir vaga grava `vaga_aberta`, token inválido volta à landing e cada
feedback grava o evento correto. Links antigos de conta excluída não podem gerar novos eventos.

## 8. Primeira entrega — implementada e validada

A execução sob demanda foi implementada usando `workflow_dispatch` com o input `perfil`.
A Edge Function lê o secret `GITHUB_DISPATCH_TOKEN`, com permissão de Actions para
`babue0/RadarEstagio`. Sem esse secret, o vínculo funciona e a busca fica para o diário.
O fluxo real levou cerca de quatro minutos no teste registrado. A trava por perfil foi
validada com duas conexões; execuções concorrentes aguardam e releem o histórico.
Confira a validade do token e reconfigure o acesso se o repositório mudar de organização.

Preserve o agendamento do cron-job.org às 07:23 de Brasília. Não adicione outro agendador.

**Concluído quando:** vínculo dispara apenas o perfil vinculado, repetição não duplica envio,
a janela de 06:23 a 07:23 aguarda o diário e os demais perfis continuam atendidos.

## 9. Código e validação antes do piloto

Implementado na `main`; migrations aplicadas e funções publicadas, frontend ainda não hospedado:

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

**As `0014`–`0016` foram aplicadas fora do histórico de migrations.** A conferência de 06/09
encontrou todos os objetos das três no banco — as colunas de consentimento, `cadastros_pendentes`,
as quatro funções da `0014`, `baixar_meus_dados` e `verificar_perfil_da_interacao` — mas nenhuma
das três registrada em `supabase_migrations.schema_migrations`. Para o Supabase elas nunca rodaram,
então o próximo `supabase db push` tentaria aplicá-las de novo e quebraria no primeiro `add column`
de coluna existente, deixando a migration seguinte pela metade.

O conserto é `supabase migration repair --status applied 0014 0015 0016`, que só grava as três como
aplicadas, sem reexecutar nada. **Conferir `supabase migration list --linked` antes do próximo
push**: enquanto a coluna `remote` das três estiver vazia, o histórico não descreve o banco.

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

## 11. Conduzir o piloto

Convide 10 a 20 estudantes por canais identificados, acompanhe por duas semanas e faça cinco
entrevistas. Confira diariamente falhas de confirmação e entrega. Meça a proporção semanal
de estudantes ativados com feedback positivo em ao menos uma recomendação; abertura sozinha
não prova utilidade.

Meça extrações, duração e custo com a diversidade real de cidades e áreas, que pode ampliar
as vagas elegíveis. Para avaliar o ranking, compare recusas com entregas de cada grupo;
não ajuste pesos por contagens brutas. Candidatura não será medida nesta versão.

Apagar contas abandonadas, reescrever o histórico Git e remover as skills não são pendências
deste lançamento: os planos já adiaram ou encerraram essas decisões.
