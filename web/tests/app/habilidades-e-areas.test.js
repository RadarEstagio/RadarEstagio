import { expect, test } from "vitest";
import {
  $,
  $$,
  abrirAplicacao,
  alterarCampo,
  areasJson,
  chamada,
  clicar,
  digitar,
  enviar,
  esperar,
  eventos,
  executar,
  executarAteTerminar,
  passoAtivo,
  perfil,
  preencher,
  teclar,
  usuario,
} from "./ambiente.js";
import { act } from "@testing-library/react";

async function abrirCadastro() {
  await esperar();
  clicar(".js-open-signup");
  await esperar();
}

function avancar(vezes) {
  for (let passo = 0; passo < vezes; passo += 1) clicar("#next-step");
}

function valoresDasAreas(seletor = 'input[name="areas"]') {
  return $$(seletor).map((campo) => campo.value);
}

test("Enter adiciona habilidade sem avançar e Continuar ainda avança", async () => {
  abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: { ...perfil, telegram_chat_id: "123" }, url: "/?conta" });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  clicar("#next-step");
  digitar("#custom-skill", "Rust");
  teclar("#custom-skill", "Enter");
  expect($("#selected-skills").textContent).toContain("Rust");
  expect($("#custom-skill").value).toBe("");
  expect(passoAtivo()).toBe("3");
  clicar("#next-step");
  expect(passoAtivo()).toBe("4");
  await esperar();
});

test("habilidade digitada respeita o tamanho e a quantidade que o banco aceita", async () => {
  abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher(false);
  clicar("#next-step");
  const adicionar = (valor) => {
    digitar("#custom-skill", valor);
    teclar("#custom-skill", "Enter");
  };
  adicionar("x".repeat(150));
  expect(formulario.elements.habilidades.value).toHaveLength(100);
  for (let indice = 1; indice < 50; indice += 1) adicionar(`habilidade-${indice}`);
  expect(formulario.elements.habilidades.value.split(",")).toHaveLength(50);
  adicionar("passou-do-limite");
  expect(formulario.elements.habilidades.value.split(",")).toHaveLength(50);
  expect($("#erro-do-campo").textContent).toContain("50 habilidades");
  expect($("#custom-skill").getAttribute("aria-invalid")).toBe("true");
  await esperar();
});

test("atalho permite cadastrar com habilidades vazias e preserva a escolha ao voltar", async () => {
  const { calls } = abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher(false);
  avancar(2);
  expect(passoAtivo()).toBe("3");
  expect($("#continue-without-skills").hidden).toBe(false);
  expect($("#erro-do-campo").textContent).toBe("Escolha ou digite pelo menos uma habilidade.");
  clicar("#next-step");
  expect(passoAtivo()).toBe("3");
  clicar("#continue-without-skills");
  expect(passoAtivo()).toBe("4");
  expect(formulario.elements.habilidades.value).toBe("");
  clicar("#previous-step");
  expect(passoAtivo()).toBe("3");
  clicar("#next-step");
  expect(passoAtivo()).toBe("4");
  enviar(formulario);
  await esperar();
  expect(chamada(calls, "signup")[1].options.data.cadastro_radar.perfil.habilidades).toEqual([]);
  const evento = eventos(calls, "etapa_habilidades_concluida")[0];
  expect(JSON.stringify(evento?.[2])).not.toContain("semHabilidades");
  await esperar();
});

test("edição de perfil salvo sem habilidades libera a etapa e remover a última exige escolha nova", async () => {
  abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, habilidades: [], telegram_chat_id: "123" },
    url: "/?conta",
  });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  clicar("#next-step");
  expect(passoAtivo()).toBe("3");
  clicar("#next-step");
  expect(passoAtivo()).toBe("4");
  clicar("#previous-step");
  clicar('[data-skill="Python"]');
  clicar('[data-skill="Python"]');
  expect($("#continue-without-skills").hidden).toBe(false);
  clicar("#next-step");
  expect(passoAtivo()).toBe("3");
  clicar("#continue-without-skills");
  expect(passoAtivo()).toBe("4");
  await esperar();
});

