# Documentação do Radar de Estágio

Revisada em 13/09/2026 contra o código da `main` e o Supabase. Implementação, publicação e
validação com usuários são estados diferentes.

## Por onde começar

- [Funcionalidades](funcionalidades.md): capacidades implementadas, dependências e limitações.
- [Plano geral](plano-geral.md): acompanhamento único de pendências e decisões da equipe.
- [Guia de publicação e piloto](guia-publicacao-e-piloto.md): configuração, evidências datadas,
  ordem de publicação, reversão e roteiro de validação.
- [README do projeto](../README.md): instalação, execução e desenvolvimento do frontend.
- [Arquitetura](arquitetura.md): camadas, justificativas técnicas, correções da auditoria e riscos.
- [Decisões do motor](decisoes-do-motor.md): por que cada regra de coleta, pré-filtro, pontuação
  e mensagem existe, com as medições que a sustentaram.
- [Contrato frontend](contrato-front.md): cadastro, Auth, RPCs, privacidade e formação acadêmica.
- [Métricas](metricas.md): eventos, cálculos, denominadores e limites de interpretação.
- [Pré-PRD](pre-prd.md): definição, hipóteses, evidências e viabilidade para a disciplina.
- [Auditorias](auditorias/): revisões datadas com achados numerados; o que virou pendência está
  no plano geral, e o que virou regra, nas decisões do motor e no `CLAUDE.md`.
- [Termos](../web/termos.html) e [Política de Privacidade](../web/privacidade.html): rascunhos
  para revisão, sem vigência; a versão aceita pelo cadastro é `VERSAO_DOS_TERMOS`.
- [Cobertura](cobertura-estagios.md), [aquisição e prova](aquisicao-e-prova.md),
  [custos](custos-operacao.md) e [hipótese comercial](hipotese-comercial.md): procedimentos e
  decisões externas ainda abertos, com dados ausentes explicitados.

## Históricos retirados

O plano de expansão, as fichas e o registro de execução (`execucao-expansao/`), a auditoria
adversarial de 08/09 e o `web/README.md` saíram em 13/09/2026, depois de consolidados nos
documentos acima. Continuam no histórico do Git. A01–A06 estão resumidos na arquitetura.

## Como manter

Cada assunto tem um documento dono. Os demais citam o dono por link em vez de repetir o fato,
porque cópia de estado diverge: foi o que tornou esta revisão necessária.

| Assunto | Documento dono |
|---|---|
| Pendências e decisões da equipe | [Plano geral](plano-geral.md) |
| O que o produto faz e seus limites | [Funcionalidades](funcionalidades.md) |
| Contrato entre site e banco | [Contrato frontend](contrato-front.md) |
| Configuração, publicação e evidências datadas | [Guia de publicação](guia-publicacao-e-piloto.md) |
| Camadas e decisões técnicas | [Arquitetura](arquitetura.md) |
| Por que cada regra do motor existe | [Decisões do motor](decisoes-do-motor.md) |
| Definição e cálculo das métricas | [Métricas](metricas.md) |
| Vocabulário do produto | [CONTEXT.md](../CONTEXT.md) |
| Regras de contribuição e fatos operacionais | [CLAUDE.md](../CLAUDE.md) |
| Achados de revisão | [Auditorias](auditorias/), datadas e não atualizadas depois |
| Registro para a disciplina | [Pré-PRD](pre-prd.md), retrato de 08/09 |

Ao mudar uma função, atualizar o catálogo e o contrato afetado. Ao publicar ou validar,
registrar data e resultado no guia e ajustar o estado no plano geral.

O piloto permanece informal por decisão do Igor em 07/09: entrevistas, coorte mínima e D7
não são condições para divulgar. A conferência operacional e a revisão dos textos estão no
plano geral. Hipótese não vira medição, teste local não vira deploy e histórico não vira
instrução para reaplicar uma entrega.
