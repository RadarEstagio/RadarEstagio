# Fichas — métricas e retenção

> Histórico em consolidação desde 09/09/2026, mantido para revisão antes da exclusão.
> Consulte a [referência mantida](../metricas.md) para o estado atual. As instruções e
> pendências abaixo retratam a execução anterior; não reiniciam tarefas nem comprovam produção.

Leia o protocolo e execute uma ficha por vez; continue a fila após concluir. Não substituir definições de `CONTEXT.md`.
As métricas permanecem no relatório CLI; nenhum ID pede dashboard ou serviço externo.

## M01

**Mapa de eventos após reorganizar cadastro. P1. Depende de C05.**

Arquivos de leitura: `web/assets/app.js`, migrations de eventos e consentimento,
`radar/storage/metricas.sql`. Entrega: seção atualizada em `docs/metricas.md` com tabela
etapa visível → evento existente → momento do disparo → abandono observável → limitação.
Não instrumentar campo de senha, conteúdo digitado ou replay de sessão.

Comparar cadastro, login e edição. Os eventos existentes têm nomes semânticos: não renomear
por posição da etapa. Se houver evento disparado no ponto errado, corrigir um emissor e seu
teste em `tests/web/cadastro_test.ts`. Se um novo evento for necessário, registrar a lacuna
 e especificação de nome/propriedades/RLS como tarefa futura; não ampliar schema neste ID.
Aceite: tabela explica o que é alcance e o que não mede conversão sequencial. Não atribuir
cadastro a quem apenas passou por uma etapa. Verificar emissores e consulta, sem dados pessoais.

### Entrega fechada

1. Inventariar chamadas `registerEvent` e emissores de banco/webhook; separar evento emitido
   pelo navegador de marco confirmado pelo servidor. Ler C05 antes de interpretar ordem.
2. Montar em `docs/metricas.md` uma linha por evento de aquisição já mostrado por `formatar_funil`.
   Colunas obrigatórias: fluxo, etapa, condição válida, emissor, identidade disponível, repetição,
   leitura no SQL e limite. Incluir login/edição como fluxos que não são novo cadastro.
3. Em W, simular avanço inválido, avanço válido, voltar/avançar e erro de signup. Não emitir
   conclusão para campo inválido nem `conta_criada` antes do sucesso de autenticação.
4. Corrigir apenas emissores que contradigam a tabela. Manter deduplicação e nomes históricos.

Fechamento: tabela cobre todos os eventos exibidos no relatório; lacunas são explicitadas com
nome/propriedades propostas para futura tarefa, não migration improvisada. Não calcular conversão
sequencial dividindo contagens com identidades ou janelas diferentes.

## M02

**Mostrar participação no feedback. P1. Pronta.**

Arquivos: `radar/storage/metricas.sql`, `radar/domain/models.py` (modelo do relatório),
`radar/reporting/funil.py`, conversão do resultado no storage, `tests/web/metricas_test.ts` e
testes Python do relatório. Reusar consultas e deduplicação existentes.

Janela: a mesma dos envios em `entregas_do_periodo`. Denominador: pares distintos
`(perfil_id,vaga_id)` entregues nessa janela. Se houver múltiplos registros de envio para o mesmo par, deduplicar antes do join.
Numerador: pares com feedback positivo ou negativo
a partir da entrega (inclusive mesmo timestamp) e até a data da consulta, usando a última resposta e desempate por ID.
Retornar contagens e percentual; sem entregas, “sem denominador”. Não usar aberturas como resposta.
Não substituir utilidade semanal. Aceite: repetição não infla, correção da resposta ainda conta
uma resposta, feedback anterior à entrega não vale, sem resposta não é aprovação. Testar SQL
isolado e apresentação. Exibir, por exemplo, “Respostas: 3 de 10 recomendações (30%)”;
o percentual é derivado das contagens, não persistido. Atualizar definição em `docs/metricas.md`.

### Contrato e implementação SQL → modelo → relatório

1. Ler `entregas_do_periodo` e fixar um registro por par, com primeira entrega dentro da janela.
   Feedback vale a partir dessa entrega, inclusive mesmo timestamp, até `limites.fim`.
