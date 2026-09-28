# Contrato entre o site e o radar

Atualizado até a migration `0031` em 19/09/2026, junto com `web/assets/app.js`.
O frontend usa Supabase Auth, tabelas e RPCs autorizadas. Não chama uma API Python do Radar.
A referência executável é o [app.js](../web/assets/app.js); o schema é definido pelo
[histórico de migrations](../supabase/migrations/).

## Cadastro e confirmação

O cadastro coleta o perfil antes de `signUp`. Envia em `options.data.cadastro_radar`:

| Campo | Conteúdo |
|---|---|
| `perfil` | `curso`, `periodo`, `habilidades`, `cidade`, `modalidade`, `areas_de_interesse`, `pessoa_com_deficiencia` (opcional) |
| `aceitou_termos` | `true` obrigatório |
| `aceita_emails` | Booleano independente, desmarcado por padrão |
| `versao_dos_termos` | Versão aceita em formato de data válida; manter coerente com os documentos |
| `sessao_id` | UUID da sessão de origem do funil; fica em memória na página quando o navegador bloqueia o armazenamento |

As opções de `areas_de_interesse` **dependem do curso**: o formulário lê `assets/areas.json`
(arquivo gerado a partir de `radar/domain/areas.py`), descobre a área do curso digitado e monta
só as subáreas dela. Curso sem área conhecida esconde o campo em vez de oferecer opções de outra
formação. O banco recusa qualquer valor fora do catálogo, então o site nunca deve inventar um.
A área sai de `normalizarCurso`, que espelha `normalizar_curso` com os prefixos, sufixos,
sinônimos, genéricos e abreviações do `areas.json`; `tests/fixtures/cursos_normalizados.json`
trava a paridade. Com o catálogo carregado e o curso sem área, a etapa de habilidades abre com um
aviso que não bloqueia: as vagas ficam menos precisas e vale voltar e escolher o nome na lista.

O campo de curso abre uma lista com os `cursos_sugeridos` do mesmo `areas.json`, em ordem
alfabética e filtrada sem acento conforme a digitação, com o mesmo comportamento da lista de
cidades. Ao contrário da cidade, o curso continua livre: quem não acha o seu na lista segue com o
texto digitado, e o `index.html` não guarda cópia da lista. Se o arquivo não carregar, o campo
avisa e a digitação vale.

O banco valida o payload e preserva cópia em `cadastros_pendentes`, sem acesso direto pelo
navegador. Na confirmação, cria o perfil com os dados e aceite registrados. O retorno consulta
sessão e banco, inclusive quando a confirmação ocorre em outro aparelho.

A cópia só vale para o primeiro link. `signUp` repetido com e-mail ainda não confirmado não regrava
o cadastro nem a senha no Auth, só reenvia o link, e todo link novo (esse `signUp` ou
`auth.resend`) descarta a cópia (`0030`): quem confirma por ele chega sem perfil e completa com
`concluir_meu_cadastro`. O job diário apaga a cópia 2 dias depois do envio e a conta não confirmada
30 dias depois do último link. O cadastro não fica nos metadados nem na identidade do Auth
(`0027` e `0030`).

**Não inserir diretamente em `perfis`.** A `0014` revogou essa permissão. Para usuário
confirmado sem perfil, o frontend chama `concluir_meu_cadastro({ cadastro })`. A RPC valida o
payload e usa a identidade autenticada. Senha é enviada somente ao Auth.

O login implementado usa e-mail e senha. Reenvio usa `auth.resend`, com e-mail editável e espera
de um minuto. Recuperação usa `resetPasswordForEmail` e `updateUser` após sessão de recuperação.
O retorno utiliza `?fluxo=recuperar`; precisa estar autorizado no Auth. Quando configurado,
o token do Turnstile é passado nas operações suportadas e descartado após a tentativa.

## Perfil e limites de escrita

`perfis.id` identifica o perfil e é o argumento de `rodar --perfil`. `user_id` referencia
`auth.users.id`. O navegador autenticado acessa apenas a própria linha pelas políticas RLS.

