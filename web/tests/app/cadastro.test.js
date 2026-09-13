import { expect, test } from "vitest";
import {
  $,
  abrirAplicacao,
  chamada,
  chamadas,
  clicar,
  digitar,
  enviar,
  esperar,
  eventos,
  executar,
  marcar,
  alterarCampo,
  passoAtivo,
  perfil,
  preencher,
  progresso,
  usuario,
} from "./ambiente.js";

async function abrirCadastro() {
  await esperar();
  clicar(".js-open-signup");
  await esperar();
}

function avancar(vezes) {
  for (let passo = 0; passo < vezes; passo += 1) clicar("#next-step");
}

test("cadastro exige aceite e envia perfil e sessão sem guardar senha localmente", async () => {
  const { calls } = abrirAplicacao();
  const formulario = preencher();
  marcar(formulario.elements.aceitou_termos, false);
  enviar(formulario);
  await esperar();
  expect(chamadas(calls, "signup")).toHaveLength(0);
  expect(eventos(calls, "etapa_preferencias_concluida")).toHaveLength(0);
  marcar(formulario.elements.aceitou_termos, true);
  enviar(formulario);
  await esperar();
  const cadastro = chamada(calls, "signup")[1].options.data.cadastro_radar;
  expect(cadastro.perfil.cidade).toBe("Recife, PE");
  expect(cadastro.aceita_emails).toBe(false);
  expect(cadastro.aceitou_termos).toBe(true);
  expect(cadastro.versao_dos_termos).toBe("2026-09-05");
  expect(cadastro.sessao_id).toMatch(/^[0-9a-f-]{36}$/);
  expect(chamada(calls, "signup")[1].password).toBe("uma-senha-forte");
  expect(JSON.stringify(cadastro)).not.toContain("uma-senha-forte");
  expect(localStorage.getItem("radar-perfil-pendente")).toBeNull();
  expect(JSON.stringify({ ...localStorage })).not.toContain("uma-senha-forte");
  expect($("#assistance-submit").disabled).toBe(true);
  expect(eventos(calls, "etapa_preferencias_concluida")).toHaveLength(0);
  expect(eventos(calls, "conta_criada")).toHaveLength(0);
});

test("cadastro começa pelo perfil e só no final pede a conta", async () => {
  const { calls } = abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher();
  expect(passoAtivo()).toBe("2");
  expect($("#progress-label").textContent).toBe("Etapa 1 de 4");
  expect(progresso()).toEqual(["0%", "0", "0%"]);
  expect($("#previous-step").hidden).toBe(true);
  expect($("#submit-profile").hidden).toBe(true);
  clicar("#next-step");
  expect(passoAtivo()).toBe("3");
  expect($("#progress-label").textContent).toBe("Etapa 2 de 4");
  expect(progresso()).toEqual(["25%", "25", "25%"]);
  clicar("#next-step");
  expect(passoAtivo()).toBe("4");
  expect($("#progress-label").textContent).toBe("Etapa 3 de 4");
  expect(progresso()).toEqual(["50%", "50", "50%"]);
  clicar("#next-step");
  expect(passoAtivo()).toBe("1");
  expect($("#progress-label").textContent).toBe("Etapa 4 de 4");
  expect(progresso()).toEqual(["75%", "75", "75%"]);
  expect(chamadas(calls, "signup")).toHaveLength(0);
  expect(formulario.elements.senha.value).toBe("uma-senha-forte");
  await esperar();
});

test("botão de cadastrar continua abrindo na triagem", async () => {
  const { calls } = abrirAplicacao();
  await abrirCadastro();
  expect(passoAtivo()).toBe("2");
  expect($("#submit-label").textContent).toBe("Criar conta e continuar");
  expect($("#conta-titulo").textContent).toBe("Comece pela sua conta");
  expect(eventos(calls, "cta_cadastro_aberto")[0][2].propriedades).toEqual({ origem: "cabecalho" });
});

