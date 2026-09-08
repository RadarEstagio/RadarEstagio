# Fichas — métricas e retenção

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

## M02

**Mostrar participação no feedback. P1. Pronta.**

Arquivos: `radar/storage/metricas.sql`, `radar/domain/models.py` (modelo do relatório),
`radar/reporting/funil.py`, conversão do resultado no storage, `tests/web/metricas_test.ts` e
testes Python do relatório. Reusar consultas e deduplicação existentes.

Janela: a mesma dos envios em `entregas_do_periodo`. Denominador: pares distintos
`(perfil_id,vaga_id)` entregues nessa janela. Se houver múltiplos registros de envio para o mesmo par, deduplicar antes do join.
Numerador: pares com feedback positivo ou negativo
posterior à entrega e até a data da consulta, usando a última resposta e desempate por ID.
Retornar contagens e percentual; sem entregas, “sem denominador”. Não usar aberturas como resposta.
Não substituir utilidade semanal. Aceite: repetição não infla, correção da resposta ainda conta
uma resposta, feedback anterior à entrega não vale, sem resposta não é aprovação. Testar SQL
isolado e apresentação. Exibir, por exemplo, “Respostas: 3 de 10 recomendações (30%)”;
o percentual é derivado das contagens, não persistido. Atualizar definição em `docs/metricas.md`.

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
