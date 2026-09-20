# Decisões do banco e das funções

Por que o schema, as migrations, o webhook e o resumo de operação são como são, com as medições
e os limites aceitos de cada decisão. Movido do `CLAUDE.md` em 20/09/2026 sem reescrita: cada
seção guarda a data da decisão, e "hoje" se refere a essa data. As regras que valem no dia a dia
ficam resumidas no `CLAUDE.md`; o contrato com o site está em [contrato frontend](contrato-front.md).

## Exclusão de conta é em duas etapas (04/09/2026)

`excluir_minha_conta()` marca `excluida_em`
e solta o chat do Telegram, porque a coluna é `unique` e segurá-la reservaria o chat por 60 dias
contra uma conta nova da própria pessoa. Quem para a entrega é o `excluida_em is null` na consulta
dos perfis, e a policy de update recusa escrita em perfil marcado. O apagamento
definitivo vem no job diário, depois de `DIAS_ATE_APAGAR_CONTA_EXCLUIDA`, e leva junto os eventos
anteriores ao login, que só têm `sessao_id` e nenhuma cascata alcança. A sessão **não** é
encerrada ao pedir: sem ela a pessoa não voltaria para cancelar.
**O apagamento tem teste que roda o SQL (18/09/2026).** Até aqui nada executava as três
consultas de `apagar_contas_excluidas` no CI: quem as cobria era `tests/test_storage_postgres.py`,
que pede `DATABASE_URL_TESTE` e fica de fora. A auditoria de 17/09 inverteu o sinal do prazo numa
cópia do repositório e as suítes passaram verdes, o que na produção apagaria quem acabou de pedir
exclusão. `tests/web/apagamento_de_contas_test.ts` aplica as migrations no PGlite e roda as
consultas lidas do `postgres.py`, na ordem do repositório (sessões, eventos sem dono, contas):
conta marcada há menos que a carência fica, marcada há mais sai com perfil, avaliações, envios e
eventos, conta ativa e pausada não são tocadas, e a sessão dividida com outra conta perde só os
eventos sem dono. Os 60 dias são decisão de produto e ficaram presos por dois testes: o padrão de
`dias_ate_apagar_conta_excluida` em `tests/test_settings.py` e a política de privacidade, que lê o
número do próprio campo em `tests/test_product_copy.py`. Mutações que passavam e agora quebram:
inverter o sinal no `delete` (as quatro do arquivo novo), invertê-lo na consulta das sessões
(três delas), neutralizar a condição do prazo (a da carência e a do navegador dividido) e trocar
60 por 7 (os dois testes do prazo). O prazo do cadastro pendente e o da conta não confirmada da
`0030` já estavam cobertos por `tests/web/prazo_do_cadastro_test.ts`, conferido pelas mesmas
mutações. Limites: o teste roda as consultas na ordem do repositório, não o método em Python, e
o PGlite tem uma conexão só, então a transação e a corrida entre execuções seguem sem teste; e o
`auth.users` do PGlite é o mínimo que as migrations exigem, então a cascata das outras tabelas do
Auth do Supabase (sessões, tokens) não é exercitada.

## Conta confirmada sem perfil é apagada na hora (13/09/2026, `0024`)

Quem confirmava o e-mail
e não salvava o perfil ficava com e-mail e senha no Auth sem saída: a exclusão marca
`perfis.excluida_em` e o job só apaga a partir de `perfis`. `apagar_minha_conta_sem_perfil()` é
`security definer`, sem argumento, filtrada por `auth.uid()` e executável só por
`authenticated`; recusa conta com perfil, que segue as duas etapas, e trava a linha do Auth antes
de conferir, para não correr com um perfil sendo criado. Apaga o que o job apagaria: os eventos
anônimos das sessões da conta e o usuário do Auth, que leva o resto por cascata. Sem prazo porque
os 60 dias existem para cancelar sem perder perfil e histórico, e sem perfil não há o que
preservar; reter o e-mail sem finalidade vai contra a LGPD. Um registro para o job apagar
exigiria tabela nova e mudança no `radar/`. O site oferece "Excluir minha conta" sob o formulário
de completar o perfil, com a confirmação de sempre (que saiu de dentro de `#account-state` para
abrir nesse estado), e encerra a sessão local depois. Publicação: `db push` antes do merge, porque
o site novo chama a função e o atual não a conhece. Se a `0024` subir antes da `0023`, o push da
`0023` pede `--include-all`.

