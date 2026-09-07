# Plano de Melhorias — Revenue-Centric Design

> Estratégia de referência. Hipóteses, sugestões e portões abaixo não são todos requisitos aprovados. A execução vigente é acompanhada no plano geral.
> Estado atual: [funcionalidades](funcionalidades.md), [plano geral](plano-geral.md) e [índice](README.md).

**Projeto:** Radar de Estágio

**Data:** 30/08/2026; execução revisada em 07/09/2026

**Horizonte inicial:** seis semanas

**Framework:** Revenue-Centric Design (RCD)

**Fase atual do produto:** Fase 2 — MVP de validação com usuários, parcialmente implementada

**Estado atual:** cadastro, controles da conta, feedback individual, rastreamento, consulta
semanal e entrega após vínculo estão implementados. O piloto, a comprovação de retenção e
monetização continuam pendentes. Nem todas as métricas originalmente propostas têm consulta.

### Legenda da revisão

- ✅ **Implementado/concluído:** existe no código ou há conclusão registrada.
- 🟡 **Parcial:** parte entregue; a pendência vem indicada.
- ⬜ **Não implementado/não validado:** falta código ou evidência da atividade.
- ➖ **Substituído/fora do escopo:** decisão posterior mudou a proposta original.

Implementação não significa publicação nem prova de valor com estudantes. Esta revisão foi
feita contra código e documentos; não repetiu testes remotos. Evidências datadas estão no
[guia](guia-publicacao-e-piloto.md). Os prazos semanais abaixo são do plano original.

### Resumo por fase

- ✅ **Fase 0:** base de cadastro e mensagem entregue; apresentação realizada.
- 🟡 **Fase 1:** eventos e relatório principal prontos; faltam taxas por janela, medianas e retenção D7.
- 🟡 **Fase 2:** dispatch e primeira entrega testados; falta experiência de progresso/celebração e medir a coorte.
- 🟡 **Fase 3:** perfil, segurança e seis respostas entregues; cadência alternativa não implementada e documentos em revisão.
- ⬜ **Fase 4:** piloto, entrevistas e prova social ainda sem conclusão registrada.
- ⬜ **Fase 5:** pagamento, modelo comercial e unit economics completos não validados.
- 🟡 **Fase 6:** histórico e personalização v1 existem; diferenciação sustentada por resultados não foi comprovada.

## 1. Objetivo

Transformar o Radar de uma demonstração técnica funcional em um produto capaz de comprovar que:

1. estudantes concluem o cadastro;
2. recebem valor rapidamente;
3. abrem e consideram as recomendações úteis;
4. continuam usando o serviço;
5. candidatam-se por causa do Radar;
6. uma parcela aceita pagar pelo resultado.

A ordem de trabalho será:

> **corrigir → medir → ativar → reter → provar → monetizar → diferenciar**

