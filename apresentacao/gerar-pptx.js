const pptxgen = require("pptxgenjs");
const path = require("path");

const REPO = "/Users/igorcosta/Projetos/RadarEstagio";
const FUNDO = "FFFFFF";
const SUPERFICIE = "F3F6F3";
const LINHA = "DDE5DF";
const TINTA = "111A15";
const SUAVE = "4A5952";
const MUDO = "7A8880";
const ACENTO = "1F6B45";
const ALERTA = "8A5A12";
const RISCO = "A0362A";

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
    x: L, y: 0.36, w: LARG, h: 0.22,
    fontSize: 9, bold: true, color: ACENTO, fontFace: "Courier New",
    charSpacing: 1.6, isTextBox: true, margin: 0,
  });
  return s;
}

function titulo(s, texto, tamanho = 30, y = 0.68) {
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

function paragrafo(s, texto, y, tamanho = 12, w = LARG) {
  s.addText(texto, {
    x: L, y, w, h: 0.6,
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

function numero(s, x, y, w, valor, rotulo) {
  s.addText(valor, {
    x, y, w, h: 0.62,
    fontSize: 34, bold: true, color: ACENTO, fontFace: "Calibri", isTextBox: true, margin: 0,
  });
  s.addText(rotulo, {
    x, y: y + 0.64, w, h: 0.66,
    fontSize: 10, color: SUAVE, fontFace: "Calibri",
    lineSpacingMultiple: 1.08, isTextBox: true, margin: 0,
  });
}

function coluna(s, x, y, w, cabecalho, itens) {
  s.addText(cabecalho, {
    x, y, w, h: 0.28,
    fontSize: 13, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
  });
  s.addText(
    itens.map(function (item, i) {
      return { text: item, options: { bullet: true, breakLine: i < itens.length - 1 } };
    }),
    {
      x, y: y + 0.34, w, h: 1.8,
      fontSize: 11, color: SUAVE, fontFace: "Calibri",
      lineSpacingMultiple: 1.08, paraSpaceAfter: 6, isTextBox: true, margin: 0,
    }
  );
}

function bloco(s, x, y, w, h, cabecalho, corpo, corDaBorda) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, fill: { color: SUPERFICIE }, line: { color: corDaBorda || LINHA, width: 1 }, rectRadius: 0.06,
  });
  s.addText(cabecalho, {
    x: x + 0.16, y: y + 0.14, w: w - 0.32, h: 0.42,
    fontSize: 12, bold: true, color: TINTA, fontFace: "Calibri",
    lineSpacingMultiple: 0.95, isTextBox: true, margin: 0,
  });
  s.addText(corpo, {
    x: x + 0.16, y: y + 0.58, w: w - 0.32, h: h - 0.74,
    fontSize: 10, color: SUAVE, fontFace: "Calibri",
    lineSpacingMultiple: 1.06, isTextBox: true, margin: 0,
  });
}

function passo(s, x, y, w, etapa, nome, valor) {
  s.addShape(pres.ShapeType.line, {
    x, y, w, h: 0, line: { color: etapa === "IA" ? ACENTO : LINHA, width: 2 },
  });
  s.addText(etapa.toUpperCase(), {
    x, y: y + 0.1, w, h: 0.2,
    fontSize: 8, color: MUDO, fontFace: "Courier New", charSpacing: 1.2, isTextBox: true, margin: 0,
  });
  s.addText(nome, {
    x, y: y + 0.32, w, h: 0.48,
    fontSize: 12.5, bold: true, color: TINTA, fontFace: "Calibri",
    lineSpacingMultiple: 0.95, isTextBox: true, margin: 0,
  });
  s.addText(valor, {
    x, y: y + 0.84, w, h: 0.5,
    fontSize: 9, color: ACENTO, fontFace: "Courier New",
    lineSpacingMultiple: 1.1, isTextBox: true, margin: 0,
  });
}

function etiquetas(s, y, itens) {
  let x = L;
  let linha = 0;
  itens.forEach(function (item) {
    const w = 0.072 * item.texto.length + 0.34;
    if (x + w > L + LARG) { x = L; linha += 1; }
    const yy = y + linha * 0.4;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: yy, w, h: 0.3,
      fill: { color: item.cor === ACENTO ? "E7F1EB" : FUNDO },
      line: { color: item.cor || LINHA, width: 1 }, rectRadius: 0.15,
    });
    s.addText(item.texto.toUpperCase(), {
      x, y: yy, w, h: 0.3,
      fontSize: 8, color: item.cor || SUAVE, fontFace: "Courier New",
      align: "center", valign: "middle", isTextBox: true, margin: 0,
    });
    x += w + 0.12;
  });
}

