# Investigação adversarial da expansão

Base: `5f5abc8`, 08/09/2026. Revisão local, sem alteração de código de aplicação, sem
chamada ao Gemini e sem envio real ao Telegram. Cenários sintéticos reproduzidos usando
funções reais; fakes dos testes existentes somente para infraestrutura e respostas externas.
Testes gerais já executados nesta base: 633 Python aprovados, 24 ignorados; 35 web aprovados;
lint e formatação aprovados. A suíte atual não cobre todos os cenários abaixo.

## A01 — termo genérico anula restrição explícita de curso

Prioridade alta. `radar/matching/compatibilidade.py:38` e
`radar/domain/areas.py` (`TERMOS_GENERICOS_DE_FORMACAO`).

Perfil: Direito. Extração com `aceita_qualquer_curso=False`:

| cursos_aceitos | Resultado de nivel_do_curso |
|---|---|
| Enfermagem | incompativel |
| Enfermagem, áreas afins | compativel |
| Enfermagem, Ensino Superior | compativel |

A presença de qualquer item genérico devolve compatível antes de analisar cursos específicos.
“Áreas afins” não equivale a qualquer formação. Impacto depende de o extrator devolver essa
lista, mas o motor deve tratar a combinação sem inventar elegibilidade. Não foi medida a
frequência desse formato em produção.

Correção esperada: separar abertura explícita a qualquer curso de grau de formação e termos
relacionais; preservar restrições específicas. Regressão: listas mistas não liberam outra
formação; abertura explicitamente declarada continua aceita.

## A02 — resposta parcial é perdida em falha temporária de um item

Prioridade alta. `radar/matching/lotes.py:65` e `:48`.

Dois anúncios, IDs 1 e 2. Fake do extrator devolve resultado válido de 1 ao receber o lote;
ao receber só 2, lança `AvaliadorIndisponivel`. Espera substituída por função vazia no teste.
Chamadas observadas:

`[1,2] → [2] → [1,2] → [2] → [1,2] → [2] → [1,2] → [2]`

Retorno final: `[]`, embora o resultado de 1 tenha sido obtido quatro vezes. A exceção do
item faltante descarta a lista local de sucessos e o retry externo repete o lote inteiro.
Há o mesmo risco de descarte do primeiro ramo quando a divisão recursiva falha no segundo.

Correção esperada: acumular sucessos por identidade e repetir só pendências com limite de
retry. Erro temporário não deve apagar trabalho concluído. Regressões: lote parcial, divisão
com primeiro ramo bem-sucedido, esgotamento de retry e ausência de resultados duplicados.

## A03 — análise incompleta pode ser comunicada como ausência de vaga

Prioridade alta. `radar/pipeline.py:277` até a chamada de aviso em `:299`.

Duas candidatas. Fake de extração devolve apenas ID 1; pontuador de teste devolve nota 10
para 1, limiar 40. ID 2 não tem extração e sua adequação permanece desconhecida.
Resumo registra `vagas_sem_extracao=1`, mas estudante recebe:

> Nenhuma vaga nova compatível com o seu perfil hoje.

A proteção existente só cobre zero avaliações, não avaliação parcial sem aprovadas. O resumo
operacional não corrige a informação dada ao estudante.

Correção esperada: separar conclusão de busca sem recomendação de processamento incompleto.
Não afirmar ausência enquanto candidatas elegíveis ao processamento permanecerem sem extração.
Pode preservar entrega das aprovadas disponíveis; não transformar falha em feedback negativo.
Regressões: zero extrações, extração parcial sem aprovadas, parcial com aprovadas e completa
sem aprovadas. Usar notificador falso e conferir a mensagem por destinatário.

## A04 — níveis explicitamente diferentes viram requisito atendido

Prioridade alta para confiança da recomendação. `radar/matching/avaliacoes.py:71`,
`_normalizar_habilidade` e `_classificar_habilidades`.

Perfil de Administração, habilidades `Inglês básico` e `Excel básico`; anúncio aceita
Administração e exige `Inglês fluente` e `Excel avançado`. Mesma cidade, remoto e período
compatível. `pontuar` retornou:

- nota: 100;
- atendidos: Inglês fluente, Excel avançado;
- não atendidos: lista vazia.

Remover qualificadores ajuda a reconhecer a ferramenta, mas apaga evidência de incompatibilidade
quando ambos os lados declaram nível. O problema inclui a explicação falsa, não apenas o peso.

Correção esperada: distinguir identidade da habilidade de proficiência. Preservar aliases de
Office e a exclusão específica de computação; não inferir fluência de idioma sem nível. Quando
não houver nível conhecido, representar incerteza. Não exige criar formulário complexo para
corrigir a afirmação indevida em campos livres já existentes.

## A05 — logout deixa interesses pré-selecionados para novo cadastro

Prioridade média. `web/assets/app.js:1340`, `areasEscolhidas` e `areasSalvas`.

Reprodução em JSDOM com harness de `tests/web/cadastro_test.ts`:

1. Abrir conta autenticada de Computação com `areas_de_interesse=[dados_ia]`.
2. Entrar em edição, carregando os interesses na memória da página.
3. Fazer logout; getSession da próxima abertura passa a retornar sessão nula.
4. Abrir novo cadastro, preencher Computação e avançar até preferências.
5. Ler checkboxes selecionados: `[dados_ia]`, sem a nova pessoa ter escolhido esse interesse.

