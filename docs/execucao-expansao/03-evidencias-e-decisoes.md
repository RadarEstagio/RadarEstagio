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
de dados. Verificar limite de sete no workflow; não disparar vagas para toda a base para testar.
Usar `rodar --perfil` somente com conta apropriada e autorização da sessão.

Aceite: cada item tem evidência ou está explicitamente pendente; segredos e identificadores
pessoais não aparecem no documento. Registrar quem acompanha contato, falhas e domínio e quais
textos legais ainda precisam da equipe. Migrations de recursos novos devem acompanhar versões
compatíveis. Preparar reversão da aplicação sem apagar dados. Não declarar aprovação jurídica.

### Procedimento e artefato final

1. Registrar SHA local/remoto e lista de componentes alterados. Ler evidências datadas já
   presentes no guia antes de consultar contas; não repetir como atual uma evidência de 06/09.
2. Preencher tabela com uma linha por componente: evidência consultada, versão esperada,
   observada, data e divergência. Sem acesso, preencher “não verificado” e método de verificação.
3. Preparar sequência concreta de publicação, citando nomes de migrations e funções realmente
   alteradas. Consultar histórico antes de propor aplicação; frontend não pode escrever campos
   que o banco ainda rejeita. Registrar eventual deploy automático ligado à main.
4. Preparar roteiro de conta da equipe, com resultado esperado por passo: salvar perfil,
   confirmar e-mail, vincular chat, receber até sete, abrir link, responder feedback e pausar.
   Execução com efeitos externos depende de acesso/autorização; roteiro sozinho é entrega local.

Saída obrigatória: tabela de versões, roteiro, ordem de publicação, reversão compatível e
pendências com responsável “a definir” se não conhecido. Não enviar mensagem nem alterar cron
para preencher a tabela. Fechamento local: todas as linhas têm evidência ou impedimento explícito.

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

### Coleta de evidência sem alterar ranking

1. Criar tabela com colunas: data, fonte, consulta/curso, cidade, modalidade, total recebido,
   após pré-filtro, extraído, recomendável, descrição completa?, erro/limite e referência do caso.
2. Usar fixtures sintéticas primeiro para documentar procedimento; rotular “sintético”, não
   misturar suas contagens com anúncios observados. Para dados reais, registrar janela e paginação.
3. Separar rejeição legítima (curso incompatível) de informação desconhecida e de falha técnica.
   Cada divergência recebe entrada/esperado/observado/causa provável/teste sugerido, sem dados pessoais.
4. Incluir casos de A01–A06 como regressões já corrigidas, não trabalho a refazer. Para novo
   defeito, criar pendência específica ligada ao exemplo; não alterar pesos nesta ficha.

Fechamento local: `docs/cobertura-estagios.md` contém método reproduzível e matriz preenchida
ou “não medido” por campo. Conclusão permitida: oferta observada na amostra. Não permitido:
“cobrimos todos os estágios” ou ausência de mercado inferida de resposta vazia/erro de fonte.

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

### Um canal, uma hipótese, um registro

1. Preparar comparação de até três canais aos quais a equipe possa ter acesso: público,
   forma de acesso, esforço, custo conhecido/desconhecido e hipótese de utilidade.
2. Recomendar um canal inicial, explicitamente como proposta se acesso não estiver confirmado.
   Preparar uma mensagem pronta para revisão com promessa de L01 e URL pública, sem dispará-la.
3. Criar registro com data/canal/mensagem, pessoas expostas quando conhecido, visitas/cadastros
   atribuíveis e sinal de utilidade. Campo não observável fica desconhecido, não zero.
4. Preparar solicitação de autorização de relato e modelo de caso: contexto, uso real, sinal
   observado, limite e autorização. Sem relato autorizado, manter placeholder explícito no documento.

Fechamento local: `docs/aquisicao-e-prova.md` tem canal proposto, mensagem, método de leitura
e próximo passo da equipe. Não publicar depoimento, mandar mensagens ou construir programa de indicação.

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

### Planilha lógica no documento

1. Criar tabela por serviço e período: faturado, franquia disponível, uso observado, estimativa,
   moeda, fonte e data. Incluir suporte como horas não medidas quando não houver registro.
2. Definir custo operacional do período = custos fixos + custos variáveis + suporte monetizado
   apenas quando taxa/hora for conhecida. Não somar franquia gratuita como cobrança.
3. Custo por usuário atendido = custo do período / perfis distintos que receberam recomendação
   no mesmo período. Denominador zero → indisponível. Mostrar custos conhecidos separadamente
   se o total não puder ser calculado por dados faltantes.
4. Preparar cenário de crescimento variando novas vagas, reaproveitamento e perfis atendidos;
   não assumir uma extração por usuário. Toda estimativa deve explicitar premissas e fórmula.

Fechamento local: `docs/custos-operacao.md` permite refazer contas com os mesmos dados.
Preços, quando necessários, são verificados em fonte oficial na execução. Não comprar plano,
consultar segredos em logs, inventar CAC/LTV ou apresentar extrações como custo em reais.

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

### Proposta comercial revisável, sem implementação de cobrança

1. Comparar assinatura e acesso por período em tabela: pagador hipotético, benefício incluído,
   duração, previsibilidade de custo, relação com busca temporária e dúvidas não resolvidas.
2. Usar E02 para descrever benefício comprovado e E04 para custo conhecido; lacunas impedem
   conclusão de margem, não a preparação do documento. Piloto gratuito permanece respeitado.
3. Preparar campos de decisão: preço, duração, renovação, cancelamento, elegibilidade de
   participantes atuais e forma de obter aceite. Deixar “decisão da equipe” se não definida.
4. Descrever teste futuro e métricas: oferta apresentada, compradores, recebimento líquido,
   custo associado, uso posterior e cancelamento. Intenção declarada não entra como comprador.

Fechamento local: `docs/hipotese-comercial.md` contém comparação e decisões pendentes precisas.
Sem decisão comercial não criar checkout, paywall ou preços na landing. E05 não bloqueia C/L/M/R.

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

### Matriz para uma decisão por vez

1. Preparar linhas para técnico por módulo, graduação por ano, curso não catalogado, interesse
   fora da grande área e anúncio com curso exato/correlatos. Cada linha descreve entrada atual,
   limitação, exemplo e o que falta decidir; não inferir equivalência profissional.
2. Apresentar duas opções por problema quando houver escolha real, com impacto em dados,
   ranking, cadastro e compatibilidade de perfis existentes. Não misturar frequência com curso.
3. Para decisão já autorizada, registrar fonte/data e desdobrar em tarefas de implementação
   separadas. Para decisão aberta, registrar pergunta concreta e manter contrato atual.
4. Se surgir ADR/alteração de domínio, ler a skill aplicável antes de escrever. Não gerar
   migration ou alterar `area_do_curso` como parte de preparar opções.

Fechamento local: seção do contrato tem exemplos e decisão/pendência por linha. Um modelo mais
barato não precisa decidir regras acadêmicas por conta própria para terminar os demais IDs.
