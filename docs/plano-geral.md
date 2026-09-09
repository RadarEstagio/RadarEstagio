# Plano geral

**Consolidado em 09/09/2026.** A expansão para diferentes áreas foi autorizada em 08/09.
O registro de execução encerra as entregas locais de cadastro, landing, métricas e pausa
(O00–R03), com testes registrados. Não há uma fila de implementação desses IDs a reiniciar.
Publicação, validação com estudantes e decisões externas continuam pendentes de evidência.
Esta consolidação não consultou serviços externos nem repetiu os testes de implementação.

Este é o acompanhamento atual do projeto. O plano formal de piloto foi retirado por decisão
do Igor: não há obrigação de recrutar uma coorte, realizar cinco entrevistas, calcular D7
ou cumprir metas de pesquisa antes de divulgar. As métricas existentes continuam disponíveis.

## 1. O que já está feito

- **Expansão local concluída:** limite de sete recomendações, cadastro com perfil antes da
  conta, caminho explícito sem habilidades, sugestões conforme o curso, demonstração
  ilustrativa e FAQ, estados de vínculo sem promessa de busca já executada, participação no
  feedback, medianas observadas, utilidade por área e motivo opcional após a pausa.
  Contratos nas migrations `0017`–`0019`; presença no Git não comprova aplicação remota.

- **Cadastro e conta:** formulário em etapas, confirmação entre aparelhos, reenvio, recuperação
  de senha, edição de perfil, consentimento e preferência de e-mails.
- **Controle dos dados:** pausa, retomada, desvínculo, exportação, exclusão com carência de
  60 dias e cancelamento. Migrations até `0016` aplicadas; histórico reconciliado em 06/09.
- **Telegram:** vínculo por token de uso único, recomendações explicadas e feedback com seis
  opções. Funções `ir` e `telegram-webhook` publicadas e código comparado com o repositório
  em 06/09, conforme o registro no guia.
- **Primeira entrega:** dispatch por perfil, com exceção entre 06:23 e 07:23 de Brasília.
  Teste registrado de vínculo até mensagem em cerca de quatro minutos; não é garantia de prazo.
- **Concorrência:** trava por perfil e releitura do histórico, testadas com duas conexões.
  Telegram e banco continuam sendo operações separadas.
- **Coleta e ranking:** Adzuna e Gupy por padrão, extração de fatos compartilhada, nota em Python,
  deduplicação e personalização v1 por recusas. Jooble pronto, mas desligado por padrão.
- **Mensagens:** listas longas resumidas; desde 09/09, habilidades desejáveis ausentes aparecem
  como “Diferenciais que a vaga cita”, separadas dos requisitos a conferir e sem virar veto.
- **Métricas:** funil, vagas abertas distintas, utilidade semanal e recusas com denominadores.
  Abertura com token real e relatório foram conferidos; falta confirmar o teste de feedback do Igor.
- **Contato e e-mail:** `contato@radarestagio.com` com recebimento confirmado; Resend verificado
  e SMTP salvo. Confirmação e recuperação reais pelo site ainda precisam de teste registrado.

As evidências remotas acima são de 05–06/09 e estão no [guia](guia-publicacao-e-piloto.md).
Esta revisão não refez esses testes nem consultou o estado atual das contas externas.

## 2. O que falta antes de divulgar

### 1. Confirmar onde o site está publicado

- [ ] Confirmar com Ian o endereço `pages.dev`, a conta Cloudflare que contém o projeto e se
  a publicação está conectada ao GitHub ou foi feita por upload.
- [ ] Definir o endereço público final e conferir HTTPS, início, Termos e Privacidade.
- [ ] Confirmar se mudanças na `main` atualizam o frontend automaticamente.

A conversa sobre publicação no Pages não confirma que ela terminou. Por isso, o estado aqui
é **a confirmar**, e não “não hospedado em lugar nenhum”. O domínio continua na conta do Igor;
a transferência para `RadarEstagio/RadarEstagio` foi confirmada em 08/09 e o PR #21 foi
integrado à main. A configuração de cada automação ainda deve ser verificada. Combinar acesso e administração sem compartilhar senhas.

### 2. Conectar o endereço ao cadastro

- [ ] Conferir Site URL e Redirect URLs do Auth, incluindo recuperação de senha.
- [ ] Trocar a `URL_DA_LANDING` provisória pelo endereço escolhido.
- [ ] Configurar Turnstile no frontend e no Supabase e testar o desafio.

Não reaplicar as migrations já registradas nem republicar funções só para repetir etapas
concluídas. Se o código ou o repositório mudar, atualizar as integrações afetadas.

### 3. Testar com uma conta da equipe

- [ ] Cadastro, confirmação, reenvio e recuperação de senha.
- [ ] Vínculo, entrega de recomendações, abertura e feedback positivo/negativo.
- [ ] Edição, pausa/retomada, exportação, exclusão e cancelamento.

