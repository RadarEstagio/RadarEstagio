# Documentação do Radar de Estágio

Cada assunto tem um documento dono. Os outros linkam o dono em vez de repetir o fato, porque
cópia de estado diverge. Implementado, publicado e validado com estudantes são estados diferentes,
e cada documento diz de qual está falando.

## Por onde começar

- [PIT](pit/pit-do-grupo.md): o projeto em uma leitura, entregue na disciplina e medido em 28 e
  30/09/2026, com a [apresentação](pit/apresentacao.html), o
  [pptx](pit/radar-de-estagio-pit.pptx) e as [telas](pit/telas/).
- [Funcionalidades](funcionalidades.md): o que o produto faz hoje, para quem usa e para quem opera.
- [Plano geral](plano-geral.md): pendências, decisões e o estado dos achados das auditorias.
- [Desenvolvimento local](desenvolvimento.md): instalar, configurar, rodar a CLI e testar.

## Por assunto

| Assunto | Documento dono |
|---|---|
| O que o produto faz e seus limites | [Funcionalidades](funcionalidades.md) |
| Pendências e decisões da equipe | [Plano geral](plano-geral.md) |
| Camadas e decisões técnicas | [Arquitetura](arquitetura.md) |
| Por que cada regra de coleta, pré-filtro, extração, nota e mensagem existe | [Decisões do motor](decisoes-do-motor.md) |
| Por que o schema, as migrations, o webhook e o resumo de operação são assim | [Decisões do banco](decisoes-do-banco.md) |
| Contrato entre o site e o banco, e os pós-mortems do site | [Contrato frontend](contrato-front.md) |
| Eventos, denominadores e leitura do relatório | [Métricas](metricas.md) |
| Instalação, comandos, testes e scripts | [Desenvolvimento local](desenvolvimento.md) |
| Configuração dos serviços e evidências datadas | [Guia de publicação e piloto](guia-publicacao-e-piloto.md) |
| Cobertura, aquisição, custos e oferta | [Frentes externas](frentes-externas.md) |
| Textos legais em vigor (versão `2026-10-08`) | [Termos de uso](termos-de-uso.md) e [Política de privacidade](politica-de-privacidade.md), iguais aos HTML de `web/` |
| Vocabulário do produto | [CONTEXT.md](../CONTEXT.md) |
| Regras de contribuição e fatos operacionais | [CLAUDE.md](../CLAUDE.md) |
| Entrega da disciplina | [PIT](pit/pit-do-grupo.md) |

## Auditorias

Revisões datadas, com achados numerados. Não são atualizadas depois: o estado de cada achado está
no plano geral, e o que virou regra, nas decisões e no `CLAUDE.md`.

- [Agendamento diário](auditorias/2026-09-10-agendamento-diario.md) (10/09/2026): G01 a G10.
- [Revenue-Centric Design](auditorias/2026-09-10-revenue-centric-design.md) (10/09/2026): RCD-01
  a RCD-16.
- [Acompanhamento do Revenue-Centric Design](auditorias/2026-10-05-revenue-centric-design.md)
  (05/10/2026).

## Como manter

- Ao mudar uma função, atualizar o catálogo e o contrato afetado.
- Ao publicar ou conferir algo no ambiente real, registrar data e comando no guia e ajustar o
  item no plano geral.
- Decisão nova vai para as decisões do motor, as do banco ou o contrato, com a data e a medição
  que a sustentam.
- Mudança nos Termos ou na Política troca a versão nos quatro arquivos e em `VERSAO_DOS_TERMOS`,
  como diz o guia.
- Documento que só retrata o estado de um dia não entra: corrige-se o dono. O que saiu do
  repositório continua no histórico do Git.

O piloto permanece informal por decisão do Igor em 07/09: entrevistas, coorte mínima e D7 não são
condições para divulgar. Hipótese não vira medição, teste local não vira deploy e histórico não
vira instrução para reaplicar uma entrega.
