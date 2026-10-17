# Frentes externas: cobertura, aquisição, custos e oferta

As quatro frentes que dependem de dado ou decisão de fora do código, preparadas em 08/09/2026
(E02 a E05) e reunidas aqui em 16/10/2026. Nenhuma tem medição externa até agora: campo
desconhecido fica "não medido", nunca zero. O estado de cada uma está no
[plano geral](plano-geral.md#4-pendências-externas); a decisão D01, sobre formação acadêmica, fica
no [contrato frontend](contrato-front.md#elegibilidade-acadêmica--decisão-d01-em-aberto).

## Termos de uso das fontes (12/09/2026)

Leitura dos termos no texto original, movida do `CLAUDE.md` em 17/10/2026, que guarda só as
regras. As medições da cota, da coleta resiliente e do enriquecimento estão nas
[decisões do motor](decisoes-do-motor.md).

- **Adzuna, uso 1.** Os termos permitem "Publishing Adzuna ad listings" sem prazo. O teste de
  14 dias e a proibição de agregação ("vacancy counts, average salaries") estão no parágrafo de
  "Any other use". O Radar publica anúncios com link para a página da Adzuna (o `redirect_url`,
  com o nosso app id), então cai no uso 1. Confirmação por escrito pedida no e-mail à Adzuna.
- **Atribuição em cada anúncio exibido**: "Jobs by Adzuna", com "Jobs" ligado a adzuna.com.br e
  "Adzuna" sendo o logo, também com link, em pelo menos 116×23 px. No Telegram vai o texto com
  os dois links, porque mensagem de texto não tem imagem (aprovação pedida no e-mail). No site
  vai o selo com `web/assets/adzuna-logo.png`, o logo oficial servido pelo site de
  desenvolvedores da Adzuna; no tema escuro ele ganha fundo branco, sem mudar as cores.
- **Limites da Adzuna**: 25 requisições por minuto, 250 por dia, 1.000 por semana e 2.500 por
  mês. `CotaDaAdzuna` segura o ritmo, grava o uso em `uso_das_fontes` (`0020`) e para a coleta
  quando acaba o saldo; a entrega imediata ainda reserva o que o diário vai gastar. Cota zerada
  vira erro de coleta, nunca "nenhuma vaga".
- **Nunca contatar anunciante que veio da Adzuna**: "Any attempt to contact a third party, even
  where they provide listings content, will be considered a breach".
- **Se o acordo acabar**, apagar "all insertion codes and data acquired from Adzuna".
- **Gupy desligada.** Os termos proíbem "aggregate, copy, or duplicate parts of Gupy Recruitment
  and Selection, including expired job opportunities", e o endpoint usado
  (`employability-portal.gupy.io/api/v1/jobs`) é interno. Era 7% dos envios (17 de 252). O
  coletor fica no código para o caso de autorização; sem ela, não religar.
- **Jooble não é saída sem parceria**: a chave gratuita tem "a total lifetime limit of 500
  requests per key" e devolve só um trecho da descrição.
- **LinkedIn** está fora de escopo: bloqueia coleta automatizada.
- **Alternativas medidas.** Greenhouse, Lever e Ashby têm API pública de vagas sem login, mas a
  documentação trata das vagas da própria empresa e não dá licença a terceiros; em 12/09 havia 36
  estágios em 6 empresas brasileiras nesses boards, quase todos em SP e BH. A Adzuna tem programa
  de parceiros ("a sponsored feed of ads for your site… generate more revenue for you"), o
  caminho para receita sem cobrar do estudante.

## E02 · Cobertura de estágios

Mede a oferta observada numa amostra; não mede o mercado inteiro e não transforma ausência de
resposta em ausência de vagas. A coleta é só de leitura, sem envio a estudantes.

### Método

Para cada janela, registrar data, fonte, consulta, curso, cidade, modalidade, paginação e
referência anonimizada do anúncio. Contar separadamente o total recebido, o resultado do
pré-filtro, os anúncios com extração, as avaliações aprovadas e as recomendações elegíveis.
Anúncio sem descrição completa, alias ausente ou erro técnico fica identificado como tal.

| Data | Fonte | Consulta/curso | Cidade | Modalidade | Recebidos | Pré-filtro | Extraídos | Recomendáveis | Descrição completa? | Erro/limite | Caso |
|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| a definir | Adzuna | Administração — financeiro/RH | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Adzuna | Software aplicado a laboratório | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Adzuna | formação desconhecida | a definir | a definir | não medido | não medido | não medido | não medido | não medido | distinguir incompatibilidade de desconhecido | a definir |
| a definir | Adzuna | saúde | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Adzuna | engenharia | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |
| a definir | Adzuna | computação — controle | a definir | a definir | não medido | não medido | não medido | não medido | não medido | acesso de coleta pendente | a definir |

As fixtures `tests/fixtures/adzuna_resposta.json` e `adzuna_detalhe.html` só documentam o
procedimento e não entram em afirmação de cobertura. Linhas reais precisam de janela e paginação
antes de serem somadas.

### Casos de qualidade

| Entrada/caso | Resultado atual a registrar | Resultado esperado | Causa provável/teste sugerido | Estado |
|---|---|---|---|---|
| Administração com vaga financeira/RH | não medido | aceitar quando a área e a descrição forem compatíveis; desconhecido quando faltarem fatos | validar `area_do_curso`, interesses e pré-filtro com fixture anonimizada | pendente de amostra |
| Software aplicado a laboratório | não medido | não descartar só pelo domínio da empresa; avaliar descrição e requisitos | fixture de descrição completa e teste de pré-filtro | pendente de amostra |
| Formação desconhecida | catálogo atual não inventa área | manter como desconhecida ou curso livre, sem sugerir outra formação | registrar alias e decidir D01 separadamente | contrato atual preservado |
| Saúde | não medido | separar exigência profissional de estágio compatível | exemplo público anonimizado e teste de regra | pendente de amostra |
| Engenharia | não medido | não misturar especialidades sem evidência | exemplo público anonimizado e teste de área | pendente de amostra |
| Computação como controle | regressões de domínio já cobertas pelos testes locais | preservar áreas e limites existentes | `tests/test_areas.py`, `tests/test_areas_do_front.py` | coberto localmente |
| Descrição truncada | não medido em fonte real | marcar informação insuficiente, não reprovar como incompatível | comparar detalhe com resultado resumido | pendente de amostra |
| Alias ausente | não medido em fonte real | registrar o termo desconhecido antes de propor catálogo | caso anonimizado e decisão D01 | pendente de amostra |

Os casos A01 a A06, resumidos na
[arquitetura](arquitetura.md#correções-e-limites-preservados-da-auditoria-de-0809), são
regressões já corrigidas e não voltam como mudança de ranking aqui. Defeito novo ganha linha
própria e um teste ligado ao exemplo; não ajustar pesos para uma amostra parecer melhor.

**Próximo passo.** Rodar `uv run python -m radar coletar` numa janela autorizada, guardar só
referências públicas ou anonimizadas e preencher uma linha por consulta. Depois avaliar sem
enviar mensagens e registrar falha de coleta separada de ausência de oferta. Responsável e acesso:
a definir. Conclusão permitida hoje: há fixtures e um método reproduzível; cobertura real,
ausência de mercado e suficiência por área seguem não medidas.

## E03 · Aquisição e prova de utilidade

A promessa usada na divulgação é a da landing: oportunidades de áreas diferentes, perfil de curso,
cidade e modalidade e até sete recomendações explicadas no Telegram durante o piloto.

| Canal | Público acessível | Esforço | Custo | Hipótese de utilidade | Acesso confirmado |
|---|---|---:|---|---|---|
| Colegas e grupos autorizados | estudantes conhecidos e comunidades em que a equipe já participa | baixo | não medido | relato rápido após uma semana mostra se o problema é real | não confirmado |
| Landing pública | pessoas que chegam por link direto ou busca | baixo | não medido | CTA e demonstração explicam a proposta sem depender de conversa | `radarestagio.com` no ar desde 03/10/2026 |
| Comunidades de curso | estudantes de uma formação com contexto comum | médio | não medido | mensagem contextualizada melhora perfil completo e feedback | não confirmado |

**Canal inicial proposto**, sujeito a autorização: colegas ou comunidade já acessível à equipe, o
de menor esforço para observar se uma recomendação serve sem comprar mídia. Não é decisão de
divulgação nem autoriza envio automático. Mensagem para revisão:

> Está procurando estágio? O Radar compara seu curso, cidade, modalidade e interesses com
> as vagas de estágio da Adzuna e envia até sete recomendações explicadas no Telegram.
> Durante o piloto, é gratuito. Você se candidata na fonte da vaga. Veja o exemplo e cadastre
> seu perfil: https://radarestagio.com/?utm_source=nome-do-grupo

Não inserir token de vínculo, token de recomendação nem URL pessoal.

**Atribuição.** Desde a migration `0032` a visita guarda o domínio do referrer e `utm_source`,
`utm_medium` e `utm_campaign`, e `python -m radar metricas` mostra as visitas por origem
([métricas](metricas.md#visitas-por-origem-e-páginas-locais)). Use um `utm_source` por grupo ou
canal, em minúsculas; sem ele a visita é lida pelo domínio do referrer ou como "direto ou
desconhecido". Origem agrupa visitas, não identifica pessoas: não atribua um cadastro a um canal
sem a evidência do próprio cadastro.

| Data | Canal | Mensagem/URL | Expostos | Visitantes atribuíveis | Cadastros conhecidos | Sinal de utilidade | Limitação |
|---|---|---|---|---:|---:|---|---|
| 08/09/2026 | nenhum envio | proposta acima | não medido | não medido | não medido | não medido | falta autorização |

**Autorização de relato.** Antes de publicar qualquer caso, registrar separadamente:

| Campo | Preenchimento |
|---|---|
| Contexto de uso | a definir com a pessoa |
| O que ela usou | perfil, Telegram, recomendação e/ou feedback |
| Sinal observado | evento ou relato, sem converter abertura em contratação |
| Limite do relato | o que não pode ser concluído a partir do caso |
| Texto autorizado | a definir |
| Nome, curso, cidade e imagem | somente com autorização explícita e se necessários |
| Responsável por guardar a autorização | a definir |

Sem relato autorizado, a landing não recebe depoimento nem logotipo de parceiro.

## E04 · Custos da operação

Planilha lógica, não fatura. Ninguém consultou as contas, os preços atuais nem as franquias, e o
repositório não guarda faturas.

| Serviço/atividade | Natureza | Faturado no período | Uso observado ou estimado | Fonte/data | Responsável |
|---|---|---|---|---|---|
| Supabase (banco, Auth, Edge Functions) | fixo/variável | não medido | plano gratuito; banco com 19,3 MB de 500 MB em 08/10 ([decisões do banco](decisoes-do-banco.md#o-resumo-mede-o-tamanho-do-banco-08102026)) | conta do projeto, a consultar | a definir |
| Cloudflare (Workers, Email Routing, Turnstile, domínio) | fixo/variável | não medido | domínio renova em 04/09/2027, pago pelo Igor; Workers sem script | conta do grupo, a consultar | Igor (domínio) |
| GitHub Actions | franquia | não medido | job de até 30 min; de 7,6 a 13,7 min entre 30/08 e 11/09 ([auditoria do agendamento](auditorias/2026-09-10-agendamento-diario.md)) | billing, a consultar | a definir |
| cron-job.org | fixo | não medido | um disparo diário às 07:23 | conta, a consultar | a definir |
| Adzuna | franquia | não medido | até 2.500 requisições por mês, pelos termos | conta/API, a consultar | a definir |
| Gemini | variável | não medido | R$ 0,066 por lote de 10 vagas em raciocínio `low` (11/09); ~R$ 14 em 30 dias por estimativa ([acompanhamento RCD](auditorias/2026-10-05-revenue-centric-design.md)) | billing, a consultar | a definir |
| Telegram | — | não medido | envio pelo bot; tarifa não inferida | termos, a consultar | a definir |
| Resend/SMTP | variável | não medido | confirmação e recuperação | conta, a consultar | a definir |
| Suporte e atendimento | variável | não medido | horas não registradas | registro da equipe, a criar | a definir |

Não somar franquia gratuita como cobrança, não tratar vagas extraídas por ativado como valor
monetário e coletar no mesmo período a diversidade de áreas e cidades, as vagas novas, a duração
do job, as falhas e as reextrações.

**Fórmulas.**

- Custo operacional do período = fixos faturados + variáveis faturados + suporte monetizado
  só quando a taxa por hora for conhecida. "Não medido" não vira zero.
- Perfis atendidos = perfis distintos que receberam ao menos uma recomendação no período.
- Custo por usuário atendido = custo operacional conhecido / perfis atendidos; com denominador
  zero, indisponível. Custos conhecidos ficam separados do total quando faltar serviço ou suporte.

Extração é contada por vaga, não multiplicada por usuário novo. Num cenário futuro, variar vagas
novas, reaproveitamento e perfis atendidos, sem supor uma extração por usuário.

**Próximo passo.** Exportar faturas e uso das contas sem chaves nem tokens, escolher uma janela
comum, registrar horas de suporte e cruzar com o relatório de métricas. CAC, LTV e margem seguem
não medidos; não há base para preço ou compra de plano.

## E05 · Hipótese comercial

Organiza uma decisão futura; não implementa checkout, cobrança, paywall ou preço e não muda o
piloto gratuito. O benefício de referência é o que a landing promete: até sete recomendações
explicadas no Telegram, com candidatura feita na fonte da vaga.

| Opção | Pagador hipotético | Benefício incluído | Duração | Previsibilidade | Relação com busca | Custo/margem |
|---|---|---|---|---|---|---|
| Assinatura | estudante ou instituição | recomendações dentro do limite vigente e controles da conta | recorrente, a decidir | receita previsível, compromisso contínuo | pode exceder uma busca específica | não medido; depende de E02/E04 |
| Acesso por período de busca | estudante | uso durante uma janela definida, sem prometer contratação | uma janela, a definir | combina com procura temporária | mais próximo do momento real de busca | não medido; depende de E02/E04 |

Estudante era a hipótese inicial de pagador; instituição patrocinadora é outra hipótese e não
deve ser assumida como novo público. Nenhuma opção foi escolhida.

### O que limita cobrar do estudante

- **A Lei do Estágio não veda cobrar do nosso usuário.** O art. 5º da Lei 11.788/2008 trata de
  agentes de integração, a quem instituições de ensino e partes cedentes recorrem "mediante
  condições acordadas em instrumento jurídico apropriado". O §1º lista os serviços desses
  agentes, entre eles "identificar oportunidades de estágio" e "cadastrar os estudantes", e o
  §2º veda a cobrança dos estudantes "a título de remuneração pelos serviços referidos nos
  incisos deste artigo" — os serviços deles. O Radar não é um agente de integração: não tem
  instrumento com instituição nem com parte cedente, não entra no termo de compromisso e não
  cadastra ninguém para uma empresa. A leitura anterior (auditoria de 10/09/2026, RCD-02) tirava
  a vedação de o Radar executar dois dos cinco serviços da lista, mas ela acompanha a figura, não
  a atividade isolada. Correção de 29/09/2026; a trava "nenhuma oferta ao estudante antes de
  consulta jurídica" nasceu dessa leitura, e mantê-la é decisão da equipe.
- **O que restringe é o mercado.** CIEE e Nube são gratuitos para o estudante porque quem paga
  são as empresas, e LinkedIn, Indeed e a própria Adzuna dão alerta de vaga de graça. O estudante
  compara o preço com gratuito, não com concorrente pago, e nenhum parecer jurídico muda isso.
- **O caminho por instituição é o que aproxima o Radar da figura legal.** Convênio para
  identificar vagas e cadastrar alunos é, na letra do art. 5º, o que um agente de integração faz.
  Nele o §2º passa a valer — não se cobra do estudante — e com ele o §3º, que responsabiliza
  civilmente quem indica estágio incompatível com o curso: a regra de curso do motor vira
  argumento de venda e risco ao mesmo tempo.
- **Pagadores ainda não consultados:** instituições de ensino (coordenação ou núcleo de
  estágios), empresas que recrutam estagiários e o programa de parceiros da Adzuna, que oferece
  "a sponsored feed of ads for your site", registrado em 12/09 como caminho de receita sem
  cobrar do estudante.

### Decisões pendentes

| Campo | Estado |
|---|---|
| Oferta escolhida | decisão da equipe |
| Pagador e elegibilidade | decisão da equipe |
| Preço e moeda | decisão da equipe; não medido |
| Duração e renovação | decisão da equipe |
| Cancelamento e reembolso | decisão da equipe; revisar textos legais |
| Participantes atuais do piloto | decisão da equipe; preservar piloto gratuito até decidir |
| Forma de obter aceite | decisão da equipe |
| Provedor de cobrança | não escolhido; tarefa separada |

**Teste futuro.** Depois de E02, E04 e uma decisão registrada, comparar uma oferta apresentada a
um grupo elegível com o piloto preservado. Registrar elegíveis expostos, oferta apresentada,
compradores com pagamento recebido, receita líquida, uso posterior, cancelamentos, custos
associados e margem. Interesse declarado não é comprador; clique ou resposta não é pagamento. Não
usar perda fictícia, paywall surpresa, recompensa ou retenção de dados para pressionar a decisão.
