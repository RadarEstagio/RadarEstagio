# PIT — Projeto de Inovação Tecnológica

**Radar de Estágio** · Métodos e Aplicações de IA (IBM3116) · Professor Alvaro Riz
**Integrantes:** Igor Costa, Ian Dias e Miguel Esteves
**Aplicação:** <https://radarestagio.pages.dev> · **Código:** <https://github.com/RadarEstagio/RadarEstagio>

Os números deste documento foram medidos na aplicação em produção, que entrega recomendações
diárias a estudantes reais desde 28/08/2026. Onde há data, ela é a da medição.

## 1. Identificação do problema

Um estudante que procura estágio precisa abrir vários portais todos os dias e ler anúncio por
anúncio para descobrir se o curso dele é aceito, se o período é suficiente, se a cidade e a
modalidade servem. A maior parte do que ele lê não se aplica ao caso dele.

O problema medido, na execução de 28/09/2026:

| Etapa | Quantidade |
|---|---|
| Anúncios de estágio coletados no dia | 733 |
| Restantes para um perfil, depois de curso, cidade e modalidade | 35 |
| Recomendações efetivamente entregues | 7 |

**Para chegar às 7 vagas que servem, alguém precisa descartar 726.** Esse trabalho de triagem
existe todo dia, com ou sem o Radar; a diferença é quem o executa. Hoje é o estudante, à mão, sem
método e sem histórico: ele reencontra a mesma vaga republicada com outro título por um agregador,
perde a que combinava porque chegou tarde e não tem como comparar dez anúncios em critérios
iguais.

O problema é relevante em escala: segundo a ABRES, **20,1 milhões** de estudantes brasileiros
estão aptos a estagiar e cerca de **1,2 milhão** consegue uma vaga — algo próximo de 6%.

## 2. Contexto do negócio

**Tipo de organização e setor.** O Radar opera no setor de intermediação de vagas de estágio, o
mesmo de agentes de integração (CIEE, Nube), agregadores (Adzuna, Indeed) e ATSs (Gupy). A
diferença é o lado do funil: esses atores organizam candidatos para a empresa; o Radar organiza
vagas para o candidato.

**Usuários envolvidos.**

- **O estudante de graduação** em busca do primeiro estágio, de qualquer curso reconhecido pelo
  catálogo do sistema (12 áreas, 45 subáreas e 105 cursos). É quem preenche o perfil e recebe as
  recomendações.
- **Quem opera o serviço** (hoje, o próprio grupo). Recebe um resumo de cada execução no Telegram,
  com usuários atendidos, vagas enviadas, requisições gastas e os avisos do dia.
- **As fontes de vaga** (hoje, a Adzuna), que fornecem os anúncios sob termos de uso que impõem
  atribuição visível e limites de requisição.

**Processo atual do estudante.** Abrir vários portais e repetir a mesma busca; ler o anúncio
inteiro para saber se o curso é aceito; reencontrar a mesma vaga republicada com outro título;
descobrir tarde a vaga que combinava.

**Principais dificuldades identificadas.**

1. **Volume sem critério.** O portal ordena por data ou relevância genérica, não pelo perfil de
   quem busca.
2. **Informação enterrada no texto.** Curso aceito, período mínimo e modalidade quase nunca são
   campos estruturados: estão no meio da descrição, em linguagem livre.
3. **Repetição.** Agregadores republicam o mesmo anúncio com outro identificador e outro nome de
   empresa, e a pessoa não percebe que já viu aquilo.
4. **Esforço diário.** A busca é episódica para a pessoa, mas o mercado publica todo dia; quem
   não olha todo dia perde.

**Situação do piloto.** Nos últimos 30 dias, medido em 30/09/2026: 113 visitas na landing, 6
perfis criados e 4 pessoas recebendo recomendações diárias.

## 3. Solução desenvolvida

