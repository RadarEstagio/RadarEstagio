# Plano geral

> Nova direção em 08/09/2026: a expansão para diferentes áreas de estágio e as melhorias de
> conversão, ativação e sustentabilidade estão no [plano de expansão baseado em Revenue-Centric Design](plano-expansao-revenue-centric.md).
> Esse plano substitui a restrição anterior à expansão de público e inclui monetização como
> planejamento futuro. As pendências operacionais abaixo continuam válidas; o piloto permanece informal.

**Atualizado em 08/09/2026 · Implementação: executar os IDs do plano de expansão. Operação: verificar publicação.**

Este é o acompanhamento atual do projeto. O plano formal de piloto foi retirado por decisão
do Igor: não há obrigação de recrutar uma coorte, realizar cinco entrevistas, calcular D7
ou cumprir metas de pesquisa antes de divulgar. As métricas existentes continuam disponíveis.

## 1. O que já está feito

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
- **Mensagens:** listas longas resumidas; habilidades desejáveis ausentes não aparecem como
  exigências não atendidas.
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
- **Fora do trabalho imediato:** monetização, plano formal de pesquisa, mediana/TTV/D7,
  campanhas de e-mail e exclusão automática por abandono. Expansão de público já está
  implementada parcialmente; melhorias e métricas adicionais seguem os IDs do plano de expansão.
- **Jooble:** ativação opcional, com chave e configuração próprias; não bloqueia a divulgação.
- **Histórico Git e skills:** permanecem conforme decisões registradas em 05/09. Não há nova
  autorização para reescrever histórico ou remover recursos de terceiros.

## 4. Onde consultar os detalhes

- [Funcionalidades](funcionalidades.md): o que usuários e desenvolvedores podem fazer.
- [Guia de publicação](guia-publicacao-e-piloto.md): configuração e evidências datadas.
- [Cadastro e privacidade](contrato-front.md): decisões dessa frente.
- [Revisão dos textos](guia-publicacao-e-piloto.md#2-revisar-os-documentos-e-combinar-a-manutenção): pendências dos responsáveis.
- [Métricas](metricas.md): definições e limites das consultas existentes.
- [Arquitetura](arquitetura.md) e [contrato frontend](contrato-front.md): implementação.
- [Índice](README.md): documentos mantidos. O histórico dos planos antigos está no Git.
