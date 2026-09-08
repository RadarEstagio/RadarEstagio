# Contrato entre o site e o radar

Revisado em 07/09/2026 contra `web/assets/app.js` e migrations até `0016`.
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

## Controles da conta

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
