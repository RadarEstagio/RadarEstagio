# Funcionalidades do Radar de Estágio

Catálogo revisado em 07/09/2026 com base no código da `main`. Destina-se aos integrantes,
estudantes e desenvolvedores. “Implementado” significa que existe código; a disponibilidade
pública depende da configuração e publicação descritas no [guia](guia-publicacao-e-piloto.md).
O catálogo não garante vaga, aprovação em processo seletivo ou cobertura de todos os portais.

## Para quem usa

| Funcionalidade | O que permite | Condição ou limite |
|---|---|---|
| Cadastro por e-mail e senha | Informar curso, período, habilidades, áreas, cidade e modalidade em etapas | Confirmação de e-mail mantida; interface pública depende da hospedagem |
| Preferências | Selecionar uma cidade e uma modalidade; várias habilidades e áreas | Modalidades: remoto, presencial, híbrido ou indiferente |
| Aceite e e-mails opcionais | Aceitar documentos e escolher separadamente comunicações opcionais | Opção de e-mails começa desmarcada; versão e data do aceite ficam registradas |
| Revelar senha | Conferir o que foi digitado | Controle visual do formulário |
| Confirmação entre aparelhos | Retomar com o perfil salvo no cadastro | Perfil preservado no banco; testar jornada real após publicação |
| Reenvio de confirmação | Corrigir o e-mail informado para a tentativa de reenvio e solicitar outro link | Espera de um minuto; não altera automaticamente o endereço da conta original |
| Recuperação de senha | Pedir e-mail de recuperação e definir senha nova | Depende do SMTP e retorno autorizado do Auth |
| Login e saída | Acessar e encerrar sessão no painel | Login social não está implementado na interface |
| Vincular Telegram | Abrir o bot pelo link pessoal e confirmar Start | Token de uso único; um chat não pode pertencer a duas contas |
| Primeira busca após vínculo | Solicitar uma execução apenas para o perfil recém-vinculado | Entre 06:23 e 07:23 de Brasília aguarda o diário; depende do dispatch |
| Recomendações diárias | Receber as melhores vagas novas compatíveis encontradas | Horário operacional registrado: 07:23; quantidade configurável, não garantida |
| Explicação da recomendação | Ver nota, requisitos atendidos/não informados, pontos e alertas disponíveis | Desejáveis ausentes não são cobrados; listas longas mostram até oito itens e “e mais N” |
| Abrir vaga | Ir à página de origem para ler e se candidatar | Candidatura acontece fora do Radar; a fonte pode encerrar ou alterar a vaga |
| Feedback individual | Tocar no número e responder sobre aquela vaga | Abre título, empresa e seis opções; exige envio persistido e conta/chat válidos |
| Corrigir feedback | Reabrir o número e escolher outra resposta | Pode abrir perguntas simultâneas; métricas usam a última resposta por recomendação |
| Editar perfil | Atualizar informações e preferências para novas recomendações | Não muda mensagens já entregues |
| Pausar e retomar | Controlar futuras entregas | Links antigos continuam navegáveis sem registrar eventos enquanto pausado |
| Desvincular Telegram | Soltar o chat e invalidar o link antigo de vínculo | Precisa vincular novamente para voltar a receber |
| Revogar e-mails opcionais | Alterar a preferência no painel | Não há campanha de e-mails opcionais implementada |
| Baixar dados | Exportar os próprios dados em JSON | RPC autenticada, sem credenciais de acesso |
| Excluir conta com arrependimento | Parar entregas, soltar o chat e agendar apagamento | Prazo configurado de 60 dias; limpeza depende do job |
| Cancelar exclusão | Desfazer a solicitação dentro da carência | Preserva pausa anterior e exige novo vínculo do Telegram |
| Aviso sem vagas | Saber que a busca ocorreu sem recomendação adequada | Após silêncio prolongado, sugere ampliar preferências na própria mensagem |

### As seis respostas de feedback

| Resposta | Registro |
|---|---|
| 👍 Essa serviu | `vaga_util` |
| 👎 A nota não fez sentido | `vaga_irrelevante`, `motivo_nota` |
| 👎 Não é da minha área | `vaga_irrelevante`, `motivo_area` |
| 👎 Pedem demais | `vaga_irrelevante`, `motivo_exigencia` |
| 👎 Local ou modalidade | `vaga_irrelevante`, `motivo_logistica` |
| 👎 Já vi essa | `vaga_irrelevante`, `motivo_repetida` |

Na personalização atual, “Já vi essa” ajuda a filtrar republicações. Duas ou mais recusas de
área nos últimos 30 dias retiram o fator de interesse daquela subárea para o usuário, com
teto e aviso específicos. Os demais motivos alimentam análise; positivo não reajusta o
ranking automaticamente. Regras e métricas têm finalidades diferentes.

## Para desenvolvedores e operação

