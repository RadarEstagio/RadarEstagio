# Plano de expansão e melhoria do Radar de Estágio

Atualizado em 08/09/2026. Status: planejamento; funcionalidades abaixo não estão implementadas por este documento.

## Direção e resultado esperado

Atender estudantes de diferentes formações e áreas, entregando recomendações de estágio relevantes e explicadas no Telegram. A expansão remove a restrição a computação; não significa cobertura de todos os anúncios existentes nem garantia de contratação.

O público principal continua definido pela necessidade: estudantes procurando estágio que precisam reduzir o tempo gasto encontrando e avaliando oportunidades. Curso, interesses, momento acadêmico e localização personalizam a experiência. A comunicação pode atender segmentos distintos sem criar um produto separado para cada curso.

A expansão de público está autorizada pela nova direção. Monetização entra como frente de planejamento e validação futura, sem cobrança ou alteração do compromisso de gratuidade neste trabalho. O piloto continua informal: não há quantidade mínima de entrevistas, coorte ou meta estatística obrigatória para divulgar.

## Fundamentos de Revenue-Centric Design

Aplicação da [skill revenue-centric-design](../.agents/skills/revenue-centric-design/SKILL.md):

| Mecanismo ou princípio | Aplicação ao Radar |
|---|---|
| ICP e níveis de consciência | Explicar a dor comum, personalizar por formação e adaptar a mensagem ao canal de aquisição. |
| A promessa tem o tamanho da prova | Comunicar cobertura real e demonstrar recomendações fiéis ao produto. |
| Valor antes do pedido; fricção declarativa | Começar pelo que o estudante procura e pedir a conta para guardar suas escolhas. |
| Hierarquia de atenção | Dar destaque ao próximo passo necessário para receber e avaliar uma recomendação. |
| Tempo até o valor | Acompanhar a primeira abertura, separadamente da entrega técnica. |
| Jobs-to-be-done | Distinguir saída por contratação de abandono por falta de utilidade. |
| Bullseye | Concentrar aquisição nos canais com evidência de estudantes interessados e vagas úteis. |
| Custo de servir e pagamento como evidência | Medir custos reais e testar uma oferta antes de elaborar vários planos. |
| Swiss Knife filter | Priorizar funcionalidades que reforçam seleção e entrega; avaliar custo permanente e esforço do usuário. |

Referências de trabalho: [posicionamento](../.agents/skills/revenue-centric-design/references/positioning-icp-and-gtm.md), [conversão](../.agents/skills/revenue-centric-design/references/conversion-and-landing-pages.md), [ativação](../.agents/skills/revenue-centric-design/references/onboarding-and-activation.md), [retenção](../.agents/skills/revenue-centric-design/references/churn-and-retention.md), [monetização](../.agents/skills/revenue-centric-design/references/pricing-and-monetization.md), [disciplina de produto](../.agents/skills/revenue-centric-design/references/product-strategy-and-features.md) e [experimentação](../.agents/skills/revenue-centric-design/references/metrics-and-experimentation.md). Os princípios orientam hipóteses; estatísticas ilustrativas da skill não são metas nem previsões para este produto.

## Prioridades e sequência

P0: necessário para entregar a expansão com qualidade. P1: melhorar conversão, ativação e utilidade. P2: crescimento e sustentabilidade comercial.

| Ordem | Frente | Prioridade | Dependência | Responsabilidade sugerida |
|---|---|---|---|---|
| 1 | Cobertura e critérios de atendimento | P0 | Nenhuma | Produto + backend |
| 2 | Seleção e ranking para diferentes áreas | P0 | Critérios definidos | Backend |
| 3 | Migração e compatibilidade | P0 | Novo modelo definido | Backend + frontend |
| 4 | Cadastro inclusivo e primeira experiência | P0/P1 | Contrato de perfil definido | Frontend + produto |
| 5 | Landing e demonstração | P1 | Cobertura e comportamento confirmados | Produto + frontend |
| 6 | Métricas e utilidade recorrente | P1 | Base atual; ampliar junto das frentes 2–4 | Backend + produto |
| 7 | Publicação e operação | P0 | Verificação integrada | Equipe |
| 8 | Aquisição e prova real | P2 | Jornada funcional | Produto |
| 9 | Oferta paga e economia | P2 | Evidência de utilidade e custos | Equipe |

Os responsáveis são papéis propostos; a equipe distribui os nomes antes de executar. Não há estimativa de calendário sem conhecer capacidade e disponibilidade. Métricas básicas, inventário de cobertura e rascunhos de interface podem avançar juntos; publicação da promessa ampla depende da seleção funcionando.

## 1. Cobertura e critérios de atendimento

