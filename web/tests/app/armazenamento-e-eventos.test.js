import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";
import {
  $,
  $$,
  abrirAplicacao,
  chamada,
  clicar,
  enviar,
  esperar,
  fecharAplicacao,
  perfil,
  preencher,
  usuario,
} from "./ambiente.js";

const PADRAO_DE_UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const pastaDoFonte = resolve(dirname(fileURLToPath(import.meta.url)), "../../src");

function sessoesDosEventos(calls) {
  return [
    ...new Set(
      calls.filter(([nome, tabela]) => nome === "insert" && tabela === "eventos_produto").map(([, , dados]) => dados.sessao_id),
    ),
  ];
}

async function cadastrar(calls) {
  await esperar();
  clicar(".js-open-signup");
  await esperar();
  enviar(preencher());
  await esperar();
  return {
    cadastro: chamada(calls, "signup")[1].options.data.cadastro_radar.sessao_id,
    eventos: sessoesDosEventos(calls),
  };
}

test("cadastro cria a conta com o armazenamento do navegador bloqueado", async () => {
  const { calls } = abrirAplicacao({ armazenamentoBloqueado: true });
  const { cadastro, eventos } = await cadastrar(calls);
  expect(cadastro).toMatch(PADRAO_DE_UUID_V4);
  expect(eventos.length).toBeGreaterThan(0);
  expect(eventos).toEqual([cadastro]);
  expect($("#auth-assistance").hidden).toBe(false);
});

test("com o armazenamento funcionando, a sessão de eventos é a mesma entre cargas e no cadastro", async () => {
  const chave = "radar-sessao-eventos";
  const primeira = abrirAplicacao();
  const resultadoDaPrimeira = await cadastrar(primeira.calls);
  const guardada = localStorage.getItem(chave);
  expect(guardada).toMatch(/^[0-9a-f-]{36}$/);
  expect(resultadoDaPrimeira.cadastro).toBe(guardada);
  expect(resultadoDaPrimeira.eventos).toEqual([guardada]);
  fecharAplicacao();

  const segunda = abrirAplicacao({ armazenado: { [chave]: guardada } });
  const resultadoDaSegunda = await cadastrar(segunda.calls);
  expect(resultadoDaSegunda.cadastro).toBe(guardada);
  expect(resultadoDaSegunda.eventos).toEqual([guardada]);
  expect(localStorage.getItem(chave)).toBe(guardada);
});

function eventosRegistradosNoFonte() {
  const nomes = new Set();
  for (const arquivo of readdirSync(pastaDoFonte, { recursive: true })) {
    if (!/\.jsx?$/.test(arquivo)) continue;
    const codigo = readFileSync(join(pastaDoFonte, arquivo), "utf8");
    for (const [, nome] of codigo.matchAll(/registrar\("([a-z_]+)"/g)) nomes.add(nome);
  }
  return nomes;
}

test("nenhum evento do site passa de 256 bytes de propriedades, mesmo com URL de 1.000 caracteres", async () => {
  const limite = 256;
  const urlLonga = (sufixo) => `/${"estágio-remoto-no-rio/".repeat(60)}`.slice(0, 1000 - sufixo.length) + sufixo;
  const bytesComoNoBanco = (propriedades) =>
    new TextEncoder().encode(JSON.stringify(propriedades)).length + 2 * Object.keys(propriedades).length;
  const eventosDo = (calls) =>
    calls.filter(([nome, tabela]) => nome === "insert" && tabela === "eventos_produto").map(([, , dados]) => dados);
  const vistos = [];

  expect(urlLonga("")).toHaveLength(1000);
  const visitante = abrirAplicacao({ url: urlLonga("") });
  await esperar();
  for (const chamadaDeCadastro of $$(".js-open-signup")) {
    clicar(chamadaDeCadastro);
    await esperar();
  }
  preencher();
  for (let passo = 0; passo < 3; passo += 1) clicar("#next-step");
  await esperar();
  vistos.push(...eventosDo(visitante.calls));
  fecharAplicacao();

  expect(urlLonga("?conta")).toHaveLength(1000);
  const dono = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfil, url: urlLonga("?conta") });
  await esperar();
  const telegram = $("#telegram-link");
  telegram.addEventListener("click", (evento) => evento.preventDefault());
  clicar(telegram);
  clicar("#success-account");
  await esperar();
  clicar("#edit-profile");
  await esperar();
  enviar("#signup-form");
  await esperar();
  vistos.push(...eventosDo(dono.calls));

  expect(new Set(vistos.map((evento) => evento.nome))).toEqual(eventosRegistradosNoFonte());
  for (const evento of vistos) {
    expect(bytesComoNoBanco(evento.propriedades), evento.nome).toBeLessThanOrEqual(limite);
  }
  const pagina = vistos.find((evento) => evento.nome === "landing_visualizada")?.propriedades.pagina;
  expect(String(pagina)).toMatch(/^\/est/);
});

test("voltar do link de confirmação com o armazenamento bloqueado mostra a ativação", async () => {
  abrirAplicacao({
    armazenamentoBloqueado: true,
    sessao: { user: usuario },
    perfilSalvo: perfil,
    url: "/#access_token=fake",
  });
  await esperar();
  expect($("#success-state").hidden).toBe(false);
  expect($("#telegram-link").hidden).toBe(false);
  expect($("#form-message").textContent).toBe("");
});

test("sair da conta com o armazenamento bloqueado volta ao site", async () => {
  const { calls } = abrirAplicacao({
    armazenamentoBloqueado: true,
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, telegram_chat_id: "123" },
    url: "/?conta",
  });
  await esperar();
  expect($("#account-page").hidden).toBe(false);
  clicar("#logout-account");
  await esperar();
  expect(calls.some(([nome]) => nome === "logout")).toBe(true);
  expect($("#account-page").hidden).toBe(true);
  expect($("#landing-page").hidden).toBe(false);
});