2. Contar pares com última resposta válida; desempatar por `ocorrido_em DESC, id DESC`.
   Sugeridos campos aditivos de `FunilDaCoorte`: `recomendacoes_com_feedback` e
   `recomendacoes_elegiveis_feedback`. Reusar campos equivalentes se já existirem.
3. Atualizar conversão em `RepositorioPostgres.funil_da_coorte`, fixtures Python e interface TypeScript
   do harness SQL. Não alterar o significado de `vagas_enviadas` para acomodar a métrica nova.
4. Em `formatar_funil`, calcular percentual a partir das contagens. Exibir zero respostas
   explicitamente quando houver denominador; zero entregas mostra “sem denominador”.

Oráculo mínimo: três pares entregues, um envio duplicado do primeiro, duas respostas para o
primeiro (positiva depois negativa), segundo só com abertura e terceiro sem interação →
1/3 respostas, 33,3%. Resposta anterior à entrega e evento futuro não alteram o resultado.
Acrescentar dois eventos no mesmo instante e IDs diferentes para provar desempate.

Fechamento: Q passa com contagens 1/3; trocar positivo por negativo não elimina participação.
Não incluir candidatura como feedback nem confundir respostas com utilidade.

## M03

**Tempo até entrega e primeira abertura. P1. Pronta.**

Mesmos pontos de entrada de M02. Coorte: perfis criados na janela do relatório. Para cada
perfil, primeira entrega válida após criação; primeira `vaga_aberta` após a entrega do mesmo
par e até a consulta. Intervalos partem de `perfis.criado_em`; não partir da visita ou do vínculo.
Calcular com timestamps UTC e diferença em segundos; converter a unidade só na apresentação.
Retornar mediana dos intervalos observados separadamente e números de perfis sem entrega/sem
abertura. Coorte vazia: sem denominador; nenhuma ocorrência: mediana indisponível, nunca zero.

Aceite: teste de eventos repetidos, abertura anterior à entrega, perfil sem entrega, entrega
sem abertura, evento futuro, duração zero legítima e coorte vazia. Relatório identifica que a
mediana usa somente casos observados; não chama entrega de tempo até o valor. Não implementar
D7, survival analysis ou metas. Atualizar docs com janela e limitações.

### Contrato temporal e casos com resultado calculado

1. Reusar `limites`/`coorte`; excluir entrega anterior à criação ou posterior ao fim da consulta.
2. Calcular a primeira entrega válida por perfil. Para abertura, buscar a primeira abertura
   válida de qualquer par efetivamente entregue ao perfil, não só da primeira vaga recebida.
3. Retornar contagem da coorte, sem entrega, sem abertura e medianas nullable em segundos.
   Usar mediana contínua (`percentile_cont(0.5)`); para dois valores, média dos dois centrais.
   Modelo Python deve distinguir `None` de `0`. Conversão de unidade só no formatador.
4. Atualizar fixture SQL reduzida de `tests/web/metricas_test.ts`, parsing e testes Python Q.

Oráculo mínimo: três perfis criados no instante T. Entregas em T+60 s e T+180 s para os dois
primeiros; terceiro sem entrega. Abertura válida do segundo em T+300 s; primeiro sem abertura.
Resultado: mediana entrega 120 s; mediana abertura 300 s; sem entrega 1; sem abertura 2.
Uma abertura de vaga não entregue e um evento futuro não contam. Caso separado T→T retorna
zero legítimo, não indisponível. Sem ocorrências retorna null; coorte vazia tem tamanho zero.

Fechamento: CLI mostra quantos casos foram observados e faltantes ao lado das medianas.
“Sem abertura” inclui quem não recebeu. Não apresentar mediana como prazo prometido ao usuário.

## M04

**Utilidade por área atual do curso. P1. Depende de M02.**

Arquivos: catálogo `radar/domain/areas.py` (leitura), storage/SQL, modelo e relatório de métricas,
testes de métricas SQL e Python. Reusar definição semanal existente: perfis operacionalmente
ativados até o fim da semana, incluindo pausados/desvinculados, e sinal de utilidade naquela
semana. Produzir agregados por área atual do curso; curso desconhecido vira grupo “Não classificado”.

