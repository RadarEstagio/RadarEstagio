const pptxgen = require("pptxgenjs");
const path = require("path");

const REPO = "/Users/igorcosta/Projetos/RadarEstagio";
const FUNDO = "0F1512";
const CARTAO = "1A241F";
const ACENTO = "5CB584";
const CLARO = "9FD3B2";
const TINTA = "EEF3EF";
const SUAVE = "C2CFC7";
const MUDO = "8FA298";
const ALERTA = "E5B567";
const RISCO = "F19A8F";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Igor Costa, Ian Dias e Miguel Esteves";
pres.title = "Radar de Estágio";

const L = 0.55;
const LARG = 8.9;

function novo(numero, seccao, complemento) {
  const s = pres.addSlide();
  s.background = { color: FUNDO };
  s.addText(
    [
      { text: String(numero).padStart(2, "0") + " · " + seccao.toUpperCase(), options: { color: CLARO, bold: true } },
      { text: "   " + complemento.toUpperCase(), options: { color: MUDO } },
    ],
    { x: L, y: 0.34, w: LARG, h: 0.24, fontSize: 9, fontFace: "Courier New", charSpacing: 1.4, isTextBox: true, margin: 0 }
  );
  return s;
}

function titulo(s, texto, y = 0.72, tamanho = 34) {
  s.addText(texto, {
    x: L, y, w: LARG, h: (texto.indexOf("\n") >= 0 ? 1.25 : 0.62) * (tamanho >= 30 ? 1 : 0.92),
    fontSize: tamanho, bold: true, color: TINTA, fontFace: "Calibri",
    lineSpacingMultiple: 0.92, isTextBox: true, margin: 0,
  });
}

function cartao(s, x, y, w, h, tituloTexto, corpo, cor = CARTAO) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, fill: { color: cor }, line: { color: "23302A", width: 1 }, rectRadius: 0.08,
  });
  s.addText(tituloTexto, {
    x: x + 0.18, y: y + 0.13, w: w - 0.36, h: 0.28,
    fontSize: 13, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
  });
  s.addText(corpo, {
    x: x + 0.18, y: y + 0.42, w: w - 0.36, h: h - 0.56,
    fontSize: 10.5, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.05,
  });
}

function numero(s, x, y, w, rotulo, valor, nota) {
  s.addText(rotulo.toUpperCase(), {
    x, y, w, h: 0.22, fontSize: 8.5, color: MUDO, fontFace: "Courier New", charSpacing: 1.2, isTextBox: true, margin: 0,
  });
  s.addText(valor, {
    x, y: y + 0.2, w, h: 0.58, fontSize: 34, bold: true, color: CLARO, fontFace: "Calibri", isTextBox: true, margin: 0,
  });
  s.addText(nota, {
    x, y: y + 0.78, w, h: 0.42, fontSize: 10, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.05,
  });
}

function etiquetas(s, y, itens) {
  let x = L;
  let linha = 0;
  itens.forEach(function (item) {
    const w = 0.075 * item.texto.length + 0.3;
    if (x + w > L + LARG) { x = L; linha += 1; }
    const yy = y + linha * 0.38;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: yy, w, h: 0.3, fill: { color: FUNDO }, line: { color: item.cor || "2E3D36", width: 1 }, rectRadius: 0.15,
    });
    s.addText(item.texto.toUpperCase(), {
      x, y: yy, w, h: 0.3, fontSize: 8.5, color: item.cor || SUAVE, fontFace: "Courier New",
      align: "center", valign: "middle", isTextBox: true, margin: 0,
    });
    x += w + 0.12;
  });
}

