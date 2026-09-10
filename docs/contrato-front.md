# Contrato entre o site e o radar

Revisado em 08/09/2026 contra `web/assets/app.js` e migrations até `0019`.
O frontend usa Supabase Auth, tabelas e RPCs autorizadas. Não chama uma API Python do Radar.
A referência executável é o [app.js](../web/assets/app.js); o schema é definido pelo
[histórico de migrations](../supabase/migrations/).

## Cadastro e confirmação

O cadastro coleta o perfil antes de `signUp`. Envia em `options.data.cadastro_radar`:

| Campo | Conteúdo |
|---|---|
| `perfil` | `curso`, `periodo`, `habilidades`, `cidade`, `modalidade`, `areas_de_interesse` |
| `aceitou_termos` | `true` obrigatório |
| `aceita_emails` | Booleano independente, desmarcado por padrão |
| `versao_dos_termos` | Versão aceita em formato de data válida; manter coerente com os documentos |
| `sessao_id` | UUID da sessão de origem do funil |

As opções de `areas_de_interesse` **dependem do curso**: o formulário lê `assets/areas.json`
(arquivo gerado a partir de `radar/domain/areas.py`), descobre a área do curso digitado e monta
só as subáreas dela. Curso sem área conhecida esconde o campo em vez de oferecer opções de outra
formação. O banco recusa qualquer valor fora do catálogo, então o site nunca deve inventar um.

O banco valida o payload e preserva cópia em `cadastros_pendentes`, sem acesso direto pelo
navegador. Na confirmação, cria o perfil com os dados e aceite registrados. O retorno consulta
sessão e banco, inclusive quando a confirmação ocorre em outro aparelho.

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
| `curso`, `periodo`, `habilidades`, `cidade`, `modalidade`, `areas_de_interesse` | Dados validados no cadastro e editáveis pelo dono |
| `ativo` | Pausar/retomar pelo painel; sistema também pode pausar por falhas de entrega |
| `motivo_pausa` | Motivo opcional da pausa atual; fica nulo ao retomar e não é histórico |
| `aceita_emails` | Preferência reversível pelo dono |
| `atualizado_em` | Atualizado ao salvar o perfil |
| `termos_aceitos_em`, `versao_dos_termos` | Registro protegido do aceite; não atualizar diretamente |
| `telegram_chat_id`, `token_vinculo` | Vínculo gerenciado pelo webhook/RPC; somente leitura no frontend |
| `excluida_em` | Gerenciado pelas RPCs de exclusão e cancelamento |
| `ativado_em` e campos operacionais | Gerenciados pelo sistema |

Há uma cidade e uma modalidade por perfil. Modalidades aceitas: `remoto`, `presencial`,
`hibrido`, `indiferente`. O catálogo de áreas está no domínio e na validação da `0014`.
Editar perfil e preferências usa `update` na própria linha, limitado por grants e RLS.
Não usar `upsert` como substituto do fluxo de criação.

`cidade` é um município do IBGE no formato `Nome, UF` (`Rio de Janeiro, RJ`), escolhido na lista
de `web/assets/cidades.json`, que sugere as cidades conforme a pessoa digita, sem exigir acento.
O site recusa texto fora da lista e grava a forma da lista quando a pessoa digita sem acento ou
sem o estado e o nome é de uma cidade só; nome repetido em mais de um estado pede a escolha na
lista. O banco continua aceitando qualquer texto de 2 a 120 caracteres: a lista é regra do
cadastro, não do schema, e o pipeline lê o nome e o estado para achar a região imediata. Se a lista não carregar, o
cadastro aceita o texto digitado e avisa, para uma falha de rede não custar a conta. A lista vem
de `uv run python scripts/gerar_cidades.py`, que lê os municípios e a população do Censo 2022
nas APIs do IBGE; a população só ordena as sugestões. Regerar quando o IBGE criar município.

`habilidades` é uma lista de zero a cinquenta strings não vazias, com no máximo 100 caracteres
após retirar espaços nas pontas. Lista vazia significa que o estudante ainda não informou
habilidades; não é convertida em texto sentinela nem implica incapacidade. O caminho de publicação
compatível é: disponibilizar o Python que lê lista vazia (C02), aplicar a migration `0018`
preservando perfis e permissões, e só então liberar o frontend que oferece esse caminho (C03).

## Controles da conta

Decisões de interface preservadas da revisão de 08/09: o campo de habilidade limita a
digitação a 100 caracteres (`maxlength` e recorte em `addCustomSkill`), sem aviso de corte.
A 51ª habilidade é recusada com erro no campo; o envio também valida o limite para listas
legadas. Foi escolhido o limite nativo para texto e erro explícito para quantidade, evitando
apagar uma seleção sem explicação. Remover a proteção do site deixaria a recusa só no banco.

Logout e troca de conta limpam interesses e dados de perfil em memória; respostas pendentes
do catálogo não podem restaurar outra sessão. Ao editar a mesma conta, seleções existentes
devem ser preservadas. Pausa é confirmada antes da pergunta opcional: falha ou omissão da
resposta não desfaz a pausa; retomar limpa o motivo.

| Operação | Caminho |
|---|---|
| Editar, pausar, retomar e revogar e-mails | `update` de colunas permitidas em `perfis` |
| Desvincular | RPC `desvincular_meu_telegram` |
| Solicitar exclusão | RPC `excluir_minha_conta` |
| Cancelar exclusão | RPC `cancelar_exclusao_da_minha_conta` |
| Exportar JSON | RPC `baixar_meus_dados` |

As RPCs operam sobre `auth.uid()`, sem receber o ID de outro usuário. Exclusão marca a conta,
solta o chat e rotaciona o token; não altera `ativo`. O painel mantém sessão para permitir
cancelamento, apresenta a data prevista e bloqueia controles incompatíveis com a exclusão.
A policy também rejeita updates de perfil marcado. Cancelar preserva a pausa anterior e
exige novo vínculo. O job executa a limpeza após a carência configurada de 60 dias.

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