| Campos | Responsabilidade |
|---|---|
| `id`, `user_id`, `criado_em` | Criação pelo banco; identidade não editável pelo formulário |
| `curso`, `periodo`, `habilidades`, `cidade`, `modalidade`, `areas_de_interesse`, `pessoa_com_deficiencia` | Dados validados no cadastro e editáveis pelo dono |
| `ativo` | Pausar/retomar pelo painel; sistema também pode pausar por falhas de entrega |
| `motivo_pausa` | Motivo opcional da pausa atual; fica nulo ao retomar e não é histórico |
| `aceita_emails` | Preferência reversível pelo dono |
| `atualizado_em` | Atualizado ao salvar o perfil |
| `termos_aceitos_em`, `versao_dos_termos` | Registro protegido do aceite; não atualizar diretamente |
| `telegram_chat_id`, `token_vinculo` | Vínculo gerenciado pelo webhook/RPC; somente leitura no frontend |
| `excluida_em` | Gerenciado pelas RPCs de exclusão e cancelamento |
| `entrega_imediata_disparada_em`, `entrega_imediata_atendida_em` | Controle da entrega imediata, gravado pelo webhook e pelo job; somente leitura no frontend, porque a `0021` concede `update` só às colunas editáveis |
| `ativado_em` e campos operacionais | Gerenciados pelo sistema |

Há uma cidade e uma modalidade por perfil. Modalidades aceitas: `remoto`, `presencial`,
`hibrido`, `indiferente`. O catálogo de áreas está no domínio e na validação da `0014`.
Editar perfil e preferências usa `update` na própria linha, limitado por grants e RLS.

`pessoa_com_deficiencia` é `true`, `false` ou `null`. O formulário oferece Sim, Não e Prefiro não
informar, esta marcada por padrão, e manda `null` para ela; perfil anterior à pergunta também tem
`null`, com o mesmo efeito. No cadastro a chave é opcional, e qualquer tipo além de booleano e
`null` é recusado (`0026`). É dado sensível: não vai para propriedade de evento, log nem prompt, e
o texto ao lado da pergunta diz para que ela serve. Com `true`, vaga para PCD compatível vem
primeiro; com `false`, vaga exclusiva para PCD não é enviada.
Não usar `upsert` como substituto do fluxo de criação.

Tetos de texto (`0025`), iguais aos que `validar_cadastro_radar` cobra desde a `0014` e medidos no
texto cru. O site limita a digitação com o mesmo `maxlength`, e um teste lê os números da migration.

| Campo | Teto | Por que esse número |
|---|---|---|
| `curso` | 200 caracteres | Maior curso do catálogo: 37; com o maior prefixo e sufixo que a normalização conhece, 84. A folga cobre o curso digitado livre |
| `cidade` | 120 caracteres | Maior município de `cidades.json`: 36 |
| cada habilidade | 100 caracteres | Maior sugerida: 23; a folga é da habilidade digitada |
| `habilidades` | 50 itens | Limite da `0018` |
| `areas_de_interesse` | 50 itens, só do catálogo | O catálogo tem 45 subáreas; o limite barra repetição sem fim |
| JSON do cadastro | só as chaves listadas em "Cadastro e confirmação" | O cadastro pendente guardava qualquer chave extra |

Perfil antigo acima de um teto faz a `0025` falhar no `db push`, sem aplicar nada.

`habilidades` e `areas_de_interesse` são listas de **uma dimensão** (`0031`): lista de listas
passava nos checks de conteúdo, que achatam a dimensão, e derrubava a leitura dos perfis no
pipeline. Lista vazia e `areas_de_interesse` nula continuam aceitas, e perfil antigo
multidimensional faria a `0031` falhar no `db push` como um teto estourado.

`cidade` é um município do IBGE no formato `Nome, UF` (`Rio de Janeiro, RJ`), escolhido na lista
de `web/assets/cidades.json`, que sugere as cidades conforme a pessoa digita, sem exigir acento.
O site recusa texto fora da lista e grava a forma da lista quando a pessoa digita sem acento ou
sem o estado e o nome é de uma cidade só; nome repetido em mais de um estado pede a escolha na
lista. O banco aceita qualquer texto de até 120 caracteres (e de pelo menos 2 no cadastro): a lista é
regra do cadastro, não do schema, e o pipeline lê o nome e o estado para achar a região imediata. Se a lista não carregar, o
cadastro aceita o texto digitado e avisa, para uma falha de rede não custar a conta. A lista vem
de `uv run python scripts/gerar_cidades.py`, que lê os municípios e a população do Censo 2022
nas APIs do IBGE; a população só ordena as sugestões. Regerar quando o IBGE criar município.

