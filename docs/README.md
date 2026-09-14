# Documentação do Radar de Estágio

Consolidada em 09/09/2026. Implementação, publicação e validação com usuários são estados
diferentes. Esta revisão reorganizou registros locais; não consultou serviços externos.

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
- [Termos](termos-de-uso.md) e [Política de Privacidade](politica-de-privacidade.md): rascunhos
  para revisão; sincronizar com HTML e versão aceita antes da vigência.
- [Cobertura](cobertura-estagios.md), [aquisição e prova](aquisicao-e-prova.md),
  [custos](custos-operacao.md) e [hipótese comercial](hipotese-comercial.md): procedimentos e
  decisões externas ainda abertos, com dados ausentes explicitados.

## Históricos retirados

O plano de expansão, as fichas e o registro de execução (`execucao-expansao/`), a auditoria
adversarial de 08/09 e o `web/README.md` saíram em 13/09/2026, depois de consolidados nos
documentos acima. Continuam no histórico do Git. A01–A06 estão resumidos na arquitetura.

## Como manter

Ao mudar uma função, atualizar o catálogo e o contrato afetado. Ao publicar ou validar,
registrar data, versão e resultado no guia e ajustar o estado no plano geral. Decisões de
cálculo ficam em métricas; justificativas técnicas na arquitetura. Não duplicar o backlog.

O piloto permanece informal por decisão do Igor em 07/09: entrevistas, coorte mínima e D7
não são condições para divulgar. A conferência operacional e a revisão dos textos estão no
plano geral. Hipótese não vira medição, teste local não vira deploy e histórico não vira
instrução para reaplicar uma entrega.
