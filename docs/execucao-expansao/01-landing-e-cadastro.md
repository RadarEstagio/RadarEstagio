# Fichas — entrega, landing e cadastro

> Histórico em consolidação desde 09/09/2026, mantido para revisão antes da exclusão.
> Consulte a [referência mantida](../contrato-front.md) para o estado atual. As instruções e
> pendências abaixo retratam a execução anterior; não reiniciam tarefas nem comprovam produção.

Leia o protocolo e execute a ficha ativa; ao concluir, registre e siga o próximo ID elegível. Caminhos relativos à raiz.

## O00

**Atualizar para sete recomendações no workflow. P0. Pronta.**

Decisão revisada pelo Igor durante a execução: usuários recebem até sete; a alteração precisa
ser refletida no workflow, padrão Python, copy e documentação.
Arquivos: `.github/workflows/radar-diario.yml`, `radar/settings.py` (conferência), documentação
que descreve a quantidade. Manter `QUANTIDADE_VAGAS_ENVIADAS` em `7` no workflow.
Sincronizar o parâmetro configurável local e o padrão Python em sete. Não alterar dias recentes,
cron, endpoint, fontes ou enviar mensagens de teste. Verificar que diário e dispatch por perfil
usam a mesma configuração. Aceite: produção versionada em sete; teste local pode sobrescrever.
Inspecionar diff/YAML; não criar teste Python para comparar uma string do workflow. Só afirmar
configuração publicada quando o commit estiver na main, sem alegar execução real.

### Execução verificável

Estado atual: workflow, decisão de produto e padrão Python usam sete.
Resultado: os dois modos do mesmo workflow, diário e por perfil, usam `"7"`.

1. Ler o bloco `env` do passo que executa o radar e localizar o consumo em `radar/settings.py`.
2. Conferir o valor de produção e atualizar as referências documentais que prometam cinco ao usuário.
3. Conferir que não existe override posterior no workflow. Não rodar o pipeline real.

Fechamento O00: diff contém limite sete e nenhuma mudança em fontes, cron ou filtros.
Registrar arquivo/linha e status Git em `progresso.md`. Este ID não comprova entrega real.

## L01

**Alinhar promessa ao produto. P1. Depende de O00 para publicar em conjunto.**

Mecanismo: promessa sustentada por prova. Arquivo: `web/index.html`; CSS apenas se necessário
para acomodar texto. Copiar a direção abaixo, ajustando pontuação sem mudar a promessa:

- Título: “Encontre estágios que combinam com seu curso e seu momento.”
- Descrição: “O Radar reúne oportunidades de diferentes áreas, compara com seu perfil e envia
  até sete recomendações explicadas no Telegram, quando houver vagas compatíveis.”
- CTA: “Cadastrar meu perfil”. Manter comportamento de “Minha conta” para sessão autenticada.
- Condição: “Gratuito durante o piloto”. Não inventar prazo, cartão, preço futuro ou número de usuários.

Revisar também title, descrição SEO/social e frases que restringem a tecnologia. Retirar “Pare
de procurar estágio” e alegação de que IA calcula a compatibilidade; “O Radar compara” basta.
Não redesenhar página nem mudar formulário. Aceite: primeira dobra explica público, limite,
canal e condição; nenhum texto promete todos os anúncios, contratação ou entrega garantida diária.
Verificação: desktop e celular, CTA funcionando e busca textual por promessas antigas.

### Execução verificável

Antes: a landing precisa ser conferida contra a promessa multiarea e o limite real.
Depois: alguém que lê a primeira dobra identifica público, entrega, canal e condição do piloto.

1. Inventariar em `web/index.html`: title, metas description/Open Graph/Twitter, hero,
   CTA inicial/final e frases que atribuem a nota à IA ou restringem o público à tecnologia.
2. Aplicar a copy definida nesta ficha nos lugares correspondentes, sem adicionar benefícios.
3. Conferir seletores `.js-open-signup` e comportamento autenticado de `mostrarChamadaDeConta`;
   mudar texto não pode remover classes, IDs ou ligação do CTA.