test("alternar para login e voltar preserva o rascunho do perfil", async () => {
  abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher();
  avancar(3);
  expect(passoAtivo()).toBe("1");
  clicar("#toggle-auth-mode");
  expect(passoAtivo()).toBe("1");
  clicar("#toggle-auth-mode");
  expect(formulario.elements.curso.value).toBe("Computação");
  expect(formulario.elements.habilidades.value).toBe("Python");
  expect(formulario.elements.cidade.value).toBe("Recife, PE");
  expect($("#progress-label").textContent).toBe("Etapa 4 de 4");
  await esperar();
});

test("envio duplicado durante a autenticação gera uma única tentativa", async () => {
  const { calls, cliente } = abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher();
  avancar(3);
  let liberarCadastro = () => {};
  const cadastroLiberado = new Promise((resolve) => {
    liberarCadastro = resolve;
  });
  cliente.auth.signUp = async (args) => {
    calls.push(["signup", args]);
    await cadastroLiberado;
    return { data: { session: null } };
  };
  enviar(formulario);
  enviar(formulario);
  await esperar();
  expect(chamadas(calls, "signup")).toHaveLength(1);
  expect($("#submit-profile").disabled).toBe(true);
  liberarCadastro();
  await esperar();
});

test("entrar pede só a conta e edição do perfil pula esse passo", async () => {
  const { controlador } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: { ...perfil, telegram_chat_id: "123" } });
  await esperar();
  executar(() => controlador.definirModo("login"));
  expect(passoAtivo()).toBe("1");
  expect($(".progress-wrap").hidden).toBe(true);
  expect($("#next-step").hidden).toBe(true);
  expect($("#submit-profile").hidden).toBe(false);
  clicar("#edit-profile");
  await esperar();
  expect(passoAtivo()).toBe("2");
  expect($("#progress-label").textContent).toBe("Etapa 1 de 3");
  expect($("#progress-percent").textContent).toBe("0%");
  expect($("#credenciais").hidden).toBe(true);
});

test("edição após login mostra preferências e salva sem pedir novo aceite", async () => {
  const { calls, controlador } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, telegram_chat_id: "123" },
  });
  await esperar();
  executar(() => controlador.definirModo("login"));
  clicar("#edit-profile");
  await esperar();
  const formulario = $("#signup-form");
  digitar(formulario.elements.cidade, "Natal, RN");
  expect(formulario.elements.cidade.closest(".field").hidden).toBe(false);
  expect(formulario.elements.aceitou_termos.required).toBe(false);
  enviar(formulario);
  await esperar();
  const atualizacao = chamada(calls, "update");
  expect(atualizacao[1]).toBe("perfis");
  expect(atualizacao[2].cidade).toBe("Natal, RN");
  expect(atualizacao[2].versao_dos_termos).toBeUndefined();
  expect(chamadas(calls, "signup")).toHaveLength(0);
});

test("preferências são registradas ao avançar, antes de criar conta", async () => {
  const { calls } = abrirAplicacao();
  clicar(".js-open-signup");
  await esperar();
  const formulario = preencher();
  avancar(2);
  await esperar();
  alterarCampo("cidade", "");
  clicar("#next-step");
  await esperar();
  expect(eventos(calls, "etapa_preferencias_concluida")).toHaveLength(0);
  alterarCampo("cidade", "Recife, PE");
  marcar(formulario.elements.aceitou_termos, false);
  clicar("#next-step");
  await esperar();
  expect(eventos(calls, "etapa_preferencias_concluida")).toHaveLength(1);
  expect(chamadas(calls, "signup")).toHaveLength(0);
  marcar(formulario.elements.aceitou_termos, true);
  enviar(formulario);
  await esperar();
  expect(eventos(calls, "etapa_preferencias_concluida")).toHaveLength(1);
  expect(eventos(calls, "etapa_perfil_concluida")).toHaveLength(1);
  expect(eventos(calls, "etapa_habilidades_concluida")[0][2].propriedades).toEqual({ quantidade: 1 });
});

