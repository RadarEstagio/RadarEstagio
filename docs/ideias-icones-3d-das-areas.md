# Ícones 3D por área: ideias para avaliar

**Proposta em análise, 10/10/2026.** Nada aqui foi implementado nem decidido. Cada ideia pode
ser aprovada, cortada ou reordenada separadamente; as decisões que só o Igor toma estão na
seção 8.

## 1. Resumo

Trocar os 12 ícones de linha das áreas da landing por ilustrações 3D geradas por IA de
imagem é viável e barato, desde que o set saia de um prompt-base único e o nome da área
continue visível no celular.

Hoje cada área é um tile de 56 px com um ícone de linha de 26 px (estilo Lucide), que vira
azul sólido ao ser apontado. O exemplo que motivou a ideia usa um objeto 3D sobre um tile
pastel, o que cabe no mesmo tile sem mexer no layout da seção.

## 2. Ideia 1: ilustrações 3D no lugar dos ícones de linha

Substituir os ícones de linha por objetos 3D dá personalidade à landing sem mudar a
estrutura da seção: o tile de 56 px continua, muda só o que há dentro dele.

O que se ganha:

- Cara de produto feito para estudante. Ícone de linha é o padrão de qualquer template de
  SaaS.
- Escopo pequeno: são 12 ilustrações, um set que dá para gerar e revisar de uma vez.
- Nenhuma mudança de layout, só de conteúdo do tile.

O que se perde:

- O ícone de linha herda a cor do texto e acompanha o tema claro e escuro sozinho. A
  ilustração tem cor fixa e precisa ser conferida nos dois temas.
- Curadoria. A IA de imagem não entrega o set coeso de primeira, e a rodada de descartes é
  o trabalho real.

Observação de escopo: a landing mostra 12 áreas, não profissões. Cada área tem subáreas no
catálogo (`domain/areas.py`), e ilustrar subáreas fica fora desta proposta.

## 3. Ideia 2: um objeto fixo por área

Definir o objeto de cada área antes de gerar, em vez de deixar a IA escolher. Isso evita
que Finanças, Administração e Comercial virem o mesmo saco de dinheiro ou a mesma maleta.
A lista mantém as metáforas que o site já usa nos ícones de linha.

| Área (`data-area`) | Objeto sugerido | Risco de confusão |
| --- | --- | --- |
| Computação (`computacao`) | Notebook com tela de código | Baixo |
| Direito (`direito`) | Balança da justiça | Baixo; martelo de juiz é a alternativa |
| Administração (`administracao`) | Prancheta com organograma | Médio: pode parecer Recursos humanos |
| Finanças (`financas`) | Moedas empilhadas ao lado de um gráfico de barras | Médio: pode parecer Comercial |
| Marketing (`marketing`) | Megafone | Baixo |
| Recursos humanos (`pessoas`) | Crachá com silhueta de pessoa | Médio: pode parecer Administração |
| Comercial (`comercial`) | Sacola de compras | Médio: pode parecer Finanças |
| Logística (`logistica`) | Caminhão com caixa | Baixo |
| Engenharias (`engenharias`) | Capacete de obra com engrenagem | Baixo |
| Saúde (`saude`) | Estetoscópio | Baixo |
| Educação (`educacao`) | Capelo de formatura sobre um livro | Baixo |
| Turismo (`turismo`) | Avião de passageiros | Baixo |

As quatro linhas de risco médio são onde o set mais costuma falhar. Vale gerar essas
primeiro e aprovar o estilo nelas.

## 4. Ideia 3: prompt-base único para manter o set coerente

O maior risco de gerar com IA é cada imagem sair com luz, ângulo e material diferentes. A
defesa é um prompt-base idêntico em todas, mudando só o objeto:

```text
3D icon of [OBJETO], isometric three-quarter view, soft matte clay material, rounded edges,
gentle studio lighting from top-left, subtle shadow below, limited palette of blue, white
and one warm accent, single object centered, transparent background, no text, no letters,
no logos, no people
```

Regras de uso:

- Mesma ferramenta e mesma sessão para as 12, para o estilo não derivar.
- Aprovar uma imagem primeiro. Se a ferramenta aceitar imagem de referência, usar a
  aprovada nas outras 11.
- Gerar 4 variações por área e escolher a melhor; descartar sem dó.
- "No text" fica no prompt porque geradores erram texto, e um crachá com letra torta
  estraga o set.
- Alinhar a paleta ao acento do site (conferir o valor de `--accent-emphasis` no
  `styles.css`) antes de gerar.