`habilidades` é uma lista de zero a cinquenta strings não vazias, com no máximo 100 caracteres
cada, contando os espaços nas pontas desde a `0025`. Cada item é o que a pessoa adicionou na tela,
sem separar por vírgula; habilidade composta ("Python, SQL") é partida pelo Python na comparação. Lista vazia significa que o estudante ainda não informou
habilidades; não é convertida em texto sentinela nem implica incapacidade. O caminho de publicação
compatível é: disponibilizar o Python que lê lista vazia (C02), aplicar a migration `0018`
preservando perfis e permissões, e só então liberar o frontend que oferece esse caminho (C03).

## Controles da conta

Decisões de interface preservadas da revisão de 08/09: o campo de habilidade limita a
digitação a 100 caracteres (`maxlength` e recorte em `addCustomSkill`), sem aviso de corte; a dica
do campo diz "Uma por vez, com até 100 caracteres".
A 51ª habilidade é recusada com erro no campo, digitada ou sugerida, e Continuar não sai da etapa
com a 51ª pendente; o corte de 100 é por ponto de código. O curso exige 2 caracteres na tela, como
no banco. O envio também valida o limite para listas
legadas. Foi escolhido o limite nativo para texto e erro explícito para quantidade, evitando
apagar uma seleção sem explicação. Remover a proteção do site deixaria a recusa só no banco.

Logout e troca de conta limpam interesses e dados de perfil em memória; respostas pendentes
do catálogo não podem restaurar outra sessão. Ao editar a mesma conta, seleções existentes
devem ser preservadas. Fechar o diálogo de cadastro (Esc, X, clique fora ou voltar) não limpa: o
rascunho fica na memória da página, sem armazenamento, e reabre na mesma etapa, sem senha nem e-mail
e só para a mesma dona, o usuário da sessão ou o visitante. Qualquer troca de dona limpa tudo,
inclusive login e sessão de outra aba; só o `signUp` feito do rascunho o leva para a conta nova.
Nenhum envio com o conteúdo do formulário (edição, `concluir_meu_cadastro`) sai se a sessão atual não
for a dona: o formulário é limpo e o site pede para entrar de novo. O mesmo vale para as ações da
conta: a página guarda o `user_id` da conta desenhada, lido da linha de `perfis` ou, na conta sem
perfil, da sessão, e antes de editar, pausar, retomar, salvar o motivo, mudar os e-mails, desvincular,
excluir, cancelar a exclusão, exportar ou apagar a conta sem perfil confere que a sessão atual é dessa
conta. Com outra conta na sessão nada é chamado e o site pede para entrar de novo; sem sessão, segue
como antes. Os `update` filtram pelo `user_id` da conta mostrada. Pausa é confirmada antes da pergunta opcional: falha ou omissão da
resposta não desfaz a pausa; retomar limpa o motivo.

| Operação | Caminho |
|---|---|
| Editar, pausar, retomar e revogar e-mails | `update` de colunas permitidas em `perfis` |
| Desvincular | RPC `desvincular_meu_telegram` |
| Solicitar exclusão | RPC `excluir_minha_conta` |
| Excluir conta sem perfil | RPC `apagar_minha_conta_sem_perfil` |
| Cancelar exclusão | RPC `cancelar_exclusao_da_minha_conta` |
| Exportar JSON | RPC `baixar_meus_dados` |

As RPCs operam sobre `auth.uid()`, sem receber o ID de outro usuário. Exclusão marca a conta,
solta o chat e rotaciona o token; não altera `ativo`. O painel mantém sessão para permitir
cancelamento, apresenta a data prevista e bloqueia controles incompatíveis com a exclusão.
A policy também rejeita updates de perfil marcado. Cancelar preserva a pausa anterior e
exige novo vínculo. O job executa a limpeza após a carência configurada de 60 dias.

Conta confirmada sem perfil não tem o que marcar. `apagar_minha_conta_sem_perfil()` (`0024`) apaga
na hora o usuário do Auth, com os eventos e o cadastro pendente por cascata, e os eventos anônimos
das sessões dele. Recusa conta com perfil (`55000`) e chamada sem sessão (`42501`); só
`authenticated` executa. O site a oferece sob o formulário de completar o perfil e, depois dela,
encerra a sessão local.

