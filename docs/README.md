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

Os documentos antigos foram removidos em 07/09/2026. As decisões de privacidade ficam no
contrato frontend, a revisão dos responsáveis no guia e o viés do ranking na arquitetura.
O histórico permanece no Git.

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
  continua na seção 2 do guia de publicação.

O plano formal de piloto foi retirado em 07/09 por decisão do Igor. A checklist simples antes
de divulgar está no plano geral; metas, entrevistas e D7 não são obrigações atuais.

## Como manter

Ao adicionar ou remover uma função, atualize o catálogo e o contrato afetado. Ao publicar ou
validar algo, registre data e resultado no guia e ajuste a pendência no plano geral. Registre
hipóteses como hipóteses e medições como medições, sem transformar um teste isolado em garantia.
