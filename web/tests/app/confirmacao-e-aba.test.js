import { fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, expect, test } from "vitest";
import { $, abrirAplicacao, alterarCampo, clicar, esperar, executar, perfil, usuario } from "./ambiente.js";

const perfilVinculado = { ...perfil, telegram_chat_id: "123" };
const metodosOriginais = {};
let fechamentos = 0;

beforeEach(() => {
  fechamentos = 0;
  for (const metodo of ["showModal", "close"]) {
    metodosOriginais[metodo] = Object.getOwnPropertyDescriptor(HTMLDialogElement.prototype, metodo);
  }
  HTMLDialogElement.prototype.showModal = function abrirModal() {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function fecharModal() {
    if (this.id === "account-confirm") fechamentos += 1;
    this.removeAttribute("open");
  };
});

afterEach(() => {
  for (const [metodo, descritor] of Object.entries(metodosOriginais)) {
    if (descritor) Object.defineProperty(HTMLDialogElement.prototype, metodo, descritor);
    else delete HTMLDialogElement.prototype[metodo];
  }
});

function confirmacaoAberta() {
  return $("#account-confirm").hasAttribute("open");
}

function voltarAAba() {
  fireEvent.focus(window);
}

function segurarProximaSessao(cliente, falha) {
  const getSession = cliente.auth.getSession;
  let liberar = () => {};
  let primeira = true;
  cliente.auth.getSession = async () => {
    if (primeira) {
      primeira = false;
      await new Promise((resolve) => {
        liberar = resolve;
      });
      if (falha) throw falha;
    }
    return getSession();
  };
  return () => executar(() => liberar());
}

function segurarRpc(cliente, nome) {
  const rpc = cliente.rpc;
  let liberar = () => {};
  cliente.rpc = async (chamada, args) => {
    if (chamada === nome) {
      await new Promise((resolve) => {
        liberar = resolve;
      });
    }
    return rpc(chamada, args);
  };
  return () => executar(() => liberar());
}

async function contaRecemVinculadaAoVoltarAAba() {
  const aberta = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfil, url: "/?conta" });
  await esperar();
  expect($("#success-state").hidden).toBe(false);
  aberta.perfilNoBanco.telegram_chat_id = "123";
  voltarAAba();
  await esperar();
  expect($("#success-state").hidden).toBe(true);
  expect($("#account-state").hidden).toBe(false);
  return aberta;
}

test("voltar à aba na ativação mostra a conta assim que o Telegram é vinculado", async () => {
  await contaRecemVinculadaAoVoltarAAba();
  expect($("#account-delivery-title").textContent).toBe("Entregas ativas");
});

test("voltar à aba durante a edição do perfil não descarta o que foi digitado", async () => {
  await contaRecemVinculadaAoVoltarAAba();
  clicar("#edit-profile");
  await esperar();
  alterarCampo("curso", "Direito");
  voltarAAba();
  await esperar();
  expect($("#signup-form").hidden).toBe(false);
  expect($("#signup-form").elements.curso.value).toBe("Direito");
  expect($("#account-state").hidden).toBe(true);
});

test("voltar à aba com a confirmação aberta não esconde o diálogo modal", async () => {
  await contaRecemVinculadaAoVoltarAAba();
  clicar("#delete-account");
  expect(confirmacaoAberta()).toBe(true);
  voltarAAba();
  await esperar();
  expect($("#account-confirm").hidden).toBe(false);
  expect(confirmacaoAberta()).toBe(true);
  expect(fechamentos).toBe(0);
  expect($("#account-confirm").dataset.acao).toBe("excluir");
});

test("voltar à aba mantém a pergunta do motivo da pausa", async () => {
  await contaRecemVinculadaAoVoltarAAba();
  clicar("#toggle-deliveries");
  await esperar();
  expect($("#pause-reason").hidden).toBe(false);
  voltarAAba();
  await esperar();
  expect($("#pause-reason").hidden).toBe(false);
});

test("consulta do vínculo que termina depois de a pessoa sair da ativação não mexe na tela", async () => {
  const { cliente, perfilNoBanco } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfil, url: "/?conta" });
  await esperar();
  const liberar = segurarProximaSessao(cliente);
  voltarAAba();
  await esperar();
  perfilNoBanco.telegram_chat_id = "123";
  clicar("#success-account");
  await esperar();
  clicar("#edit-profile");
  await esperar();
  alterarCampo("curso", "Direito");
  liberar();
  await esperar();
  expect($("#signup-form").hidden).toBe(false);
  expect($("#signup-form").elements.curso.value).toBe("Direito");
});

