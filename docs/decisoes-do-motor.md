# Decisões do motor de recomendação

Por que coleta, pré-filtro, extração, pontuação e mensagem são como são, com as medições que
sustentaram cada regra. Movido do `CLAUDE.md` em 19/09/2026 sem reescrita: cada seção guarda a
data da decisão, e "hoje" se refere a essa data. As regras que não podem quebrar estão resumidas
no `CLAUDE.md`; a organização em camadas está na [arquitetura](arquitetura.md).

## Pontuação: por que os pesos são estes

Pesos em `matching/avaliacoes.py`. O que motivou cada trava:

- **Cobertura de requisitos suavizada**, `(1+atendidas)/(1+exigidas)`: requisito ausente do
  perfil vale como incerteza ("não informado"), nunca como veto. As travas de 60/70 pontos por
  habilidade ausente foram removidas em 31/08/2026 porque enterravam vagas boas (EPE Ciência de
  Dados a 48 por "faltar Power BI") enquanto anúncios sem stack ocupavam o topo.
- **Vaga que não declara stack** recebe cobertura neutra de 0.25 (~nota 65): entregável, atrás
  de vaga com boa parte dos requisitos batidos, mas não de *qualquer* vaga com requisito batido:
  quem atende 1 de 8 ou mais tem cobertura menor (2/9 < 0.25). Era 0.35 até 09/09/2026, quando a
  mensagem do Igor mostrou anúncio mudo em 75 acima de vaga em que ele batia MySQL e SQL (69).
- **Vaga sem nenhum requisito atendido não passa da neutra** (10/09/2026). Com um requisito só,
  a suavização dava 0.5 a quem não atendia nada, o dobro da vaga sem stack. A Monte Carlo
  (obrigatório Excel, que não conta em computação, e desejável Power BI) tirava 75 para os dois
  estudantes de Engenharia de Software sem atender nada: na execução de 10/09 ficou em 7º e 9º,
  sem ser enviada, e entre as candidatas não enviadas estava em 1º e 2º. Agora, se nenhum
  requisito que conta na nota é atendido, em nenhuma das listas, a cobertura fica no máximo em
  0.25; quem atende ao menos um segue a fórmula. O teto nunca sobe nota e não é peso novo: é
  coerência com a cobertura neutra, como a troca de 0.35 por 0.25. Office e idioma atendidos em
  computação continuam fora da conta e não tiram a vaga do teto. Medido nas 119 extrações da
  versão atual contra 18 perfis (6 reais e 12 do catálogo): 300 de 2.142 pares caem, 9 abaixo
  da nota mínima. Nas candidatas das últimas 48 h ainda não enviadas dos 4 perfis reais com
  candidatas, saem das 7 primeiras 9 vagas, todas sem requisito atendido; entram 9, seis que
  batem algo do perfil e três sem requisito atendido que ganham pelos outros fatores (curso,
  área, interesse). O teto é da vaga inteira, não de cada lista: obrigatória não atendida com
  desejável atendido continua valendo 0.5 com peso 80%, e a Colégio IPA, que pede "Suporte" e
  cita "Programação", tira 75. Por lista, os pares com nota 70 ou mais sem obrigatória atendida
  cairiam de 15 para 8, mas mudaria também vaga com todas as obrigatórias batidas e um
  desejável faltando; fica para decidir com `vaga_irrelevante`.
- **"Planilhas" é família atendida por Excel** (10/09/2026). Era membro de Pacote Office, não
  nome de família, então Excel não atendia "planilhas" (7 extrações), "planilhas eletrônicas"
  nem "Google Sheets". Com o teto acima, a vaga de Administração que pedia só "planilhas
  eletrônicas" caía de 65 para 54 para a estudante que tem Excel; agora sobe para 75, e 39
  pares da medição acima sobem por isso. Custo aceito: "Controle de planilhas" no perfil deixa
  de atender "planilhas" por palavras, porque a família decide sozinha o requisito que nomeia.
  Seguem abertos: "Pacote Office" no perfil não atende "Excel" (56 extrações; é a única
  habilidade de Office que o catálogo sugere para Direito, Saúde e Educação), e Excel não atende
  "informática" nem "microinformática" (2 extrações cada).
- **Requisito genérico é atendido por habilidade da mesma família** (09/09/2026): "banco de
  dados" por SQL/MySQL/Postgres, "back-end" por Java/Spring/Django/Node, "front-end" por
  React/HTML/CSS/JS, "programação" por qualquer linguagem, "ETL", "cloud", "versionamento",
  "mobile", "pacote Office", "análise de dados" e "IA" idem (`FAMILIAS_DE_HABILIDADES`). O nível
  exigido continua valendo contra o melhor membro presente. Antes, um perfil com SQL, MySQL,
  Java e Spring via zero atendidos em "banco de dados, front-end, back-end, ETL".
- **SQL e bancos relacionais são uma classe só na nota** (13/09/2026). "SQL" não era nome de
  família: quem tinha MySQL ou PostgreSQL ficava sem nada atendido na vaga que pedia SQL (54, a
  nota de quem tem MongoDB). Ian decidiu que, para estágio, SQL e o banco são a mesma coisa:
  SQL, MySQL, PostgreSQL, SQL Server, SQLite, MariaDB e Oracle Database se atendem nos dois
  sentidos (`EQUIVALENCIAS_DE_HABILIDADES`). A primeira versão só deixava SQL atender os bancos,
  e o termo genérico valia mais que o específico: na vaga adzuna:5873229288, que pede
  PostgreSQL, MySQL e Oracle, "SQL" tirava 70 e "MySQL" 63. Dentro das famílias o membro vale
  pelos equivalentes, senão "ETL" e "análise de dados", que listam SQL, deixavam MySQL abaixo.
  Não é peso novo, é equivalência, como as famílias de 09/09. O que acompanha a classe:
  - "Oracle" exigido é atendido pela classe, mas "Oracle" no perfil não atende nada dela,
    porque também é o ERP: o perfil de Engenharia de Produção com Excel, Oracle e SAP ganhava
    SQL em 16 vagas reais. "Oracle Database" entra nos dois lados.
  - PL/SQL e T-SQL no perfil implicam SQL, com o mesmo nível, e o requisito PL/SQL ou T-SQL só é
    atendido pelo próprio dialeto. Toda grafia vai para a forma com barra antes da partição
    (`GRAFIAS_DE_DIALETOS_DE_SQL`: "PL-SQL" e "PLSQL" a "PL/SQL"; "T-SQL", "TSQL" e
    "Transact-SQL" a "T/SQL"), e a partição do `b1ccbf1` dá a parte "SQL", com nível e
    palavras, também dentro de habilidade composta. Juntar "PL/SQL" num nome só, como a versão
    anterior fazia, tirava a parte "SQL" de "Oracle PL/SQL" e parecidos (75 → 61) e deixava
    "Oracle" no perfil atender "Oracle PL/SQL" por palavras, o caso do ERP.
  - Aliases levam formas compostas à classe: "Banco de dados SQL", "Linguagem SQL" e "Consultas
    SQL" a SQL; "Microsoft SQL Server", "MSSQL" e "Azure SQL Database" a SQL Server; "Oracle DB"
    a Oracle Database; "Postgre" a PostgreSQL. NoSQL, MySQL Workbench, SSRS, Oracle ERP e Oracle
    Cloud ficam fora. Esses aliases valem só na comparação com o perfil
    (`ALIASES_DE_COMPARACAO`): a identidade do requisito, que decide a regra de requisito
    repetido, continua a do `b1ccbf1`. Sem isso "SQL Server avançado" e "Azure SQL Database"
    viravam um requisito só, o segundo passava a exigir o nível avançado (75 → 61) e o
    desejável sumia dos diferenciais.
  - A classe não é família. Família decide sozinha o requisito que nomeia e desliga a
    comparação por palavras; na versão que usava família, "Consultas SQL", "Banco de dados
    MySQL" e "ERP Oracle" perderam em Direito o requisito que atendiam (98 → 64).
  - Nível, composição ("MySQL e Python" exige as duas partes) e NoSQL fora da classe seguem
    valendo. A regra é só da nota: o prompt segue separando SQL de MySQL para guardar o nome do
    anúncio, e `VERSAO_DA_EXTRACAO` segue `7efdbc95`.

  Medido contra o `b1ccbf1`: nenhuma nota cai e nenhum requisito atendido some nas 41 vagas
  reais que citam banco (246 pares com 6 perfis, 114 sobem; 861 com os 21 perfis da auditoria,
  200 sobem) nem nos 8.836 pares da matriz da auditoria (2.298 sobem), e MySQL ou PostgreSQL
  deixam de ficar abaixo de SQL na mesma vaga (eram 16 e 21 vagas).
  `tests/test_corpus_de_bancos.py` pontua um corpus com dialeto dentro de habilidade composta e
  requisitos que o alias junta, com as regras novas ligadas e todas desligadas juntas
  (equivalências, aliases de comparação e grafias dos dialetos), e exige que nenhuma nota caia,
  nenhum requisito suma e alguma nota suba; resiste a mudança de peso e quebra se as grafias
  voltarem a juntar o dialeto ou se a identidade do requisito voltar a usar o alias. Risco
  aberto: fora de computação a parte "SQL" do dialeto compara por palavras, então "T-SQL" passa
  a atender "SQL Server Reporting Services", como "PL/SQL" e "SQL" já atendiam.
- **Soft skill não conta na cobertura de computação** (09/09/2026), como Office e idiomas:
  anúncio cuja única habilidade era "comunicação" ganhava cobertura 0.5 e nota 75. Fora de
  computação continua contando, porque "Comunicação" e "Organização" são habilidades sugeridas
  no cadastro dessas áreas.
- **Desejáveis que faltam aparecem na mensagem** (09/09/2026) como "Diferenciais que a vaga
  cita", logo abaixo dos requisitos a conferir. Só 39% dos anúncios reais listam desejáveis, com
  3 ou 4 itens, então a linha custa ~150 caracteres numa mensagem de 7 vagas. Continuam sem
  virar veto e sem entrar em "a conferir"; o peso de 20% nas habilidades é o de sempre. O rótulo
  é "diferenciais", não "não atendidos", pelo mesmo motivo do "a conferir" do Igor.
- **Idiomas e pacote Office não contam na cobertura** (ninguém os cadastra no perfil), mas
  seguem visíveis na lista de requisitos. As variantes normalizam antes da comparação
  (03/09/2026): "Microsoft Excel" vira `excel` e "Google Sheets" vira `planilhas`. Antes só o
  nome exato era ignorado e a variante pesava — uma vaga de dados caiu para 68 penalizada por
  Google Docs, Drive e Excel. A normalização é por alias, não por pedaço de palavra, para
  `WordPress` não virar `Word`.
- **Modalidade extraída preenche a lacuna da fonte** (05/09/2026): a Adzuna não traz
  modalidade estruturada, então a IA extrai o regime declarado no texto ("remoto",
  "hibrido", "presencial", null se o anúncio não diz — nunca deduzido pela cidade). A
  modalidade da fonte prevalece; a extraída vale na logística, na trava de perfil remoto e
  no rótulo da mensagem. Valor fora do vocabulário vira null sem derrubar o lote.
