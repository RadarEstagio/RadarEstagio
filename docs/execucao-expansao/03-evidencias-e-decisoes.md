# Fichas — evidências e decisões externas

Estas tarefas produzem registros concretos, mas conclusão depende de acesso ou decisão da
equipe. Prepare o que for possível; não invente resultados nem crie funcionalidades comerciais
para preencher uma lacuna de dados. Nenhuma exige quantidade mínima de entrevistas.

## E01

**Verificar versão publicada e jornada real. P0.**

Ler `docs/guia-publicacao-e-piloto.md`, `CLAUDE.md`, workflow e funções. Atualizar o guia com
tabela componente → versão esperada → versão observada → data → resultado → pendência.
Componentes: frontend Cloudflare, Auth/redirect/CAPTCHA, migrations, webhook, rastreio, cron
externo e job diário. Organização já é `RadarEstagio/RadarEstagio`; não recriar repositório.
Sucesso do check Cloudflare no PR não comprova que cron e Supabase estão atualizados.

Primeiro consultar estado sem mutação. Para publicar, preparar ordem exata conforme diferenças
observadas; não reaplicar migrations registradas. Testes com conta da equipe: cadastro,
confirmação/recuperação, vínculo, entrega, abertura, feedback, edição, pausa/retomada e controles
de dados. Verificar limite de cinco no workflow; não disparar vagas para toda a base para testar.
Usar `rodar --perfil` somente com conta apropriada e autorização da sessão.

Aceite: cada item tem evidência ou está explicitamente pendente; segredos e identificadores
pessoais não aparecem no documento. Registrar quem acompanha contato, falhas e domínio e quais
textos legais ainda precisam da equipe. Migrations de recursos novos devem acompanhar versões
compatíveis. Preparar reversão da aplicação sem apagar dados. Não declarar aprovação jurídica.

## E02

**Matriz de cobertura e casos de qualidade. P1.**

Entrega: `docs/cobertura-estagios.md`, com data/fonte/janela e tabela área ou curso → cidade/
modalidade → anúncios coletados → aprovados no pré-filtro → recomendáveis após avaliação →
limites/erros. Não chamar contagem coletada de cobertura total de mercado.

Usar amostra de anúncios acessível, sem envios. Separar coleta indisponível, ausência de
anúncios e descarte. Registrar pelo menos os cenários do problema, quando houver dados:
Administração com vaga financeira/RH; software aplicado a laboratório; formação desconhecida;
saúde; engenharia; computação como controle. Não transformar essa lista em mínimo para divulgar.

Para cada erro, guardar exemplo público ou anonimizado, resultado atual e esperado com motivo;
criar uma tarefa de correção por causa, não ajustar pesos arbitrariamente. Observar descrição
truncada, alias ausente, cursos aceitos e informação desconhecida. Só propor fonte nova após
lacuna demonstrada. Sem acesso: entregar estrutura e procedimento com células “não medido”.

## E03

**Canal inicial e prova de utilidade. P2. Depende de E01.**

Entrega: `docs/aquisicao-e-prova.md`. Aplicar Bullseye: listar canais acessíveis, escolher um
para primeiro teste, explicar hipótese de público e mensagem. Priorizar colegas/comunidades
quando houver acesso da equipe; não enviar mensagens sem autorização explícita.

Preparar mensagem coerente com L01 e registro simples origem → visitantes/cadastros conhecidos
→ pessoas que sinalizam utilidade → limitações de atribuição. Se o produto ainda não registra
origem, usar evidência declarada/manual e não inventar atribuição automática. Propor tarefa
separada de tracking somente após definir propriedades permitidas e uso de dados.

Caso real: pedir autorização para uso do relato, registrar o que ele comprova e preparar texto
sem dados desnecessários. Publicação na landing é uma tarefa posterior com conteúdo autorizado.
Não usar abertura como candidatura ou contratação. Compartilhamento futuro deve usar URL
pública, nunca token pessoal de envio/vínculo. Mídia paga, recompensas e páginas por curso
ficam fora desta tarefa. Sem evidência, documento registra hipótese.

## E04

**Custos reais e capacidade. P2.**

Entrega: `docs/custos-operacao.md` com período, moeda, fonte e tabela de custos fixos,
variáveis, aquisição e suporte. Campos desconhecidos ficam “não medido”, não zero. Separar
custo faturado, franquia gratuita e estimativa; vagas extraídas por ativado não é valor monetário.
Usar registros existentes, sem carregar infraestrutura só para medir.

Relacionar diversidade de áreas/cidades, anúncios novos, tempo de job, falhas e extrações
reaproveitadas. Preservar configuração vigente e não comprar plano. Se citar preços atuais,
consultar a fonte oficial na execução e registrar data. Calcular cenários transparentes de
custo por usuário atendido, sem atribuir toda extração compartilhada a um único usuário novo.
Aceite: fórmulas e premissas reproduzíveis; dados ausentes identificados; custo de suporte
contabilizado ou explicitamente não medido. Não inventar CAC/LTV sem aquisição/pagamento.

## E05

**Oferta e teste comercial. P2. Depende de E02, E04 e decisão da equipe.**

Entrega: `docs/hipotese-comercial.md`. Levar à equipe comparação concreta: assinatura versus
acesso por período de busca, benefício incluído, possível pagador, custo e motivo de escolha.
Estudante é hipótese inicial; instituição patrocinadora é outra hipótese comercial, não mudança
implícita de público. Não escolher preço ou renovação em nome da equipe.

Após decisão registrada, descrever oferta com preço, duração, compromisso com piloto gratuito,
renovação/cancelamento e método de validação. Diferenciar interesse, intenção e pagamento real.
Preparar contagens a acompanhar: expostos elegíveis, compradores, receita líquida, uso posterior,
cancelamentos e margem. Construção de checkout/cobrança exige plano separado com provedor e
condições definidos; esta tarefa não instala gateway nem inicia cobrança.

Três planos, ancoragem e upgrade são opções posteriores a necessidades comprovadas. Não criar
perda fictícia, paywall surpresa ou retenção de dados para pressionar pagamento. Aceite: decisão
ou perguntas remanescentes registradas; hipótese não apresentada como monetização validada.

## D01

**Contrato de elegibilidade e formação. P1. Depende de casos de E02.**

O modelo atual exige período inteiro >=1, tem uma área principal por curso, subáreas de
interesse e uma exceção de cursos intercambiáveis em computação. Não expandir esses contratos
por suposição durante uma tarefa de copy ou cadastro.

Entrega: seção de decisão em `docs/contrato-front.md` e, se houver decisão arquitetural,
seguir a skill de domínio aplicável. Preparar exemplos e opções para a equipe sobre:

- Cursos técnicos e formações organizadas por ano/módulo, sem conversão inventada em semestre.
- Curso versus grande área: quando um anúncio exige curso exato, aceita correlatos ou não informa.
- Interesse em atividade de outra área sem afirmar formação elegível.
- Termos/aliases ausentes e profissões que não cabem nas 12 áreas.
- Regras de peso por área, preferência de frequência e fontes novas, somente com problema observado.

Após decisão, escrever tarefas separadas de contrato/migration, leitura e avaliação Python,
interface e verificação integrada. Enumerar campos, semântica de desconhecido, compatibilidade
com perfis antigos e ordem de publicação antes de permitir implementação. Não gerar migration
com decisão ainda aberta. Aceite desta ficha é proposta revisável, não código generalista novo.
