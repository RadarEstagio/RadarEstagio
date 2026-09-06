# Revisão dos documentos e sequência de implementação

**Estado: rascunhos e páginas HTML preparados; revisão final de Igor e Ian pendente.**

**Atualizado em 06/09/2026.** Cadastro, consentimento, recuperação, exportação e proteção das
interações estão na `main`. As migrations `0014`–`0016` foram aplicadas e as funções publicadas,
conforme o registro de 05/09 à noite. Feedback e métricas estão implementados; primeira entrega
e trava por perfil foram validadas remotamente. A consulta do funil foi conferida com dados reais.

O frontend ainda não foi hospedado. As páginas de Termos e Privacidade permanecem sem vigência,
com revisão final pendente. Falta testar o fluxo completo pelo site publicado, incluindo e-mails
de confirmação e recuperação. Esta revisão documental não repetiu verificações no banco remoto.
O [guia de publicação e piloto](guia-publicacao-e-piloto.md) reúne os passos restantes.

O passo 1 da seção 4 do [plano de cadastro](plano-cadastro-e-privacidade.md) determina:
“Escrever os dois documentos; Igor e Ian revisam antes de qualquer código”. Os textos para
essa revisão são os [Termos de Uso](termos-de-uso.md) e a
[Política de Privacidade](politica-de-privacidade.md). Não são documentos publicados nem textos
em vigor. O usuário confirmou o domínio `radarestagio.com` e os responsáveis Igor Costa, Ian Dias e Miguel Esteves. O endereço escolhido para contato é `contato@radarestagio.com`; o recebimento foi testado e confirmado por Igor em 05/09.

## O que revisar agora

- Recebimento em `contato@radarestagio.com` confirmado; combinar a rotina de atendimento.
- Revisar a descrição do serviço, das recomendações e das limitações das fontes.
- Revisar a retenção de 60 dias para arrependimento e o tratamento de pedidos de eliminação
  que não desejem aguardar esse prazo. A existência do prazo no código não comprova, sozinha,
  sua adequação jurídica.
- Definir e registrar a base legal por finalidade, em particular para métricas associadas à
  conta. Aceitar a política não deve virar consentimento genérico para todo tratamento.
- Confirmar condições de transferência internacional, logs e backups dos fornecedores e
  preencher as passagens de revisão antes de publicar.

## Promessas e validações restantes

| Trecho dos rascunhos | Condição para publicar |
|---|---|
| Feedback positivo e sobre a nota | Implementado e publicado; validar respostas reais às seis opções |
| Primeira busca após o vínculo | Implementada e validada em cerca de quatro minutos; preservar configuração e janela do diário |
| Preferência por e-mails e versão aceita | `0014` aplicada; publicar frontend e finalizar versão dos documentos |
| Download dos dados | RPC `0015` e botão implementados; testar no ambiente integrado |
| Recuperação de senha | Implementada localmente; testar o e-mail real e o retorno autorizado |
| Cloudflare, Turnstile e Resend | Configurar e verificar os serviços antes de apresentá-los como ativos |
| Interrupção após exclusão | Implementada e disponibilizada; testar exclusão pelo fluxo integrado |

As migrations `0014`–`0016` foram registradas como conferidas objeto a objeto no banco remoto.
Isso não substitui o teste integrado de exclusão e arrependimento. A `0013` permanece intacta. O prazo de apagamento depende da execução diária; não se deve prometer
apagamento em um horário exato nem extensão desse apagamento a mensagens já no Telegram.

## Sequência restante

1. Revisar os textos com os responsáveis e definir versão e vigência antes de abrir cadastros.
2. Resolver a integração do repositório com Cloudflare Pages e hospedar o frontend.
3. Ajustar Auth e `URL_DA_LANDING` para o site; configurar Turnstile na ordem do guia.
4. Validar confirmação, reenvio e recuperação com e-mail real.
5. Testar cadastro entre aparelhos, vínculo, feedback, exportação, pausa, exclusão e cancelamento.
6. Conferir as métricas com respostas reais e registrar resultados antes de recrutar o piloto.

Não reaplicar nem reescrever migrations já aplicadas para executar esses passos. A publicação
parcial do backend não torna os documentos vigentes nem encerra a validação do produto.