function tabela(s, y, cabecalhos, linhas, larguras) {
  const cabeca = cabecalhos.map(function (texto) {
    return {
      text: texto.toUpperCase(),
      options: { bold: false, color: MUDO, fontFace: "Courier New", fontSize: 8, valign: "top" },
    };
  });
  const corpo = linhas.map(function (linha) {
    return linha.map(function (celula, i) {
      return {
        text: celula,
        options: { color: i === 0 ? TINTA : SUAVE, bold: i === 0, fontFace: "Calibri", fontSize: 10, valign: "top" },
      };
    });
  });
  s.addTable([cabeca].concat(corpo), {
    x: L, y, w: LARG, colW: larguras,
    border: { type: "solid", pt: 0.5, color: LINHA },
    margin: [6, 10, 6, 0], autoPage: false,
  });
}

// 01 · Abertura
let s = novo(1, "Abertura");
s.addText("Radar de Estágio", {
  x: L, y: 1.42, w: LARG, h: 1.05,
  fontSize: 48, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
paragrafo(s, "Um agente que busca vagas de estágio todos os dias, compara cada anúncio com o perfil do estudante e entrega no Telegram até sete recomendações explicadas.", 2.55, 14);
s.addText("Igor Costa · Ian Dias · Miguel Esteves", {
  x: L, y: 3.42, w: LARG, h: 0.26,
  fontSize: 12, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
paragrafo(s, "Métodos e Aplicações de IA · IBM3116", 3.7, 11);
etiquetas(s, 4.32, [
  { texto: "Em produção desde 28/08/2026", cor: ACENTO },
  { texto: "31 dias de entrega diária" },
  { texto: "410 recomendações enviadas" },
]);
s.addNotes("Somos três alunos e o Radar está no ar há 31 dias, entregando sozinho todo dia às 07:23. Tudo que vem a seguir são números de produção, não de simulação.");

// 02 · Problema
s = novo(2, "Problema");
titulo(s, "Para achar 7 vagas que servem,\nalguém precisa descartar 726.");
numero(s, L, 2.2, 2.6, "733", "anúncios coletados na execução de hoje");
numero(s, L + 2.95, 2.2, 2.6, "35", "sobram para um perfil, depois de curso, cidade e modalidade");
numero(s, L + 5.9, 2.2, 2.6, "7", "chegam ao estudante, as únicas acima da nota mínima");
paragrafo(s, "Esse funil existe com ou sem o Radar. Sem ele, quem descarta é o estudante — todo dia, à mão. No Brasil, 20,1 milhões podem estagiar e 1,2 milhão consegue.", 4.15, 12);
fonte(s, "ABRES — Associação Brasileira de Estágios, 2024", 4.85);
s.addNotes("O 733 é a coleta real de hoje. O 35 é o que sobra para um perfil depois do pré-filtro, e o 7 é o limite da mensagem. O trabalho de descartar 726 anúncios existe de qualquer jeito: a pergunta é quem faz.");

// 03 · Contexto e público
s = novo(3, "Contexto e público");
titulo(s, "Universitário no primeiro estágio.");
coluna(s, L, 1.62, 4.2, "Quem usa", [
  "Estudante de graduação, qualquer curso das 12 áreas do catálogo",
  "Procura o primeiro estágio e não tem tempo de triar anúncio todo dia",
  "Já usa Telegram — nenhum aplicativo novo",
]);
coluna(s, L + 4.6, 1.62, 4.2, "Como ele faz hoje", [
  "Abre vários portais e repete a mesma busca",
  "Lê o anúncio inteiro para saber se o curso é aceito",
  "Reencontra a mesma vaga republicada com outro título",
]);
numero(s, L, 3.75, 2.6, "103", "visitas na landing em 30 dias");
numero(s, L + 2.95, 3.75, 2.6, "6", "perfis criados");
numero(s, L + 5.9, 3.75, 2.6, "4", "recebendo recomendações");
s.addNotes("O público é o estudante de qualquer curso, não só de computação: o catálogo tem 12 áreas e 105 cursos. Os números embaixo são do piloto dos últimos 30 dias, e o funil aperta forte entre visita e cadastro.");

// 04 · Solução
s = novo(4, "Solução");
titulo(s, "A IA lê o anúncio. O Python decide a nota.", 26);
paragrafo(s, "O estudante preenche o perfil uma vez. Todo dia às 07:23 o sistema coleta, descarta o que não serve, pede à IA apenas os fatos do anúncio e calcula a compatibilidade por regras determinísticas.", 1.56, 12);
bloco(s, L, 2.42, 2.05, 1.62, "Coleta e filtro", "API da Adzuna, deduplicação e pré-filtro por curso, cidade e modalidade. Sem IA.");
bloco(s, L + 2.22, 2.42, 2.05, 1.62, "Extração por IA", "Gemini Flash devolve requisitos, cursos aceitos, período e modalidade em JSON validado.", ACENTO);
bloco(s, L + 4.44, 2.42, 2.05, 1.62, "Nota determinística", "45% habilidades, 15% período, 10% curso, 10% área, 10% logística, 10% interesse.");
bloco(s, L + 6.66, 2.42, 2.05, 1.62, "Entrega", "Bot no Telegram, link rastreado e um botão de resposta por vaga.");
etiquetas(s, 4.36, [
  { texto: "Python" }, { texto: "GitHub Actions" }, { texto: "Supabase / PostgreSQL" },
  { texto: "Gemini Flash" }, { texto: "Telegram Bot API" },
]);
s.addNotes("A divisão de trabalho é a decisão central do projeto: a IA só extrai fatos do anúncio e nunca vê o perfil; quem compara e pontua é Python puro. Isso torna a nota auditável e o custo viável, porque a mesma extração serve todos os usuários.");

// 05 · Demonstração
s = novo(5, "Demonstração");
titulo(s, "Cadastro no site, recomendação no Telegram.", 26);
const alturaDaTela = 2.6;
const larguraDoCadastro = alturaDaTela * (2122 / 1330);
const larguraDoTelegram = alturaDaTela * (950 / 1271);
const inicio = L + (LARG - (larguraDoCadastro + larguraDoTelegram + 0.35)) / 2;
s.addImage({ path: path.join(REPO, "apresentacao/telas/cadastro.png"), x: inicio, y: 1.6, w: larguraDoCadastro, h: alturaDaTela });
s.addImage({ path: path.join(REPO, "apresentacao/telas/demo.png"), x: inicio + larguraDoCadastro + 0.35, y: 1.6, w: larguraDoTelegram, h: alturaDaTela });
s.addText("O perfil vem antes da conta — quatro etapas, uma única vez.", {
  x: inicio, y: 4.32, w: larguraDoCadastro, h: 0.4,
  fontSize: 10, color: MUDO, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addText("A mensagem diária: nota, requisitos atendidos e o selo da fonte.", {
  x: inicio + larguraDoCadastro + 0.35, y: 4.32, w: larguraDoTelegram + 1.2, h: 0.4,
  fontSize: 10, color: MUDO, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addNotes("À esquerda, o cadastro: o perfil vem antes da conta, de propósito, para não cobrar e-mail e senha antes de mostrar o produto. À direita, a mensagem real das 07:23, com a nota, o que o perfil atende, o que falta conferir e a atribuição obrigatória da Adzuna.");

// 06 · Fluxo
s = novo(6, "Fluxo");
titulo(s, "Entrada → Processamento → IA → Resultado → Decisão", 24);
const largDoPasso = 1.62;
const vaoDoPasso = 0.18;
passo(s, L, 2.0, largDoPasso, "Entrada", "Coleta", "733 vagas\n16 requisições");
passo(s, L + (largDoPasso + vaoDoPasso), 2.0, largDoPasso, "Processamento", "Dedupe e pré-filtro", "35 candidatas\npor perfil");
passo(s, L + 2 * (largDoPasso + vaoDoPasso), 2.0, largDoPasso, "IA", "Extração de fatos", "4 requisições\nao Gemini");
passo(s, L + 3 * (largDoPasso + vaoDoPasso), 2.0, largDoPasso, "Resultado", "Nota e ranking", "23 vagas\npara 4 pessoas");
passo(s, L + 4 * (largDoPasso + vaoDoPasso), 2.0, largDoPasso, "Decisão", "Telegram", "a pessoa abre\ne responde");
paragrafo(s, "A extração é por vaga, não por pessoa: a mesma leitura serve todos os perfis, e por isso um usuário novo quase não custa. Números da execução de 28/09.", 3.8, 12);
s.addNotes("Da coleta à mensagem são cinco etapas, e só uma usa IA. As 4 requisições ao Gemini valeram para os quatro usuários juntos, porque a extração fica guardada por vaga e é reaproveitada entre pessoas e entre dias.");

// 07 · Casos reais
s = novo(7, "Casos reais");
titulo(s, "A indústria já automatizou a triagem.");
tabela(s, 1.6, ["Empresa", "O que fez", "Resultado"], [
  ["Unilever", "Triagem de 250 mil candidaturas por ciclo com entrevista em vídeo e jogos cognitivos", "Contratação de 4 meses para 4 semanas; 50 mil horas de entrevista economizadas"],
  ["Gupy", "ATS brasileiro com NLP na ordenação de candidatos, em 2.300 empresas clientes (2021)", "480 mil vagas preenchidas em 2021, com redução de até 80% no tempo de contratação"],
  ["LinkedIn", "Casa 50 milhões de vagas com cada usuário num funil de quatro estágios", "Lição da própria engenharia: otimizar por clique premia título sensacionalista"],
], [1.3, 3.9, 3.6]);
paragrafo(s, "Todos filtram pessoas para a empresa. O Radar inverte o lado: filtra vagas para o estudante, então nunca descarta alguém — no máximo deixa de recomendar uma vaga.", 3.95, 12);
fonte(s, "Google for Startups, história da Gupy · LinkedIn Engineering Blog · estudos de caso sobre HireVue e Pymetrics na Unilever", 4.75);
s.addNotes("A mecânica não é nova: extrair requisitos de texto livre, comparar com um perfil e ordenar. O que muda é o lado do funil. Como esses sistemas decidem sobre pessoas, o risco deles é discriminar; o nosso risco é só deixar de recomendar uma vaga.");

// 08 · Proposta de valor
s = novo(8, "Proposta de valor");
titulo(s, "O trabalho repetitivo sai do estudante.");
tabela(s, 1.6, ["Etapa", "Sem o Radar", "Com o Radar"], [
  ["Procurar", "Abrir portais e repetir a busca todo dia", "Uma execução diária, sem ação do estudante"],
  ["Triar", "Ler anúncio por anúncio para ver se o curso é aceito", "733 anúncios viram 7, já conferidos"],
  ["Entender", "Deduzir dos requisitos se vale a pena", "Nota de 0 a 100 com o que atende e o que falta"],
  ["Repetir", "Reencontrar a mesma vaga republicada", "Deduplicação e histórico por pessoa"],
], [1.3, 3.75, 3.75]);
numero(s, L, 4.05, 2.6, "1,7 min", "do cadastro à primeira lista, mediana observada");
numero(s, L + 2.95, 4.05, 2.6, "≈ R$ 0", "custo de um usuário novo: a extração é por vaga");
numero(s, L + 5.9, 4.05, 2.6, "105", "cursos reconhecidos, não só computação");
s.addNotes("O ganho não é achar uma vaga que ninguém acharia: é tirar do estudante o trabalho repetido. E o custo marginal perto de zero é consequência direta da arquitetura, não de otimização.");

// 09 · Riscos, limites e dados
s = novo(9, "Riscos, limites e dados");
titulo(s, "O motor funciona. Falta a prova de valor.", 26);
coluna(s, L, 1.62, 4.2, "Riscos e limitações", [
  "Zero vaga marcada como útil em 410 entregas: 12 aberturas e 6 respostas",
  "Uma fonte só: a Adzuna responde por tudo, e a Gupy saiu pelos termos de uso",
  "O estudante é um pagador improvável: os concorrentes são gratuitos para ele",
]);
coluna(s, L + 4.6, 1.62, 4.2, "Dados e privacidade", [
  "Origem: API oficial da Adzuna, com atribuição obrigatória em cada anúncio",
  "Formato: JSON das vagas e JSON validado por schema na saída da IA",
  "O perfil nunca vai para a IA: o prompt só contém o anúncio",
]);
etiquetas(s, 4.05, [
  { texto: "2.020 testes automatizados", cor: ACENTO },
  { texto: "Domínio próprio pendente", cor: ALERTA },
  { texto: "Sem validação por estudantes", cor: RISCO },
]);
s.addNotes("O risco que decide o projeto não é técnico. Sem ninguém marcando uma vaga como útil, não há como recalibrar a nota, e por isso a regra do projeto é não mexer em peso nenhum sem um caso real vindo de usuário.");

// 10 · Próximos passos
s = novo(10, "Próximos passos");
titulo(s, "Protótipo → MVP → Piloto → Implantação", 28);
bloco(s, L, 1.68, 2.05, 1.5, "Protótipo · agosto", "Coleta e nota em Python, com perfil fixo e sem banco.");
bloco(s, L + 2.22, 1.68, 2.05, 1.5, "MVP · 28/08", "Banco, conta no site, Telegram e entrega diária automática.", ACENTO);
bloco(s, L + 4.44, 1.68, 2.05, 1.5, "Piloto · agora", "6 perfis, 4 ativados, 410 recomendações. Falta o sinal de utilidade.", ALERTA);
bloco(s, L + 6.66, 1.68, 2.05, 1.5, "Implantação · a seguir", "Domínio próprio, textos legais aprovados e um pagador definido.");
s.addShape(pres.ShapeType.roundRect, {
  x: L, y: 3.48, w: LARG, h: 1.34, fill: { color: SUPERFICIE }, line: { color: LINHA, width: 1 }, rectRadius: 0.06,
});
s.addText("A pergunta honesta: isso vira negócio?", {
  x: L + 0.26, y: 3.68, w: LARG - 0.52, h: 0.4,
  fontSize: 20, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addText("Tecnicamente, já roda sozinho há 31 dias. Como produto, ainda falta a prova de que a recomendação serve — e é isso, não mais código, que decide o próximo passo.", {
  x: L + 0.26, y: 4.14, w: LARG - 0.52, h: 0.56,
  fontSize: 11.5, color: SUAVE, fontFace: "Calibri", lineSpacingMultiple: 1.1, isTextBox: true, margin: 0,
});
s.addNotes("Fechamos com a pergunta que o próprio projeto ainda não respondeu. O próximo passo não é mais código: é conversar com quem recebeu as vagas e descobrir por que ninguém respondeu.");

pres.writeFile({ fileName: path.join(REPO, "apresentacao/radar-de-estagio-pit.pptx") }).then(function (nome) {
  console.log("gerado: " + nome);
});