## Cadastro que não confirma o e-mail tem prazo (16/09/2026, `0030`)

O cadastro ia para
`cadastros_pendentes` no `signUp` e só saía na confirmação: quem nunca confirmava deixava ali para
sempre curso, cidade, habilidades e a resposta sobre deficiência, e a conta ficava no Auth. Refazer
o cadastro não trocava nada: no GoTrue 2.196 (`internal/api/signup.go`), `signUp` com e-mail já
cadastrado e não confirmado não regrava metadados nem senha ("do not update the user because we
can't be sure of their claimed identity"), só reenvia o link, gravando `confirmation_token` e
`confirmation_sent_at`, com 429 se o último envio tem menos de 60 s. O cadastro novo nunca chegava
ao banco, a confirmação criava o perfil com o antigo e o `concluir_meu_cadastro` seguinte não o
trocava (`on conflict do nothing`). E esse mesmo `signUp`, feito por quem sabe o e-mail de alguém
que ainda não confirmou, devolve o usuário real com `identities[].identity_data`, para onde o Auth
copia os metadados do `signUp`: a `0027` só limpou `raw_user_meta_data`, e em 16/09 5 das 6
identidades ainda tinham `cadastro_radar`, lidas por qualquer um nesse caso. O que mudou:
- **Todo link depois do primeiro descarta o pendente** (gatilho `after update of
  confirmation_sent_at`, com a conta não confirmada e `confirmation_sent_at` já preenchido antes).
  O banco não distingue a pessoa refazendo o cadastro, o "Reenviar confirmação" e um terceiro com
  o e-mail dela, porque `auth.resend` grava as mesmas duas colunas. Trocar pelo cadastro novo não
  dá, porque o Auth não o entrega, e se desse um terceiro trocaria o perfil de outra pessoa;
  descartando, quem confirma cai em "Complete seu perfil" e preenche de novo, o que percebe. Custo
  aceito: quem só reenvia o link, por não achar o e-mail, também preenche de novo.
- **A identidade não guarda o cadastro**: gatilho `before insert or update` em `auth.identities`,
  como o da `0027` em `auth.users`, e a migração limpa as antigas. A cópia para
  `cadastros_pendentes` lê a inserção em `auth.users`, que vem antes da identidade.
- **O job apaga o pendente recebido há mais de 2 dias e a conta não confirmada 30 dias depois do
  último link** (`DIAS_ATE_APAGAR_CADASTRO_PENDENTE` e `DIAS_ATE_APAGAR_CONTA_NAO_CONFIRMADA`, no
  `pipeline.py`), com os eventos anônimos das sessões da conta, como na conta excluída; a cascata
  leva o pendente, a identidade e os eventos da conta. Conta com perfil ou sem link enviado
  (criada no painel) fica. Dois dias porque o pendente só serve ao primeiro link, que vale 24 h no
  padrão do GoTrue; trinta porque `metricas` lê a coorte de 30 dias, e apagar antes tiraria do
  funil quem não confirmou, o abandono que ele deve mostrar. São constantes, não variáveis de
  ambiente, porque a política de privacidade promete os números e
  `test_politica_de_privacidade_diz_os_prazos_do_cadastro_nao_confirmado` os lê delas. Falha ao
  apagar só avisa no log.

Medido em 16/09, só leitura: nenhum pendente, nenhuma conta sem confirmar, as 6 contas confirmaram
entre 0,02 s e 147 s depois do link e nenhuma pediu outro; o banco não tem `pg_cron`. Os testes
repetem em PGlite as escritas do GoTrue (`cadastro_pendente_test.ts`,
`metadados_do_cadastro_test.ts` e `prazo_do_cadastro_test.ts`, que lê o SQL do `postgres.py`), e
os bancos de teste ganharam `confirmation_sent_at` e `auth.identities`. Limites: o GoTrue mantém a
senha do primeiro `signUp`, então quem cadastra antes o e-mail de outra pessoa conhece a senha da
conta que ela confirmar; o descarte tira os dados dele do perfil, não a senha, e só o prazo de 30
dias, renovado a cada link (que chega ao e-mail da pessoa), fecha a janela. Um aviso no site para
usar "Esqueci a senha" ficou de fora. `signUp` repetido em menos de 60 s, ou com o limite de
e-mails do Auth esgotado, volta 429 sem gravar nada, e o primeiro link ainda cria o perfil com o
cadastro antigo. Reenvio pedido depois de a conta ser apagada responde 200 sem mandar e-mail; quem
tenta entrar vê "E-mail ou senha incorretos" e cadastra de novo. Os 2 dias supõem "Email OTP
Expiration" de até 24 h no painel, a conferir; se for maior, a confirmação tardia só pede o perfil
de novo. Publicação: `db push` da `0030` antes do merge, para o descarte valer quando a política
já o descreve; invertida, nada quebra, porque o SQL do job não depende da `0030`. Conferir depois
do push: `select count(*) from auth.identities where identity_data ? 'cadastro_radar'` deve dar
zero. Se a `0030` subir antes da `0028` ou da `0029`, o push delas pede `--include-all`.

## SQL aplicado fora do CLI não entra no histórico de migrations (06/09/2026)

As `0014`–`0016`
tinham todos os objetos no banco e nenhuma linha em `supabase_migrations.schema_migrations`.
Como o `db push` grava o registro na mesma transação em que aplica, três aplicadas e nenhuma
registrada denunciam SQL rodado direto — pelo painel, por `db query` ou por psql. O efeito só
aparece depois: com a coluna `remote` vazia, o push seguinte tenta reaplicá-las e quebra no
primeiro `add column` de coluna existente, deixando a migration nova pela metade. Foi
reconciliado com `supabase migration repair --status applied 0014 0015 0016`, que só grava o
registro e não reexecuta SQL. **Conferir `supabase migration list --linked` depois de aplicar e
antes do próximo push** — é o que torna visível a regra de nunca aplicar pelo painel.

## Texto que o Postgres recusa sai na entrada (16/09/2026)

. Dois caracteres vindos da fonte ou
da IA quebravam as gravações. O surrogate solto, metade de um emoji (o resumo de 500 caracteres
da API cortado no meio do par chega escapado no JSON), não se codifica em UTF-8: o psycopg
levanta `UnicodeEncodeError`, que não é `psycopg.Error`, e o job caía na primeira gravação,
antes de qualquer envio e sem resumo de operação, todo dia enquanto a vaga estivesse na janela
(a `/land/ad/` nunca é enriquecida e guarda sempre o trecho da API); o `httpx` do Telegram
levanta o mesmo erro. O NUL o Postgres recusa em `text` e em `jsonb` com `DataError`, e como
extrações, dias sem extração, avaliações e envios de um usuário vão cada um numa transação, uma
vaga assim fazia nenhuma extração do run ser gravada (todas pagas de novo no dia seguinte), a
retenção da `0022` não contar o dia e o envio não ser gravado, e a mesma mensagem voltava todo
dia. As duas falhas foram reproduzidas num Postgres local com todas as migrations, rodando o
pipeline com o coletor da Adzuna, o agy e o Telegram atrás de `httpx.MockTransport`. A limpeza é
feita uma vez, nos modelos: `Vaga` e `ExtracaoDaVaga` passam todo texto por
`sem_caracteres_invalidos` (`domain/texto.py`), que tira NUL e surrogate solto e junta as duas
metades de um emoji que chegam separadas; nenhum outro caractere muda (acento, travessão, `<`,
`&`, emoji inteiro, `�`). O validador da `Vaga` cobre os três coletores, e o da extração cobre
a resposta do Gemini, a do agy e a leitura do cache; o enriquecimento limpa a descrição da
página por conta própria, porque o `model_copy` não valida. A identidade das vagas guardadas não
muda, porque o banco nunca aceitou esses caracteres, e o schema da extração é o mesmo:
`VERSAO_DA_EXTRACAO` segue `7efdbc95`. Como defesa, `guardar_extracoes`,
`registrar_vagas_sem_extracao`, `guardar_avaliacoes` e `registrar_envios` tratam o
`UnicodeEncodeError` como falha do banco (`FALHAS_AO_GRAVAR_TEXTO`): aviso do dia, não queda.
Medido em 16/09, só leitura: nenhuma das 1.003 vagas nem das 790 extrações tem `�` ou NUL
escapado, e nenhuma das 966 vagas da Adzuna tem emoji ou outro caractere fora do plano básico;
as 18 com emoji são da Gupy, com a descrição inteira. Não se sabe se a Adzuna manda esses
caracteres, e a correção é para não depender disso. Limites: gravar cada extração em separado,
para uma ruim não levar as outras, ficou de fora, porque depois da limpeza nenhum texto da
extração é recusado e o que sobra para falhar é o banco inteiro; o `model_validate_json` recusa
a resposta do Gemini inteira se ela trouxer um surrogate solto escapado (erro de avaliação, o
lote se divide até isolar a vaga), o que só acontece se o modelo o inventar, já que o prompt sai
limpo; corpo da Adzuna com byte UTF-8 inválido continua sendo corpo que não é JSON (ver "Coleta
resiliente"); e os testes do storage são de integração, fora do CI. Publicação: sem migration
nem deploy.

## Toda execução se reporta

ao `TELEGRAM_CHAT_ID`, que com banco passa a ser o chat de
operação: usuários ativos, quantos receberam recomendação, vagas enviadas e requisições. Kill
por timeout, que o Python não consegue reportar, é coberto pelo passo `if: failure() ||
cancelled()` do workflow. O passo do radar tem timeout próprio (28 min, abaixo dos 30 do job)
para o estouro contar como falha do passo: o GitHub trata o estouro do job como cancelamento,
e a documentação não diz se `failure()` vale nesse caso.
**Código de saída honesto e resumo que denuncia (18/09/2026).** Com o token do bot revogado o
Telegram recusa tudo: ninguém recebia mensagem, o resumo também falhava, o processo terminava
em zero e o Actions ficava verde. Agora `rodar` e `testar-local` levantam `ErroDeExecucao`
(`pipeline.py`) e saem com código 1 em dois casos, cada um com teste próprio:
- **o resumo não chegou ao chat de operação**: execução que não se relata não pode ser lida
  como verde, e é o caso do token revogado. Sem `TELEGRAM_CHAT_ID` não há resumo e o critério
  não vale.
- **ninguém foi atendido por falha**: havia usuários na execução, nenhum recebeu mensagem
  alguma (nem recomendação nem "nenhuma vaga compatível") e ao menos um ficou sem por **falha
  de verdade** — revalidação indisponível, banco fora do ar, envio recusado pelo Telegram por
  erro nosso ou indisponibilidade dele.

Não são falha, de propósito: o dia legítimo em que todos recebem "nenhuma vaga compatível"; a
execução sem usuários ativos, inclusive `rodar --perfil` sem entrega a fazer; a execução em que
parte falhou mas ao menos um recebeu, porque a falha de um usuário não derruba os outros e o
resumo já mostra o número; o destinatário que bloqueou o bot ou sumiu (o 403 e o 400 que
nomeia o destinatário), que é escolha dele e já leva à pausa por `FALHAS_DE_ENVIO_ATE_PAUSAR`;
e a **mensagem segurada** por vaga sem extração ou coleta incompleta, que é comportamento
deliberado (ver "Falha parcial virava 'nenhuma vaga compatível'" e "Coleta resiliente"): a
pessoa fica pendente para a execução seguinte e o resumo tem linha própria para o caso. Pintar
isso de vermelho deixava toda entrega imediata cujo candidato ainda não foi extraído terminar
em vermelho, e alarme que toca sozinho todo dia deixa de ser lido. Falha de verdade ao lado de
uma mensagem segurada continua derrubando a execução.
O `ErroDeExecucao` é levantado no `__main__`, depois de gravar o uso da Adzuna e de mandar o
resumo, então a execução vermelha não desfaz o que entregou nem perde a linha `adzuna:diario`.
O resumo ganhou, no estilo dos avisos que já tinha, o que só existia no log: "⚠️ Usuários sem
mensagem por falha", "⚠️ Mensagens seguradas por vaga sem extração", "⚠️ Mensagens seguradas
pela coleta incompleta", "⚠️ Usuários com envio não gravado" (a mensagem chegou e a linha de
`envios` não: a pessoa recebe as mesmas vagas amanhã) e "⚠️ Limpeza de contas falhou:
<motivo>", uma linha por motivo entre conta excluída e cadastro não confirmado. Limites
aceitos: **um dia inteiro de Gemini fora deixa todos sem mensagem e a execução segue verde**,
com "⚠️ Vagas sem extração" e "⚠️ Mensagens seguradas por vaga sem extração" no resumo — quem
opera precisa ler o resumo, o código de saída não conta essa história; o mesmo vale para a
Adzuna que não responde depois da primeira vaga. Quando o resumo não sai, o aviso do passo
`if: failure()` usa o mesmo token e falha junto, então o vermelho do run é o único sinal. E
segue passando por verde o dia em que um recebeu e vinte falharam, que só o número no resumo
denuncia.

## Eventos do site têm limite no banco

(13/09/2026, migration `0023`). A chave pública deixava
inserir em `eventos_produto` sem fim, trocando de `sessao_id` a cada requisição e com 4 KB de
propriedades, e banco cheio no plano gratuito fica só leitura, o que para cadastro, vínculo e
diário. Evento `web` agora tem propriedades de até 256 bytes, no máximo 60 por sessão e 60 por
conta na última hora e um teto por hora de 2.400 para visitantes e 900 para contas
(`teto_de_eventos_do_site_por_hora`, contados em `eventos_do_site_por_hora`); acima disso o
insert falha com `PT429` (HTTP 429 no PostgREST) e o site só avisa no console. O teto é o que
limita o tamanho, porque limite só por sessão se fura trocando de sessão. Ele comporta um dia de
divulgação: 150 cadastros numa hora, cada um com ~10 eventos anônimos (funil com idas e voltas)
e 6 de conta, mais 3 curiosos por cadastro com landing e CTA; o primeiro teto, 600, perdia
metade dos eventos anônimos de uma turma de 150. Pior caso sob abuso contínuo: 79.200 linhas por
dia, de 440 a 490 bytes cada com índices, ~35 MB por dia, o que enche 500 MB em ~2 semanas. Por
isso o resumo de operação mostra os eventos do site das últimas 24 h e avisa quando algum teto
foi atingido; banco sem a tabela ou leitura que falha só gera aviso no log. Eventos do banco e do
Telegram não passam pelo gatilho. Custo aceito: sob abuso, os eventos anônimos legítimos daquela
hora se perdem e o funil conta visitantes falsos até o teto. Deduplicar marcos por sessão ficou
de fora, porque o funil já conta pessoas distintas. O check de 256 bytes é `not valid`: não
confere as linhas antigas, mas barra `update` futuro de linha web antiga maior que isso; hoje
nada atualiza linha web. A `0023` pode ir ao banco antes do merge: o site atual já grava dentro
dos limites.

## Aberturas, pausas e vínculos repetidos

(16/09/2026, migration `0028`). O limite da `0023`
só vale para evento `web`, e dois caminhos ainda gravavam sem fim: cada GET no link rastreável
grava um `vaga_aberta`, então um script chamando em laço o link de uma mensagem encaminhada
enchia `eventos_produto`; e cada volta de pausar e retomar por `update` direto na própria linha
de `perfis` gravava um `entregas_pausadas`. Desvincular pela RPC e mandar `/start` de novo
gravava um `telegram_vinculado` por volta, pelo mesmo gatilho da `0005`. O gatilho
`z_descartar_eventos_repetidos` descarta, sem erro (`return null`), o `vaga_aberta` de um par
`(perfil_id, vaga_id)` que já tem um, e o `entregas_pausadas` ou `telegram_vinculado` do mesmo
perfil a menos de um dia (por `ocorrido_em`) do anterior. Descarte, e não `PT429` como na
`0023`, porque o `update` de pausa não pode falhar por causa do evento e abrir de novo não é
erro: o estado do perfil muda sempre, o motivo da pausa fica em `perfis.motivo_pausa` (o evento
nunca o levou) e a `ir` redireciona como antes. Sem teto por hora nem aviso no resumo de
operação: fica sempre a primeira ocorrência, então abuso não apaga evento legítimo, e o tamanho
fica preso ao que o Radar controla, uma abertura por envio (`envios` tem chave
`(perfil_id, vaga_id)`) e duas linhas por perfil por dia. Nenhum número muda porque os leitores
já tratam repetição: o `metricas.sql` conta pares distintos com abertura depois do envio, a
primeira abertura e pessoas distintas por etapa, e `perfis_vinculados` e `SQL_VAGAS_ENCERRADAS`
perguntam se o evento existe; a encerrada quer abertura anterior ao voto, e a primeira é a mais
antiga. A abertura trava o par com `pg_advisory_xact_lock` antes de conferir, para GETs
simultâneos não passarem juntos; pausa e vínculo já são serializados pela trava da linha de
`perfis`. O prefixo `z_` faz o gatilho rodar depois de `verificar_perfil_da_interacao`, e
abertura de conta pausada segue recusada com `42501`. Medido em 16/09, só leitura: 379 eventos;
41 `vaga_aberta` em 31 pares (24 com uma, 6 com duas, 1 com cinco), repetições de 1 s a 37 min,
no máximo 7 aberturas por perfil numa hora e 7 no banco inteiro; 2 `entregas_pausadas`, do mesmo
perfil, a 5 dias uma da outra; 4 `telegram_vinculado`, um por perfil. Aplicada a esse histórico,
a regra descartaria as 10 aberturas repetidas, e o funil de 7, 30 e 365 dias e as vagas
encerradas saem iguais. `tests/web/eventos_repetidos_test.ts` monta o mesmo histórico com e sem
o gatilho (repetições, feedback corrigido, voto de encerrada antes e depois da abertura, pausas e
revínculos em laço) e exige as mesmas métricas. Limites: a segunda pausa e o revínculo do mesmo
dia e as reaberturas somem do histórico bruto, e um leitor futuro de "última abertura" ou de
pausas por dia não os terá; GET em laço ainda executa a `ir` com duas consultas, o que não cresce
o banco mas gasta invocações de Edge Function, que têm cota própria no plano; a corrida entre
GETs simultâneos não é testada, porque o PGlite tem uma conexão só, e o descarte não foi
exercitado pelo PostgREST publicado (a `ir` não pede a linha de volta, e o esperado é 201 com
zero linhas; se vier erro, o `catch` da `ir` já segue para a vaga); e o feedback (`vaga_util`,
`vaga_irrelevante`) segue sem limite, porque a utilidade semanal lê a última resposta de cada
semana e descartar resposta igual à anterior mudaria a semana seguinte; tocar os botões em laço
exige automatizar uma conta do Telegram, e é o próximo caminho a fechar se aparecer.
Publicação: `db push` da `0028` antes ou depois do merge, tanto faz, porque nada no código
depende dela; a `ir` não muda e não precisa de deploy. Se a `0029` ou a `0030` subirem antes, o
push da `0028` pede `--include-all`.

## Textos do perfil têm teto no banco

(13/09/2026, migration `0025`). Uma conta comum gravava
210 mil caracteres em `perfis.curso` por `update` direto, e o cadastro guardava em
`cadastros_pendentes` qualquer chave extra do JSON. Os checks de `perfis` são **validados**, não
`not valid` como o da `0023`: `perfis` é atualizado todo dia pelo job e pelo webhook, às vezes em
lote, e um check `not valid` deixaria uma linha antiga acima do teto derrubar esses updates longe
da migration. Validado, um perfil acima do teto faz o `db push` falhar inteiro, sem aplicar nada,
e o erro nomeia a constraint: corrigir a linha e repetir. `validar_cadastro_radar` passou a
recusar chave desconhecida no cadastro e no perfil; todas as versões do site mandaram só as
conhecidas. Grants e policies não mudam; a função nova do check fica com o grant padrão, como a
`habilidades_do_perfil_validas` da `0018`, e precisa dele: o check roda com o papel de quem grava,
e sem `execute` o update do próprio dono falha. Pode ir ao banco antes do merge: o site atual já limita
cidade e habilidade e o cadastro já passava pela validação; só um curso de mais de 200 caracteres
digitado na edição seria recusado, com a mensagem genérica de erro. Continua sem teto nosso o
`raw_user_meta_data` do Auth, que o navegador escreve pelo `signUp` e pelo `updateUser`.

## Listas do perfil em uma dimensão

(18/09/2026, migration `0031`). Qualquer conta cadastrada
derrubava o diário de todo mundo: um `update` direto gravava `perfis.areas_de_interesse` como
lista de listas, porque o `<@` da `0017` e o `cardinality` da `0025` achatam a dimensão e só
olham o conteúdo, e o Python quebrava com `TypeError` ao converter os perfis, antes da coleta.
Ninguém recebia mensagem, o resumo de operação não saía e o dia seguinte repetia. Em
`habilidades` o valor já era recusado, mas por acidente: o `array_position(valor, null)` da
`0018` levanta `0A000` ("searching for elements in multidimensional arrays is not supported"),
que some se aquela função for reescrita. A correção é nas duas camadas:
- **No banco**, `coalesce(array_ndims(coluna), 1) = 1` nas duas colunas. Os checks são
  **validados**, pelo mesmo motivo da `0025`: `perfis` é atualizado todo dia pelo job e pelo
  webhook, e um check `not valid` deixaria uma linha antiga derrubar esses updates longe da
  migration. Lista vazia e `areas_de_interesse` nula continuam aceitas, porque `array_ndims`
  devolve nulo nas duas.
- **No Python**, `listar_ativos` converte linha a linha (`usuarios_das_linhas`): a linha que não
  vira `Usuario` (`TypeError` ou `ValueError`, que cobre o `ValidationError` do pydantic) é
  pulada e os demais seguem atendidos; falha da consulta inteira continua sendo a única fatal. O
  log leva só o tipo da exceção e os 8 primeiros caracteres do id, entre reticências
  (`trecho_do_id`), porque o `ValidationError` repete o valor do campo e o log do Actions é
  público, e a auditoria de 17/09 já aponta como grave o `perfil_id` inteiro que o diário
  imprime — o trecho acha a linha para quem tem o banco e não identifica ninguém sozinho.
  `perfis_ilegiveis` conta as puladas e o resumo de operação
  mostra "⚠️ Perfis com dados inválidos, fora da execução: N"; o número vem do repositório, não
  do `ResumoDaExecucao`, porque a leitura acontece antes do pipeline, como as coletas
  incompletas.

Medido em 18/09, só leitura: dos 6 perfis, nenhum é multidimensional (4 com uma dimensão em
`areas_de_interesse`, 2 com a lista vazia, 6 com uma dimensão em `habilidades`), então a
migration aplica sem corrigir linha alguma. O cadastro (`concluir_meu_cadastro`) já recusava
lista de listas com "lista inválida", porque cobra `jsonb_typeof(item) = 'string'`; o buraco
era só o `update` direto, que o `grant` da `0002` e da `0006` permite. Limites: o Python pula a
linha ilegível por qualquer causa, então um defeito nosso de conversão passa a esconder a pessoa
em vez de parar o job, e só o resumo denuncia; `converter_em_entrega`, do `julgar` e do
`gabarito`, continua sem essa proteção, o que não alcança linha nova agora que o banco cobra a
dimensão. Publicação: `db push` da `0031` antes ou depois do merge, tanto faz, porque o `radar/`
não depende dela e o site nunca gravou lista de listas; sem deploy de função. Se a `0031` subir
antes de outra pendente, o push dela pede `--include-all`.
