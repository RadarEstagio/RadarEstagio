# Plano — cadastro, consentimento e privacidade


**Atualizado em 06/09/2026.** Código na `main`; migrations `0014`–`0016` aplicadas e
Edge Functions publicadas, conforme registro remoto de 05/09 à noite. As três foram aplicadas
fora do histórico de migrations e precisam de `migration repair` antes do próximo push. Frontend ainda não
hospedado. Termos e Política continuam em revisão. Confirmação e recuperação reais, Turnstile
e o fluxo completo de cadastro ainda precisam ser validados após a publicação.

**Escopo:** o cadastro de ponta a ponta, os dois documentos legais e o que a LGPD exige do
produto. Nasceu da conversa sobre o e-mail de confirmação parecer amador e cresceu para cobrir
tudo que fica entre a landing e a primeira vaga entregue.

## 1. Decisões tomadas

| # | Assunto | Decisão |
|---|---|---|
| 1 | Controlador dos dados | Os três integrantes do projeto |
| 2 | Canal de contato | `contato@radarestagio.com` criado e recebimento confirmado por Igor |
| 3 | Retenção | Enquanto a conta existir. Excluir apaga em cascata o que está ligado à conta |
| 4 | Portabilidade | Botão de baixar os próprios dados, por função no banco |
| 5 | Menor de idade | Fora do escopo; o documento não trata |
| 6 | Confirmação de e-mail | **Mantida.** Sem ela o endereço nunca é verificado e a recuperação de conta fica apoiada em algo que ninguém provou existir |
| 7 | Exclusão de conta | Marca agora, apaga em 60 dias, com direito a arrependimento |

A decisão 6 contraria a recomendação inicial de remover a confirmação para encurtar o funil. O
argumento que venceu: o produto pretende enviar e-mail no futuro, e enviar para endereço não
verificado gera bounce, o que derruba a reputação do domínio e faz *todos* os e-mails caírem em
spam, inclusive os de confirmação. Deixa de ser preferência e vira requisito técnico.

## 2. O que muda para o estudante

### Cadastro

```
Etapa 1   curso e período
Etapa 2   habilidades
Etapa 3   áreas, cidade, modalidade, e-mail, senha (com olho para revelar)
          [ ] Aceito os Termos de Uso e a Política de Privacidade   ← bloqueia
          [ ] Quero receber e-mails ocasionais do Radar             ← opcional
          "Criar conta e continuar"  →  Turnstile
```

Dois checkboxes, não um. São coisas diferentes: aceitar os termos é porta jurídica e impede
seguir; consentir e-mail é opcional, começa desmarcado e tem que ser reversível no painel.

### Confirmação em qualquer aparelho

O perfil é enviado no cadastro e preservado no banco para criação após confirmação.
O frontend consulta sessão e banco ao retornar, inclusive em outro aparelho; a sessão de
origem acompanha o cadastro para manter a associação do funil. Implementado e testado
localmente, com validação completa no site publicado ainda pendente.


### Tela de reenvio

Três caminhos levam a ela: não recebeu, o link expirou, ou tentou entrar sem ter confirmado. O
campo de e-mail é editável e vem preenchido quando se sabe qual é — sem isso, quem clica num link
expirado em outro aparelho chega sem nenhum contexto.

O botão trava por um minuto depois do envio, porque o Supabase limita o reenvio e o botão pareceria
quebrado.

### Exclusão com arrependimento

**Implementado e aplicado em 05/09**, com uma diferença importante do que este plano previa:
`ativo` **não** é tocado.

```
clica em excluir
   ↓  imediato
excluida_em = now()       sai do where do job, que exige excluida_em is null
telegram_chat_id = null   nada mais chega no Telegram; token_vinculo roda junto
   ↓  60 dias
auth.users apagado; a cascata leva perfil, avaliações, envios e eventos ligados à conta
mais os eventos anônimos daquelas sessões, que cascata nenhuma alcança
```

**Por que `ativo` ficou de fora.** Ele já significava duas coisas — pausa pedida pelo dono e pausa
por falha de envio. Usá-lo também para exclusão fazia o gatilho da `0005` emitir `entregas_pausadas`
para quem saiu de vez, misturando churn definitivo com pausa temporária no funil; e o cancelamento,
que punha `ativo = true` sem saber o estado anterior, religava quem tinha pausado antes de excluir.

**Por que o chat é solto.** `telegram_chat_id` é `unique`. Segurá-lo durante a carência reservava o
Telegram da pessoa por 60 dias contra uma conta nova dela mesma, com "chat de outra conta" e sem
saída. O preço é que quem cancelar precisa vincular o Telegram de novo — decisão do Igor em 05/09.

A policy de update também passou a recusar escrita em perfil marcado: esconder botão é cortesia,
não é o que garante a regra.

A primeira etapa é o que a pessoa pediu: parar de processar. A segunda é o apagamento definitivo.
Entre as duas ela pode entrar e cancelar.

