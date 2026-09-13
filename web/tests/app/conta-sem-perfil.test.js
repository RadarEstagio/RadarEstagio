import { fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, expect, test } from "vitest";
import {
  $,
  abrirAplicacao,
  chamadas,
  clicar,
  enviar,
  esperar,
  executar,
  perfil,
  preencher,
  usuario,
  visivel,
} from "./ambiente.js";

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

function abrirContaSemPerfil() {
  return abrirAplicacao({ sessao: { user: usuario }, url: "/?conta" });
}

function nomesDasRpcs(calls) {
  return chamadas(calls, "rpc").map(([, nome]) => nome);
}

function segurarRpc(cliente, calls, nome, resposta) {
  let liberar = () => {};
  const rpc = cliente.rpc;
  cliente.rpc = async (chamada, args) => {
    if (chamada !== nome) return rpc(chamada, args);
    calls.push(["rpc", chamada, args]);
    await new Promise((resolve) => {
      liberar = resolve;
    });
    return resposta;
  };
  return () => executar(() => liberar());
}

test("conta confirmada sem perfil pode ser excluída pelo site", async () => {
  const { calls } = abrirContaSemPerfil();
  await esperar();
  expect($("#form-notice").textContent).toMatch(/Complete seu perfil/);
  const botao = $("#delete-account-without-profile");
  expect(visivel(botao)).toBe(true);
  clicar(botao);
  expect(visivel("#account-confirm")).toBe(true);
  expect($("#account-confirm-title").textContent).toBe("Excluir sua conta?");
  expect($("#account-confirm-warning-title").textContent).toBe("Sua conta será apagada agora");
  clicar("#account-confirm-no");
  expect($("#account-confirm").hidden).toBe(true);
  expect(document.activeElement.id).toBe("delete-account-without-profile");
  clicar(botao);
  clicar("#account-confirm-yes");
  await esperar();
  expect(nomesDasRpcs(calls)).toEqual(["apagar_minha_conta_sem_perfil"]);
  expect(chamadas(calls, "logout")).toHaveLength(1);
  expect(fechamentos).toBeGreaterThan(0);
  expect($("#account-confirm").hidden).toBe(true);
  expect($("#success-title").textContent).toBe("Sua conta foi apagada.");
  expect(visivel("#success-state")).toBe(true);
  expect($("#success-account").hidden).toBe(true);
  expect(visivel(botao)).toBe(false);
  expect($('[data-event-origin="cabecalho"]').textContent.trim()).toBe("Cadastrar meu perfil");
});

test("falha ao excluir a conta sem perfil avisa na tela e mantém a sessão", async () => {
  const { calls, cliente } = abrirContaSemPerfil();
  await esperar();
  cliente.rpc = async (nome, args) => {
    calls.push(["rpc", nome, args]);
    return { error: new TypeError("Failed to fetch") };
  };
  clicar("#delete-account-without-profile");
  clicar("#account-confirm-yes");
  await esperar();
  expect($("#form-message").textContent).toMatch(/conexão/);
  expect(visivel("#form-message")).toBe(true);
  expect(chamadas(calls, "logout")).toHaveLength(0);
  expect(visivel("#delete-account-without-profile")).toBe(true);
});

test.each([
  [Object.assign(new Error("conta com perfil usa excluir_minha_conta"), { code: "55000" }), /já tem um perfil salvo/],
  [Object.assign(new Error("sem sessão"), { code: "42501" }), /sessão expirou.*excluir/],
  [new TypeError("Failed to fetch"), /Não foi possível excluir a conta agora/],
])("falha ao excluir a conta sem perfil explica o motivo com mensagem da exclusão (%s)", async (erro, esperada) => {
  const { calls, cliente } = abrirContaSemPerfil();
  await esperar();
  cliente.rpc = async (nome, args) => {
    calls.push(["rpc", nome, args]);
    return { error: erro };
  };
  clicar("#delete-account-without-profile");
  clicar("#account-confirm-yes");
  await esperar();
  const mensagem = $("#form-message").textContent;
  expect(mensagem).toMatch(esperada);
  expect(mensagem).not.toMatch(/cadastro|salvar o perfil/);
  expect(visivel("#form-message")).toBe(true);
});

test("enviar o perfil trava a exclusão da conta sem perfil até a resposta", async () => {
  const { calls, cliente } = abrirContaSemPerfil();
  await esperar();
  const liberar = segurarRpc(cliente, calls, "concluir_meu_cadastro", { error: new TypeError("Failed to fetch") });
  enviar(preencher());
  await esperar();
  const botao = $("#delete-account-without-profile");
  expect(botao.disabled).toBe(true);
  clicar(botao);
  expect($("#account-confirm").hasAttribute("open")).toBe(false);
  liberar();
  await esperar();
  expect(botao.disabled).toBe(false);
  expect(nomesDasRpcs(calls)).toEqual(["concluir_meu_cadastro"]);
});

test("excluir a conta sem perfil fica ocupado e trava o envio do perfil", async () => {
  const { calls, cliente } = abrirContaSemPerfil();
  await esperar();
  const liberar = segurarRpc(cliente, calls, "apagar_minha_conta_sem_perfil", { data: null });
  const botao = $("#delete-account-without-profile");
  clicar(botao);
  clicar("#account-confirm-yes");
  await esperar();
  expect(botao.disabled).toBe(true);
  expect(botao.getAttribute("aria-busy")).toBe("true");
  expect($("#submit-profile").disabled).toBe(true);
  enviar(preencher());
  await esperar();
  liberar();
  await esperar();
  expect(nomesDasRpcs(calls)).toEqual(["apagar_minha_conta_sem_perfil"]);
  expect($("#success-title").textContent).toBe("Sua conta foi apagada.");
  expect(botao.getAttribute("aria-busy")).toBe("false");
});

test("conta com perfil não oferece a exclusão imediata", async () => {
  abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, telegram_chat_id: "123" },
    url: "/?conta#account-privacy-panel",
  });
  await esperar();
  expect(visivel("#delete-account")).toBe(true);
  expect(visivel("#delete-account-without-profile")).toBe(false);
});

test("voltar no histórico para o site com a exclusão sem perfil aberta fecha a confirmação", async () => {
  abrirContaSemPerfil();
  await esperar();
  clicar("#delete-account-without-profile");
  expect($("#account-confirm").dataset.acao).toBe("apagar-sem-perfil");
  expect($("#account-confirm").hasAttribute("open")).toBe(true);
  window.history.replaceState(null, "", "/");
  fireEvent.popState(window);
  await esperar();
  expect($("#landing-page").hidden).toBe(false);
  expect(fechamentos).toBeGreaterThan(0);
  expect($("#account-confirm").hasAttribute("open")).toBe(false);
  expect($("#account-confirm").hidden).toBe(true);
});