**O que ela faz.** Todos os dias às 07:23 de Brasília, sem nenhuma ação do usuário, o sistema
coleta as vagas de estágio publicadas, descarta as que não servem ao perfil de cada pessoa, pede
a um modelo de linguagem os fatos de cada anúncio, calcula uma nota de compatibilidade por regras
determinísticas e envia no Telegram até sete recomendações explicadas. Quando nada passa da nota
mínima, avisa que não houve vaga compatível — não manda qualquer coisa para preencher.

**Quem utiliza.** O estudante, pelo site (cadastro do perfil e gestão da conta) e pelo Telegram
(recebimento e feedback).

**Principais funcionalidades.**

- Cadastro do perfil em quatro etapas: curso e período; cidade e modalidade; habilidades; áreas de
  interesse. A conta fica por último, de propósito: pedir e-mail e senha antes de mostrar o valor
  cobra o preço antes da entrega.
- Vínculo com o Telegram por token de uso único.
- Coleta diária com deduplicação de republicações e pré-filtro por área do curso, cidade,
  modalidade e nível de ensino.
- Extração de fatos do anúncio por IA e pontuação de compatibilidade por regra.
- Mensagem diária com nota de 0 a 100, requisitos atendidos, requisitos a conferir, avisos
  (por exemplo, "exige a partir do 4º período") e link rastreado.
- Feedback por vaga, com uma opção positiva e seis motivos de recusa, que alimenta o filtro de
  republicação e o ranking do próprio usuário.
- Controle da conta pelo estudante: editar o perfil, pausar as entregas, desvincular o Telegram,
  exportar os próprios dados e excluir a conta.

**Tecnologias utilizadas.** Python 3.12; API oficial da Adzuna como fonte de vagas; Google Gemini
Flash na extração; PostgreSQL gerenciado no Supabase, com Row Level Security por usuário; Edge
Functions (Deno) para o webhook do Telegram e para o link rastreável; GitHub Actions como
executor, disparado por um cron externo; site estático em HTML, CSS e JavaScript no Cloudflare
Pages.

**Onde a IA entra — e onde não entra.** Esta é a decisão de projeto mais importante:

> **A IA lê o anúncio. O Python decide a nota.**

O modelo recebe apenas o texto do anúncio e devolve JSON validado por schema com os **fatos**:
requisitos obrigatórios e desejáveis, cursos aceitos, período mínimo, modalidade declarada. Ele
**nunca recebe o perfil do estudante** e não opina sobre compatibilidade. Quem compara os fatos
extraídos com o perfil e calcula a nota é código determinístico, com pesos fixos: 45% habilidades,
15% período e experiência, 10% curso, 10% área da vaga, 10% logística e 10% área de interesse,
mais travas que limitam a nota (curso incompatível, período abaixo do mínimo, vaga presencial em
outra cidade). O corte de envio é a nota 40.

Três consequências práticas dessa separação:

1. **A nota é auditável.** A mesma vaga com o mesmo perfil dá sempre a mesma nota, e é possível
   explicar item a item por que ela é o que é. Um modelo que pontuasse diretamente daria respostas
   diferentes para a mesma entrada e não teria como ser conferido.
2. **O custo não cresce por usuário.** Como o prompt não contém perfil, cada vaga é extraída uma
   única vez e a extração serve todos os estudantes, naquele dia e nos seguintes.
3. **O erro do modelo fica contido.** Uma extração errada afeta os fatos de uma vaga, não a regra
   de decisão de todo o sistema.

**Interação entre usuário, aplicação, dados e IA.** O usuário escreve seu perfil no site, que grava
direto no banco; o contrato entre o site e o motor é o próprio schema do banco, sem API entre eles.
O motor lê os perfis, coleta as vagas, guarda cada anúncio e cada extração no banco (em `JSONB`,
porque o formato das fontes muda), pontua em memória e grava a avaliação antes de enviar — para que
uma falha do Telegram não jogue fora o que a IA já custou. O envio gera um registro com token
próprio, que é o que o link rastreável usa para saber que aquela pessoa abriu aquela vaga. O
feedback volta pelo webhook e altera o que ela recebe nos dias seguintes.

As telas da aplicação (formulário e mensagem diária) estão na apresentação que acompanha este
documento, slide 5.