4. Inspecionar 375 px e 1280 px: título inteiro, CTA acessível, sem rolagem horizontal.

Fechamento L01: registrar as superfícies revisadas e o resultado do clique com/sem sessão.
Não exigir teste de snapshot de frases. Se não houver navegador, registrar visual pendente.

## L02

**Demonstração e dúvidas frequentes. P1. Depende de L01.**

Arquivos: `web/index.html`, `web/assets/styles.css`; ler `radar/notification/formatador.py`.
Colocar “Exemplo ilustrativo” visível; usar “compatibilidade” em vez de “match”. Preservar
exemplo fictício identificado, não converter o cartão em link para uma vaga inventada. Mostrar
nota, justificativa e possibilidade de requisitos não informados no formato realmente entregue.
Rotular marcas como fontes/tecnologias, não parceiros ou prova social.

Acrescentar respostas curtas: fontes não cobrem tudo; Telegram precisa ser vinculado; dias sem
vaga podem ocorrer; candidatura é feita na fonte; edição e pausa ficam na conta. Usar HTML
sem novo componente JS se possível. Não inventar depoimentos. Aceite: dúvidas respondidas e
demo distinguível de oportunidade real. Verificar teclado, foco, mobile e links.

### Execução verificável

1. Comparar o cartão da landing com `formatar_vaga` em `radar/notification/formatador.py`.
   Listar campos exibidos e retirar os que não existem na entrega. Identificar o exemplo como fictício.
2. Usar uma oportunidade ilustrativa consistente: curso, requisitos e explicação não podem se
   contradizer. Não atribuir nota a uma vaga real sem avaliação nem inventar empresa parceira.
3. Incluir as cinco respostas da ficha com elementos semânticos. Se usar `details/summary`,
   testar abertura por teclado e manter indicador visível; não criar accordion JS próprio.
4. Conferir todos os links e a leitura na largura mínima. Nenhuma ação deve candidatar o usuário.

Fechamento L02: nota/justificativa/requisitos a conferir aparecem no exemplo, fontes são rotuladas
corretamente e as cinco dúvidas têm resposta. Nenhuma prova social fictícia.

## C01

**Habilidades vazias no banco. P0. Sem dependência de código novo.**

Ler `supabase/migrations/0001_tabelas_iniciais.sql`, `0014_cadastro_e_consentimento.sql` e
`0017_areas_de_todos_os_cursos.sql`; editar somente uma migration nova e
`tests/web/migrations_test.ts` (ou teste novo que use a mesma configuração).

Contrato fechado para implementação neste lote: `habilidades=[]` significa “nenhuma habilidade informada”.
Não distinguir desconhecimento de recusa em informar; não criar string sentinela “iniciante”.
Permitir array vazio, preservando NOT NULL, tipos, limite de 50, validação dos elementos,
consentimento, lista de áreas e RLS. Identificar o nome da constraint existente antes de removê-la.
Atualizar `validar_cadastro_radar` na migration nova preservando o restante do contrato.
A edição usa update direto: conferir a validação da coluna, não só a RPC de cadastro.
As mesmas regras de array/elementos devem valer em ambos os caminhos.
C01 define e testa a migration localmente; não a aplicar em produção neste ID. C02 deve
ser publicado primeiro, depois a migration C01 e por último o frontend C03. Se houver dados antigos
fora do contrato, registrar o caso e não apagar/corrigir os dados por suposição.

Aceite: cadastro e edição com lista vazia funcionam no banco isolado; arrays inválidos,
elementos vazios e edição de outro usuário continuam rejeitados; perfil antigo preservado.
Rodar testes web/banco. Não publicar isoladamente: C02 precisa estar disponível para que o job
consiga ler os novos perfis. Registrar esse requisito em `docs/contrato-front.md`.

### Implementação em três passos locais

