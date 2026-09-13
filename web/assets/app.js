const botaoDoTema = document.querySelector("#theme-toggle");
const CHAVE_DO_TEMA = "radar-tema";

function mostrarTema(tema) {
  document.documentElement.dataset.tema = tema;
  botaoDoTema.setAttribute("aria-pressed", String(tema === "escuro"));
}

mostrarTema(document.documentElement.dataset.tema === "escuro" ? "escuro" : "claro");
botaoDoTema.addEventListener("click", () => {
  const tema = document.documentElement.dataset.tema === "escuro" ? "claro" : "escuro";
  mostrarTema(tema);
  try {
    localStorage.setItem(CHAVE_DO_TEMA, tema);
  } catch {}
});

const demonstracaoDoChat = document.querySelector("[data-chat-demo]");
const reduzirMovimento = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
const ROLAGEM_MINIMA_ATE_CHAT = 90;

if (demonstracaoDoChat && !reduzirMovimento) {
  const reproduzirChatAoRolar = () => {
    const limitesDoChat = demonstracaoDoChat.getBoundingClientRect();
    const chatEntrouNaAreaUtil = limitesDoChat.top <= window.innerHeight * 0.82 && limitesDoChat.bottom >= 0;
    if (window.scrollY < ROLAGEM_MINIMA_ATE_CHAT || !chatEntrouNaAreaUtil) return;
    demonstracaoDoChat.classList.remove("is-waiting");
    demonstracaoDoChat.classList.add("is-playing");
    window.removeEventListener("scroll", reproduzirChatAoRolar);
  };
  window.addEventListener("scroll", reproduzirChatAoRolar, { passive: true });
} else if (demonstracaoDoChat) {
  demonstracaoDoChat.classList.remove("is-waiting");
  demonstracaoDoChat.classList.add("is-playing");
}

const dialog = document.querySelector("#signup-dialog");
const accountPage = document.querySelector("#account-page");
const accountContent = document.querySelector("#account-content");
const landingPage = document.querySelector("#landing-page");
const dialogShell = document.querySelector(".dialog-shell");
const landingTitle = document.title;
const form = document.querySelector("#signup-form");
const successState = document.querySelector("#success-state");
const progressWrap = document.querySelector(".progress-wrap");
const progressLabel = document.querySelector("#progress-label");
const progressPercent = document.querySelector("#progress-percent");
const progressBar = document.querySelector("#progress-bar");
const progressTrack = document.querySelector("#progress-track");
const formMessage = document.querySelector("#form-message");
const formNotice = document.querySelector("#form-notice");
const assistanceMessage = document.querySelector("#assistance-message");
const assistanceNotice = document.querySelector("#assistance-notice");
const submitProfile = document.querySelector("#submit-profile");
const submitLabel = document.querySelector("#submit-label");
const toggleAuthMode = document.querySelector("#toggle-auth-mode");
const telegramLink = document.querySelector("#telegram-link");
const accountState = document.querySelector("#account-state");
const accountMessage = document.querySelector("#account-message");
const accountNotice = document.querySelector("#account-notice");
const accountConfirm = document.querySelector("#account-confirm");
const toggleDeliveries = document.querySelector("#toggle-deliveries");
const accountNavLinks = [...document.querySelectorAll(".account-nav a")];
const accountNavEntries = accountNavLinks.map((link) => ({
  link,
  target: document.querySelector(link.hash),
}));
const pauseReason = document.querySelector("#pause-reason");
const pauseReasonMessage = document.querySelector("#pause-reason-message");
const savePauseReason = document.querySelector("#save-pause-reason");
const skipPauseReason = document.querySelector("#skip-pause-reason");
const credenciais = document.querySelector("#credenciais");
const chamadasDeCadastro = [...document.querySelectorAll(".js-open-signup")];
const chamadasDeLogin = [...document.querySelectorAll(".js-open-login")];
const rotulosDeCadastro = new Map(
  chamadasDeCadastro.map((botao) => [botao, botao.firstChild.textContent]),
);
let usuarioAutenticado = false;
const accountSwitch = document.querySelector("#account-switch");
let editandoPerfilExistente = false;
const MENSAGEM_SEM_SESSAO = "Sua sessão expirou. Feche e entre de novo para continuar.";
const MENSAGEM_SEM_PERFIL = "Não encontramos seu perfil. Feche e entre de novo.";
const MENSAGEM_ENTREGAS_JA_MUDARAM = "As entregas já tinham mudado em outro lugar. Nada foi alterado; a tela mostra o estado atual.";
const COLUNAS_DO_PERFIL = "curso,periodo,habilidades,cidade,modalidade,areas_de_interesse,telegram_chat_id,token_vinculo,ativo,motivo_pausa,excluida_em,aceita_emails,termos_aceitos_em,versao_dos_termos";
const DIAS_ATE_APAGAR = 60;
const VERSAO_DOS_TERMOS = "2026-09-05";
const MAXIMO_DE_HABILIDADES = 50;
const TAMANHO_MAXIMO_DA_HABILIDADE = 100;
const MOTIVOS_PAUSA = new Set([
  "conseguiu_estagio",
  "interrompeu_busca",
  "sem_vagas_uteis",
  "frequencia",
  "outro",
]);
let assistanceMode = null;
let recoverySession = false;
let resendAvailableAt = 0;
let resendTimer = null;
let captchaWidget = null;
let captchaToken = "";
const authReturn = new URLSearchParams(window.location.hash.slice(1));
const authQuery = new URLSearchParams(window.location.search);
const returningFromAuth = authReturn.has("access_token") || authQuery.has("code");
const returningFromRecovery = authReturn.get("type") === "recovery" || authQuery.get("fluxo") === "recuperar";
const authLinkError = authReturn.get("error_code") || authQuery.get("error_code") || authReturn.get("error") || authQuery.get("error");
const pendingProfileKey = "radar-perfil-pendente";
const eventSessionKey = "radar-sessao-eventos";
const landingViewKey = "radar-landing-vista";
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
let currentStep = 1;
let authMode = "signup";
let radarClient = null;
const selectedSkills = new Set();
let continuarSemHabilidades = false;
const previousStep = document.querySelector("#previous-step");
const nextStep = document.querySelector("#next-step");
const continuarSemHabilidadesButton = document.querySelector("#continue-without-skills");
const PASSO_CONTA = 1;
const PASSO_MOMENTO = 2;
const PASSO_HABILIDADES = 3;
const PASSO_PREFERENCIAS = 4;
const PROGRESSO_AO_CONFIRMAR = 100;
const PASSOS_DO_PERFIL = [PASSO_MOMENTO, PASSO_HABILIDADES, PASSO_PREFERENCIAS];
let passosAtivos = [...PASSOS_DO_PERFIL, PASSO_CONTA];
const modalidadesAceitas = new Set(["remoto", "presencial", "hibrido", "indiferente"]);
const campoDeAreas = document.querySelector("#campo-areas");
const gradeDeAreas = document.querySelector("#grade-de-areas");
let catalogoDeAreas = null;
let areasEscolhidas = new Set();
let areasSalvas = [];
let identidadeDoFormulario = 0;
let requisicaoDeHabilidades = 0;
let requisicaoDeAreas = 0;
const MAXIMO_DE_CIDADES_SUGERIDAS = 8;
const campoDeCidade = form.elements.cidade;
const botaoDeCidades = document.querySelector("#mostrar-cidades");
const listaDeCidades = document.querySelector("#lista-de-cidades");
const avisoDeCidades = document.querySelector("#cities-catalog-notice");
let catalogoDeCidades = null;
let carregamentoDeCidades = null;
let cidadeDestacada = -1;

