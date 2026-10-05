# Acompanhamento da auditoria Revenue-Centric Design

Data: 05/10/2026. Base: `main` em `a98e140`. Acompanha a
[auditoria de 10/09](2026-09-10-revenue-centric-design.md), que marcava os sinais para
reavaliar em 24/09; a reavaliação não aconteceu nessa data e é feita aqui.

## Como foi feita

- **Código:** cada um dos 16 achados conferido contra a `main` atual.
- **Dados:** `python -m radar metricas` e consultas agregadas, somente de leitura, ao banco de
  produção na madrugada de 05/10. Nenhum dado pessoal foi extraído; os perfis aparecem pela data
  de criação.
- **Histórico:** commits sem merge desde 13/09, contados por tipo e escopo.

## 1. Veredito

**Nenhum dos 16 achados foi tratado, e a distribuição parou.** Desde 13/09 entraram 309 commits:
cerca de 87 de documentação e 58 de correção do motor (matching, domínio, filtragem, áreas,
pré-filtro, pipeline e storage). O resto foi site, CI e a mudança de hospedagem, domínio e
Turnstile, que eram pré-requisito de divulgação. O padrão do RCD-03, esforço fora do gargalo,
continua o mesmo.

## 2. O que os dados mostram

| Indicador | 10/09 | 05/10 |
|---|---|---|
| Perfis criados desde a auditoria | — | 2 em 25 dias (23/09, vinculado; 03/10, sem vínculo, provável teste da equipe no domínio novo) |
| Sessões na landing por semana | 97 na semana de 07/09 | 13, 4, 40 e 7 nas semanas de 14/09, 21/09, 28/09 e 05/10 (parcial) |
| Recomendações entregues em 30 dias | 196 (desde 28/08) | 535 |
| Abertura | 6,1% | 3% (14 aberturas) |
| Respostas de feedback | 0 | 6 de 750 recomendações (0,8%) |
| Vaga útil ou candidatura | 0 | 0 em todas as semanas desde 31/08 |
| Da criação do perfil à primeira entrega | mediana 1,4 min | mediana 1,7 min |
| Vagas extraídas em 30 dias | — | 2.066, 516,5 por usuário ativado |

**As respostas de feedback quase não são sinal externo.** As seis respostas vieram de três
perfis:

| Data | Motivo | Perfil criado em |
|---|---|---|
| 11/09 | "A nota não fez sentido" (4 vezes) | 07/09, perfil do grupo |
| 16/09 | "Vaga encerrada" | 28/08, perfil do grupo |
| 24/09 | "Não é da minha área" | 23/09 |

O único sinal de alguém de fora da equipe é uma recusa por área. As quatro recusas por nota são
de um perfil do grupo, no mesmo dia, e não bastam para ajustar peso: a regra "não ajustar peso
sem `vaga_irrelevante` real" continua de pé.

**Custo de servir:** 2.066 extrações pela tarifa registrada (R$ 0,066 por lote de 10) dão cerca
de R$ 14 em 30 dias. É estimativa, não fatura. O custo é quase todo fixo, porque a extração é
por vaga e serve todos os perfis, e por isso o gratuito para o estudante continua viável.

**A semana de 28/09 teve 40 sessões e nenhum cadastro.** Sem origem na visita (RCD-04), não dá
para saber se foi divulgação, a troca de domínio ou a própria equipe.

## 3. Estado dos achados

| ID | Achado | Estado em 05/10 |
|---|---|---|
| RCD-01 | Feedback sem sinal | Aberto: a pergunta continua no fim da mensagem (`formatador.py:38`) e "Me candidatei" não existe |
| RCD-02 | Sem pagador | Leitura legal corrigida em 29/09; nenhuma conversa com pagador |
| RCD-03 | Esforço fora do gargalo | Aberto; ver o veredito |
| RCD-04 | Visita sem origem, equipe no funil | Aberto |
| RCD-05 | Valor só depois de três trocas de contexto | Aberto; 3 dos 8 perfis nunca vincularam o Telegram |
| RCD-06 | Conta sem nada acumulado | Aberto |
| RCD-07 | Trabalho episódico | Aberto; depende de RCD-01 e RCD-05 |
| RCD-08 | Promessa maior que a prova | Aberto: "100% automático" e "Vagas que atendem seu perfil" (`web/index.html:72-73`), faixa "ADZUNA GEMINI TELEGRAM" (`:127`), "todos os dias de manhã" (`vinculo.ts:25,32`) |
| RCD-09 | Bot responde "use o botão do site" a tudo | Aberto (`vinculo.ts:34`) |
| RCD-10 | ICP difuso | Sem decisão registrada |
| RCD-11 | Nada diferencia de um alerta gratuito | Aberto |
| RCD-12 | Mensagem densa | Aberto |
| RCD-13 | Só existe pausar tudo | Aberto |
| RCD-14 | Progresso em 0% e "Comece pela sua conta" | Aberto (`app.js:655`, `app.js:876`, `web/index.html:354`) |
| RCD-15 | Cartão "A definir" | Aberto (`web/index.html:213`) |
| RCD-16 | "Sobre" leva ao CTA final | Aberto (`web/index.html:46`, `:261`) |

