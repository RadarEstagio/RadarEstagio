import { cidadeDaLista, cidadesParecidas, homonimasDe } from "../domain/cidades.js";
import { CONFIRMACOES, SECOES_DA_CONTA, VALORES_DOS_MOTIVOS_DE_PAUSA, dataDoApagamento } from "../domain/conta.js";
import { areaDoCurso } from "../domain/cursos.js";
import {
  MAXIMO_DE_HABILIDADES,
  MENSAGEM_SEM_CONFIGURACAO,
  MENSAGEM_SEM_PERFIL,
  MENSAGEM_SEM_SESSAO,
  MODALIDADES_ACEITAS,
  TAMANHO_MAXIMO_DA_HABILIDADE,
  VERSAO_DOS_TERMOS,
  emailValido,
  erroDeValidacao,
  mensagemHumana,
  mensagensDeValidacao,
} from "../domain/perfil.js";
import { textoDeBusca } from "../domain/texto.js";
import { criarPaginas } from "../landing/paginas.js";
import { criarCaptcha } from "../services/captcha.js";
import { criarCatalogos } from "../services/catalogos.js";
import { criarEventos } from "../services/eventos.js";
import { enderecoDeRetorno, lerRetornoDoAuth } from "./navegacao.js";

export const PASSO_CONTA = 1;
export const PASSO_MOMENTO = 2;
export const PASSO_HABILIDADES = 3;
export const PASSO_PREFERENCIAS = 4;
export const HABILIDADES_INICIAIS = ["Python", "JavaScript", "Java", "React", "SQL", "Git", "Excel", "Power BI", "Linux", "Redes"];

const PASSOS_DO_PERFIL = [PASSO_MOMENTO, PASSO_HABILIDADES, PASSO_PREFERENCIAS];
const PROGRESSO_AO_CONFIRMAR = 100;
const CHAVE_DO_PERFIL_PENDENTE = "radar-perfil-pendente";
const COLUNAS_DO_PERFIL =
  "curso,periodo,habilidades,cidade,modalidade,areas_de_interesse,telegram_chat_id,token_vinculo,ativo,motivo_pausa,excluida_em,aceita_emails,termos_aceitos_em,versao_dos_termos";
const CAMPOS_DO_PASSO = {
  [PASSO_CONTA]: ["email", "senha", "aceitou_termos", "aceita_emails"],
  [PASSO_MOMENTO]: ["curso", "periodo"],
  [PASSO_HABILIDADES]: [],
  [PASSO_PREFERENCIAS]: ["cidade", "modalidade"],
};
const SELETOR_DO_CAMPO = {
  "custom-skill": "#custom-skill",
  cidade: "#cidade",
  senha: "#signup-password",
};

function camposVazios() {
  return {
    email: "",
    senha: "",
    curso: "",
    periodo: "",
    cidade: "",
    modalidade: "",
    aceitou_termos: false,
    aceita_emails: false,
    habilidade_digitada: "",
  };
}

function estadoInicial() {
  return {
    superficie: "fechada",
    tela: "formulario",
    autenticado: false,
    modo: "signup",
    edicao: false,
    credenciaisOcultas: false,
    passos: [...PASSOS_DO_PERFIL, PASSO_CONTA],
    passo: PASSO_CONTA,
    progresso: null,
    campos: camposVazios(),
    habilidades: [],
    semHabilidades: false,
    sugeridas: HABILIDADES_INICIAIS,
    avisoDeHabilidades: false,
    subareas: null,
    areasEscolhidas: [],
    cidades: { aberta: false, opcoes: null, destacada: -1, avisoDeCatalogo: false },
    erro: null,
    mensagem: { texto: "", tom: "erro" },
    enviando: false,
    senhasVisiveis: {},
    assistencia: { modo: null, email: "", senha: "", restante: 0, ocupada: false },
    sucesso: {
      kicker: "Perfil salvo",
      titulo: "Agora, ative as entregas.",
      copy: "Vincule seu Telegram para receber as vagas selecionadas pelo Radar.",
      token: null,
      linkVisivel: false,
    },
    conta: {
      perfil: null,
      mensagem: { texto: "", tom: "erro" },
      confirmacao: null,
      pausa: { aberta: false, motivo: null, mensagem: "", ocupada: false },
      alternando: false,
      emails: { valor: false, ocupado: false },
      baixando: false,
      secao: SECOES_DA_CONTA[0].hash,
    },
    foco: null,
  };
}

export function captchaOculto(estado) {
  return estado.tela === "sucesso" || estado.tela === "conta"
    || (estado.tela === "assistencia" && estado.assistencia.modo === "new-password");
}