A classificação deve usar `area_do_curso` em Python, não outra lista de cursos em SQL. Se a
consulta precisar retornar fatos para agregação, retornar apenas identificador interno, curso,
semana e indicador de utilidade; não imprimir identificadores pessoais no relatório. Cada perfil
pertence a um grupo neste relatório. Não explodir interesses em linhas nem somar usuário duas vezes.

Aceite: soma de denominadores e numeradores por área reproduz o total semanal; histórico de
edição de curso não é inventado. Mostrar ressalva “agrupado pelo curso atual”; mudança de curso
ou exclusão pode mudar agrupamentos passados. Sem grupo com amostra, não concluir desempenho.
Não incluir cidade/fonte/curso em uma matriz combinatória neste lote.

### Agregação sem duplicar o domínio

1. Identificar os fatos de utilidade semanal existentes no SQL. Produzir linhas mínimas por
   perfil/semana com curso atual e sinal booleano; manter exatamente janelas e elegibilidade
   usadas no total atual. Não enviar eventos brutos inteiros ao Python.
2. No caminho de conversão de `RepositorioPostgres.funil_da_coorte`, classificar com `area_do_curso` e
   agregar antes de retornar ao relatório. Reusar `UtilidadeSemanal` ou modelo análogo com área.
3. Atualizar schema reduzido do teste SQL para incluir `curso`; não presumir que esse harness
   aplica migrations. Testar fatos SQL e agregação Python separadamente e a apresentação final.
4. Mostrar cada área com numerador/denominador e “agrupado pelo curso atual”. Não imprimir IDs.

Oráculo: na mesma semana, Computação tem 2 ativados/1 útil; Direito 1/1; desconhecido 1/0.
Total deve ser 4/2 e soma dos grupos também. Um dos perfis pode estar pausado e continua
contando conforme regra existente. Duas vagas úteis do mesmo perfil continuam um perfil útil.
Trocar curso de um perfil muda apenas seu grupo, não o total. Rodar Q.

Fechamento: soma por semana bate com total existente, incluindo semanas parciais. Não acrescentar
filtro de ativo ao denominador por conveniência nem interpretar amostra pequena como conclusão.

## R01

**Guardar motivo da pausa atual. P1. Pronta.**

Arquivos: migration nova, `tests/web/migrations_test.ts`, `docs/contrato-front.md`.
Contrato deste lote: coluna nullable `motivo_pausa` em `perfis`, valores
`conseguiu_estagio`, `interrompeu_busca`, `sem_vagas_uteis`, `frequencia`, `outro`.
Sem texto livre ou enum de eventos novo. Campo ausente/null é resposta não informada.
Guardar motivo da pausa atual, não histórico de todas as pausas. Não migrar causas presumidas.

Permitir atualização apenas dentro das permissões do próprio perfil existentes. Preservar
RLS e bloqueio de conta excluída. Nenhuma constraint pode impedir pausar sem responder.
Não acoplar exigência de motivo ao campo `ativo`. Conferir exportação/exclusão existentes e
incluir o novo campo onde a exportação listar campos explicitamente.
Aceite: dono pode responder/null; valor inválido e acesso a outro perfil rejeitados; contas
antigas permanecem válidas. Testar banco isolado. R02 deve limpar motivo ao retomar.

### Migration e propriedade dos dados

1. Criar migration incremental posterior a C01 com `motivo_pausa text null` e check do catálogo
   desta ficha. Atualizar grant por coluna preservando grants existentes e RLS por `auth.uid()`.
2. Conferir função de exportação da migration 0015 e caminho de exclusão; se exportação enumera
   campos, incluir motivo. Não criar tabela de histórico nem alterar gatilho de pausa.
3. Em B: inserir perfil antes da migration e confirmar motivo null depois; dono grava cada
   valor/null; inválido é rejeitado; outro usuário não altera; conta excluída permanece bloqueada.
4. Documentar que o frontend vai apagar motivo ao retomar, e que campo não registra histórico.

Fechamento: pausar funciona com motivo null, sem obrigar pergunta. Coluna/permissões precisam
estar publicadas antes de R02/R03. Não aplicar migration remota como parte do teste isolado.

## R02

**Motivo opcional depois da pausa. P1. Depende de R01.**