## 4. Fluxo da solução

**Entrada → Processamento → IA → Resultado → Decisão**, com os números medidos na execução de
28/09/2026:

| Etapa | O que acontece | Medida do dia |
|---|---|---|
| **Entrada** | Coleta na API da Adzuna, por termos de busca das áreas cadastradas e por cidade de cada perfil ativo | 733 vagas em 16 requisições |
| **Processamento** | Deduplicação de republicações e pré-filtro por área do curso, cidade, modalidade e nível de ensino — tudo em Python, sem IA | 35 candidatas por perfil |
| **IA** | Extração dos fatos de cada anúncio, em lotes de dez, com cache compartilhado entre usuários e entre dias | 4 requisições ao Gemini |
| **Resultado** | Nota e ranking por perfil, recalculados do zero a cada execução | 23 recomendações para 4 pessoas |
| **Decisão** | Mensagem no Telegram; a pessoa abre o link, candidata-se na fonte e responde o feedback | até 7 vagas por mensagem |

O número que resume a arquitetura é o **4**: quatro requisições de IA atenderam os quatro usuários
do dia, porque a extração é por vaga e não por pessoa. Antes dessa decisão, eram cerca de seis
requisições por usuário por dia, e vinte estudantes já estouravam a cota.

## 5. Pesquisa de soluções e casos existentes

### Caso 1 — Unilever

- **Empresa:** Unilever, bens de consumo, operação global de recrutamento.
- **Problema:** cerca de 250 mil candidaturas por ciclo para aproximadamente 800 vagas de
  programas de entrada; a triagem manual levava meses.
- **Tecnologia:** entrevista em vídeo com análise automatizada (HireVue) e jogos cognitivos
  (Pymetrics) para ordenar candidatos antes da etapa humana.
- **Resultados relatados:** tempo de contratação de cerca de quatro meses para cerca de quatro
  semanas; aproximadamente 50 mil horas de entrevista economizadas.
- **Semelhança com o Radar:** o gargalo é o mesmo — volume grande demais para leitura humana — e a
  resposta é a mesma: ordenar antes de ler. **Diferença:** ali a máquina decide sobre pessoas, o
  que levanta risco de discriminação; no Radar ela decide sobre anúncios.

### Caso 2 — Gupy

- **Empresa:** Gupy, empresa brasileira de tecnologia para recrutamento (ATS).
- **Problema:** o volume de currículos por vaga no Brasil inviabiliza a triagem manual pelas
  equipes de RH das empresas clientes.
- **Tecnologia:** processamento de linguagem natural aplicado à ordenação e recomendação de
  candidatos dentro do processo seletivo, em 2.300 empresas clientes em 2021.
- **Resultados relatados:** 480 mil vagas preenchidas em 2021 e redução de até 80% no tempo de
  contratação.
- **Semelhança com o Radar:** extrair requisitos de texto livre e casar com um perfil é exatamente
  o que o nosso extrator faz. **Diferença:** a Gupy é paga pela empresa contratante, o que mostra
  de que lado do mercado está o dinheiro — ponto que pesa na nossa análise de viabilidade.

### Caso 3 — LinkedIn

- **Organização:** LinkedIn, rede profissional global.
- **Problema:** casar dezenas de milhões de vagas com cada usuário, em tempo real.
- **Tecnologia:** funil de recomendação em quatro estágios — recuperação de candidatas, calibração,
  modelo de engajamento e reordenação final por regras de negócio.
- **Resultado relatado:** além da escala, uma lição publicada pela própria engenharia — otimizar a
  recomendação por cliques premia títulos sensacionalistas e produz candidatura frustrada.
- **Semelhança com o Radar:** a arquitetura em camadas, com **regras explícitas na última etapa**,
  é a mesma escolha que fizemos ao deixar a nota fora do modelo. Essa lição também explica por que
  a nossa métrica de sucesso não é abertura de link, e sim a vaga marcada como útil.

## 6. Proposta de valor

O valor não está em achar uma vaga que ninguém acharia: está em **tirar do estudante o trabalho
repetido** e em dar a ele um critério de comparação que hoje não existe.

