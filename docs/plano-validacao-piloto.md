# Plano de validação do piloto

**Atualizado em 07/09/2026 · Estado: preparação**

Validar se estudantes recebem uma recomendação útil e voltam a usar o Radar. Este plano
substitui o antigo plano de melhorias RCD; tarefas concluídas e cronogramas vencidos ficam
no histórico do Git. Funcionalidades estão no [catálogo](funcionalidades.md), publicação no
[guia](guia-publicacao-e-piloto.md) e pendências gerais no [plano geral](plano-geral.md).

Princípios RCD mantidos: cadastro não comprova valor; retorno e ação útil são sinais mais
fortes. Com 10–20 participantes, usar observação e cinco entrevistas, sem teste A/B.
A nova revisão de produto deve partir dos resultados deste piloto.

## 1. Preparar a entrada

**Pendente:** confirmar o site publicado, revisar os textos e completar o teste integrado.

**Ação:** seguir o guia com conta de teste: cadastro, confirmação entre aparelhos, recuperação,
vínculo, primeira entrega, abertura, feedback, edição, exportação e exclusão. Registrar data,
resultado e falhas; separar contas de teste da coorte. Combinar quem atende dúvidas e incidentes.

**Métrica:** etapas concluídas e bloqueios encontrados no caminho até a primeira abertura.

**Concluído quando:** jornada crítica funciona no endereço definitivo, documentos revisados,
configurações conferidas e responsáveis registrados. Não recrutar para uma etapa bloqueada.

## 2. Fechar a medição que falta

**Já existe:** eventos da jornada, vagas abertas distintas, feedback individual, utilidade
semanal, recusas com denominadores e resumo de extrações.

**Pendente:** consulta de tempos medianos, taxas de ativação por janela e retenção D7.

**Ação:** preparar consultas reproduzíveis usando os eventos existentes e um recorte explícito
da coorte. Identificar fonte de recrutamento por registro mínimo, sem confundir origem de
clique no site com canal de aquisição. Pode começar manualmente; não exige dashboard.

**Métricas e regras:**

- **Primeira entrega:** criação do perfil → primeira recomendação; informar mediana dos que
  receberam e quantos ainda não receberam. Tempo desde vínculo pode ser diagnóstico separado.
- **Ativação em 24 horas:** vinculados que receberam recomendação até 24 horas após vínculo /
  vinculados com pelo menos 24 horas de observação. Mostrar também a janela de sete dias.
- **Ativação de produto e TTV:** primeira abertura após criação do perfil; calcular taxa em sete
  dias para perfis com janela completa e mediana de tempo dos que abriram.
- **North Star:** ativados com ao menos uma vaga útil na semana / ativados elegíveis, conforme
  [Métricas](metricas.md). Recortar participantes do piloto e marcar semana parcial.
- **Retenção D7:** regra operacional proposta para este piloto: entre participantes com primeira
  interação nos dias 0–6 após ativação operacional, quantos voltam a abrir ou responder nos dias
  7–13. Contar apenas quem completou a observação; confirmar a regra antes de recrutar.
- **Qualidade:** recusas por motivo e grupo de anúncio, sempre com quantidade de entregas como
  denominador. Ausência de resposta não é aprovação.
- **Operação:** extrações, duração, falhas e tempo de suporte. Extrações não equivalem a custo
  monetário total.

**Concluído quando:** consultas conferidas com casos conhecidos, regras e período registrados,
contas de teste excluídas e resultados apresentam contagens junto dos percentuais. Não confundir
North Star semanal com retenção D7. Apagamento de contas pode alterar agregados históricos;
registrar a data da consulta e preservar apenas resultados agregados para comparação.

## 3. Acompanhar 10–20 estudantes

**Pendente:** recrutamento e acompanhamento concluídos não estão registrados.

**Ação:** recrutar universitários de tecnologia buscando estágio e dispostos a usar Telegram.
Acompanhar cada participante por 14 dias completos; se as entradas forem escalonadas, estender
o calendário. Registrar canal e datas de entrada, sem ampliar a coleta de dados sem necessidade.

**Métricas:** conclusão do cadastro, vínculo, primeira entrega, abertura, utilidade e retorno.
Investigar ausência de vagas separadamente de falha técnica de envio.

**Critérios:** as metas iniciais já propostas são mediana de primeira entrega abaixo de
15 minutos e pelo menos 80% dos vinculados recebendo recomendação em 24 horas. Confirmar
limites e definição do relógio antes de iniciar; considerar a exceção do diário sem esconder
seu efeito no resultado geral. Um teste técnico em quatro minutos não comprova essas metas.

**Concluído quando:** todos completaram a observação ou tiveram saída registrada e os resultados
mostram numeradores, denominadores e perdas. Utilidade e retenção ainda não têm um limiar
aprovado: defini-lo antes do piloto, sem escolher depois para favorecer o resultado.

## 4. Fazer cinco entrevistas

**Pendente:** entrevistas concluídas não estão registradas.

**Ação:** conversar com participantes que usaram, ignoraram ou abandonaram o serviço. Pedir
exemplos concretos de recomendações recebidas:

- Como procurava estágio antes e o que mudou durante o piloto?
- Qual vaga serviu e o que a tornou útil?
- Qual nota ou explicação pareceu errada? Por quê?
- Por que deixou de abrir ou responder alguma mensagem?
- O Telegram e a frequência ajudaram ou incomodaram?
- Candidatou-se a alguma vaga recebida? Qual foi o papel do Radar?
- O que precisa melhorar para continuar usando?

**Métrica:** padrões de utilidade, confiança, abandono e adequação do canal, ligados a exemplos.
Candidatura é relato qualitativo, pois o produto não captura esse evento; não apresentar como
conversão automaticamente atribuída.

**Concluído quando:** cinco conversas registradas com acesso restrito, síntese sem identificação
desnecessária e problemas priorizados por impacto. Não publicar depoimentos sem autorização.

## 5. Decidir a próxima rodada

**Ação:** reunir a equipe ao fim da observação e comparar resultados com os critérios definidos.

- **Falha de cadastro ou entrega:** corrigir a jornada e repetir a parte afetada.
- **Entrega funciona, utilidade baixa:** investigar cobertura, perfil e recusas; comparar grupos
  de anúncios com denominadores antes de alterar ranking ou ativar nova fonte.
- **Utilidade existe, retorno baixo:** investigar frequência, Telegram e fim da busca por estágio.
  Conseguir estágio é motivo diferente de abandonar por frustração.
- **Utilidade e retorno sustentados:** planejar novo ciclo e, então, avaliar um teste comercial.

**Concluído quando:** uma decisão registrada informa evidência, limitação da amostra, ação,
responsável e data de revisão. Atualizar a landing somente com resultados verificáveis.

## Fora desta rodada

Checkout, assinatura, página de preços, novas frentes de produto e expansão de público não são
entregas deste piloto. Jooble e a personalização v1 já existem; qualquer mudança durante a
observação deve ser registrada, pois altera a interpretação dos resultados.

Após o piloto, uma nova revisão RCD pode avaliar retenção, custo e eventual disposição a pagar.
O objetivo agora é comprovar valor e identificar o próximo problema, não executar todo o
roadmap antigo.