Logout limpa formulário e habilidades, mas não os dois estados de interesses. É contaminação
de estado no mesmo navegador, não evidência de acesso indevido ao banco de outro usuário.

Correção esperada: limpar dados de perfil em memória ao encerrar sessão e iniciar outra
inscrição; impedir callback pendente de restaurar estado da sessão antiga. Preservar a
restauração intencional ao editar a mesma conta. Testar contas sequenciais e catálogo indisponível.

## A06 — extração é feita antes de excluir anúncios já entregues

Prioridade média; comportamento preexistente, com custo mais visível após versionar cache.
`radar/pipeline.py:98`, `:107`, `:270`.

Único perfil já recebeu `(adzuna,1)`; único anúncio coletado é esse mesmo; não existe extração
reutilizável da versão atual. Observado no fake de infraestrutura:

- IDs passados ao extrator: `[1]`;
- extrações novas: 1;
- recomendações novas: 0.

As candidatas globais são extraídas antes de o atendimento consultar o histórico individual.
Depois de mudar prompt/formato, anúncios ainda recentes podem consumir cota mesmo quando já
foram entregues a todos os perfis interessados. Não é necessária nova extração para reenviar,
porque o produto corretamente não reenvia esses anúncios.

Correção esperada: formar união de candidatas ainda úteis para pelo menos um destinatário,
considerando histórico antes do enriquecimento/extração. Manter trava e releitura antes do
envio, porque a pré-seleção não substitui a proteção contra concorrência. Se outro perfil
novo ainda precisa do anúncio, extrair normalmente. Falha ao ler histórico não autoriza envio.
Testar caso todos receberam, apenas um recebeu e novo usuário com extração compartilhada.

## Ordem sugerida e limites

Priorizar A02 (perda de resultados/cota), A01/A04 (elegibilidade e explicação), A03 (mensagem
enganosa), A05 e A06. As correções precisam de testes próprios; suíte verde da base não prova
ausência desses defeitos. Não atribuir todos a um único autor: a revisão cobre o resultado
integrado de várias mudanças e inclui comportamento antigo.

Não foram verificadas execução em produção, frequência real de cada caso, cota faturada,
colisões reais de IDs entre fontes ou comportamento visual em navegador. Colisão por ID sem
fonte e republicação com descrição curta já aparecem como limitações no CLAUDE.md; não foram
contadas como novas descobertas nesta investigação.

## Revalidação após correções de Ian — base `a87f9fc`

Atualização de 08/09/2026. Repetidos os cenários sintéticos originais, sem serviços externos.

| Achado | Resultado da revalidação |
|---|---|
| A01 | Aberto: Direito continua compatível com `[Enfermagem, áreas afins]` e `[Enfermagem, Ensino Superior]`, com abertura a qualquer curso falsa. |
| A02 | Cenário corrigido: preserva ID 1; chama `[1,2]` uma vez e repete somente `[2]` quatro vezes. |
| A03 | Cenário corrigido: contabiliza uma vaga sem extração e não envia mensagem de ausência de compatibilidade. |
| A04 | Parcial: básico versus fluente/avançado passa a não atendido, nota 70. Sem nível declarado ainda confirma proficiência exigida. |
| A05 | Cenário corrigido: novo cadastro inicia com interesses selecionados `[]`. |
| A06 | Cenário corrigido: anúncio entregue a todos não chega ao extrator; zero extrações novas. |

Lacuna restante de A04, reproduzida com `pontuar`: perfil Administração, habilidades
`[Inglês, Excel]`, vaga exigindo `[Inglês fluente, Excel avançado]`. Resultado: nota 100,
ambos os requisitos atendidos. Em `radar/matching/avaliacoes.py`, `_atende` retorna verdadeiro
quando o nível do perfil não foi informado. Isso reconhece a habilidade, mas não comprova o
nível exigido; a explicação precisa preservar essa incerteza.

Validação geral desta base: **638 testes Python aprovados, 24 ignorados; 36 testes web
aprovados; Ruff e formatação aprovados**. A01 e a lacuna de A04 permanecem reproduzíveis apesar
da suíte verde. Prioridade restante: restrição de curso e proficiência desconhecida.
Esta revalidação confirma os cenários descritos; não certifica produção nem todos os casos
alternativos listados como regressões desejáveis no relatório original.

## Correções integradas após revalidação

A01: somente abertura explícita a qualquer curso permite ignorar a lista de cursos.
Grau de formação e termos relacionais são ignorados na comparação de cursos específicos;
sozinhos, produzem compatibilidade parcial. A04: nível desconhecido no perfil não satisfaz
nível explícito na vaga; requisito sem nível continua aceitando a habilidade cadastrada.
A mensagem apresenta requisitos não comprovados como “Requisitos a conferir no seu perfil”,
preservando a distinção entre falta de evidência e incapacidade da pessoa.
Foram adicionados testes para listas mistas, termos genéricos isolados, abertura explícita,
proficiência desconhecida e requisitos sem nível, preservando aliases de Office.

Correções publicadas no Git em `c2d6f96` (A01) e `40ed28c` (A04 e mensagem).
Validação: 649 testes Python aprovados, 24 ignorados; lint/formatação aprovados.
Push na main não comprova execução em produção.