O motivo da pausa é opcional e aceita somente `conseguiu_estagio`, `interrompeu_busca`,
`sem_vagas_uteis`, `frequencia` ou `outro`. A coluna representa a situação atual, não registra
histórico e não é preenchida para pausas técnicas pelo sistema. O frontend limpa o motivo no
mesmo update que retoma as entregas.

## Elegibilidade acadêmica — decisão D01 em aberto

Preparado em 08/09/2026 a partir do contrato atual e dos casos pedidos em E02. O código mantém
`periodo` como inteiro maior ou igual a 1, uma área principal por curso, subáreas do catálogo e
as exceções já existentes de computação. Nenhuma equivalência nova, migration ou ajuste de peso
foi criado nesta preparação.

| Caso | Entrada atual/limitação | Opção A | Opção B | Impacto que a equipe precisa escolher |
|---|---|---|---|---|
| Curso técnico por módulo | `periodo` aceita inteiro, mas módulo não significa semestre automaticamente | preservar o número como módulo e exibir o rótulo informado | mapear módulo para uma etapa acadêmica mediante catálogo por instituição | altera cadastro, texto de comparação e compatibilidade de perfis antigos |
| Graduação por ano | o formulário chama o campo de período e não conhece duração do curso | manter ano/período como ordem declarada, sem conversão | cadastrar duração/escala da formação e converter apenas com fonte confiável | adiciona campos e regra de migração; não decidir por suposição |
| Anúncio exige curso exato | o match usa curso/área atual e pode ter informação incompleta | exigir correspondência exata quando o anúncio declarar isso | aceitar correlatos definidos por catálogo revisado | altera ranking e elegibilidade; precisa de exemplos públicos |
| Anúncio aceita correlatos | não há contrato geral de equivalência entre formações | tratar correlato como desconhecido até ser declarado | manter catálogo de correlatos com versão e responsável | afeta perfis antigos, avaliação e explicação da recomendação |
| Interesse em atividade de outra área | interesses dependem da área do curso no frontend | permitir interesse declarado, sem transformar em formação elegível | criar subárea transversal com regra explícita | afeta catálogo e comparação, mas não deve falsificar curso |
| Curso/alias ausente | curso desconhecido não recebe sugestões de outra área | preservar curso livre e registrar desconhecido | aprovar alias em catálogo versionado antes de classificar | exige revisão de domínio; não deve apagar seleção do usuário |
| Profissão fora das áreas atuais | catálogo não cobre todos os cursos e profissões | grupo “Não classificado” até evidência suficiente | adicionar área/subáreas após caso observado e revisão | migration, frontend e pontuação separados; não ampliar agora |
| Frequência, pesos e fontes | decisões não são consequência automática do curso | manter contrato vigente e abrir tarefa específica | mudar somente após caso medido e decisão registrada | não misturar com equivalência acadêmica |

### Decisões solicitadas

1. Para técnico e graduação, qual escala deve ser armazenada e mostrada sem converter módulo,
   ano ou semestre por inferência?
2. Em que condições um anúncio declarado como “correlato” pode aceitar outro curso, e quem
   mantém esse catálogo?
3. O grupo “Não classificado” é suficiente enquanto aliases e novas profissões não tiverem
   casos reais? A resposta deve incluir os exemplos de E02.
4. Quais termos de uma fonte podem ser guardados como alias e qual será a versão do catálogo?

Até a decisão, o frontend deve manter o contrato executável atual: período inteiro, curso
declarado, área do catálogo quando reconhecida e desconhecido sem equivalência inventada.
Implementação posterior deve ser dividida em contrato/migration, leitura e avaliação Python,
interface e verificação integrada, com compatibilidade explícita para perfis existentes.

## Telegram e entrega

O botão abre `https://t.me/RadarEstagio_bot?start=<token_vinculo>`. O usuário confirma Start;
o webhook recebe `/start`, valida o token e grava o chat. O token é rotacionado no vínculo.
O site deve reler o perfil ao retornar, sem reutilizar token antigo.

