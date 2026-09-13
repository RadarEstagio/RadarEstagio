import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";
import {
  $,
  abrirAplicacao,
  alterarCampo,
  areasJson,
  chamada,
  chamadas,
  clicar,
  digitar,
  enviar,
  esperar,
  habilidadesNaTela,
  passoAtivo,
  preencher,
  teclar,
} from "./ambiente.js";

const raizDoRepositorio = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const lerDoRepositorio = (caminho) => readFileSync(resolve(raizDoRepositorio, caminho), "utf8");

async function abrirEtapaDeHabilidades() {
  await esperar();
  clicar(".js-open-signup");
  await esperar();
  preencher(false);
  clicar("#next-step");
  await esperar();
}

function adicionarHabilidade(valor) {
  digitar("#custom-skill", valor);
  teclar("#custom-skill", "Enter");
}

async function habilidadesEnviadas(calls) {
  clicar("#next-step");
  clicar("#next-step");
  enviar("#signup-form");
  await esperar();
  return chamada(calls, "signup")[1].options.data.cadastro_radar.perfil.habilidades;
}

test("corte de 100 caracteres não parte emoji nem deixa espaço que o envio apagaria", async () => {
  const { calls } = abrirAplicacao();
  await abrirEtapaDeHabilidades();
  adicionarHabilidade(`${"c".repeat(99)}😀`);
  adicionarHabilidade(`${"a".repeat(99)} ${"b".repeat(20)}`);
  const naTela = habilidadesNaTela();
  expect(naTela).toEqual([`${"c".repeat(99)}😀`, "a".repeat(99)]);
  const enviadas = await habilidadesEnviadas(calls);
  expect(enviadas).toEqual(naTela);
  for (const habilidade of enviadas) {
    expect(/[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/.test(habilidade)).toBe(false);
    expect(Array.from(habilidade).length).toBeLessThanOrEqual(100);
  }
});

async function abrirEtapaCom50Habilidades() {
  await abrirEtapaDeHabilidades();
  for (let indice = 0; indice < 50; indice += 1) adicionarHabilidade(`h${indice}`);
}

test("com 50 habilidades, a sugerida não entra e o aviso aparece na etapa", async () => {
  abrirAplicacao();
  await abrirEtapaCom50Habilidades();
  const sugerida = $("#skill-picker [data-skill]");
  clicar(sugerida);
  expect(habilidadesNaTela()).toHaveLength(50);
  expect(sugerida.getAttribute("aria-pressed")).toBe("false");
  expect($("#erro-do-campo").textContent).toMatch(/no máximo 50 habilidades/);
});

test("a 51ª digitada seguida de Continuar fica na etapa com o aviso, sem sumir", async () => {
  abrirAplicacao();
  await abrirEtapaCom50Habilidades();
  digitar("#custom-skill", "Figma");
  clicar("#next-step");
  await esperar();
  expect(passoAtivo()).toBe("3");
  expect($("#custom-skill").value).toBe("Figma");
  expect($("#erro-do-campo").textContent).toMatch(/no máximo 50 habilidades/);
});

test("curso com menos de 2 caracteres fica na etapa com aviso e não chega ao banco", async () => {
  const { calls } = abrirAplicacao();
  await esperar();
  clicar(".js-open-signup");
  await esperar();
  const formulario = preencher();
  alterarCampo("curso", " A ");
  clicar("#next-step");
  await esperar();
  expect(passoAtivo()).toBe("2");
  expect($("#erro-do-campo").textContent).toMatch(/pelo menos 2 caracteres/);
  enviar(formulario);
  await esperar();
  expect(chamadas(calls, "signup")).toHaveLength(0);
  expect(passoAtivo()).toBe("2");
});

test("habilidade digitada com vírgula é uma só na tela e no envio", async () => {
  const { calls } = abrirAplicacao();
  await abrirEtapaDeHabilidades();
  adicionarHabilidade("Pacote Office (Word, Excel)");
  adicionarHabilidade("Python, SQL");
  expect(habilidadesNaTela()).toEqual(["Pacote Office (Word, Excel)", "Python, SQL"]);
  expect(await habilidadesEnviadas(calls)).toEqual(["Pacote Office (Word, Excel)", "Python, SQL"]);
});

test("cinquenta habilidades com vírgula cabem no envio e a 51ª é recusada na tela", async () => {
  const { calls } = abrirAplicacao();
  await abrirEtapaDeHabilidades();
  for (let indice = 0; indice < 50; indice += 1) adicionarHabilidade(`A${indice}, B${indice}`);
  adicionarHabilidade("A50, B50");
  expect(habilidadesNaTela()).toHaveLength(50);
  expect($("#erro-do-campo").textContent).toMatch(/no máximo 50 habilidades/);
  digitar("#custom-skill", "");
  const naTela = habilidadesNaTela();
  expect(await habilidadesEnviadas(calls)).toEqual(naTela);
});

test("campos do cadastro limitam a digitação aos tetos que o banco aceita", async () => {
  const tetos = lerDoRepositorio("supabase/migrations/0025_tamanho_dos_textos_do_perfil.sql");
  const listaDeHabilidades = lerDoRepositorio("supabase/migrations/0018_habilidades_vazias.sql");
  const regrasDoPerfil = lerDoRepositorio("web/src/domain/perfil.js");
  const numero = (texto, padrao) => {
    const achado = texto.match(padrao);
    expect(achado, `${padrao} não encontrado`).toBeTruthy();
    return Number(achado[1]);
  };
  const constanteDoSite = (nome) => numero(regrasDoPerfil, new RegExp(`const ${nome} = (\\d+);`));
  const maisSubareasDeUmCurso = Math.max(...areasJson.areas.map((area) => area.subareas.length));

  abrirAplicacao();
  await esperar();
  const formulario = $("#signup-form");
  const noSite = {
    curso: formulario.elements.curso.maxLength,
    cidade: formulario.elements.cidade.maxLength,
    habilidade: $("#custom-skill").maxLength,
  };
  const noBanco = {
    curso: [
      numero(tetos, /char_length\(curso\) <= (\d+)/),
      numero(tetos, /btrim\(perfil->>'curso'\)\) not between 2 and (\d+)/),
      numero(tetos, /length\(perfil->>'curso'\) > (\d+)/),
    ],
    cidade: [
      numero(tetos, /char_length\(cidade\) <= (\d+)/),
      numero(tetos, /btrim\(perfil->>'cidade'\)\) not between 2 and (\d+)/),
      numero(tetos, /length\(perfil->>'cidade'\) > (\d+)/),
    ],
    habilidade: [
      numero(tetos, /todos_os_textos_cabem\(habilidades, (\d+)\)/),
      numero(tetos, /btrim\(item #>> '\{\}'\)\) not between 1 and (\d+)/),
      numero(tetos, /length\(item #>> '\{\}'\) > (\d+)/),
      constanteDoSite("TAMANHO_MAXIMO_DA_HABILIDADE"),
    ],
  };
  for (const campo of Object.keys(noBanco)) {
    for (const valor of noBanco[campo]) expect(valor, campo).toBe(noSite[campo]);
  }
  expect(numero(tetos, /btrim\(perfil->>'curso'\)\) not between (\d+) and/)).toBe(formulario.elements.curso.minLength);
  const maximoDeHabilidades = constanteDoSite("MAXIMO_DE_HABILIDADES");
  const listaNoCadastro = numero(tetos, /jsonb_array_length\(perfil->lista\) > (\d+)/);
  expect(listaNoCadastro).toBe(maximoDeHabilidades);
  expect(numero(listaDeHabilidades, /cardinality\(valor\) between 0 and (\d+)/)).toBe(maximoDeHabilidades);
  expect(numero(tetos, /cardinality\(areas_de_interesse\) <= (\d+)/)).toBeGreaterThanOrEqual(maisSubareasDeUmCurso);
  expect(listaNoCadastro).toBeGreaterThanOrEqual(maisSubareasDeUmCurso);
});