function ativarSecaoDaConta(linkAtivo) {
  accountNavLinks.forEach((link) => {
    const ativo = link === linkAtivo;
    link.classList.toggle("is-active", ativo);
    if (ativo) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}

const conteudoDasSecoesDaConta = {
  "#account-overview-panel": {
    titulo: "Conta",
    descricao: "Confira seu perfil de busca e controle como o Radar entrega suas recomendações.",
  },
  "#account-delivery-panel": {
    titulo: "Entregas",
    descricao: "Controle o envio das vagas e as comunicações do Radar.",
  },
  "#account-data-panel": {
    titulo: "Dados e acesso",
    descricao: "Baixe suas informações ou encerre a sessão atual.",
  },
  "#account-privacy-panel": {
    titulo: "Privacidade",
    descricao: "Gerencie o vínculo com o Telegram e as ações permanentes da sua conta.",
  },
};

function mostrarSecaoDaConta(linkAtivo, atualizarEndereco = true) {
  const entradaAtiva = accountNavEntries.find(({ link }) => link === linkAtivo) ?? accountNavEntries[0];
  accountNavEntries.forEach(({ target }) => {
    if (target) target.hidden = target !== entradaAtiva.target;
  });
  ativarSecaoDaConta(entradaAtiva.link);
  const conteudo = conteudoDasSecoesDaConta[entradaAtiva.link.hash];
  document.querySelector("#account-title").textContent = conteudo.titulo;
  document.querySelector(".account-heading > p:last-child").textContent = conteudo.descricao;
  if (atualizarEndereco) {
    const url = new URL(window.location.href);
    url.hash = entradaAtiva.link.hash;
    window.history.replaceState(null, "", url);
  }
  window.scrollTo(0, 0);
}

accountNavEntries.forEach(({ link, target }) => {
  if (!target) return;
  link.addEventListener("click", (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    mostrarSecaoDaConta(link);
  });
});

window.addEventListener("hashchange", () => {
  if (accountPage.hidden || accountState.hidden) return;
  const entrada = accountNavEntries.find(({ link }) => link.hash === window.location.hash);
  if (entrada) mostrarSecaoDaConta(entrada.link, false);
});

function normalizarTexto(texto) {
  return texto
    .replace(/[\u2010\u2011\u2013\u2014\u2212]/g, "-")
    .normalize("NFKD")
    .replace(/[^\x00-\x7f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

async function carregarAreas() {
  if (catalogoDeAreas) return catalogoDeAreas;
  try {
    const resposta = await fetch("assets/areas.json");
    catalogoDeAreas = resposta.ok ? await resposta.json() : null;
  } catch {
    catalogoDeAreas = null;
  }
  return catalogoDeAreas;
}

function textoDeBusca(texto) {
  return normalizarTexto(texto.replace(/[\u2018\u2019\u02bc\u2032]/g, " "))
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function carregarCidades() {
  if (catalogoDeCidades) return Promise.resolve(catalogoDeCidades);
  carregamentoDeCidades ??= fetch("assets/cidades.json")
    .then((resposta) => (resposta.ok ? resposta.json() : null))
    .catch(() => null)
    .then((cidades) => {
      carregamentoDeCidades = null;
      avisoDeCidades.hidden = Array.isArray(cidades);
      if (!Array.isArray(cidades)) return null;
      catalogoDeCidades = cidades.map((nome) => ({
        nome,
        busca: textoDeBusca(nome),
        municipio: textoDeBusca(nome.slice(0, nome.lastIndexOf(","))),
      }));
      return catalogoDeCidades;
    });
  return carregamentoDeCidades;
}

function homonimasDe(busca) {
  return catalogoDeCidades.filter((cidade) => cidade.municipio === busca);
}

function cidadeDaLista(texto) {
  const busca = textoDeBusca(texto);
  if (!catalogoDeCidades || !busca) return null;
  const exata = catalogoDeCidades.find((cidade) => cidade.busca === busca);
  if (exata) return exata.nome;
  const homonimas = homonimasDe(busca);
  return homonimas.length === 1 ? homonimas[0].nome : null;
}

function cidadeDoFormulario() {
  const digitada = campoDeCidade.value.trim();
  if (!catalogoDeCidades) return digitada.length >= 2 ? digitada : null;
  return cidadeDaLista(digitada);
}

function mensagemDaCidade() {
  const busca = textoDeBusca(campoDeCidade.value);
  if (!busca) return mensagensValidacao.cidade;
  if (catalogoDeCidades && homonimasDe(busca).length > 1) {
    return "Existe mais de uma cidade com esse nome. Escolha a do seu estado na lista.";
  }
  return "Escolha sua cidade na lista, como Rio de Janeiro, RJ.";
}

function cidadesParecidas(texto) {
  const busca = textoDeBusca(texto);
  if (!busca) return catalogoDeCidades.slice(0, MAXIMO_DE_CIDADES_SUGERIDAS);
  const noComeco = [];
  const emOutraPalavra = [];
  for (const cidade of catalogoDeCidades) {
    if (cidade.busca.startsWith(busca)) noComeco.push(cidade);
    else if (cidade.busca.includes(` ${busca}`)) emOutraPalavra.push(cidade);
    if (noComeco.length === MAXIMO_DE_CIDADES_SUGERIDAS) break;
  }
  return [...noComeco, ...emOutraPalavra].slice(0, MAXIMO_DE_CIDADES_SUGERIDAS);
}

function opcaoDeCidade(cidade, posicao) {
  const separador = cidade.nome.lastIndexOf(", ");
  const nome = document.createElement("span");
  nome.textContent = cidade.nome.slice(0, separador);
  const uf = document.createElement("span");
  uf.textContent = cidade.nome.slice(separador + 2);
  const opcao = document.createElement("li");
  opcao.id = `cidade-sugerida-${posicao}`;
  opcao.setAttribute("role", "option");
  opcao.setAttribute("aria-selected", "false");
  opcao.dataset.cidade = cidade.nome;
  opcao.append(nome, uf);
  return opcao;
}

function semCidadeEncontrada() {
  const aviso = document.createElement("li");
  aviso.setAttribute("role", "option");
  aviso.setAttribute("aria-disabled", "true");
  aviso.textContent = "Nenhuma cidade encontrada. Confira a grafia.";
  return aviso;
}

function mostrarCidades(texto) {
  if (!catalogoDeCidades) return;
  const parecidas = cidadesParecidas(texto);
  listaDeCidades.replaceChildren(
    ...(parecidas.length > 0 ? parecidas.map(opcaoDeCidade) : [semCidadeEncontrada()]),
  );
  cidadeDestacada = -1;
  campoDeCidade.removeAttribute("aria-activedescendant");
  listaDeCidades.hidden = false;
  campoDeCidade.setAttribute("aria-expanded", "true");
  botaoDeCidades.setAttribute("aria-expanded", "true");
}

async function abrirCidades() {
  await carregarCidades();
  const digitada = campoDeCidade.value.trim();
  mostrarCidades(cidadeDaLista(digitada) === digitada ? "" : digitada);
}

function fecharCidades() {
  listaDeCidades.hidden = true;
  cidadeDestacada = -1;
  campoDeCidade.removeAttribute("aria-activedescendant");
  campoDeCidade.setAttribute("aria-expanded", "false");
  botaoDeCidades.setAttribute("aria-expanded", "false");
}

function destacarCidade(posicao) {
  const opcoes = [...listaDeCidades.querySelectorAll("[data-cidade]")];
  if (opcoes.length === 0) return;
  cidadeDestacada = (posicao + opcoes.length) % opcoes.length;
  opcoes.forEach((opcao, indice) => {
    opcao.setAttribute("aria-selected", String(indice === cidadeDestacada));
  });
  campoDeCidade.setAttribute("aria-activedescendant", opcoes[cidadeDestacada].id);
  opcoes[cidadeDestacada].scrollIntoView?.({ block: "nearest" });
}

function escolherCidade(nome) {
  campoDeCidade.value = nome;
  fecharCidades();
  campoDeCidade.dispatchEvent(new Event("change", { bubbles: true }));
}

function normalizarCurso(curso, catalogo) {
  const sufixo = new RegExp(`(?:\\s*[-–|:]\\s*|\\s+)(?:${catalogo.sufixos.join("|")})$`);
  let texto = normalizarTexto(curso)
    .replace(/\s+/g, " ")
    .replace(/\s*(?:\(.*\)|[-–|/].*)$/, "")
    .replace(sufixo, "");
  const conhecidos = new Set(catalogo.areas.flatMap((area) => area.cursos));
  const prefixo = new RegExp(
    `^(?:${catalogo.prefixos.join("|")})(?: (?:${catalogo.conectores.join("|")}))?\\s+`,
  );
  for (;;) {
    if (catalogo.genericos.includes(texto)) return "";
    if (Object.hasOwn(catalogo.sinonimos, texto)) return catalogo.sinonimos[texto];
    if (conhecidos.has(texto)) return texto;
    const encontrado = texto.match(prefixo);
    if (!encontrado) return texto;
    texto = texto.slice(encontrado[0].length);
  }
}

function areaDoCurso(curso, catalogo) {
  if (!catalogo) return null;
  const normalizado = normalizarCurso(curso, catalogo);
  if (!normalizado) return null;
  const encontrada = catalogo.areas.find((area) => area.cursos.includes(normalizado));
  if (encontrada) return encontrada;
  if (normalizarTexto(curso).startsWith("licenciatura")) {
    return catalogo.areas.find((area) => area.nome === "educacao") ?? null;
  }
  return null;
}

async function montarAreasDoCurso() {
  const requisicao = ++requisicaoDeAreas;
  const identidade = identidadeDoFormulario;
  const cursoSolicitado = form.elements.curso?.value ?? "";
  const catalogo = await carregarAreas();
  if (
    requisicao !== requisicaoDeAreas
    || identidade !== identidadeDoFormulario
    || (form.elements.curso?.value ?? "") !== cursoSolicitado
  ) return;
  const area = areaDoCurso(cursoSolicitado, catalogo);
  gradeDeAreas.replaceChildren();
  campoDeAreas.hidden = !area;
  if (!area) return;
  for (const subarea of area.subareas) {
    const rotulo = document.createElement("label");
    const campo = document.createElement("input");
    campo.type = "checkbox";
    campo.name = "areas";
    campo.value = subarea.valor;
    campo.checked = areasEscolhidas.has(subarea.valor);
    const texto = document.createElement("span");
    texto.textContent = subarea.rotulo;
    rotulo.append(campo, texto);
    gradeDeAreas.append(rotulo);
  }
}

function esquecerPerfilCarregado() {
  areasSalvas = [];
  areasEscolhidas = new Set();
}

function areasDeInteresseDoFormulario(data) {
  const marcadas = data.getAll("areas");
  if (!catalogoDeAreas) return [...areasSalvas];
  const area = areaDoCurso(data.get("curso") ?? "", catalogoDeAreas);
  if (!area) return [];
  const permitidas = new Set(area.subareas.map((subarea) => subarea.valor));
  return marcadas.filter((valor) => permitidas.has(valor));
}

async function montarHabilidadesDoCurso() {
  const requisicao = ++requisicaoDeHabilidades;
  const identidade = identidadeDoFormulario;
  const cursoSolicitado = form.elements.curso?.value ?? "";
  const picker = document.querySelector("#skill-picker");
  const aviso = document.querySelector("#skills-catalog-notice");
  const catalogo = await carregarAreas();
  if (
    requisicao !== requisicaoDeHabilidades
    || identidade !== identidadeDoFormulario
    || (form.elements.curso?.value ?? "") !== cursoSolicitado
  ) return;
  if (!catalogo) {
    picker.replaceChildren();
    aviso.hidden = false;
    renderSkills();
    return;
  }
  aviso.hidden = true;
  const area = areaDoCurso(cursoSolicitado, catalogo);
  const sugeridas = area?.habilidades ?? [];
  picker.replaceChildren(...sugeridas.map((habilidade) => {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.dataset.skill = habilidade;
    botao.setAttribute("aria-pressed", "false");
    botao.textContent = habilidade;
    return botao;
  }));
  renderSkills();
}

function lembrarAreasEscolhidas() {
  gradeDeAreas.querySelectorAll('input[name="areas"]').forEach((campo) => {
    if (campo.checked) areasEscolhidas.add(campo.value);
    else areasEscolhidas.delete(campo.value);
  });
}
let campoComErro = null;
const mensagensValidacao = {
  curso: "Informe o nome do seu curso.",
  periodo: "Selecione o período que você está cursando.",
  cidade: "Informe a cidade onde você procura vaga.",
  modalidade: "Escolha uma modalidade.",
  email: "Digite um e-mail como nome@exemplo.com.",
  aceitou_termos: "Aceite os Termos de Uso e a Política de Privacidade para criar a conta.",
  senha: "Use pelo menos 8 caracteres.",
};

function getClient() {
  if (radarClient) return radarClient;
  const config = window.RADAR_CONFIG;
  if (!window.supabase?.createClient || !config?.supabaseUrl || !config?.supabasePublishableKey) {
    throw new Error(
      "O cadastro ainda não foi configurado. Informe a chave pública do Supabase em web/config.js.",
    );
  }
  radarClient = window.supabase.createClient(config.supabaseUrl, config.supabasePublishableKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  });
  radarClient.auth.onAuthStateChange((event) => {
    if (event === "PASSWORD_RECOVERY") {
      recoverySession = true;
      window.setTimeout(() => showAssistance("new-password"), 0);
    }
  });
  return radarClient;
}

function eventSessionId() {
  const existing = localStorage.getItem(eventSessionKey);
  if (existing && uuidPattern.test(existing)) return existing;
  const created = crypto.randomUUID();
  localStorage.setItem(eventSessionKey, created);
  return created;
}

async function registerEvent(name, properties = {}) {
  try {
    const client = getClient();
    const { data } = await client.auth.getSession();
    const { error } = await client.from("eventos_produto").insert({
      nome: name,
      sessao_id: eventSessionId(),
      user_id: data.session?.user.id ?? null,
      propriedades: properties,
    });
    if (error) throw error;
  } catch (error) {
    console.warn(`Radar: o evento "${name}" não foi registrado.`, error);
    return false;
  }
  return true;
}

function landingJaContadaNestaSessao() {
  try {
    if (sessionStorage.getItem(landingViewKey)) return true;
    sessionStorage.setItem(landingViewKey, "1");
    return false;
  } catch {
    return false;
  }
}

function percentualDoPasso() {
  return Math.round((passosAtivos.indexOf(currentStep) / passosAtivos.length) * 100);
}

function mostrarProgresso(percent) {
  progressPercent.textContent = `${percent}%`;
  progressBar.style.width = `${percent}%`;
  progressTrack.setAttribute("aria-valuenow", String(percent));
}

function showStep(step) {
  currentStep = passosAtivos.includes(step) ? step : passosAtivos[0];
  const posicao = passosAtivos.indexOf(currentStep);
  document.querySelectorAll(".form-step").forEach((element) => {
    element.classList.toggle("is-active", Number(element.dataset.step) === currentStep);
  });
  progressWrap.hidden = passosAtivos.length === 1;
  progressLabel.textContent = `Etapa ${posicao + 1} de ${passosAtivos.length}`;
  mostrarProgresso(percentualDoPasso());
  previousStep.hidden = posicao === 0;
  nextStep.hidden = posicao === passosAtivos.length - 1;
  submitProfile.hidden = posicao !== passosAtivos.length - 1;
  document.querySelector(
    `.form-step[data-step="${currentStep}"] input:not([type="hidden"]), .form-step[data-step="${currentStep}"] select, .form-step[data-step="${currentStep}"] button`,
  )?.focus();
}

function atualizarPassosAtivos() {
  const consentimento = document.querySelector("#signup-consent");
  if (authMode === "login") passosAtivos = [PASSO_CONTA];
  else if (editandoPerfilExistente || (credenciais.hidden && consentimento.hidden)) {
    passosAtivos = [...PASSOS_DO_PERFIL];
  } else passosAtivos = [...PASSOS_DO_PERFIL, PASSO_CONTA];
  showStep(currentStep);
}

function limparErroSeCorrigido(event) {
  if (!campoComErro || campoComErro.id === "custom-skill") return;
  const alvo = event.target;
  if (alvo !== campoComErro && alvo.name !== campoComErro.name) return;
  if (campoComErro.checkValidity()) limparErroDoCampo();
}

function validateStep(step) {
  limparErroDoCampo();
  if (step === PASSO_HABILIDADES && selectedSkills.size === 0 && !continuarSemHabilidades) {
    showStep(step);
    marcarErroNoCampo(document.querySelector("#custom-skill"), "Escolha ou digite pelo menos uma habilidade.");
    return false;
  }
  setFormMessage();
  const fields = [...document.querySelectorAll(
    `.form-step[data-step="${step}"] input:not([type="hidden"]), .form-step[data-step="${step}"] select`,
  )];
  const cidade = step === PASSO_PREFERENCIAS ? cidadeDoFormulario() : null;
  if (cidade) campoDeCidade.value = cidade;
  const invalid = fields.find((field) => {
    if (field.name === "cidade" && !cidade) return true;
    if (field.name === "modalidade" && !modalidadesAceitas.has(form.elements.modalidade.value)) return true;
    return !field.checkValidity();
  });
  if (invalid) {
    showStep(step);
    const mensagem = invalid.name === "cidade" ? mensagemDaCidade() : mensagensValidacao[invalid.name];
    marcarErroNoCampo(invalid, mensagem ?? "Revise os campos antes de continuar.");
    return false;
  }
  if (step === PASSO_CONTA && authMode === "signup" && !editandoPerfilExistente && !form.elements.aceitou_termos.checked) {
    showStep(step);
    marcarErroNoCampo(form.elements.aceitou_termos, mensagensValidacao.aceitou_termos);
    return false;
  }
  return true;
}

function renderSkills() {
  if (selectedSkills.size > 0 && campoComErro?.id === "custom-skill") limparErroDoCampo();
  form.elements.habilidades.value = [...selectedSkills].join(",");
  document.querySelectorAll("[data-skill]").forEach((button) => {
    const active = selectedSkills.has(button.dataset.skill);
    button.classList.toggle("is-selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
  const container = document.querySelector("#selected-skills");
  container.replaceChildren(...[...selectedSkills].map((skill) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.textContent = `${skill} ×`;
    chip.setAttribute("aria-label", `Remover ${skill}`);
    chip.addEventListener("click", () => {
      selectedSkills.delete(skill);
      if (selectedSkills.size === 0) continuarSemHabilidades = false;
      renderSkills();
    });
    return chip;
  }));
  continuarSemHabilidadesButton.hidden = selectedSkills.size > 0;
}

function addCustomSkill() {
  const input = document.querySelector("#custom-skill");
  const skill = input.value.trim().slice(0, TAMANHO_MAXIMO_DA_HABILIDADE);
  if (!skill) return;
  if (selectedSkills.size >= MAXIMO_DE_HABILIDADES && !selectedSkills.has(skill)) {
    marcarErroNoCampo(input, `Escolha no máximo ${MAXIMO_DE_HABILIDADES} habilidades.`);
    return;
  }
  selectedSkills.add(skill);
  continuarSemHabilidades = false;
  input.value = "";
  renderSkills();
  setFormMessage();
}

function validationError(message) {
  const error = new Error(message);
  error.name = "RadarValidationError";
  return error;
}

function humanizeError(error, { profilePending = false } = {}) {
  const message = String(error?.message ?? "").toLowerCase();
  const code = String(error?.code ?? "").toLowerCase();
  const status = Number(error?.status);

  if (message.startsWith("o cadastro ainda não foi configurado")) {
    return error.message;
  }
  if (error?.name === "RadarValidationError") return error.message;
  if (profilePending) {
    return "Sua conta foi criada, mas o perfil ainda não foi salvo. Entre novamente para concluir o perfil.";
  }
  if (code === "user_already_exists" || code === "email_exists" || message.includes("user already registered")) {
    return "Já existe uma conta com esse e-mail. Escolha “Entrar” ou use outro e-mail.";
  }
  if (code === "invalid_credentials" || message.includes("invalid login credentials")) {
    return "E-mail ou senha incorretos. Confira os dados ou crie uma conta.";
  }
  if (code === "email_not_confirmed" || message.includes("email not confirmed")) {
    return "Confirme seu e-mail pelo link recebido antes de entrar.";
  }
  if (code === "weak_password" || message.includes("password should be at least")) {
    return "A senha precisa ter pelo menos 8 caracteres.";
  }
  if (code === "over_email_send_rate_limit" || status === 429) {
    return "Muitas tentativas em pouco tempo. Aguarde alguns minutos e tente novamente.";
  }
  if (code === "23505" || message.includes("duplicate key")) {
    return "Este perfil já existe. Recarregue a página e tente novamente.";
  }
  if (code === "42501" || message.includes("row-level security") || message.includes("permission denied")) {
    return "Não foi possível salvar o perfil nesta conta. Entre novamente e tente outra vez.";
  }
  if (message.includes("failed to fetch") || message.includes("network") || message.includes("fetch")) {
    return "Não foi possível conectar ao cadastro. Verifique a conexão e tente novamente.";
  }
  return "Não foi possível concluir o cadastro agora. Verifique os dados e tente novamente.";
}

function limparErroDoCampo() {
  if (!campoComErro) return;
  campoComErro.removeAttribute("aria-invalid");
  campoComErro.removeAttribute("aria-describedby");
  document.querySelector("#erro-do-campo")?.remove();
  campoComErro = null;
}

function marcarErroNoCampo(campo, mensagem) {
  limparErroDoCampo();
  const aviso = document.createElement("span");
  aviso.className = "field-error";
  aviso.id = "erro-do-campo";
  aviso.textContent = mensagem;
  const rotuloDeConsentimento = campo.closest(".consent-fields") ? campo.closest("label") : null;
  if (rotuloDeConsentimento) rotuloDeConsentimento.insertAdjacentElement("afterend", aviso);
  else (campo.closest(".field") ?? campo.parentElement).append(aviso);
  campo.setAttribute("aria-invalid", "true");
  campo.setAttribute("aria-describedby", aviso.id);
  campoComErro = campo;
  campo.focus();
}

function setFormMessage(message = "", tom = "erro") {
  const naAssistencia = !document.querySelector("#auth-assistance").hidden;
  const erro = naAssistencia ? assistanceMessage : formMessage;
  const aviso = naAssistencia ? assistanceNotice : formNotice;
  [formMessage, formNotice, assistanceMessage, assistanceNotice].forEach((regiao) => {
    regiao.textContent = "";
  });
  (tom === "aviso" ? aviso : erro).textContent = message;
}

function marcarOcupado(botao, ocupado) {
  botao.disabled = ocupado;
  botao.setAttribute("aria-busy", String(ocupado));
}

function setSubmitting(submitting) {
  marcarOcupado(submitProfile, submitting);
  if (editandoPerfilExistente) {
    submitLabel.textContent = "Salvar alterações";
    return;
  }
  submitLabel.textContent = authMode === "signup"
    ? "Criar conta e continuar"
    : "Entrar e continuar";
}

const COPY_DA_CONTA = {
  signup: {
    titulo: "Comece pela sua conta",
    ajuda: "O e-mail dá acesso à conta e confirma o cadastro. A senha protege seus dados.",
    senha: "Pelo menos 8 caracteres",
  },
  login: {
    titulo: "Entre na sua conta",
    ajuda: "Use o e-mail e a senha que você cadastrou. Seu perfil continua salvo.",
    senha: "Sua senha",
  },
};

function setAuthMode(mode) {
  authMode = mode;
  const copy = COPY_DA_CONTA[mode];
  document.querySelector("#conta-titulo").textContent = copy.titulo;
  document.querySelector("#conta-ajuda").textContent = copy.ajuda;
  form.elements.senha.placeholder = copy.senha;
  document.querySelector("#signup-consent").hidden = mode !== "signup";
  form.elements.aceitou_termos.required = mode === "signup";
  const password = form.elements.senha;
  password.autocomplete = mode === "signup" ? "new-password" : "current-password";
  toggleAuthMode.textContent = mode === "signup" ? "Entrar" : "Criar conta";
  toggleAuthMode.parentElement.firstChild.textContent = mode === "signup"
    ? "Já possui uma conta? "
    : "Ainda não possui uma conta? ";
  setSubmitting(false);
  setFormMessage();
  atualizarPassosAtivos();
}

function sairDoModoEdicao() {
  editandoPerfilExistente = false;
  credenciais.hidden = false;
  document.querySelector(".auth-help").hidden = false;
  atualizarPassosAtivos();
  accountSwitch.hidden = false;
  form.elements.email.required = true;
  form.elements.senha.required = true;
  document.querySelector("#signup-consent").hidden = authMode !== "signup";
  form.elements.aceitou_termos.required = authMode === "signup";
}

function entrarNoModoEdicao() {
  setAuthMode("signup");
  editandoPerfilExistente = true;
  credenciais.hidden = true;
  document.querySelector(".auth-help").hidden = true;
  accountSwitch.hidden = true;
  form.elements.email.required = false;
  form.elements.senha.required = false;
  document.querySelector("#signup-consent").hidden = true;
  form.elements.aceitou_termos.required = false;
  submitLabel.textContent = "Salvar alterações";
  atualizarPassosAtivos();
}

function resetDialogView() {
  identidadeDoFormulario += 1;
  assistanceMode = null;
  document.querySelector("#auth-assistance").hidden = true;
  document.querySelector("#captcha-container").hidden = false;
  sairDoModoEdicao();
  form.hidden = false;
  rotularDialogo("signup-title");
  successState.hidden = true;
  esconderConta();
  pauseReason.hidden = true;
  pauseReasonMessage.textContent = "";
  setAccountMessage();
  progressWrap.hidden = false;
  telegramLink.hidden = true;
  setFormMessage();
  limparErroDoCampo();
  setSubmitting(false);
  continuarSemHabilidades = false;
  showStep(PASSO_CONTA);
}

function limparRascunhoDoCadastro() {
  form.reset();
  selectedSkills.clear();
  continuarSemHabilidades = false;
  esquecerPerfilCarregado();
  gradeDeAreas.replaceChildren();
  campoDeAreas.hidden = true;
  document.querySelector("#skills-catalog-notice").hidden = true;
  renderSkills();
}

function openAccountPage() {
  mostrarChamadaDeConta(true);
  if (!accountPage.hidden) return;
  if (dialog.open && typeof dialog.close === "function") dialog.close();
  else dialog.removeAttribute("open");
  accountContent.append(dialogShell);
  landingPage.hidden = true;
  accountPage.hidden = false;
  document.body.classList.add("account-page-open");
  document.body.style.overflow = "";
  document.title = "Minha conta — Radar de Estágio";
  const url = new URL(window.location.href);
  if (!url.searchParams.has("conta")) {
    url.searchParams.set("conta", "");
    window.history.pushState(null, "", url);
  }
  window.scrollTo(0, 0);
}

function leaveAccountPage() {
  if (accountPage.hidden) return;
  dialog.append(dialogShell);
  accountPage.hidden = true;
  landingPage.hidden = false;
  document.body.classList.remove("account-page-open");
  document.title = landingTitle;
  const url = new URL(window.location.href);
  url.searchParams.delete("conta");
  url.hash = "";
  window.history.replaceState(null, "", url);
  document.querySelector(".js-open-signup").focus();
}

function mostrarChamadaDeConta(autenticado) {
  usuarioAutenticado = autenticado;
  chamadasDeCadastro.forEach((botao) => {
    botao.firstChild.textContent = autenticado
      ? `${botao.dataset.rotuloConta} `
      : rotulosDeCadastro.get(botao);
  });
  chamadasDeLogin.forEach((botao) => {
    botao.hidden = autenticado;
  });
}

function rotularDialogo(idDoTitulo) {
  dialog.setAttribute("aria-labelledby", idDoTitulo);
}

function openDialog() {
  if (dialog.open || !accountPage.hidden) return;
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
  document.body.style.overflow = "hidden";
}

function closeSignup() {
  leaveAccountPage();
  if (dialog.open && typeof dialog.close === "function") dialog.close();
  else dialog.removeAttribute("open");
  document.body.style.overflow = "";
}

function profileFromForm() {
  addCustomSkill();
  const data = new FormData(form);
  const profile = {
    curso: data.get("curso").trim(),
    periodo: Number(data.get("periodo")),
    habilidades: data
      .get("habilidades")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    cidade: cidadeDoFormulario() ?? "",
    modalidade: data.get("modalidade"),
    areas_de_interesse: areasDeInteresseDoFormulario(data),
  };
  if (!profile.curso) throw validationError(mensagensValidacao.curso);
  if (!Number.isInteger(profile.periodo) || profile.periodo < 1) {
    throw validationError(mensagensValidacao.periodo);
  }
  if (profile.habilidades.length === 0 && !continuarSemHabilidades) {
    throw validationError("Escolha ou digite pelo menos uma habilidade.");
  }
  if (profile.habilidades.length > MAXIMO_DE_HABILIDADES) {
    throw validationError(`Escolha no máximo ${MAXIMO_DE_HABILIDADES} habilidades.`);
  }
  if (!profile.cidade) throw validationError(mensagemDaCidade());
  if (!modalidadesAceitas.has(profile.modalidade)) {
    throw validationError(mensagensValidacao.modalidade);
  }
  return profile;
}

function readPendingProfile() {
  try {
    return JSON.parse(localStorage.getItem(pendingProfileKey));
  } catch {
    return null;
  }
}

function clearPendingProfile() {
  localStorage.removeItem(pendingProfileKey);
}

function showSuccess({ kicker, title, copy, token, linked = false }) {
  esconderConta();
  document.querySelector("#auth-assistance").hidden = true;
  document.querySelector("#captcha-container").hidden = true;
  form.hidden = true;
  progressWrap.hidden = true;
  successState.hidden = false;
  setFormMessage();
  rotularDialogo("success-title");
  document.querySelector("#success-kicker").textContent = kicker;
  document.querySelector("#success-title").textContent = title;
  document.querySelector("#success-copy").textContent = copy;
  telegramLink.hidden = !token || linked;
  if (token && !linked) {
    const bot = window.RADAR_CONFIG.telegramBot;
    telegramLink.href = `https://t.me/${bot}?start=${token}`;
  }
  document.querySelector("#success-title").focus();
}

function showConfirmation(email) {
  showAssistance("resend", email);
  setFormMessage("Se o cadastro foi aceito, você receberá um link. Confirme em qualquer aparelho para continuar.", "aviso");
  startResendCooldown();
}

function mostrarEstadoDoPerfil(profile) {
  if (profile.telegram_chat_id || profile.excluida_em) {
    showAccount(profile);
    return;
  }
  showActivation(profile);
}

function showActivation(profile) {
  openAccountPage();
  showSuccess({
    kicker: "Perfil salvo",
    title: "Agora, ative as entregas.",
    copy: "Vincule seu Telegram para receber as vagas selecionadas pelo Radar.",
    token: profile.token_vinculo,
  });
}

function setAccountMessage(message = "", tom = "erro") {
  const regiao = tom === "aviso" ? accountNotice : accountMessage;
  const outra = tom === "aviso" ? accountMessage : accountNotice;
  outra.textContent = "";
  regiao.textContent = message;
}

function resumoDoPerfil(profile) {
  const modalidades = {
    remoto: "remoto",
    presencial: "presencial",
    hibrido: "híbrido",
    indiferente: "qualquer modalidade",
  };
  return `${profile.curso} · ${profile.periodo}º período\n${profile.cidade} · ${modalidades[profile.modalidade]}`;
}

function mostrarHabilidadesDaConta(habilidades) {
  const lista = document.querySelector("#account-skills");
  lista.replaceChildren();
  if (!habilidades.length) {
    const vazia = document.createElement("span");
    vazia.className = "account-skills-empty";
    vazia.textContent = "Habilidades ainda não informadas";
    lista.append(vazia);
    return;
  }
  habilidades.forEach((habilidade) => {
    const item = document.createElement("span");
    item.textContent = habilidade;
    lista.append(item);
  });
}

function visualDasEntregas(profile) {
  if (profile.excluida_em) return { estado: "deletion", titulo: "Exclusão agendada", simbolo: "!" };
  if (!profile.telegram_chat_id) return { estado: "unlinked", titulo: "Telegram pendente", simbolo: "↗" };
  if (!profile.ativo) return { estado: "paused", titulo: "Entregas pausadas", simbolo: "Ⅱ" };
  return { estado: "active", titulo: "Entregas ativas", simbolo: "✓" };
}

function estadoDasEntregas(profile) {
  if (profile.excluida_em) {
    return `Exclusão pedida. Seus dados são apagados em ${dataDoApagamento(profile.excluida_em)}.`;
  }
  if (!profile.telegram_chat_id) return "Telegram ainda não vinculado.";
  if (!profile.ativo) return "Entregas pausadas. Nada chega até você retomar.";
  return "Telegram vinculado. As recomendações chegarão por lá quando houver vagas compatíveis. A primeira busca pode aguardar a próxima execução diária.";
}

function showAccount(profile) {
  openAccountPage();
  document.querySelector("#auth-assistance").hidden = true;
  document.querySelector("#captcha-container").hidden = true;
  document.querySelector("#account-emails").checked = Boolean(profile.aceita_emails);
  document.querySelector("#account-emails").disabled = Boolean(profile.excluida_em);
  document.querySelector("#edit-profile").hidden = Boolean(profile.excluida_em);
  form.hidden = true;
  progressWrap.hidden = true;
  successState.hidden = true;
  fecharConfirmacao(false);
  pauseReason.hidden = true;
  pauseReasonMessage.textContent = "";
  accountState.hidden = false;
  setAccountMessage();
  document.querySelector("#account-summary").textContent = resumoDoPerfil(profile);
  mostrarHabilidadesDaConta(profile.habilidades);
  document.querySelector("#account-schedule").textContent = estadoDasEntregas(profile);
  const visual = visualDasEntregas(profile);
  document.querySelector("#account-delivery-card").dataset.status = visual.estado;
  document.querySelector("#account-delivery-title").textContent = visual.titulo;
  document.querySelector("#account-status-icon").textContent = visual.simbolo;
  const emExclusao = Boolean(profile.excluida_em);
  toggleDeliveries.textContent = profile.ativo ? "Pausar entregas" : "Retomar entregas";
  toggleDeliveries.dataset.acao = profile.ativo ? "pausar" : "retomar";
  toggleDeliveries.hidden = !profile.telegram_chat_id || emExclusao;
  document.querySelector("#unlink-telegram").hidden = !profile.telegram_chat_id || emExclusao;
  document.querySelector("#delete-account").hidden = emExclusao;
  document.querySelector("#cancel-deletion").hidden = !emExclusao;
  const entradaAtual = accountNavEntries.find(({ link }) => link.hash === window.location.hash);
  mostrarSecaoDaConta(entradaAtual?.link ?? accountNavEntries[0].link, false);
  document.querySelector("#account-title").focus();
}

function preencherFormularioCom(profile) {
  form.elements.curso.value = profile.curso;
  form.elements.periodo.value = String(profile.periodo);
  form.elements.cidade.value = profile.cidade;
  form.elements.modalidade.value = profile.modalidade;
  selectedSkills.clear();
  profile.habilidades.forEach((skill) => selectedSkills.add(skill));
  continuarSemHabilidades = profile.habilidades.length === 0;
  renderSkills();
  void montarHabilidadesDoCurso();
  areasSalvas = [...(profile.areas_de_interesse ?? [])];
  areasEscolhidas = new Set(areasSalvas);
  void montarAreasDoCurso();
}

async function perfilAtual() {
  const session = await currentSession();
  if (!session) throw validationError(MENSAGEM_SEM_SESSAO);
  const profile = await loadProfile(session.user.id);
  if (!profile) throw validationError(MENSAGEM_SEM_PERFIL);
  return profile;
}

async function alternarEntregas(pausar) {
  const session = await currentSession();
  if (!session) throw validationError(MENSAGEM_SEM_SESSAO);
  const updates = pausar
    ? { ativo: false, atualizado_em: new Date().toISOString() }
    : { ativo: true, motivo_pausa: null, atualizado_em: new Date().toISOString() };
  const { data, error } = await getClient()
    .from("perfis")
    .update(updates)
    .eq("user_id", session.user.id)
    .eq("ativo", pausar)
    .select(COLUNAS_DO_PERFIL)
    .maybeSingle();
  if (error) throw error;
  return data;
}

function mostrarPerguntaMotivoPausa() {
  pauseReason.hidden = false;
  pauseReasonMessage.textContent = "";
  pauseReason.querySelectorAll('input[name="motivo-pausa"]').forEach((input) => {
    input.checked = false;
  });
  document.querySelector("#pause-reason-title").focus();
}

function esconderPerguntaMotivoPausa() {
  pauseReason.hidden = true;
  pauseReasonMessage.textContent = "";
}

async function salvarMotivoPausa(motivo) {
  if (!MOTIVOS_PAUSA.has(motivo)) {
    throw validationError("Escolha um dos motivos ou pule esta pergunta.");
  }
  const session = await currentSession();
  if (!session) throw validationError(MENSAGEM_SEM_SESSAO);
  const { data, error } = await getClient()
    .from("perfis")
    .update({ motivo_pausa: motivo, atualizado_em: new Date().toISOString() })
    .eq("user_id", session.user.id)
    .eq("ativo", false)
    .select("user_id,ativo,motivo_pausa")
    .maybeSingle();
  if (error) throw error;
  if (!data || data.ativo !== false) {
    throw validationError("A conta não está mais pausada. Atualize o estado da conta e tente novamente.");
  }
  return data;
}

function dataDoApagamento(marcadaEm) {
  const marcada = marcadaEm ? new Date(marcadaEm) : new Date();
  marcada.setDate(marcada.getDate() + DIAS_ATE_APAGAR);
  return marcada.toLocaleDateString("pt-BR");
}

function fecharConfirmacao(restaurarFoco = true) {
  const acao = accountConfirm.dataset.acao;
  if (accountConfirm.open && typeof accountConfirm.close === "function") accountConfirm.close();
  accountConfirm.hidden = true;
  delete accountConfirm.dataset.acao;
  if (!restaurarFoco || !acao) return;
  const origem = acao === "desvincular" ? "#unlink-telegram" : "#delete-account";
  document.querySelector(origem).focus();
}

function esconderConta() {
  fecharConfirmacao(false);
  accountState.hidden = true;
}

function pedirConfirmacao(acao) {
  const configuracoes = {
    desvincular: {
      titulo: "Desvincular o Telegram?",
      aviso: "As entregas serão interrompidas",
      detalhe: "O vínculo atual deixará de funcionar. Você poderá conectar o Telegram novamente depois.",
      copy: "Nenhuma vaga será enviada até uma nova vinculação.",
      confirmar: "Desvincular Telegram",
    },
    excluir: {
      titulo: "Excluir sua conta?",
      aviso: "Sua conta será marcada para exclusão",
      detalhe: "As entregas param na hora. Seus dados serão apagados definitivamente depois de 60 dias.",
      copy: "Até o prazo terminar, você pode entrar novamente e cancelar a exclusão.",
      confirmar: "Excluir conta",
    },
  };
  const configuracao = configuracoes[acao];
  accountConfirm.dataset.acao = acao;
  document.querySelector("#account-confirm-title").textContent = configuracao.titulo;
  document.querySelector("#account-confirm-warning-title").textContent = configuracao.aviso;
  document.querySelector("#account-confirm-warning-copy").textContent = configuracao.detalhe;
  document.querySelector("#account-confirm-copy").textContent = configuracao.copy;
  document.querySelector("#account-confirm-yes").textContent = configuracao.confirmar;
  accountConfirm.hidden = false;
  if (typeof accountConfirm.showModal === "function" && !accountConfirm.open) accountConfirm.showModal();
  document.querySelector("#account-confirm-no").focus();
}

async function currentSession() {
  const { data, error } = await getClient().auth.getSession();
  if (error) throw error;
  return data.session;
}

async function loadProfile(userId) {
  const { data, error } = await getClient()
    .from("perfis")
    .select(COLUNAS_DO_PERFIL)
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw error;
  return data;
}

function cadastroFromProfile(profile) {
  return {
    perfil: profile,
    aceitou_termos: form.elements.aceitou_termos.checked,
    aceita_emails: form.elements.aceita_emails.checked,
    versao_dos_termos: VERSAO_DOS_TERMOS,
    sessao_id: eventSessionId(),
  };
}

async function persistProfile(userId, profile) {
  const existing = await loadProfile(userId);
  if (existing) {
    const { error } = await getClient().from("perfis")
      .update({ ...profile, atualizado_em: new Date().toISOString() }).eq("user_id", userId).select("user_id").single();
    if (error) throw error;
  } else {
    const { error } = await getClient().rpc("concluir_meu_cadastro", { cadastro: cadastroFromProfile(profile) });
    if (error) throw error;
  }
  clearPendingProfile();
  void registerEvent("perfil_salvo");
  return loadProfile(userId);
}

async function authenticate(email, password, profile) {
  const token = requireCaptcha();
  try {
    if (authMode === "login") {
      const { data, error } = await getClient().auth.signInWithPassword({ email, password, options: { captchaToken: token } });
      if (error) throw error;
      return data.session;
    }
    const { data, error } = await getClient().auth.signUp({
      email,
      password,
      options: { emailRedirectTo: authRedirect(), captchaToken: token, data: { cadastro_radar: cadastroFromProfile(profile) } },
    });
    if (error) throw error;
    return data.session;
  } finally {
    resetCaptcha();
  }
}

function aguardandoVinculoDoTelegram() {
  return (dialog.open || !accountPage.hidden) && !successState.hidden && !telegramLink.hidden;
}

async function refreshActivationStatus() {
  if (!aguardandoVinculoDoTelegram()) return;
  try {
    const session = await currentSession();
    if (!session) return;
    const profile = await loadProfile(session.user.id);
    if (profile && aguardandoVinculoDoTelegram()) mostrarEstadoDoPerfil(profile);
  } catch {
    document.querySelector("#success-copy").textContent =
      "O Telegram foi aberto, mas ainda não conseguimos confirmar o vínculo. Tente voltar a esta janela novamente.";
  }
}

function abrirLogin() {
  resetDialogView();
  setAuthMode("login");
  showStep(PASSO_CONTA);
  openDialog();
}

async function openSignup() {
  resetDialogView();
  if (!usuarioAutenticado && authMode === "signup") showStep(PASSO_MOMENTO);
  if (!usuarioAutenticado) openDialog();
  try {
    const session = await currentSession();
    mostrarChamadaDeConta(Boolean(session));
    if (!session) {
      limparRascunhoDoCadastro();
      setAuthMode("signup");
      showStep(PASSO_MOMENTO);
      openDialog();
      return;
    }
    form.elements.email.value = session.user.email ?? "";
    const profile = await loadProfile(session.user.id);
    if (profile) mostrarEstadoDoPerfil(profile);
    else prepareMissingProfile(session);
  } catch (error) {
    openDialog();
    setFormMessage(humanizeError(error));
  }
}

async function resumeConfirmedSignup() {
  try {
    const session = await currentSession();
    mostrarChamadaDeConta(Boolean(session));
    if (authLinkError) {
      showAssistance(returningFromRecovery ? "reset" : "resend");
      setFormMessage("Esse link expirou ou já foi usado. Solicite um novo abaixo.");
      return;
    }
    if (returningFromRecovery || recoverySession) {
      if (session && recoverySession) showAssistance("new-password");
      else if (!session) showAssistance("reset");
      return;
    }
    if (!session) {
      if (authQuery.has("conta")) abrirLogin();
      return;
    }
    const profile = await loadProfile(session.user.id);
    if (!returningFromAuth && !readPendingProfile() && !authQuery.has("conta")) return;
    clearPendingProfile();
    if (profile) mostrarEstadoDoPerfil(profile);
    else prepareMissingProfile(session);
  } catch (error) {
    resetDialogView();
    openDialog();
    setFormMessage(humanizeError(error, { profilePending: true }));
  }
}

function prepareMissingProfile(session) {
  resetDialogView();
  openAccountPage();
  setAuthMode("signup");
  form.elements.email.value = session.user.email ?? "";
  credenciais.hidden = true;
  document.querySelector(".auth-help").hidden = true;
  form.elements.email.required = false;
  form.elements.senha.required = false;
  accountSwitch.hidden = true;
  atualizarPassosAtivos();
  setFormMessage("Seu e-mail está confirmado. Complete seu perfil para continuar.", "aviso");
}

function validarFluxo() {
  return passosAtivos.every((passo) => validateStep(passo));
}

function avancarPasso() {
  if (currentStep === PASSO_HABILIDADES) addCustomSkill();
  if (currentStep === PASSO_PREFERENCIAS) lembrarAreasEscolhidas();
  if (!validateStep(currentStep)) return;
  if (currentStep === PASSO_MOMENTO) void montarHabilidadesDoCurso();
  if (currentStep === PASSO_HABILIDADES) void montarAreasDoCurso();
  if (currentStep === PASSO_MOMENTO) void registerEvent("etapa_perfil_concluida");
  if (currentStep === PASSO_HABILIDADES) {
    void registerEvent("etapa_habilidades_concluida", { quantidade: selectedSkills.size });
  }
  if (currentStep === PASSO_PREFERENCIAS) void registerEvent("etapa_preferencias_concluida");
  showStep(passosAtivos[passosAtivos.indexOf(currentStep) + 1]);
}

function voltarPasso() {
  if (currentStep === PASSO_PREFERENCIAS) lembrarAreasEscolhidas();
  showStep(passosAtivos[passosAtivos.indexOf(currentStep) - 1]);
}

chamadasDeLogin.forEach((button) => {
  button.addEventListener("click", () => {
    if (usuarioAutenticado) {
      openSignup();
      return;
    }
    limparRascunhoDoCadastro();
    abrirLogin();
  });
});

chamadasDeCadastro.forEach((button) => {
  button.addEventListener("click", () => {
    if (!usuarioAutenticado) {
      void registerEvent("cta_cadastro_aberto", {
        origem: button.dataset.eventOrigin ?? "desconhecida",
      });
    }
    openSignup();
  });
});
document.querySelector("#close-dialog").addEventListener("click", closeSignup);
document.querySelector("#close-account").addEventListener("click", closeSignup);
document.querySelector("#back-to-site").addEventListener("click", closeSignup);
document.querySelectorAll("#account-home, #footer-home").forEach((link) => {
  link.addEventListener("click", (event) => {
    if (accountPage.hidden) return;
    event.preventDefault();
    closeSignup();
  });
});
window.addEventListener("popstate", () => {
  if (new URLSearchParams(window.location.search).has("conta")) openSignup();
  else closeSignup();
});

document.querySelector("#edit-profile").addEventListener("click", async () => {
  try {
    const profile = await perfilAtual();
    preencherFormularioCom(profile);
    esconderConta();
    form.hidden = false;
    progressWrap.hidden = false;
    entrarNoModoEdicao();
    setSubmitting(false);
    showStep(PASSO_MOMENTO);
  } catch (error) {
    setAccountMessage(humanizeError(error));
  }
});

toggleDeliveries.addEventListener("click", async () => {
  if (toggleDeliveries.disabled) return;
  toggleDeliveries.disabled = true;
  setAccountMessage();
  const pausar = toggleDeliveries.dataset.acao === "pausar";
  try {
    const atualizado = await alternarEntregas(pausar);
    if (atualizado) {
      showAccount(atualizado);
      if (pausar) mostrarPerguntaMotivoPausa();
      return;
    }
    showAccount(await perfilAtual());
    setAccountMessage(MENSAGEM_ENTREGAS_JA_MUDARAM, "aviso");
  } catch (error) {
    setAccountMessage(humanizeError(error));
  } finally {
    toggleDeliveries.disabled = false;
  }
});

savePauseReason.addEventListener("click", async () => {
  if (savePauseReason.disabled) return;
  const selected = pauseReason.querySelector('input[name="motivo-pausa"]:checked');
  if (!selected) {
    pauseReasonMessage.textContent = "Escolha um motivo ou clique em “Pular”.";
    pauseReason.querySelector('input[name="motivo-pausa"]').focus();
    return;
  }
  marcarOcupado(savePauseReason, true);
  skipPauseReason.disabled = true;
  try {
    await salvarMotivoPausa(selected.value);
    const profile = await perfilAtual();
    showAccount(profile);
    setAccountMessage("Motivo salvo.", "aviso");
  } catch (error) {
    pauseReasonMessage.textContent = humanizeError(error);
  } finally {
    marcarOcupado(savePauseReason, false);
    skipPauseReason.disabled = false;
  }
});

skipPauseReason.addEventListener("click", () => {
  if (skipPauseReason.disabled) return;
  esconderPerguntaMotivoPausa();
  document.querySelector("#account-title").focus();
});

document.querySelector("#unlink-telegram").addEventListener("click", () => {
  pedirConfirmacao("desvincular");
});

document.querySelector("#delete-account").addEventListener("click", () => {
  pedirConfirmacao("excluir");
});

document.querySelector("#cancel-deletion").addEventListener("click", async () => {
  setAccountMessage();
  try {
    const { error } = await getClient().rpc("cancelar_exclusao_da_minha_conta");
    if (error) throw error;
    const profile = await perfilAtual();
    mostrarEstadoDoPerfil(profile);
  } catch (error) {
    setAccountMessage(humanizeError(error));
  }
});

document.querySelector("#account-confirm-no").addEventListener("click", () => {
  fecharConfirmacao();
});

document.querySelector("#account-confirm-close").addEventListener("click", () => fecharConfirmacao());

accountConfirm.addEventListener("cancel", (event) => {
  event.preventDefault();
  fecharConfirmacao();
});

document.querySelector("#account-confirm-yes").addEventListener("click", async () => {
  const acao = accountConfirm.dataset.acao;
  fecharConfirmacao();
  setAccountMessage();
  try {
    if (acao === "desvincular") {
      const { error } = await getClient().rpc("desvincular_meu_telegram");
      if (error) throw error;
      const profile = await perfilAtual();
      if (!profile) {
        showConfirmation(form.elements.email.value);
        return;
      }
      mostrarEstadoDoPerfil(profile);
      return;
    }
    const { data, error } = await getClient().rpc("excluir_minha_conta");
    if (error) throw error;
    showSuccess({
      kicker: "Exclusão agendada",
      title: "As entregas pararam agora.",
      copy: `Seus dados são apagados definitivamente em ${dataDoApagamento(data)}. Até lá, entre aqui de novo para cancelar.`,
    });
  } catch (error) {
    setAccountMessage(humanizeError(error));
  }
});
document.querySelector("#finish-signup").addEventListener("click", closeSignup);
previousStep.addEventListener("click", voltarPasso);
nextStep.addEventListener("click", avancarPasso);
document.querySelector("#skill-picker").addEventListener("click", (event) => {
  const button = event.target.closest("[data-skill]");
  if (!button) return;
  const skill = button.dataset.skill;
  if (selectedSkills.has(skill)) {
    selectedSkills.delete(skill);
    if (selectedSkills.size === 0) continuarSemHabilidades = false;
  } else {
    selectedSkills.add(skill);
    continuarSemHabilidades = false;
  }
  renderSkills();
  setFormMessage();
});
continuarSemHabilidadesButton.addEventListener("click", () => {
  if (selectedSkills.size > 0) return;
  continuarSemHabilidades = true;
  avancarPasso();
});
document.querySelector("#custom-skill").addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  addCustomSkill();
});
toggleAuthMode.addEventListener("click", () => {
  setAuthMode(authMode === "signup" ? "login" : "signup");
});

form.addEventListener("input", limparErroSeCorrigido);
form.addEventListener("change", limparErroSeCorrigido);

campoDeCidade.addEventListener("focus", () => {
  void carregarCidades();
});

campoDeCidade.addEventListener("input", async () => {
  await carregarCidades();
  if (document.activeElement === campoDeCidade) mostrarCidades(campoDeCidade.value);
});

campoDeCidade.addEventListener("keydown", (event) => {
  const aberta = !listaDeCidades.hidden;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    if (!aberta) void abrirCidades();
    else destacarCidade(event.key === "ArrowDown" ? cidadeDestacada + 1 : Math.max(cidadeDestacada, 0) - 1);
  } else if (event.key === "Enter" && aberta && cidadeDestacada >= 0) {
    event.preventDefault();
    escolherCidade(listaDeCidades.querySelectorAll("[data-cidade]")[cidadeDestacada].dataset.cidade);
  } else if (event.key === "Escape" && aberta) {
    event.preventDefault();
    fecharCidades();
  }
});

campoDeCidade.addEventListener("blur", () => {
  fecharCidades();
  const cidade = cidadeDaLista(campoDeCidade.value);
  if (cidade) campoDeCidade.value = cidade;
});

botaoDeCidades.addEventListener("mousedown", (event) => event.preventDefault());
botaoDeCidades.addEventListener("click", () => {
  if (!listaDeCidades.hidden) {
    fecharCidades();
    return;
  }
  campoDeCidade.focus();
  void abrirCidades();
});

listaDeCidades.addEventListener("mousedown", (event) => event.preventDefault());
listaDeCidades.addEventListener("click", (event) => {
  const opcao = event.target.closest("[data-cidade]");
  if (opcao) escolherCidade(opcao.dataset.cidade);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submitProfile.disabled) return;
  if (passosAtivos.includes(PASSO_PREFERENCIAS) && !catalogoDeCidades) {
    setSubmitting(true);
    await carregarCidades();
    setSubmitting(false);
  }
  if (!validarFluxo()) return;
  if (currentStep === PASSO_PREFERENCIAS && authMode !== "login") {
    void registerEvent("etapa_preferencias_concluida");
  }
  const email = form.elements.email.value.trim();
  const password = form.elements.senha.value;
  let profileSaveStarted = false;
  setFormMessage();
  setSubmitting(true);
  mostrarProgresso(PROGRESSO_AO_CONFIRMAR);
  try {
    const profile = authMode === "login" ? null : profileFromForm();
    const existingSession = await currentSession();
    if (editandoPerfilExistente && !existingSession) {
      sairDoModoEdicao();
      setFormMessage(MENSAGEM_SEM_SESSAO);
      return;
    }
    if (!editandoPerfilExistente && existingSession && existingSession.user.email !== email) {
      const { error } = await getClient().auth.signOut();
      if (error) throw error;
      esquecerPerfilCarregado();
    }
    const session = editandoPerfilExistente || existingSession?.user.email === email
      ? existingSession
      : await authenticate(email, password, profile);
    form.elements.senha.value = "";
    if (!session) {
      showConfirmation(email);
      return;
    }
    const existing = await loadProfile(session.user.id);
    if (existing && !editandoPerfilExistente) {
      mostrarEstadoDoPerfil(existing);
      return;
    }
    if (authMode === "login") {
      prepareMissingProfile(session);
      return;
    }
    profileSaveStarted = true;
    const savedProfile = await persistProfile(session.user.id, profile);
    mostrarEstadoDoPerfil(savedProfile);
  } catch (error) {
    if (error?.code === "email_not_confirmed") showAssistance("resend", email);
    setFormMessage(humanizeError(error, { profilePending: profileSaveStarted }));
  } finally {
    setSubmitting(false);
    if (!form.hidden) mostrarProgresso(percentualDoPasso());
  }
});

telegramLink.addEventListener("click", () => {
  void registerEvent("telegram_aberto");
  window.setTimeout(refreshActivationStatus, 1500);
});

window.addEventListener("focus", () => {
  void refreshActivationStatus();
});

dialog.addEventListener("click", (event) => {
  if (event.target === dialog) closeSignup();
});
dialog.addEventListener("close", () => { document.body.style.overflow = ""; });

document.addEventListener("keydown", (event) => {
  if (event.defaultPrevented) return;
  if (event.key === "Escape" && dialog.open) closeSignup();
  if (event.key === "Enter" && (dialog.open || !accountPage.hidden) && !form.hidden && !nextStep.hidden && event.target.matches("input, select")) {
    event.preventDefault();
    avancarPasso();
  }
});

function authRedirect() {
  return window.location.origin + window.location.pathname;
}

function requireCaptcha() {
  if (!window.RADAR_CONFIG.turnstileSiteKey) return undefined;
  if (!captchaToken) throw validationError("Conclua a verificação de segurança antes de continuar.");
  return captchaToken;
}

function resetCaptcha() {
  captchaToken = "";
  if (captchaWidget !== null) window.turnstile?.reset(captchaWidget);
}

function setupCaptcha() {
  if (!window.RADAR_CONFIG.turnstileSiteKey) return;
  window.radarCaptchaReady = () => {
    captchaWidget = window.turnstile.render("#captcha-container", {
      sitekey: window.RADAR_CONFIG.turnstileSiteKey,
      callback: (token) => { captchaToken = token; },
      "expired-callback": () => { captchaToken = ""; },
      "error-callback": () => {
        captchaToken = "";
        setFormMessage("A verificação de segurança falhou. Confira sua conexão e tente novamente.");
      },
    });
  };
  const script = document.createElement("script");
  script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=radarCaptchaReady&render=explicit";
  script.async = true;
  script.onerror = () => setFormMessage("Não foi possível carregar a verificação de segurança. Recarregue a página.");
  document.head.append(script);
}

function updateResendButton() {
  if (assistanceMode !== "resend") return;
  const remaining = Math.max(0, Math.ceil((resendAvailableAt - Date.now()) / 1000));
  const button = document.querySelector("#assistance-submit");
  button.disabled = remaining > 0;
  button.textContent = remaining > 0 ? `Reenviar em ${remaining}s` : "Reenviar confirmação";
  if (!remaining && resendTimer) {
    window.clearInterval(resendTimer);
    resendTimer = null;
  }
}

function startResendCooldown() {
  resendAvailableAt = Date.now() + 60000;
  if (resendTimer) window.clearInterval(resendTimer);
  resendTimer = window.setInterval(updateResendButton, 1000);
  updateResendButton();
}

function showAssistance(mode, email = "") {
  assistanceMode = mode;
  form.hidden = true;
  progressWrap.hidden = true;
  successState.hidden = true;
  esconderConta();
  document.querySelector("#auth-assistance").hidden = false;
  rotularDialogo("assistance-title");
  document.querySelector("#captcha-container").hidden = mode === "new-password";
  const definingPassword = mode === "new-password";
  const emailInput = document.querySelector("#assistance-email");
  const passwordInput = document.querySelector("#assistance-password");
  document.querySelector("#assistance-email-field").hidden = definingPassword;
  document.querySelector("#assistance-password-field").hidden = !definingPassword;
  emailInput.required = !definingPassword;
  passwordInput.required = definingPassword;
  emailInput.value = email || emailInput.value || form.elements.email.value;
  passwordInput.value = "";
  const content = {
    resend: ["Confirme seu e-mail", "Abra o link em qualquer aparelho. Se precisar, corrija o endereço e solicite outro link.", "Reenviar confirmação"],
    reset: ["Recuperar senha", "Informe o e-mail da sua conta para receber um link de recuperação.", "Enviar link de recuperação"],
    "new-password": ["Defina sua nova senha", "Use uma senha com pelo menos 8 caracteres.", "Salvar nova senha"],
  }[mode];
  document.querySelector("#assistance-title").textContent = content[0];
  document.querySelector("#assistance-copy").textContent = content[1];
  document.querySelector("#assistance-submit").textContent = content[2];
  marcarOcupado(document.querySelector("#assistance-submit"), false);
  setFormMessage();
  updateResendButton();
  openDialog();
  (definingPassword ? passwordInput : emailInput).focus();
}

document.querySelector("#forgot-password").addEventListener("click", () => showAssistance("reset"));
document.querySelector("#open-resend").addEventListener("click", () => showAssistance("resend"));
document.querySelector("#assistance-back").addEventListener("click", () => {
  resetDialogView();
  setAuthMode("login");
  showStep(PASSO_CONTA);
});

document.querySelector("#assistance-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const mode = assistanceMode;
  if (mode === "resend" && Date.now() < resendAvailableAt) return;
  const button = document.querySelector("#assistance-submit");
  if (button.disabled) return;
  marcarOcupado(button, true);
  setFormMessage();
  try {
    const email = document.querySelector("#assistance-email").value.trim();
    if (mode === "new-password") {
      if (!recoverySession || !(await currentSession())) throw validationError("Solicite um novo link de recuperação para definir sua senha.");
      const password = document.querySelector("#assistance-password").value;
      if (password.length < 8) throw validationError(mensagensValidacao.senha);
      const { error } = await getClient().auth.updateUser({ password });
      if (error) throw error;
      document.querySelector("#assistance-password").value = "";
      recoverySession = false;
      window.history.replaceState(null, "", window.location.pathname);
      const { error: logoutError } = await getClient().auth.signOut();
      if (logoutError) throw logoutError;
      resetDialogView();
      setAuthMode("login");
      showStep(PASSO_CONTA);
      setFormMessage("Senha atualizada. Entre com sua nova senha.", "aviso");
      return;
    }
    const token = requireCaptcha();
    const result = mode === "resend"
      ? await getClient().auth.resend({ type: "signup", email, options: { emailRedirectTo: authRedirect(), captchaToken: token } })
      : await getClient().auth.resetPasswordForEmail(email, { redirectTo: authRedirect() + "?fluxo=recuperar", captchaToken: token });
    if (result.error) {
      if (result.error.status === 429 && mode === "resend") startResendCooldown();
      throw result.error;
    }
    if (mode === "resend") startResendCooldown();
    setFormMessage("Se houver uma conta elegível para esse endereço, você receberá o link. Confira também o spam.", "aviso");
  } catch (error) {
    setFormMessage(humanizeError(error));
  } finally {
    resetCaptcha();
    marcarOcupado(button, false);
    updateResendButton();
  }
});

document.querySelectorAll("[data-toggle-password]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = button.dataset.togglePassword === "senha"
      ? form.elements.senha : document.querySelector("#assistance-password");
    const showing = input.type === "password";
    input.type = showing ? "text" : "password";
    const label = showing ? "Ocultar senha" : "Mostrar senha";
    button.setAttribute("aria-label", label);
    button.title = label;
    button.setAttribute("aria-pressed", String(showing));
  });
});