export function criarControlador({ janela, criarCliente }) {
  const documento = janela.document;
  const paginas = criarPaginas(documento);
  const retorno = lerRetornoDoAuth(janela.location);
  const catalogos = criarCatalogos(janela);
  const eventos = criarEventos({ janela, obterCliente });
  const captcha = criarCaptcha({
    janela,
    chave: configuracao().turnstileSiteKey ?? "",
    aoFalhar: (texto) => mostrarMensagem(texto),
  });
  const ouvintes = new Set();
  const limpezas = [];
  let estado = estadoInicial();
  let cliente = null;
  let sessaoDeRecuperacao = false;
  let reenvioDisponivelEm = 0;
  let temporizadorDoReenvio = null;
  let identidadeDoFormulario = 0;
  let requisicaoDeHabilidades = 0;
  let requisicaoDeAreas = 0;
  let areasSalvas = [];

  function configuracao() {
    return janela.RADAR_CONFIG ?? {};
  }

  function mudar(transformar) {
    estado = { ...estado, ...transformar(estado) };
    for (const ouvinte of ouvintes) ouvinte();
  }

  function mudarCampos(parcial) {
    mudar((atual) => ({ campos: { ...atual.campos, ...parcial } }));
  }

  function mudarConta(parcial) {
    mudar((atual) => ({ conta: { ...atual.conta, ...parcial } }));
  }

  function mudarPausa(parcial) {
    mudar((atual) => ({ conta: { ...atual.conta, pausa: { ...atual.conta.pausa, ...parcial } } }));
  }

  function mudarAssistencia(parcial) {
    mudar((atual) => ({ assistencia: { ...atual.assistencia, ...parcial } }));
  }

  function mudarCidades(parcial) {
    mudar((atual) => ({ cidades: { ...atual.cidades, ...parcial } }));
  }

  function focar(seletor) {
    mudar((atual) => ({ foco: { seletor, versao: (atual.foco?.versao ?? 0) + 1 } }));
  }

  function obterCliente() {
    if (cliente) return cliente;
    const { supabaseUrl, supabasePublishableKey } = configuracao();
    if (!supabaseUrl || !supabasePublishableKey) throw new Error(MENSAGEM_SEM_CONFIGURACAO);
    cliente = criarCliente(supabaseUrl, supabasePublishableKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    });
    cliente.auth.onAuthStateChange((evento) => {
      if (evento !== "PASSWORD_RECOVERY") return;
      sessaoDeRecuperacao = true;
      janela.setTimeout(() => mostrarAssistencia("new-password"), 0);
    });
    return cliente;
  }

  function mostrarMensagem(texto = "", tom = "erro") {
    mudar(() => ({ mensagem: { texto, tom } }));
  }

  function mostrarMensagemDaConta(texto = "", tom = "erro") {
    mudarConta({ mensagem: { texto, tom } });
  }

  function consentimentoExigido() {
    return estado.modo === "signup" && !estado.edicao;
  }

  function mostrarPasso(passo) {
    mudar((atual) => ({ passo: atual.passos.includes(passo) ? passo : atual.passos[0], progresso: null }));
    const seletorDoPasso = `.form-step[data-step="${estado.passo}"]`;
    focar(`${seletorDoPasso} input:not([type="hidden"]), ${seletorDoPasso} select, ${seletorDoPasso} button`);
  }

  function atualizarPassos() {
    mudar((atual) => {
      if (atual.modo === "login") return { passos: [PASSO_CONTA] };
      if (atual.edicao) return { passos: [...PASSOS_DO_PERFIL] };
      return { passos: [...PASSOS_DO_PERFIL, PASSO_CONTA] };
    });
    mostrarPasso(estado.passo);
  }

  function limparErroDoCampo() {
    if (estado.erro) mudar(() => ({ erro: null }));
  }

  function marcarErroNoCampo(campo, mensagem) {
    mudar(() => ({ erro: { campo, mensagem } }));
    focar(SELETOR_DO_CAMPO[campo] ?? `#signup-form [name="${campo}"]`);
  }

  function campoValido(nome) {
    const { campos, credenciaisOcultas } = estado;
    const email = campos.email.trim();
    if (nome === "email") return (credenciaisOcultas || email !== "") && (email === "" || emailValido(email));
    if (nome === "senha") {
      return (credenciaisOcultas || campos.senha !== "") && (campos.senha === "" || campos.senha.length >= 8);
    }
    if (nome === "aceitou_termos") return !consentimentoExigido() || campos.aceitou_termos;
    if (nome === "curso") return campos.curso !== "";
    if (nome === "periodo") return campos.periodo !== "";
    if (nome === "cidade") return campos.cidade.length >= 2;
    if (nome === "modalidade") return campos.modalidade !== "";
    return true;
  }

  function limparErroSeCorrigido(nome) {
    if (!estado.erro || estado.erro.campo === "custom-skill" || estado.erro.campo !== nome) return;
    if (campoValido(nome)) limparErroDoCampo();
  }

  function alterarCampo(nome, valor) {
    mudarCampos({ [nome]: valor });
    limparErroSeCorrigido(nome);
  }

  function alternarSenha(alvo) {
    mudar((atual) => ({ senhasVisiveis: { ...atual.senhasVisiveis, [alvo]: !atual.senhasVisiveis[alvo] } }));
  }

  async function carregarCidades() {
    const catalogo = await catalogos.carregarCidades();
    mudarCidades({ avisoDeCatalogo: !catalogo });
    return catalogo;
  }

  function cidadeDoFormulario() {
    const digitada = estado.campos.cidade.trim();
    const catalogo = catalogos.cidadesCarregadas();
    if (!catalogo) return digitada.length >= 2 ? digitada : null;
    return cidadeDaLista(catalogo, digitada);
  }

  function mensagemDaCidade() {
    const busca = textoDeBusca(estado.campos.cidade);
    if (!busca) return mensagensDeValidacao.cidade;
    const catalogo = catalogos.cidadesCarregadas();
    if (catalogo && homonimasDe(catalogo, busca).length > 1) {
      return "Existe mais de uma cidade com esse nome. Escolha a do seu estado na lista.";
    }
    return "Escolha sua cidade na lista, como Rio de Janeiro, RJ.";
  }

  function mostrarCidades(texto) {
    const catalogo = catalogos.cidadesCarregadas();
    if (!catalogo) return;
    mudarCidades({ aberta: true, opcoes: cidadesParecidas(catalogo, texto), destacada: -1 });
  }

  async function abrirCidades() {
    const catalogo = await carregarCidades();
    const digitada = estado.campos.cidade.trim();
    mostrarCidades(catalogo && cidadeDaLista(catalogo, digitada) === digitada ? "" : digitada);
  }

  function fecharCidades() {
    mudarCidades({ aberta: false, destacada: -1 });
  }

  function destacarCidade(posicao) {
    const total = estado.cidades.opcoes?.length ?? 0;
    if (total === 0) return;
    mudarCidades({ destacada: (posicao + total) % total });
  }

  function escolherCidade(nome) {
    mudarCampos({ cidade: nome });
    fecharCidades();
    limparErroSeCorrigido("cidade");
  }

  function focarNaCidade() {
    void carregarCidades();
  }

  async function digitarCidade(valor) {
    alterarCampo("cidade", valor);
    await carregarCidades();
    if (documento.activeElement?.id === "cidade") mostrarCidades(estado.campos.cidade);
  }

  function teclarNaCidade(evento) {
    const { aberta, destacada, opcoes } = estado.cidades;
    if (evento.key === "ArrowDown" || evento.key === "ArrowUp") {
      evento.preventDefault();
      if (!aberta) void abrirCidades();
      else destacarCidade(evento.key === "ArrowDown" ? destacada + 1 : Math.max(destacada, 0) - 1);
    } else if (evento.key === "Enter" && aberta && destacada >= 0) {
      evento.preventDefault();
      escolherCidade(opcoes[destacada].nome);
    } else if (evento.key === "Escape" && aberta) {
      evento.preventDefault();
      fecharCidades();
    }
  }

  function sairDaCidade() {
    fecharCidades();
    const cidade = cidadeDaLista(catalogos.cidadesCarregadas(), estado.campos.cidade);
    if (cidade) mudarCampos({ cidade });
  }

  function alternarListaDeCidades() {
    if (estado.cidades.aberta) {
      fecharCidades();
      return;
    }
    focar("#cidade");
    void abrirCidades();
  }

  function definirHabilidades(habilidades) {
    mudar((atual) => ({
      habilidades,
      erro: habilidades.length > 0 && atual.erro?.campo === "custom-skill" ? null : atual.erro,
    }));
  }

  function adicionarHabilidadeDigitada() {
    const habilidade = estado.campos.habilidade_digitada.trim().slice(0, TAMANHO_MAXIMO_DA_HABILIDADE);
    if (!habilidade) return;
    const jaEscolhida = estado.habilidades.includes(habilidade);
    if (estado.habilidades.length >= MAXIMO_DE_HABILIDADES && !jaEscolhida) {
      marcarErroNoCampo("custom-skill", `Escolha no máximo ${MAXIMO_DE_HABILIDADES} habilidades.`);
      return;
    }
    definirHabilidades(jaEscolhida ? estado.habilidades : [...estado.habilidades, habilidade]);
    mudar((atual) => ({ semHabilidades: false, campos: { ...atual.campos, habilidade_digitada: "" } }));
    mostrarMensagem();
  }

  function removerHabilidade(habilidade) {
    const restantes = estado.habilidades.filter((item) => item !== habilidade);
    definirHabilidades(restantes);
    if (restantes.length === 0) mudar(() => ({ semHabilidades: false }));
  }

  function alternarHabilidadeSugerida(habilidade) {
    if (estado.habilidades.includes(habilidade)) removerHabilidade(habilidade);
    else {
      definirHabilidades([...estado.habilidades, habilidade]);
      mudar(() => ({ semHabilidades: false }));
    }
    mostrarMensagem();
  }

  function teclarNaHabilidade(evento) {
    if (evento.key !== "Enter") return;
    evento.preventDefault();
    adicionarHabilidadeDigitada();
  }

  function continuarSemHabilidades() {
    if (estado.habilidades.length > 0) return;
    mudar(() => ({ semHabilidades: true }));
    avancarPasso();
  }

  function alternarArea(valor) {
    mudar((atual) => ({
      areasEscolhidas: atual.areasEscolhidas.includes(valor)
        ? atual.areasEscolhidas.filter((escolhida) => escolhida !== valor)
        : [...atual.areasEscolhidas, valor],
    }));
  }

  function respostaAntiga(requisicao, atual, identidade, curso) {
    return requisicao !== atual || identidade !== identidadeDoFormulario || estado.campos.curso !== curso;
  }

  async function montarAreasDoCurso() {
    const requisicao = ++requisicaoDeAreas;
    const identidade = identidadeDoFormulario;
    const curso = estado.campos.curso;
    const catalogo = await catalogos.carregarAreas();
    if (respostaAntiga(requisicao, requisicaoDeAreas, identidade, curso)) return;
    const area = areaDoCurso(curso, catalogo);
    mudar(() => ({ subareas: area ? area.subareas : null }));
  }

  async function montarHabilidadesDoCurso() {
    const requisicao = ++requisicaoDeHabilidades;
    const identidade = identidadeDoFormulario;
    const curso = estado.campos.curso;
    const catalogo = await catalogos.carregarAreas();
    if (respostaAntiga(requisicao, requisicaoDeHabilidades, identidade, curso)) return;
    if (!catalogo) {
      mudar(() => ({ sugeridas: [], avisoDeHabilidades: true }));
      return;
    }
    const area = areaDoCurso(curso, catalogo);
    mudar(() => ({ sugeridas: area?.habilidades ?? [], avisoDeHabilidades: false }));
  }

  function areasDeInteresseDoFormulario() {
    const marcadas = (estado.subareas ?? [])
      .map((subarea) => subarea.valor)
      .filter((valor) => estado.areasEscolhidas.includes(valor));
    const catalogo = catalogos.areasCarregadas();
    if (!catalogo) return [...areasSalvas];
    const area = areaDoCurso(estado.campos.curso, catalogo);
    if (!area) return [];
    const permitidas = new Set(area.subareas.map((subarea) => subarea.valor));
    return marcadas.filter((valor) => permitidas.has(valor));
  }

  function esquecerPerfilCarregado() {
    areasSalvas = [];
    mudar(() => ({ areasEscolhidas: [] }));
  }

  function validarPasso(passo) {
    limparErroDoCampo();
    if (passo === PASSO_HABILIDADES && estado.habilidades.length === 0 && !estado.semHabilidades) {
      mostrarPasso(passo);
      marcarErroNoCampo("custom-skill", "Escolha ou digite pelo menos uma habilidade.");
      return false;
    }
    mostrarMensagem();
    const cidade = passo === PASSO_PREFERENCIAS ? cidadeDoFormulario() : null;
    if (cidade) mudarCampos({ cidade });
    const invalido = CAMPOS_DO_PASSO[passo].find((campo) => {
      if (campo === "cidade") return !cidade;
      if (campo === "modalidade") return !MODALIDADES_ACEITAS.has(estado.campos.modalidade);
      return !campoValido(campo);
    });
    if (invalido) {
      mostrarPasso(passo);
      const mensagem = invalido === "cidade" ? mensagemDaCidade() : mensagensDeValidacao[invalido];
      marcarErroNoCampo(invalido, mensagem ?? "Revise os campos antes de continuar.");
      return false;
    }
    if (passo === PASSO_CONTA && consentimentoExigido() && !estado.campos.aceitou_termos) {
      mostrarPasso(passo);
      marcarErroNoCampo("aceitou_termos", mensagensDeValidacao.aceitou_termos);
      return false;
    }
    return true;
  }

  function validarFluxo() {
    return estado.passos.every((passo) => validarPasso(passo));
  }

  function avancarPasso() {
    const passo = estado.passo;
    if (passo === PASSO_HABILIDADES) adicionarHabilidadeDigitada();
    if (!validarPasso(passo)) return;
    if (passo === PASSO_MOMENTO) {
      void montarHabilidadesDoCurso();
      void eventos.registrar("etapa_perfil_concluida");
    }
    if (passo === PASSO_HABILIDADES) {
      void montarAreasDoCurso();
      void eventos.registrar("etapa_habilidades_concluida", { quantidade: estado.habilidades.length });
    }
    if (passo === PASSO_PREFERENCIAS) void eventos.registrar("etapa_preferencias_concluida");
    mostrarPasso(estado.passos[estado.passos.indexOf(passo) + 1]);
  }

  function voltarPasso() {
    mostrarPasso(estado.passos[estado.passos.indexOf(estado.passo) - 1]);
  }

  function definirModo(modo) {
    mudar(() => ({ modo, enviando: false }));
    mostrarMensagem();
    atualizarPassos();
  }

  function sairDoModoEdicao() {
    mudar(() => ({ edicao: false, credenciaisOcultas: false }));
    atualizarPassos();
  }

  function entrarNoModoEdicao() {
    definirModo("signup");
    mudar(() => ({ edicao: true, credenciaisOcultas: true }));
    atualizarPassos();
  }

  function reiniciarPainel() {
    identidadeDoFormulario += 1;
    mudar((atual) => ({
      tela: "formulario",
      assistencia: { ...atual.assistencia, modo: null },
      sucesso: { ...atual.sucesso, linkVisivel: false },
      conta: {
        ...atual.conta,
        confirmacao: null,
        mensagem: { texto: "", tom: "erro" },
        pausa: { ...atual.conta.pausa, aberta: false, mensagem: "" },
      },
      erro: null,
      mensagem: { texto: "", tom: "erro" },
      enviando: false,
      semHabilidades: false,
    }));
    sairDoModoEdicao();
    paginas.rotularDialogo("signup-title");
    mostrarPasso(PASSO_CONTA);
  }

  function limparRascunhoDoCadastro() {
    areasSalvas = [];
    mudar(() => ({
      campos: camposVazios(),
      habilidades: [],
      semHabilidades: false,
      areasEscolhidas: [],
      subareas: null,
      avisoDeHabilidades: false,
    }));
  }

  function mostrarChamadaDeConta(autenticado) {
    mudar(() => ({ autenticado }));
    paginas.rotularChamadas(autenticado);
  }

  function abrirDialogo() {
    if (estado.superficie !== "fechada") return;
    paginas.abrirDialogo();
    mudar(() => ({ superficie: "dialogo" }));
  }

  function abrirPaginaDaConta() {
    mostrarChamadaDeConta(true);
    if (estado.superficie === "pagina") return;
    paginas.mostrarConta();
    mudar(() => ({ superficie: "pagina" }));
    const url = new URL(janela.location.href);
    if (!url.searchParams.has("conta")) {
      url.searchParams.set("conta", "");
      janela.history.pushState(null, "", url);
    }
    janela.scrollTo(0, 0);
  }

  function sairDaPaginaDaConta() {
    if (estado.superficie !== "pagina") return;
    paginas.esconderConta();
    mudar(() => ({ superficie: "fechada" }));
    const url = new URL(janela.location.href);
    url.searchParams.delete("conta");
    url.hash = "";
    janela.history.replaceState(null, "", url);
    paginas.focarCadastro();
  }

  function fecharCadastro() {
    sairDaPaginaDaConta();
    paginas.fecharDialogo();
    mudar(() => ({ superficie: "fechada" }));
  }

  function mostrarSucesso({ kicker, titulo, copy, token = null, vinculado = false }) {
    mudar(() => ({
      tela: "sucesso",
      sucesso: { kicker, titulo, copy, token, linkVisivel: Boolean(token) && !vinculado },
    }));
    mostrarMensagem();
    paginas.rotularDialogo("success-title");
    focar("#success-title");
  }

  function mostrarSecaoDaConta(hash, atualizarEndereco = true) {
    const secao = SECOES_DA_CONTA.find((item) => item.hash === hash) ?? SECOES_DA_CONTA[0];
    mudarConta({ secao: secao.hash });
    if (atualizarEndereco) {
      const url = new URL(janela.location.href);
      url.hash = secao.hash;
      janela.history.replaceState(null, "", url);
    }
    janela.scrollTo(0, 0);
  }

  function mostrarConta(perfil) {
    abrirPaginaDaConta();
    mudar((atual) => ({
      tela: "conta",
      conta: {
        ...atual.conta,
        perfil,
        emails: { ...atual.conta.emails, valor: Boolean(perfil.aceita_emails) },
        confirmacao: null,
        mensagem: { texto: "", tom: "erro" },
        pausa: { ...atual.conta.pausa, aberta: false, mensagem: "" },
      },
    }));
    const secaoAtual = SECOES_DA_CONTA.find(({ hash }) => hash === janela.location.hash) ?? SECOES_DA_CONTA[0];
    mostrarSecaoDaConta(secaoAtual.hash, false);
    focar("#account-title");
  }

  function mostrarAtivacao(perfil) {
    abrirPaginaDaConta();
    mostrarSucesso({
      kicker: "Perfil salvo",
      titulo: "Agora, ative as entregas.",
      copy: "Vincule seu Telegram para receber as vagas selecionadas pelo Radar.",
      token: perfil.token_vinculo,
    });
  }

  function mostrarEstadoDoPerfil(perfil) {
    if (perfil.telegram_chat_id || perfil.excluida_em) {
      mostrarConta(perfil);
      return;
    }
    mostrarAtivacao(perfil);
  }

  function preencherFormularioCom(perfil) {
    mudar((atual) => ({
      campos: {
        ...atual.campos,
        curso: perfil.curso,
        periodo: String(perfil.periodo),
        cidade: perfil.cidade,
        modalidade: perfil.modalidade,
      },
      habilidades: [...perfil.habilidades],
      semHabilidades: perfil.habilidades.length === 0,
      areasEscolhidas: [...(perfil.areas_de_interesse ?? [])],
    }));
    areasSalvas = [...(perfil.areas_de_interesse ?? [])];
    void montarHabilidadesDoCurso();
    void montarAreasDoCurso();
  }

  function lerPerfilPendente() {
    try {
      return JSON.parse(janela.localStorage.getItem(CHAVE_DO_PERFIL_PENDENTE));
    } catch {
      return null;
    }
  }

  function limparPerfilPendente() {
    janela.localStorage.removeItem(CHAVE_DO_PERFIL_PENDENTE);
  }

  async function sessaoAtual() {
    const { data, error } = await obterCliente().auth.getSession();
    if (error) throw error;
    return data.session;
  }

  async function carregarPerfil(userId) {
    const { data, error } = await obterCliente()
      .from("perfis")
      .select(COLUNAS_DO_PERFIL)
      .eq("user_id", userId)
      .maybeSingle();
    if (error) throw error;
    return data;
  }

  async function perfilAtual() {
    const sessao = await sessaoAtual();
    if (!sessao) throw erroDeValidacao(MENSAGEM_SEM_SESSAO);
    const perfil = await carregarPerfil(sessao.user.id);
    if (!perfil) throw erroDeValidacao(MENSAGEM_SEM_PERFIL);
    return perfil;
  }

  function cadastroDoPerfil(perfil) {
    return {
      perfil,
      aceitou_termos: estado.campos.aceitou_termos,
      aceita_emails: estado.campos.aceita_emails,
      versao_dos_termos: VERSAO_DOS_TERMOS,
      sessao_id: eventos.idDaSessao(),
    };
  }

  function perfilDoFormulario() {
    adicionarHabilidadeDigitada();
    const { campos } = estado;
    const perfil = {
      curso: campos.curso.trim(),
      periodo: Number(campos.periodo),
      habilidades: estado.habilidades.join(",").split(",").map((item) => item.trim()).filter(Boolean),
      cidade: cidadeDoFormulario() ?? "",
      modalidade: campos.modalidade,
      areas_de_interesse: areasDeInteresseDoFormulario(),
    };
    if (!perfil.curso) throw erroDeValidacao(mensagensDeValidacao.curso);
    if (!Number.isInteger(perfil.periodo) || perfil.periodo < 1) throw erroDeValidacao(mensagensDeValidacao.periodo);
    if (perfil.habilidades.length === 0 && !estado.semHabilidades) {
      throw erroDeValidacao("Escolha ou digite pelo menos uma habilidade.");
    }
    if (perfil.habilidades.length > MAXIMO_DE_HABILIDADES) {
      throw erroDeValidacao(`Escolha no máximo ${MAXIMO_DE_HABILIDADES} habilidades.`);
    }
    if (!perfil.cidade) throw erroDeValidacao(mensagemDaCidade());
    if (!MODALIDADES_ACEITAS.has(perfil.modalidade)) throw erroDeValidacao(mensagensDeValidacao.modalidade);
    return perfil;
  }

  async function persistirPerfil(userId, perfil) {
    const existente = await carregarPerfil(userId);
    if (existente) {
      const { error } = await obterCliente()
        .from("perfis")
        .update({ ...perfil, atualizado_em: new Date().toISOString() })
        .eq("user_id", userId)
        .select("user_id")
        .single();
      if (error) throw error;
    } else {
      const { error } = await obterCliente().rpc("concluir_meu_cadastro", { cadastro: cadastroDoPerfil(perfil) });
      if (error) throw error;
    }
    limparPerfilPendente();
    void eventos.registrar("perfil_salvo");
    return carregarPerfil(userId);
  }

  async function autenticar(email, password, perfil) {
    const captchaToken = captcha.exigir();
    try {
      if (estado.modo === "login") {
        const { data, error } = await obterCliente().auth.signInWithPassword({
          email,
          password,
          options: { captchaToken },
        });
        if (error) throw error;
        return data.session;
      }
      const { data, error } = await obterCliente().auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: enderecoDeRetorno(janela.location),
          captchaToken,
          data: { cadastro_radar: cadastroDoPerfil(perfil) },
        },
      });
      if (error) throw error;
      return data.session;
    } finally {
      captcha.reiniciar();
    }
  }

  function prepararPerfilAusente(sessao) {
    reiniciarPainel();
    abrirPaginaDaConta();
    definirModo("signup");
    mudar((atual) => ({ campos: { ...atual.campos, email: sessao.user.email ?? "" }, credenciaisOcultas: true }));
    atualizarPassos();
    mostrarMensagem("Seu e-mail está confirmado. Complete seu perfil para continuar.", "aviso");
  }

  async function enviarCadastro(evento) {
    evento?.preventDefault();
    if (estado.enviando) return;
    if (estado.passos.includes(PASSO_PREFERENCIAS) && !catalogos.cidadesCarregadas()) {
      mudar(() => ({ enviando: true }));
      await carregarCidades();
      mudar(() => ({ enviando: false }));
    }
    if (!validarFluxo()) return;
    if (estado.passo === PASSO_PREFERENCIAS && estado.modo !== "login") {
      void eventos.registrar("etapa_preferencias_concluida");
    }
    const email = estado.campos.email.trim();
    const senha = estado.campos.senha;
    let salvamentoIniciado = false;
    mostrarMensagem();
    mudar(() => ({ enviando: true, progresso: PROGRESSO_AO_CONFIRMAR }));
    try {
      const perfil = estado.modo === "login" ? null : perfilDoFormulario();
      const sessaoExistente = await sessaoAtual();
      if (estado.edicao && !sessaoExistente) {
        sairDoModoEdicao();
        mostrarMensagem(MENSAGEM_SEM_SESSAO);
        return;
      }
      if (!estado.edicao && sessaoExistente && sessaoExistente.user.email !== email) {
        const { error } = await obterCliente().auth.signOut();
        if (error) throw error;
        esquecerPerfilCarregado();
      }
      const sessao = estado.edicao || sessaoExistente?.user.email === email
        ? sessaoExistente
        : await autenticar(email, senha, perfil);
      mudarCampos({ senha: "" });
      if (!sessao) {
        mostrarConfirmacao(email);
        return;
      }
      const existente = await carregarPerfil(sessao.user.id);
      if (existente && !estado.edicao) {
        mostrarEstadoDoPerfil(existente);
        return;
      }
      if (estado.modo === "login") {
        prepararPerfilAusente(sessao);
        return;
      }
      salvamentoIniciado = true;
      const perfilSalvo = await persistirPerfil(sessao.user.id, perfil);
      mostrarEstadoDoPerfil(perfilSalvo);
    } catch (erro) {
      if (erro?.code === "email_not_confirmed") mostrarAssistencia("resend", email);
      mostrarMensagem(mensagemHumana(erro, { perfilPendente: salvamentoIniciado }));
    } finally {
      mudar((atual) => ({ enviando: false, progresso: atual.tela === "formulario" ? null : atual.progresso }));
    }
  }

  async function atualizarAtivacao() {
    try {
      const sessao = await sessaoAtual();
      if (!sessao) return;
      const perfil = await carregarPerfil(sessao.user.id);
      if (perfil) mostrarEstadoDoPerfil(perfil);
    } catch {
      mudar((atual) => ({
        sucesso: {
          ...atual.sucesso,
          copy: "O Telegram foi aberto, mas ainda não conseguimos confirmar o vínculo. Tente voltar a esta janela novamente.",
        },
      }));
    }
  }

  function abrirTelegram() {
    void eventos.registrar("telegram_aberto");
    janela.setTimeout(atualizarAtivacao, 1500);
  }

  function abrirLogin() {
    reiniciarPainel();
    definirModo("login");
    mostrarPasso(PASSO_CONTA);
    abrirDialogo();
  }

  async function abrirCadastro() {
    reiniciarPainel();
    if (!estado.autenticado && estado.modo === "signup") mostrarPasso(PASSO_MOMENTO);
    if (!estado.autenticado) abrirDialogo();
    try {
      const sessao = await sessaoAtual();
      mostrarChamadaDeConta(Boolean(sessao));
      if (!sessao) {
        limparRascunhoDoCadastro();
        definirModo("signup");
        mostrarPasso(PASSO_MOMENTO);
        abrirDialogo();
        return;
      }
      mudarCampos({ email: sessao.user.email ?? "" });
      const perfil = await carregarPerfil(sessao.user.id);
      if (perfil) mostrarEstadoDoPerfil(perfil);
      else prepararPerfilAusente(sessao);
    } catch (erro) {
      abrirDialogo();
      mostrarMensagem(mensagemHumana(erro));
    }
  }

  async function retomarCadastroConfirmado() {
    try {
      const sessao = await sessaoAtual();
      mostrarChamadaDeConta(Boolean(sessao));
      if (retorno.erroDoLink) {
        mostrarAssistencia(retorno.voltandoDaRecuperacao ? "reset" : "resend");
        mostrarMensagem("Esse link expirou ou já foi usado. Solicite um novo abaixo.");
        return;
      }
      if (retorno.voltandoDaRecuperacao || sessaoDeRecuperacao) {
        if (sessao && sessaoDeRecuperacao) mostrarAssistencia("new-password");
        else if (!sessao) mostrarAssistencia("reset");
        return;
      }
      if (!sessao) {
        if (retorno.consulta.has("conta")) abrirLogin();
        return;
      }
      const perfil = await carregarPerfil(sessao.user.id);
      if (!retorno.voltandoDoAuth && !lerPerfilPendente() && !retorno.consulta.has("conta")) return;
      limparPerfilPendente();
      if (perfil) mostrarEstadoDoPerfil(perfil);
      else prepararPerfilAusente(sessao);
    } catch (erro) {
      reiniciarPainel();
      abrirDialogo();
      mostrarMensagem(mensagemHumana(erro, { perfilPendente: true }));
    }
  }

  function atualizarBotaoDeReenvio() {
    if (estado.assistencia.modo !== "resend") return;
    const restante = Math.max(0, Math.ceil((reenvioDisponivelEm - Date.now()) / 1000));
    mudarAssistencia({ restante });
    if (!restante && temporizadorDoReenvio) {
      janela.clearInterval(temporizadorDoReenvio);
      temporizadorDoReenvio = null;
    }
  }

  function iniciarEsperaDoReenvio() {
    reenvioDisponivelEm = Date.now() + 60000;
    if (temporizadorDoReenvio) janela.clearInterval(temporizadorDoReenvio);
    temporizadorDoReenvio = janela.setInterval(atualizarBotaoDeReenvio, 1000);
    atualizarBotaoDeReenvio();
  }

  function mostrarAssistencia(modo, email = "") {
    mudar((atual) => ({
      tela: "assistencia",
      assistencia: {
        ...atual.assistencia,
        modo,
        email: email || atual.assistencia.email || atual.campos.email,
        senha: "",
        ocupada: false,
      },
    }));
    paginas.rotularDialogo("assistance-title");
    mostrarMensagem();
    atualizarBotaoDeReenvio();
    abrirDialogo();
    focar(modo === "new-password" ? "#assistance-password" : "#assistance-email");
  }

  function mostrarConfirmacao(email) {
    mostrarAssistencia("resend", email);
    mostrarMensagem(
      "Se o cadastro foi aceito, você receberá um link. Confirme em qualquer aparelho para continuar.",
      "aviso",
    );
    iniciarEsperaDoReenvio();
  }

  function alterarAssistencia(campo, valor) {
    mudarAssistencia({ [campo]: valor });
  }

  function voltarParaEntrar() {
    reiniciarPainel();
    definirModo("login");
    mostrarPasso(PASSO_CONTA);
  }

  async function enviarAssistencia(evento) {
    evento?.preventDefault();
    const { modo, ocupada, restante } = estado.assistencia;
    if (modo === "resend" && Date.now() < reenvioDisponivelEm) return;
    if (ocupada || (modo === "resend" && restante > 0)) return;
    mudarAssistencia({ ocupada: true });
    mostrarMensagem();
    try {
      const email = estado.assistencia.email.trim();
      if (modo === "new-password") {
        if (!sessaoDeRecuperacao || !(await sessaoAtual())) {
          throw erroDeValidacao("Solicite um novo link de recuperação para definir sua senha.");
        }
        const password = estado.assistencia.senha;
        if (password.length < 8) throw erroDeValidacao(mensagensDeValidacao.senha);
        const { error } = await obterCliente().auth.updateUser({ password });
        if (error) throw error;
        mudarAssistencia({ senha: "" });
        sessaoDeRecuperacao = false;
        janela.history.replaceState(null, "", janela.location.pathname);
        const { error: erroAoSair } = await obterCliente().auth.signOut();
        if (erroAoSair) throw erroAoSair;
        reiniciarPainel();
        definirModo("login");
        mostrarPasso(PASSO_CONTA);
        mostrarMensagem("Senha atualizada. Entre com sua nova senha.", "aviso");
        return;
      }
      const captchaToken = captcha.exigir();
      const endereco = enderecoDeRetorno(janela.location);
      const resultado = modo === "resend"
        ? await obterCliente().auth.resend({ type: "signup", email, options: { emailRedirectTo: endereco, captchaToken } })
        : await obterCliente().auth.resetPasswordForEmail(email, { redirectTo: `${endereco}?fluxo=recuperar`, captchaToken });
      if (resultado.error) {
        if (resultado.error.status === 429 && modo === "resend") iniciarEsperaDoReenvio();
        throw resultado.error;
      }
      if (modo === "resend") iniciarEsperaDoReenvio();
      mostrarMensagem(
        "Se houver uma conta elegível para esse endereço, você receberá o link. Confira também o spam.",
        "aviso",
      );
    } catch (erro) {
      mostrarMensagem(mensagemHumana(erro));
    } finally {
      captcha.reiniciar();
      mudarAssistencia({ ocupada: false });
      atualizarBotaoDeReenvio();
    }
  }

  async function editarPerfil() {
    try {
      const perfil = await perfilAtual();
      preencherFormularioCom(perfil);
      mudar(() => ({ tela: "formulario" }));
      entrarNoModoEdicao();
      mudar(() => ({ enviando: false }));
      mostrarPasso(PASSO_MOMENTO);
    } catch (erro) {
      mostrarMensagemDaConta(mensagemHumana(erro));
    }
  }

  async function alternarEntregas() {
    if (estado.conta.alternando) return;
    mudarConta({ alternando: true });
    mostrarMensagemDaConta();
    try {
      const perfil = await perfilAtual();
      const estavaAtivo = perfil.ativo;
      const sessao = await sessaoAtual();
      if (!sessao) throw erroDeValidacao(MENSAGEM_SEM_SESSAO);
      const atualizacao = estavaAtivo
        ? { ativo: false, atualizado_em: new Date().toISOString() }
        : { ativo: true, motivo_pausa: null, atualizado_em: new Date().toISOString() };
      const { error } = await obterCliente().from("perfis").update(atualizacao).eq("user_id", sessao.user.id);
      if (error) throw error;
      mostrarConta({ ...perfil, ativo: !estavaAtivo, motivo_pausa: null });
      if (estavaAtivo) {
        mudarPausa({ aberta: true, mensagem: "", motivo: null });
        focar("#pause-reason-title");
      }
    } catch (erro) {
      mostrarMensagemDaConta(mensagemHumana(erro));
    } finally {
      mudarConta({ alternando: false });
    }
  }

  function escolherMotivo(motivo) {
    mudarPausa({ motivo });
  }

  async function salvarMotivoDaPausa() {
    if (estado.conta.pausa.ocupada) return;
    const motivo = estado.conta.pausa.motivo;
    if (!motivo) {
      mudarPausa({ mensagem: "Escolha um motivo ou clique em “Pular”." });
      focar('input[name="motivo-pausa"]');
      return;
    }
    mudarPausa({ ocupada: true });
    try {
      if (!VALORES_DOS_MOTIVOS_DE_PAUSA.has(motivo)) {
        throw erroDeValidacao("Escolha um dos motivos ou pule esta pergunta.");
      }
      const sessao = await sessaoAtual();
      if (!sessao) throw erroDeValidacao(MENSAGEM_SEM_SESSAO);
      const { data, error } = await obterCliente()
        .from("perfis")
        .update({ motivo_pausa: motivo, atualizado_em: new Date().toISOString() })
        .eq("user_id", sessao.user.id)
        .eq("ativo", false)
        .select("user_id,ativo,motivo_pausa")
        .maybeSingle();
      if (error) throw error;
      if (!data || data.ativo !== false) {
        throw erroDeValidacao("A conta não está mais pausada. Atualize o estado da conta e tente novamente.");
      }
      mostrarConta(await perfilAtual());
      mostrarMensagemDaConta("Motivo salvo.", "aviso");
    } catch (erro) {
      mudarPausa({ mensagem: mensagemHumana(erro) });
    } finally {
      mudarPausa({ ocupada: false });
    }
  }

  function pularMotivoDaPausa() {
    if (estado.conta.pausa.ocupada) return;
    mudarPausa({ aberta: false, mensagem: "" });
    focar("#account-title");
  }

  function pedirConfirmacao(acao) {
    mudarConta({ confirmacao: acao });
    focar("#account-confirm-no");
  }

  function fecharConfirmacao(restaurarFoco = true) {
    const acao = estado.conta.confirmacao;
    mudarConta({ confirmacao: null });
    if (restaurarFoco && acao) focar(CONFIRMACOES[acao].origem);
  }

  async function confirmarAcao() {
    const acao = estado.conta.confirmacao;
    fecharConfirmacao();
    mostrarMensagemDaConta();
    try {
      if (acao === "desvincular") {
        const { error } = await obterCliente().rpc("desvincular_meu_telegram");
        if (error) throw error;
        mostrarEstadoDoPerfil(await perfilAtual());
        return;
      }
      const { data, error } = await obterCliente().rpc("excluir_minha_conta");
      if (error) throw error;
      mostrarSucesso({
        kicker: "Exclusão agendada",
        titulo: "As entregas pararam agora.",
        copy: `Seus dados são apagados definitivamente em ${dataDoApagamento(data)}. Até lá, entre aqui de novo para cancelar.`,
      });
    } catch (erro) {
      mostrarMensagemDaConta(mensagemHumana(erro));
    }
  }

  async function cancelarExclusao() {
    mostrarMensagemDaConta();
    try {
      const { error } = await obterCliente().rpc("cancelar_exclusao_da_minha_conta");
      if (error) throw error;
      mostrarEstadoDoPerfil(await perfilAtual());
    } catch (erro) {
      mostrarMensagemDaConta(mensagemHumana(erro));
    }
  }

  async function alterarEmails(pedido) {
    mudarConta({ emails: { valor: pedido, ocupado: true } });
    try {
      const sessao = await sessaoAtual();
      if (!sessao) throw erroDeValidacao(MENSAGEM_SEM_SESSAO);
      const { data, error } = await obterCliente()
        .from("perfis")
        .update({ aceita_emails: pedido })
        .eq("user_id", sessao.user.id)
        .select("aceita_emails")
        .single();
      if (error) throw error;
      mudarConta({ emails: { valor: data.aceita_emails, ocupado: true } });
      mostrarMensagemDaConta("Preferência de e-mails atualizada.", "aviso");
    } catch (erro) {
      mudarConta({ emails: { valor: !pedido, ocupado: true } });
      mostrarMensagemDaConta(mensagemHumana(erro));
    } finally {
      mudar((atual) => ({ conta: { ...atual.conta, emails: { ...atual.conta.emails, ocupado: false } } }));
    }
  }

  async function baixarDados() {
    mudarConta({ baixando: true });
    try {
      const { data, error } = await obterCliente().rpc("baixar_meus_dados");
      if (error) throw error;
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const link = documento.createElement("a");
      link.href = url;
      link.download = "meus-dados-radar.json";
      documento.body.append(link);
      link.click();
      link.remove();
      janela.setTimeout(() => URL.revokeObjectURL(url), 1000);
      mostrarMensagemDaConta("Seus dados foram preparados para download.", "aviso");
    } catch (erro) {
      mostrarMensagemDaConta(mensagemHumana(erro));
    } finally {
      mudarConta({ baixando: false });
    }
  }

  async function abrirContaDoSucesso() {
    try {
      mostrarConta(await perfilAtual());
    } catch (erro) {
      mostrarMensagem(mensagemHumana(erro));
    }
  }

  async function sairDaConta() {
    const { error } = await obterCliente().auth.signOut();
    if (error) {
      mostrarMensagemDaConta(mensagemHumana(error));
      return;
    }
    limparPerfilPendente();
    mostrarChamadaDeConta(false);
    fecharCadastro();
    limparRascunhoDoCadastro();
    reiniciarPainel();
    definirModo("login");
    mostrarPasso(PASSO_CONTA);
  }

  function ouvir(alvo, tipo, funcao) {
    alvo.addEventListener(tipo, funcao);
    limpezas.push(() => alvo.removeEventListener(tipo, funcao));
  }

  function tratarTeclado(evento) {
    if (evento.defaultPrevented) return;
    if (evento.key === "Escape" && estado.superficie === "dialogo") fecharCadastro();
    const posicao = estado.passos.indexOf(estado.passo);
    const temProximoPasso = posicao < estado.passos.length - 1;
    if (
      evento.key === "Enter"
      && estado.superficie !== "fechada"
      && estado.tela === "formulario"
      && temProximoPasso
      && evento.target.matches?.("input, select")
    ) {
      evento.preventDefault();
      avancarPasso();
    }
  }

  function iniciar() {
    for (const botao of paginas.chamadasDeLogin) {
      ouvir(botao, "click", () => {
        if (estado.autenticado) {
          void abrirCadastro();
          return;
        }
        limparRascunhoDoCadastro();
        abrirLogin();
      });
    }
    for (const botao of paginas.chamadasDeCadastro) {
      ouvir(botao, "click", () => {
        if (!estado.autenticado) {
          void eventos.registrar("cta_cadastro_aberto", { origem: botao.dataset.eventOrigin ?? "desconhecida" });
        }
        void abrirCadastro();
      });
    }
    const inicioNoRodape = documento.querySelector("#footer-home");
    if (inicioNoRodape) {
      ouvir(inicioNoRodape, "click", (evento) => {
        if (estado.superficie !== "pagina") return;
        evento.preventDefault();
        fecharCadastro();
      });
    }
    ouvir(janela, "popstate", () => {
      if (new URLSearchParams(janela.location.search).has("conta")) void abrirCadastro();
      else fecharCadastro();
    });
    ouvir(janela, "hashchange", () => {
      if (estado.superficie !== "pagina" || estado.tela !== "conta") return;
      const secao = SECOES_DA_CONTA.find(({ hash }) => hash === janela.location.hash);
      if (secao) mostrarSecaoDaConta(secao.hash, false);
    });
    ouvir(janela, "focus", () => {
      if (estado.superficie === "fechada" || !estado.sucesso.linkVisivel) return;
      void atualizarAtivacao();
    });
    ouvir(paginas.dialogo, "click", (evento) => {
      if (evento.target === paginas.dialogo) fecharCadastro();
    });
    ouvir(paginas.dialogo, "close", () => {
      documento.body.style.overflow = "";
      if (estado.superficie === "dialogo") mudar(() => ({ superficie: "fechada" }));
    });
    ouvir(documento, "keydown", tratarTeclado);
    captcha.carregar();
    if (!eventos.landingJaContadaNestaSessao()) {
      void eventos.registrar("landing_visualizada", { pagina: janela.location.pathname });
    }
    return retomarCadastroConfirmado();
  }

  function encerrar() {
    for (const limpar of limpezas.splice(0)) limpar();
    if (temporizadorDoReenvio) janela.clearInterval(temporizadorDoReenvio);
    temporizadorDoReenvio = null;
    ouvintes.clear();
  }

  return {
    documento,
    dialogo: paginas.dialogo,
    paginaDaConta: paginas.conta,
    elementoDoCaptcha: captcha.elemento,
    estado: () => estado,
    assinar(ouvinte) {
      ouvintes.add(ouvinte);
      return () => ouvintes.delete(ouvinte);
    },
    linkDoTelegram: (token) => `https://t.me/${configuracao().telegramBot}?start=${token}`,
    exigirCaptcha: () => captcha.exigir(),
    iniciar,
    encerrar,
    alterarCampo,
    alternarSenha,
    definirModo,
    avancarPasso,
    voltarPasso,
    enviarCadastro,
    alternarHabilidadeSugerida,
    removerHabilidade,
    teclarNaHabilidade,
    continuarSemHabilidades,
    alternarArea,
    focarNaCidade,
    digitarCidade,
    teclarNaCidade,
    sairDaCidade,
    alternarListaDeCidades,
    escolherCidade,
    montarHabilidadesDoCurso,
    mostrarAssistencia,
    alterarAssistencia,
    enviarAssistencia,
    voltarParaEntrar,
    fecharCadastro,
    mostrarSecaoDaConta,
    abrirContaDoSucesso,
    abrirTelegram,
    editarPerfil,
    alternarEntregas,
    escolherMotivo,
    salvarMotivoDaPausa,
    pularMotivoDaPausa,
    pedirConfirmacao,
    fecharConfirmacao,
    confirmarAcao,
    cancelarExclusao,
    alterarEmails,
    baixarDados,
    sairDaConta,
  };
}