## 4. Plano

Três frentes, cada uma em PR próprio e com commits fatiados por decisão. Nenhuma aplica
migration em produção nem republica Edge Function: isso fica para quem revisar o PR, conferindo
`supabase migration list --linked` depois.

### Frente 1 · Textos e progresso (RCD-08, 09, 14, 15, 16)

Correção de minutos, sem IA e sem migration.

1. **Landing (RCD-08).** Trocar "100% automático" e "Vagas que atendem seu perfil" por
   promessas que a prova sustenta: o Radar compara curso, cidade e período e explica o que
   falta conferir. Trocar a faixa de fornecedores pelo trabalho que o Radar faz, sem número
   inventado: número só entra se vier do pipeline.
2. **Bot (RCD-08).** O vínculo diz que as vagas chegam "quando houver vagas compatíveis" e que a
   primeira lista sai em instantes; "já vinculado" deixa de prometer "todos os dias".
3. **Mensagem livre (RCD-09).** Chat vinculado que escreve texto livre recebe "Recebemos sua
   mensagem; a equipe lê todas", com o contato e o link da conta, e o texto é encaminhado ao chat
   de operação. Chat não vinculado continua recebendo a instrução de vínculo. A Política de
   Privacidade passa a dizer que a equipe lê essas mensagens; a mudança de texto legal muda a
   versão e fica para a revisão da equipe antes do merge.
4. **Etapa da conta (RCD-14).** Título "Último passo: crie sua conta para ativar seu Radar" e
   progresso `(posição + 1) / (total + 1)`, no `app.js` e no `index.html`.
5. **Preços (RCD-15).** Tirar o cartão "A definir" e deixar o compromisso: gratuito durante o
   piloto, sem cartão, e nada muda sem aviso e aceite.
6. **Sobre (RCD-16).** O item do menu deixa de apontar para o CTA final; sem foto ou nome novo
   sem autorização, a seção usa o que já é público no rodapé.

### Frente 2 · Origem da visita e equipe fora do funil (RCD-04)

1. Migration nova permitindo na `landing_visualizada` o domínio do `document.referrer` e
   `utm_source`, `utm_medium` e `utm_campaign`, dentro do teto de 256 bytes da `0023`. Só o
   domínio do referrer, nunca o caminho nem a query.
2. O `app.js` grava essas propriedades na visita, com o mesmo cuidado de armazenamento das
   regras do `CLAUDE.md`.
3. A consulta de métricas descarta visitas de páginas locais (`file:`, `localhost`, `/web/`) e
   mostra as visitas por origem.
4. Marcar as contas da equipe e tirá-las do funil exige decidir onde a marca mora; a frente
   propõe e registra a decisão em `docs/decisoes-do-banco.md`, sem gravar marca em produção.

### Frente 3 · Pergunta do dia seguinte (RCD-01)

1. Na execução diária, quem abriu uma vaga no dia anterior e ainda não respondeu sobre ela
   recebe: "Ontem você abriu *título — empresa*. E aí?", com **Me candidatei**, **Não serviu** e
   **Ainda vou ver**. No máximo uma mensagem por pessoa por dia, sobre a abertura mais recente.
2. "Me candidatei" emite `candidatura_iniciada` e conta como útil; "Não serviu" abre os motivos
   atuais; "Ainda vou ver" não emite recusa.
3. A pergunta não segura nem atrasa a mensagem de recomendações, e falha nela vira aviso no
   resumo, nunca código 1.
4. Definição em `docs/metricas.md` e porquê em `docs/decisoes-do-motor.md`.

### Fora do plano

- **Congelamento (RCD-03):** regra do motor só muda com caso vindo de usuário real. As quatro
  recusas por nota de 11/09 não contam: são de um perfil do grupo.
- **Divulgação:** o item 7 do plano geral, "Pedir para alguns colegas usarem", vem logo depois
  da Frente 2, com um `utm_source` por grupo ou canal.
- **RCD-02, 05, 06, 07, 10 a 13:** seguem como decisão da equipe; dependem das frentes acima.

## 5. Sinais para reavaliar em 19/10

- Visitas com origem conhecida e sessões locais fora do funil.
- Fração de quem abriu uma vaga que responde à pergunta do dia seguinte.
- Candidaturas declaradas por semana.
- Mensagens livres recebidas pelo bot e o que elas dizem.
- Perfis novos por canal depois da divulgação.

## 6. Princípios citados

Os mesmos da [auditoria de 10/09](2026-09-10-revenue-centric-design.md#9-princípios-citados):
dívida de expectativa, efeito de progresso, efeito Zeigarnik, Bullseye, tráfego frio como teste
de honestidade e volume de suporte como problema de design.