Essa sequência segue o princípio de adequar o trabalho de produto ao estágio atual: no MVP,
encurtar o caminho até o valor; depois ativar, converter, expandir e sistematizar
([referência RCD](https://x.com/richardrx/status/2066476811177877962)).

## 2. Métricas centrais

### 2.1 North Star inicial

**Situação em 07/09:** ✅ Consulta semanal implementada em `radar/storage/metricas.sql`; validação com feedback de uma coorte ainda pendente.

> **Percentual de estudantes com ativação operacional que encontram pelo menos uma vaga útil por
> semana.**

### 2.2 Resultado final de negócio

**Situação em 07/09:** ➖ Sem emissor de candidatura por decisão posterior. O relatório aceita registros históricos, mas não mede novas candidaturas pelo produto atual.

> **Candidaturas qualificadas iniciadas por usuário com ativação operacional por semana.**

### 2.3 Definições

**Situação em 07/09:** 🟡 Conceitos definidos; tempo mediano, TTV e retenção D7 ainda não têm cálculo no relatório atual. Utilidade semanal não equivale a retenção D7.

- **Ativação operacional:** primeira entrega aceita pelo Telegram contendo ao menos uma recomendação.
- **Ativação de produto:** primeira abertura de uma vaga recomendada.
- **Vaga útil:** recomendação marcada como relevante ou que gera uma candidatura atribuída; uma
  abertura isolada indica interesse, não utilidade.
- **Candidatura qualificada:** candidatura iniciada a partir de uma recomendação considerada útil.
- **Tempo até a primeira entrega:** intervalo entre a criação do perfil e a ativação operacional.
- **TTV:** intervalo entre a criação do perfil e a ativação de produto.
- **Retenção D7:** usuário que volta a interagir com ao menos uma recomendação na semana seguinte.

## 3. Fase 0 — Estabilizar para a entrega

**Prazo:** até 02/09/2026

**Objetivo:** não demonstrar um funil quebrado ou uma promessa que o produto não entrega.

### 3.1 Corrigir o cadastro

**Situação em 07/09:** ✅ Validações, tratamento de erros e testes implementados, incluindo confirmação entre aparelhos e recuperação. Falta concluir teste integrado pela landing publicada; “cada falha possível” não é garantia de cobertura exaustiva.

**Registro inicial:** ajustes entregues em 30/08/2026; situação atual detalhada acima.

- Validar a etapa 3 antes do envio.
- Impedir cidade, modalidade, e-mail ou senha inválidos.
- Tratar o caso de conta criada sem perfil salvo.
- Traduzir erros técnicos do Supabase para mensagens humanas e acionáveis.
- Criar testes para cada falha possível do último passo.

**Critério de conclusão:** nenhum dado inválido chega ao Supabase e todo erro informa como o
usuário pode continuar.

### 3.2 Alinhar promessa e produto

**Situação em 07/09:** 🟡 Mensagem, edição de perfil e catálogo atualizados; documentos históricos identificados. A revisão final dos textos públicos e legais segue pendente. Hoje há personalização por feedback, limitada à v1.

**Registro inicial:** ajustes entregues em 30/08/2026; situação atual detalhada acima.

- Remover dos documentos a afirmação de que o Radar aprende com feedback enquanto isso não existir.
- Não prometer edição do perfil sem oferecer a interface correspondente.
- Substituir “Chegue antes” por uma promessa comprovável ou medir o tempo real entre publicação,
  detecção e entrega.
- Atualizar a fase declarada do projeto, pois partes relevantes da Fase 2 já estão implementadas.
- Atualizar números antigos de testes e evidências técnicas.

### 3.3 Tornar a mensagem real igual à demonstração

**Situação em 07/09:** ✅ Conteúdo implementado; o link pode passar por `ir` antes da fonte. Listas longas são resumidas e desejáveis ausentes não são cobrados.

**Registro inicial:** ajustes entregues em 30/08/2026; situação atual detalhada acima.

A mensagem do Telegram agora inclui:

- localização e modalidade, quando informadas;
- fonte da vaga;
- data de publicação;
- nota e justificativa;
- pontos a favor e contra;
- link original.

**Critério de conclusão:** tudo que aparece na demonstração da landing existe na entrega real.

### 3.4 Preparar a apresentação

**Situação em 07/09:** ✅ Apresentação já realizada; roteiro removido da documentação ativa.

**Status:** preparação concluída em 30/08/2026; apresentação já realizada. O roteiro foi retirado da documentação ativa e permanece recuperável pelo histórico do Git.

Apresentar separadamente:

- o que foi tecnicamente comprovado;
- o que ainda é hipótese de produto;
- os marcos de ativação operacional e de produto;
- o risco relacionado ao tempo até o primeiro valor;
- o plano de validação com usuários.

## 4. Fase 1 — Instrumentar o funil

**Prazo:** semana 1

**Objetivo:** localizar cada vazamento antes de redesenhar ou expandir o produto.

### 4.1 Eventos mínimos

**Situação em 07/09:** 🟡 Emissores da jornada, abertura e feedback implementados. Apenas candidatura ficou deliberadamente sem emissor; testar o cadastro público completo permanece pendente.

**Registro inicial:** instrumentação parcial da jornada em 30/08; abertura e feedback foram acrescentados depois.

- `landing_visualizada`
- `cta_cadastro_aberto`
- `etapa_perfil_concluida`
- `etapa_habilidades_concluida`
- `etapa_preferencias_concluida`
- `conta_criada`
- `email_confirmado`
- `perfil_salvo`
- `telegram_aberto`
- `telegram_vinculado`
- `primeira_recomendacao_enviada`
- `vaga_aberta`
- `vaga_util`
- `vaga_irrelevante`
- `candidatura_iniciada`
- `entregas_pausadas`

Todos os eventos listados têm emissor no código, exceto `candidatura_iniciada`,
retirado do escopo de captura. `vaga_aberta` vem de `ir`; `vaga_util` e `vaga_irrelevante`
vêm do feedback individual no webhook. A existência no catálogo SQL sozinha não é emissor.

### 4.2 Métricas do funil

**Situação em 07/09:** 🟡 Ver marcação por métrica abaixo. Os dados e as contagens existem para parte do funil; isso não implica que todas as taxas e janelas estejam calculadas.

- Landing → abertura do cadastro. **✅ Contagens das etapas no relatório.**
- Cadastro aberto → perfil salvo. **✅ Contagens das etapas no relatório.**
- Perfil salvo → Telegram vinculado. **✅ Contagens das etapas no relatório.**
- Telegram vinculado → primeira recomendação. **✅ Contagens das etapas no relatório.**
- Taxa de ativação operacional em 24 horas e em 7 dias. **⬜ Janelas não calculadas no relatório.**
- Tempo mediano até a primeira entrega. **⬜ Mediana não calculada.**
- Taxa de ativação de produto em 7 dias e TTV mediano, depois de `vaga_aberta` existir. **⬜ Abertura existe; taxa em sete dias e TTV mediano ainda não.**
- Recomendação → clique. **✅ Vagas abertas distintas e entregas contabilizadas.**
- Recomendação → vaga útil. **✅ Utilidade por recomendação e por semana calculadas.**
- Recomendação → candidatura. **➖ Sem captura nova; somente compatibilidade com registros históricos.**
- Retenção D7 por interação real. **⬜ Não calculada.**
- Custo de IA por usuário com ativação operacional. **🟡 Indicador de extrações por ativado; não custo monetário completo.**

Com baixo volume, não serão usados testes A/B. Cinco boas entrevistas e observação de sessões
produzem mais sinal que um experimento sem amostra suficiente
([referência RCD](https://x.com/richardrx/status/2061463480868229189)).

**Critério de conclusão:** uma consulta consegue reconstruir o funil completo de cada coorte.

## 5. Fase 2 — Reduzir o tempo até a primeira entrega

**Prazo:** semana 2

**Objetivo:** entregar a primeira recomendação em minutos, não no dia seguinte, e conduzir à
primeira abertura.

### 5.1 Jornada desejada

**Situação em 07/09:** 🟡 Busca por perfil, trava, janela do diário e registros implementados. Teste real de vínculo até mensagem em cerca de quatro minutos está registrado; não comprova mediana da coorte.

```text
Perfil → conta → Telegram → busca imediata → recomendação entregue → vaga aberta
```

Depois do vínculo:

1. mostrar “Telegram vinculado”;
2. informar que o Radar está procurando a primeira oportunidade — 🟡 painel informa próximas execuções, sem progresso ao vivo;
3. executar uma busca específica para o novo perfil;
4. entregar uma recomendação real imediatamente;
5. celebrar o primeiro resultado — ⬜ experiência específica não implementada;
6. registrar `ativado_em` como ativação operacional;
7. registrar a primeira `vaga_aberta` como ativação de produto.

O onboarding só termina quando o usuário interage com o resultado prometido. A prioridade é
reduzir o tempo até a entrega e depois o TTV, não adicionar mais explicações ou funcionalidades
([referência RCD](https://x.com/richardrx/status/2059616501544468624)).

### 5.2 Quando não houver vaga adequada

**Situação em 07/09:** ✅ Não ativa sem recomendação, explica ausência e próxima busca. Ajustes existem no painel; sugestão proativa de ampliar preferências aparece após silêncio prolongado, não necessariamente no primeiro dia.

- Não marcar o perfil como ativado.
- Explicar que nenhuma oportunidade segura foi encontrada.
- Informar quando ocorrerá a próxima busca.
- Oferecer ajuste de cidade ou modalidade.
- Não pressionar o usuário a aceitar vagas ruins apenas para gerar uma entrega.

### 5.3 Metas iniciais

**Situação em 07/09:** ⬜ Metas ainda não comprovadas no piloto. Um teste em quatro minutos não comprova 80% em 24 horas nem mediana abaixo de 15 minutos.

- tempo mediano até a primeira entrega abaixo de 15 minutos.
- Evolução posterior do tempo até a primeira entrega para menos de 5 minutos.
- Pelo menos 80% dos usuários vinculados recebendo uma recomendação em 24 horas.

Esses limites devem ser aprovados antes do piloto e não ajustados posteriormente para justificar
os resultados observados.

## 6. Fase 3 — Dar controle e construir retenção

**Prazo:** semana 3

**Objetivo:** descobrir se as recomendações ajudam e acumular personalização.

### 6.1 Feedback no Telegram

**Situação em 07/09:** ✅ Feedback por vaga implementado com seis respostas. A lista original abaixo foi substituída: positivo e cinco recusas, incluindo nota, área, exigência, logística e repetição. Candidatura e denúncia de vaga encerrada não foram implementadas.

Cada vaga deve permitir:

- ✅ Positivo: entregue como `👍 Essa serviu`.
- ✅ Negativo: entregue como cinco motivos específicos.
- ➖ `Candidatei-me`: sem emissor por decisão do piloto.
- ⬜ `Vaga encerrada ou problemática`: sem opção específica.

A regra inicial de apenas registrar foi substituída pela personalização v1: repetição alimenta
o filtro; subárea com duas ou mais recusas em 30 dias perde o fator de interesse. Os demais
motivos e o positivo não alteram automaticamente os pesos. Eficácia no piloto ainda não comprovada.

### 6.2 Gestão do perfil

**Situação em 07/09:** ✅ Edição, pausa, retomada, desvínculo e exclusão com cancelamento implementados. Também há exportação e revogação de e-mails. 🟡 Informação de próxima busca é geral; não há acompanhamento em tempo real do job no painel.

Criar uma página simples, sem transformá-la em um dashboard completo:

- editar curso, período e habilidades;
- alterar cidade e modalidade;
- pausar e retomar entregas;
- desvincular Telegram;
- excluir conta e dados;
- consultar quando ocorrerá a próxima busca.

### 6.3 Cadência de comunicação

**Situação em 07/09:** ➖ Silêncio com resumo semanal não foi adotado. O produto envia aviso diário sem vagas e sugestão após silêncio prolongado. ⬜ Preferência de cadência ainda precisa ser observada; alertas contínuos por nova vaga não existem.

- Evitar mensagens vazias diárias que possam gerar fadiga.
- Avaliar silêncio nos dias sem vagas, acompanhado por um resumo semanal.
- Manter alertas imediatos somente para oportunidades realmente relevantes.
- Observar se o usuário prefere confirmação diária ou apenas novidades.

### 6.4 Segurança e confiança

**Situação em 07/09:** 🟡 Rotação de token e exclusão implementadas, com revalidação das interações. Textos de privacidade existem, mas revisão final/vigência continuam pendentes.

- Invalidar ou rotacionar o token após o vínculo.
- Impedir que um link antigo redirecione entregas para outro Telegram.
- Criar uma explicação curta de privacidade e finalidade dos dados.
- Oferecer exclusão dos dados sem contato manual.

**Critério de conclusão:** o usuário consegue controlar o serviço e toda recomendação pode gerar
um sinal mensurável de qualidade.

## 7. Fase 4 — Validar produto e construir prova

**Prazo:** semana 4

**Objetivo:** substituir promessas genéricas por evidências reais.

### 7.1 Piloto

**Situação em 07/09:** ⬜ Sem execução concluída registrada. Acompanhar até candidatura exigiria entrevista/manual, pois não há emissor desse evento.

Recrutar de 10 a 20 estudantes que atendam aos critérios:

- universitários de tecnologia;
- buscando o primeiro estágio no momento do teste;
- dispostos a usar Telegram durante duas semanas.

Cada pessoa deve ser acompanhada desde a landing até a primeira candidatura.

### 7.2 Entrevistas

**Situação em 07/09:** ⬜ Cinco entrevistas ainda não registradas como realizadas.

Realizar pelo menos cinco entrevistas aprofundadas:

- Como a pessoa procura estágio hoje?
- Quanto tempo gasta por semana?
- O que faz uma vaga parecer relevante?
- Em quais notas e justificativas confia?
- Telegram é conveniente ou uma barreira?
- Qual recomendação foi útil?
- Por que as outras foram ignoradas?
- O que precisaria acontecer para a pessoa pagar pelo Radar agora?

### 7.3 Landing baseada em prova

**Situação em 07/09:** ⬜ Prova social de resultados do piloto ainda não disponível. Não publicar metas ou testes isolados como resultado de usuários.

Depois do piloto, substituir a faixa de tecnologias por evidências como:

- estudantes com ativação operacional e de produto;
- recomendações consideradas úteis;
- candidaturas iniciadas;
- tempo mediano até a primeira entrega e TTV mediano;
- depoimento verificável com contexto;
- captura anonimizada de uma recomendação real.

A promessa comercial deve crescer apenas na proporção da prova disponível. Quando landing e
produto divergem, cria-se dívida de expectativa e churn futuro
([referência RCD](https://x.com/richardrx/status/2049568514311172355)).

### 7.4 Copy inicial recomendada

**Situação em 07/09:** 🟡 A landing tem mensagem e CTA próprios; o texto abaixo é sugestão original, não reprodução integral implementada nem experimento validado.

**Headline:**

> Pare de garimpar vagas de estágio todos os dias.

**Subheadline:**

> Receba no Telegram oportunidades de tecnologia compatíveis com seu curso, período e
> habilidades — ranqueadas e explicadas.

**CTA:**

> Montar meu Radar grátis

**Microcopy:**

> Cerca de 2 minutos · sem cartão · o Radar nunca se candidata por você

A microcopy deve explicar o que acontece, quanto demora e qual é o compromisso
([referência RCD](https://x.com/richardrx/status/2058875777739866490)).

## 8. Fase 5 — Validar monetização

**Prazo:** semana 5

**Objetivo:** descobrir se existe disposição real a pagar sem construir uma página de preços
prematuramente.

### 8.1 Calcular os unit economics

**Situação em 07/09:** 🟡 Há contagem de extrações e indicador por ativado. ⬜ Custo monetário completo, suporte, vida útil e subsídio entre planos não calculados.

- Custo de IA por usuário.
- Custo por busca.
- Custo por usuário com ativação operacional.
- Custo de suporte.
- Vida útil esperada de um usuário procurando estágio.
- Quantidade de pagantes necessária para sustentar cada usuário gratuito.

O custo gratuito precisa ser tratado explicitamente: em um produto de IA, o usuário gratuito
continua consumindo recursos variáveis
([referência RCD](https://x.com/richardrx/status/2071962778072469560)).

### 8.2 Hipóteses de modelo

**Situação em 07/09:** ⬜ Modelos comerciais não testados nem implementados.

Testar uma hipótese por vez:

1. passe de busca ativa por 30 ou 60 dias;
2. assinatura mensal enquanto o estudante estiver procurando;
3. plano gratuito limitado e entrega diária paga;
4. acesso patrocinado por faculdade ou programa de empregabilidade.

O passe pode se ajustar melhor ao churn estrutural: quando o estudante consegue estágio, o
trabalho para o qual contratou o produto termina.

### 8.3 Teste de transação

**Situação em 07/09:** ⬜ Piloto pago e aceitação de pagamento não realizados; nenhum checkout implementado.

- Oferecer um piloto pago aos primeiros dez usuários.
- Entregar uma primeira prova de valor antes de cobrar.
- Pedir pagamento real, não apenas perguntar “você pagaria?”.
- Quando alguém recusar, perguntar o que precisaria existir para pagar.
- Considerar a hipótese promissora se pelo menos três dos dez aceitarem o compromisso financeiro
  definido antes do teste.

Ainda não criar uma estrutura Good–Better–Best, decoy ou página com três planos. Esses mecanismos
só fazem sentido depois de validar o produto e o eixo de valor.

## 9. Fase 6 — Diferenciação e moat

**Situação em 07/09:** 🟡 Histórico, feedback individual, dedupe e personalização v1 implementados. ⬜ Padrões de candidatura, confiança e vantagem sustentada ainda sem prova com usuários.

**Prazo:** semana 6 em diante

**Objetivo:** tornar o Radar progressivamente melhor para cada usuário e mais difícil de copiar.

O diferencial defensável não será Gemini, Telegram ou coleta de vagas isoladamente. Será:

- histórico de preferências reais;
- feedback sobre vagas específicas;
- padrões que antecedem candidaturas;
- personalização acumulada;
- confiança nas explicações;
- cobertura e deduplicação comprovadas;
- dados sobre quais oportunidades geram ação.

A intenção original era aguardar volume suficiente. A decisão posterior introduziu regras
limitadas de personalização v1; medir seu efeito antes de ampliar essa influência.

## 10. Estratégia inicial de distribuição

**Situação em 07/09:** ⬜ Testes comparativos de canais, atribuição de aquisição por canal e CAC não concluídos. O campo de origem de clique do frontend não substitui atribuição de campanha.

A distribuição só deve ser ampliada depois de corrigidos os vazamentos de cadastro e ativação
operacional.
Usando o framework Bullseye, o Radar deve concentrar o teste em até três canais:

1. grupos e turmas da própria universidade;
2. comunidades estudantis de tecnologia em Telegram, WhatsApp ou Discord;
3. coordenações de curso, centros acadêmicos e programas de empregabilidade.

Cada canal deve receber identificação de origem para comparar:

- visitantes;
- cadastros;
- ativações;
- vagas úteis;
- candidaturas;
- custo de aquisição, quando existir.

O canal não deve ser avaliado apenas pelo volume de cadastros, mas pela qualidade e retenção dos
usuários que traz ([referência RCD](https://x.com/richardrx/status/2036035304868434115)).

## 11. O que não construir agora

**Situação em 07/09:** ➖ Exclusões de escopo, não tarefas atrasadas. Jooble foi implementado como opção após sondagem de cobertura, mas continua desligado por padrão.

Pelo filtro **Swiss Knife**, ficam fora do roadmap imediato:

- dashboard completo;
- criador de currículo;
- candidatura automática;
- feed de conteúdo;
- cursos ou trilhas de estudo;
- tendências de mercado;
- novos modelos de IA sem evidência de problema;
- novas fontes antes de comprovar insuficiência das atuais;
- sistema de indicação antes de existir retenção;
- três ou mais planos de preço.

Cada funcionalidade nova deve responder:

1. Encurta o TTV?
2. Aumenta ativação operacional ou de produto?
3. Melhora a qualidade medida das vagas?
4. Aumenta retenção ou receita?
5. Qual custo permanente adiciona?

Se não passar por esses critérios, não entra no produto
([referência RCD](https://x.com/richardrx/status/2059236567533650119)).

## 12. Backlog priorizado

| Prioridade | Entrega | Situação em 07/09 |
|---|---|---|
| P0 | Validação da etapa 3 | ✅ Implementada |
| P0 | Alinhar promessa e entrega | 🟡 Revisão pública/legal pendente |
| P0 | Fonte, data, localização e modalidade | ✅ Implementadas |
| P0 | Funil até ativação operacional | ✅ Emissores e contagens; teste público pendente |
| P0 | Primeira entrega após vínculo | ✅ Implementada, com janela do diário |
| P1 | Abertura, utilidade e candidatura | 🟡 Duas primeiras prontas; candidatura fora da captura |
| P1 | Editar, pausar e excluir perfil | ✅ Implementado |
| P1 | Feedback no Telegram | ✅ Seis opções; sem candidatura |
| P1 | Token de uso único | ✅ Implementado |
| P1 | Piloto e prova social | ⬜ Não concluídos |
| P2 | Pagamento e modelo comercial | ⬜ Não testados |
| P2 | Personalização por feedback | 🟡 V1 implementada; eficácia não validada |
| P3 | Novas fontes e expansão | 🟡 Jooble opcional pronto; demais expansões não implementadas |

## 13. Portões de decisão

### Portão A — Funil íntegro

**Situação em 07/09:** 🟡 Ainda não encerrado: falta teste integrado do cadastro público e revisão final; candidatura não faz parte do funil capturado.

Avançar quando:

- não houver falhas bloqueantes no cadastro;
- landing, documentação e mensagem fizerem a mesma promessa;
- o funil puder ser medido de ponta a ponta.

### Portão B — Ativação operacional comprovada

**Situação em 07/09:** 🟡 Teste técnico registrado, mas metas da coorte não medidas.

Avançar quando:

- a maioria dos usuários vinculados receber uma recomendação em até 24 horas;
- o tempo mediano até a primeira entrega estiver dentro do limite aprovado;
- as perdas entre perfil e Telegram forem conhecidas.

### Portão C — Ativação de produto e retenção comprovadas

**Situação em 07/09:** 🟡 Controles e instrumentação prontos; retenção D7 e utilidade da coorte não comprovadas.

Avançar quando:

- houver abertura e interação útil em D7;
- os motivos de rejeição das vagas forem conhecidos;
- o usuário conseguir editar, pausar e excluir seus dados.

### Portão D — Monetização validada

**Situação em 07/09:** ⬜ Não atingido: sem pagamento validado nem unit economics completos.

Avançar quando:

- o custo por usuário com ativação operacional estiver calculado;
- usuários reais aceitarem um pagamento definido previamente;
- o modelo escolhido cobrir o custo de atender usuários gratuitos e pagantes.

## 14. Regra de execução

Cada entrega deve incluir:

- hipótese explícita;
- métrica afetada;
- implementação mínima;
- teste automatizado proporcional ao risco;
- verificação manual de ponta a ponta;
- evento de produto correspondente;
- atualização da documentação;
- decisão de manter, ajustar ou remover com base no resultado.

O objetivo não é redesenhar o Radar do zero. É corrigir os vazamentos existentes, medir o efeito
e ampliar o produto somente quando o comportamento dos usuários justificar o próximo investimento.