O vínculo dispara `workflow_dispatch` para esse perfil, exceto entre 06:23 e 07:23 de Brasília,
quando aguarda o diário. Sem configuração de dispatch, o vínculo funciona e a busca fica para
o diário. Estar vinculado não garante que haverá vaga compatível naquela execução.

Feedback e abertura são tratados pelas Edge Functions. O site não escreve eventos de Telegram
em nome do usuário. Tokens de recomendações sem registro em `envios`, incluindo `testar-local`,
não permitem feedback. As regras estão no [catálogo](funcionalidades.md) e em
[Métricas](metricas.md).

## Segurança e eventos

Somente URL do projeto, chave pública Supabase e site key do Turnstile ficam no frontend.
Nunca expor senha do banco, `DATABASE_URL`, `service_role` ou secrets de Telegram/Resend.
Eventos do navegador respeitam o catálogo web autorizado; eventos de confirmação, vínculo e
primeira entrega têm fontes próprias no banco. A sessão de origem não substitui autenticação.
O site corta cada texto das propriedades em 40 caracteres, para caber nos 256 bytes que o banco
aceita em evento web (`0023`).

Não alterar schema pelo painel nem ampliar grants para contornar um erro do frontend.
Use novas migrations e os testes de `tests/web/` para mudanças nesse contrato.

## Decisões de cadastro e privacidade

- A confirmação de e-mail mantém um canal verificado para acesso e recuperação. O reenvio
  permite corrigir o endereço e respeita o intervalo entre tentativas.
- Aceite dos termos e autorização opcional de e-mails são controles separados. A autorização
  opcional pode ser revogada e não representa consentimento geral para todas as finalidades.
- Pausa usa `ativo`; exclusão usa `excluida_em`. Pausar não inicia apagamento nem bloqueia
  a navegação das vagas antigas, embora interrompa novos registros de interação.
- A exclusão interrompe entregas, libera o vínculo do Telegram e permite arrependimento
  durante 60 dias. Cancelar exige vincular o Telegram novamente. O atendimento de pedidos
  de eliminação imediata precisa ser definido pelos responsáveis no guia de publicação.
- Não há limpeza automática de contas abandonadas. A limpeza de sessão anônima deve atingir
  somente dados sem proprietário, preservando outras contas do mesmo navegador.

## Decisões e pós-mortems do site

Movidos do `CLAUDE.md` em 20/09/2026, sem reescrita: cada um guarda a data da decisão, o que
foi medido e o limite aceito.

### Conta no site: volta à aba e botão de pausa (13/09/2026).

Voltar à aba (`focus`) só consulta
o banco com a tela de ativação à mostra e o link do Telegram visível
(`aguardandoVinculoDoTelegram`), e a condição é conferida de novo quando a consulta termina, com
sucesso ou erro. Antes, depois da ativação, toda volta à aba redesenhava a conta: descartava a
edição em andamento, sumia com a pergunta do motivo da pausa e escondia a confirmação sem
fechá-la. Um `<dialog>` aberto com `showModal` e escondido continua modal e trava a página, e no
celular não há Esc; por isso esconder a conta é sempre `esconderConta()`, que passa por
`fecharConfirmacao`, nunca `hidden = true`. O botão de pausa guarda a ação que mostrou
(`data-acao`), e o update leva `.eq("ativo", ...)` e devolve a linha (`select(COLUNAS_DO_PERFIL)`),
que desenha a conta sem leitura extra. Zero linhas significa que a conta mudou em outro lugar
(outro aparelho, pausa automática, exclusão): nada é invertido, o perfil é relido e a pessoa é
avisada. Antes, "Pausar entregas" com a conta já pausada retomava as entregas e apagava o
motivo. O JSDOM não implementa `showModal`: os testes o simulam e conferem `open`, `hidden` e se
`close()` foi chamado. O card de preços fala só da Adzuna, e
`test_card_de_precos_nao_promete_duas_fontes_de_vagas` impede que "duas fontes" volte.

### Armazenamento bloqueado e conta que não carrega (13/09/2026).