- [ ] Inventariar consultas, termos e filtros de cada coletor que restringem a tecnologia.
- [ ] Amostrar anúncios disponíveis nas fontes atuais por área, cidade, modalidade e formação exigida; registrar data da observação.
- [ ] Distinguir ausência de oferta, falha de coleta e rejeição pelo ranking.
- [ ] Definir um catálogo inicial extensível de áreas com exemplos e aliases, permitindo múltiplas áreas e classificação desconhecida.
- [ ] Considerar formações de níveis distintos, sem presumir que todo estágio exige graduação ou que todo curso usa semestres.
- [ ] Medir lacunas antes de ativar Jooble ou implementar outra fonte. Conferir acesso, limites e qualidade das descrições no momento da decisão.
- [ ] Evitar tratar bolsa não informada, modalidade desconhecida ou descrição incompleta como dado confirmado.

Conclusão: existe uma matriz datada de cobertura e um contrato claro do que será aceito. Áreas pouco cobertas recebem comunicação honesta; a arquitetura permite sua inclusão sem nova reescrita geral.

## 2. Seleção, elegibilidade e ranking

Superfícies atuais: `radar/collectors/`, `radar/filtering/prefiltro.py`, `radar/domain/models.py`, `radar/matching/prompt.py`, `compatibilidade.py` e `avaliacoes.py`.

- [ ] Remover a exclusão geral de vagas fora de computação, preservando identificação de estágio, deduplicação e restrições reais do perfil.
- [ ] Substituir `area_de_tecnologia` e interesses exclusivos de computação por critérios adequados a diferentes áreas.
- [ ] Comparar curso do estudante com cursos explicitamente aceitos. Reconhecer aliases e “qualquer curso”; não declarar elegibilidade apenas porque um curso pertence a uma grande área.
- [ ] Tratar requisito obrigatório incompatível, preferência não atendida e informação ausente de formas distintas.
- [ ] Extrair habilidades técnicas, ferramentas, idiomas e outros requisitos explícitos pertinentes ao anúncio. Rever exclusões globais como Office/idiomas, relevantes em outras áreas.
- [ ] Preservar separação entre obrigatório, atividade principal e desejável; não transformar requisito desejável em veto.
- [ ] Rever pesos dominados por habilidades de software. Começar com critérios explicáveis comuns; adotar pesos específicos por área somente quando exemplos e feedback justificarem.
- [ ] Não favorecer anúncio incompleto por parecer fácil de atender; manter incerteza visível e nota contextualizada como compatibilidade, nunca chance de contratação.
- [ ] Adaptar personalização por recusas para o novo catálogo sem ampliar uma rejeição específica para áreas inteiras indevidamente.

Verificação: conjunto de casos com anúncios de áreas distintas, perfis iniciantes, cursos equivalentes e incompatíveis, dados ausentes, requisitos desejáveis, modalidade e período. Incluir perfis atuais de tecnologia para detectar regressões. Testes devem verificar seleção e explicações, além da pontuação.

Conclusão: vaga elegível de outra área chega ao ranking; incompatibilidade explícita não vira recomendação de alta compatibilidade; justificativas correspondem aos fatos do anúncio e do perfil.

## 3. Migração sem perda de perfil e histórico

- [ ] Mapear campos, enums, validações, SQL, frontend e feedback afetados pelo novo modelo.
- [ ] Versionar mudanças de banco em migrations e planejar uma transição compatível entre versões do site, funções e job.
- [ ] Mapear interesses antigos para o novo catálogo; preservar ambiguidades sem inventar preferências.
- [ ] Versionar extrações e regras de avaliação, identificando resultados antigos que exigem reextração ou recálculo.
- [ ] Reprocessar de forma controlada, com limite de custo e prioridade para anúncios ainda relevantes.
- [ ] Preservar vínculos, consentimentos, histórico de envios e bloqueio de repetição. Recalcular nota não autoriza reenviar vaga já entregue.
- [ ] Testar migração com dados representativos e definir reversão de aplicação e recuperação dos dados antes da publicação.

Conclusão: perfis existentes continuam utilizáveis, o cache não mistura regras incompatíveis e a transição não produz reenvios indevidos.

## 4. Cadastro, iniciantes e primeira experiência

Mecanismos: fricção declarativa, divulgação progressiva e valor antes do pedido.