document.querySelector("#account-emails").addEventListener("change", async (event) => {
  const input = event.target;
  const requested = input.checked;
  input.disabled = true;
  try {
    const session = await currentSession();
    if (!session) throw validationError(MENSAGEM_SEM_SESSAO);
    const { data, error } = await getClient().from("perfis").update({ aceita_emails: requested })
      .eq("user_id", session.user.id).select("aceita_emails").single();
    if (error) throw error;
    input.checked = data.aceita_emails;
    setAccountMessage("Preferência de e-mails atualizada.", "aviso");
  } catch (error) {
    input.checked = !requested;
    setAccountMessage(humanizeError(error));
  } finally {
    input.disabled = false;
  }
});

document.querySelector("#download-data").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  marcarOcupado(button, true);
  try {
    const { data, error } = await getClient().rpc("baixar_meus_dados");
    if (error) throw error;
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "meus-dados-radar.json";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setAccountMessage("Seus dados foram preparados para download.", "aviso");
  } catch (error) {
    setAccountMessage(humanizeError(error));
  } finally {
    marcarOcupado(button, false);
  }
});

document.querySelector("#success-account").addEventListener("click", async () => {
  try {
    showAccount(await perfilAtual());
  } catch (error) {
    setFormMessage(humanizeError(error));
  }
});

document.querySelector("#logout-account").addEventListener("click", async () => {
  const { error } = await getClient().auth.signOut();
  if (error) { setAccountMessage(humanizeError(error)); return; }
  clearPendingProfile();
  mostrarChamadaDeConta(false);
  closeSignup();
  limparRascunhoDoCadastro();
  resetDialogView();
  setAuthMode("login");
  showStep(PASSO_CONTA);
});

setupCaptcha();

if (!landingJaContadaNestaSessao()) {
  void registerEvent("landing_visualizada", { pagina: window.location.pathname });
}
resumeConfirmedSignup();
