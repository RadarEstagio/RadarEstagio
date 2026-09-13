import { fireEvent } from "@testing-library/react";
import { expect, test } from "vitest";
import {
  $,
  $$,
  abrirAplicacao,
  chamadas,
  clicar,
  dialogoAberto,
  eventos,
  esperar,
  perfil,
  usuario,
} from "./ambiente.js";

test("demonstração do Telegram anima a chegada de duas vagas", async () => {
  abrirAplicacao();
  await esperar();
  const demo = $("[data-chat-demo]");
  expect(demo.classList.contains("is-waiting")).toBe(true);
  expect(demo.classList.contains("is-playing")).toBe(false);
  Object.defineProperty(window, "scrollY", { value: 89, configurable: true });
  fireEvent.scroll(window);
  expect(demo.classList.contains("is-waiting")).toBe(true);
  Object.defineProperty(window, "scrollY", { value: 90, configurable: true });
  fireEvent.scroll(window);
  expect(demo.classList.contains("is-waiting")).toBe(false);
  expect(demo.classList.contains("is-playing")).toBe(true);
  expect(demo.querySelectorAll(".chat-vacancy")).toHaveLength(2);
  expect(demo.querySelector(".chat-vacancy-second .chat-vacancy-title").textContent).toBe(
    "2. Estágio em marketing e conteúdo",
  );
  expect(demo.querySelector(".chat-typing")).toBeTruthy();
  expect(demo.querySelector(".chat-feedback")).toBeTruthy();
  expect(demo.querySelector(".chat-composer-field").textContent.trim()).toBe("Mensagem");
  expect(demo.querySelectorAll(".chat-composer-icon")).toHaveLength(2);
});

test("tema fica direto no cabeçalho, começa claro e guarda a escolha", async () => {
  abrirAplicacao();
  const raiz = document.documentElement;
  const botao = $("#theme-toggle");
  expect($("#header-settings")).toBeNull();
  expect(botao.matches(".header-utilities > button")).toBe(true);
  expect(botao.getAttribute("aria-label")).toBe("Modo escuro");
  expect(raiz.dataset.tema).toBe("claro");
  expect(botao.getAttribute("aria-pressed")).toBe("false");
  clicar(botao);
  expect(raiz.dataset.tema).toBe("escuro");
  expect(botao.getAttribute("aria-pressed")).toBe("true");
  expect(localStorage.getItem("radar-tema")).toBe("escuro");
  clicar(botao);
  expect(raiz.dataset.tema).toBe("claro");
  expect(botao.getAttribute("aria-pressed")).toBe("false");
  expect(localStorage.getItem("radar-tema")).toBe("claro");
  await esperar();
});

test("tema e login são controles separados com ações independentes", async () => {
  abrirAplicacao();
  await esperar();
  const tema = $("#theme-toggle");
  const entrar = $(".header-login");
  expect(tema.nextElementSibling).toBe(entrar);
  clicar(tema);
  expect(document.documentElement.dataset.tema).toBe("escuro");
  expect(dialogoAberto()).toBe(false);
  clicar(entrar);
  await esperar();
  expect(document.documentElement.dataset.tema).toBe("escuro");
  expect(dialogoAberto()).toBe(true);
  expect($("#conta-titulo").textContent).toBe("Entre na sua conta");
});

test("tema escuro salvo é aplicado no head, antes da aplicação carregar", async () => {
  const { temaAntesDoApp } = abrirAplicacao({ temaSalvo: "escuro" });
  const scriptsDoHead = $$("head script:not([src])");
  expect(scriptsDoHead.some((script) => script.textContent.includes("radar-tema"))).toBe(true);
  expect(temaAntesDoApp).toBe("escuro");
  expect(document.documentElement.dataset.tema).toBe("escuro");
  expect($("#theme-toggle").getAttribute("aria-pressed")).toBe("true");
  await esperar();
});

test("tema alterna sem erro quando o navegador bloqueia o armazenamento", async () => {
  abrirAplicacao({ armazenamentoBloqueado: true });
  expect(document.documentElement.dataset.tema).toBe("claro");
  clicar("#theme-toggle");
  expect(document.documentElement.dataset.tema).toBe("escuro");
  await esperar();
});

test("sessão aberta troca a chamada da landing por minha conta", async () => {
  const { calls } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfil });
  await esperar();
  const cabecalho = $('[data-event-origin="cabecalho"]');
  expect($("#landing-page").hidden).toBe(false);
  expect(cabecalho.textContent.trim()).toBe("Minha conta");
  expect($('[data-event-origin="hero"]').textContent.trim()).toBe("Minha conta →");
  clicar(cabecalho);
  await esperar();
  expect(eventos(calls, "cta_cadastro_aberto")).toHaveLength(0);
  expect($("#account-page").hidden).toBe(false);
  clicar("#logout-account");
  await esperar();
  expect(cabecalho.textContent.trim()).toBe("Cadastrar meu perfil");
  expect(chamadas(calls, "logout")).toHaveLength(1);
});

test("quem já entrou vai para a conta sem piscar o modal", async () => {
  abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: { ...perfil, telegram_chat_id: "123" } });
  await esperar();
  clicar('[data-event-origin="cabecalho"]');
  expect(dialogoAberto()).toBe(false);
  await esperar();
  expect(dialogoAberto()).toBe(false);
  expect($("#account-page").hidden).toBe(false);
});

test("visita à landing é contada uma vez por sessão do navegador", async () => {
  const { calls } = abrirAplicacao();
  await esperar();
  expect(eventos(calls, "landing_visualizada")).toHaveLength(1);
  expect(sessionStorage.getItem("radar-landing-vista")).toBe("1");
});