test("login não emite conclusão de preferências e edição emite ao salvar", async () => {
  const edicao = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: { ...perfil, telegram_chat_id: "123" },
    url: "/?conta",
  });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  avancar(2);
  enviar("#signup-form");
  await esperar();
  expect(eventos(edicao.calls, "etapa_preferencias_concluida")).toHaveLength(1);

  const login = abrirAplicacao({ perfilSalvo: perfil });
  preencher();
  clicar("#toggle-auth-mode");
  enviar("#signup-form");
  await esperar();
  expect(chamadas(login.calls, "login")).toHaveLength(1);
  expect(eventos(login.calls, "etapa_preferencias_concluida")).toHaveLength(0);
});

test("editar o perfil preserva o rótulo e o indicador de envio do botão", async () => {
  const { controlador } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: { ...perfil, telegram_chat_id: "123" } });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  expect($("#submit-label").textContent).toBe("Salvar alterações");
  expect($("#submit-profile .button-spinner")).toBeTruthy();
  clicar("#logout-account");
  await esperar();
  executar(() => controlador.definirModo("signup"));
  expect($("#submit-label").textContent).toBe("Criar conta e continuar");
});

test("confirmar o cadastro leva a barra a 100% enquanto a conta é criada", async () => {
  const { calls, cliente } = abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher();
  avancar(3);
  expect(progresso()).toEqual(["75%", "75", "75%"]);
  let liberarCadastro = () => {};
  const cadastroLiberado = new Promise((resolve) => {
    liberarCadastro = resolve;
  });
  cliente.auth.signUp = async (args) => {
    calls.push(["signup", args]);
    await cadastroLiberado;
    return { data: { session: null } };
  };
  enviar(formulario);
  await esperar();
  expect(progresso()).toEqual(["100%", "100", "100%"]);
  liberarCadastro();
  await esperar();
});

test("cadastro recusado devolve a barra ao último passo", async () => {
  const { calls, cliente } = abrirAplicacao();
  await abrirCadastro();
  const formulario = preencher();
  avancar(3);
  cliente.auth.signUp = async (args) => {
    calls.push(["signup", args]);
    return { data: { session: null }, error: new Error("falha simulada") };
  };
  enviar(formulario);
  await esperar();
  expect(formulario.hidden).toBe(false);
  expect(progresso()).toEqual(["75%", "75", "75%"]);
  expect($("#form-message").textContent).toBe(
    "Não foi possível concluir o cadastro agora. Verifique os dados e tente novamente.",
  );
});

test("erro ao salvar perfil iniciante mantém dados e a opção de habilidades vazias", async () => {
  const { cliente } = abrirAplicacao();
  await esperar();
  cliente.auth.signUp = async () => ({ data: { session: { user: usuario } } });
  cliente.rpc = async () => ({ error: new Error("indisponível") });
  clicar(".js-open-signup");
  await esperar();
  const formulario = preencher(false);
  avancar(2);
  clicar("#continue-without-skills");
  enviar(formulario);
  await esperar();
  expect(passoAtivo()).toBe("4");
  expect(formulario.elements.cidade.value).toBe("Recife, PE");
  expect(formulario.elements.habilidades.value).toBe("");
  expect($("#form-message").textContent).toContain("Entre novamente para concluir o perfil");
  clicar("#previous-step");
  clicar("#next-step");
  expect(passoAtivo()).toBe("4");
  await esperar();
});

test("perfil confirmado sem linha no banco conclui o cadastro pela RPC", async () => {
  const { calls } = abrirAplicacao({ sessao: { user: usuario }, url: "/#access_token=fake" });
  await esperar();
  alterarCampo("curso", "Computação");
  alterarCampo("periodo", "3");
  alterarCampo("cidade", "Recife, PE");
  clicar('#signup-form [value="remoto"]');
  clicar('[data-skill="Python"]');
  marcar('#signup-form [name="aceitou_termos"]', true);
  enviar("#signup-form");
  await esperar();
  const [, nome, argumentos] = chamada(calls, "rpc");
  expect(nome).toBe("concluir_meu_cadastro");
  expect(argumentos.cadastro.perfil.curso).toBe("Computação");
  expect(chamadas(calls, "signup")).toHaveLength(0);
  expect(calls.some(([registrada, tabela]) => registrada === "insert" && tabela === "perfis")).toBe(false);
});
