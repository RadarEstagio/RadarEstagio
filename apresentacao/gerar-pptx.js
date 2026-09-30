const pptxgen = require("pptxgenjs");
const path = require("path");

const REPO = "/Users/igorcosta/Projetos/RadarEstagio";
const FUNDO = "0F1512";
const BANDA = "17201A";
const BANDA_ALTA = "1C2620";
const LINHA = "26332C";
const TINTA = "EEF3EF";
const SUAVE = "C2CFC7";
const MUDO = "8FA298";
const ACENTO = "5CB584";
const CLARO = "9FD3B2";
const ALERTA = "E5B567";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Igor Costa, Ian Dias e Miguel Esteves";
pres.title = "Radar de Estágio";

const L = 0.6;
const LARG = 8.8;

function novo(numero, seccao) {
  const s = pres.addSlide();
  s.background = { color: FUNDO };
  s.addText(String(numero).padStart(2, "0") + " · " + seccao.toUpperCase(), {
    x: L, y: 0.34, w: LARG, h: 0.22,
    fontSize: 9, bold: true, color: ACENTO, fontFace: "Courier New",
    charSpacing: 1.6, isTextBox: true, margin: 0,
  });
  return s;
}

function titulo(s, texto, tamanho = 30, y = 0.66) {
  const porLinha = Math.floor((LARG * 1.85 * 72) / tamanho);
  const linhas = texto.split("\n").reduce(function (total, parte) {
    return total + Math.max(1, Math.ceil(parte.length / porLinha));
  }, 0);
  s.addText(texto, {
    x: L, y, w: LARG, h: linhas * (tamanho / 72) * 1.3,
    fontSize: tamanho, bold: true, color: TINTA, fontFace: "Calibri",
    lineSpacingMultiple: 0.95, isTextBox: true, margin: 0,
  });
}

function paragrafo(s, texto, y, tamanho = 13) {
  s.addText(texto, {
    x: L, y, w: LARG, h: 0.62,
    fontSize: tamanho, color: SUAVE, fontFace: "Calibri",
    lineSpacingMultiple: 1.1, isTextBox: true, margin: 0,
  });
}

function fonte(s, texto, y) {
  s.addText(texto, {
    x: L, y, w: LARG, h: 0.24,
    fontSize: 8, color: MUDO, fontFace: "Courier New", isTextBox: true, margin: 0,
  });
}

function moldura(s, y, h, destaque) {
  s.addShape(pres.ShapeType.roundRect, {
    x: L, y, w: LARG, h,
    fill: { color: destaque || BANDA }, line: { color: LINHA, width: 1 }, rectRadius: 0.06,
  });
}

function divisorias(s, y, h, quantidade) {
  const passoDaColuna = LARG / quantidade;
  for (let i = 1; i < quantidade; i += 1) {
    s.addShape(pres.ShapeType.line, {
      x: L + i * passoDaColuna, y, w: 0, h,
      line: { color: LINHA, width: 1 },
    });
  }
}

function faixa(s, y, itens, opcoes) {
  const config = opcoes || {};
  const h = config.h || 1.25;
  const tamanhoDoValor = config.tamanhoDoValor || 30;
  moldura(s, y, h);
  divisorias(s, y, h, itens.length);
  const largura = LARG / itens.length;
  itens.forEach(function (item, i) {
    const x = L + i * largura + 0.2;
    const w = largura - 0.4;
    if (item.realce) {
      s.addShape(pres.ShapeType.rect, {
        x: L + i * largura + 0.02, y: y + 0.02, w: largura - 0.04, h: h - 0.04,
        fill: { color: BANDA_ALTA }, line: { color: BANDA_ALTA, width: 0 },
      });
    }
    if (item.etapa) {
      s.addText(item.etapa.toUpperCase(), {
        x, y: y + 0.16, w, h: 0.2,
        fontSize: 7.5, color: MUDO, fontFace: "Courier New", charSpacing: 1.2, isTextBox: true, margin: 0,
      });
    }
    s.addText(item.valor, {
      x, y: y + (item.etapa ? 0.38 : 0.18), w,
      h: item.etapa ? 0.5 : tamanhoDoValor > 20 ? 0.56 : 0.3,
      fontSize: tamanhoDoValor, bold: true,
      color: item.corDoValor || (tamanhoDoValor > 20 ? CLARO : TINTA),
      fontFace: "Calibri", lineSpacingMultiple: 0.95, isTextBox: true, margin: 0,
    });
    s.addText(item.rotulo, {
      x, y: y + (item.etapa ? 0.92 : tamanhoDoValor > 20 ? 0.8 : 0.5), w,
      h: h - (item.etapa ? 1.04 : tamanhoDoValor > 20 ? 0.92 : 0.62),
      fontSize: item.mono ? 9.5 : 11,
      color: item.mono ? ACENTO : SUAVE,
      fontFace: item.mono ? "Courier New" : "Calibri",
      lineSpacingMultiple: 1.08, isTextBox: true, margin: 0,
    });
  });
}