C01.1 — Banco: identificar a constraint de cardinalidade de `perfis.habilidades` em 0001 e
as validações de `validar_cadastro_radar` em 0014/versões posteriores. Criar uma única migration
incremental. Remover apenas o mínimo de um item; impor também no update direto o contrato
0–50 strings não vazias após trim. Array nulo, elementos nulos ou em branco continuam inválidos.
Não presumir que a RPC protege updates diretos. Preservar permissões existentes.

C01.2 — Integração: estender o harness de `tests/web/migrations_test.ts` para aplicar a migration
nova depois de inserir um perfil no schema anterior. Não editar migrations antigas para o teste passar.

| Operação | Entrada | Resultado obrigatório |
|---|---|---|
| Cadastro por caminho real da aplicação | `habilidades=[]` | Perfil salvo com array vazio |
| Update do dono | `[]` | Sucesso |
| Cadastro/update | null, elemento null, `" "`, mais de 50 itens | Rejeição |
| Update de outro usuário | Array válido | Nenhuma alteração no perfil alheio |
| Leitura após migration | Perfil antigo com habilidades | Mesmos valores anteriores |

C01.3 — Contrato: registrar semântica e sequência C02 → migration C01 → frontend C03 em
`docs/contrato-front.md`. Rodar comando B abaixo. Marcar implementação local, sem aplicar remoto.
Fechamento: evidência de ambos os caminhos de escrita e preservação de dados, não busca textual no SQL.

## C02

**Perfil iniciante no Python. P0. Implementar após definir o contrato de C01; publicar antes de C01.**

Arquivos: `radar/domain/models.py`, `radar/matching/avaliacoes.py` somente se necessário,
`tests/test_models.py`, `tests/test_avaliacoes.py`, teste de leitura de perfil em storage.
Remover mínimo de uma habilidade. Manter array tipado. Usar a fórmula existente com conjunto
informado vazio; não mudar pesos ou criar bônus para iniciante. Ausência de habilidade não é
veto automático: demais critérios podem permitir recomendação. Não declarar requisito atendido.

Aceite: perfil vazio carrega, pontuação é finita entre 0–100, requisitos aparecem como não
pontos a conferir no perfil, sem afirmar incapacidade; perfis antigos mantêm resultados. Verificar
que não há divisão por zero e que a seleção respeita curso, modalidade e nota mínima.
Testar casos em computação e outra área. Não usar expectativa de nota alta como aprovação.
Rodar Python direcionado e completo. Registrar coordenação de publicação com C01/C03.

### Implementação e regressões

1. Em `Perfil`, `radar/domain/models.py`, remover somente `min_length=1` de habilidades.
   Não tornar `None` equivalente a array vazio nem inventar habilidades padrão.
2. Verificar construção do perfil em `radar/storage/postgres.py` com array vazio. Adicionar
   caso ao teste de storage existente; manter curso, período, cidade e modalidade intactos.
3. Usar `pontuar` com perfis vazios de Computação e Direito e anúncio compatível de cada área.
   Confirmar requisitos atendidos vazios, nota finita e preservação das travas de curso/logística.
4. Comparar perfil antigo com fixture existente: resultado não muda. Rodar P e as regressões
   de `tests/test_compatibilidade.py`. Não reequilibrar pesos para produzir nota desejada.

Fechamento: `Perfil(habilidades=[])` é válido; `habilidades=None` é inválido; leitura de storage
não falha; nenhum requisito é dado como conhecido. C02 precisa chegar ao job antes de C01 remoto.

## C03

**Caminho sem habilidades no site. P1. Depende de C02.**

Arquivos: `web/index.html`, `web/assets/app.js`, estilos pontuais, `tests/web/cadastro_test.ts`.
Adicionar ação explícita “Ainda não quero informar habilidades”. Ela permite continuar com
`[]`; retirar bloqueios em `validateStep` e `profileFromForm` apenas para esse caminho.
Não adicionar texto fictício ao array. Se já houver habilidades, não apagá-las silenciosamente:
a ação deve significar continuar com o que está selecionado ou estar disponível só sem seleção.
Escolha definida: mostrar a ação apenas quando a seleção estiver vazia.
Manter um estado transitório explícito de opção por lista vazia. “Continuar” comum ainda pede
uma habilidade ou essa opção; o atalho libera a etapa e a validação final. Ao editar perfil
já salvo com `[]`, iniciar esse estado como permitido. Nova inscrição deve resetá-lo. Voltar
à etapa não perde a escolha; remover a última habilidade em seleção nova exige escolher o
atalho novamente. Não persistir esse estado extra no banco nem nos eventos.