test("as areas de interesse acompanham o curso digitado", async () => {
  abrirAplicacao();
  await abrirCadastro();
  preencher();
  alterarCampo("curso", "Direito");
  avancar(3);
  await esperar();
  expect($("#campo-areas").hidden).toBe(false);
  expect(valoresDasAreas()).toContain("direito_contencioso");
  expect(valoresDasAreas()).not.toContain("desenvolvimento_web");
});

test("curso de computacao continua vendo as areas de tecnologia", async () => {
  abrirAplicacao();
  await abrirCadastro();
  preencher();
  avancar(3);
  await esperar();
  expect(valoresDasAreas()).toContain("desenvolvimento_web");
  expect(valoresDasAreas()).not.toContain("direito_contencioso");
});

test("curso sem area conhecida esconde o campo de areas", async () => {
  abrirAplicacao();
  await abrirCadastro();
  preencher();
  alterarCampo("curso", "Curso Que Ninguem Tem");
  avancar(3);
  await esperar();
  expect($("#campo-areas").hidden).toBe(true);
  expect(valoresDasAreas()).toHaveLength(0);
});

test.each([
  ["Medicina Veterinária", null],
  ["Design de Interiores", null],
  ["Tecnologia em Gestão Financeira", "financeiro"],
  ["Gestão de Recursos Humanos", "recrutamento_e_selecao"],
  ["Bacharelado em Ciência da Computação", "desenvolvimento_web"],
])("áreas respeitam o nome completo de %s", async (curso, subarea) => {
  abrirAplicacao();
  await abrirCadastro();
  preencher();
  alterarCampo("curso", curso);
  avancar(3);
  await esperar();
  if (subarea === null) expect(valoresDasAreas()).toEqual([]);
  else expect(valoresDasAreas()).toContain(subarea);
});

test.each([
  ["Cursando Direito", "direito_contencioso", "desenvolvimento_web"],
  ["Estudante de Ciências Econômicas", "financeiro", "direito_contencioso"],
])("formacao e sinonimo em %s ainda montam as areas certas", async (curso, esperada, indevida) => {
  abrirAplicacao();
  await abrirCadastro();
  preencher();
  alterarCampo("curso", curso);
  avancar(3);
  await esperar();
  expect(valoresDasAreas()).toContain(esperada);
  expect(valoresDasAreas()).not.toContain(indevida);
});

test("catalogo indisponivel na edicao preserva as areas salvas em vez de apagar", async () => {
  const { calls, controlador } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, telegram_chat_id: "123", areas_de_interesse: ["desenvolvimento_web"] },
  });
  window.fetch = async () => {
    throw new Error("offline");
  };
  await esperar();
  executar(() => controlador.definirModo("login"));
  clicar("#edit-profile");
  await esperar();
  const formulario = $("#signup-form");
  digitar(formulario.elements.cidade, "Natal, RN");
  enviar(formulario);
  await esperar();
  const atualizacao = chamada(calls, "update");
  expect(atualizacao[2].cidade).toBe("Natal, RN");
  expect(atualizacao[2].areas_de_interesse).toEqual(["desenvolvimento_web"]);
});

test("trocar o curso na edicao descarta as areas do curso antigo no payload", async () => {
  const { calls, controlador } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, telegram_chat_id: "123", areas_de_interesse: ["desenvolvimento_web"] },
  });
  await esperar();
  executar(() => controlador.definirModo("login"));
  clicar("#edit-profile");
  await esperar();
  const formulario = $("#signup-form");
  digitar(formulario.elements.curso, "Direito");
  enviar(formulario);
  await esperar();
  const atualizacao = chamada(calls, "update");
  expect(atualizacao[2].curso).toBe("Direito");
  expect(atualizacao[2].areas_de_interesse).toEqual([]);
});

