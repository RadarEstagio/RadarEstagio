# Auditoria Revenue-Centric Design

Data: 10/09/2026. Base: `main` em `11f32df`; as citações de linha foram reconferidas contra
`0750eba` em 11/09, depois do botão de tema, que deslocou `web/index.html` e `web/assets/app.js`.

Esta auditoria aplica a skill Revenue-Centric Design (101 princípios de Richard, @richardrx,
distribuídos em dez referências) ao Radar como produto: aquisição, ativação, retenção,
monetização e diferenciação. Não é revisão de código. Foi pedida para ser crítica, e é.

## Como foi feita

- **Skill:** `SKILL.md` e as dez referências. Nesta máquina o link
  `.claude/skills/revenue-centric-design` aponta para `.agents/skills/revenue-centric-design`,
  que não existe, e a skill foi lida de uma cópia local em outro projeto. O problema é local, não
  do repositório: `.agents/` e `.claude/skills/` são ignorados pelo Git e não têm arquivo
  versionado algum, então quem clona não recebe skill nenhuma, embora
  `plano-expansao-revenue-centric.md` cite os mecanismos dela.
- **Produto:** `web/index.html`, `web/assets/app.js` (etapas, progresso e estados da conta),
  `radar/notification/formatador.py` (a mensagem), `supabase/functions/telegram-webhook/`
  (respostas do bot e feedback) e o workflow diário.
- **Documentos:** pré-PRD, plano geral, funcionalidades, métricas, hipótese comercial, custos,
  aquisição, cobertura e o plano de expansão anterior.
- **Dados:** `python -m radar metricas` e consultas agregadas, somente de leitura, ao banco de
  produção na tarde de 10/09. Nenhum dado pessoal foi extraído; os perfis aparecem numerados
  por data de criação.
- **Histórico:** contagem de commits por dia, tipo e escopo.
- **Fora do alcance:** entrevistas, gravação de sessões, faturas e contas externas.

**Limite que muda a leitura:** o piloto externo começou, na prática, hoje. Quatro dos seis perfis
foram criados em 10/09. Nenhum número aqui mede retenção. Eles mostram se o sistema está
desenhado para gerar valor, aprender com quem usa e, um dia, gerar receita, e mostram onde o
esforço do grupo foi parar. A crítica é sobre isso.

## 1. Veredito

**O motor é de produto maduro; a prova de valor é zero.** De 28/08 a 10/09 o Radar entregou 196
recomendações. Vieram 12 aberturas, nenhuma resposta de feedback, nenhuma candidatura registrada
e utilidade semanal de 0 em 4. Não há pagador definido, preço nem canal de aquisição medido. O
pagador que os documentos presumem, o estudante, esbarra na Lei do Estágio e no modo como esse
mercado já funciona no Brasil.

Quatro problemas decidem o futuro do projeto, nesta ordem:

1. **O ciclo de aprendizado está travado.** A nota só pode ser recalibrada com recusa real, a
   North Star depende de "essa serviu" ou de candidatura, e o fluxo de feedback produziu 0
   respostas em 196 envios, inclusive nas 147 recomendações que o próprio grupo recebeu.
2. **Não há caminho de receita que caiba no mercado.** Cobrar do estudante é zona cinzenta
   jurídica e contraria o padrão do setor; ninguém procurou ainda quem tem dinheiro e dor.
3. **O esforço está fora do gargalo.** Foram 668 commits em 17 dias, 338 nos últimos três, a
   maior parte em motor de matching e documentação, enquanto a distribuição segue sem medição e o
   sinal de valor está zerado.
4. **Nada retém.** O produto é um fluxo de notificações sem ativo acumulado, para um trabalho que
   acaba quando dá certo.

A causa comum é de fase. Pela skill, a alavanca do design muda com o estágio do produto: no MVP o
trabalho é encurtar o caminho até o valor e recusar funcionalidades "óbvias"; na fase de
sobrevivência, consertar a ativação, porque a primeira semana vale mais que o roadmap inteiro. O
Radar opera como produto em escala (juiz automático, métricas com medianas, 12 áreas, regiões do
IBGE, exclusão com carência e cancelamento) sem ter provado valor para um único estudante
externo. A decisão de 07/09 de retirar as cinco entrevistas e o D7 é a que mais contraria a
skill: tirou o único instrumento que funciona com seis usuários e manteve a máquina de medição,
que só funciona com centenas.

O que está bom, e deve ser preservado, está na seção 6. O principal: a mediana entre a criação
do perfil e a primeira lista é de 1,4 minuto, patamar que o benchmark citado pela skill atribui
aos melhores produtos.

## 2. O que os dados mostram

### Funil de 30 dias

Contagem por identidade na primeira aparição de cada evento, como no relatório `metricas`.

| Etapa | Identidades | Passagem |
|---|---:|---:|
| Visitou a landing | 77 | — |
| Abriu o cadastro | 11 | 14% |
| Concluiu a etapa de curso e período | 6 | 55% |
| Criou a conta e confirmou o e-mail | 6 | 100% |
| Vinculou o Telegram | 4 | 67% |
| Recebeu a primeira recomendação | 4 | 100% |
| Abriu ao menos uma vaga | 3 | 75% |
| Marcou vaga útil ou candidatura | 0 | 0% |

Os dois primeiros números não descrevem tráfego de estudante (RCD-04): nenhuma visita guarda
origem, 18 dos 107 eventos de visita (17%) vêm de páginas de ambiente local e as contas da equipe
não são separadas. Mesmo depois de limpo, é tráfego quente de colegas. A skill trata conversão
medida em público quente como ficção até ser posta à prova em tráfego frio.

### Entregas, de 28/08 a 10/09