Para feedback, usar envio persistido no banco: `testar-local` gera tokens que o webhook não
encontra. `rodar --perfil` recebe `perfis.id` e exige `DATABASE_URL` configurada para atender
um perfil real. Não colocar essa conexão no frontend. Anotar os erros encontrados e corrigir
os bloqueadores antes de convidar outras pessoas.

### 4. Concluir os textos e combinar a manutenção

- [ ] Igor, Ian e Miguel revisarem Termos e Política e resolverem as passagens pendentes.
- [ ] Definir versão/vigência e sincronizar Markdown e páginas HTML.
- [ ] Combinar quem responde ao contato, acompanha falhas e paga a renovação do domínio.

As páginas seguem como rascunhos até essa revisão; a implementação não aprova os textos.

### 5. Pedir para alguns colegas usarem

- [ ] Enviar o site quando o fluxo estiver funcionando.
- [ ] Perguntar onde travaram, se alguma vaga serviu e se as mensagens ficaram claras.
- [ ] Anotar problemas concretos e escolher o próximo ajuste com a equipe.

Sem quantidade mínima, roteiro obrigatório de entrevista, prazo de duas semanas ou metas
formais. Consultar as métricas quando ajudarem a entender um problema; não é necessário criar
um dashboard ou novas consultas para começar essa conversa.

## 3. Limitações e decisões que continuam valendo

- **Candidatura:** acontece na fonte; o Radar não se candidata e não captura novas candidaturas.
- **Feedback:** última resposta conta nas métricas, mas pode haver eventos brutos repetidos e
  perguntas simultâneas. Mensagem enviada sem gravação pode deixar token órfão.
- **Histórico:** exclusões definitivas podem alterar métricas de semanas passadas.
- **Ranking:** a v1 usa repetição e recusas de área. Os outros motivos não mudam pesos
  automaticamente; investigar exemplos antes de recalibrar.
- **IA:** reuso reduz trabalho repetido; novos anúncios, cidades e áreas podem exigir extrações.
- **Fora do trabalho imediato:** cobrança, plano formal de pesquisa, D7, campanhas de e-mail
  e exclusão automática por abandono. Medianas de entrega e abertura já estão implementadas;
  são tempos observados, não promessa de prazo. Monetização permanece uma hipótese futura.
- **Jooble:** ativação opcional, com chave e configuração próprias; não bloqueia a divulgação.
- **Histórico Git e skills:** permanecem conforme decisões registradas em 05/09. Não há nova
  autorização para reescrever histórico ou remover recursos de terceiros.

## 4. Pendências externas da expansão

Os IDs abaixo são referências históricas. Atualizar o estado geral aqui e a evidência no
documento indicado; não manter uma segunda fila no antigo registro de execução.

| Frente | Estado e próximo passo | Documento responsável |
|---|---|---|
| E01 — publicação e jornada | Conferir versões, migrations, deploy automático, Auth, SMTP, CAPTCHA, cron e jornada com conta da equipe; inspecionar 375 px e 1280 px | [Guia](guia-publicacao-e-piloto.md) |
| E02 — cobertura | Escolher janela, acesso e responsável; coletar amostra e separar erro técnico, desconhecido e descarte legítimo | [Cobertura](cobertura-estagios.md) |
| E03 — aquisição | Após verificar a jornada, confirmar canal, URL, responsável e mensagem; obter autorização antes de divulgar relato | [Aquisição e prova](aquisicao-e-prova.md) |
| E04 — custos | Reunir faturas, uso e horas de suporte em uma janela comum; custos desconhecidos não são zero | [Custos](custos-operacao.md) |
| E05 — oferta | Após cobertura e custos, decidir oferta, pagador, preço, duração, renovação, cancelamento, aceite e provedor; checkout é tarefa posterior | [Hipótese comercial](hipotese-comercial.md) |
| D01 — formação | Usar casos de cobertura para decidir escala acadêmica, correlatos, aliases e cursos fora do catálogo; preservar contrato atual até decisão | [Contrato](contrato-front.md#elegibilidade-acadêmica--decisão-d01-em-aberto) |

Os responsáveis continuam a confirmar; a proposta de divisão está na seção 2 do guia.
E02–E05/D01 não criam metas formais nem impedem o piloto informal depois da conferência
operacional. Não há autorização de cobrança ou disparo de mensagens implícita nesta fila.

## 5. Onde consultar os detalhes

- [Funcionalidades](funcionalidades.md): o que usuários e desenvolvedores podem fazer.
- [Guia de publicação](guia-publicacao-e-piloto.md): configuração e evidências datadas.
- [Cadastro e privacidade](contrato-front.md): decisões dessa frente.
- [Revisão dos textos](guia-publicacao-e-piloto.md#2-revisar-os-documentos-e-combinar-a-manutenção): pendências dos responsáveis.
- [Métricas](metricas.md): definições e limites das consultas existentes.
- [Arquitetura](arquitetura.md) e [contrato frontend](contrato-front.md): implementação.
- [Índice](README.md): documentos mantidos. O histórico dos planos antigos está no Git.