test("resposta da pausa que chega com a confirmação aberta fecha o diálogo em vez de escondê-lo", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  const liberar = segurarProximaSessao(cliente);
  clicar("#toggle-deliveries");
  await esperar();
  clicar("#delete-account");
  expect(confirmacaoAberta()).toBe(true);
  liberar();
  await esperar();
  expect(fechamentos).toBeGreaterThan(0);
  expect(confirmacaoAberta()).toBe(false);
  expect($("#account-confirm").hidden).toBe(true);
});

test("voltar no histórico para a conta com a confirmação aberta fecha o diálogo em vez de escondê-lo", async () => {
  abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  clicar("#delete-account");
  expect(confirmacaoAberta()).toBe(true);
  fireEvent.popState(window);
  await esperar();
  expect(fechamentos).toBeGreaterThan(0);
  expect(confirmacaoAberta()).toBe(false);
  expect($("#account-confirm").hidden).toBe(true);
});

test.each([
  ["excluir", "#delete-account"],
  ["desvincular", "#unlink-telegram"],
])("voltar no histórico para o site com a confirmação de %s aberta fecha a confirmação", async (acao, origem) => {
  abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  clicar(origem);
  expect($("#account-confirm").dataset.acao).toBe(acao);
  expect(confirmacaoAberta()).toBe(true);
  window.history.replaceState(null, "", "/");
  fireEvent.popState(window);
  await esperar();
  expect($("#landing-page").hidden).toBe(false);
  expect(fechamentos).toBeGreaterThan(0);
  expect(confirmacaoAberta()).toBe(false);
  expect($("#account-confirm").hidden).toBe(true);
  expect(document.querySelectorAll("dialog[open]")).toHaveLength(0);
});

test("resposta do desvincular que chega com a exclusão aberta fecha a confirmação", async () => {
  const { cliente, perfilNoBanco } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  const liberar = segurarRpc(cliente, "desvincular_meu_telegram");
  clicar("#unlink-telegram");
  clicar("#account-confirm-yes");
  await esperar();
  perfilNoBanco.telegram_chat_id = null;
  clicar("#delete-account");
  expect(confirmacaoAberta()).toBe(true);
  liberar();
  await esperar();
  expect($("#success-state").hidden).toBe(false);
  expect($("#account-state").hidden).toBe(true);
  expect(confirmacaoAberta()).toBe(false);
  expect($("#account-confirm").hidden).toBe(true);
});

test("resposta da exclusão que chega com o desvincular aberto fecha a confirmação", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  const liberar = segurarRpc(cliente, "excluir_minha_conta");
  clicar("#delete-account");
  clicar("#account-confirm-yes");
  await esperar();
  clicar("#unlink-telegram");
  expect(confirmacaoAberta()).toBe(true);
  liberar();
  await esperar();
  expect($("#success-title").textContent).toBe("As entregas pararam agora.");
  expect(confirmacaoAberta()).toBe(false);
  expect($("#account-confirm").hidden).toBe(true);
});

test("editar perfil que termina de carregar com a confirmação aberta fecha o diálogo", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  const liberar = segurarProximaSessao(cliente);
  clicar("#edit-profile");
  await esperar();
  clicar("#delete-account");
  expect(confirmacaoAberta()).toBe(true);
  liberar();
  await esperar();
  expect($("#signup-form").hidden).toBe(false);
  expect(confirmacaoAberta()).toBe(false);
  expect($("#account-confirm").hidden).toBe(true);
});

test("consulta do vínculo que falha depois da exclusão não troca o texto da exclusão", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfil, url: "/?conta" });
  await esperar();
  const liberar = segurarProximaSessao(cliente, new TypeError("Failed to fetch"));
  voltarAAba();
  await esperar();
  clicar("#success-account");
  await esperar();
  clicar("#delete-account");
  clicar("#account-confirm-yes");
  await esperar();
  expect($("#success-title").textContent).toBe("As entregas pararam agora.");
  liberar();
  await esperar();
  expect($("#success-copy").textContent).toMatch(/apagados definitivamente/);
});