| Indicador | Valor |
|---|---|
| Recomendações entregues | 196 |
| Vagas abertas (pares distintos) | 12 (6,1%) |
| Respostas de feedback | 0; nenhum `vaga_util`, `vaga_irrelevante` ou `candidatura_iniciada` na história do banco |
| Nota das entregues, pela regra atual | mediana 72; quartis 65 e 80; 31 abaixo de 60 (16%) |
| Nota média, abertas × não abertas | 73,3 × 69,9 |
| Fonte | Adzuna 184 (94%), Gupy 12 |
| Sem modalidade na fonte nem na extração, desde 05/09 | 66 de 104 (63%) |
| Idade da vaga no envio | mediana 20 h; 3º quartil 53 h; 53 com mais de 48 h (27%) |
| Da criação do perfil à primeira entrega | mediana 1,4 min (4 perfis) |
| Da criação do perfil à primeira abertura | mediana 11,6 h (3 perfis) |
| Hora dos cliques em vaga | 13 de 19 na faixa das 8h ou das 12h |

A nota vem de `avaliacoes`, regravada a cada execução com a regra vigente. É a nota que a regra
de hoje dá à vaga enviada, não necessariamente a que apareceu na mensagem.

### Abertura por posição no dia

| Posição, pela nota | Enviadas | Abertas | Taxa |
|---|---:|---:|---:|
| 1ª | 37 | 5 | 13,5% |
| 2ª a 7ª | 119 | 7 | 5,9% |
| 8ª em diante | 40 | 0 | 0% |

As 40 entregas além da sétima posição vêm de mais de uma execução para o mesmo perfil no mesmo
dia (testes e reexecuções). A amostra é pequena: o padrão serve de hipótese, não de conclusão.

### Por perfil

| Perfil | Criado em | Dias com envio | Envios | Vagas abertas |
|---|---|---:|---:|---:|
| P1 (grupo) | 28/08 | 14 | 147 | 7 |
| P2 (grupo) | 08/09 | 4 | 35 | 4 |
| P3 | 10/09 | 0 | 0 | 0 |
| P4 | 10/09 | 0 | 0 | 0 |
| P5 | 10/09 | 1 | 7 | 1 |
| P6 | 10/09 | 1 | 7 | 0 |

P1 e P2 são os perfis do grupo, segundo o pré-PRD de 08/09. O usuário mais motivado que existe,
quem constrói o produto, abriu 7 de 147 recomendações (4,8%) em duas semanas e não respondeu
nenhuma. P3 e P4 criaram conta hoje e não vincularam o Telegram. Dois dos quatro ativados são de
fora de computação.

## 3. Fase do produto e onde o esforço foi parar

A skill separa cinco fases e o que o design deve fazer em cada uma: encurtar (MVP), ativar
(sobrevivência), converter (tração), aprofundar (encaixe produto-mercado) e sistematizar
(escala). "Polir a interface de um produto que ninguém quer é o erro mais bonito que existe." E,
para diagnosticar o gargalo: se ninguém entra, é distribuição; se entram, não pagam e saem, é
design.

O Radar está entre o MVP e a sobrevivência. Em 08/09, o pré-PRD registrava 30 sessões na landing
em 30 dias e nenhum estudante externo cadastrado; a semana de 07/09 já soma 79 sessões, parte
delas da equipe. Sessão e identidade são medidas diferentes: as 79 sessões de uma semana não
contradizem as 77 identidades de 30 dias do funil, porque a mesma pessoa abre a página várias
vezes. O gargalo era distribuição. O trabalho foi para outro lugar:

- **Volume:** 668 commits de 25/08 a 10/09; 338 entre 08 e 10/09; 181 do tipo `docs` (27% do
  total). São 6.394 linhas de Python em `radar/`, 9.694 de testes, 4.944 de documentação em
  `docs/` e um `CLAUDE.md` de 862 linhas (66 KB), que toda sessão de agente carrega inteiro.
- **Direção:** nas últimas 72 horas, as categorias mais frequentes foram documentação (52
  commits) e correções do motor (37, somando matching, áreas, pré-filtro, filtering, domínio e
  avaliação). As regras novas tratam "Ciências Jurídicas" no plural, "Pessoas Jurídicas" com
  espaço duplo, apóstrofo curvo em nome de cidade. Cada uma tem teste, e quase todas vieram de
  auditoria interna, perfil sintético ou do juiz automático, não de reclamação de usuário.
- **Construído antes do uso:** o juiz automático (09/09), cujo gabarito humano de 20 entregas
  segue sem nenhum rótulo; o motivo da pausa (R01–R03), que o próprio pré-PRD recomendava "adiar
  até haver pausas reais" (houve um evento de pausa na história do banco); exclusão com carência
  de 60 dias e cancelamento; exportação em JSON; 12 áreas, 45 subáreas e 105 cursos antes do
  primeiro estudante externo de computação; regiões imediatas do IBGE; o coletor da Jooble,
  desligado.