Com o armazenamento bloqueado
(modo privado, bloqueador), `eventSessionId` e `clearPendingProfile` lançavam exceção e o `signUp`
nunca era chamado. Toda leitura e escrita de `localStorage`/`sessionStorage` do site fica em `try`,
e a sessão de eventos vira um UUID em memória na página, o mesmo no cadastro e nos eventos. O
cliente do Supabase não precisa de armazenamento: o auth-js testa o `localStorage` com `try` e, se
falha, guarda a sessão em memória (conferido no código do 2.112.4 e do 2.114.0, iguais nesse
ponto; o 2.116.0 não pôde ser baixado). Custo aceito: a sessão some ao recarregar, o tema não é
lembrado e `landing_visualizada` conta toda carga. Falha ao ler sessão ou perfil deixou de virar
"Sua conta foi criada, mas o perfil ainda não foi salvo", que quem tinha perfil via com a sessão
velha ou sem rede: agora abre o login com "Não conseguimos carregar sua conta", e o aviso de perfil
pendente só sai quando o perfil foi lido e não existe (`contaSemPerfil`). A visita comum à landing
não lê mais o perfil, que era descartado. O erro de "Minha conta" na ativação vai para
`#success-message`, porque o formulário fica escondido nessa tela.

### Segunda auditoria da conta (13/09/2026).

Propriedades de evento cabem em 256 bytes: a `0023`
(branch `fix/eventos-e-reserva`) recusa evento web acima disso, e `landing_visualizada` levava o
caminho inteiro da URL. `propriedadesDoEvento` corta cada texto em 40 pontos de código, porque o
pior caractere escapado no JSON tem 6 bytes (40 × 6 mais `{"pagina": ""}` dá 254); o corte é por
ponto de código para não partir emoji, que o `jsonb` recusaria. Evento novo com dois textos exige
refazer a conta, e o teste com URL de 1.000 caracteres confere todos os `registerEvent`.
`closeSignup` fecha a confirmação antes de sair da conta, porque voltar no histórico deixava o
`<dialog>` modal aberto. Envio do perfil e exclusão sem perfil se travam até a resposta, senão a
exclusão ganhava a corrida e o erro do envio ia para o formulário escondido. A exclusão sem perfil
tem mensagens próprias (`55000`, `42501`, rede), não as do cadastro.

### Perfil, habilidades e rascunho (13/09/2026).

Os textos que o navegador grava no perfil têm teto
no banco (`0025`): curso 200, cidade 120, habilidade 100 e listas de 50 itens. São os tetos que
`validar_cadastro_radar` já cobrava desde a `0014`, agora também no `update` direto e sobre o texto
cru (espaços nas pontas furavam o `btrim`); mantê-los evita que um cadastro pendente, validado antes,
falhe na confirmação do e-mail. A folga vem dos catálogos: o maior curso sugerido tem 37 caracteres,
84 com o maior prefixo e sufixo que a normalização conhece, e a maior cidade do IBGE tem 36. O site
limita a digitação com o mesmo `maxlength` e cobra na etapa o mínimo de 2 no curso, porque o
navegador só marca texto curto que a pessoa digitou. O teste de coerência compara com o site os
checks, os dois números de cada texto em `validar_cadastro_radar` e o limite das listas da `0018`, e
exige que perfil e cadastro aceitem todas as subáreas de um curso; lendo só os checks, mudar a
validação do cadastro passava. Habilidade digitada nunca é separada por vírgula: cada item na tela é
um item no banco. O envio partia o campo oculto por vírgula, então "Pacote Office (Word, Excel)"
virava dois pedaços e 50 itens na tela viravam mais de 50 no banco, que recusava. Separar ao adicionar
exigiria copiar no site as regras com que o Python já parte a habilidade composta (parênteses, " e ",
nível da última parte). O corte de 100 é por ponto de código, como em `propriedadesDoEvento`: o
`slice` partia emoji e o Postgres recusava o JSON. O limite de 50 vale também para a sugerida e para
Continuar, que antes passavam sem aviso. Fechar o diálogo (Esc, X, clique fora, voltar) não apaga o
rascunho: ele fica na memória da página, sem armazenamento, e reabre na mesma etapa, mas sem senha nem
e-mail e só para a mesma dona. Senha e e-mail saem porque identificam a pessoa, e quem reabre já
refaz a etapa da conta por causa da senha. O rascunho guarda a dona (`donoDoRascunho`): o id do
usuário da sessão, ou visitante. Qualquer troca de dona limpa tudo: ao reabrir, na volta do link, ao
completar o perfil, ao ler a conta e depois de um login. Só o `signUp` feito do rascunho o adota,
porque é a mesma pessoa se cadastrando; se ele espera a confirmação do e-mail, a sessão que chega com
esse e-mail também o mantém (`emailDoCadastroEnviado`). Login pelo diálogo e sessão vinda de outra aba
nunca adotam. Sessão que falha ao renovar limpa o rascunho de conta, porque não se sabe quem é a dona.
E nada do formulário é gravado numa conta que não é a dona: antes da edição, do `concluir_meu_cadastro`
e da troca de conta, a sessão atual precisa ser a dona, senão o formulário é limpo e aparece "Sua
sessão mudou". Em duas abas, a edição de A aberta aqui era gravada na conta de B que entrou na outra;
o `main` faz o mesmo. Logout, exclusão e o "Entrar" do cabeçalho seguem limpando. Custo aceito: na
mesma aba, quem abre o cadastro depois de um visitante vê o curso, a cidade e as habilidades dele até
entrar numa conta; depois do envio, reabrir mostra o que foi enviado.

