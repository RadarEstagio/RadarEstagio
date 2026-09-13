import { expect, test } from "vitest";
import {
  $,
  $$,
  abrirAplicacao,
  alterarCampo,
  chamada,
  chamadas,
  clicar,
  dialogoAberto,
  digitar,
  enviar,
  esperar,
  executar,
  focar,
  passoAtivo,
  perfil,
  preencher,
  teclar,
  usuario,
} from "./ambiente.js";

async function abrirPreferencias() {
  await esperar();
  clicar(".js-open-signup");
  await esperar();
  const formulario = preencher();
  clicar("#next-step");
  clicar("#next-step");
  focar(formulario.elements.cidade);
  await esperar();
  return formulario;
}

async function digitarCidade(texto) {
  digitar("#cidade", texto);
  await esperar();
  return $$("#lista-de-cidades [data-cidade]").map((opcao) => opcao.dataset.cidade);
}

test("cidade sugere municípios reais conforme a pessoa digita, sem exigir acento", async () => {
  abrirAplicacao();
  await abrirPreferencias();
  const rio = await digitarCidade("rio");
  expect(rio[0]).toBe("Rio de Janeiro, RJ");
  expect(rio.length).toBeGreaterThan(1);
  expect(rio.length).toBeLessThanOrEqual(8);
  expect(rio.every((cidade) => cidade.startsWith("Rio"))).toBe(true);
  expect($("#cidade").getAttribute("aria-expanded")).toBe("true");
  expect((await digitarCidade("niteroi"))[0]).toBe("Niterói, RJ");
  expect((await digitarCidade("sao paulo"))[0]).toBe("São Paulo, SP");
  expect(await digitarCidade("cidade que nao existe")).toEqual([]);
  expect($("#lista-de-cidades").textContent).toBe("Nenhuma cidade encontrada. Confira a grafia.");
});

test("cidade com apóstrofo é achada com apóstrofo curvo ou acento agudo", async () => {
  abrirAplicacao();
  const formulario = await abrirPreferencias();
  for (const digitado of [
    "santa barbara d’oeste",
    "santa barbara d‘oeste",
    "santa barbara dʼoeste",
    "santa barbara d´oeste",
  ]) {
    expect((await digitarCidade(digitado))[0]).toBe("Santa Bárbara d'Oeste, SP");
  }
  alterarCampo("cidade", "Sant’Ana do Livramento");
  clicar("#next-step");
  expect(formulario.elements.cidade.value).toBe("Sant'Ana do Livramento, RS");
});

test("clicar numa sugestão preenche a cidade e fecha a lista", async () => {
  abrirAplicacao();
  const formulario = await abrirPreferencias();
  await digitarCidade("curit");
  clicar('#lista-de-cidades [data-cidade="Curitiba, PR"]');
  expect(formulario.elements.cidade.value).toBe("Curitiba, PR");
  expect($("#lista-de-cidades").hidden).toBe(true);
  expect(formulario.elements.cidade.getAttribute("aria-expanded")).toBe("false");
});

test("setinha abre as maiores cidades com o campo vazio e fecha no segundo clique", async () => {
  abrirAplicacao();
  await abrirPreferencias();
  alterarCampo("cidade", "");
  const setinha = $("#mostrar-cidades");
  clicar(setinha);
  await esperar();
  const opcoes = $$("#lista-de-cidades [data-cidade]");
  expect(opcoes.slice(0, 3).map((opcao) => opcao.dataset.cidade)).toEqual([
    "São Paulo, SP",
    "Rio de Janeiro, RJ",
    "Brasília, DF",
  ]);
  expect(setinha.getAttribute("aria-expanded")).toBe("true");
  clicar(setinha);
  expect($("#lista-de-cidades").hidden).toBe(true);
  expect(setinha.getAttribute("aria-expanded")).toBe("false");
});

test("setas escolhem a sugestão e Enter confirma sem avançar o passo", async () => {
  abrirAplicacao();
  const formulario = await abrirPreferencias();
  await digitarCidade("rio");
  teclar("#cidade", "ArrowDown");
  teclar("#cidade", "ArrowDown");
  teclar("#cidade", "ArrowUp");
  const destacada = $('#lista-de-cidades [aria-selected="true"]');
  expect(destacada.dataset.cidade).toBe("Rio de Janeiro, RJ");
  expect(formulario.elements.cidade.getAttribute("aria-activedescendant")).toBe(destacada.id);
  teclar("#cidade", "Enter");
  expect(formulario.elements.cidade.value).toBe("Rio de Janeiro, RJ");
  expect(passoAtivo()).toBe("4");
  await digitarCidade("rio");
  teclar("#cidade", "Escape");
  expect($("#lista-de-cidades").hidden).toBe(true);
  expect(dialogoAberto()).toBe(true);
});

test("cidade fora da lista não avança e explica o que fazer", async () => {
  abrirAplicacao();
  const formulario = await abrirPreferencias();
  alterarCampo("cidade", "Cidade Inventada");
  clicar("#next-step");
  expect($("#erro-do-campo").textContent).toBe("Escolha sua cidade na lista, como Rio de Janeiro, RJ.");
  expect(formulario.elements.cidade.getAttribute("aria-invalid")).toBe("true");
  expect(passoAtivo()).toBe("4");
  alterarCampo("cidade", "Bom Jesus");
  clicar("#next-step");
  expect($("#erro-do-campo").textContent).toBe(
    "Existe mais de uma cidade com esse nome. Escolha a do seu estado na lista.",
  );
});

test("cidade escrita sem acento ou sem estado é salva no formato da lista", async () => {
  const { calls } = abrirAplicacao();
  const formulario = await abrirPreferencias();
  alterarCampo("cidade", "niteroi");
  clicar("#next-step");
  expect(formulario.elements.cidade.value).toBe("Niterói, RJ");
  enviar(formulario);
  await esperar();
  expect(chamada(calls, "signup")[1].options.data.cadastro_radar.perfil.cidade).toBe("Niterói, RJ");
});

test("envio direto recusa cidade fora da lista mesmo sem a lista carregada antes", async () => {
  const { calls } = abrirAplicacao();
  await esperar();
  clicar(".js-open-signup");
  await esperar();
  const formulario = preencher();
  alterarCampo("cidade", "Cidade Inventada");
  enviar(formulario);
  await esperar();
  expect(chamadas(calls, "signup")).toHaveLength(0);
  expect($("#erro-do-campo").textContent).toBe("Escolha sua cidade na lista, como Rio de Janeiro, RJ.");
  expect(passoAtivo()).toBe("4");
});

test("lista de cidades fora do ar avisa e não bloqueia o cadastro", async () => {
  const { calls } = abrirAplicacao();
  const areas = await window.fetch("assets/areas.json");
  window.fetch = async (caminho) => (String(caminho).includes("areas.json") ? areas : { ok: false, json: async () => null });
  const formulario = await abrirPreferencias();
  expect($("#cities-catalog-notice").hidden).toBe(false);
  alterarCampo("cidade", "Recife, PE");
  enviar(formulario);
  await esperar();
  expect(chamada(calls, "signup")[1].options.data.cadastro_radar.perfil.cidade).toBe("Recife, PE");
});

test("perfil antigo sem estado na cidade é corrigido ao salvar a edição", async () => {
  const { calls, controlador } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, cidade: "Rio de Janeiro", telegram_chat_id: "123" },
  });
  await esperar();
  executar(() => controlador.definirModo("login"));
  clicar("#edit-profile");
  await esperar();
  enviar("#signup-form");
  await esperar();
  expect(chamada(calls, "update")[2].cidade).toBe("Rio de Janeiro, RJ");
});