- **Não construído:** a visita nunca guardou origem; o teste humano do feedback em produção
  nunca foi confirmado (`docs/metricas.md`: "falta validar respostas positivas e negativas
  reais"); domínio, Turnstile e textos legais seguem pendentes.
- **Iteração visual sem volume:** 36 commits `style` e 17 `copy`, boa parte na landing, para uma
  página com 77 identidades distintas em 30 dias, parte delas da equipe. Sem volume, a skill manda decidir por conversa,
  não por iteração: "cinco boas entrevistas valem mais que um teste A/B sem amostra".

A skill tem uma frase para o padrão: "velocidade de construção sem obsessão por ativação é só um
jeito mais eficiente de chegar ao churn". O prompt do plano de expansão ("Não pare na primeira
tarefa nem somente em planejamento") transformou a própria skill numa fila de funcionalidades.
Os IDs de dentro do produto (O00–R03) foram todos implementados; as três frentes que tratam de
receita (E03 canal, E04 custos, E05 oferta) seguem "preparado, falta evidência externa". A skill
foi aplicada como backlog, não como teste de receita.

Decisões registradas que esta auditoria contesta:

1. **Retirar as cinco entrevistas e o D7 (07/09).** Com seis usuários, conversa é o único
   instrumento que produz sinal. O D7 é o que a skill põe no lugar de "concluiu o cadastro".
2. **Expandir para 12 áreas (08/09) antes de validar uma.** Ver RCD-10.
3. **"Histórico de vagas para o estudante: adiar até H5."** É a principal alavanca de retenção e
   uma das formas de medir H5 (RCD-06).
4. **Monetização como "hipótese futura" com o estudante como pagador.** Ver RCD-02.

A regra "não ajustar peso sem `vaga_irrelevante` real" está certa e deve continuar. O erro é não
ter desenhado o mecanismo que gera esse sinal (RCD-01).

**Proposta:** congelar ajuste de regra do motor sem caso vindo de usuário real (recusa,
mensagem ou conversa) até o ciclo de feedback funcionar. Falha de entrega, privacidade e
segurança ficam fora do congelamento.

## 4. Placar dos nove princípios

| # | Princípio | Situação | Por quê |
|---|---|---|---|
| 1 | Neutralidade é omissão | Parcial | A landing dirige para um CTA só; a conta e a mensagem não dizem qual é a próxima ação |
| 2 | Quem fala com todos não convence ninguém | Não atende | 12 áreas, o país inteiro, qualquer período; o hero serve a qualquer estudante |
| 3 | Valor primeiro, pedido depois | Parcial | Conta no último passo e entrega em 1,4 min; mas o valor só aparece depois de e-mail e Telegram, e a demonstração é fictícia |
| 4 | A promessa tem o tamanho da prova | Não atende | Nenhuma prova externa; nomes de fornecedores no lugar de prova; "vagas que atendem seu perfil" com nota mínima 40 |
| 5 | Igual compete em preço, diferente em categoria | Não atende | 94% das entregas vêm da Adzuna, que tem alerta gratuito; a landing não diz o que o Radar faz e o alerta não faz |
| 6 | O padrão é a decisão tomada pelo usuário | Parcial | Padrões éticos (e-mail desmarcado, habilidade opcional); sete por dia, todo dia, sem alternativa além de pausar |
| 7 | Retenção se constrói | Não atende | Nada se acumula na conta; trabalho episódico sem evento de retorno |
| 8 | Expansão nasce do uso | Ainda não se aplica | Não há limite nem momento de upgrade; o candidato natural seria velocidade, que o lote diário não entrega |
| 9 | Preço é filtro | Não atende | Não há pagador; o presumido tem restrição legal e pouca capacidade de pagar |

## 5. Achados

A severidade segue a escala de quatro níveis da skill para análise heurística:

- **Crítico:** trava aprendizado, conversão ou receita.
- **Grave:** perde usuários ou distorce decisões.
- **Moderado:** atrito ou incoerência que se acumula.
- **Estético:** feio, mas inofensivo.

| ID | Severidade | Achado |
|---|---|---|
| RCD-01 | Crítico | Feedback com 0 respostas em 196 envios trava o aprendizado e zera a North Star |
| RCD-02 | Crítico | Não há pagador viável; cobrar do estudante esbarra na Lei do Estágio |
| RCD-03 | Crítico | Esforço no motor e na documentação, fora do gargalo (seção 3) |
| RCD-04 | Grave | Visita sem origem e métricas misturadas com sessões da equipe |
| RCD-05 | Grave | O valor só aparece depois de três trocas de contexto; a demonstração é fictícia |
| RCD-06 | Grave | A conta é painel de configurações, sem nada acumulado |
| RCD-07 | Grave | Trabalho episódico: o sucesso do usuário é churn |
| RCD-08 | Grave | A promessa é maior que a prova |
| RCD-09 | Grave | O bot responde "use o botão do site" a qualquer mensagem |
| RCD-10 | Grave | ICP difuso: 12 áreas antes de validar uma |
| RCD-11 | Moderado | Nada diferencia o Radar de um alerta gratuito da mesma fonte |
| RCD-12 | Moderado | Mensagem densa; a atenção fica no topo |
| RCD-13 | Moderado | A única alternativa à saída é pausar tudo |
| RCD-14 | Moderado | O progresso começa em 0% e a última etapa diz "Comece pela sua conta" |
| RCD-15 | Moderado | O card de preço "A definir" gera dúvida sem filtrar ninguém |
| RCD-16 | Estético | "Sobre" leva ao CTA final e não há rosto humano na página |

### RCD-01 · Crítico · O feedback não produz sinal e trava o aprendizado

**Princípios:** medir ativação, não cadastro; onboarding como gatilho de comportamento (efeito
Zeigarnik); tratar a interface como dado.

**Evidência.**

- Zero respostas em 196 recomendações e nenhum `vaga_util`, `vaga_irrelevante` ou
  `candidatura_iniciada` na história do banco. P1, perfil do grupo, recebeu 147 recomendações em
  14 dias e não respondeu nenhuma. Se foi para não poluir as métricas, o efeito é o mesmo: não há
  prova de que o fluxo funciona do lado humano.
- A pergunta ("Deixe seu feedback 👇", `radar/notification/formatador.py:33`) fica no fim da
  última parte de uma mensagem longa, depois de o estudante já ter saído pelo link. Responder
  exige dois toques: o número abre outra mensagem
  (`supabase/functions/telegram-webhook/index.ts:159`) com uma opção positiva e cinco negativas
  (`feedback.ts:87-93`). O desenho pede uma taxonomia de reclamação, não uma decisão.
- Candidatura não tem emissor (`docs/metricas.md`), então metade da definição de vaga útil é
  zero por construção.
- A calibração da nota depende de `vaga_irrelevante` real, que este desenho não gera. As
  decisões de regra continuam vindo de auditoria interna e do juiz automático, um modelo
  julgando outro modelo: é a maldição do conhecimento com um passo a mais.

**Impacto.** A utilidade semanal é 0% por construção, não necessariamente por falta de valor. O
projeto não consegue distinguir "o ranking é ruim" de "ninguém responde".

**Recomendação.** Perguntar pelo que a pessoa fez, no dia seguinte, e só sobre as vagas que ela
abriu: "Ontem você abriu *Estágio X — Empresa Y*. E aí?", com três botões: **Me candidatei**,
**Não serviu** e **Ainda vou ver**. "Me candidatei" emite `candidatura_iniciada`, que já está no
catálogo de eventos, e conta como útil; "Não serviu" abre as cinco razões atuais. É uma mensagem
por dia, só para quem abriu, presa a um comportamento real (a abertura) e com um laço aberto que
a pessoa tende a fechar. O sinal para ler em duas semanas é a fração de quem abriu que responde.
Custo: webhook e uma etapa no job, sem IA.

### RCD-02 · Crítico · Não há pagador viável

**Princípios:** preço é filtro; nicho com dor e dinheiro para pagar; cobrar os primeiros dez
usuários; o custo de servir decide se o gratuito funciona.

**Evidência.**

- A Lei 11.788/2008, art. 5º, lista no §1º os serviços dos agentes de integração, entre eles
  "I – identificar oportunidades de estágio" e "V – cadastrar os estudantes". O §2º diz: "É
  vedada a cobrança de qualquer valor dos estudantes, a título de remuneração pelos serviços
  referidos nos incisos deste artigo" (texto conferido no Planalto em 10/09/2026). O Radar não é
  agente de integração formal, porque não tem instrumento com instituição de ensino nem com
  empresa, mas executa dois dos cinco serviços que a lei atribui a eles.
- O mercado segue a lei. Agentes de integração conhecidos, como CIEE e Nube, não cobram do
  estudante e são pagos pelas empresas. LinkedIn, Indeed e a própria Adzuna oferecem alerta de
  vaga gratuito.
- `docs/hipotese-comercial.md` compara assinatura e acesso por período. A assinatura já admite
  "estudante ou instituição" e o texto registra a instituição patrocinadora como outra hipótese,
  mas o estudante é a hipótese inicial, o acesso por período só tem ele como pagador e a lei não
  aparece em lugar nenhum. A landing diz que "o preço sai do que os primeiros usuários disserem
  que vale a pena" (`web/index.html:194`).
- Como ICP pagador, o estudante falha no terceiro filtro da skill (dinheiro para pagar o ticket)
  e o trabalho que ele contrata é episódico (RCD-07).
- Em compensação, servir um estudante custa pouco: a extração é por vaga (343 vagas extraídas
  para 4 ativados), o Actions é gratuito em repositório público e nenhuma fatura está registrada
  em `custos-operacao.md`. Pela skill, é o caso em que o gratuito funciona como canal de
  aquisição, desde que alguém pague.

**Recomendação.**

1. Tirar "o estudante paga" da mesa até uma consulta jurídica. Este documento não é parecer; é o
   motivo para pedir um.
2. Testar pagadores que têm dor e dinheiro: (a) instituições de ensino, pela coordenação de curso
   ou pelo núcleo de estágios, que ganham um canal para os alunos e uma leitura de oferta por
   curso — hipótese já registrada na `hipotese-comercial.md` e nunca testada com ninguém; (b) empresas que recrutam estagiários e querem candidatos já filtrados por curso e
   período (hoje "recrutadores seguem fora", pelo pré-PRD); (c) acordo de publicação com as
   fontes, se os termos de uso permitirem.
3. Fazer isso com conversa e oferta concreta, não com página de preços: três conversas com
   possíveis pagadores antes de qualquer checkout. Pela skill, pagamento é o teste mais barato de
   dor real; interesse declarado não é compra, como a própria hipótese comercial já registra.
4. Registrar em `hipotese-comercial.md` a restrição legal e a estrutura do mercado. O §3º do
   mesmo artigo responsabiliza civilmente o agente que indicar estágio incompatível com o curso:
   num modelo com instituição ou empresa, a compatibilidade de curso que o grupo construiu vira
   argumento de venda e também responsabilidade.

### RCD-03 · Crítico · O esforço está fora do gargalo

**Princípios:** diagnosticar o gargalo (distribuição ou design); construir mais rápido não resolve
churn; o filtro do canivete suíço.

**Evidência.** Está detalhada na seção 3, e o resumo é este: 668 commits em 17 dias, 338 deles
entre 08 e 10/09, com documentação (181 commits, 27% do total) e motor de matching como categorias
dominantes, enquanto a distribuição nunca foi medida (RCD-04), o feedback nunca produziu um único
sinal (RCD-01) e a cobertura por área segue "não medido" em todas as linhas reais. Construído
antes de existir uso: juiz automático com o gabarito humano ainda sem nenhum rótulo, motivo da
pausa com um evento de pausa na história do banco, exclusão com carência, exportação, 12 áreas com
105 cursos e as regiões imediatas do IBGE.

**Impacto.** Cada regra nova do motor nasce de auditoria interna, de perfil sintético ou de um
modelo julgando outro modelo, nunca de alguém que usou o produto. O projeto acumula precisão onde
não tem como saber se estava errando, e nenhuma hora foi para o que está zerado: origem da visita,
conversa com usuário e busca de pagador.

**Recomendação.** Congelar ajuste de regra do motor sem caso vindo de usuário real (recusa,
mensagem ou conversa), junto com a Jooble, novas áreas, novas métricas e evolução do juiz — é a
linha final do plano da seção 7. Falha de entrega, privacidade e segurança ficam fora do
congelamento, que vale até o ciclo de feedback do RCD-01 produzir a primeira resposta.

### RCD-04 · Grave · Distribuição sem origem e métricas contaminadas

**Princípios:** Bullseye (no máximo três canais em foco); tráfego frio como teste de honestidade;
cadastro não é tração.

**Evidência.**

- Nenhum dos 107 eventos `landing_visualizada` tem origem. A propriedade `origem` só aparece no
  `cta_cadastro_aberto` e diz qual botão foi clicado (cabeçalho, hero), não de onde a pessoa
  veio.
- 18 dos 107 eventos de visita (17%) têm `pagina` de ambiente local: `/web/index.html`, que
  indica servidor local a partir da raiz do repositório, e caminhos de arquivo em disco,
  inclusive de sessões de agente. O SQL das métricas não os filtra.
- O guia pede "identifique as contas e sessões de teste para separá-las das métricas do piloto"
  (`docs/guia-publicacao-e-piloto.md:311-312`). Isso não foi feito.

**Impacto.** Com 77 identidades, cada testador move a taxa de conversão em mais de um ponto. O E03
(escolher canal) não tem como ser lido.

**Recomendação.** Registrar na visita o domínio do `document.referrer` e o `utm_source`, o que
exige ampliar as propriedades permitidas por migration, como `aquisicao-e-prova.md` já antecipa.
Descartar na consulta eventos cuja página não seja a do site publicado. Marcar as contas da
equipe e tirá-las do funil. Divulgar com um `utm_source` diferente por grupo ou canal. Só então
escolher até três canais.

### RCD-05 · Grave · O valor só aparece depois de três trocas de contexto

**Princípios:** valor primeiro, pedido depois; nunca entregar uma tela vazia (dados de exemplo);
demonstração como padrão de onboarding; reduzir o tempo até o valor reordenando e removendo.

**Evidência.**

- O caminho é site → caixa de e-mail → site → Telegram. Das 11 pessoas que abriram o cadastro,
  6 concluíram a primeira etapa; dos 6 perfis salvos, 4 vincularam o Telegram.
- Antes da conta, a única prova é o cartão "Exemplo ilustrativo · não é uma vaga real"
  (`web/index.html:77`). É honesto, mas é promessa sem prova. O valor real chega depois do
  vínculo, e aí chega rápido: mediana de 1,4 minuto entre a criação do perfil e a primeira lista.
- A conta no último passo (C05) foi a decisão certa; o que ficou pendente foi pôr valor real
  antes dela.

**Recomendação.**

1. **Prévia real antes da conta.** Depois de curso e cidade, mostrar: "Hoje o Radar analisou N
   vagas para o seu curso na sua região; estas 3 teriam nota acima de 70", com título, empresa e
   nota, e o link só depois da conta. O job já calcula tudo isso; basta gravar uma amostra por
   área e região e expô-la por RPC. A demonstração deixa de ser fictícia.
2. **Perguntar aos dois que não vincularam** o que aconteceu. Se o Telegram for a barreira,
   mandar a primeira lista por e-mail a quem não vincular em 24 horas, com o botão do Telegram
   (conferir a base legal: é o serviço pedido, não marketing).
3. **Avaliar o vínculo antes da confirmação do e-mail**, que hoje é um passo administrativo
   entre a pessoa e o valor. Exige revisão de segurança antes de qualquer mudança.

### RCD-06 · Grave · A conta é painel de configurações, sem nada acumulado

**Princípios:** retenção se constrói ("mostre o que o usuário acumulou; a perda percebida retém
mais que o benefício prometido"); o painel responde "o que eu faço agora?"; custo de troca.

**Evidência.** A conta mostra resumo do perfil, habilidades, estado das entregas, preferência de
e-mail, exportação, saída, desvínculo e exclusão (`web/index.html:445-534`). Nenhuma vaga
recebida, aberta ou em andamento aparece ali. O pré-PRD adia o histórico "até H5". O único ativo
que existe (o histórico de recomendações e aberturas) está no banco e ninguém o vê. O custo de
sair é zero.

**Recomendação.** Pôr "Suas vagas" no topo da conta: as recomendações dos últimos 30 dias com
estado (nova, aberta, me candidatei, não serviu) e data. A lista vira o segundo lugar para
registrar "me candidatei" (RCD-01) e o destino de "ver as outras" (RCD-12). Os dados já existem
em `envios` e `eventos_produto`; não há custo de IA.

### RCD-07 · Grave · Trabalho episódico: o sucesso do usuário é churn

**Princípios:** ancorar produto de trabalho único a um evento recorrente da vida (o caso
TurboTax); a tela de saída como última conversa.

**Evidência.** O trabalho definido no pré-PRD ("mostre quais vagas recentes merecem minha
atenção") termina quando a pessoa é contratada. O motivo "Consegui um estágio" existe
(`web/index.html:477`), mas nada acontece depois dele.

**Recomendação.** Quando alguém pausar com "Consegui um estágio", comemorar (o fim de uma
experiência pesa na memória tanto quanto o pico) e perguntar, de forma opcional, quando o estágio
termina, oferecendo voltar dois meses antes. A lei limita o estágio na mesma parte concedente a dois
anos, salvo para estagiário com deficiência (art. 11), então todo estágio tem data de fim; os
ciclos semestrais de programas de estágio são o outro evento recorrente. Custa um campo de data e uma regra no job,
mas só vale depois de RCD-01 e RCD-05.

### RCD-08 · Grave · A promessa é maior que a prova

**Princípios:** a promessa tem o tamanho da prova; o churn começa na landing (dívida de
expectativa); números precisos; camadas de confiança.

**Evidência.**

- A landing garante "100% automático" e "Vagas que atendem seu perfil" (`web/index.html:59-60`).
  A nota mínima é 40, 16% das entregas ficam abaixo de 60 pela regra atual, e a própria mensagem
  lista "Requisitos a conferir".
- O bot, no vínculo: "Você vai receber as vagas compatíveis com o seu perfil todos os dias de
  manhã" (`supabase/functions/telegram-webhook/vinculo.ts:25`). Existem dias com "Nenhuma vaga
  nova compatível" (`radar/notification/formatador.py:95`), e a FAQ avisa isso.
- A faixa de prova é uma lista de fornecedores: "ADZUNA GUPY GEMINI TELEGRAM"
  (`web/index.html:114`). Para o estudante isso não prova nada, e "Gemini" sinaliza IA de
  prateleira.
- A demonstração mostra Gupy, "Híbrido", "Remoto", "Publicada hoje" e notas 83 e 79. Na
  realidade, 94% das entregas vêm da Adzuna, 63% das entregas desde 05/09 saem sem modalidade,
  a idade mediana da vaga é de 20 horas (27% com mais de 48) e a nota mediana é 72.
- O plano gratuito promete "Até sete recomendações por dia" (`web/index.html:184`); a FAQ fala
  em "uma mensagem por execução", e 40 entregas passaram da sétima posição no mesmo dia por
  causa de reexecuções.

**Recomendação.** Trocar a faixa de fornecedores por números precisos da execução de ontem, que o
resumo operacional já calcula ("ontem: X anúncios lidos, Y descartados por curso ou cidade, Z
enviados"). A skill cita o efeito do número preciso: "526 casas" convence, "mais de 500" soa como
marketing. Abrir a primeira lista mostrando o trabalho invisível ("de N anúncios de hoje, 7
passaram pelo seu perfil"), que é o pico da ativação. Mudar o texto do vínculo para "quando
houver vagas compatíveis" e "sua primeira lista chega em instantes". Ou garantir uma entrega por
perfil por dia, ou trocar "por dia" por "por execução". Tornar a demonstração real (RCD-05).

### RCD-09 · Grave · O bot descarta a única conversa espontânea

**Princípios:** achar os vazamentos antes de refazer o balde (micro-decepções); volume de suporte
é problema de design; ouvir quem nunca viu o produto.

**Evidência.** A FAQ diz: "Se ficar faltando alguma coisa, é só falar com a gente pelo Telegram"
(`web/index.html:210`). Qualquer texto enviado ao bot que não seja um token de vínculo recebe
"Para vincular, use o botão do Telegram no site do Radar de Estágio"
(`supabase/functions/telegram-webhook/index.ts:95-101`, `vinculo.ts:34`), inclusive quando o
chat já está vinculado. A pessoa que escreve "essa vaga não é da minha área" ou "como pauso?"
recebe uma instrução de vínculo.

**Impacto.** Quem escreve ao bot está no momento de maior intenção ou de maior frustração. Hoje
essa mensagem é jogada fora, e com seis usuários ela é o sinal qualitativo mais valioso que o
piloto pode ter.

**Recomendação.** Para chat vinculado, responder "Recebemos sua mensagem; a equipe lê todas",
com `contato@radarestagio.com` e o link da conta, e encaminhar o texto ao chat de operação. Isso
transforma o bot no canal qualitativo que falta, quase sem custo. Registrar na Política de
Privacidade que a equipe lê essas mensagens.

### RCD-10 · Grave · ICP difuso: 12 áreas antes de validar uma

**Princípios:** quem fala com todos não convence ninguém; escolher um nicho mal atendido (dor,
tamanho, dinheiro e afinidade do fundador); foco no núcleo.

**Evidência.** A expansão de 08/09 levou o produto a 12 áreas, 45 subáreas e 105 cursos quando
nenhum estudante externo de computação tinha usado o Radar. Cada área trouxe regras próprias,
que hoje ocupam boa parte do `CLAUDE.md`. O hero ("Cansado de procurar estágio?") serve a
qualquer estudante de qualquer lugar. A cobertura por área nunca foi medida
(`docs/cobertura-estagios.md`: "não medido" em todas as linhas reais).

**Recomendação.** Definir o ICP do piloto pelos critérios de compra, não por demografia: o
gatilho (abertura dos programas do semestre), a dor (descobrir a vaga tarde ou gastar horas
triando), a tentativa anterior (alertas genéricos) e a prova que a pessoa precisa (a vaga certa,
com o motivo). Concentrar a divulgação onde há afinidade: computação, a formação do grupo, na
cidade onde o grupo mede as fontes, mais uma área cuja cobertura a matriz de cobertura confirme.
O catálogo de 12 áreas continua funcionando; o que para é o ajuste fino de regras para áreas sem
usuário.

### RCD-11 · Moderado · Nada diferencia o Radar de um alerta gratuito

**Princípios:** igual compete em preço, diferente em categoria; mesmo motor, experiência
diferente; nível de consciência (Eugene Schwartz).

**Evidência.** Quem procura estágio já conhece alertas: está no nível "consciente da solução". A
skill manda falar com esse público por comparação honesta ("três jeitos de resolver X e por que o
terceiro escala"). A landing não compara com nada, embora 94% do que o Radar entrega venha de uma
fonte que tem o próprio alerta.

**Recomendação.** Um bloco de comparação com um caso real: "a mesma busca no alerta do portal
devolve N vagas com 'estágio' no título; o Radar devolve 7, descarta as que não aceitam seu curso
e diz o que falta em cada uma". O número sai do pipeline (coletadas × enviadas).

### RCD-12 · Moderado · Mensagem densa; a atenção fica no topo

**Princípios:** o usuário escaneia, não lê; ruído é imposto cognitivo; lei de Hick; hierarquia de
atenção.

**Evidência.** Cada vaga ocupa até dez linhas (título, local, fonte, nota, requisitos atendidos, a
conferir, diferenciais, pontos, avisos, alerta e link), e sete vagas se dividem em várias partes;
o pior caso medido é de 3.216 caracteres por bloco. A 1ª posição tem 13,5% de abertura e as
posições 2 a 7, 5,9%. A nota quase não separa o que é aberto: 73,3 contra 69,9.

**Recomendação.** Testar três vagas em destaque, cada uma com uma linha de "por que esta" e o
link, e "ver as outras 4" na conta (RCD-06). A amostra é pequena: decidir depois das conversas.
É um teste de apresentação, não uma mudança na quantidade decidida pelo grupo.

### RCD-13 · Moderado · A única alternativa à saída é pausar tudo

**Princípios:** o padrão é a decisão que você tomou pelo usuário; oferecer alternativa antes do
adeus.

**Evidência.** A entrega é diária às 07:23, sem opção de frequência. Entre os motivos de pausa
está "Minha frequência mudou" (`web/index.html:480`): o produto reconhece o problema, mas só
oferece tudo ou nada.

**Recomendação.** Ao pausar, oferecer "receber só às segundas" antes de confirmar.

### RCD-14 · Moderado · O progresso começa em 0% e a última etapa diz "Comece pela sua conta"

**Princípios:** efeito de progresso ("quem vê 30% concluído termina mais do que quem vê 0%;
começar em 0% é erro de design"); gradiente de meta.

**Evidência.** `percentualDoPasso` (`web/assets/app.js:566-568`) divide a posição pelo total e
mostra 0%, 25%, 50% e 75%: começa em zero e nunca chega perto do fim. Desde a C05 a conta é a
última etapa (`app.js:598`), mas o título continua "Comece pela sua conta" (`app.js:776`) e
aparece em "Etapa 4 de 4", justamente no passo que pede e-mail e senha.

**Recomendação.** "Último passo: crie sua conta para ativar seu Radar" e progresso calculado como
(posição + 1) / (total + 1). Correção de minutos.

### RCD-15 · Moderado · O card de preço "A definir" gera dúvida sem filtrar ninguém

**Princípios:** encurtar a janela de decisão (o caminho até a ação precisa ser mais curto que o
caminho até a dúvida); preço é filtro.

**Evidência.** O menu leva a "Preços", onde o segundo card diz "Depois do piloto · A definir"
(`web/index.html:193-194`). Ele levanta a pergunta "vai virar pago?" sem ancorar valor algum e,
depois de RCD-02, talvez prometa algo que o grupo não deva fazer.

**Recomendação.** Tirar o segundo card e deixar um compromisso firme: gratuito durante o piloto,
sem cartão, e nada muda sem aviso e aceite.

### RCD-16 · Estético · "Sobre" leva ao CTA final e não há rosto humano

**Princípio:** camadas de confiança (rosto humano real, prova específica e verificável, oferta
que cabe no problema, mecanismo coerente com a promessa).

**Evidência.** O item "Sobre" do menu (`web/index.html:37`) leva à seção do CTA final
(`web/index.html:241`). Os nomes do grupo aparecem só no rodapé.

**Recomendação.** Uma seção curta "quem faz", com autorização: produto de estudantes para
estudantes tem na afinidade do fundador a prova mais barata que existe.

## 6. O que preservar

- **Entrega imediata.** Mediana de 1,4 minuto entre a criação do perfil e a primeira lista; o guia
  registra cerca de 4 minutos do `/start` à mensagem. O benchmark que a skill cita põe a média do
  mercado em 1 dia e 12 horas e os melhores abaixo de 5 minutos. É a melhor decisão de produto do
  projeto.
- **Conta no último passo, habilidade opcional e áreas de interesse como declaração de
  intenção.** É fricção declarativa, a que a skill manda manter.
- **Honestidade.** Exemplo marcado como ilustrativo, "essas fontes não cobrem todo o mercado",
  "requisitos a conferir" em vez de "não atendidos". Isso reduz a dívida de expectativa.
- **Vocabulário e denominadores.** Ativação operacional separada da de produto, métricas que não
  confundem abertura com utilidade. O problema não é falta de métrica, é falta de sinal.
- **Pausa como alternativa à exclusão**, com motivo opcional.
- **Custo marginal baixo.** Extração por vaga, não por usuário: é o que torna viável o gratuito
  para o estudante.
- **Deduplicação e "já vi essa".** Menos ruído na mensagem.

## 7. Plano recomendado

Ordem por impacto sobre esforço, no espírito do filtro que a skill propõe ((novos usuários +
nova receita + impacto) / esforço). A pontuação é julgamento desta auditoria, não medição.

| Ordem | Ação | Achados | Esforço |
|---|---|---|---|
| 1 | Cinco conversas guiadas, com compartilhamento de tela: os dois que não vincularam, dois ativados de hoje e um colega que abriu o cadastro e desistiu | 01, 04, 05, 10 | Baixo |
| 2 | Marcar contas e sessões da equipe; registrar a origem da visita; divulgar com `utm_source` por canal | 04 | Baixo |
| 3 | Pergunta do dia seguinte, com "Me candidatei", para quem abriu | 01 | Médio |
| 4 | Consertos pequenos: texto do vínculo, resposta a mensagem livre, título e progresso da etapa da conta, card "A definir", item "Sobre" | 08, 09, 14, 15, 16 | Baixo |
| 5 | "Suas vagas" no topo da conta | 06, 12 | Médio |
| 6 | Prévia com vagas reais antes da conta | 05, 08 | Médio |
| 7 | Consulta jurídica sobre cobrar do estudante e três conversas com possíveis pagadores (instituição de ensino, empresa) | 02 | Baixo em código |
| 8 | ICP do piloto por escrito e bloco de comparação com alertas | 10, 11 | Baixo |
| 9 | Frequência semanal como alternativa à pausa; retorno perto do fim do estágio | 07, 13 | Baixo |
| — | Congelar: regra do motor sem caso de usuário, Jooble, novas áreas, novas métricas, evolução do juiz | 03 | — |

## 8. Sinais para reavaliar em 24/09

Não são metas; são as leituras que permitem decidir o próximo passo.

- A fração de quem abriu uma vaga que responde à pergunta do dia seguinte.
- Candidaturas declaradas por semana (hoje não existe emissor).
- Visitas com origem conhecida e nenhuma sessão da equipe no funil.
- Das cinco conversas: quantas pessoas descrevem a busca como dor semanal (H1), por que os que não
  vincularam pararam e o que o Radar teria de fazer para alguém pagar por ele.
- Ao menos uma resposta de possível pagador: sim, não ou "sim, se".

Só com esses sinais a regra "não ajustar peso sem `vaga_irrelevante` real" deixa de ser uma
espera indefinida.

## 9. Princípios citados

Todos de @richardrx; a skill traz a síntese em inglês, e as frases citadas aqui foram traduzidas.

| Princípio | Fonte |
|---|---|
| Os nove princípios da Revenue-Centric Design | [2026-05-05](https://x.com/richardrx/status/2051672248348479691) |
| A alavanca do design muda com a fase do produto | [2026-06-15](https://x.com/richardrx/status/2066476811177877962) |
| Achar os vazamentos antes de refazer o balde (quatro níveis de severidade) | [2026-06-04](https://x.com/richardrx/status/2062621019978760424) |
| Diagnosticar o gargalo: distribuição ou design | [2026-02-28](https://x.com/richardrx/status/2027721170569564521) |
| Construir mais rápido não resolve churn; ativação resolve | [2026-04-02](https://x.com/richardrx/status/2039685818273378644) |
| Filtro do canivete suíço | [2026-05-26](https://x.com/richardrx/status/2059236567533650119) |
| Não apostar em teste A/B sem amostra; cinco entrevistas | [2026-06-01](https://x.com/richardrx/status/2061463480868229189) |
| Medir ativação, não cadastro (benchmark de tempo até o valor) | [2026-05-27](https://x.com/richardrx/status/2059616501544468624) |
| Onboarding como gatilho de comportamento (Zeigarnik) | [2026-05-11](https://x.com/richardrx/status/2053878928494690414) |
| Tratar a interface como dado | [2026-03-30](https://x.com/richardrx/status/2038566978760122661) |
| Preço é filtro; freemium e custo de servir | [2026-06-30](https://x.com/richardrx/status/2071962778072469560) |
| Cobrar os primeiros dez usuários | [2026-04-26](https://x.com/richardrx/status/2048359526487716333) |
| Escolher um nicho mal atendido como ICP | [2026-05-19](https://x.com/richardrx/status/2056789797646029232) |
| Bullseye | [2026-03-23](https://x.com/richardrx/status/2036035304868434115) |
| Tráfego frio como teste de honestidade | [2026-06-08](https://x.com/richardrx/status/2063972594223661127) |
| Nunca entregar uma tela vazia | [2026-05-12](https://x.com/richardrx/status/2054283657934758021) |
| Reduzir o tempo até o valor reordenando e removendo | [2026-03-27](https://x.com/richardrx/status/2037583944283996418) |
| Fricção declarativa × administrativa | [2026-05-07](https://x.com/richardrx/status/2052350703541039324) |
| O painel responde "o que eu faço agora?" | [2026-02-13](https://x.com/richardrx/status/2022255404743381289) |
| Custo de troca | [2026-06-23](https://x.com/richardrx/status/2069382946214080985) |
| Produto de trabalho único e evento recorrente | [2026-04-24](https://x.com/richardrx/status/2047620778338795918) |
| O churn começa na landing | [2026-04-29](https://x.com/richardrx/status/2049568514311172355) |
| A tela de saída como última conversa | [2026-05-13](https://x.com/richardrx/status/2054562119962501186) |
| Números precisos | [2026-02-18](https://x.com/richardrx/status/2024141244717281514) |
| Contraste, posição e confiança | [2026-04-28](https://x.com/richardrx/status/2049215050997784774) |
| ICP e nível de consciência antes do visual | [2026-01-14](https://x.com/richardrx/status/2011427153133351046) |
| Mesmo motor, experiência diferente | [2026-03-03](https://x.com/richardrx/status/2028837448717926518) |
| O usuário escaneia | [2026-04-08](https://x.com/richardrx/status/2042013751742705816) |
| O padrão é a decisão | [2026-05-22](https://x.com/richardrx/status/2057872036718899256) |
| Churn antes de 30 dias e efeito de progresso | [2026-04-20](https://x.com/richardrx/status/2046212675017887881) |
| Volume de suporte é problema de design | [2026-04-23](https://x.com/richardrx/status/2047289409238712726) |
| Maldição do conhecimento | [2026-06-04](https://x.com/richardrx/status/2062509937037590997) |
| Comemorar o momento de ativação (regra do pico e do fim) | [2026-04-04](https://x.com/richardrx/status/2040415841628651689) |