### Navegação da conta no celular (16/09/2026).

A conta mostra um painel por vez
(`mostrarSecaoDaConta`), e os links de `.account-nav` são o único caminho para Entregas, Dados e
acesso e Privacidade. A regra que escondia a navegação até 860px vinha de quando as seções apareciam
juntas; depois da troca para um painel por vez, no celular não havia como pausar, sair, baixar os
dados, desvincular o Telegram ou excluir a conta. Agora ela é uma barra horizontal abaixo da marca,
de borda a borda e com rolagem própria, dentro do cabeçalho grudado, que cresce uma linha de 44px.
A barra lateral vira grade para a barra ocupar a linha inteira, e a navegação leva
`contain: inline-size`: sem isso a largura dos links entra no cálculo das colunas da marca e do
"Voltar ao site" e pode quebrar o botão em duas linhas. O JSDOM não avalia media query, então
`test_navegacao_da_conta_segue_visivel_no_celular_com_as_quatro_secoes` lê o CSS e recusa regra de
tela estreita que esconda a navegação ou os links. Limite aceito: quem abre a conta direto numa
seção pelo endereço (`#account-privacy-panel`) pode ver o item ativo cortado na borda direita até
rolar a barra; o título da página já diz a seção.

### Ações da conta conferem a conta mostrada (16/09/2026).

As ações de "Minha conta" usavam a sessão
atual, e o auth-js relê a sessão do armazenamento a cada `getSession`. Com a conta de A na tela e B
entrando em outra aba, Excluir marcava B e soltava o Telegram dele, Desvincular soltava o de B, pausa,
motivo e e-mails gravavam na linha de B, Cancelar exclusão e Baixar meus dados agiam sobre B, e a conta
sem perfil de A apagava B na hora. A página guarda o id da conta desenhada (`contaMostrada`):
`showAccount` o lê da própria linha, e por isso `COLUNAS_DO_PERFIL` traz `user_id`; a conta sem perfil o
lê da sessão que a abriu. Toda ação da conta que chama o Supabase (editar, pausar e retomar, motivo,
e-mails, desvincular, excluir, cancelar a exclusão, baixar os dados e apagar a conta sem perfil) passa
antes por `recusarSeASessaoMudou`: com outra conta na sessão nada é chamado e `recusarPorTrocaDeSessao`
leva ao login com "Sua sessão mudou". É a mesma saída do rascunho de outra dona, que passou a usar
`abrirLogin` e por isso esconde a conta, a confirmação e o "Excluir minha conta" da conta sem perfil.
Sessão ausente segue como antes. Os `update` filtram por `contaMostrada`, não pelo id lido da sessão, e
uma troca entre a conferência e a requisição não grava em B, porque o RLS não deixa o token de B
alcançar a linha de A. As RPCs agem sobre `auth.uid()` e não têm esse fecho: a janela é a de uma
leitura de sessão. Ficam de fora de propósito o "Minha conta" da ativação e a volta à aba, que releem e
desenham a conta da sessão atual, e "Sair da conta", que encerra a sessão que estiver no navegador
(o `signOut` global também revoga as outras sessões dessa conta). Controle novo da conta que chame o
Supabase precisa da conferência, e teste que clica num controle da conta precisa desenhá-la antes
(`?conta`), senão a ação é recusada.