| Etapa do processo | Sem o Radar | Com o Radar | Como a melhoria ocorre |
|---|---|---|---|
| Procurar | Abrir portais e repetir a busca todo dia | Uma execução diária automática | O custo da busca sai da pessoa e vai para um job que roda uma vez para todos |
| Triar | Ler anúncio por anúncio para ver se o curso é aceito | 733 anúncios viram 7 | O pré-filtro descarta por regra objetiva antes de qualquer leitura |
| Entender | Deduzir dos requisitos se vale a pena | Nota de 0 a 100, com o que atende e o que falta | A extração transforma texto livre em campos comparáveis |
| Repetir | Reencontrar a mesma vaga republicada | Deduplicação e histórico por pessoa | A chave de duplicata e o histórico de envios bloqueiam o reenvio |
| Decidir | Comparar anúncios em critérios diferentes | Mesmo critério para todas as vagas | A nota é determinística: mesma entrada, mesma saída |

**Redução de tempo.** A mediana observada entre concluir o cadastro e receber a primeira lista de
vagas é de **1,7 minuto**.

**Redução de custo operacional.** O custo marginal de um usuário novo é próximo de zero, porque a
extração é por vaga: o custo medido é de **R$ 0,066 por lote de dez vagas**, independentemente de
quantas pessoas recebem aquelas vagas.

**Redução de erro.** O período mínimo, o curso aceito e a modalidade passam a ser conferidos por
regra, e não pela leitura apressada de quem está com pressa de se candidatar.

**Apoio à decisão.** A mensagem não diz apenas "esta vaga combina": diz quais requisitos o perfil
atende, quais precisam ser conferidos e quais diferenciais o anúncio cita.

**Capacidade operacional.** O sistema cobre 12 áreas e 105 cursos com o mesmo pipeline; ampliar
para uma área nova é acrescentar entradas no catálogo, não escrever código novo.

## 7. Dados necessários

**Origem.** API oficial da Adzuna, com chave, sob termos que exigem atribuição visível em cada
anúncio exibido ("Jobs by Adzuna") e limitam o uso a 25 requisições por minuto, 250 por dia, 1.000
por semana e 2.500 por mês. O sistema controla essa cota e interrompe a coleta quando o saldo
acaba, reservando o consumo previsto da execução diária.

**Formato.** JSON na entrada, vindo da API; JSON validado por schema na saída do modelo; no banco,
colunas relacionais para o que é estável (perfis, envios, avaliações) e `JSONB` para o payload cru
das vagas e para a extração — porque o formato das fontes muda sem aviso.

**Frequência de atualização.** Coleta e pontuação diárias, às 07:23 de Brasília. Quem vincula o
Telegram fora da janela do diário recebe uma execução imediata só para o próprio perfil. A extração
de uma vaga é reaproveitada enquanto o prompt e o catálogo não mudarem; qualquer alteração neles
troca a versão registrada e a vaga volta ao modelo.

**Problemas de qualidade conhecidos.**

- A API devolve a descrição **truncada em 500 caracteres**, o que esconde requisitos.
- Anúncios já encerrados continuam listados: a fonte não informa expiração.
- Agregadores republicam o mesmo anúncio com outro identificador e outro nome de empresa.
- Parte dos anúncios não declara stack nenhuma, o que torna a comparação por habilidade inócua.
- A fonte informa a região, não a cidade exata: uma vaga em São Gonçalo chega rotulada como Rio de
  Janeiro.

**Necessidade de armazenamento.** Um banco PostgreSQL gerenciado, hoje no plano gratuito do
Supabase (500 MB). São guardados perfis, vagas, extrações, avaliações, envios e eventos de produto;
o volume é pequeno, mas o crescimento dos eventos precisa de teto, porque banco cheio no plano
gratuito entra em modo somente leitura e derruba cadastro, vínculo e entrega.

**Privacidade.** O perfil é dado pessoal e o sistema trata isso como restrição de projeto, não como
detalhe:

- cada usuário só alcança a própria linha, por Row Level Security no banco;
- **o perfil nunca entra no prompt** — o modelo recebe apenas o texto do anúncio;
- a pergunta sobre deficiência é opcional, começa em "prefiro não informar" e não aparece em log,
  evento, prompt ou exportação;
- o estudante exporta os próprios dados e exclui a conta pelo site, com 60 dias para desfazer antes
  do apagamento definitivo;
- cadastro não confirmado é descartado por prazo, para não reter e-mail sem finalidade.

## 8. Riscos e limitações

**Respostas incorretas da IA.** A extração erra. O caso medido: em 483 anúncios com período mínimo
preenchido, nove traziam na verdade uma preferência ("preferencialmente a partir do 4º período") e
o modelo gravou como exigência — e, como perfil abaixo do mínimo tem a nota limitada a 35 contra um
corte de 40, essas vagas somem para quem está em período anterior. Em outros doze anúncios com a
mesma construção o modelo acertou, o que torna o erro inconsistente e difícil de detectar. As
defesas hoje são: o modelo só extrai fatos, nunca decide; valores fora de faixa são descartados na
validação; e a mensagem é segurada quando uma candidata fica sem extração, em vez de afirmar que
"nada é compatível".

**Dependência de API externa.** A Adzuna responde por toda a coleta. A Gupy foi desligada em 12/09
porque os termos de uso dela proíbem agregar vagas, e a Jooble tem limite de 500 requisições por
chave na versão gratuita. Fonte única significa que uma mudança de termos, de preço ou de
disponibilidade para o serviço inteiro.

**Qualidade dos dados.** Descrição truncada, vaga encerrada que continua listada e cidade informada
por região são limitações da fonte, não do nosso código, e afetam direto a qualidade da
recomendação.

**Custos de infraestrutura.** O custo cresce com **cobertura**, não com usuários: mais cidades e
mais áreas significam mais vagas novas para extrair. Hoje o custo é baixo, mas não é fixo.

**Privacidade e segurança.** O repositório é público, o que obriga disciplina: nenhum dado real de
usuário no código, segredos apenas por variável de ambiente, ações do CI fixadas por hash de
commit e token de leitura. O banco guarda dado pessoal e um dado sensível opcional, o que coloca o
projeto sob a LGPD.

**Supervisão humana.** O sistema envia sozinho, mas não opera sozinho: alguém precisa ler o resumo
diário para perceber cota estourada, coleta incompleta ou queda do modelo. A execução termina com
código de erro quando não consegue se reportar, justamente para não passar por verde.

**Resistência e adoção — o risco que decide o projeto.** No relatório da coorte dos últimos 30
dias, medido em 30/09/2026: **425 recomendações entregues, 12 aberturas de vaga (3%), 6 respostas de
feedback (0,9% das 644 recomendações do período) e nenhuma vaga marcada como útil**. No acumulado
desde 28/08 são 704 envios e 46 aberturas, em 36 pares distintos de pessoa e vaga, e o número de
vagas marcadas como úteis continua zero. Sem esse sinal, não
há como recalibrar a nota com evidência, e a regra que adotamos é não mexer em peso nenhum sem um
caso real vindo de usuário. Este é o risco mais grave do projeto, e ele não é técnico.

**Limitação de modelo de negócio.** O estudante é um pagador improvável: CIEE, Nube e os alertas
dos próprios portais são gratuitos para ele, porque quem paga são as empresas. A Lei 11.788/2008
veda cobrança do estudante por *agentes de integração*; o Radar não é um, mas um convênio com
instituição de ensino o aproximaria dessa figura, e aí a vedação passaria a valer.

## 9. Viabilidade

**Complexidade técnica: baixa, e já demonstrada.** O sistema está em produção desde 28/08/2026,
entrega todos os dias sem intervenção e tem 2.020 testes automatizados. A arquitetura é um script
disparado por cron, não um serviço; não há servidor para manter no ar.