Explicar: “Você pode começar pelo curso e pelas preferências. Depois, informe suas habilidades
para melhorar as recomendações.” Preservar edição, retorno de etapas e confirmação em outro
aparelho. Aceite: cadastro e edição vazios persistem; usuário pode adicionar habilidades depois;
Enter no campo continua adicionando habilidade sem enviar formulário. Rodar testes web e
verificação visual/foco. Publicar frontend somente após C01+C02 compatíveis.

### Máquina de estados da opção vazia

Usar um booleano transitório com nome explícito para “continuar sem habilidades”, inicial false.
Alterar `validateStep`, `profileFromForm`, `renderSkills`, preenchimento e reset de formulário.
O booleano não entra no payload. A lista de habilidades continua sendo a única informação persistida.

| Transição | Seleção | Permissão vazia após transição |
|---|---|---|
| Novo cadastro / logout / troca de conta | Vazia | false |
| Clicar no atalho sem habilidades | Vazia | true e avança |
| Voltar de preferências | Vazia | Preserva true |
| Carregar edição com `[]` salvo | Vazia | true |
| Adicionar habilidade | Não vazia | false; lista permite avanço |
| Remover última habilidade | Vazia | false; pede escolha explícita novamente |

C03.1: incluir ação e explicação em HTML, mostrar só com seleção vazia e conectar transição.
C03.2: aplicar a mesma regra na validação de etapa e payload final; `[]` deve sobreviver a
`cadastroFromProfile`, confirmação por e-mail e `persistProfile` sem strings sentinelas.
C03.3: cobrir cada linha da tabela em W, incluindo edição que salva e reabre `[]`, Enter no
campo de habilidade e erro de rede que preserva opção/dados. Testar logout seguido de cadastro.

Fechamento: atalho funciona do início até o payload; não basta desbloquear botão. Inspecionar
foco após atalho e mensagem de validação. Não publicar antes de C01/C02 compatíveis.

## C04

**Concluir sugestões contextuais existentes. P1. Parcial. Depende de C03.**

Já existe: `Area.habilidades` em `radar/domain/areas.py`, exportação em `catalogo_do_site`,
`web/assets/areas.json` gerado e `montarHabilidadesDoCurso` em `web/assets/app.js`.
Não recriar campo, catálogo, botões ou mecanismo de seleção. Preservar sugestões atuais
para áreas conhecidas; não substituir listas só para repetir os exemplos do plano anterior.

Trabalho restante, fechado para este ID:

1. Curso desconhecido: não mostrar sugestões de outra área nem o fallback `habilidades_gerais`;
   oferecer entrada livre e o caminho vazio de C03. Não remover o campo do catálogo por limpeza.
2. Falha ao carregar JSON: limpar sugestões que ficaram de um curso anterior, manter entrada
   livre e C03 funcionais e mostrar aviso discreto. Não apagar habilidades escolhidas.
3. Mudança de curso: atualizar sugestões preservando seleção e itens livres. Nenhum item novo
   deve vir selecionado. Resposta assíncrona deve refletir o curso e a sessão atuais.
4. Validar integração com C03, logout e nova inscrição. Não restaurar interesses/estado vazio
   permitido de outra pessoa. Edição do mesmo perfil deve manter os dados salvos.

