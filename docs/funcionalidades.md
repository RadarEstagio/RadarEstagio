# Funcionalidades do Radar de Estágio

Catálogo revisado em 07/09/2026 com base no código da `main`. Destina-se aos integrantes,
estudantes e desenvolvedores. “Implementado” significa que existe código; a disponibilidade
pública depende da configuração e publicação descritas no [guia](guia-publicacao-e-piloto.md).
O catálogo não garante vaga, aprovação em processo seletivo ou cobertura de todos os portais.

## Navegação

- [Para quem usa](#para-quem-usa) — conta, recomendações e controle dos dados.
- [Respostas de feedback](#as-seis-respostas-de-feedback) — opções e efeito no ranking.
- [Para desenvolvedores e operação](#para-desenvolvedores-e-operação) — coleta, IA, entrega e segurança.
- [Comandos](#comandos) — execução e testes locais.
- [Configuração e manutenção](#configuração-e-manutenção).
- [Fora do escopo](#o-que-não-está-incluído).
- [Estado de disponibilização](#estado-de-disponibilização).

---

## Para quem usa

### Conta e acesso

#### 01. Cadastro por e-mail e senha

Informar curso, período, habilidades, áreas, cidade e modalidade e, no último passo, e-mail e
senha. Quem já tem conta escolhe "Entrar" e vê só o passo da conta; quem edita o perfil depois
do login não passa por ele.

**Condições e limites:** Confirmação de e-mail mantida; a conta só é criada no envio do último
passo, nunca ao avançar entre etapas; interface pública depende da hospedagem.

#### 02. Preferências

Selecionar uma cidade e uma modalidade; várias habilidades e áreas. As áreas oferecidas são as do
curso informado, e "Ainda não quero informar habilidades" segue sem nenhuma.

**Condições e limites:** Modalidades: remoto, presencial, híbrido ou indiferente. Até 50
habilidades de até 100 caracteres. Lista vazia significa habilidade não informada, não incapacidade:
a vaga continua sendo avaliada pelos demais critérios. Curso sem área conhecida não recebe
sugestões de habilidade; a digitação livre continua valendo.

#### 03. Aceite e e-mails opcionais

Aceitar documentos e escolher separadamente comunicações opcionais.

**Condições e limites:** Opção de e-mails começa desmarcada; versão e data do aceite ficam registradas.

#### 04. Revelar senha

Conferir o que foi digitado.

**Condições e limites:** Controle visual do formulário.

#### 05. Confirmação entre aparelhos

Retomar com o perfil salvo no cadastro.

**Condições e limites:** Perfil preservado no banco; testar jornada real após publicação.

#### 06. Reenvio de confirmação

Corrigir o e-mail informado para a tentativa de reenvio e solicitar outro link.

**Condições e limites:** Espera de um minuto; não altera automaticamente o endereço da conta original.

#### 07. Recuperação de senha

Pedir e-mail de recuperação e definir senha nova.

**Condições e limites:** Depende do SMTP e retorno autorizado do Auth.

#### 08. Login e saída

Acessar e encerrar sessão no painel.

**Condições e limites:** Login social não está implementado na interface.

### Telegram e recomendações

#### 09. Vincular Telegram

Abrir o bot pelo link pessoal e confirmar Start.

**Condições e limites:** Token de uso único; um chat não pode pertencer a duas contas.

#### 10. Primeira busca após vínculo

Solicitar uma execução apenas para o perfil recém-vinculado.

**Condições e limites:** Entre 06:23 e 07:23 de Brasília aguarda o diário; depende do dispatch.

#### 11. Recomendações diárias

Receber as melhores vagas novas compatíveis encontradas.

**Condições e limites:** Horário operacional registrado: 07:23; quantidade configurável, não garantida.

#### 12. Explicação da recomendação

Ver nota, requisitos atendidos/não informados, pontos e alertas disponíveis.

**Condições e limites:** Desejáveis ausentes não são cobrados; listas longas mostram até oito itens e “e mais N”.

#### 13. Abrir vaga

Ir à página de origem para ler e se candidatar.

**Condições e limites:** Candidatura acontece fora do Radar; a fonte pode encerrar ou alterar a vaga.

#### 14. Feedback individual

Tocar no número e responder sobre aquela vaga.

**Condições e limites:** Abre título, empresa e seis opções; exige envio persistido e conta/chat válidos.

#### 15. Corrigir feedback

Reabrir o número e escolher outra resposta.

**Condições e limites:** Pode abrir perguntas simultâneas; métricas usam a última resposta por recomendação.

### Controle dos seus dados e entregas

#### 16. Editar perfil

Atualizar informações e preferências para novas recomendações.

**Condições e limites:** Não muda mensagens já entregues.

#### 17. Pausar e retomar

Controlar futuras entregas. Depois de pausar, uma pergunta opcional oferece cinco motivos e a
opção de pular.

**Condições e limites:** Links antigos continuam navegáveis sem registrar eventos enquanto pausado.
A resposta é opcional, não bloqueia a pausa e não é pedida para pausa automática por falha de
envio. O motivo guarda só a pausa atual e é apagado ao retomar.

#### 18. Desvincular Telegram

Soltar o chat e invalidar o link antigo de vínculo.

**Condições e limites:** Precisa vincular novamente para voltar a receber.

#### 19. Revogar e-mails opcionais

Alterar a preferência no painel.

**Condições e limites:** Não há campanha de e-mails opcionais implementada.

#### 20. Baixar dados

Exportar os próprios dados em JSON.

**Condições e limites:** RPC autenticada, sem credenciais de acesso.

#### 21. Excluir conta com arrependimento

Parar entregas, soltar o chat e agendar apagamento.

**Condições e limites:** Prazo configurado de 60 dias; limpeza depende do job.

#### 22. Cancelar exclusão

Desfazer a solicitação dentro da carência.

**Condições e limites:** Preserva pausa anterior e exige novo vínculo do Telegram.

#### 23. Aviso sem vagas

Saber que a busca ocorreu sem recomendação adequada.

**Condições e limites:** Após silêncio prolongado, sugere ampliar preferências na própria mensagem.

---

## As seis respostas de feedback

- **👍 Essa serviu**: `vaga_util`.
- **👎 A nota não fez sentido**: `vaga_irrelevante`, `motivo_nota`.
- **👎 Não é da minha área**: `vaga_irrelevante`, `motivo_area`.
- **👎 Pedem demais**: `vaga_irrelevante`, `motivo_exigencia`.
- **👎 Local ou modalidade**: `vaga_irrelevante`, `motivo_logistica`.
- **👎 Já vi essa**: `vaga_irrelevante`, `motivo_repetida`.

Na personalização atual, “Já vi essa” ajuda a filtrar republicações. Duas ou mais recusas de
área nos últimos 30 dias retiram o fator de interesse daquela subárea para o usuário, com
teto e aviso específicos. Os demais motivos alimentam análise; positivo não reajusta o
ranking automaticamente. Regras e métricas têm finalidades diferentes.

---

## Para desenvolvedores e operação

### Coleta e qualidade das vagas

#### 01. Coleta por múltiplas fontes

Adzuna e Gupy por padrão; buscas consideram cidades dos perfis.

**Código de referência:** `radar/collectors/`.

#### 02. Jooble opcional

Coletor pronto; exige chave e inclusão em `FONTES`.

**Código de referência:** `radar/collectors/jooble.py`, `radar/settings.py`.

#### 03. Tolerância a fonte indisponível

Composto continua com fontes que responderam; falha se nenhuma responder.

**Código de referência:** `radar/collectors/composto.py`.

#### 04. Deduplicação

Une duplicatas e filtra republicações, incluindo histórico recente do usuário.

**Código de referência:** `radar/filtering/duplicatas.py`.

#### 05. Pré-filtro

Regras de estágio, área do curso, localização e elegibilidade reduzem candidatos à IA.

**Código de referência:** `radar/filtering/prefiltro.py`.

#### 06. Enriquecimento

Tenta obter descrição mais completa antes da extração.

**Código de referência:** `radar/matching/enriquecimento.py`.

### Extração e personalização

#### 07. Extração de fatos por IA

Gemini API ou adapter local AGY; lotes, tentativas e recuperação parcial.

**Código de referência:** `radar/matching/`.

#### 08. Reuso de extração

Uma extração por vaga compartilhada entre perfis.

**Condições e limites:** Novas vagas elegíveis ainda podem consumir IA.

#### 09. Nota determinística

Python compara curso, período, habilidades, área, interesses e logística.

**Código de referência:** `radar/matching/avaliacoes.py`, `compatibilidade.py`.

#### 10. Histórico por perfil

Persistência de avaliações, envios e recusas no PostgreSQL.

**Código de referência:** `radar/storage/postgres.py`.

### Entrega e interações

#### 11. Atendimento concorrente

Advisory lock por perfil, seguido de releitura do histórico.

**Condições e limites:** Não torna Telegram e banco uma transação atômica.

#### 12. Revalidação de privacidade

Confere destinatário antes do envio; falha de leitura bloqueia e aparece no resumo.

**Código de referência:** `radar/pipeline.py`.

#### 13. Entrega Telegram

HTML escapado, divisão de mensagem e teclado na última parte.

**Código de referência:** `radar/notification/`.

#### 14. Feedback via webhook

Valida token/chat/perfil e grava antes de tentar apagar a pergunta.

**Condições e limites:** Falhas cosméticas após insert não provocam HTTP 500.

#### 15. Rastreamento

Token em `ir`, redirecionamento 302 sem cache e evento de abertura.

**Código de referência:** `HEAD` não registra; exclusão bloqueia navegação.

### Segurança e operação

#### 16. Auth e isolamento

Supabase Auth, RLS, grants e RPCs limitadas ao dono.

**Código de referência:** `supabase/migrations/`, `web/assets/app.js`.

#### 17. Antiabuso

Integração Turnstile pronta.

**Condições e limites:** Inerte enquanto chave/configuração não forem ativadas.

#### 18. Limpeza de contas

Job remove contas após carência e dados associados, incluindo sessões anônimas elegíveis.

**Condições e limites:** Não apaga mensagens já entregues no Telegram.

#### 19. Falhas de entrega

Contagem e pausa após falhas seguidas; resumo de operação.

**Condições e limites:** Limiar configurável.

#### 20. Agendamento

Workflow manual disparado pelo cron-job.org ou pelo vínculo.

**Condições e limites:** Não há cron nativo ativo no workflow.

#### 21. Relatório CLI

Aquisição, coorte, participação no feedback, tempo observado até a primeira entrega e abertura,
utilidade semanal e por área do curso, contas pausadas por motivo e recusas com denominadores.

**Código de referência:** `radar/reporting/funil.py`, `radar/domain/metricas.py`,
`radar/storage/metricas.sql`.

#### 22. Testes

Python, Deno, DOM simulado e PostgreSQL isolado via PGlite.

**Código de referência:** `tests/`, testes nas Edge Functions.

---

## Comandos

Prefixo: `uv run python -m radar`.

- **`verificar`**: Validar configuração.
- **`coletar`**: Consultar fontes e inspecionar coleta.
- **`avaliar`**: Coletar e avaliar; pode consumir cota de IA.
- **`testar-telegram`**: Enviar mensagem de teste ao Telegram.
- **`testar-local`**: Rodar com perfil fixo e memória, ignorando banco/histórico; envia mensagens reais.
- **`rodar`**: Executar para destinatários ativos do banco; sem `DATABASE_URL`, usa perfil fixo.
- **`rodar --perfil UUID`**: Selecionar `perfis.id`, não `user_id`; exige banco para usar perfil real.
- **`metricas`**: Consultar relatório; exige banco.

**Limitação do modo local:** os botões são gerados, mas os tokens não são persistidos. Portanto,
feedback dessas mensagens não funciona no webhook. Use envios do fluxo com banco para testar.
Envios normais que falham na gravação também podem deixar tokens órfãos.

## Configuração e manutenção

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