function caixa(s, x, y, w, h, cabecalho, itens, destaque) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h,
    fill: { color: BANDA }, line: { color: destaque ? ACENTO : LINHA, width: 1 }, rectRadius: 0.06,
  });
  s.addText(cabecalho, {
    x: x + 0.2, y: y + 0.16, w: w - 0.4, h: 0.42,
    fontSize: 13.5, bold: true, color: TINTA, fontFace: "Calibri",
    lineSpacingMultiple: 0.95, isTextBox: true, margin: 0,
  });
  const corpo = Array.isArray(itens)
    ? itens.map(function (item, i) {
        return { text: item, options: { bullet: true, breakLine: i < itens.length - 1 } };
      })
    : itens;
  s.addText(corpo, {
    x: x + 0.2, y: y + 0.6, w: w - 0.4, h: h - 0.76,
    fontSize: Array.isArray(itens) ? 11.5 : 11.5,
    color: SUAVE, fontFace: "Calibri",
    lineSpacingMultiple: 1.08, paraSpaceAfter: Array.isArray(itens) ? 6 : 0,
    isTextBox: true, margin: 0,
  });
}

function tabela(s, y, cabecalhos, linhas, larguras, colunaDeDestaque) {
  const cabeca = cabecalhos.map(function (texto, i) {
    return {
      text: texto.toUpperCase(),
      options: {
        color: i === colunaDeDestaque ? ACENTO : MUDO,
        fontFace: "Courier New", fontSize: 8.5, valign: "middle", fill: { color: BANDA_ALTA },
      },
    };
  });
  const corpo = linhas.map(function (linha, n) {
    return linha.map(function (celula, i) {
      return {
        text: celula,
        options: {
          color: i === 0 || i === colunaDeDestaque ? TINTA : SUAVE,
          bold: i === 0,
          fontFace: "Calibri", fontSize: 11, valign: "top",
          fill: { color: n % 2 === 0 ? BANDA : FUNDO },
        },
      };
    });
  });
  s.addTable([cabeca].concat(corpo), {
    x: L, y, w: LARG, colW: larguras,
    border: { type: "solid", pt: 0.5, color: LINHA },
    margin: [7, 12, 7, 12], autoPage: false,
  });
}