- [ ] Prototipar sequência: formação/momento → interesses e logística → habilidades → conta para salvar → confirmação quando exigida → Telegram.
- [ ] Mostrar poucas sugestões contextuais, busca e entrada livre; evitar uma lista extensa de todas as profissões.
- [ ] Permitir múltiplos interesses e incerteza sobre a área desejada sem interpretar isso como autorização irrestrita.
- [ ] Incluir “Ainda estou aprendendo” ou “Não quero informar agora”, diferenciando os estados quando necessário. Ajustar também validações de domínio e banco que exigem uma habilidade.
- [ ] Pedir dados que influenciam seleção e explicar sua finalidade; permitir informar requisitos adicionais depois, quando fizerem diferença.
- [ ] Preservar escolhas ao voltar etapas e confirmar em outro aparelho, mantendo o comportamento existente.
- [ ] Mostrar confirmação e vínculo no progresso total; não apresentar cadastro concluído como entrega já ativada.
- [ ] Manter recuperação, reenvio, edição e erros acionáveis; verificar uso em celular, teclado e leitores de tela nas partes alteradas.
- [ ] Confirmar estados de perfil salvo, Telegram vinculado e busca solicitada. Só afirmar busca iniciada quando houver evidência desse estado.
- [ ] Preservar entrega inicial existente e explicar espera/fallback para o diário, sem prometer prazo não medido.
- [ ] Diferenciar ausência de vagas de falha operacional; oferecer edição de preferências sem pressionar o estudante a aceitar condições inadequadas.

Conclusão: o estudante consegue cadastrar um perfil verdadeiro, recuperar interrupções e entender quando e onde receberá recomendações. Observar colegas usando ajuda a encontrar erros, sem amostra mínima obrigatória.

## 5. Landing, confiança e demonstração

- [ ] Atualizar título, descrição, metadados, formulário e exemplos para diferentes áreas.
- [ ] Explicar limite de até cinco recomendações quando houver oportunidades compatíveis e indicar Telegram antes do CTA.
- [ ] Uniformizar a condição gratuita vigente, esclarecendo o que ela cobre. Não anunciar um preço ou prazo ainda não decidido.
- [ ] Identificar a demonstração visivelmente como “Exemplo ilustrativo” e usar o formato real da mensagem.
- [ ] Trocar “match” pelo vocabulário do produto e alinhar alegações sobre IA ao comportamento real.
- [ ] Tratar logos como fontes/tecnologias, sem sugerir endosso ou prova de resultado.
- [ ] Responder às dúvidas principais: áreas atendidas, dias sem vagas, vínculo, edição, pausa e candidatura na fonte.
- [ ] Acrescentar prova real autorizada quando disponível, com contexto e sem inferir contratação a partir de um clique.

Copy inicial proposta:

> **Encontre estágios que combinam com seu curso e seu momento.**
> O Radar reúne oportunidades de diferentes áreas, compara com seu perfil e envia até cinco recomendações explicadas no Telegram, quando houver vagas compatíveis.
> **Cadastrar meu perfil**

Conclusão: promessa, demonstração e entrega descrevem o mesmo produto. Verificar legibilidade e funcionamento da página em tamanhos móveis e desktop.

## 6. Medição e retenção por utilidade

Preservar definições de `CONTEXT.md` e `docs/metricas.md`. A primeira abertura é ativação de produto; feedback positivo é evidência explícita de utilidade. Candidatura continua sem captura nova até existir mecanismo próprio.

- [ ] Conferir instrumentação de credenciais, etapas, confirmação, vínculo e primeira entrega; acrescentar eventos apenas para perguntas ainda sem resposta.
- [ ] Segmentar cobertura e utilidade por formação/área e localização, indicando tamanho das amostras e permitindo múltiplos interesses sem somar usuários duas vezes no total.
- [ ] Apresentar alcance de etapas como alcance; construir conversão sequencial somente com ordem, identidade e janela definidas.
- [ ] Acompanhar tempo até primeira entrega e primeira abertura junto da proporção ainda sem cada resultado. Não calcular sucesso apenas sobre os que completaram.
- [ ] Ler utilidade semanal ao lado da participação no feedback e dos motivos de recusa; ausência de resposta não é aprovação.
- [ ] Manter a métrica geral atual e acrescentar leitura por tempo desde cadastro quando útil. Não remover silenciosamente pausados do denominador para melhorar indicadores.
- [ ] Pedir motivo opcional da pausa: conseguiu estágio, interrompeu a busca, faltaram vagas úteis, frequência ou outro. Resposta não condiciona a pausa.
- [ ] Separar saída por sucesso de insatisfação; oferecer retomada simples.
- [ ] Ajustar frequência somente se o uso indicar necessidade. Não criar notificações ou recompensas artificiais para produzir engajamento.
- [ ] Registrar data das consultas e limitações de exclusão de dados, semanas parciais, amostras pequenas e atribuição.

Conclusão: a equipe consegue identificar se o problema é aquisição, cadastro, cobertura, relevância ou conclusão da busca. As métricas existentes podem continuar em relatório; dashboard não é requisito.

## 7. Publicação e operação