Arquivos de entrada: os quatro acima, `web/index.html`, `tests/test_areas_do_front.py` e
`tests/web/cadastro_test.ts`. Não criar migration nem mudar ranking, aliases ou subáreas.
Aceite: testar área conhecida, desconhecida, catálogo indisponível, troca rápida de curso,
seleção preservada, item livre e novo cadastro após logout. JSON continua igual ao catálogo.
Executar testes direcionados Python e web; inspecionar celular, teclado e aviso de fallback.

### Sequência de alteração mínima

1. Em `montarHabilidadesDoCurso`, trocar fallback de curso desconhecido por lista de sugestões
   vazia. Continuar usando `renderSkills` para preservar itens já selecionados.
2. Tratar retorno nulo de `carregarAreas`: retirar botões antigos e apresentar aviso próximo
   ao campo. Falha de catálogo não impede `addCustomSkill` nem o atalho de C03.
3. Validar que o resultado é aplicado ao curso atual. Se precisar de controle de requisição,
   usar identidade da chamada/sessão; não criar cache de perfis nem catálogo duplicado.
4. Testar no harness W: Direito → curso desconhecido; dois cursos trocados antes da resposta;
   indisponibilidade após uma seleção; logout antes da resposta; item livre preservado.

Fechamento: sugestões nunca representam curso anterior; ausência de sugestões não apaga seleção;
JSON permanece gerado pelo catálogo. Rodar também `uv run pytest -q tests/test_areas_do_front.py`.

## C05

**Conta após o perfil. P1. Depende de C03.**

Mecanismo: fricção declarativa. Arquivos: `web/assets/app.js`, `web/index.html`,
`tests/web/cadastro_test.ts`, `docs/contrato-front.md`.

Ordem fechada para novo cadastro: momento → habilidades → preferências → conta. Preservar IDs
lógicos `PASSO_*`; mudar `passosAtivos` e fluxo, não renumerar eventos antigos. Login continua
somente conta; edição continua somente perfil. Conta inclui consentimento e CAPTCHA quando
configurado. Só chamar signup após todos os campos necessários válidos. Não criar conta vazia
na passagem de etapa nem guardar senha no navegador.

Mapear todos os `showStep(PASSO_CONTA)` e decidir quais são login/recuperação versus cadastro.
Garantir que montagem assíncrona das áreas termina sem apagar escolhas antes do envio. Revisar
`etapa_preferencias_concluida`: deve significar conclusão válida de preferências, não tentativa
final de autenticação. Manter identidade anônima e confirmação em outro aparelho.

Aceite: testes de cadastro, login, edição, voltar/avançar, rejeição de campos, reenvio, recovery,
CAPTCHA e erro de rede passam. Usuário não perde perfil ao alternar para login. Inspeção mobile
e teclado. Não refatorar o arquivo inteiro; se o diff crescer além do fluxo, reduzir escopo.

Matriz mínima de navegação para implementar e testar:

| Entrada | Passos visíveis | Última ação |
|---|---|---|
| Novo cadastro | Momento, habilidades, preferências, conta | Criar conta e continuar |
| Login | Conta | Entrar |
| Editar perfil autenticado | Momento, habilidades, preferências | Salvar perfil |
| Confirmou e-mail, perfil completo | Estado da conta/vínculo | Vincular Telegram se faltar |
| Confirmou e-mail, perfil ainda incompleto | Etapas de perfil necessárias | Salvar e seguir para vínculo |
| Recuperação de senha | Assistência atual | Redefinir senha |

Derivar primeiro/último passo e progresso de `passosAtivos`, não de comparação numérica com
4. Conferir Enter, botão voltar, `validarFluxo`, rótulo do submit e restauração após erro.
Não mostrar “100% pronto para receber” enquanto confirmação/vínculo ainda estiverem pendentes.

### Quatro etapas de implementação, uma entrega de navegação

C05.1 — Ordem: em `atualizarPassosAtivos`, novo cadastro usa
`[...PASSOS_DO_PERFIL, PASSO_CONTA]`. `showStep`, `avancarPasso` e `voltarPasso` devem trabalhar
com posição no array. Não trocar valores de `PASSO_*`. Abrir novo cadastro no primeiro passo ativo.

