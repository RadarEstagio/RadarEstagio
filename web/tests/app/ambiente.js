import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { act, fireEvent } from "@testing-library/react";
import { afterEach, expect } from "vitest";
import { iniciarAplicacao } from "../../src/app/iniciar.jsx";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

for (const armazenamento of ["localStorage", "sessionStorage"]) {
  if (!globalThis[armazenamento] && globalThis.jsdom?.window[armazenamento]) {
    Object.defineProperty(globalThis, armazenamento, {
      value: globalThis.jsdom.window[armazenamento],
      configurable: true,
      writable: true,
    });
  }
}

const pastaWeb = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const lerDaPastaWeb = (caminho) => readFileSync(resolve(pastaWeb, caminho), "utf8");
const html = lerDaPastaWeb("index.html");
export const areasJson = JSON.parse(lerDaPastaWeb("assets/areas.json"));
const cidadesJson = JSON.parse(lerDaPastaWeb("assets/cidades.json"));
const catalogos = { "assets/areas.json": areasJson, "assets/cidades.json": cidadesJson };

export const usuario = { id: "00000000-0000-4000-8000-000000000001", email: "teste@example.com" };
export const perfil = {
  curso: "Computação",
  periodo: 3,
  habilidades: ["Python"],
  cidade: "Recife, PE",
  modalidade: "remoto",
  areas_de_interesse: [],
  token_vinculo: "token",
  ativo: true,
  motivo_pausa: null,
  aceita_emails: false,
  telegram_chat_id: null,
};

let aplicacaoAberta = null;

afterEach(() => fecharAplicacao());

export function $(seletor) {
  return document.querySelector(seletor);
}

export function $$(seletor) {
  return [...document.querySelectorAll(seletor)];
}

function elemento(alvo) {
  return typeof alvo === "string" ? $(alvo) : alvo;
}

export function clicar(alvo) {
  fireEvent.click(elemento(alvo));
}

export function digitar(alvo, valor) {
  fireEvent.change(elemento(alvo), { target: { value: valor } });
}

export function marcar(alvo, marcado) {
  const caixa = elemento(alvo);
  if (caixa.checked !== marcado) fireEvent.click(caixa);
}

export function teclar(alvo, key) {
  fireEvent.keyDown(elemento(alvo), { key });
}

export function enviar(alvo) {
  fireEvent.submit(elemento(alvo));
}

export function focar(alvo) {
  act(() => elemento(alvo).focus());
}

export function executar(funcao) {
  act(() => {
    funcao();
  });
}

export async function executarAteTerminar(funcao) {
  await act(async () => {
    await funcao();
  });
}

export async function esperar(milissegundos = 15) {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, milissegundos));
  });
}

export function passoAtivo() {
  return $(".form-step.is-active").dataset.step;
}

export function dialogoAberto() {
  return $("#signup-dialog").hasAttribute("open");
}

export function progresso() {
  return [
    $("#progress-percent").textContent,
    $("#progress-track").getAttribute("aria-valuenow"),
    $("#progress-bar").style.width,
  ];
}

export function chamadas(calls, nome) {
  return calls.filter(([registrada]) => registrada === nome);
}

export function chamada(calls, nome) {
  const encontrada = calls.find(([registrada]) => registrada === nome);
  expect(encontrada, `chamada ${nome} ausente`).toBeTruthy();
  return encontrada;
}

export function eventos(calls, nome) {
  return calls.filter(([registrada, , dados]) => registrada === "insert" && dados?.nome === nome);
}

export function alterarCampo(nome, valor) {
  executar(() => aplicacaoAberta.controlador.alterarCampo(nome, valor));
}

export function preencher(incluirHabilidade = true) {
  const formulario = $("#signup-form");
  for (const [nome, valor] of Object.entries({
    curso: "Computação",
    periodo: "3",
    cidade: "Recife, PE",
    email: usuario.email,
    senha: "uma-senha-forte",
  })) {
    alterarCampo(nome, valor);
  }
  clicar(formulario.querySelector('[value="remoto"]'));
  if (incluirHabilidade) clicar('[data-skill="Python"]');
  marcar(formulario.elements.aceitou_termos, true);
  return formulario;
}

function janelaSemArmazenamento() {
  return new Proxy(window, {
    get(alvo, chave) {
      if (chave === "localStorage") throw new DOMException("armazenamento bloqueado", "SecurityError");
      const valor = Reflect.get(alvo, chave);
      return typeof valor === "function" && !/^[A-Z]/.test(String(chave)) ? valor.bind(alvo) : valor;
    },
    set(alvo, chave, valor) {
      return Reflect.set(alvo, chave, valor);
    },
  });
}