- [ ] Resolver as pendências atuais do plano geral: endereço público, configuração de Auth, Turnstile, textos pendentes e responsáveis pela operação.
- [ ] Verificar a jornada integrada: cadastro, confirmação, recuperação, vínculo, entrega, abertura, feedback, edição, pausa e controles da conta.
- [ ] Monitorar duração de coleta, extrações novas, falhas, entregas e custo após ampliar áreas/cidades.
- [ ] Estimar carga com diversidade de perfis: reuso de extração reduz duplicação, mas ampliar cobertura aumenta anúncios e trabalho.
- [ ] Publicar banco, backend, funções e frontend em ordem compatível; confirmar logs e exemplos após atualização.
- [ ] Corrigir bloqueadores funcionais e incompatibilidades graves antes de ampliar a divulgação. Problemas específicos de cobertura podem ser comunicados e acompanhados sem fingir atendimento comprovado.
- [ ] Atualizar documentação de funcionalidades, operação e contrato após a implementação efetiva.

Conclusão: a equipe sabe publicar, verificar, responder a falhas e reverter uma versão defeituosa. Prazo de primeira entrega observado não vira garantia pública automaticamente.

## 8. Aquisição e diferenciação

Mecanismos: Bullseye, consciência do público e prova antes da escala.

- [ ] Começar pelos canais acessíveis à equipe, como colegas, comunidades de cursos e contatos com centros acadêmicos; selecionar conforme acesso e retorno observado.
- [ ] Adaptar exemplos por área, preservando a promessa central. Páginas específicas só entram quando houver demanda e cobertura que justifiquem manutenção.
- [ ] Registrar origem de aquisição sem incluir dados pessoais nos parâmetros da URL.
- [ ] Comparar usuários que chegam e sinalizam utilidade por canal; separar público próximo da equipe de pessoas sem vínculo anterior.
- [ ] Facilitar compartilhamento voluntário após uma experiência útil, sem expor links pessoais rastreáveis ou tokens de vínculo.
- [ ] Avaliar investimento em mídia após compreender gargalos e custo por usuário com utilidade; definir orçamento e regra de parada antes de gastar.

Conclusão: há evidência de quais canais trazem estudantes atendidos pelo produto. A diferenciação demonstrada combina seleção pessoal, explicações, menor repetição e melhoria por feedback.

## 9. Monetização e economia

Mecanismos: custo de servir, pagamento como evidência e oferta no momento de valor.

- [ ] Definir hipótese inicial de pagador. Estudante é a hipótese B2C; instituição patrocinadora exige validação comercial separada e não deve misturar prioridades de imediato.
- [ ] Medir custos fixos, incrementais, suporte, taxas de pagamento e aquisição. Vagas extraídas por ativado é indicador operacional, não custo em reais.
- [ ] Investigar benefício pelo qual usuários com utilidade pagariam e alternativas que já usam.
- [ ] Comparar uma assinatura simples com acesso por período de busca, considerando saída por contratação. Não fixar preço sem observar disposição de pagar e custo.
- [ ] Preparar oferta concreta com preço, duração, condições de acesso, renovação e cancelamento; preservar o que foi prometido aos participantes gratuitos.
- [ ] Testar pagamento real com participantes informados. Intenção declarada e clique em interesse não equivalem a compra.
- [ ] Medir visitantes elegíveis à oferta, compradores, uso posterior, cancelamentos, receita líquida e margem de contribuição por coorte.
- [ ] Considerar expansão paga somente por benefício adicional comprovado. Não bloquear de surpresa uma vaga já prometida nem criar perda fictícia de histórico.
- [ ] Definir mais planos apenas se aparecerem necessidades e disposições de pagar distintas. Good-Better-Best e ancoragem são opções futuras, não requisitos para este MVP.

Conclusão: existe uma oferta testável e uma leitura de sustentabilidade. Se utilidade existir sem pagamento, investigar pagador, benefício e modelo antes de escalar aquisição paga.

## Critérios de decisão e controle de escopo

Não prometer aumentos percentuais sem medição. Com pouco volume, usar problemas observados e feedback concreto; A/B exige amostra e regra de decisão definidas previamente. Metas numéricas podem ser estabelecidas após a linha de base, sem importar benchmarks da skill.

Para cada entrega, registrar problema, responsável, dependência, evidência de funcionamento e próximo ajuste. Aplicar o Swiss Knife filter a currículo por IA, dashboard, cursos, candidatura automática, gamificação e novas integrações: só priorizar quando reforçarem a entrega central e justificarem custo permanente.

Primeiro lote executável: inventário das restrições a tecnologia, matriz de cobertura, proposta do novo contrato de perfil/vaga e conjunto de exemplos de aceitação. Depois, implementar seleção e migração; integrar cadastro e comunicação; verificar a jornada; divulgar e melhorar com os sinais reais.