**Proteções implementadas:** o pipeline revalida antes de enviar; `ir` e o webhook verificam
exclusão e vínculo atual. Contas pausadas ou desvinculadas podem navegar por links antigos
sem gerar eventos; exclusão bloqueia ambos. A `0016` também impede novos eventos de vaga
para contas inativas. A limpeza alcança eventos anônimos das sessões sem apagar eventos
atribuídos a outras contas do mesmo navegador.

A revalidação e o envio externo são etapas distintas; não constituem uma transação única.

Os 60 dias precisam de justificativa perante a LGPD — guardar dado "por precaução" não basta.
Permitir o arrependimento é a justificativa, e vai escrita na política.

**Isso obriga alguém a apagar no 61º dia.** O passo entra no job diário, que já roda às 07:23 e já
tem `DATABASE_URL`. Sem isso o documento promete o que não acontece.

## 3. Os dois documentos

O que os torna diferentes de política copiada da internet é serem **verdadeiros**. O que o sistema
faz está todo lido:

**Dados coletados** — e-mail, senha (o Supabase guarda só o hash), curso, período, habilidades,
cidade, modalidade, áreas de interesse e o `chat_id` do Telegram. Mais eventos de funil, que usam
identificador de sessão anônimo e não guardam dado pessoal nas propriedades.

A cidade merece nota à parte: ela sai do sistema. O coletor monta a busca por cidade para os
perfis presenciais e híbridos, então Adzuna e Gupy recebem esse campo — sem saber de quem é. A
política precisa dizer isso; escrever "nada seu é enviado" seria falso.

**Com quem são compartilhados**

| Quem | O que recebe |
|---|---|
| Supabase | tudo — é onde o banco e as contas moram |
| Telegram | o `chat_id` e o conteúdo das mensagens |
| Google Gemini | **apenas o texto dos anúncios de vaga** |
| Adzuna e Gupy | **a cidade** dos perfis presenciais e híbridos, usada como termo de busca; nenhum identificador individual |
| Cloudflare | tráfego do site e o Turnstile |
| GitHub Actions | **todo o perfil**: o job diário roda em runner do GitHub com a `DATABASE_URL` e carrega curso, período, habilidades, cidade, modalidade, interesses e `chat_id` para a memória de lá |

A linha do Gemini é um ponto forte e verificável: desde a separação entre extração e pontuação, em
03/09/2026, o perfil deixou de ir no prompt. Antes seguiam curso, período e habilidades; hoje a IA
lê só o anúncio.

**Direitos** — correção e exclusão já existem no painel. Portabilidade entra com o botão de baixar
os dados. O documento não promete nada além disso.

## 4. Implementação e validação

| Entrega | Estado |
|---|---|
| Termos e Política, HTML e links | Preparados; revisão final e publicação pendentes |
| Exclusão e cancelamento, limpeza após 60 dias | Implementados; `0013` aplicada |
| Consentimento e perfil após confirmação | Implementados; `0014` aplicada |
| Exportação dos próprios dados | RPC `0015` aplicada e botão pronto; testar pela interface publicada |
| Proteção dos eventos e revalidação | Implementadas; `0016` aplicada e funções publicadas |
| Checkboxes, senha visível e revogação de e-mails | Implementados no frontend |
| Confirmação entre aparelhos e reenvio | Testados localmente; testar com Auth real |
| Recuperação de senha | Implementada; testar envio e retorno reais |
| Turnstile | Integração pronta e inerte até configurar as chaves |

As migrations aplicadas não devem ser reescritas. Mudanças posteriores devem entrar em novas
migrations. O checklist de publicação e teste está em `guia-publicacao-e-piloto.md`.


## 5. Dependências externas

| O quê | Trava o quê |
|---|---|
| ~~Domínio~~ | **comprado em 05/09.** Contato funcionando; falta associar à hospedagem |
| Resend | **decidido em 05/09: entra antes do piloto.** Com o domínio na mão, o remetente compartilhado do Supabase é o que impede o cadastro de sustentar 10 a 20 pessoas na mesma tarde: são poucos e-mails por hora e caem em spam. Entrar não depende de e-mail; cadastrar sim |
| Chaves do Turnstile | pública no `web/config.js`, secreta no Supabase |

Turnstile continua inerte até configurar as chaves e disponibilizar o frontend atualizado.
A exportação já existe no banco e na interface; falta validar o fluxo integrado.

Sobre o limite de envio: trocar para o Resend **não remove** a limitação por hora. O Supabase
mantém um limite próprio mesmo com SMTP personalizado — mais alto que o do servidor compartilhado
e configurável, mas existe. Conferir o valor no painel antes do piloto.

## 6. Fora do escopo, e por quê

- **Apagar conta abandonada automaticamente.** O rigoroso seria remover perfil sem interação por
  12 meses, mas isso exige rotina que ninguém escreveu, e prometer no documento o que não está
  implementado é o defeito que a auditoria persegue. Revisitar depois do piloto.
- **Termos e política revisados por advogado.** O rascunho descreve o sistema com honestidade; não
  substitui revisão jurídica se o projeto sair do contexto acadêmico.
- **Link de descadastro no e-mail.** Enquanto nenhum e-mail opcional for enviado, o checkbox no
  painel cumpre o papel.