Arquivos: `web/assets/app.js`, `web/index.html`, estilos pontuais e testes de cadastro/conta.
Após confirmação de pausa bem-sucedida, mostrar pergunta opcional com rótulos claros para os
cinco valores de R01 e ação “Pular”. Não pedir antes nem bloquear o botão de pausa.
Persistir resposta em chamada separada: falha ao salvar motivo mantém conta pausada e permite
repetir ou pular. Retomar limpa `motivo_pausa` no mesmo update que ativa, preservando os demais
controles. Não coletar motivo de pausa automática por falhas como se fosse resposta do estudante.

Aceite: pausar sem resposta, responder, erro na resposta e retomar funcionam; foco vai para
estado confirmado; pular fecha sem reativar; reabrir conta pausada não repete pergunta
obrigatoriamente. Se o frontend reativar automaticamente em outro fluxo, limpar o motivo ali
também; não deixar um motivo antigo reaparecer após nova pausa. Não adicionar e-mail, incentivo ou cobrança para reter quem conseguiu estágio.

### Fluxo de pausa, resposta e retomada

R02.1: revisar `alternarEntregas` e handler da conta. Só exibir pergunta quando update de pausa
retornar sucesso; manter confirmação de pausa visível mesmo se salvar motivo falhar.
R02.2: controles com os cinco rótulos e “Pular”. Salvar motivo somente para perfil próprio
atualmente pausado; filtrar update por usuário e `ativo=false`. Conferir retorno de linha para
não mostrar salvo se outra aba retomou. Nunca alterar `ativo` ao salvar resposta.
R02.3: retomar envia `{ativo:true, motivo_pausa:null}` no mesmo update. Fechar pergunta e limpar
estado local após sucesso. Durante requisição impedir envio duplicado; falha permite tentar de novo.

| Cenário W | Resultado |
|---|---|
| Falha ao pausar | Conta permanece ativa; pergunta não aparece |
| Pausa OK + Pular | Pausada, sem motivo |
| Pausa OK + resposta OK | Pausada, motivo escolhido persistido |
| Erro ao salvar motivo | Pausada, erro recuperável, pode pular |
| Retomada OK | Ativa, motivo null |
| Retomada falha | Estado pausado e motivo anterior preservados |
| Resposta atrasada após outra aba retomar | Não grava motivo em perfil ativo |
| Logout com pergunta aberta | Estado local descartado; nada aparece para nova pessoa |

Fechamento: foco chega à confirmação/pergunta, todos os controles funcionam por teclado,
nenhuma resposta ou falha reativa conta. Não oferecer recompensa ou bloquear saída.

## R03

**Distribuição dos motivos das contas pausadas. P1. Depende de R02.**

Arquivos: relatório/modelo/storage e testes. Mostrar situação atual: perfis não excluídos com
`ativo=false`, agrupados pelo motivo ou “Não informado”. Denominador inclui os sem resposta.
Separar `conseguiu_estagio` de `sem_vagas_uteis`. Não chamar o quadro de churn mensal nem
reconstruir histórico inexistente. Retomada remove usuário desse quadro. Pausa técnica sem
resposta permanece “Não informado”, não inferir intenção. Contagens devem fechar com o total.
Atualizar `docs/metricas.md`. Testar vazio, todos os motivos, sem resposta, retomada e exclusão.

Uma resposta em branco ou inválida não deve reativar conta. O quadro representa estado atual,
sem promessa de tendências históricas ou taxa de churn.

### Quadro de situação atual

1. Criar agregação SQL separada das CTEs de coorte: `excluida_em is null AND ativo=false`.
   Janela de criação/relatório não restringe este quadro; o título deve dizer situação atual.
2. Retornar contagens por motivo e null. Adicionar campo aditivo ao modelo, conversão e CLI.
3. Atualizar schema reduzido do teste SQL com `ativo`, `excluida_em`, `motivo_pausa`; não
   inventar defaults nos testes que removam os casos de null ou usuário antigo.
4. Testar Q: cinco pausados com um de cada motivo e dois pausados sem motivo → total sete.
   Adicionar ativo com motivo residual e excluído pausado → total continua sete. Retomar um
   dos sete → total seis. Dataset vazio → nenhuma conta pausada, sem divisão por zero.

Fechamento: soma das categorias fecha com total e inclui pausas técnicas sem resposta.
Não reutilizar “recusas por motivo” de vagas nem chamar esse quadro de taxa histórica de churn.
