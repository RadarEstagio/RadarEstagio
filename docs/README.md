# Documentação do Radar de Estágio

Revisão de 07/09/2026. Este índice define o papel de cada documento. Implementação no código,
publicação e validação com usuários são estados diferentes; nenhum documento deve tratá-los
como equivalentes.

## Por onde começar

- **O que o produto faz:** [Funcionalidades](funcionalidades.md), para usuários e desenvolvedores.
- **O que falta concluir:** [Plano geral](plano-geral.md).
- **Como publicar e testar:** [Guia de publicação e piloto](guia-publicacao-e-piloto.md).
- **Como contribuir:** [README do projeto](../README.md), [arquitetura](arquitetura.md) e
  [contrato do frontend](contrato-front.md).
- **Como interpretar resultados:** [Métricas](metricas.md).

## Revisão: o que faz sentido manter

| Documento | Decisão | Papel e limite |
|---|---|---|
| `funcionalidades.md` | Novo, manter atualizado | Catálogo do que existe, dependências e limitações; não duplica o checklist de deploy |
| `plano-geral.md` | Manter | Único acompanhamento geral das entregas e pendências |
| `guia-publicacao-e-piloto.md` | Manter | Procedimentos e evidências datadas de publicação e validação |
| `arquitetura.md` | Manter e atualizar quando mudar estrutura | Camadas e decisões técnicas; não usar como status de produção |
| `contrato-front.md` | Manter; corrigido nesta revisão | Auth, perfil, RPCs e limites de escrita; exemplo antigo de insert removido |
| `metricas.md` | Manter | Definições, denominadores, deduplicação e limites históricos |
| `termos-de-uso.md` | Manter em revisão | Texto para revisão; sincronizar com `web/termos.html` antes de publicar |
| `politica-de-privacidade.md` | Manter em revisão | Texto para revisão; sincronizar com `web/privacidade.html` antes de publicar |
| `revisao-cadastro-e-privacidade.md` | Manter até concluir revisão | Checklist de responsáveis e promessas; depois registrar conclusão, sem virar outro backlog |
| `plano-cadastro-e-privacidade.md` | Manter como decisões da frente | Explica consentimento, exclusão e escolhas; execução pertence ao plano geral e ao guia |
| `passos-realizados.md` | Preservar como histórico | Relato dos passos iniciais; números e pendências retratam a época, não o estado atual |
| `proposta.md` | Preservar como proposta original | Contexto acadêmico e intenção; custos, stack e roadmap originais não são contrato vigente |
| `plano-mvp.md` | Preservar como histórico | Plano da Fase 1 concluída; não executar novamente |
| `pre-prd.md` | Preservar como análise de 02/09 | Hipóteses e viabilidade daquela revisão; não manter um segundo catálogo atual |
| `plano-melhorias-rcd.md` | Preservar como estratégia | Hipóteses, critérios e portões; não transformar toda sugestão em requisito aprovado |
| `auditoria-rcd.md` | Preservar como diagnóstico datado | Evidência dos achados e do viés de ranking; sprints antigos não substituem o plano geral |
| `apresentacao.md` | Preservar como roteiro datado | Preparação de apresentação; revisar afirmações e evidências antes de usar novamente |

Não faz mais sentido manter proposta, pré-PRD, auditoria e dois planos de execução como
fontes concorrentes de status. Eles continuam úteis para explicar decisões. Nesta revisão,
foram sinalizados nos próprios arquivos, sem apagar conteúdo nem quebrar links existentes.

## Correções e pendências documentais

- Contrato do frontend atualizado: cadastro validado pelo banco após confirmação, RPC para
  completar cadastro, consentimento e controles de conta já implementados.
- Arquitetura e instruções do agente corrigidas nos pontos que ainda atribuíam a nota à IA,
  omitiam callbacks de feedback ou prometiam custo zero para toda primeira entrega.
- Catálogo distingue Jooble opcional, CAPTCHA dependente de configuração e ausência de
  feedback persistente no modo local.
- Estado externo não foi consultado novamente nesta revisão. As evidências de 05–06/09
  permanecem datadas no guia; publicação da landing ainda precisa ser confirmada pela equipe.
- Textos legais não foram aprovados nem tiveram vigência alterada. A revisão dos responsáveis
  continua no documento próprio.

## Como manter

Ao adicionar ou remover uma função, atualize o catálogo e o contrato afetado. Ao publicar ou
validar algo, registre data e resultado no guia e ajuste a pendência no plano geral. Registre
hipóteses como hipóteses e medições como medições, sem transformar um teste isolado em garantia.
