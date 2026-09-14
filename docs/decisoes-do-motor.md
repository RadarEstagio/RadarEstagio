# Decisões do motor de recomendação

Por que coleta, pré-filtro, extração, pontuação e mensagem são como são, com as medições que
sustentaram cada regra. Movido do `CLAUDE.md` em 13/09/2026 sem reescrita: cada seção guarda a
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
- **Pontos a favor e contra são gerados da comparação** (03/09/2026), não escritos pela IA.
  Sobraram "Curso compatível", "Período mínimo incompatível" e "Exige experiência prévia", porque
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
  curso digitado. Mexeu em `areas.py`, regere; `tests/test_areas_do_front.py` e
  `tests/test_migracao_das_areas.py` quebram se alguma das três listas sair do lugar.

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
- **Estágio de mestrado ou doutorado chegava a graduando.** "Estágio de Mestrado em Economia"
  (EPE) foi a um perfil de Direito com nota 55, só com o alerta de pegadinha. Título com
  mestrado, doutorado ou pós-graduação sai no pré-filtro, como já saía "pleno" e "sênior".
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
- "laboratório" saiu do padrão de exclusão de saúde: vetava "Desenvolvimento de Software para
  Laboratório" para quem é de computação. Continua no padrão positivo, então saúde ainda
  reconhece laboratório como título seu.
- A exclusão de Office e idiomas do cálculo agora se restringe a perfis de computação.
  Nas demais formações, requisitos explícitos contam com a mesma normalização das explicações.
