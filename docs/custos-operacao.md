# Custos da operação

Preparado em 08/09/2026 para E04. Esta é uma planilha lógica, não uma fatura. A sessão não
consultou contas, preços atuais, franquias ou logs financeiros; por isso os campos ausentes
estão como “não medido”, nunca como zero.

## Período e evidências disponíveis

Período proposto para a primeira medição: uma janela fechada de 30 dias, com data inicial e
final definidas pela equipe. O repositório informa o workflow, fontes, limites e fórmulas,
mas não contém faturas. O `docs/pre-prd.md` registra uma fotografia operacional anterior de
perfis, vagas, extrações, avaliações e entregas; ela não deve ser tratada como fatura ou custo
atual sem reconferência.

## Tabela de custos

| Serviço/atividade | Natureza | Faturado no período | Franquia gratuita | Uso observado | Estimativa | Moeda | Fonte/data | Responsável |
|---|---|---|---|---|---|---|---|---|
| Supabase Database/Auth/Edge Functions | fixo/variável | não medido | não medido | projeto `xrhvjwemmylwbqgluebc` registrado no guia | não calculada | não medido | conta do projeto, a consultar | a definir |
| Cloudflare Pages/Email/Turnstile | fixo/variável | não medido | não medido | Pages e Email Service descritos no guia | não calculada | não medido | conta Cloudflare, a consultar | a definir |
| GitHub Actions | variável/franquia | não medido | não medido | workflow tem timeout de 15 min; execução não foi consultada | não calculada | não medido | billing Actions, a consultar | a definir |
| cron-job.org | fixo/variável | não medido | não medido | cron externo às 07:23 BRT descrito no guia | não calculada | não medido | conta cron, a consultar | a definir |
| Adzuna | variável | não medido | não medido | fonte padrão configurada; chamadas não foram executadas nesta sessão | não calculada | não medido | conta/API, a consultar | a definir |
| Gupy | variável | não medido | não medido | fonte pública padrão configurada | não medido | não medido | observação oficial na janela, a consultar | a definir |
| Gemini | variável | não medido | não medido | extração compartilhada; o pré-PRD registra alerta de cota, sem fatura | não calculada | não medido | billing/API, a consultar | a definir |
| Telegram | variável | não medido | não medido | envio pelo bot; tarifa não inferida | não calculada | não medido | conta/termos, a consultar | a definir |
| Resend/SMTP | variável | não medido | não medido | configuração descrita, confirmação real pendente | não calculada | não medido | conta Resend/Supabase, a consultar | a definir |
| Suporte e atendimento | variável | não medido | não medido | horas não registradas | não calculada | não medido | registro da equipe, a criar | a definir |

Não somar franquia gratuita como cobrança. Não tratar vagas extraídas por ativado como valor
monetário. Diversidade de áreas/cidades, vagas novas, duração do job, falhas e reextrações
devem ser coletadas junto do mesmo período.

## Fórmulas reproduzíveis

- Custo operacional do período = custos fixos faturados + custos variáveis faturados + suporte
  monetizado somente quando taxa/hora for conhecida. Itens “não medido” não viram zero.
- Perfis atendidos = perfis distintos que receberam ao menos uma recomendação no período.
- Custo por usuário atendido = custo operacional conhecido do período / perfis atendidos; se
  o denominador for zero, mostrar indisponível.
- Custo conhecido por usuário = custos conhecidos / perfis atendidos, separado do custo total
  quando houver serviços ou suporte ausentes.

Extrações compartilhadas devem ser contadas por vaga/processamento, não multiplicadas por cada
usuário novo. Para um cenário futuro, variar novas vagas, percentual de reaproveitamento e
perfis atendidos; registrar a fórmula e não assumir uma extração por usuário.

## Próximo passo da equipe

Exportar faturas e uso das contas sem incluir chaves ou tokens, escolher uma janela comum,
registrar horas de suporte e cruzar com o relatório de métricas. Responsável e acesso: a
definir. CAC, LTV e margem permanecem não medidos; não há base para preço ou compra de plano.