test("area marcada no cadastro vai para o payload na ordem do catalogo", async () => {
  const { calls } = abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher();
  avancar(2);
  await esperar();
  const [primeira, segunda] = $$('input[name="areas"]');
  clicar(segunda);
  clicar(primeira);
  clicar("#next-step");
  enviar(formulario);
  await esperar();
  const areas = chamada(calls, "signup")[1].options.data.cadastro_radar.perfil.areas_de_interesse;
  expect(areas).toEqual([primeira.value, segunda.value]);
});

test.each([
  ["Direito", "Redação", "Python"],
  ["Computação", "Python", "Redação"],
  ["Curso Que Ninguem Tem", null, "Python"],
])("habilidades sugeridas acompanham o curso %s", async (curso, esperada, indevida) => {
  abrirAplicacao();
  await abrirCadastro();
  preencher(Boolean(esperada));
  alterarCampo("curso", curso);
  avancar(2);
  await esperar();
  const sugeridas = $$("#skill-picker [data-skill]").map((botao) => botao.dataset.skill);
  if (esperada) expect(sugeridas).toContain(esperada);
  else expect(sugeridas).toEqual([]);
  expect(sugeridas).not.toContain(indevida);
  if (!esperada) expect($("#continue-without-skills").hidden).toBe(false);
});

test("falha do catálogo limpa sugestões sem apagar habilidade escolhida", async () => {
  const { controlador } = abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher(false);
  window.fetch = async () => {
    throw new Error("offline");
  };
  clicar("#next-step");
  await esperar();
  digitar("#custom-skill", "Python");
  teclar("#custom-skill", "Enter");
  await executarAteTerminar(() => controlador.montarHabilidadesDoCurso());
  expect($$("#skill-picker [data-skill]")).toEqual([]);
  expect(formulario.elements.habilidades.value).toBe("Python");
  expect($("#skills-catalog-notice").hidden).toBe(false);
  expect($("#continue-without-skills").hidden).toBe(true);
});

test("resposta assíncrona de curso anterior não substitui o curso atual", async () => {
  const { controlador } = abrirAplicacao();
  await abrirCadastro();
  preencher(false);
  alterarCampo("curso", "Direito");
  const respostas = [];
  window.fetch = () => new Promise((resolve) => respostas.push(resolve));
  let primeira;
  let segunda;
  executar(() => {
    primeira = controlador.montarHabilidadesDoCurso();
  });
  alterarCampo("curso", "Computação");
  executar(() => {
    segunda = controlador.montarHabilidadesDoCurso();
  });
  await act(async () => {
    respostas[1]({ ok: true, json: async () => areasJson });
    await segunda;
  });
  await act(async () => {
    respostas[0]({ ok: true, json: async () => areasJson });
    await primeira;
  });
  const sugeridas = $$("#skill-picker [data-skill]").map((botao) => botao.dataset.skill);
  expect(sugeridas).toContain("Python");
  expect(sugeridas).not.toContain("Redação");
});

test("sair da conta nao deixa as areas de interesse da pessoa anterior no proximo cadastro", async () => {
  const { controlador } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, telegram_chat_id: "123", areas_de_interesse: ["dados_ia"] },
  });
  await esperar();
  executar(() => controlador.definirModo("login"));
  clicar("#edit-profile");
  await esperar();
  clicar("#logout-account");
  await esperar();
  executar(() => controlador.definirModo("signup"));
  clicar(".js-open-signup");
  await esperar();
  preencher();
  avancar(3);
  await esperar();
  expect(valoresDasAreas('input[name="areas"]:checked')).toEqual([]);
});

test("curso escrito como tecnologia da informacao abre as areas de computacao", async () => {
  const { controlador } = abrirAplicacao();
  await esperar();
  executar(() => controlador.definirModo("signup"));
  clicar(".js-open-signup");
  await esperar();
  preencher();
  alterarCampo("curso", "Bacharelado em Tecnologia da Informação");
  avancar(3);
  await esperar();
  expect($("#campo-areas").hidden).toBe(false);
  expect(valoresDasAreas().length).toBeGreaterThan(0);
});