**Infraestrutura necessária.** GitHub Actions (gratuito em repositório público) como executor;
PostgreSQL gerenciado (plano gratuito do Supabase); Cloudflare Pages para o site estático; um
disparador externo de cron; chave da API da Adzuna (gratuita); e a API do Gemini, único item pago
por uso. Para uso real em escala maior, o plano pago do banco e um domínio próprio são os dois
primeiros custos a aparecer.

**Integração.** O sistema não precisa se integrar a nenhum sistema de terceiros para funcionar: o
contrato entre o site e o motor é o próprio schema do banco. Isso reduz muito o risco de
implantação. A integração que existe é com fontes de vaga, e é por API pública documentada.

**Custos.** O custo variável hoje é a extração, medida em R$ 0,066 por lote de dez vagas; os demais
serviços estão em plano gratuito. O que muda essa conta é ampliar cobertura (mais cidades, mais
áreas) e sair dos planos gratuitos, não crescer a base de usuários.

**Pessoas.** Três estudantes construíram e operam o sistema. Para operação real são necessários:
alguém acompanhando o resumo diário e as falhas; alguém respondendo pedidos de dados e exclusão,
por exigência da LGPD; e alguém responsável pelo domínio e pelas contas de serviço. Essa divisão
ainda não foi fechada pelo grupo.

**Disponibilidade de dados.** É o ponto mais frágil: fonte única, sob termos de uso que podem
mudar. Ampliar para outra fonte é tecnicamente barato — o coletor é uma interface e uma fonte nova
se pluga sem alterar o resto —, mas depende de acordo comercial, não de código.

**Manutenção.** Os pontos que exigem atenção continuada são: mudanças nos termos das fontes;
vencimento de credenciais (o token que dispara a execução diária vence em 09/09/2027); evolução do
modelo de IA, que pode mudar formato de resposta; e as regras do motor, que precisam de evidência
de uso para serem ajustadas.

**Conclusão de viabilidade.** A viabilidade técnica está demonstrada por operação real. A
viabilidade como negócio depende de duas respostas que ainda não temos: se a recomendação serve
para quem a recebe, e quem paga por ela.

## 10. Próximos passos

| Etapa | O que envolve |
|---|---|
| **Protótipo** | Coleta e nota em Python, com perfil fixo e sem banco |
| **MVP** | Banco, conta no site, vínculo com o Telegram e entrega diária automática |
| **Piloto** | Validar com estudantes; obter o sinal de utilidade que permite calibrar a nota |
| **Avaliação** | Medir utilidade por vaga, concordância entre a nota e o julgamento das pessoas, e o funil da visita à primeira recomendação |
| **Ajustes** | Recalibrar pesos com os casos reais coletados; decidir a segunda fonte de vagas; escolher e testar um pagador |
| **Implantação** | Domínio próprio, textos legais aprovados, plano pago do banco e responsabilidades definidas |

**Funcionalidades que poderiam ser desenvolvidas.**

- **Fechar o ciclo de feedback**, que hoje é o gargalo: perguntar uma coisa só, logo depois de a
  pessoa abrir a vaga, em vez de sete botões no fim da mensagem.
- **Painel web de métricas**, hoje disponível apenas por linha de comando.
- **Segunda fonte de vagas**, para reduzir a dependência da Adzuna.
- **Registro de candidatura**, que é o evento de valor real e hoje não é observável: o estudante se
  candidata no site da fonte, fora do nosso alcance.
- **Uso do feedback nas demais dimensões** ("pedem demais", "local ou modalidade"), que hoje só
  molda republicação e área de interesse.

## Referências

1. ABRES — Associação Brasileira de Estágios. *Dados do estágio no Brasil*, 2024.
2. Google for Startups. *História da Gupy* — caso empresarial de ATS brasileiro com IA.
3. LinkedIn Engineering Blog. *Job recommendations at LinkedIn* — arquitetura de recomendação em
   quatro estágios.
4. Adzuna. *API documentation and terms of use* — documentação oficial da fonte de vagas.
5. Google. *Gemini API — structured output e limites de uso* — documentação oficial do modelo.
6. BRASIL. *Lei nº 11.788, de 25 de setembro de 2008* — Lei do Estágio.
