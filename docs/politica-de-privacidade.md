# Política de Privacidade — Radar de Estágio

**Rascunho para aprovação de Igor, Ian e Miguel. Não publicado e ainda sem vigência.**

Este texto é o mesmo de `web/privacidade.html` e descreve a versão prevista para o piloto. As
passagens antes marcadas como pendentes (bases legais, processamento internacional, logs e cópias
de segurança) foram resolvidas em 08/09/2026 e aguardam aprovação. As condições para publicar
estão em [revisão dos documentos](guia-publicacao-e-piloto.md#2-revisar-os-documentos-e-combinar-a-manutenção).

## 1. Responsáveis e contato

Igor Costa, Ian Dias e Miguel Esteves são os responsáveis pelas decisões sobre o tratamento
dos dados pessoais no projeto acadêmico Radar de Estágio.

Site: https://radarestagio.com.
Para assuntos de privacidade e pedidos sobre seus dados: [contato@radarestagio.com](mailto:contato@radarestagio.com).

## 2. Dados utilizados

- **Conta e acesso.** Usamos seu e-mail e os dados de autenticação para criar a conta, confirmar
  o endereço, permitir o acesso e recuperar a senha. O Supabase gerencia a autenticação e
  armazena um hash da senha.
- **Perfil e recomendações.** Curso, período, habilidades, cidade, modalidade e áreas de
  interesse ajudam a selecionar vagas e calcular a compatibilidade. Guardamos recomendações,
  notas, explicações e histórico de envio para entregar oportunidades, evitar repetições e
  verificar o funcionamento.
- **Telegram.** Usamos o identificador do seu chat para vincular a conta e entregar mensagens.
- **Uso do Radar.** Registramos aberturas de links, feedback sobre vagas, identificador de
  sessão e eventos de navegação e cadastro para entender o uso do serviço e identificar
  problemas nas recomendações e no cadastro.
- **Preferências e histórico da conta.** Guardamos o aceite dos termos e sua preferência por
  e-mails. Datas de criação, atualização, ativação, pausa e pedido de exclusão, além de falhas
  de entrega e do motivo opcional da pausa, permitem operar a conta e executar seus controles.

O identificador de sessão não contém seu nome, mas pode ser associado à conta ao longo do
cadastro. Por isso, não tratamos esse histórico como informação irreversivelmente anônima.
As propriedades dos eventos são destinadas a informações sobre o uso do produto, sem campos
de texto livre para dados pessoais.

O navegador guarda dados da sessão de acesso e um identificador local usado nas métricas.
O fluxo de cadastro também pode manter temporariamente um perfil pendente no dispositivo.
Provedores de hospedagem, autenticação e proteção contra abuso processam dados técnicos das
requisições, como endereço IP e informações do navegador, conforme a configuração de cada
serviço.

## 3. Finalidades, bases legais e escolhas

Usamos os dados necessários à conta e às recomendações para prestar o serviço solicitado.
O cadastro exige os dados indicados no formulário; sem um Telegram vinculado, não há entrega
de recomendações por esse canal.

O envio de e-mails ocasionais depende de uma escolha separada, inicialmente desmarcada.
Recusar ou revogar essa escolha não impede o uso do Radar. Você pode alterá-la no painel.
Confirmação de e-mail e recuperação de senha são comunicações necessárias à conta.

As métricas ajudam a identificar abandono do cadastro, falhas de entrega e recomendações que
não serviram.

Cada finalidade se apoia em uma das hipóteses do artigo 7º da LGPD:

- **Conta, perfil, vínculo com o Telegram, recomendações e histórico de envio:** necessários
  para prestar o serviço que você pediu ao se cadastrar (art. 7º, V).
- **E-mails ocasionais:** consentimento, dado por uma escolha separada e revogável no painel
  (art. 7º, I).
- **Métricas de uso, feedback sobre vagas e proteção do site contra abuso:** legítimo interesse
  dos responsáveis em avaliar, corrigir e proteger o serviço (art. 7º, IX), limitado a dados de
  uso sem texto livre. Você pode se opor a esse tratamento pelo canal de contato.
- **Registro do aceite dos termos e das suas escolhas:** exercício regular de direitos e
  comprovação das condições aceitas (art. 7º, VI).

## 4. Quem processa seus dados

Para operar o Radar, utilizamos fornecedores que processam dados para as finalidades descritas
abaixo.

- **Conta e armazenamento.** O Supabase processa os dados da conta, do perfil e do histórico do
  Radar para autenticação e armazenamento.
- **Mensagens e e-mails.** O Telegram processa o identificador do chat, as recomendações e as
  interações com o bot. O Resend processa seu endereço de e-mail e o conteúdo das mensagens
  para enviar comunicações da conta.
- **Busca e envio de recomendações.** O GitHub Actions processa o perfil, o identificador do
  chat e os dados das recomendações durante as rotinas automáticas. Adzuna e Gupy recebem
  termos de busca, incluindo a cidade dos perfis presenciais ou híbridos, sem identificador
  individual do estudante.
- **Hospedagem e proteção do site.** A Cloudflare processa o tráfego do site e dados técnicos
  de verificação contra abuso pelo Turnstile.

O banco de dados e a autenticação ficam em um projeto do Supabase na região de São Paulo.
Cloudflare, Telegram, Google, GitHub, Resend e Adzuna são empresas com infraestrutura fora do
Brasil, então parte dos dados descritos acima pode ser transferida internacionalmente. Essas
transferências se apoiam nas hipóteses do artigo 33 da LGPD, em especial na necessidade de
executar o serviço que você pediu e nas cláusulas contratuais e políticas de privacidade
publicadas por cada fornecedor. Os responsáveis não mantêm cópia dos seus dados em outros
países fora desses serviços.

Ao abrir uma vaga, você é redirecionado ao site da fonte. O tratamento feito por esse site,
inclusive dos dados da candidatura, segue as regras dele.

## 5. Seleção automatizada

O Google Gemini recebe o texto e as informações dos anúncios para extrair requisitos. O perfil
do estudante não é incluído nesse processamento. O código do Radar compara essas informações
com seu perfil para produzir a nota e a explicação. O Radar não toma decisões de contratação.
Você pode corrigir seu perfil, dar feedback por vaga e pedir esclarecimentos aos responsáveis
sobre uma recomendação.

## 6. Retenção e exclusão

Os dados associados à conta são mantidos enquanto ela existir. Pausar as entregas ou
desvincular o Telegram não elimina o perfil nem o histórico.

O pedido de exclusão no painel marca a conta e remove seu vínculo com o Telegram. O prazo de
60 dias permite cancelar o pedido. Ao terminar esse prazo, a rotina diária apaga a conta,
o perfil, as avaliações, os envios e os eventos ligados à conta. Também apaga os eventos sem
dono das sessões identificadas como associadas à conta, sem apagar eventos pertencentes a
outras contas que usaram o mesmo navegador.

Anúncios públicos de vagas podem permanecer no catálogo. Mensagens já recebidas no Telegram
e dados enviados aos sites de candidatura não são removidos por essa rotina. O apagamento do
banco também não limpa automaticamente o armazenamento local dos seus outros dispositivos.

Não há rotina de exclusão automática de contas apenas por inatividade.

Os fornecedores mantêm registros técnicos e cópias de segurança por prazos definidos nos planos
contratados, que os responsáveis não controlam item a item: o GitHub guarda os registros de cada
execução automática por até 90 dias, as mensagens já entregues permanecem no seu chat do
Telegram até que você as apague, e as cópias de segurança do banco, quando existirem no plano
contratado, expiram nos prazos do fornecedor. O apagamento da conta não elimina essas cópias
imediatamente.

## 7. Seus direitos e controles

O painel permite corrigir o perfil, controlar as entregas, revogar e-mails opcionais, baixar
uma cópia dos dados e solicitar ou cancelar a exclusão no prazo indicado.

Você também pode solicitar confirmação do tratamento, acesso, correção, informações sobre
compartilhamento, portabilidade nos termos aplicáveis e exclusão ou bloqueio quando cabíveis.
Pedidos sobre decisões automatizadas podem ser enviados pelo mesmo canal. Esses direitos
decorrem da [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm),
especialmente dos artigos 18 a 20.

Envie seu pedido a [contato@radarestagio.com](mailto:contato@radarestagio.com). Podemos precisar
confirmar sua identidade para evitar entregar seus dados a outra pessoa. O download do painel
não inclui senhas, hashes, tokens de acesso ou credenciais dos serviços.

## 8. Atualizações

A versão publicada terá data de vigência. Alterações relevantes serão informadas no site.
Novas finalidades que exijam consentimento terão uma escolha específica apresentada antes
do início desse uso.