function criarClienteFalso({ sessao, perfilGuardado, calls, aoRegistrarAuth }) {
  return {
    auth: {
      getSession: async () => ({ data: { session: sessao } }),
      onAuthStateChange: (callback) => {
        aoRegistrarAuth(callback);
        return { data: { subscription: { unsubscribe() {} } } };
      },
      signUp: async (args) => {
        calls.push(["signup", args]);
        return { data: { session: null } };
      },
      signInWithPassword: async (args) => {
        calls.push(["login", args]);
        return { data: { session: { user: usuario } } };
      },
      resend: async (args) => {
        calls.push(["resend", args]);
        return {};
      },
      resetPasswordForEmail: async (email, opcoes) => {
        calls.push(["reset", email, opcoes]);
        return {};
      },
      updateUser: async (args) => {
        calls.push(["password", args]);
        return {};
      },
      signOut: async () => {
        calls.push(["logout"]);
        return {};
      },
    },
    from: (tabela) => {
      const consulta = {
        select: () => consulta,
        eq: () => consulta,
        insert: async (args) => {
          calls.push(["insert", tabela, args]);
          return {};
        },
        update: (args) => {
          calls.push(["update", tabela, args]);
          if (tabela === "perfis" && perfilGuardado) Object.assign(perfilGuardado, args);
          return consulta;
        },
        maybeSingle: async () => ({ data: perfilGuardado }),
        single: async () => ({ data: perfilGuardado }),
      };
      return consulta;
    },
    rpc: async (nome, args) => {
      calls.push(["rpc", nome, args]);
      return { data: {} };
    },
  };
}

export function abrirAplicacao({
  sessao = null,
  perfilSalvo = null,
  url = "/",
  chave = "",
  temaSalvo = null,
  armazenamentoBloqueado = false,
} = {}) {
  fecharAplicacao();
  const pagina = new DOMParser().parseFromString(html, "text/html");
  document.title = pagina.title;
  document.head.innerHTML = pagina.head.innerHTML;
  document.body.innerHTML = pagina.body.innerHTML;
  document.body.removeAttribute("class");
  document.body.removeAttribute("style");
  delete document.documentElement.dataset.tema;
  window.history.replaceState(null, "", url);
  window.localStorage.clear();
  window.sessionStorage.clear();
  if (temaSalvo) window.localStorage.setItem("radar-tema", temaSalvo);
  const armazenamentoDoHead = armazenamentoBloqueado
    ? new Proxy({}, { get() { throw new DOMException("armazenamento bloqueado", "SecurityError"); } })
    : window.localStorage;
  for (const script of document.head.querySelectorAll("script:not([src])")) {
    new Function("localStorage", "document", script.textContent)(armazenamentoDoHead, document);
  }
  const temaAntesDoApp = document.documentElement.dataset.tema;
  Object.defineProperty(window, "scrollY", { value: 0, configurable: true });
  window.scrollTo = () => {};
  window.fetch = async (caminho) => ({
    ok: Object.hasOwn(catalogos, String(caminho)),
    json: async () => catalogos[String(caminho)],
  });
  delete window.turnstile;
  delete window.radarCaptchaReady;
  window.RADAR_CONFIG = {
    supabaseUrl: "https://example.com",
    supabasePublishableKey: "public",
    telegramBot: "bot",
    turnstileSiteKey: chave,
  };
  const calls = [];
  let aoMudarAuth = () => {
    throw new Error("callback não registrado");
  };
  const cliente = criarClienteFalso({
    sessao,
    perfilGuardado: perfilSalvo ? structuredClone(perfilSalvo) : null,
    calls,
    aoRegistrarAuth: (callback) => {
      aoMudarAuth = callback;
    },
  });
  const janela = armazenamentoBloqueado ? janelaSemArmazenamento() : window;
  act(() => {
    aplicacaoAberta = iniciarAplicacao({ janela, criarCliente: () => cliente });
  });
  return {
    calls,
    cliente,
    controlador: aplicacaoAberta.controlador,
    temaAntesDoApp,
    eventoDeAuth: (evento) => executar(() => aoMudarAuth(evento)),
  };
}

export function fecharAplicacao() {
  if (!aplicacaoAberta) return;
  const aberta = aplicacaoAberta;
  aplicacaoAberta = null;
  act(() => aberta.encerrar());
}