- **Habilidades comparadas por nome normalizado, depois família e, fora de computação, por
  palavras inteiras** (10/09/2026, revisto no mesmo dia depois da auditoria do #41). Só o nome
  exato deixava estudantes fora de computação sem nada atendido: o anúncio de Direito descreve
  atividades ("revisão de contratos", "atendimento ao público") e o perfil cadastra a habilidade
  ("Contratos", "Atendimento"). As duas vagas do Veirano, que descreviam o perfil de um estudante
  de Direito, ficaram fora com 64 e passam a 86. Fora de computação, quando nome e família falham,
  o requisito é atendido se todas as palavras de um estão no outro, nos dois sentidos, com plural
  dobrado; palavra inteira, nunca pedaço, e "análise de dados" não atende "análise de crédito".
  **Nem perfil nem vaga de computação comparam por palavras**: a primeira versão deixou
  `JavaScript` atender "React JS", `SQL` atender "PL/SQL" e `React` atender "React Native", e lá
  os requisitos são nomes de tecnologia, que o nome exato e as famílias já tratam. A trava olhava
  só o curso até a segunda auditoria de 10/09, e um estudante de Estatística com React atendia
  "React Native" (55 → 93); agora olha também a área da vaga. O custo, medido em 22 perfis × 343
  extrações: em vaga de computação, perfil de outro curso perde também correspondência que não é
  técnica ("inglês técnico" ← Inglês, "atendimento ao cliente" ← Atendimento, "manutenção de
  computadores" ← Manutenção); 24 de 7.546 pares perdem requisito atendido, 4 com nota menor
  (−15, −15, −10, −1), nenhum entre as candidatas reais. Vaga com `area_da_vaga` nula não é
  travada: são programas abertos a várias formações, sem falso positivo encontrado. Requisito com " e ", "/", vírgula,
  ";", "|" ou " & "/" + " com espaços exige todas as partes ("Excel e Power BI" não é atendido
  só por Excel; "F&O" e "R&S" não se partem); separador dentro de parênteses não conta. " ou " e
  "e/ou" são alternativas, e basta uma. O nível dito na última parte vale para as partes sem nível,
  dentro da mesma alternativa ("Inglês e Espanhol avançados"); dito só na primeira, não se espalha
  ("Excel avançado e Power BI"), e não atravessa um "ou". Parte que só tem nível se junta à
  anterior, e a faixa vale pelo menor ("Inglês intermediário/avançado" é atendido por
  intermediário). O nome inteiro do requisito composto exige o maior nível das partes, e o da
  habilidade composta do perfil vale pelo menor, contando parte sem nível: "Inglês e Espanhol
  básicos" não atende "Inglês avançado e Espanhol básico", nem "Inglês avançado e Espanhol"
  atende "Inglês e Espanhol avançados". Limite conhecido: nível no plural depois de "ou" ("Inglês
  ou Espanhol avançados") vale só para a última alternativa; não há caso nos dados. Habilidade do
  perfil escrita assim vira várias, pela mesma regra. Requisito que aparece mais de uma vez com o
  mesmo nome só conta como atendido se todas as versões forem, então a ordem em que a IA listou
  não muda a nota, e a mensagem mostra a versão que falta ("a conferir: Excel avançado" para quem
  tem Excel, não "Excel"). O nível é o maior entre nome, família e palavras,
  para que acrescentar habilidade nunca derrube a nota; família decide sozinha o requisito que
  nomeia; alias vale só para o nome inteiro. Risco aceito: habilidade genérica de uma palavra
  ("Organização", "Gestão", "Processos") atende toda atividade que a contém, e requisito de uma
  palavra ("redes", "segurança") é atendido por habilidade que a contenha ("Redes sociais",
  "Segurança do trabalho"); o pré-filtro corta a maior parte desses cruzamentos entre áreas.
- **Área de interesse** (01/09/2026, revisto em 08/09/2026): a IA classifica a vaga em subáreas
  de um catálogo fechado (`AreaDeInteresse`, derivado de `domain/areas.py`) e o fator compara com
  `perfis.areas_de_interesse`. São três níveis: match ganha o fator cheio; **outra subárea do
  mesmo campo do curso vale meio fator e não gera aviso**; vaga de outro campo zera o fator,
  limita a nota a 65 e põe o aviso "Fora das suas áreas de interesse". Vaga sem subárea
  reconhecida também fica com meio fator. Perfil sem interesses não é penalizado, e área recusada
  no Telegram continua zerando. O nível do meio existe porque punir igual quem marcou "Mercado
  financeiro" e recebeu Contabilidade era mentir no aviso e cobrar duas vezes: estar em outro
  campo já pesa em `PESO_AREA`.
- **Curso** (02/09/2026): incompatível limita a 35 (abaixo da nota mínima, sai da mensagem) com
  o aviso "Exige formação de outra área"; parcial limita a 75 — vaga operacional de fundos com
  Excel/Python/SQL chegou a 90 só pela stack genérica. Desde 03/09/2026 quem decide o nível é
  `matching/compatibilidade.py`, com o catálogo de cursos de `domain/areas.py`, e não mais o
  julgamento do modelo: a IA extrai `cursos_aceitos` e o Python compara. Curso aceito da mesma
  área só conta como equivalente quando a área declara `cursos_intercambiaveis` — verdadeiro só
  em computação, onde Ciência da Computação, Engenharia de Software e ADS disputam as mesmas
  vagas. Sem essa trava, Engenharia Civil valia por Engenharia Química e Contábeis por Economia
  (08/09/2026).
- **Período mínimo** (14/09/2026): perfil abaixo do `periodo_minimo` extraído limita a 35 com o
  aviso "Exige a partir do Nº período", como curso incompatível. Antes só zerava os 15 pontos de
  período/experiência, e um perfil de Administração no 1º período recebeu em 1º lugar, com 80, a
  vaga do CIEE que pede "4º ou 5º período". O aviso substitui o ponto contra genérico, mas avisos
  não são gravados em `avaliacoes` (como no curso incompatível): `baixar_meus_dados` mostra 35 sem
  motivo, e as linhas antigas ainda têm "Período mínimo incompatível". Experiência exigida segue
  só no fator, e faixa ("4º ao 6º") segue sem teto superior, porque o prompt não extrai o limite.
  Valor fora de 1 a 12 vira `None` na validação: ano lido como período esconderia a vaga de todos.
  Das 131 extrações da versão `7efdbc95` com `periodo_minimo`, 130 batem com o anúncio. O erro é
  frase de preferência lida como mínimo, e o modelo é inconsistente nela: de 4 achadas, só "é
  desejável que esteja cursando entre o 4 ao 7 semestre" (adzuna:5872138783) virou 4; a mesma
  frase na 5872067515, "preferencialmente o 6º ou 7º período" (5880906488) e "desejável entre 4º
  e 7º período" (5881849408) vieram nulas. Com o teto, esse erro esconde a vaga; a correção é uma
  frase no prompt, adiada porque muda `VERSAO_DA_EXTRACAO` e reextrai o cache. Nos 9 anúncios com
  faixa por curso a extração guardou o menor mínimo (5880225477: ADS a partir do 3º e CC a partir
  do 7º → 3), mas é comportamento observado: o prompt não manda. Nos 4 perfis ativos, 54 de 663
  pares caem abaixo de 40 e 8 dos 188 envios de 7 dias não teriam saído. Risco aberto:
  `perfis.periodo` é o que a pessoa digitou no cadastro e não avança sozinho, então perfil
  desatualizado passa a perder vaga que já pode fazer.
- **Pontos a favor e contra são gerados da comparação** (03/09/2026), não escritos pela IA.
  Sobraram "Curso compatível" e "Exige experiência prévia" (o período virou aviso em 14/09), porque
  as habilidades já aparecem na lista de requisitos e duplicavam. `alerta_pegadinha` continua
  vindo do modelo.
- **Viés conhecido, registrado em 03/09/2026**: anúncio que declara
  uma tecnologia só e é atendido tira 100, enquanto um que declara cinco e atende três tira 85 —
  a suavização dá 1.0 cravado com 1 de 1. Quanto mais honesto o anúncio, pior a nota. As duas
  correções possíveis e o sinal que reverte a decisão estão na seção de viés do ranking de
  `docs/arquitetura.md`. **Não ajustar peso sem `vaga_irrelevante` real.**

## Áreas: uma fonte só para curso, vaga, banco e site (08/09/2026)

`domain/areas.py` é o catálogo único das 12 áreas. Cada área declara os cursos que caem nela,
três padrões de vaga, os termos de busca e as subáreas. Tudo o mais deriva daí, e é por isso que
nada pode ganhar uma lista própria:

- `AreaDeInteresse` (em `domain/models.py`) é **construído** a partir de `SUBAREAS`.
- A migration `0017` foi **gerada** do mesmo catálogo — o `CHECK` de `perfis.areas_de_interesse`
  e a função `validar_cadastro_radar`.
- `web/assets/areas.json` é **arquivo gerado** e serve o cadastro, que monta as áreas conforme o
  curso digitado e lista os `cursos_sugeridos` no campo de curso (16/09/2026: o `datalist`
  com cópia da lista saiu do `index.html`; o curso segue livre, ao contrário da cidade). Mexeu
  em `areas.py`, regere; `tests/test_areas_do_front.py` e `tests/test_migracao_das_areas.py`
  quebram se alguma das três listas sair do lugar.

Os padrões são dois de propósito: `titulo` é amplo e responde "essa vaga é da minha área?";
`exclusao` é estreito e responde "essa vaga é inequivocamente de outra?". O padrão `titulo`
compilado inclui automaticamente os nomes de curso e os rótulos de subárea da área — "Estágio em
Engenharia de Alimentos" e "Produção de Material Didático" contam sem lista extra.

Precedência do pré-filtro (`fora_da_area_do_curso`, revista em 08/09/2026 à noite):
1. Descrição que cita o curso do perfil **com contexto de formação** ("cursando X", "estudantes
   de X", "aceita X", "cursos: X") ou que abre a qualquer formação mantém. Sem o contexto, "terá
   direito a vale-transporte" mantinha toda vaga para Direito e "boa comunicação" mantinha tudo
   para Comunicação — 19 de 20 casos falsos numa auditoria. Desde a noite de 08/09 a exigência
   vale também para nome composto ("consultoria em recursos humanos" mantinha tudo para RH), a
   janela é de 24 palavras (listas longas de cursos aceitos) e o contexto não atravessa rótulo
   "campo:" — anúncio de agência traz "formação: não informado … ramo: recursos humanos".
   Desde 10/09/2026 a busca inclui os sinônimos de nome composto que o catálogo converte no
   curso da pessoa (`nomes_do_curso`): quem cursa Ciências Contábeis procurava só "contabilidade"
   e perdia "cursando Administração ou Ciências Contábeis" — 23 vagas reais, mais 2 de Ciências
   Econômicas e 3 de "gestão de RH". Sigla e palavra solta ("si", "ti", "redes") ficam de fora
   porque aparecem em texto comum ("entre si", "redes sociais").
   **Rótulo de formação com qualificador (16/09/2026).** A trava do dois-pontos só deixava passar
   o dois-pontos colado ao termo ("Formação:", "Cursos:"), e a vaga de título genérico caía com
   "Cursos aceitos: Administração", "Formação acadêmica: Direito", "**Cursos desejáveis**: -
   Marketing", "Graduação em: …", "Curso(s): …" e "Graduação:Economia | Administração", em que
   só o primeiro curso contava por faltar espaço depois do dois-pontos. `PADRAO_ROTULO_DE_FORMACAO`
   aceita o termo de formação (curso, cursos, curso(s), formação, graduação, escolaridade,
   cursando, ensino ou nível superior) com até dois qualificadores de uma lista fechada (aceitos,
   acadêmica, desejada, desejáveis, necessária, em, de, andamento, curso, abaixo), ligados só por
   espaço ou negrito de markdown. Depois do rótulo valem as mesmas 24 palavras, e o segundo
   dois-pontos continua travando: "formação acadêmica: não informado … ramo: recursos humanos"
   segue de fora. A lista é fechada porque a descrição chega sem quebra de linha e o valor de um
   campo emenda no rótulo do seguinte; aceitando qualquer palavra e qualquer termo de formação
   antes do dois-pontos, três anúncios reais vazavam: "área de atuação : jurídico … logística"
   para Logística, "graduação;desejáveis: inglês …;boa comunicação" para Comunicação e
   "conhecimentos e formação requeridos: … conhecimento básico em informática" para Informática.
   Medido contra o `main` nas 1.003 vagas guardadas com 65 cursos sintéticos (65.195 pares): 129
   citações de curso em 44 vagas ganham contexto e nenhuma perde; 27 pares deixam de ser
   descartados e nenhum passa a ser. 24 são cursos que o anúncio lista ("Cursos desejáveis" do
   grupo YDUQS, "Estágio Comercial" com "cursando **Ensino Superior** em:", "Graduação:" sem
   espaço numa vaga de análise de sistemas que aceita Administração); os outros 3 são do curso
   "Gestão", que casa dentro de "gestão de TI", "gestão comercial" e "gestão da informação", como
   já casava em "cursando gestão comercial". `vagas` só guarda o que passou no pré-filtro de algum
   perfil, então a vaga que o defeito descartava para todos não entra na conta, e o ganho real é
   maior que o medido. Limites: "exigida" e "requerida" ficaram fora dos qualificadores (a única
   ocorrência era a de Informática), então "Formação exigida: X" segue travada; rótulo com frase
   não conta ("Graduação em andamento a partir do 5º período:", 2 pares reais de uma vaga de PMO
   perdidos para Engenharia de Produção e Relações Internacionais; "nas seguintes áreas:"); e,
   como já valia para "Formação:", contam as 24 palavras depois do rótulo, não só a lista, e ponto
   sem espaço (".conhecimento em banco de dados") não fecha a frase.
2. Curso sem área conhecida: mantém só título sem marcador forte de área alguma ("Programa de
   Estágio", "Estagiário"). Sem isso, um perfil de Agronomia passava 96% das vagas (641 de 667)
   para a extração.
3. **Sinal da própria área no título vence o veto de outra área.** "Marketing Comercial" é de
   marketing e de comercial; "Direito Civil" era vetado por `civil` de engenharias, "Estágio
   Administrativo Financeiro" por `financeiro`. Com a ordem antiga, 240 de 315 títulos legítimos
   caíam para o próprio dono; com a nova, zero título com marcador forte é perdido nos dados reais.
4. Sem sinal próprio, marcador forte de outra área descarta; título genérico cai para a descrição.

Os padrões de descrição são estreitos de propósito ("rotinas administrativas", não
"administração"; "área comercial", não "comercial"), porque a citação do curso já é tratada com
contexto no passo 1.

**Produção de vídeo e responsabilidade civil (16/09/2026).** A exclusão de engenharias toma
"produção" e "civil" como marca de outra área, então "Estágio em Produção de Vídeo" saía para
Comunicação e para curso fora do catálogo (Cinema e Audiovisual cai no passo 2), e "Responsabilidade
Civil" saía para Direito sem a descrição ser lida. "Produção (de) vídeo(s)" entrou nas exceções de
"produção" (conteúdo, audiovisual, editorial, material, eventos), no veto e no título de
engenharias, que mantêm a mesma lista; "civil" depois de "responsabilidade" entrou ao lado de
direito, processo e registro. Sem o veto, o título cai na descrição (passo 4), como "Edição de
Vídeo" já caía: para Comunicação sem contexto de marketing na descrição, a vaga continua saindo.
Seguem com o veto de engenharias "Engenharia de Produção", "Produção", "Produção Industrial",
"Planejamento e Controle da Produção", "Engenharia Civil" e "Construção Civil". Medido: nenhum dos
763 títulos distintos do banco muda em padrão algum, e nenhum par muda. Num corpus de 25 títulos × 9
cursos × 4 descrições, 92 pares mudam: 60 deixam de sair (Comunicação e Publicidade com descrição de
marketing, Cinema e Audiovisual e Agronomia em qualquer descrição) e 32 passam a sair, os de
Engenharia de Produção e Civil em "Produção de Vídeo", que deixou de ser título de engenharia.
Custo aceito: curso sem área conhecida (Agronomia) passa a receber esses títulos, como já recebe
"Estágio em Edição de Vídeo". Limites: "Produção e Edição de Vídeo", "Produção Cultural", "Produção
de Moda", "Defesa Civil" e "Sociedade Civil" seguem vetados, e "vídeo" não é sinal de marketing no
título.

## Qualidade da mensagem e do pré-filtro

- `NOTA_MINIMA` (padrão 40) corta vagas fracas da mensagem. Sem aprovadas, o estudante recebe
  que nada compatível apareceu e que a busca volta amanhã: silêncio total pareceria serviço
  morto. Depois de `DIAS_DE_SILENCIO_ATE_AVISAR` dias sem nenhuma recomendação, e no máximo uma
  vez por período, a mesma mensagem ganha um parágrafo sugerindo ampliar cidade ou modalidade —
  parágrafo, e não segunda mensagem, para não notificar duas vezes no mesmo dia.
- `fora_da_area_do_curso` (`domain/areas.py` + `filtering/prefiltro.py`) exige sinal da área do
  curso da pessoa no título ou, se o título for genérico, na descrição; título de outra área
  descarta antes de tudo. Cada área tem dois padrões: `titulo` (amplo, "é da minha área?") e
  `exclusao` (estreito, "é inequivocamente de outra área?"), porque um padrão só derrubaria
  vagas legítimas. Curso sem área conhecida não filtra por área — melhor recomendar demais que
  emudecer o radar.

- **Vaga só para curso técnico** (14/09/2026). A Jovem Valor anunciou estágio "para estudantes de
  ensino técnico em administração" e o perfil de Administração, de graduação, o recebeu com
  "Curso compatível", porque `normalizar_curso` tira "técnico em" como prefixo. Para perfil que
  não é de curso técnico, vaga cujos `cursos_aceitos` são todos de nível técnico
  (`curso_de_nivel_tecnico`; ensino médio e "áreas afins" ao lado não contam como superior) tem
  curso incompatível, teto 35 e o aviso "Vaga para estudantes de curso técnico". **Técnico como
  acréscimo fica exatamente como no `main`**, pedido do dono: com algum item de nível superior, a
  lista inteira é comparada como antes, técnico incluído. A primeira versão tirava o técnico da
  comparação e "ADM" + "Técnico em Administração" caía de 98 para 35;
  `test_lista_com_curso_superior_e_tecnico_pontua_como_no_main` impede a volta, e
  `test_item_sem_tecnico_com_barra_ou_alternativa_pontua_como_no_main` fixa as notas do `main`
  para item sem técnico com "/", "ou" e "e/ou". Item que cita técnico e tem "ou", "e/ou", "/" ou
  vírgula vale como a lista das suas alternativas (`cursos_do_item`, na compatibilidade, não em
  `normalizar_curso`, que tem paridade com o site): "Técnico em Administração ou Administração" e
  "Técnico ou superior em X" valem por X, a vírgula distribui o nível ("Técnico ou Superior em
  Administração, Contabilidade ou Economia") e "Técnico ou superior", sem curso, fica parcial
  como "Ensino Superior". "Aluno(a)(s) do curso técnico em X" conta como item técnico, como
  "estudantes". Perfil técnico nunca recebe a trava de só técnico e compara com todas as
  alternativas, então "Técnico ou superior em X" também sobe para ele (35 no `main`, compatível
  agora). CST e ADS contam como nível superior nos itens de curso (`PADRAO_NIVEL_SUPERIOR`); no
  título a sigla solta é outra coisa ("Meta Ads", "Google Ads") e só conta depois de "ou", "e" ou
  "em". No pré-filtro sai o título que dirige a vaga a estudantes ou alunos de ensino, curso ou
  nível técnico ("vaga de estágio para estudantes de ensino técnico"), o que começa por "Estágio
  (de|para) nível ou curso técnico" e o que tem "nível técnico" num trecho só seu depois de hífen,
  salvo se também citar nível superior (`PADRAO_TITULO_TAMBEM_SUPERIOR`). Ficam o público atendido
  ("apoio a alunos do ensino técnico"), "Inglês nível técnico", o substantivo "técnica(s)"
  ("estudantes de técnicas de vendas"), "Estágio Técnico" e "Suporte Técnico". A exceção é a
  mesma do ensino médio, que passou a manter "ensino médio ou tecnólogo" e "ou graduandos". O
  prompt não mudou. Medido em 14/09 contra o `main`, nas 456 extrações da versão atual com os 4
  perfis ativos (1.824 pares): 10 extrações são só técnico e nenhuma tem item que cite técnico
  com separador; 22 pares mudam no caminho do pipeline (descarte do pré-filtro e, entre os que
  passam, nota, avisos ou pontos): 11 perdem nota, 3 só trocam o aviso, 2 saem no pré-filtro e 6
  só trocam o motivo do descarte. No run de 14/09 só a Jovem Valor sai do top 7 de Administração.
  O título pega 2 dos 893 títulos de `vagas`, que só guarda o que passou no pré-filtro de algum
  perfil. Limites: quando a IA tira o "Técnico em" dos itens seguintes ("Técnico em Automação",
  "Eletrotécnica"), a vaga parece mista e segue como no `main` (3 extrações); "Técnico em X ou Y"
  em que o técnico vale para os dois ("Técnico em Informática ou Telecomunicações") deixa de ser
  só técnico; hífen não separa ("Técnico - Superior em Administração" segue 35); parênteses davam
  parcial ("Técnico ou Superior (Administração)") e desde 16/09 valem como "Técnico ou superior em
  Administração" (ver "Curso com pontuação, complemento ou abreviação"); "ADM ou Técnico em ADM"
  fica igual a ["ADM"], que dava 35 até "ADM" virar sinônimo de administração em 16/09/2026 e agora
  vale como Administração (ver "Curso aceito fora do catálogo").
- **Vagas para PCD** (16/09/2026). A vaga afirmativa da MUDES ("Vaga Afirmativa (Lgbtqiapn, Raça,
  Gênero, Pcd, 40)") chegou em 1º lugar, com 100, a quem não é PCD e sem indicação nenhuma. O
  perfil ganhou `pessoa_com_deficiencia` (`0026`): `true`, `false` ou `null`, e `null` é tanto
  "Prefiro não informar" quanto perfil anterior à pergunta, com o mesmo efeito. Decisões do Ian:
  - Quem respondeu **não** deixa de receber vaga **exclusiva** para PCD (motivo de descarte
    `exclusiva_para_pcd`). Vaga **afirmativa** para vários grupos continua chegando, com o aviso
    "Vaga afirmativa: confira se você faz parte de um destes grupos: <lista do anúncio>" (ou
    "confira no anúncio a quem ela se destina" sem lista legível): o Radar não sabe raça, gênero,
    orientação nem idade, e tirá-la esconderia a vaga de quem é dos outros grupos.
  - Para quem é **PCD**, exclusiva e afirmativa que inclui PCD vão para o **topo da mensagem**
    (`prioritaria_para_pcd`, primeiro critério de `criterio_de_ranking`, só em memória), com o
    ponto a favor "Vaga exclusiva para PCD" ou "Vaga afirmativa que inclui PCD". A nota não muda
    e a prioridade só vale acima de `NOTA_MINIMA`: vaga PCD que não combina com o perfil segue
    fora. Nenhum peso mudou.
  - Quem **não informou** segue como antes: recebe tudo, sem prioridade, e a exclusiva ganha o
    aviso "Vaga exclusiva para pessoas com deficiência (PCD)".

  A classificação é regra em `domain/publico.py`, sem IA e sem mudar a extração. Quase toda
  menção a PCD é da empresa: das 1.003 vagas do banco em 16/09, 29 citam PCD, deficiência ou ação
  afirmativa e 25 são "PcDs são bem-vindas", "também extensivas para PCD", "sem distinção de
  deficiência". O erro que mais custa é marcar como exclusiva uma vaga comum, porque ela some em
  silêncio para quem respondeu não; a primeira versão fazia isso em 21 casos que a revisão
  reproduziu, entre eles a reserva legal ("haverá reserva de vagas para pessoas com deficiência,
  nos termos da lei"), comum em estágio público, e instituição que atende PCD ("Escola exclusiva
  para pessoas com deficiência visual"), o que tirava vagas de Pedagogia, Psicologia e
  Fisioterapia. Por isso:
  - **Exclusiva** exige que o sujeito seja esta vaga, no singular ("vaga", "oportunidade",
    "processo seletivo", "seleção", "inscrições"), seguido de "para PCD" ou de "exclusiva",
    "somente", "destinada" etc.; sem outro público logo depois ("e", "ou", "também", "Vaga para
    PCD: Não") e sem "não", "também", "nossas", "outras", "confira", "programa" ou "reserva"
    antes. Plural ("vagas para PCD") é cota ou outra vaga e não conta.
  - **No título**, PCD precisa ser um trecho inteiro ("Estágio - PCD", "(PcD)", "PCD | …") ou vir em
    "Estágio para PCD". "(PcDs são bem-vindas)", "PcD ou Ampla Concorrência" e "Educação para
    Pessoas com Deficiência" não contam.
  - **Afirmativa** exige "vaga afirmativa" ou "ação afirmativa" no singular, porque "ações
    afirmativas" costuma ser política da empresa; no título, "Afirmativa" sozinha basta. Os grupos
    vêm só do parêntese logo depois dessa expressão, com vírgula e nome de grupo: "(Barra da
    Tijuca)" e "políticas afirmativas (PCD, raça)" não viram lista.

  Resultado nas 1.003: 1 exclusiva, 1 afirmativa com PCD (MUDES), 2 afirmativas sem lista, 999
  gerais, igual à leitura manual das 29, antes e depois da correção.

  **Formatos que dizem não ser só de PCD** (16/09/2026, auditoria). "Vaga para PCD/Ampla
  concorrência", "Vaga para PCD (não exclusiva)" e "Vaga para PCD - Não" eram exclusivas: depois do
  termo a regra só via "e", "ou", " também" e ": não" ou "? não", e no título o trecho "Estágio -
  PCD - Não" ou "(PcD - não exclusiva)" bastava, sem olhar o que vinha depois do separador. Agora,
  logo depois de PCD, e também depois da sigla em "pessoas com deficiência (PCD)", a barra sempre
  tira a exclusividade ("PCD/Ampla", "PCD/Não PCD", "PCD/reabilitados"), e "também", "ampla",
  "preferencialmente", "N/A", "não se aplica", "não informado", "não PCD" e o "não" como resposta
  solta a tiram depois de qualquer sequência de espaço, hífen, dois-pontos, interrogação, vírgula,
  parêntese ou barra vertical (`SEM_OUTRO_PUBLICO_DEPOIS`). Resposta solta é o "não" seguido de fim
  de texto, ".", ";", ",", "|", ")", "/" ou " - " (`NAO_COMO_RESPOSTA_SOLTA`): "Vaga para PCD -
  Não", "PCD: Não." e "PCD - Não - Bolsa" são gerais, mas "Vaga exclusiva para pessoas com
  deficiência, não exigimos experiência" e "Vaga PCD: não é necessário experiência" seguem
  exclusivas, porque o "não" é de outra oração. A primeira versão desta correção aceitava "não"
  seguido de qualquer palavra e tornava geral essa vaga, que no `main` era exclusiva: quem respondeu
  não voltava a recebê-la. Quebra de linha não tem regra própria: coletores e enriquecimento juntam
  os espaços, e nenhuma das 1.003 vagas guardadas tem quebra. O trecho do título passa pela mesma
  regra depois do separador, e "não exclusiva" ou "não é exclusivo" até 60 caracteres depois do
  termo, sem ponto no meio, também tira. Seguem exclusivas "Vaga PCD: Sim", "Vaga exclusiva para
  PCD | Bolsa", "Estágio - PCD - Rio de Janeiro", "Estágio - PCD - Não requer experiência" e
  "Processo seletivo exclusivo para PCD. Atuação não exclusiva em TI.". Nas 1.003 vagas a
  classificação é a mesma do `main`: nenhuma usa esses formatos, e a leitura manual das 30 que citam
  PCD, deficiência, necessidades especiais ou ação afirmativa confere com ela. Limites aceitos, para
  o lado de não exclusiva: "e" logo depois do separador do título tira a exclusividade ("Estágio -
  PCD - E-commerce"), e a barra trata sinônimo ("PCD/PNE") como outro público. Seguem exclusivas,
  sem regra: "Vaga para PCD - aberta a todos", "PCD: Opcional", "( ) Sim (X) Não" e "não
  exclusiva" depois de ponto ou a mais de 60 caracteres.

  **Frase comum que virava vaga exclusiva** (18/09/2026, auditoria). O sujeito no singular era
  cobrado, mas não a posição dele na frase, e o trecho do título aceitava o termo por extenso. Duas
  famílias de frase, nenhuma delas vaga de PCD, tiravam a vaga de quem respondeu "não":
  - **PCD como objeto de uma atividade ou de texto institucional.** "Apoio ao recrutamento e
    seleção para pessoas com deficiência" é tarefa de RH, "igualdade de oportunidade para pessoas
    com deficiência" é discurso da empresa, e "divulgação de vaga para PCD" é a atividade do
    estágio. Agora o sujeito precisa **abrir a frase**: início do texto, ponto, dois-pontos, ponto
    e vírgula, exclamação, interrogação, barra vertical, parêntese, colchete, aspas, asterisco de
    markdown ou hífen de lista, com artigo ou demonstrativo opcional antes
    (`PADRAO_ABERTURA_DE_FRASE`, conferido em `a_vaga_e_o_sujeito`). Os separadores são os que os
    anúncios reais usam: a única exclusiva do banco vem de "- Requisitos solicitados pela empresa:
    Vaga de Emprego para Pessoas com Deficiência (PCD)", e a Adzuna junta as linhas, então o rótulo
    com dois-pontos e o marcador de lista são o que sobra da quebra. Deny-list de palavra antes,
    como a `PADRAO_CONTEXTO_QUE_ANULA`, não fecharia: o que precede é verbo ("garantimos", "mapear",
    "faz"), e verbo não tem lista.
  - **PCD por extenso como trecho do título.** "Estágio em Psicologia - Pessoas com Deficiência" é
    o público que o trabalho atende, e o mesmo título aparece em Pedagogia, Fisioterapia,
    Fonoaudiologia, Terapia Ocupacional, Serviço Social e Educação Física. O trecho solto conta
    agora só com a **sigla** ("Estágio - PCD", "(PcD)", "PCD | …"), que é a marca de vaga dos sites
    de emprego; por extenso só quando o título diz que é a vaga ("- Vaga Pessoas com Deficiência",
    "- Exclusiva para Pessoas com Deficiência"). "Estágio para Pessoas com Deficiência" não mudou,
    porque ali o "para" já dirige a vaga.

  Medido nas 1.095 vagas guardadas em 18/09: **nenhuma muda** (1 exclusiva, 1 afirmativa com PCD,
  3 afirmativas, 1.090 gerais, como no `main`), e as 36 que citam PCD, deficiência, necessidades
  especiais ou ação afirmativa foram lidas à mão e conferem. O defeito só aparece em corpus
  adversarial porque `vagas` guarda o que passou no pré-filtro de algum perfil, quase tudo de
  computação do Rio, e a vaga de Psicologia ou de RH que ele escondia não chega lá. Num corpus de
  18 contextos de atividade × 4 sujeitos × 3 grafias do termo, as 216 frases eram exclusivas e
  agora nenhuma é; nos títulos, 8 áreas × 3 separadores × 3 grafias, 72 eram exclusivos e sobram os
  24 da sigla. As guardas com as exclusivas legítimas (descrição e título) continuam passando.
  Limites aceitos: "Estágio em Psicologia - PCD" segue exclusiva, porque a sigla solta é a marca do
  site de emprego e distinguir os dois casos exigiria saber a área da vaga antes da extração;
  rótulo seguido de dois-pontos abre frase, então "Projeto de inclusão: seleção para pessoas com
  deficiência atendidas" segue exclusiva; e "Estágio para Pessoas com Deficiência Auditiva no CAPS"
  também, pela mesma forma da legítima. Para o outro lado, perde a exclusividade a frase que a diz
  no meio de outra ("Estágio em Marketing, vaga exclusiva para PCD" depois da vírgula, "Nesta
  seleção para PCD") e o título sem separador ("Estagiário de TI Vaga para PCD"); nenhum caso nos
  dados. Nada mudou no prompt, na nota, na prioridade nem nos avisos, e `VERSAO_DA_EXTRACAO` segue
  `7efdbc95`. Publicação: só o `radar/`, sem migration e sem deploy.

  É dado sensível (LGPD, art. 11, I): a pergunta é opcional, começa em "Prefiro não informar", diz
  ao lado para que serve, e a resposta não entra em evento, log, prompt nem export. O juiz monta o
  perfil campo a campo e não a recebe; a amostra de `descartes`, que leva `perfil_id`, calcula o
  descarte com o perfil sem a resposta, senão o motivo `exclusiva_para_pcd` diria quem respondeu
  não. Fechar o diálogo apaga a resposta junto com senha e e-mail, porque numa aba compartilhada
  a próxima pessoa a veria marcada. A política de privacidade ganhou o dado e a base legal, ainda
  como rascunho para aprovação. Vaza por dois caminhos aceitos: o ponto a favor "Vaga exclusiva
  para PCD" é gravado em `avaliacoes` de toda vaga pontuada, enviada ou não, e a mensagem no
  Telegram mostra que a vaga é para PCD.

  **O cadastro ficava nos metadados do Auth** (`0027`). O `signUp` manda o perfil em
  `raw_user_meta_data.cadastro_radar`; o gatilho da `0014` o copia para `cadastros_pendentes` e o
  apaga na confirmação, mas em 16/09 5 das 6 contas confirmadas ainda o tinham, e os metadados vão
  no token de sessão. A causa provável é o Auth regravar os metadados depois do gatilho. A `0027`
  põe um gatilho `before update` em `auth.users` que tira a chave de toda gravação depois da
  inserção (a inserção precisa dela para a cópia, e nada mais a lê) e limpou as contas antigas.
  Conferir depois do push: `select count(*) from auth.users where raw_user_meta_data ?
  'cadastro_radar'` deve dar zero. A identidade do Auth guardava outra cópia, que a `0030` tira
  (ver "Cadastro que não confirma o e-mail tem prazo").

  Publicação: `db push` da `0026` e da `0027` antes do merge, porque o `rodar` passa a ler a coluna
  e o site manda a chave, que a validação anterior recusa. Limites: vaga dirigida a outro grupo
  sem a palavra "afirmativa" ("exclusiva para mulheres") não recebe aviso; "ação afirmativa" no
  singular dentro do texto institucional gera aviso falso; afirmativa cuja lista não está entre
  parênteses logo depois da expressão não dá prioridade a PCD; exclusividade dita só no plural,
  sem sujeito ("Destinada a PCD.") ou só depois dos 500 caracteres da Adzuna escapa ou só é pega
  no pré-filtro da entrega, depois de a vaga ter sido extraída. Errar para esse lado é
  intencional: quem não é PCD recebe uma vaga a mais que não serve, em vez de perder em silêncio
  uma que serve.

## Auditoria adversarial de 08/09/2026 (noite): o que mais mudou

Três revisores independentes e uma medição em produção depois da expansão. Regras que ficaram:

- **Extração e nota.** `area_da_vaga` é normalizada no modelo e vira `None` se não está no
  catálogo — "Computação", "tecnologia" ou "" viravam área alheia (teto 35). O fator de interesse
  decide "mesmo campo" pelas subáreas da vaga contra as dos interesses (`AREA_DA_SUBAREA`), não
  pela área da vaga nem pelo curso: programa aberto a várias formações com subárea de computação
  ganhava aviso falso. O teto de 65 só vale para outro campo, área recusada ou vaga sem subárea
  reconhecida; outra subárea do mesmo campo não é presa a 65. Curso genérico aceito
  ("Engenharia", "Sistemas", "Negócios") vale se estiver inteiro no nome do perfil e o catálogo
  reconhecer o perfil. Qualificadores de nível saem da habilidade ("Excel avançado" → excel;
  "Office 365" → office), senão furavam a exclusão de Office em computação e não casavam fora
  dela.
- **Recusas e histórico.** Recusa no Telegram nunca cancela uma subárea escolhida no cadastro
  (a vaga recusada carrega várias subáreas). `avaliacoes` é upsert: a nota gravada acompanha as
  regras atuais, porque `baixar_meus_dados` a exporta. Subárea de outro campo gravada no banco é
  ignorada ao carregar o perfil; o site só envia as do curso atual e, sem catálogo, repete as
  salvas em vez de apagar.
- **Cache de extração com versão.** `modelo_extracao` guarda `modelo#hash(prompt+formato)` e a
  leitura filtra por ele: mudar prompt ou catálogo invalida o cache sozinho, sem depender de a
  validação rejeitar o formato antigo.
- **Prompt sem viés de TI.** Habilidades são "ferramentas, idiomas e habilidades", com exemplos
  de várias áreas; pegadinha é "área diferente da que o título sugere"; a lista das 12 áreas e as
  subáreas com rótulo vêm do catálogo.
- **Incidente das 16:13 de 08/09.** Primeiro run com o motor novo: cota gratuita do Gemini (20
  requisições) estourou porque 503 dividia o lote e multiplicava requisições; 0 de 36 vagas foram
  extraídas e o run "passou" enviando 13 vagas com notas antigas guardadas. Desde então 502/503/504
  esperam e repetem o **mesmo** lote (`AvaliadorIndisponivel`), e o resumo do Telegram e o stdout
  mostram "vagas sem extração" e "extrações não gravadas" — antes só o log sabia. Com o recálculo
  total do Igor, cota estourada hoje significa **zero envio**, e o resumo tem que denunciar.
  O **500** tem regra própria desde 13/09/2026 (`FalhaInternaDoAvaliador`): o lote repete a
  chamada uma vez, depois de 10 s, e se o 500 voltar é dividido como erro não temporário. Até
  então o 500 dividia o lote na hora, como erro comum; tratá-lo igual ao 503, na primeira correção,
  fazia um 500 persistente parar a extração inteira (0 de 30 contra 29 de 30), e o 500 costuma
  vir da própria entrada. Três esperas de 61 s custariam 30% do prazo por lote.

As habilidades sugeridas no cadastro vêm do catálogo por área (`Area.habilidades`) e são montadas
ao entrar na etapa de habilidades; a lista de computação é a mesma de antes. Curso sem área
conhecida não recebe sugestão alguma desde a expansão: oferecer `HABILIDADES_GERAIS` a quem o
catálogo não reconhece era sugerir a área errada, e o campo continua no catálogo sem leitor no
site. Habilidade também deixou de ser obrigatória — lista vazia significa "não informou", nunca
incapacidade, e o site limita 50 itens de 100 caracteres porque a `0018` cobra isso no banco.
O aviso "Área que você recusou" nomeia as subáreas pelo rótulo do catálogo.

Sabidos e não corrigidos: republicação por outra fonte com descrição curta pode reenviar;
o banco ainda aceita subárea de outro curso (mitigado ao carregar); a Jooble multiplica
consultas por termo (segue desligada). A chave por `id_externo` sem `fonte` foi corrigida em
10/09/2026, na rodada de confiabilidade.

## Segunda rodada de falhas reproduzidas (08/09/2026, fim de tarde)

Cinco falhas que a auditoria anterior deixou passar, cada uma reproduzida por um teste que
falhava antes da correção:

- **Lote perdia o que já tinha extraído.** A repetição por erro temporário envolvia o lote
  inteiro, inclusive a reextração uma a uma das vagas que o modelo omitiu. Um 429 numa única
  vaga omitida repetia o lote quatro vezes e descartava as extrações certas. Agora só a chamada
  à API é repetida (`_chamar_esperando_a_cota`) e cada lote acumula o resultado antes de a cota
  interromper; divisão do lote continua só para erro não temporário.
- **Nível básico satisfazia requisito avançado.** Tirar o qualificador de nível para comparar o
  nome fazia "Inglês básico" valer por "Inglês fluente" (nota 100). O nome segue comparado sem
  o nível; o requisito só é atendido se o perfil declara nível igual ou maior (básico 1,
  intermediário 2, avançado/fluente/nativo 3). Requisito sem nível aceita a habilidade conhecida;
  requisito com nível exige que o perfil declare o seu (Igor, 08/09 à noite: "Excel" no perfil
  não comprova "Excel avançado"). A lista na mensagem virou "Requisitos a conferir no seu
  perfil". No corpus antigo (só computação) apenas 4 de 202 extrações citam nível; em Direito e
  Administração é o padrão.
- **Falha parcial virava "nenhuma vaga compatível".** O silêncio só valia quando nenhuma
  candidata tinha extração; com parte extraída e nada acima da nota mínima, o usuário recebia
  uma conclusão que o sistema não podia tirar. Qualquer candidata sem extração segura a mensagem
  e volta a ser candidata no dia seguinte. **A retenção tem limite por vaga desde 13/09/2026**:
  uma vaga que nunca é extraída (resposta vazia, JSON inválido) segurava a mensagem todos os dias.
  A `0022` conta em `vagas.dias_sem_extracao` os dias distintos de Brasília em que a vaga terminou
  a execução sem extração; a mensagem só sai quando todas as candidatas não avaliadas já faltaram
  em 3 dias, e uma vaga nova sem extração continua segurando. Extração gravada zera a contagem.
  A primeira versão contava desde a última recomendação e soltava "nenhuma vaga compatível" já no
  primeiro dia de falha para quem tinha recebido vagas havia 3 dias, inclusive como primeira
  mensagem de quem criou o perfil antes de vincular. Registro que falha (banco sem a `0022`)
  mantém a retenção; o `testar-local` (`RepositorioDoModoLocal`) não segura. Uma queda do Gemini
  de 3 dias seguidos solta a mensagem no 3º dia; o resumo de operação mostra as vagas sem
  extração. Coleta incompleta também segura, por outro motivo: ver "Coleta resiliente".
- **Logout herdava áreas de interesse.** `#logout-account` limpava formulário e habilidades,
  mas não `areasEscolhidas`/`areasSalvas`, e a grade da etapa 4 é remontada a partir delas. O
  mesmo esquecimento vale ao trocar de conta dentro do formulário, onde as salvas eram reserva
  sem catálogo.
- **IA processava vaga já entregue a todos.** As candidatas iam para a extração antes dos
  envios; com o cache versionado por prompt, cada mudança de prompt reextraía o histórico
  inteiro. `candidatas_de_algum_perfil` agora consulta `ids_ja_enviadas` por usuário; falha ao
  lê-los mantém a vaga na extração, nunca o contrário (`atender_usuario_travado` reconsulta e
  segue estrito).

Lição de método: os quatro pontos do Igor e a auditoria anterior foram verificados lendo o
código e rodando a suíte que já existia — que só cobria o que já se sabia. Falha nova se
procura escrevendo o teste que a reproduz **antes** de mexer no código.

## Terceira rodada: auditoria com as vagas reais do banco (08/09/2026, noite)

Feita rodando pré-filtro, normalização de curso e nota sobre as 415 vagas e 202 extrações
guardadas, com 12 perfis sintéticos de áreas distintas, e validando SQL, Telegram e funções com
sondas executáveis. O que mudou:

- **"Tecnologia da Informação" virava `informacao`.** `normalizar_curso` tirava todos os prefixos
  de formação de uma vez, e "tecnologia" + "da" é prefixo. É o nome de curso mais citado nos
  anúncios reais (36 de 202 extrações); anúncio que aceitava só ele ficava incompatível (teto 35)
  para todo estudante de computação. A normalização agora tira um prefixo por vez e para no
  primeiro nome que o catálogo ou os sinônimos conhecem; o site espelha a regra, e
  `tests/fixtures/cursos_normalizados.json` trava a paridade dos dois lados, uma entrada por forma
  de escrever o curso. Entraram sinônimos vistos nos anúncios: Sistemas da Informação, SI, Redes, Data
  Science, T.I, Gestão da TI, Processamento de Dados. Em 10/09/2026 entraram Ciências Jurídicas
  e Ciências Jurídicas e Sociais: a vaga que aceitava só esse nome dava curso incompatível (teto
  35) a quem cursa Direito, e "Estágio em Ciências Jurídicas" caía no pré-filtro porque o padrão
  de direito só aceitava "jurídico"/"jurídica" no singular (achado na mensagem de um estudante de
  Direito do piloto). O plural vale no título e na exclusão, e "jurídica(s)" não conta depois de
  "pessoa(s) ", "pessoa(s)-", "física(s) e " nem "contas " (`JURIDICO_FORA_DE_PESSOA_JURIDICA`):
  "Crédito para Pessoas Jurídicas" é de finanças e "atendimento do público pessoa jurídica" é de
  agência bancária. Na descrição fica o singular, com a mesma trava. A trava só funciona porque o
  pré-filtro usa a normalização do catálogo, que junta espaços: até a segunda auditoria de 10/09
  ele tinha uma `normalizar` própria, e "Pessoas  Jurídicas" com espaço duplo escapava.
- **Termo de área na descrição exige contexto.** Título genérico era mantido por "com direito a
  bolsas" (Direito), "ramo: recursos humanos" na assinatura de agências (RH), "mercado
  financeiro" no blurb da empresa (Economia), "farmácia online" nos benefícios (Saúde). Nos dados
  reais, 7 de 7 vazamentos de Direito e 4 de 4 de RH eram assim. `descricao_e_da_area` aceita o
  termo só depois de contexto de formação ou de atuação ("área de", "rotinas de", "conhecimento
  em"); `menciona_o_curso` exige contexto de formação, inclusive para nome composto. Efeito
  medido: RH 19 → 11 candidatas, Enfermagem 5 → 2, computação 303 → 290, sem perder as listas
  "cursando engenharia mecânica ou produção".
- **Falha ao ler o histórico de um usuário derrubava o run.** `ErroDeArmazenamento` em
  `ids_ja_enviadas`, `recusas_do_usuario` ou `vagas_enviadas_recentemente` subia até `executar`.
  Vira aviso do usuário afetado, como já era para gravar e enviar.
- **Perfil híbrido ou indiferente recebia vaga presencial de outra cidade** (achado numa rodada
  de ponta a ponta com coleta real: pedagogia híbrida do Rio recebeu estágio em Palhoça/SC com
  nota 61 e sem aviso). O pré-filtro só conferia cidade para perfil presencial, e a logística
  vale 5 pontos. Agora, para quem não é remoto, vaga de outra cidade só fica se admite remoto
  (modalidade da fonte ou "remoto"/"home office" no texto); depois da extração, vaga presencial
  ou híbrida em outra cidade fica limitada a 30 com aviso próprio, como já acontecia com perfil
  remoto. Perfil presencial continua exigindo a própria cidade mesmo para vaga remota — desde
  10/09/2026, a própria cidade ou uma da mesma região imediata do IBGE.
  **Home-office com hífen e teletrabalho (16/09/2026).** O texto só contava como remoto com
  "remoto", "remote" ou "home office" com espaço (ou junto), então vaga de outra cidade que dizia
  "home-office" ou "teletrabalho" saía para híbrido, indiferente e remoto, e o perfil remoto via
  como presencial a vaga que citava a sede e o home-office. As duas grafias (e "tele-trabalho")
  entram no mesmo `PADRAO_TRABALHO_REMOTO`; perfil presencial não muda. Medido nas 1.003 vagas
  do banco com 448 perfis sintéticos (16 cursos, 7 cidades, 4 modalidades), somando a descrição
  guardada e a cortada em 500 caracteres: 134 pares de 4 vagas passam a ficar, e nenhuma é remota
  (3 híbridas pela extração, uma delas por "auxílio home-office"; a quarta só pede "disponibilidade
  para home-office"). É a imprecisão que a grafia com espaço já tinha com "auxílio home office"
  e "híbrido (home office e presencial)": entre as vagas da Adzuna do banco com remoto no texto e
  modalidade extraída, 22 são remotas, 16 híbridas e 3 presenciais. Depois da extração a híbrida
  de outra cidade fica em 30 e não é enviada, então o custo é extração. Limite da medição: `vagas`
  só guarda o que passou no pré-filtro de algum perfil, e 872 das 1.003 são do Rio, então a vaga
  de outra cidade que só dizia "home-office" quase nunca foi guardada e o ganho não aparece.
- **Estágio de mestrado ou doutorado chegava a graduando.** "Estágio de Mestrado em Economia"
  (EPE) foi a um perfil de Direito com nota 55, só com o alerta de pegadinha. Título com
  mestrado, doutorado ou pós-graduação sai no pré-filtro, como já saía "pleno" e "sênior".
  **Título que também aceita graduação (16/09/2026).** "Graduação ou Pós-Graduação", "Graduandos
  e Mestrandos" e "universitários e pós-graduandos" saíam como estágio de pós. A exceção vale só
  quando graduação, graduandos, universitários ou superior vem ligado ao termo da pós por "ou",
  "e", "/" ou vírgula, nas duas ordens (`PADRAO_GRADUACAO_JUNTO_DA_POS`). Não é a exceção do
  ensino médio, que aceita qualquer menção a nível superior: ela soltaria "Estágio de Mestrado no
  Hospital Universitário", "Mestrado em Engenharia - Graduação concluída" e "mestrandos da
  graduação", que seguem descartados. O banco tem 2 títulos com termo de pós (EPE, mestrado),
  nenhum muda; num corpus de 32 títulos, 12 deixam de sair, 11 com razão. Limites: "Estágio de
  Doutorado, graduação concluída" passa pela vírgula; "Graduação em Direito ou Pós-Graduação", com
  palavras no meio, continua saindo; e "Pós Graduação" com espaço nunca foi descartada.
- **Estágio de ensino médio chegava a universitário** (09/09, execução real com 12 perfis):
  "Vaga de estágio para estudantes de ensino médio" foi para Pedagogia com nota 60, porque
  "ensino" é sinal de educação no título. Título de ensino médio, nível médio ou jovem aprendiz
  sai no pré-filtro, exceto quando também diz superior, graduação ou faculdade ("Nível Médio e
  Superior" fica); e "ensino médio" deixou de contar como sinal de educação. Na coleta do dia,
  11 títulos assim entre 983.

Conferido e correto: as 20 constantes SQL e o `metricas.sql` passam por `EXPLAIN` contra o
schema real; mensagem com 7 vagas longas e `<`, `&` nos textos divide em partes abaixo de 4096
com tags fechadas; janela da entrega imediata é 09:23–10:23 UTC (06:23–07:23 de Brasília);
suítes das Edge Functions (8 + 24) e do cadastro (38) verdes; nenhuma ref remota alcança commit
do Claude.

**Sete:** o workflow manda até **7** vagas (`QUANTIDADE_VAGAS_ENVIADAS: "7"`, commit de 03/09,
porque com 5 slots vaga boa saía da janela sem ser enviada). A landing de 08/09 prometia "até
cinco"; Ian decidiu manter 7, a landing passou a dizer "até sete" e o PR #22 do Igor adotou o
mesmo valor no padrão do código, na copy e no plano de expansão.

## Rodada de confiabilidade (10/09/2026)

Correções de uma revisão externa, cada uma com o teste que reproduz a falha antes do conserto.
O que muda para quem opera:

- **A conexão do banco abre em `autocommit`.** Sem isso a primeira consulta abria transação
  implícita e os blocos `transaction()` viravam savepoints: nada era confirmado para outra
  conexão até o processo fechar. A mensagem chegava antes de o token do envio existir para o
  webhook, e a trava do perfil era liberada antes da confirmação. Nunca voltar `autocommit`
  para o padrão sem mover a fronteira da transação junto.
- **Vaga é `(fonte, id_externo)` em todo dicionário do fluxo**, e o `id_vaga` do prompt é
  `fonte:id_externo`. Antes, duas vagas com o mesmo número em fontes distintas viravam uma só e
  o mesmo anúncio era entregue duas vezes. O `id_vaga` guardado nas extrações antigas continua
  sendo só o número; a leitura não usa esse campo, usa as colunas.
- **A chave de duplicata inclui a cidade.** Duas vagas presenciais da mesma empresa e título em
  cidades diferentes viravam uma só antes do filtro por perfil, e quem era da outra cidade
  perdia a vaga em silêncio.
- **O prompt preserva o nível da habilidade.** Ele mandava apagar ("Excel avançado" → "Excel")
  enquanto o pontuador distingue nível desde 08/09, então requisito avançado passava por
  atendido. **Isso mudou `VERSAO_DA_EXTRACAO` de `ace8b756` para `7efdbc95`: a primeira
  execução depois do merge reextrai as candidatas e gasta cota.** Acompanhar o resumo das 07:23.
  `tests/test_contrato_extracao_pontuacao.py` cobre a fronteira; teste de etapa isolada não pega
  esse tipo de falha, porque cada lado passa sozinho.
- **Recusa corrigida deixa de penalizar.** As consultas de recusa por área e de vaga repetida
  liam todo evento negativo, inclusive o que a pessoa depois trocou por "essa serviu". Agora leem
  a última resposta por vaga, como as métricas já faziam. Os testes rodam em PGlite
  (`tests/web/recusas_test.ts`), lendo o SQL direto do `postgres.py`, então não dependem de
  banco de teste.
- **Negação não conta como exigência de experiência**: "não exigimos 2 anos de experiência" era
  descartado antes da IA. A negação vale só dentro da mesma frase.
  **Duração do estágio e negação depois (16/09/2026).** A Adzuna junta as linhas do anúncio, e
  "Duração: 2 anos" seguida do rótulo "Experiência" virava "2 anos experiência", que o regex lia
  como exigência porque o "de" era opcional: a vaga saía com ou sem "Experiência não necessária"
  depois. A exigência passou a ser "N anos de experiência" ou "experiência de N anos". E a negação
  só era lida antes, então "Experiência de 2 anos não é necessária" saía: ela vale também nas 4
  palavras seguintes, sem atravessar ponto, vírgula nem ponto e vírgula, senão "3 anos de
  experiência, não precisa ter carro" deixaria de sair. O banco não mede a regra: ela não depende
  do perfil, então `vagas` nunca guarda o que ela corta (zero vagas marcadas antes e depois). Num
  corpus de 34 frases, 13 deixam de sair: 10 com razão e 3 pioras aceitas, a exigência escrita sem
  o "de" ("3 anos experiência em vendas", "Mínimo 2 anos experiência", "5+ anos experiência"),
  gramaticalmente rara e que a nota ainda pesa pela experiência extraída. Seguem saindo, como
  antes: "não obrigatória" (fora do vocabulário da negação), "Desejável 2 anos de experiência" e o
  texto institucional "consultoria com 5 anos de experiência no mercado".
- **Falha de entrega temporária não pausa mais o perfil.** Só HTTP 403 e o 400 que nomeia o
  destinatário (`chat not found`, bot bloqueado) contam para `falhas_de_envio`. Indisponibilidade
  do Telegram e erro de formatação nosso viram aviso do dia. Além disso, resposta de erro sem
  corpo JSON levantava `JSONDecodeError` de dentro do `except` e derrubava a execução inteira,
  deixando sem mensagem quem vinha depois na fila.
- **Travessão no nome do curso.** O Python descartava caracteres fora do ASCII, então "Letras –
  Português" virava "letras portugues" e ficava sem área, enquanto o site já tratava travessão
  como hífen e gravava os interesses. macOS e iOS trocam " - " por " – " sozinhos. O inverso
  também acontecia: o site só conhecia o "–", e "Direito — Bacharelado" (travessão longo, que o
  macOS põe no lugar de "--") ficava sem área no cadastro e gravava o perfil sem interesses. Desde
  10/09/2026 o `normalizarTexto` do site espelha o `normalizar` do Python: os mesmos cinco traços
  viram hífen, caractere fora do ASCII sai e espaços se juntam; a fixture de paridade tem as formas.
  A mesma função serve a busca de cidade: apagar o que não é ASCII fez o apóstrofo curvo (’ ‘ ʼ)
  sumir ("d’Oeste" virava "doeste"), e as 47 cidades com apóstrofo digitadas assim deixaram de
  ser achadas; com "'" ou "´" continuavam funcionando. A correção fica em `textoDeBusca`, que
  é só da cidade e troca o apóstrofo curvo por espaço antes de normalizar. Pôr a troca em
  `normalizarTexto` quebrava a paridade do curso ("Pedagogia’" ficava sem área no site), e a
  fixture tem essas formas. Mudou `normalizarTexto`, teste a cidade junto com o curso.
- **`python -m radar descartes --amostra 30 --saida arquivo.json`** grava uma amostra do que o
  pré-filtro cortou, com o motivo, para rotular à mão. É o lado que o `julgar` não alcança: ele
  mede a vaga entregue, nunca a boa vaga que sumiu antes da IA.
- **As suítes rodam em pull request** (`.github/workflows/testes.yml`): pytest, ruff e as três
  suítes Deno. Os testes de integração Postgres continuam de fora, porque exigem o schema do
  Supabase.
- **O cliente supabase do site tem versão fixa** (`2.116.0`), não mais `@2`.

Não corrigido de propósito: os pesos da nota. A regra de não recalibrar sem `vaga_irrelevante`
real continua valendo. Perfil sem habilidade cadastrada recebia nota alta sem nada distinguir
compatibilidade observada de informação ausente; a resposta foi um aviso na mensagem
("Nota calculada sem habilidades no seu perfil"), não um peso novo.

## Entrega no Telegram (10/09/2026)

- **Falha no meio da mensagem não apaga o que chegou.** A mensagem de sete vagas vai em várias
  partes; se a segunda falhava, nada era gravado e no dia seguinte tudo voltava. O notificador
  informa quantas partes o Telegram aceitou, `recomendacoes_por_parte` diz quais vagas estavam
  nelas, e só essas entram no histórico. Efeito colateral aceito: o teclado de feedback fica na
  última parte, então vaga entregue numa falha parcial fica sem botão.
- **Texto vindo da fonte tem teto.** A divisão só corta no separador entre vagas, então um bloco
  grande passava de 4096 e o Telegram recusava a mensagem inteira com 400, que ainda contava como
  falha de envio do usuário. Título, empresa, localização, requisitos, pontos, avisos e alerta
  são cortados **depois** do escape, para não partir uma entidade HTML. Pior caso medido: 3216
  caracteres por bloco.
- **A data da mensagem é a de Brasília**, não a do UTC. Entrega imediata entre 21:00 e 23:59
  chegava datada do dia seguinte; o diário das 07:23 nunca mostrou o problema.
- **Vaga fechada na origem** (16/09/2026). "Estágio em Ti - Desenvolvimento de Sistemas - Rio"
  (Wilson Sons, adzuna:5885226961) foi publicada na Adzuna às 16:33 de 15/09, coletada e
  enriquecida às 07:25 de 16/09 com a descrição completa e enviada a duas pessoas às 07:25; horas
  depois o site de origem dizia "Esta vaga expirou", e a página da Adzuna continuava no ar com a
  descrição e "Candidatar-se". **O Radar não tem como saber que a vaga fechou**: a Adzuna não
  informa expiração e segue listando o anúncio, e conferir a origem exigiria seguir o link da
  Adzuna de forma automática, que é o clique que ela contabiliza. Reler a página da Adzuna antes
  de enviar não teria pegado este caso. A resposta é o feedback: "👎 Vaga encerrada"
  (`motivo_encerrada`) tira a vaga de todos no pipeline, antes da deduplicação, da extração e da
  entrega, desde que a mesma pessoa tenha aberto a vaga pelo link antes de marcar (`vaga_aberta`
  anterior) e que essa seja a última resposta dela à vaga nos últimos 30 dias
  (`SQL_VAGAS_ENCERRADAS`). O efeito é global porque vaga fechada está fechada para todos. Saem a
  vaga com a mesma fonte e número e as republicações dela (`remover_republicacoes_de`, a regra de
  "Já vi essa"), e o filtro roda antes da deduplicação: agregadores republicam com outro número, e
  a deduplicação fica com a versão de descrição maior, que escapava. Exigir a abertura só barra
  quem não abriu; o toque errado de quem abriu ("Já vi essa" fica logo acima) é tratado pelo
  aviso próprio, que diz que a vaga deixa de ser enviada e que tocar no número de novo desfaz.
  Falha ao ler as marcações só avisa no log. `motivo_encerrada` fica fora das recusas por grupo
  de extração e da concordância do `julgar`, que medem o ranking, e aparece na quebra por motivo;
  continua em `vagas_irrelevantes` e na última resposta da utilidade (ver `docs/metricas.md`).
  Limites: quem recebe a vaga no mesmo envio de quem a marcou não é protegido; link encaminhado a
  outra pessoa grava `vaga_aberta` no perfil de quem recebeu a mensagem; e teste com conta da
  equipe em vaga real tira a vaga de todos se a marcação não for desfeita (o roteiro do guia
  avisa). Publicação: `supabase functions deploy telegram-webhook`, porque o teclado e o aviso
  são da função; o `radar/` não precisa de migration.
  **Quem pode tirar a vaga de todos (16/09/2026).** Uma marcação bastava, e daí saíam três
  defeitos: uma pessoa, ou uma conta de teste esquecida, podia marcar em série as vagas que recebeu
  e esvaziar as mensagens dos outros por 30 dias; a marcação de conta excluída seguia valendo durante
  a carência; e a republicação espalhava o voto, porque texto padrão de agência nas 40 primeiras
  palavras junta vagas de empresas diferentes com o mesmo título e cidade. Agora a marcação tem dois
  alcances:
  - **Quem marcou deixa de receber, sempre.** A última resposta "Vaga encerrada" dos últimos 30 dias
    entra em `SQL_VAGAS_QUE_NAO_VOLTAM`, junto com "Já vi essa", sem exigir abertura e em qualquer
    estado da conta, e a vaga e as republicações dela pela regra ampla deixam de chegar à pessoa. O
    envio já a barrava pelo número, mas pela republicação só até 30 dias depois do envio.
  - **Os outros, com três condições** (`SQL_VAGAS_ENCERRADAS`). Abertura pelo link antes da
    marcação, como antes. Perfil existente e sem exclusão: a conta apagada já perdia os eventos em
    cascata, e excluir suspende o efeito, que volta se a exclusão for cancelada. Pausada ou sem
    Telegram segue valendo, decisão do dono: essa conta não recebe vagas nem consegue votar, e a
    marcação que conta foi dada com a conta ativa (a primeira versão desta correção a tirava, porque
    a conta não consegue desfazer o voto). E só as `MARCACOES_DE_ENCERRADA_QUE_VALEM_PARA_TODOS` (3)
    primeiras marcações vigentes do perfil em 30 dias, em ordem de `ocorrido_em` com a vaga
    desempatando; da quarta em diante a marcação vale só para quem marcou, e a vaga que já saiu para
    os outros não volta quando a pessoa marca mais uma (a primeira versão anulava todas, também
    decisão revista pelo dono). Marcação sem abertura ocupa lugar na ordem, sem sair para os outros.
    Desfazer uma marcação a tira da ordem e a seguinte sobe; remarcar a põe no fim. A republicação
    só sai para todos se for da mesma empresa ou de empresa sem nome
    (`republicacao_da_mesma_empresa`, com `EMPRESAS_NAO_IDENTIFICADAS`, como na chave de duplicata).

  Medido no banco em 16/09: há 1 marcação, de conta ativa que abriu a vaga antes, e ela continua
  valendo para todos; nenhuma vem de conta excluída ou pausada, e a vaga não tem republicação
  guardada. O teto: 1 marcação em 31 vagas abertas pelo link, e o perfil que mais abre abriu 20 em 10
  dias, cerca de 60 por mês, o que dá 3 marcações mesmo com 5% de vagas fechadas; a mensagem tem até
  7 vagas, e da quarta marcação em diante, mesmo de uma mensagem só, o efeito fica com quem marcou.
  A empresa: das 307 vagas já enviadas, as que podem ser marcadas, 49 têm republicação entre as 1.003
  guardadas, 134 no total; com a regra da empresa, 39 e 74. As 60 que deixam de sair para todos foram
  conferidas à mão e são todas o mesmo anúncio com outro rótulo de empresa (BuscarVagas e Divulga
  Vagas, "Ltda" a mais, "Oportunidades Petros"). É o custo aceito: essa cópia chega uma vez a quem não
  marcou, visível. Nenhum par de empresas realmente diferentes com o mesmo título e cidade passa de
  0,31 de semelhança nas 40 primeiras palavras, então a proteção ainda não evitou um caso real.
  Limites: as agências (Fundação Mudes, CIEE, Nube) aparecem com o próprio nome na empresa, e entre as
  vagas delas só o texto separa, como antes; cada conta ainda tira até três vagas de todos por 30
  dias, e contas combinadas somam; marcação errada de conta pausada ou desvinculada não tem como ser
  desfeita até a conta voltar; quem recebe a vaga no mesmo envio segue sem proteção; e marcar sem
  abrir gasta um dos três lugares. A contagem de `motivo_encerrada` nas métricas deixa de ser o
  número de vagas tiradas de todos (`docs/metricas.md`). O teste em PGlite lê as constantes inteiras
  de `postgres.py` para montar a consulta, porque o teto entra nela como literal. Publicação: só o
  `radar/`, sem migration e sem deploy de função; o aviso do bot ("Essa vaga deixa de ser enviada")
  segue verdadeiro para quem marcou.

## Erro inesperado não derruba os outros usuários (18/09/2026)

Auditoria dos médios "o run inteiro cai por causa de um único dado". `atender_usuario` e
`executar_fluxo` só tratavam os quatro erros de domínio (`ErroDeColeta`, `ErroDeAvaliacao`,
`ErroDeNotificacao`, `ErroDeArmazenamento`), então qualquer outra exceção vinda de um perfil ou de
uma vaga deixava sem mensagem todo mundo da fila, inclusive quem já tinha sido atendido, cujo
retorno se perdia, e sem aviso de operação. A rede de segurança tem dois níveis:

- **Por usuário.** O laço de `executar` envolve `atender_usuario`: `Exception` vira
  `logger.exception` com o traceback e o usuário fica sem entrega, como já era o erro de envio e o
  de gravação. O resumo de operação ganhou "⚠️ Sem entrega por erro inesperado: N (veja o traceback
  no log)" e o `stdout` traz o mesmo número; o campo é
  `ResumoDaExecucao.usuarios_sem_entrega_por_erro_inesperado`.
- **Da execução.** Qualquer `Exception` que suba do pipeline vira o mesmo aviso de falha que os
  quatro erros conhecidos, com o nome do tipo na frente da mensagem, e segue subindo. Sem isso o
  dono só descobria a queda olhando o log do Actions.

`KeyboardInterrupt`, `SystemExit` e as demais `BaseException` continuam subindo sem virar aviso,
porque interrupção não é defeito de dado; por isso a `ExecucaoInterrompida` dos testes de entrega
imediata, que imita um kill, passou a herdar de `BaseException`.

Os quatro casos reproduzidos pela auditoria foram corrigidos também na origem, cada um com o teste
que falhava antes:

- **Telegram com corpo de erro que não é objeto JSON.** `descricao_do_erro` chamava `.get` no que
  `resposta.json()` devolvesse; um proxy respondendo `"Bad Gateway"`, uma lista ou um número dava
  `AttributeError` de dentro do `except` do `HTTPStatusError`. Corpo que não é objeto cai agora no
  mesmo texto cru que já servia ao corpo que nem é JSON.
- **URL malformada de uma vaga.** `urlsplit` levanta `ValueError` com colchete de IPv6 aberto
  (`https://[oops/vaga/1`), o que derrubava a formatação da mensagem (`dominio_da_vaga`) e o
  enriquecimento (`aponta_para_anuncio_land_ad`); e `httpx.InvalidURL`, que não é `HTTPError`,
  escapava do `except` do enriquecimento (porta inválida, caractere não imprimível, URL longa
  demais). Domínio ilegível volta a cair no nome da fonte, caminho ilegível vale como caminho
  vazio e a URL que o httpx recusa entra no aviso das páginas que falham: a vaga segue com os 500
  caracteres da API. O link continua apontando para a URL como veio.
- **Gemini com resposta que o SDK não lê.** O tratamento de 16/09 cobria corpo que não é JSON e
  envelope fora do formato, mas gzip corrompido (`httpx.DecodingError`) e excesso de redirect
  (`httpx.TooManyRedirects`) são `RequestError` e não `TransportError`, e `parts` como objeto no
  lugar de lista vira `AttributeError` dentro do pydantic do SDK. Os três viram
  `AvaliadorIndisponivel`, o tratamento do 503: espera e repete o mesmo lote dentro do prazo. A
  mensagem da falha de rede passa a nomear o tipo. `VERSAO_DA_EXTRACAO` segue `7efdbc95`.
- **Número gigante no pré-filtro.** `int()` recusa texto com mais de 4.300 dígitos desde o Python
  3.11, e o padrão de anos de experiência captura `\d+` sobre a descrição inteira. Número com mais
  de 4 dígitos passa a ser ignorado em vez de convertido; nenhum descarte muda, porque a faixa que
  descarta é de 2 a 9 anos.

O que a rede **não** cobre: exceção fora do laço por usuário (coleta, deduplicação,
enriquecimento, extração, leitura dos ativos, apagamento de contas) segue derrubando a execução
inteira, agora com aviso de operação — é o preço de essas etapas serem uma só para todos. Exceção
depois do pipeline (registro do uso da Adzuna, leitura dos eventos do site, formatação e envio do
resumo) fica fora do `try` e não vira aviso. Se `liberar_atendimento` falhar depois de a mensagem
sair, o retorno se perde e a pessoa é contada como sem entrega, embora tenha recebido. E o aviso é
enviado pelo próprio notificador: se ele também quebrar, o run morre com o traceback dos dois
erros encadeados, sem mensagem no Telegram. O código de saída do processo não mudou.

## Cidades vizinhas: região imediata do IBGE (10/09/2026)

Quem mora em Niterói trabalha no Rio, mas a cidade era comparada pelo nome exato. Nos 30 dias
anteriores, 448 vagas chegaram como "Rio de Janeiro" e 1 como "Niterói": um perfil presencial de
Niterói praticamente não recebia nada. A Adzuna ainda rotula pela região, e "Estágio TI - Niterói"
veio como Rio de Janeiro.

`domain/regioes.py` classifica vaga × perfil em mesma cidade, mesma região imediata do IBGE ou
distante, lendo `radar/domain/regioes_imediatas.json` (510 regiões, gerado por
`scripts/gerar_cidades.py` junto com a lista do site). O que muda:

- **Mesma região vale como a cidade** no pré-filtro e na trava de 30 para híbrido e indiferente.
- **Na logística vale metade** da cidade, cerca de 2,5 pontos a menos: a própria cidade continua
  na frente, sem enterrar a vizinha.
- **A coleta busca também a maior cidade da região** do perfil (Adzuna `where`),
  senão um perfil de Niterói sozinho dependeria de haver alguém do Rio para as vagas do Rio
  serem coletadas.
- **O juiz recebe as cidades da região** no perfil; sem isso ele marcaria `logistica` na vaga
  do Rio para quem é de Niterói.
- **O estado da vaga é lido nos formatos das fontes** ("Estado do Rio de Janeiro", "Rio de
  Janeiro", "RJ"). Sem estado, vale o nome quando ele só existe num estado; perfil antigo
  "Rio de Janeiro" continua achando a região. Nome igual em estados diferentes deixou de ser a
  mesma cidade.

Limite conhecido: a região imediata do Rio tem 21 municípios e inclui Saquarema e Mangaratiba, a
cerca de 100 km. Se o feedback "local ou modalidade" apontar esses casos, o ajuste é uma lista de
exceções ou a região metropolitana, não voltar ao nome exato.

## Juiz de recomendações: LLM as a judge (09/09/2026)

`python -m radar julgar --dias 7 --amostra 30` pede a um **segundo modelo** que julgue, às
cegas, uma amostra das entregas recentes: para cada vaga enviada, `relevante`, `nota_juiz`,
`problema` (catálogo fechado: outra_area, exige_demais, logistica, repetida, anuncio_fraco,
nenhum) e um motivo. O juiz vê o perfil e o anúncio completo, **nunca a nota do Radar**, para o
julgamento ser independente. O relatório (`reporting/julgamento.py`) traz relevância por perfil,
problemas, concordância com o feedback das pessoas quando existir, e as vagas reprovadas pelo
juiz com nota do Radar acima de 70 — a lista que interessa para revisar regra.

O modelo vem de `JUIZ_MODELO` (padrão `claude-sonnet-4-6`, outra família que a do extrator)
e o adapter segue `AVALIADOR`: `agy` local, sem cota; pela API precisa ser um modelo Gemini. O
comando só lê o banco; nada de nota alterada. Só pontuação por regra em Python decide o que é
enviado — o juiz mede, não ranqueia. Antes de usar o número do juiz como evidência, ele precisa
ser validado contra o gabarito humano de 20 vagas (pré-PRD, H2); abaixo de 75% de concordância
é ruído com cara de número.

Primeira rodada real (09/09, `claude-sonnet-4-6` pelo `agy`, 24 de 168 entregas de 14 dias, 5
minutos): 12 relevantes, mediana do juiz 39 contra 69 do Radar. As cinco reprovadas com nota
alta eram todas de 28 a 31/08, antes das regras de área, interesse e cidade — o relatório mostra
a data de cada uma por isso. Limitação que o juiz expôs: a Adzuna informa a região, não a
cidade ("Estagiário de TI - São Gonçalo" vem como "Rio de Janeiro"); 1 caso em 168 envios,
registrado, sem regra nova.

Desde 10/09/2026 o comando **falha com código 1** quando nenhuma entrega é julgada, imprimindo
o último erro do avaliador. Antes, o padrão `gemini_api` + `claude-sonnet-4-6` devolvia
relatório vazio com código 0, o que parecia execução limpa. O `--gabarito` também avisa quantos
rótulos ficaram fora da janela de `--dias`, em vez de descartá-los em silêncio.

O gabarito humano nasce de `python -m radar gabarito --dias 2 --amostra 20 --saida arquivo.json`:
o arquivo lista as entregas com `relevante: null` para cada pessoa preencher com true ou false;
`julgar --gabarito arquivo.json` julga só essas e imprime a concordância juiz × pessoas. O
primeiro arquivo, com 20 entregas de 08 e 09/09, saiu do Git em 12/09 porque trazia vagas reais e o
`perfil_id` de cada usuário: fica em `gabaritos/`, ignorada, e vai em privado a quem for rotular.

## Quarta rodada: auditoria após a reescrita do `main` (09/09/2026)

O `main` foi reescrito por force push (rebase sobre a PR de estilo e o README). Antes de
auditar, os 13 commits locais foram conferidos por patch-id contra o novo histórico (todos
presentes), o site publicado já servia a nova versão e as quatro suítes passaram. O que a rodada
achou, com coleta real (823 vagas), banco e juiz:

- **Rótulo de subárea entrava no regex de título.** `PADROES_DE_TITULO` junta marcadores, nomes
  de curso e rótulos das subáreas; o rótulo "Segurança" de computação aceitava "Estágio Técnico em
  Segurança do Trabalho" para Engenharia de Software (nota 58, sem menção a curso). Nove títulos
  da coleta, todos de segurança do trabalho. O rótulo virou "Segurança da informação", que já era
  o marcador da área; os outros rótulos só aceitavam títulos coerentes com a área.
- **Contexto de formação atravessava o fim da frase.** "Estagiário na área de gestão financeira
  (Barra). O grupo atende marketing e comunicação" contava "marketing" como curso citado, porque
  "área de" estava a 20 palavras. A janela de contexto (formação e atuação) agora começa no último
  ". " antes do termo. Medido: zero pares (curso, vaga) mudaram em 12 cursos × 823 vagas; só o
  caso encontrado deixa de passar. "; " e quebra de linha não são fronteira porque listas de
  cursos usam os dois.
- **Perfil remoto recebia vaga de outra cidade sem modalidade a 88, sem aviso.** O pré-filtro
  ignorava a cidade para perfil remoto e a logística vale pouco; Administração remota no Rio
  recebeu Fortaleza, Belo Horizonte e Itajaí "modalidade não informada" nas primeiras posições.
  Agora perfil remoto segue a mesma regra do híbrido: vaga de outra cidade só fica se admite remoto.
  Medido para um perfil remoto do Rio em 11 cursos: 947 → 265 candidatas; das 260 descartadas com
  descrição truncada que puderam ser completadas, 18 (7%) citam remoto só no texto completo — a
  mesma limitação que o híbrido já tinha, registrada abaixo. Nenhum usuário atual é remoto.
- **`julgar --gabarito` com arquivo ausente ou inválido** estourava traceback; vira
  `ErroDeArmazenamento` com mensagem e saída 1.

O que foi verificado e não precisou de regra: os 8 envios de outra cidade para perfis presenciais
são todos do run das 07:23 de 08/09, antes da trava das 23:47; o run de 09/09 não tem nenhum. O
juiz (14 de 48 entregas de 2 dias) reprovou com nota alta só casos de 08/09 pela mesma razão,
mais "Estágio em TI" de infraestrutura para Engenharia de Software (subárea de computação; o
interesse do perfil decide) e um anúncio que lista Informática, Computação e ADS sem citar
Engenharia de Software (cursos intercambiáveis por decisão).

Pendências que esta rodada deixou anotadas: (1) refiltrar as candidatas depois do enriquecimento
e antes da extração recuperaria os 7% de vagas remotas que só dizem isso após os 500 caracteres da
Adzuna, sem gastar extração; (2) "Banco de Talentos" não é vaga aberta e chega como estágio;
(3) a Adzuna informa região, não cidade.

## Cobertura das fontes (30/08/2026)

A Adzuna classificava 93% das vagas brasileiras como categoria "Unknown", então `category=it-jobs`
escondia quase tudo (55 vagas em 5 dias no país inteiro). A busca passou a ser por termos, sem
categoria, repetida por cidade de perfil presencial, híbrido ou indiferente (desde 10/09/2026
também pela maior cidade da região imediata do perfil; remoto não acrescenta cidade); a localização vem de
`location.area` (cidade, estado), então bairro não quebra o filtro de cidade. A Gupy deixou de
buscar por termos no título e traz todos os estágios do país e da cidade. Efeito medido: perfil
Rio presencial saiu de 2 para 55 candidatas em um dia.

Paginação da Adzuna (08/09/2026): a busca por termos das áreas cadastradas encontra 4.988 vagas,
mas `LIMITE_DE_PAGINAS_POR_REGIAO` puxava 4 páginas de 50 por região — 4% do disponível, e esse
teto era repartido entre os cursos conforme a base crescia. A página 15 ainda devolve 50 vagas
cheias e relevantes, então o limite subiu para 10. Medido no Rio com quatro áreas: 699 vagas
coletadas contra ~400, e cada curso ganhou de 65% a 120% mais candidatas. Subir páginas é
preferível a buscar por área separadamente: o custo fica plano (10 chamadas por região) em vez de
multiplicar por curso.

Agregadores (Divulga Vagas, BuscarVagas) republicam o mesmo anúncio com "empresa" diferente:
`remover_republicacoes` em `filtering/duplicatas.py` une vagas com mesmo título e cidade cujas 40
primeiras palavras da descrição coincidam em 80% — só o início conta porque a Adzuna trunca a
descrição em 500 caracteres. A mesma regra bloqueia republicação entre dias (04/09/2026): a
candidata é comparada com as vagas enviadas ao usuário nos últimos 30 dias, porque o id novo do
repost furava o anti-repetição por id. Duplicata entre fontes: fica a versão que informa
modalidade e, em empate, a de descrição mais longa.

**Duplicata que não era a mesma vaga (16/09/2026).** A deduplicação juntava vagas diferentes em
três casos, e a pessoa perdia uma delas sem aviso:
- **Empresa sem nome.** Com "Empresa não informada", "Confidencial", "Empresa Confidencial" ou
  empresa vazia, a chave título + empresa + cidade virava só título e cidade. Nas vagas guardadas,
  "Estágio Em Administração - Recrutamento Aberto" tinha cinco anúncios de descrições diferentes, e
  todos viravam um. Para essas empresas (`EMPRESAS_NAO_IDENTIFICADAS`) a chave leva também a
  descrição normalizada inteira: o mesmo anúncio repetido segue unido pela chave, mesmo com menos de
  20 palavras, que a republicação não compara, e o texto parecido segue unido pela republicação.
- **Símbolo no título.** A limpeza trocava por espaço tudo que não é letra ou número, e "C#", "C++"
  e "C" viravam "c". "#" e "++" colados ao fim da palavra agora fazem parte dela; caixa, acento e o
  resto da pontuação seguem ignorados ("C#/.NET" é "c# .net").
- **Cidade sem estado.** A chave usava o nome antes da vírgula, e "Bom Jesus, PI" era "Bom Jesus,
  RS" (240 nomes de município existem em mais de um estado). As chaves usam `identificar_municipio`
  de `domain/regioes.py`: o estado vale nos formatos das fontes e, sem estado, vem do nome quando ele
  só existe num estado, então "Niterói" segue igual a "Niterói, Estado do Rio de Janeiro".

Símbolo e cidade valem também para a republicação e, com ela, para "Já vi essa", as enviadas nos
últimos 30 dias e "Vaga encerrada"; a empresa não, porque a republicação já não a olha (o efeito de
"Vaga encerrada" para os outros passou a olhar, ver "Vaga fechada na origem"). Medido nas
1.003 vagas guardadas, com a regra do `main` e a nova sobre o conjunto e sobre janelas que imitam
uma execução (vagas publicadas nos 4 dias antes de cada dia de coleta): o conjunto passa de 879 para
888 vagas únicas, e 8 das 20 janelas, todas de 08 a 16/09, ganham de 1 a 6. Os 17 grupos desfeitos
são todos de empresa sem nome e foram conferidos à mão: nenhum par com descrição igual ou parecida
se separa, nenhum par com descrição diferente se junta, e o anúncio repetido (restaurante, suporte
nas lojas, "Auxílio nas atividades administrativas") continua um só. O filtro entre dias bloqueia os
mesmos 100 pares de enviada e candidata, e a única vaga encerrada não tira nada a mais nem a menos.
Símbolo e cidade não mudam nenhum grupo nos dados, porque `vagas` guarda só o que passou no
pré-filtro de algum perfil, quase tudo do Rio, e só um título tem C#: ficam cobertos pelos testes.
Limites aceitos: nome repetido sem estado ("Bom Jesus") não é unido a estado algum, então a mesma
vaga pode chegar duas vezes em vez de sumir; empresa sem nome que repete o anúncio com texto curto
e diferente também chega duas vezes; agência com nome que anuncia vagas de clientes com o mesmo
título continua juntando vagas distintas (numa janela de 14/09, a Fundação Mudes juntou "Estágio em
Administração" de uma empresa de vistorias e de uma de engenharia), e tratá-la como empresa sem nome
separaria a vaga que a empresa republica com texto reescrito; outro rótulo de empresa escondida
("Sigilosa") segue valendo como nome; e "T.I" e "TI" continuam chaves diferentes, como antes.

## Correções da revisão de expansão (08/09/2026)

- Cursos passam por correspondência integral após remover prefixos de formação; aliases
  explícitos estão no catálogo e no JSON gerado. Medicina Veterinária fica desconhecida,
  não herda saúde humana; Gestão Financeira tem alias em finanças.
- Perfil sem área reconhecida **soma** uma busca geral (Adzuna sem `what_or`, Jooble com
  "estágio" puro) à busca dirigida dos cursos conhecidos, em vez de substituí-la. Trocar a de
  todos custava 68% das candidatas de computação e 66% das de Direito no Rio (167→54, 116→40),
  porque o `what_or` é o que ordena as 500 primeiras da fatia nacional. Termos de busca são
  palavras soltas: a Adzuna trata `what_or` como OR por palavra, então "recursos humanos" virava
  "recursos" OU "humanos" (1546 vagas contra 1185 da frase); o catálogo usa "recrutamento",
  "rh", "exportação".
- Curso mencionado na descrição com contexto de formação, ou abertura a qualquer formação,
  mantém a vaga para análise mesmo com título de outra área. A compatibilidade de curso é
  decidida após a extração.
- Pontuação é recalculada em Python em toda execução. Notas persistidas não são reutilizadas;
  extrações continuam compartilhadas e histórico de envios continua bloqueando repetição.
- Curso genérico aceito pelo anúncio ("Engenharia", "Química", "Administração") conta como o
  curso específico do perfil quando o nome aceito aparece inteiro dentro do nome do perfil **e**
  o catálogo reconhece o perfil. Sem a segunda condição, "Medicina" valeria para Medicina
  Veterinária — que é desconhecida de propósito. A correspondência integral sozinha marcava
  como incompatível (teto 35) quem estuda Engenharia Civil numa vaga "cursando Engenharia".
- A correspondência integral roda depois de `normalizar_curso`: tira prefixos de formação
  ("Cursando", "Graduação em", "Curso Superior de Tecnologia em"), sufixos ("completo",
  "- Bacharelado", "(Bacharelado)", "/Eletrônica"), aplica sinônimos ("Ciências Econômicas" →
  economia, "ADS", "TI", "RH") e devolve vazio para termo genérico ("Ensino Superior",
  "qualquer curso") — que em `cursos_aceitos` não comprova elegibilidade sozinho. Só abertura explícita
  a qualquer curso libera todas as formações; termos genéricos não anulam cursos específicos. "Licenciatura em X" sem
  alias cai em educação. Prefixos, sufixos, sinônimos e genéricos vão no `areas.json` e o site
  aplica a mesma regra. Nome que ainda não está lá vira área desconhecida: recebe só título
  genérico, busca geral e nota parcial. Ao ver um curso frequente cair nesse caso, o conserto é
  um alias.
- **Curso aceito fora do catálogo** (16/09/2026). Na vaga, nome que o catálogo não reconhece não
  tem área, e a lista feita só desses nomes dava curso incompatível, teto 35 e "Exige formação de
  outra área". Nas 566 extrações da versão `7efdbc95` com os 4 perfis ativos, 62 dos 2.264 pares
  caíam nisso. Conferidos à mão: 50 estão certos (vaga de ensino médio ou EJA, 16; só para
  técnico, 4; lista técnica em que a IA tirou o "Técnico em" dos itens seguintes, 12; nome de
  outra formação para quem não é dela, 18), 10 eram sinônimo que faltava ("ADM" para
  Administração; "Tecnologia", "Tecnologia/Sistemas", "Cibersegurança" e "Sistemas para a
  Internet" para computação) e 2 são erro da extração: adzuna:5882923702 pede "TI, Estatística,
  Matemática, Engenharias" e a IA guardou só Estatística e Matemática. Fora dos 62, lista mista
  escondia mais 3 pares ("T.I, ADM" de Administração e "desenvolvimento de software ou
  administração" de computação). A correção são sinônimos: "ADM", "Tecnologia", "Cibersegurança",
  "Sistemas para a Internet" e "Desenvolvimento de Software", mais "Rede de Computadores" e
  "Análise de Sistema", que estão em 7 vagas e só passavam porque a lista trazia outro curso de
  computação. **A regra não mudou.** Tratar como parcial (teto 75) a lista sem nome reconhecido
  subia 22 pares que passam no pré-filtro, 12 certos e 10 errados (ensino médio para Administração
  a 54, técnico em automação e em mecânica para computação de 43 a 53); mesmo tirando ensino médio
  e técnico, levava a vaga que pede Engenharia a Administração (54) e a de Estatística e Matemática
  a Medicina Veterinária (59). Os nomes fora do catálogo nas vagas são quase todos curso de outra
  formação (Estatística em 13 vagas, Matemática em 11, Ciências Sociais, Design de Moda,
  Biblioteconomia), a família "Engenharia(s)" (28 vagas), que `mesmo_curso` já resolve para quem é
  de engenharia, ou nível de ensino, e para eles o 35 está certo;
  `test_nome_fora_do_catalogo_de_outra_formacao_segue_incompativel` impede relaxar a lista inteira.
  Medido contra o `main` com 43 perfis (os 4 ativos e 39 sintéticos, 24.338 pares): 75 pares mudam,
  todos sobem, 55 passam no pré-filtro e cruzam a nota mínima, e nenhum descarte muda. Nos 4 ativos
  são 13 (35 → 51 a 80), 11 entregáveis; agrupando por dia de coleta, sem histórico, a vaga de
  Ciência de Dados que aceita "Tecnologia" entraria no top 7 dos dois perfis de computação em 11/09
  e a de estágio administrativo que aceita "ADM" no de Administração em 12/09. Sinônimo não entra
  no padrão de título, mas o composto entra em `nomes_do_curso`: quem cursa Sistemas para Internet,
  Desenvolvimento de Sistemas, Redes de Computadores ou Análise de Sistemas passa a achar também a
  forma nova citada na descrição. Limites: "Curso Superior de Tecnologia" e "Graduação em
  Tecnologia" sozinhos passam a valer como Tecnologia da Informação (nenhum caso nas 790
  extrações); o erro da extração segue, porque a correção é de prompt e muda `VERSAO_DA_EXTRACAO`;
  grafia errada ("Administação") e "Administração Bacharelado" seguem desconhecidas e hoje só
  aparecem ao lado de um nome reconhecido ("Eng. Elétrica" passou a valer pela expansão de
  abreviações do item seguinte); e nome novo continua dando 35 até ganhar alias.
- **Curso com pontuação, complemento ou abreviação** (16/09/2026). "Ciência da Computação.",
  "Direito, UERJ" e "Eng. de Software" ficavam sem área: `normalizar_curso` só cortava o
  complemento depois de hífen, barra, "|" ou de parêntese que fechava o nome, e não conhecia
  abreviação. O site não dizia nada à pessoa. Agora a normalização tira a pontuação das pontas,
  corta a partir de vírgula e de parêntese no meio do nome ("Psicologia (UFRJ) - noturno") e
  expande "Eng", "Adm", "Ciên", "Ciênc" e "C" no começo do que sobra depois dos prefixos de
  formação, com ponto ou espaço e só com outra palavra depois (`ABREVIACOES_DE_FORMACAO`, que vai
  no `areas.json`): "Graduação em Eng. Elétrica" chega a engenharia elétrica. As de ciência viram
  "ciencias", que os sinônimos levam a ciência da computação e que fecha com Contábeis,
  Econômicas, Atuariais, Biológicas e Jurídicas; "C. de Dados" segue desconhecido. Abreviação
  sozinha não expande: "Eng." solto segue desconhecido, e "ADM" solto vale como Administração pelo
  sinônimo do item anterior. O site espelha a regra e a fixture de paridade ganhou as formas. Um fuzz de
  5.150 entradas (catálogo, sinônimos, os 296 `cursos_aceitos` reais e variações com pontuação,
  complemento e abreviação) deu zero divergência entre Python e site, nenhuma perdeu a área que
  tinha e a normalização segue idempotente; só trocam de área "Licenciatura em X" com pontuação no
  fim, que caía em educação e passa à área de X, como já acontecia sem a pontuação.
  Medido no banco: os 6 perfis reais já tinham área e continuam (0 → 0 sem área). Das 296 formas
  distintas de `cursos_aceitos` das 790 extrações, só "Eng. Elétrica", "Eng. de Computação" e
  "Eng. de Produção" mudam, as três para o curso certo (170 → 173 com área). Nas 600 extrações
  que validam no modelo atual, nenhum par com os perfis reais muda; com os cursos sugeridos do
  catálogo, 3 de 27.600 pares mudam, Engenharia Elétrica e de Produção em duas vagas de dados que
  listam "Eng." (35 → 52 e 63, curso compatível), e as duas seguem cortadas pelo pré-filtro para
  esses perfis. Um perfil sintético "Direito, UERJ" passa de 42 vagas com nota 40 ou mais, nenhuma
  com curso compatível, a 71, com 61 compatíveis. Do lado da vaga, sem caso nos dados: item sem
  técnico com vírgula vale pelo primeiro curso, como já valia com barra ("Administração,
  Contabilidade ou Economia" dá compatível a Administração e segue 35 para os outros, que antes
  também tinham 35), e "Técnico ou Superior (Administração)" deixa de ser parcial e fica
  compatível para Administração e 35 para Contábeis, como "Técnico ou superior em Administração".
  O aviso do site abre a etapa de habilidades quando o catálogo carregou e o curso não tem área:
  diz o nome digitado, que as vagas ficam menos precisas e sem sugestões nem áreas de interesse, e
  sugere voltar e escolher o nome na lista; Continuar segue e o curso é salvo como foi digitado.
  Fica no topo dessa etapa, a primeira tela depois do curso, e não embaixo do campo, onde a lista
  aberta o cobre durante a digitação e o clique em Continuar troca de etapa antes da leitura. Sem
  catálogo o aviso some, e limpar o rascunho o apaga, porque ele leva o curso da pessoa. Limites:
  curso sem separador ("Direito UERJ", "Direito 5º período"), com ponto no meio ("Direito. UERJ")
  ou abreviação fora do começo ("Sist. de Informação", "Anal. de Sistemas") continua desconhecido
  e só ganha o aviso; e vírgula corta o nome, então o que vem depois dela nunca conta. Publicação:
  site e `radar/` juntos, sem migration; `VERSAO_DA_EXTRACAO` segue `7efdbc95`.
- "laboratório" saiu do padrão de exclusão de saúde: vetava "Desenvolvimento de Software para
  Laboratório" para quem é de computação. Continua no padrão positivo, então saúde ainda
  reconhece laboratório como título seu.
- A exclusão de Office e idiomas do cálculo agora se restringe a perfis de computação.
  Nas demais formações, requisitos explícitos contam com a mesma normalização das explicações.

## A extração tem prazo

(11/09/2026, G01 e G07 da auditoria do agendamento). Ela roda antes
de qualquer envio e só é gravada no fim, então um kill do job durante ela deixava todos sem
mensagem e jogava fora o que já tinha sido pago, e o dia seguinte repetia a mesma fila.
`PRAZO_DA_EXTRACAO_SEGUNDOS` (padrão 600) é conferido antes de cada requisição e de cada espera
de cota; esgotado, a extração para e segue com o que tem, e o resumo mostra "vagas sem
extração". A conferência **reserva o tempo da própria chamada**, então uma requisição só começa
se couber inteira no prazo: sem isso, três repetições de 120 s mais as esperas furavam os 600 s
e o run podia terminar com zero extrações. Cada chamada leva `GEMINI_TIMEOUT_SEGUNDOS`
(padrão 120, extrator e juiz), e tanto o timeout quanto falha de rede (`httpx.TransportError`,
que cobre conexão recusada e queda no meio da resposta) viram indisponibilidade, tratada como o
504: espera e repete o mesmo lote dentro do prazo. Antes só o timeout era tratado, e um
`ConnectError` derrubava a execução inteira sem resumo de operação. As candidatas vão para a
extração intercaladas por usuário, para o corte não cair sempre em quem entrou por último. O job
tem 30 minutos e o passo do radar 28. Números que sustentam os valores, medidos no diário de
11/09: ~27 s por requisição (93 vagas em 11 requisições) e ~21 s por usuário na entrega, o que
acomoda cerca de 40 usuários. Dois limites conhecidos: o timeout do `httpx` é por operação de
socket, não por chamada, então resposta que chega devagar sem parar não o estoura; e o
enriquecimento das descrições roda antes da extração sem orçamento algum, então uma Adzuna lenta
ainda pode levar o job ao kill.

## Raciocínio da extração em `low`

(11/09/2026, `GEMINI_RACIOCINIO`). O `gemini-3.6-flash`
pensa por padrão e o raciocínio é cobrado como saída: numa requisição real de 10 vagas foram
4.902 tokens de raciocínio para 2.655 de resposta, cerca de 60% do custo (R$ 0,15 por lote, a
US$ 0,75 e 3,75 por milhão e R$ 5,10). Teste com 50 vagas de 11/09 contra as extrações
gravadas: repetir o modo padrão concordou em 90% dos campos, que é o ruído do próprio modelo;
`low` em 88%; `minimal` em 82%. O top 7 dos 4 perfis reais mudou em `low` o mesmo que no
padrão repetido, fora uma vaga de Direito, e em `minimal` mudou mais. `minimal` ainda devolveu
um lote inteiro de 10 vagas vazias, sem habilidade nem curso, que o extrator não detecta e o
cache guardaria, por isso ficou de fora. `low` custa R$ 0,066 por lote e leva ~12 s contra
~30 s; o padrão devolveu 1 de 10 num dos cinco lotes (o mesmo lote incompleto do diário de
11/09) e `low` devolveu 10 de 10 em todos. Ponto a acompanhar: pegadinha. A gravada tinha 3 em
41 vagas, o padrão repetido achou 1 e `low` nenhuma. `GEMINI_RACIOCINIO=padrao` volta ao
comportamento anterior sem mudar código; o nível não entra na identidade da extração, então
trocá-lo não reextrai o que está no cache. Vale só para a extração: o juiz segue no padrão.

## A extração não é repetida por usuário

(03/09/2026, formulação revista em 10/09). Isso não
é o mesmo que dizer que o custo total independe da coorte: mais usuários trazem mais cidades e
mais áreas, e portanto mais vagas novas para extrair, além de mais consultas, pontuação,
gravações, envios e suporte. O que não cresce é o trabalho repetido sobre a **mesma** vaga.
O prompt não contém perfil, então cada vaga é extraída uma vez e a extração serve todos. Ela fica em `vagas.extracao` (JSONB), de
modo que reexecução no mesmo dia ou usuário novo entrando não gastam cota. Antes eram cerca de
6 requisições por usuário por dia: 20 estudantes estouravam a cota e o job morria no timeout de
15 minutos, sempre deixando sem mensagem quem entrou por último, porque a fila é ordenada por
`criado_em`. O resumo de cada execução informa quantas requisições foram gastas, e
`test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas` impede que a propriedade se perca.

## Lote incompleto pede junto o que faltou

(10/09/2026). Em 10/09, 3 de 13 lotes voltaram com
1 de 10 extrações, e as 9 que faltavam iam uma a uma, cada chamada levando de novo a instrução
de 9.170 caracteres. Agora, se a resposta traz parte do lote, só com ids do lote, e faltam 2 ou
mais, as que faltaram vão juntas numa requisição, uma vez, e o que ainda faltar segue uma a
uma. Lote que volta vazio segue uma a uma, porque repeti-lo mandaria o mesmo prompt; resposta
com id fora do lote ou repetido também. A repetição que falha com erro não temporário, ou volta
com id fora do que faltou ou repetido, é descartada inteira e segue uma a uma; com 429 ou 503
ela espera e se repete como qualquer lote, e a cota diária interrompe a extração como antes.
Custo: cada chamada de 2 ou mais vagas que volta incompleta gera no máximo 1 requisição a mais
que antes, sem contar as novas tentativas após 429/503. Num lote dividido por erro cada parte
conta, então um lote de 10 pode passar de +1. Em caracteres de entrada, a repetição de 9 vagas
tem de 17% a 34% das 9 chamadas avulsas (descrições de 500 a 3.000 caracteres), e é esse o
acréscimo quando ela volta sem nada. Fuzz de 6.000 cenários contra a versão anterior, sem erro
temporário: nenhuma vaga a menos e o limite nunca violado. Limites aceitos: o descarte não pega
troca de ids entre as vagas que faltaram, e a extração errada iria para o cache compartilhado,
como já pode acontecer na primeira chamada de qualquer lote; e erro temporário persistente só
na repetição para a execução mais cedo que antes. Os logs `Lote de N vagas voltou com M
extrações` e `Repetição de N vagas ...` registram os ids que faltaram, os devolvidos sem vaga e
os repetidos: ainda não se sabe se o modelo devolve um item só ou copia os ids errado.

## Só entra extração com o id de uma vaga do lote pedido

(18/09/2026, grave 3 da auditoria de
17/09). O `ExtratorEmLotes` aproveitava qualquer item que o modelo devolvesse, inclusive com
`id_vaga` de outra vaga, e no `obter_extracoes` a primeira extração que chega para um id vence,
com a verdadeira descartada em silêncio. Bastava um id copiado errado, ou um bloco `### Vaga id=`
forjado na descrição de um anúncio, para uma vaga boa ficar com os fatos de outra, cair para a
nota que esses fatos dão **para todos os usuários** e ainda mandar a extração errada para o cache
compartilhado, que os dias seguintes reaproveitam. Agora só é aproveitada extração cujo `id_vaga`
está no lote pedido e aparece uma vez só; id fora do lote e id repetido são descartados com log
que diz os ids devolvidos e o lote, e a vaga segue como "sem extração", o caminho que já segura a
mensagem e a devolve ao extrator. As **duas** cópias de um id repetido caem: não dá para saber
qual é a verdadeira, e a vaga volta sozinha, num prompt em que a descrição da outra não está. A
regra all-or-nothing da repetição do lote incompleto fica como está, porque é mais estrita que
esta. O `pipeline.py` também passou a registrar o descarte, para nada sobrescrever em silêncio;
quem decide o que é aproveitável continua sendo o extrator em lotes. Custo: um id repetido num
lote de 10 custa 2 requisições avulsas em vez de 1, e o log da cota passa a contar essa vaga entre
as sem extração.
**A injeção pelo texto do anúncio não foi fechada, de propósito.** `VERSAO_DA_EXTRACAO` cobre
`INSTRUCAO_DE_EXTRACAO` e o schema, **não** `descrever_vaga`: escapar ali a linha que imita o
cabeçalho de vaga mudaria o que a IA lê sem invalidar o cache, e extração feita sobre o texto cru
conviveria com extração feita sobre o escapado sem como distinguir; pôr `descrever_vaga` no hash
reextrairia as 882 do cache de uma vez. Medido em 18/09, só leitura: das 1.095 vagas guardadas,
nenhuma descrição tem `###`, "id_vaga" ou "extracoes", e nenhuma tem quebra de linha (o
enriquecimento junta os espaços e a Adzuna não mandou nenhuma), então o cabeçalho forjado só
apareceria no meio da linha "Descrição:", nunca no começo de uma. Das 882 extrações guardadas,
nenhuma tem `id_vaga` diferente da vaga em que está gravada (658 no formato `fonte:id` da versão
atual, 224 só com o número, das versões antigas): o defeito é do código, não um incidente
observado. O prompt já manda tratar a descrição como dado não confiável. Se um anúncio com
cabeçalho forjado aparecer, escapar `descrever_vaga` junto com a troca de `VERSAO_DA_EXTRACAO` é o
conserto. Limites conhecidos: troca de ids **entre duas vagas do mesmo lote** passa, porque os
dois ids são do lote e nenhum se repete, e a extração errada vai para o cache — é o mesmo limite
já registrado acima para a repetição; e item forjado que **substitui** o verdadeiro (o modelo
devolve um item só, com o id da outra vaga) também passa, e só a vaga que faltou é repedida. Sem
migration e sem deploy; `VERSAO_DA_EXTRACAO` segue `7efdbc95`.

## Resposta malformada do avaliador não derruba o job

(16/09/2026, item 14 da auditoria). Só
erro do `httpx` e `APIError` viravam erro de avaliação. HTTP 200 com corpo que não é JSON
(página HTML de proxy, corpo cortado sem erro de transporte) fazia o SDK levantar
`json.JSONDecodeError`; JSON com tipo errado no envelope (`text` numérico, `parts` ou
`usageMetadata` como texto), `pydantic.ValidationError`; corpo escalar ou `candidates` numérico,
`TypeError`. As três atravessavam `ExtratorEmLotes` e `executar_fluxo`: o job morria antes de
qualquer envio, as extrações pagas no run se perdiam, o resumo de operação não saía e o `julgar`
terminava em traceback. Agora `gerar_json` as converte em `AvaliadorIndisponivel`, o tratamento
do 502/503/504, do timeout e da falha de rede: espera e repete o **mesmo** lote dentro do prazo
e, se persistir, para a extração com o que já veio, e o resumo mostra as vagas sem extração. Não
é a regra do 500 nem divisão porque o envelope é escrito pelo servidor, não pelo modelo: nada no
lote o causa, dividir não isola vaga alguma e, com o corpo quebrado persistente (proxy, mudança de
formato da API), pagaria uma chamada por vaga; parar depois de 4 chamadas e 3 esperas de 61 s é o
mais barato. A mensagem leva os 200 primeiros caracteres do corpo, para dizer de onde ele veio. A
configuração do pedido é montada antes do `try`, então erro de programação ao montá-la segue
aparecendo como tal. Ficam como estavam, erro do lote que divide: o envelope sem texto (pedido
barrado em `promptFeedback`, candidato com `finishReason` SAFETY, MAX_TOKENS sem partes, sem
candidatos), que o SDK entrega como "resposta vazia" e é causado pelo conteúdo, e o texto do
modelo fora do JSON pedido. O juiz usa o mesmo `gerar_json` e não repete: o lote fica sem
julgamento e os outros seguem. No `agy`, saída que não decodifica em UTF-8 levantava
`UnicodeDecodeError` do `subprocess` e virou a mesma "saída inválida" das demais. Os testes usam
o SDK de verdade sobre `httpx.MockTransport`, o que também pega uma versão do `google-genai` que
mude onde o corpo é lido. Limites: o SDK aceita sem erro corpo `{}`, `null`, `[]`, string JSON e
`candidates` como texto, que viram "resposta vazia", então um proxy que devolva isso divide cada
lote até a vaga (19 chamadas por lote de 10) até o prazo; corpo aninhado a ponto de estourar a
recursão do `json.loads` (`RecursionError`) segue derrubando; `TypeError` ou `ValidationError`
do próprio SDK ao montar o pedido também virariam indisponibilidade, mas só com mudança de código
ou de versão, que o teste da resposta válida pelo SDK pega; e o log da espera diz "Cota por
minuto atingida", como já dizia no 503. Sem migration e sem deploy; `VERSAO_DA_EXTRACAO` segue
`7efdbc95`.