// 01 · Abertura
let s = novo(1, "Abertura");
s.addText("Radar de Estágio", {
  x: L, y: 1.55, w: LARG, h: 1.0,
  fontSize: 46, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
paragrafo(s, "Um agente que busca vagas de estágio todos os dias, compara cada anúncio com o perfil do estudante e entrega no Telegram até sete recomendações explicadas.", 2.66, 14);
s.addText("Igor Costa · Ian Dias · Miguel Esteves", {
  x: L, y: 3.62, w: LARG, h: 0.28,
  fontSize: 13, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addText("Métodos e Aplicações de IA · IBM3116", {
  x: L, y: 3.94, w: LARG, h: 0.28,
  fontSize: 12, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addNotes("Somos três alunos e o Radar já está em produção, entregando sozinho todo dia às 07:23. Tudo que vem a seguir são números de produção, não de simulação.");

// 02 · Problema
s = novo(2, "Problema");
titulo(s, "Para achar 7 vagas que servem,\nalguém precisa descartar 726.");
faixa(s, 1.95, [
  { valor: "733", rotulo: "anúncios coletados na execução de hoje" },
  { valor: "35", rotulo: "sobram para um perfil, depois de curso, cidade e modalidade" },
  { valor: "7", rotulo: "chegam ao estudante, as únicas acima da nota mínima" },
], { h: 1.45 });
paragrafo(s, "Esse funil existe com ou sem o Radar. Sem ele, quem descarta é o estudante — todo dia, à mão. No Brasil, 20,1 milhões podem estagiar e 1,2 milhão consegue.", 3.62, 13);
fonte(s, "ABRES — Associação Brasileira de Estágios, 2024", 4.4);
s.addNotes("O 733 é a coleta real de hoje. O 35 é o que sobra para um perfil depois do pré-filtro, e o 7 é o limite da mensagem. O trabalho de descartar 726 anúncios existe de qualquer jeito: a pergunta é quem faz.");

// 03 · Contexto e público
s = novo(3, "Contexto e público");
titulo(s, "Universitário no primeiro estágio.");
paragrafo(s, "O Radar atende quem está procurando o primeiro estágio e não tem tempo de abrir portal todo dia. A busca continua a mesma; o que muda é quem faz a triagem.", 1.28, 13);
caixa(s, L, 2.02, 4.3, 2.4, "Quem usa", [
  "Estudante de graduação, qualquer curso das 12 áreas do catálogo",
  "Procura o primeiro estágio e não tem tempo de triar anúncio todo dia",
  "Já usa Telegram — nenhum aplicativo novo",
]);
caixa(s, L + 4.5, 2.02, 4.3, 2.4, "Como ele faz hoje", [
  "Abre vários portais e repete a mesma busca",
  "Lê o anúncio inteiro para saber se o curso é aceito",
  "Reencontra a mesma vaga republicada com outro título",
]);
s.addNotes("O público é o estudante de qualquer curso, não só de computação: o catálogo tem 12 áreas e 105 cursos.");

// 04 · Solução
s = novo(4, "Solução");
titulo(s, "A IA lê o anúncio. O Python decide a nota.", 26);
paragrafo(s, "O estudante preenche o perfil uma vez. Todo dia às 07:23, pelo GitHub Actions, o sistema coleta, descarta o que não serve, pede à IA apenas os fatos do anúncio e calcula a compatibilidade por regras determinísticas.", 1.3, 13);
const largDaCaixa = 2.08;
const vaoDaCaixa = 0.16;
caixa(s, L, 2.18, largDaCaixa, 2.25, "Coleta e filtro", "API da Adzuna, deduplicação e pré-filtro por curso, cidade e modalidade. Sem IA.");
caixa(s, L + largDaCaixa + vaoDaCaixa, 2.18, largDaCaixa, 2.25, "Extração por IA", "Gemini Flash devolve requisitos, cursos aceitos, período e modalidade em JSON validado.", true);
caixa(s, L + 2 * (largDaCaixa + vaoDaCaixa), 2.18, largDaCaixa, 2.25, "Nota determinística", "Python puro: 45% habilidades, 15% período, 10% curso, 10% área, 10% logística, 10% interesse.");
caixa(s, L + 3 * (largDaCaixa + vaoDaCaixa), 2.18, largDaCaixa, 2.25, "Entrega e histórico", "Bot no Telegram, link rastreado e perfis, notas e envios no Supabase.");
s.addNotes("A divisão de trabalho é a decisão central do projeto: a IA só extrai fatos do anúncio e nunca vê o perfil; quem compara e pontua é Python puro. Isso torna a nota auditável e o custo viável, porque a mesma extração serve todos os usuários.");

// 05 · Demonstração
s = novo(5, "Demonstração");
titulo(s, "Formulário no site, recomendação no Telegram.", 26);
const alturaDaTela = 3.2;
const larguraDoCadastro = alturaDaTela * (2122 / 1330);
const larguraDoTelegram = alturaDaTela * (980 / 1280);
const inicio = L + (LARG - (larguraDoCadastro + larguraDoTelegram + 0.28)) / 2;
s.addImage({ path: path.join(REPO, "apresentacao/telas/cadastro.png"), x: inicio, y: 1.4, w: larguraDoCadastro, h: alturaDaTela });
s.addImage({ path: path.join(REPO, "apresentacao/telas/demo.png"), x: inicio + larguraDoCadastro + 0.28, y: 1.4, w: larguraDoTelegram, h: alturaDaTela });
s.addText("O formulário tem quatro etapas e é preenchido uma única vez.", {
  x: inicio, y: 4.72, w: larguraDoCadastro, h: 0.28,
  fontSize: 10.5, color: MUDO, fontFace: "Calibri", isTextBox: true, margin: 0,
});
const inicioDoTelegram = inicio + larguraDoCadastro + 0.28;
s.addText("A mensagem diária: nota, requisitos e o selo da fonte.", {
  x: inicioDoTelegram, y: 4.72, w: L + LARG - inicioDoTelegram, h: 0.42,
  fontSize: 10.5, color: MUDO, fontFace: "Calibri", lineSpacingMultiple: 1.05, isTextBox: true, margin: 0,
});
s.addText(
  [
    { text: "O site está no ar em ", options: { color: SUAVE } },
    { text: "radarestagio.pages.dev", options: { color: CLARO, underline: true, hyperlink: { url: "https://radarestagio.pages.dev" } } },
  ],
  { x: inicio, y: 5.08, w: LARG, h: 0.3, fontSize: 11.5, fontFace: "Calibri", isTextBox: true, margin: 0 }
);
s.addNotes("À esquerda, o formulário: o perfil vem antes da conta, de propósito, para não cobrar e-mail e senha antes de mostrar o produto. À direita, a mensagem real das 07:23, com a nota, o que o perfil atende, o que falta conferir e a atribuição obrigatória da Adzuna.");

// 06 · Fluxo
s = novo(6, "Fluxo");
titulo(s, "Entrada → Processamento → IA → Resultado → Decisão", 24);
faixa(s, 1.4, [
  { etapa: "Entrada", valor: "Coleta", rotulo: "733 vagas\n16 requisições", mono: true },
  { etapa: "Processamento", valor: "Dedupe e pré-filtro", rotulo: "35 candidatas\npor perfil", mono: true },
  { etapa: "IA", valor: "Extração de fatos", rotulo: "4 requisições\nao Gemini", mono: true, realce: true, corDoValor: CLARO },
  { etapa: "Resultado", valor: "Nota e ranking", rotulo: "23 vagas\npara 4 pessoas", mono: true },
  { etapa: "Decisão", valor: "Telegram", rotulo: "a pessoa abre\ne responde", mono: true },
], { h: 1.72, tamanhoDoValor: 13 });
paragrafo(s, "A extração é por vaga, não por pessoa: a mesma leitura serve todos os perfis, e por isso um usuário novo quase não custa. Números da execução de 28/09.", 3.32, 13);
s.addNotes("Da coleta à mensagem são cinco etapas, e só uma usa IA. As 4 requisições ao Gemini valeram para os quatro usuários juntos, porque a extração fica guardada por vaga e é reaproveitada entre pessoas e entre dias.");

// 07 · Casos reais
s = novo(7, "Casos reais");
titulo(s, "A indústria já automatizou a triagem.");
tabela(s, 1.58, ["Empresa", "O que fez", "Resultado"], [
  ["Unilever", "Triagem de 250 mil candidaturas por ciclo com entrevista em vídeo e jogos cognitivos", "Contratação de 4 meses para 4 semanas; 50 mil horas de entrevista economizadas"],
  ["Gupy", "ATS brasileiro com NLP na ordenação de candidatos, em 2.300 empresas clientes", "480 mil vagas preenchidas em 2021, com redução de até 80% no tempo de contratação"],
  ["LinkedIn", "Casa 50 milhões de vagas com cada usuário num funil de quatro estágios", "Lição da própria engenharia: otimizar por clique premia título sensacionalista"],
], [1.4, 3.7, 3.7]);
paragrafo(s, "Todos filtram pessoas para a empresa. O Radar inverte o lado: filtra vagas para o estudante, então nunca descarta alguém — no máximo deixa de recomendar uma vaga.", 3.86, 13);
fonte(s, "Google for Startups, história da Gupy · LinkedIn Engineering Blog · estudos de caso sobre HireVue e Pymetrics na Unilever", 4.62);
s.addNotes("A mecânica não é nova: extrair requisitos de texto livre, comparar com um perfil e ordenar. O que muda é o lado do funil. Como esses sistemas decidem sobre pessoas, o risco deles é discriminar; o nosso risco é só deixar de recomendar uma vaga.");

// 08 · Proposta de valor
s = novo(8, "Proposta de valor");
titulo(s, "O trabalho repetitivo sai do estudante.");
tabela(s, 1.58, ["Etapa", "Sem o Radar", "Com o Radar"], [
  ["Procurar", "Abrir portais e repetir a busca todo dia", "Uma execução diária, sem ação do estudante"],
  ["Triar", "Ler anúncio por anúncio para ver se o curso é aceito", "733 anúncios viram 7, já conferidos"],
  ["Entender", "Deduzir dos requisitos se vale a pena", "Nota de 0 a 100 com o que atende e o que falta"],
  ["Repetir", "Reencontrar a mesma vaga republicada", "Deduplicação e histórico por pessoa"],
], [1.4, 3.7, 3.7], 2);
faixa(s, 3.98, [
  { valor: "1,7 min", rotulo: "do cadastro à primeira lista, mediana observada", corDoValor: CLARO },
  { valor: "≈ R$ 0", rotulo: "custo de um usuário novo: a extração é por vaga", corDoValor: CLARO },
  { valor: "105 cursos", rotulo: "reconhecidos pelo catálogo, não só computação", corDoValor: CLARO },
], { h: 1.02, tamanhoDoValor: 15 });
s.addNotes("O ganho não é achar uma vaga que ninguém acharia: é tirar do estudante o trabalho repetido. E o custo marginal perto de zero é consequência direta da arquitetura, não de otimização.");

// 09 · Riscos, limites e dados
s = novo(9, "Riscos, limites e dados");
titulo(s, "O motor funciona. Falta a prova de valor.", 26);
paragrafo(s, "O sistema entrega todo dia sem intervenção. O que ainda não existe é evidência de que a recomendação serve para quem recebe.", 1.28, 13);
caixa(s, L, 1.96, 4.3, 2.6, "Riscos e limitações", [
  "Zero vaga marcada como útil em 410 entregas: 12 aberturas e 6 respostas",
  "Uma fonte só: a Adzuna responde por tudo, e a Gupy saiu pelos termos de uso",
  "O estudante é um pagador improvável: os concorrentes são gratuitos para ele",
]);
caixa(s, L + 4.5, 1.96, 4.3, 2.6, "Dados e privacidade", [
  "Origem: API oficial da Adzuna, com atribuição obrigatória em cada anúncio",
  "Formato: JSON das vagas e JSON validado por schema na saída da IA",
  "O perfil nunca vai para a IA: o prompt só contém o anúncio",
]);
s.addNotes("O risco que decide o projeto não é técnico. Sem ninguém marcando uma vaga como útil, não há como recalibrar a nota, e por isso a regra do projeto é não mexer em peso nenhum sem um caso real vindo de usuário.");

// 10 · Próximos passos
s = novo(10, "Próximos passos");
titulo(s, "Protótipo → MVP → Piloto → Implantação", 28);
faixa(s, 1.4, [
  { etapa: "Etapa 1", valor: "Protótipo", rotulo: "Coleta e nota em Python, com perfil fixo e sem banco." },
  { etapa: "Etapa 2", valor: "MVP", rotulo: "Banco, conta no site, vínculo com o Telegram e entrega diária automática." },
  { etapa: "Etapa 3", valor: "Piloto", rotulo: "Validar com estudantes: o sinal de utilidade é o que permite calibrar a nota." },
  { etapa: "Etapa 4", valor: "Implantação", rotulo: "Domínio próprio, textos legais aprovados e um pagador definido." },
], { h: 1.95, tamanhoDoValor: 14 });
s.addShape(pres.ShapeType.roundRect, {
  x: L, y: 3.6, w: LARG, h: 1.34, fill: { color: BANDA }, line: { color: LINHA, width: 1 }, rectRadius: 0.06,
});
s.addText("A pergunta honesta: isso vira negócio?", {
  x: L + 0.28, y: 3.8, w: LARG - 0.56, h: 0.4,
  fontSize: 19, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addText("Tecnicamente o sistema já roda sozinho, todo dia, sem ninguém apertar nada. Como produto, ainda falta a prova de que a recomendação serve — e é isso, não mais código, que decide o próximo passo.", {
  x: L + 0.28, y: 4.24, w: LARG - 0.56, h: 0.58,
  fontSize: 11.5, color: SUAVE, fontFace: "Calibri", lineSpacingMultiple: 1.1, isTextBox: true, margin: 0,
});
s.addNotes("Fechamos com a pergunta que o próprio projeto ainda não respondeu. O próximo passo não é mais código: é conversar com quem recebeu as vagas e descobrir por que ninguém respondeu.");

pres.writeFile({ fileName: path.join(REPO, "apresentacao/radar-de-estagio-pit.pptx") }).then(function (nome) {
  console.log("gerado: " + nome);
});