| Capacidade | Implementação e comportamento | Referência |
|---|---|---|
| Coleta por múltiplas fontes | Adzuna e Gupy por padrão; buscas consideram cidades dos perfis | `radar/collectors/` |
| Jooble opcional | Coletor pronto; exige chave e inclusão em `FONTES` | `radar/collectors/jooble.py`, `radar/settings.py` |
| Tolerância a fonte indisponível | Composto continua com fontes que responderam; falha se nenhuma responder | `radar/collectors/composto.py` |
| Deduplicação | Une duplicatas e filtra republicações, incluindo histórico recente do usuário | `radar/filtering/duplicatas.py` |
| Pré-filtro | Regras de estágio, computação, localização e elegibilidade reduzem candidatos à IA | `radar/filtering/prefiltro.py` |
| Enriquecimento | Tenta obter descrição mais completa antes da extração | `radar/matching/enriquecimento.py` |
| Extração de fatos por IA | Gemini API ou adapter local AGY; lotes, tentativas e recuperação parcial | `radar/matching/` |
| Reuso de extração | Uma extração por vaga compartilhada entre perfis | Novas vagas elegíveis ainda podem consumir IA |
| Nota determinística | Python compara curso, período, tecnologias, interesses e logística | `radar/matching/avaliacoes.py`, `compatibilidade.py` |
| Histórico por perfil | Persistência de avaliações, envios e recusas no PostgreSQL | `radar/storage/postgres.py` |
| Atendimento concorrente | Advisory lock por perfil, seguido de releitura do histórico | Não torna Telegram e banco uma transação atômica |
| Revalidação de privacidade | Confere destinatário antes do envio; falha de leitura bloqueia e aparece no resumo | `radar/pipeline.py` |
| Entrega Telegram | HTML escapado, divisão de mensagem e teclado na última parte | `radar/notification/` |
| Feedback via webhook | Valida token/chat/perfil e grava antes de tentar apagar a pergunta | Falhas cosméticas após insert não provocam HTTP 500 |
| Rastreamento | Token em `ir`, redirecionamento 302 sem cache e evento de abertura | `HEAD` não registra; exclusão bloqueia navegação |
| Auth e isolamento | Supabase Auth, RLS, grants e RPCs limitadas ao dono | `supabase/migrations/`, `web/assets/app.js` |
| Antiabuso | Integração Turnstile pronta | Inerte enquanto chave/configuração não forem ativadas |
| Limpeza de contas | Job remove contas após carência e dados associados, incluindo sessões anônimas elegíveis | Não apaga mensagens já entregues no Telegram |
| Falhas de entrega | Contagem e pausa após falhas seguidas; resumo de operação | Limiar configurável |
| Agendamento | Workflow manual disparado pelo cron-job.org ou pelo vínculo | Não há cron nativo ativo no workflow |
| Relatório CLI | Aquisição, coorte, utilidade semanal e recusas com denominadores | `radar/reporting/funil.py`, `radar/storage/metricas.sql` |
| Testes | Python, Deno, DOM simulado e PostgreSQL isolado via PGlite | `tests/`, testes nas Edge Functions |

### Comandos

Prefixo: `uv run python -m radar`.

| Comando | Uso e efeitos |
|---|---|
| `verificar` | Validar configuração |
| `coletar` | Consultar fontes e inspecionar coleta |
| `avaliar` | Coletar e avaliar; pode consumir cota de IA |
| `testar-telegram` | Enviar mensagem de teste ao Telegram |
| `testar-local` | Rodar com perfil fixo e memória, ignorando banco/histórico; envia mensagens reais |
| `rodar` | Executar para destinatários ativos do banco; sem `DATABASE_URL`, usa perfil fixo |
| `rodar --perfil UUID` | Selecionar `perfis.id`, não `user_id`; exige banco para usar perfil real |
| `metricas` | Consultar relatório; exige banco |

**Limitação do modo local:** os botões são gerados, mas os tokens não são persistidos. Portanto,
feedback dessas mensagens não funciona no webhook. Use envios do fluxo com banco para testar.
Envios normais que falham na gravação também podem deixar tokens órfãos.

### Configuração e manutenção

Configuração Python em `.env` e secrets do Actions; frontend usa somente URL/chave pública
Supabase e site key do Turnstile. Nunca colocar `DATABASE_URL`, senha, chave do Resend ou
`service_role` no frontend. O atendimento com trava de sessão requer conexão compatível com
sessão, como conexão direta ou session pooler; não usar transaction pooler para essa trava.

Mudanças de banco entram em novas migrations. Conferir `supabase migration list --linked`
antes/depois de aplicar: objetos existentes e histórico de migrations são coisas distintas.
Os passos concretos e as evidências remotas estão no [guia](guia-publicacao-e-piloto.md).

## O que não está incluído

- Candidatura automática, envio de currículo ou captura de “já me candidatei”.
- Painel web de métricas e lista de vagas no painel da conta.
- Pagamentos, assinatura e campanhas de marketing por e-mail.
- Login social na interface, múltiplas cidades/modalidades por perfil ou cadastro pelo diálogo do bot.
- Ajustes automáticos de pesos por todo feedback ou garantia de processamento único dos callbacks.
- Ativação automática do Jooble ou enriquecimento específico de todas as fontes que ele agrega.

As métricas deduplicam respostas, mas eventos brutos podem repetir. Apagamento definitivo
altera a base histórica, inclusive denominadores de semanas anteriores. Consulte
[Métricas](metricas.md) antes de comparar períodos ou tratar uma abertura como utilidade.

## Estado de disponibilização

O guia registra migrations e funções publicadas e verificadas em 05–06/09, primeira entrega
real e teste de concorrência. A revisão deste catálogo foi local e não repetiu essas provas.
A equipe ainda precisa confirmar a hospedagem final, configuração de Auth/Turnstile, revisão
dos textos e teste completo de cadastro antes do piloto. Não confundir testes automatizados
com validação de utilidade por estudantes.