C05.2 — Entradas: revisar `setAuthMode`, `openSignup`, `resetDialogView`, `entrarNoModoEdicao`,
`resumeConfirmedSignup` e `prepareMissingProfile`. Login abre conta; edição abre perfil;
recovery permanece no fluxo de assistência. Alternar para login e voltar preserva o rascunho
na sessão da página. Logout/nova pessoa apagam o rascunho. Não persistir senha.

C05.3 — Envio: revisar `validarFluxo`, listener de submit, `authenticate` e `persistProfile`.
Antes do último passo não chamar signup. No último, validar perfil, consentimento e CAPTCHA.
Aguardar montagem relevante de áreas antes de formar payload. Erro de rede mantém dados,
permite repetir e libera botão; não mostrar perfil salvo antes de confirmação do backend.

C05.4 — Regressões: executar cada linha da matriz de navegação desta ficha em W. Adicionar
asserção de que signup não foi chamado após concluir preferências. Conferir envio final com
habilidades vazias e não vazias, ida/volta por todas as etapas, e-mail existente, senha inválida,
reenvio, confirmação em outro aparelho, CAPTCHA ausente/expirado e dupla tentativa de submit.
Conferir que eventos semânticos não mudaram de nome; posicionamento final é revisado em M01.

Fechamento: todas as entradas têm primeiro/último passo coerentes; só o submit final autentica
novo cadastro. Inspecionar teclado e progresso em 375/1280 px. Não encerrar após mudar o array.

## C06

**Estados após cadastro e espera. P1. Pronta.**

Arquivos: `web/assets/app.js` (`showActivation`, conta), `web/index.html`,
`radar/notification/formatador.py`; ler função `entrega_imediata.ts` sem alterar dispatch.
Perfil salvo ainda sem vínculo: CTA vincular. Vínculo confirmado: “Telegram vinculado. As
recomendações chegarão por lá quando houver vagas compatíveis.” Explicar que a primeira busca
pode aguardar o diário. Não afirmar “busca iniciada”, “concluída” ou prazo de quatro minutos,
pois não existe confirmação desse estado no navegador. Manter consulta atual de vínculo.

Aviso sem vagas deve informar ausência de recomendações e continuidade da busca; aviso de
falha operacional não deve fingir ausência de oferta. Preservar tratamento de erro existente, inclusive a supressão do aviso de ausência quando
há candidatas sem extração (`7a4586e`). Não desfazer essa proteção ao editar copy.
Não fabricar endpoint de progresso nem adicionar polling de workflows. Aceite: textos e CTA
correspondem ao estado observado; falha de vínculo não aparece como sucesso. Testar estados
web e formatação alterados; esclarecer em docs onde não há observabilidade.

### Estados e resultado observável

| Dado realmente observado | Mostrar | Não concluir |
|---|---|---|
| E-mail ainda não confirmado | Orientação de confirmação/reenvio | Perfil ativado |
| Perfil salvo, sem chat vinculado | CTA do Telegram | Busca iniciada |
| Chat vinculado | Confirmação do vínculo e espera | Job executado ou prazo garantido |
| Consulta de vínculo falhou | Erro recuperável, tentar novamente | Sucesso ou ausência de vagas |
| Busca completa sem selecionadas | Sem recomendações nesta busca | Mercado sem oportunidades |
| Busca incompleta sem selecionadas | Preservar supressão de mensagem do pipeline | Nenhuma compatível |

1. Comparar `showConfirmation`, `showActivation`, `showAccount` e `refreshActivationStatus`
   com a tabela. Ajustar copy/CTA, sem novo estado de execução não fornecido pelo servidor.
2. Revisar formatador somente para os estados efetivamente recebidos. Preservar a proteção de A03.
3. Executar W e `uv run pytest -q tests/test_formatador.py tests/test_pipeline.py`.

Fechamento: cada frase pode ser sustentada por dado disponível. Registrar limite de observabilidade
em contrato/documentação; não criar polling de Actions ou enviar Telegram real para testar copy.