// 01
let s = novo(1, "Abertura", "Métodos e Aplicações de IA · IBM3116");
s.addText("Radar de Estágio", {
  x: L, y: 0.78, w: LARG, h: 1.1, fontSize: 54, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addText("Um agente que garimpa vagas de estágio todos os dias, compara cada anúncio com o perfil do estudante e entrega no Telegram até sete recomendações explicadas — só quando há vagas compatíveis.", {
  x: L, y: 1.92, w: 7.6, h: 0.8, fontSize: 14, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.1,
});
cartao(s, L, 2.92, 2.85, 0.95, "Igor Costa", "Pipeline, matching e banco");
cartao(s, L + 3.0, 2.92, 2.85, 0.95, "Ian Dias", "Operação, coleta e entrega");
cartao(s, L + 6.0, 2.92, 2.9, 0.95, "Miguel Esteves", "Cadastro, dados e privacidade");
etiquetas(s, 4.12, [
  { texto: "Em produção desde 28/08/2026", cor: ACENTO },
  { texto: "31 dias de entregas diárias" },
  { texto: "410 recomendações enviadas" },
]);
s.addNotes("Somos três. O produto está no ar desde 28 de agosto, entregando todo dia às 7h23, sem intervenção.");

// 02
s = novo(2, "Problema", "Específico e mensurável");
titulo(s, "Para achar 7 vagas que servem,\nalguém precisa descartar 726.");
numero(s, L, 2.05, 2.6, "Coletadas hoje", "733", "anúncios de estágio na execução das 07:23");
numero(s, L + 2.9, 2.05, 2.6, "Sobraram para um perfil", "35", "depois de curso, cidade e modalidade");
numero(s, L + 5.8, 2.05, 2.6, "Entregues", "7", "as únicas acima da nota mínima");
s.addText("Esse funil existe todo dia, com ou sem o Radar. Sem ele, é o estudante que abre os portais, lê requisitos repetidos e descarta à mão — e ainda perde a vaga que fechou antes de ele chegar.", {
  x: L, y: 3.5, w: 4.6, h: 1.1, fontSize: 12, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.1,
});
cartao(s, L + 5.0, 3.45, 3.9, 1.45, "O tamanho do mercado",
  "20,1 milhões de estudantes aptos a estagiar no Brasil; 1,2 milhão conseguem — cerca de 6%. Entre 40% e 60% dos estagiários são efetivados.\nFonte: ABRES, 2024");
s.addNotes("O número do slide é de hoje: 733 anúncios coletados, 35 candidatas para um perfil, 7 entregues.");

// 03
s = novo(3, "Contexto e público", "Quem usa e como é hoje");
titulo(s, "Universitário no primeiro estágio.", 0.72, 30);
cartao(s, L, 1.78, 4.3, 1.6, "Quem",
  "• Graduação em qualquer curso do catálogo: 12 áreas, 45 subáreas, 105 cursos\n• Busca o primeiro estágio, sem tempo de triar anúncio todo dia\n• Já usa Telegram: nenhum aplicativo novo para instalar");
cartao(s, L + 4.6, 1.78, 4.3, 1.6, "O processo atual dele",
  "• Abrir vários portais e repetir a mesma busca\n• Ler requisitos para saber se o curso é aceito\n• Reencontrar a mesma vaga republicada\n• Descobrir tarde a vaga que combinava");
s.addText("PILOTO, ÚLTIMOS 30 DIAS", {
  x: L, y: 3.52, w: LARG, h: 0.22, fontSize: 8.5, color: MUDO, fontFace: "Courier New", charSpacing: 1.2, isTextBox: true, margin: 0,
});
numero(s, L, 3.8, 2.6, "Visitas", "103", "identidades distintas na landing");
numero(s, L + 2.9, 3.8, 2.6, "Perfis criados", "6", "4 vincularam o Telegram");
numero(s, L + 5.8, 3.8, 2.6, "Ativados", "4", "receberam a primeira recomendação");
s.addNotes("O catálogo cobre 12 áreas: não é um produto só de computação.");

// 04
s = novo(4, "Solução", "O que faz, com o quê, e onde entra a IA");
titulo(s, "A IA lê o anúncio. O Python decide a nota.", 0.72, 30);
s.addText("O estudante preenche o perfil uma vez. Todo dia às 07:23 o sistema coleta, descarta o que não serve, pede à IA apenas os fatos do anúncio e calcula a compatibilidade por regras determinísticas. A mesma extração serve todos os usuários, e a mesma vaga com o mesmo perfil dá sempre a mesma nota.", {
  x: L, y: 1.75, w: 4.1, h: 1.7, fontSize: 12, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.12,
});
cartao(s, L + 4.4, 1.7, 2.15, 1.15, "Coleta e filtro", "API da Adzuna, deduplicação e pré-filtro — sem IA");
cartao(s, L + 6.75, 1.7, 2.15, 1.15, "Extração por IA", "Gemini Flash devolve requisitos em JSON validado");
cartao(s, L + 4.4, 2.95, 2.15, 1.15, "Nota determinística", "45% habilidades, 15% período, 10% curso, área e logística");
cartao(s, L + 6.75, 2.95, 2.15, 1.15, "Entrega e feedback", "Bot no Telegram, link rastreado e feedback por vaga");
etiquetas(s, 4.32, [
  { texto: "Python 3.12" }, { texto: "GitHub Actions" }, { texto: "Supabase" },
  { texto: "Gemini Flash", cor: ACENTO }, { texto: "Telegram" }, { texto: "Cloudflare" },
]);
s.addNotes("O prompt nunca contém o perfil: a IA só lê o anúncio. Isso deixa a nota auditável e o custo por vaga, não por usuário.");

// 05
s = novo(5, "Demonstração", "As telas do produto");
titulo(s, "Cadastro, recomendação, conta.", 0.72, 30);
s.addImage({ path: path.join(REPO, "apresentacao/telas/demo.png"), x: L, y: 1.78, h: 3.25, w: 3.6, sizing: { type: "contain", w: 3.6, h: 3.25 } });
s.addImage({ path: path.join(REPO, "apresentacao/telas/cadastro.png"), x: L + 4.0, y: 1.78, w: 4.9, h: 2.3, sizing: { type: "contain", w: 4.9, h: 2.3 } });
s.addText("A mensagem diária traz nota, requisitos atendidos, o que conferir e o selo da fonte, exigido pelos termos da Adzuna. O cadastro tem quatro etapas e pede a conta só no fim.", {
  x: L + 4.0, y: 4.2, w: 4.9, h: 0.85, fontSize: 11, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.1,
});
s.addNotes("Demonstração ao vivo se der tempo: abrir o site e mostrar a mensagem real no Telegram.");

// 06
s = novo(6, "Fluxo", "Números reais da execução de 28/09");
titulo(s, "Entrada → Processamento → IA → Resultado → Decisão", 0.72, 26);
const etapas = [
  ["Entrada", "Coleta", "Adzuna, por termo e cidade", "733 vagas · 16 requisições"],
  ["Processamento", "Dedupe e pré-filtro", "Republicação, curso, cidade, nível", "35 candidatas por perfil"],
  ["IA", "Extração de fatos", "Um lote por chamada, cache compartilhado", "4 requisições ao Gemini"],
  ["Resultado", "Nota e ranking", "Regras em Python, recalculadas sempre", "23 vagas para 4 pessoas"],
  ["Decisão", "Telegram", "A pessoa abre e se candidata na fonte", "7 botões de feedback"],
];
etapas.forEach(function (e, i) {
  const x = L + i * 1.79;
  const destaque = e[0] === "IA";
  s.addShape(pres.ShapeType.roundRect, {
    x, y: 1.78, w: 1.66, h: 1.9,
    fill: { color: destaque ? "1E3128" : CARTAO },
    line: { color: destaque ? ACENTO : "23302A", width: 1 }, rectRadius: 0.08,
  });
  s.addText(e[0].toUpperCase(), { x: x + 0.14, y: 1.88, w: 1.4, h: 0.2, fontSize: 8, color: ACENTO, fontFace: "Courier New", charSpacing: 1, isTextBox: true, margin: 0 });
  s.addText(e[1], { x: x + 0.14, y: 2.1, w: 1.4, h: 0.46, fontSize: 13, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0 });
  s.addText(e[2], { x: x + 0.14, y: 2.58, w: 1.4, h: 0.62, fontSize: 9.5, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.05 });
  s.addText(e[3], { x: x + 0.14, y: 3.22, w: 1.4, h: 0.4, fontSize: 9, color: CLARO, fontFace: "Courier New", isTextBox: true, margin: 0, lineSpacingMultiple: 1.05 });
});
numero(s, L, 3.95, 2.6, "Do cadastro à 1ª lista", "1,7 min", "mediana observada em 4 casos");
numero(s, L + 2.9, 3.95, 2.6, "Extrações reaproveitadas", "1.670", "uma por vaga, servem todos os perfis");
numero(s, L + 5.8, 3.95, 2.6, "Custo por lote de 10 vagas", "R$ 0,066", "medido em 11/09");
s.addNotes("A IA entra uma vez por vaga. Dobrar os usuários não dobra as requisições: é o que torna o custo viável.");

// 07
s = novo(7, "Casos reais", "Quem já fez algo parecido");
titulo(s, "A indústria automatizou a triagem.", 0.72, 28);
s.addTable(
  [
    [
      { text: "Empresa", options: { bold: true, color: MUDO, fontSize: 9, fontFace: "Courier New" } },
      { text: "Problema", options: { bold: true, color: MUDO, fontSize: 9, fontFace: "Courier New" } },
      { text: "Tecnologia", options: { bold: true, color: MUDO, fontSize: 9, fontFace: "Courier New" } },
      { text: "Resultados", options: { bold: true, color: MUDO, fontSize: 9, fontFace: "Courier New" } },
    ],
    ["Unilever", "250 mil candidaturas por ciclo para 800 vagas; triagem de até 4 meses", "HireVue (entrevista em vídeo) e Pymetrics (jogos cognitivos)", "−90% no tempo de contratação, 50 mil horas e £1 mi/ano economizados, +16% em diversidade"],
    ["Gupy", "Volume de currículos por vaga inviabiliza a triagem manual", "NLP na ordenação e recomendação, em 2.300 empresas clientes (2021)", "480 mil vagas preenchidas em 2021 e até −80% no tempo de contratação, com 22,5 milhões de candidatos na base"],
    ["LinkedIn", "Casar 50 milhões de vagas com cada usuário em tempo real", "Funil de quatro estágios, com reordenação por regras de negócio", "Lição da própria engenharia: otimizar por clique premia título sensacionalista"],
  ],
  {
    x: L, y: 1.82, w: LARG, colW: [1.2, 2.5, 2.4, 2.8],
    fontSize: 9.5, color: SUAVE, fontFace: "Calibri",
    fill: { color: CARTAO }, border: { type: "solid", color: "23302A", pt: 1 },
    valign: "top", margin: 6, autoPage: false,
  }
);
cartao(s, L, 3.98, 4.3, 1.14, "O que se parece", "Extrair requisitos de texto livre, comparar com um perfil e ordenar. A decisão final fica com regras explícitas, não com o modelo.");
cartao(s, L + 4.6, 3.98, 4.3, 1.14, "O que muda", "Eles filtram pessoas para a empresa. O Radar filtra vagas para o estudante: nunca descarta alguém.");
s.addNotes("Unilever e Gupy provam a mecânica; o LinkedIn dá o alerta que seguimos: não calibrar por clique.");

// 08
s = novo(8, "Proposta de valor", "O que o processo ganha");
titulo(s, "O trabalho repetitivo sai do estudante.", 0.72, 30);
s.addTable(
  [
    [
      { text: "Etapa", options: { bold: true, color: MUDO, fontSize: 9, fontFace: "Courier New" } },
      { text: "Sem o Radar", options: { bold: true, color: MUDO, fontSize: 9, fontFace: "Courier New" } },
      { text: "Com o Radar", options: { bold: true, color: MUDO, fontSize: 9, fontFace: "Courier New" } },
    ],
    ["Procurar", "Abrir portais e repetir a busca todo dia", "Uma execução diária às 07:23, sem ação do estudante"],
    ["Triar", "Ler anúncio por anúncio para ver se o curso é aceito", "733 anúncios viram 7, com curso, período e cidade conferidos"],
    ["Entender", "Deduzir dos requisitos se vale a pena", "Nota de 0 a 100 com o que atende e o que falta conferir"],
    ["Repetir", "Reencontrar a mesma vaga republicada", "Deduplicação e histórico por pessoa impedem o reenvio"],
  ],
  {
    x: L, y: 1.78, w: LARG, colW: [1.3, 3.6, 4.0],
    fontSize: 10, color: SUAVE, fontFace: "Calibri",
    fill: { color: CARTAO }, border: { type: "solid", color: "23302A", pt: 1 },
    valign: "top", margin: 6, autoPage: false,
  }
);
numero(s, L, 3.92, 2.6, "Tempo até a primeira lista", "1,7 min", "do cadastro à mensagem no Telegram");
numero(s, L + 2.9, 3.92, 2.6, "Custo por usuário novo", "≈ R$ 0", "a extração é por vaga, não por pessoa");
numero(s, L + 5.8, 3.92, 2.6, "Cobertura do catálogo", "12 áreas", "105 cursos reconhecidos");
s.addNotes("O ganho não é achar vaga que ninguém tem: é tirar a triagem diária do estudante.");

// 09
s = novo(9, "Riscos, limites e dados", "O que ainda não está provado");
titulo(s, "O motor funciona. Falta a prova de valor.", 0.72, 30);
cartao(s, L, 1.8, 4.3, 2.1, "Riscos e limitações",
  "• Zero vaga marcada como útil em 410 entregas: 12 aberturas e 6 respostas\n• Uma fonte só: a Adzuna responde por tudo\n• O custo cresce com cidades e áreas, não com usuários\n• Estudante é pagador improvável: concorrentes são gratuitos para ele, e a lei só veda cobrança a agentes de integração");
cartao(s, L + 4.6, 1.8, 4.3, 2.1, "Dados: origem, formato e privacidade",
  "• Origem: API oficial da Adzuna, com atribuição obrigatória\n• Formato: JSON das vagas e JSON validado por schema na saída da IA\n• Privacidade: RLS por usuário, exportação e exclusão com 60 dias\n• O perfil nunca vai para a IA: o prompt só contém o anúncio");
etiquetas(s, 4.1, [
  { texto: "2.020 testes automatizados", cor: ACENTO },
  { texto: "30 migrations versionadas", cor: ACENTO },
  { texto: "Domínio pendente", cor: ALERTA },
  { texto: "Sem validação real", cor: RISCO },
]);
s.addNotes("A limitação honesta: ninguém marcou vaga como útil ainda. É o que decide se continua.");

// 10
s = novo(10, "Próximos passos", "Onde estamos e o que falta");
titulo(s, "Protótipo → MVP → Piloto → Implantação", 0.72, 30);
const fases = [
  ["Agosto", "Protótipo", "Coleta e nota em Python, com perfil fixo", ACENTO],
  ["28/08", "MVP", "Banco, conta, vínculo e entrega diária", ACENTO],
  ["Agora", "Piloto", "6 perfis, 4 ativados, 410 recomendações", ALERTA],
  ["A seguir", "Implantação", "Domínio, CAPTCHA, textos legais e um pagador", MUDO],
];
fases.forEach(function (f, i) {
  const x = L + i * 2.24;
  s.addText(f[0].toUpperCase(), { x, y: 1.85, w: 2.0, h: 0.2, fontSize: 8.5, color: f[3], fontFace: "Courier New", charSpacing: 1.1, isTextBox: true, margin: 0 });
  s.addText(f[1], { x, y: 2.07, w: 2.0, h: 0.34, fontSize: 16, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0 });
  s.addText(f[2], { x, y: 2.43, w: 2.0, h: 0.7, fontSize: 10, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.05 });
});
cartao(s, L, 3.3, 4.3, 1.6, "As três próximas decisões",
  "• Conversar com quem recebeu: por que abriu 12 vagas e não respondeu nada?\n• Fechar o ciclo de feedback antes de mexer em qualquer peso da nota\n• Testar instituição ou empresa como pagador, já que o estudante não pode ser");
s.addText("Isso vira negócio?", {
  x: L + 4.6, y: 3.35, w: 4.3, h: 0.45, fontSize: 22, bold: true, color: TINTA, fontFace: "Calibri", isTextBox: true, margin: 0,
});
s.addText("Tecnicamente, já roda sozinho há 31 dias. Como produto, falta a prova de que a recomendação serve — e é isso, não mais código, que decide o próximo passo.", {
  x: L + 4.6, y: 3.85, w: 4.3, h: 1.0, fontSize: 12, color: SUAVE, fontFace: "Calibri", isTextBox: true, margin: 0, lineSpacingMultiple: 1.1,
});
s.addNotes("Fechamento: o próximo passo não é mais código, é conversa com usuário.");

pres.writeFile({ fileName: path.join(REPO, "apresentacao/radar-de-estagio-pit.pptx") }).then(function (nome) {
  console.log("gerado:", nome);
});