## 5. Ideia 4: especificação dos arquivos

| Item | Valor proposto |
| --- | --- |
| Formato | WebP com canal alfa |
| Geração | 1024 × 1024 |
| Exportação | 144 × 144 px (3x de um ícone exibido a 48 px) |
| Peso alvo | até 12 KB por arquivo, cerca de 100 KB o set |
| Fundo | Transparente, sem halo branco nas bordas, testado sobre claro e escuro |
| Caminho | `web/assets/areas/<nome>.webp`, com `<nome>` igual ao `data-area` |
| HTML | `<img>` com `width` e `height` declarados e `alt=""` |

O `alt` vazio é correto porque o nome da área já está dentro do botão. Imagem gerada em
1024 px sem otimizar é o que pesa; o resto é pequeno.

## 6. Ideia 5: mudanças no site

1. **Markup.** Trocar o `<svg>` dentro de `.area-tile` por `<img>` nos 12 botões de
   `web/index.html`. O botão continua com o texto de `.area-name`, que dá o nome acessível.
2. **Destaque do tile.** Hoje `.is-apontada` pinta o tile de azul sólido e muda a cor do
   ícone para branco. Uma ilustração colorida sobre azul sólido briga. Trocar por borda de
   acento e um `scale` leve, respeitando `prefers-reduced-motion`.
3. **Nome visível.** `.area-name` só aparece em hover, foco e `.is-apontada`. No celular não
   há hover, então quem toca não vê o nome e a ilustração, menos óbvia que um símbolo,
   fica sem legenda. Proposta: mostrar o nome sempre, em 12 px, abaixo do tile. Não
   verifiquei como `.is-apontada` se comporta no toque.
4. **Tema escuro.** Testar o tile com fundo pastel no tema escuro. Pode precisar de um
   fundo de tile próprio por tema.
5. **Fallback.** Manter os SVGs de linha até o set inteiro ser aprovado, e trocar os 12 de
   uma vez, para a seção nunca mostrar dois estilos.
6. **Testes e docs.** `tests/test_product_copy.py` cobra trechos do HTML, então a troca
   precisa passar por ele. O registro da mudança vai em `docs/contrato-front.md`, o
   documento dono do site.

## 7. Ideia 6: carrossel como no exemplo

O exemplo é uma faixa horizontal que rola, com os ícones alternando altura e as bordas
esmaecidas. Na nossa landing as 12 áreas são botões que o usuário aponta e escolhe, então
um alvo em movimento atrapalha o clique e o foco do teclado, e movimento contínuo exige
controle de pausa (WCAG 2.2.2).

Proposta: aproveitar o visual sem o movimento. A grade fica estática, com deslocamento
vertical alternado entre os tiles e as bordas esmaecidas como decoração. Carrossel que rola
só entraria se fosse puramente decorativo, fora da escolha de área, com pausa e sem
animação para quem pede movimento reduzido.

## 8. Riscos e decisões

| Risco | Mitigação |
| --- | --- |
| Set incoerente | Prompt-base fixo, mesma sessão, imagem de referência, descartes |
| Halo claro no tema escuro | Pedir alfa, testar nos dois temas, remover o fundo se preciso |
| Peso da página | WebP a 144 px, até 12 KB cada |
| Metáforas parecidas entre áreas | Tabela de objetos aprovada antes de gerar |
| Sem hover no celular | Nome da área sempre visível |
| Texto errado dentro da imagem | "no text" no prompt |
| Licença da imagem gerada | Conferir os termos da ferramenta e anotar qual foi usada |
| Repositório público | Os arquivos ficam públicos; nada de pessoa real nas imagens |

Decisões que só o Igor toma:

- [ ] Escopo: só as 12 áreas, ou também as subáreas?
- [ ] Qual ferramenta de imagem gera o set? Define se há imagem de referência e canal alfa.
- [ ] Nome da área sempre visível, ou só no foco?
- [ ] Tile pastel como no exemplo, ou ilustração sem fundo?
- [ ] Carrossel fora, com só o deslocamento vertical da ideia 6?

## 9. Ordem sugerida de execução

1. Aprovar a lista de objetos da ideia 2.
2. Gerar um objeto, aprovar o estilo e só então gerar os outros 11.
3. Exportar e otimizar conforme a ideia 4.
4. Trocar o markup e o CSS, com o nome visível e o novo destaque do tile.
5. Rodar a suíte e conferir os dois temas em tela de celular e de computador.
6. Commits separados: os arquivos de imagem, o markup com CSS e testes, e o registro em
   `docs/contrato-front.md`.
