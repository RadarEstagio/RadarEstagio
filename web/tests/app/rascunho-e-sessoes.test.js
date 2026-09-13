import { fireEvent } from "@testing-library/react";
import { expect, test } from "vitest";
import {
  $,
  abrirAplicacao,
  alterarCampo,
  chamada,
  clicar,
  dialogoAberto,
  digitar,
  enviar,
  esperar,
  habilidadesNaTela,
  marcar,
  passoAtivo,
  perfil,
  preencher,
  teclar,
  usuario,
} from "./ambiente.js";

const outraPessoa = { id: "00000000-0000-4000-8000-000000000002", email: "outra@example.com" };
const perfilVinculado = { ...perfil, telegram_chat_id: "123" };

function fecharComEsc() {
  teclar("#cidade", "Escape");
}

async function reabrirCadastro() {
  clicar(".js-open-signup");
  await esperar();
}

function adicionarHabilidade(valor) {
  digitar("#custom-skill", valor);
  teclar("#custom-skill", "Enter");
}

function sessaoPassaASer(cliente, sessao) {
  cliente.auth.getSession = async () => ({ data: { session: sessao } });
}

function campo(nome) {
  return $("#signup-form").elements[nome];
}

function conferirCadastroVazio(contexto) {
  expect(campo("curso").value, contexto).toBe("");
  expect(campo("email").value, contexto).toBe("");
  expect(habilidadesNaTela(), contexto).toEqual([]);
}

function conferirSenhaVaziaEEscondida(contexto) {
  const botao = $('[data-toggle-password="senha"]');
  expect($("#signup-password").value, contexto).toBe("");
  expect($("#signup-password").type, contexto).toBe("password");
  expect(botao.getAttribute("aria-pressed"), contexto).toBe("false");
  expect(botao.getAttribute("aria-label"), contexto).toBe("Mostrar senha");
}

function conferirEnvioRecusado(calls, contexto) {
  expect(calls.some(([nome, tabela]) => nome === "update" && tabela === "perfis"), contexto).toBe(false);
  expect(calls.some(([nome, alvo]) => nome === "rpc" && alvo === "concluir_meu_cadastro"), contexto).toBe(false);
  expect(calls.some(([nome]) => ["logout", "signup", "login"].includes(nome)), contexto).toBe(false);
  expect($("#form-message").textContent, contexto).toMatch(/Sua sessão mudou/);
  conferirCadastroVazio(contexto);
}

function contaSemPerfilNoBanco(cliente) {
  const from = cliente.from;
  cliente.from = (tabela) => {
    const consulta = from(tabela);
    consulta.maybeSingle = async () => ({ data: null });
    return consulta;
  };
}

async function rascunhoDeVisitanteFechado() {
  await esperar();
  await reabrirCadastro();
  preencher();
  clicar("#next-step");
  await esperar();
  fecharComEsc();
}

function conferirPerfilACompletarVazio(contexto) {
  expect($("#missing-profile-deletion").hidden, contexto).toBe(false);
  expect(campo("curso").value, contexto).toBe("");
  expect(campo("cidade").value, contexto).toBe("");
  expect(habilidadesNaTela(), contexto).toEqual([]);
  expect(campo("email").value, contexto).toBe(outraPessoa.email);
}

test("fechar o cadastro com Esc ou no X e reabrir devolve o rascunho na mesma etapa", async () => {
  const { calls } = abrirAplicacao();
  await esperar();
  await reabrirCadastro();
  preencher();
  clicar("#next-step");
  await esperar();
  adicionarHabilidade("Figma");
  clicar("#next-step");
  await esperar();
  marcar('input[name="areas"][value="dados_ia"]', true);

  const conferirRascunho = () => {
    expect(dialogoAberto()).toBe(true);
    expect(passoAtivo()).toBe("4");
    expect(campo("curso").value).toBe("Computação");
    expect(campo("periodo").value).toBe("3");
    expect(campo("cidade").value).toBe("Recife, PE");
    expect($('#signup-form [value="remoto"]').checked).toBe(true);
    expect(habilidadesNaTela()).toEqual(["Python", "Figma"]);
    expect($('input[name="areas"][value="dados_ia"]').checked).toBe(true);
    expect(campo("senha").value).toBe("");
    expect(campo("email").value).toBe("");
  };
  fecharComEsc();
  expect(dialogoAberto()).toBe(false);
  await reabrirCadastro();
  conferirRascunho();
  clicar("#close-dialog");
  expect(dialogoAberto()).toBe(false);
  await reabrirCadastro();
  conferirRascunho();

  clicar("#next-step");
  alterarCampo("email", usuario.email);
  alterarCampo("senha", "uma-senha-forte");
  enviar("#signup-form");
  await esperar();
  const enviado = chamada(calls, "signup")[1].options.data.cadastro_radar.perfil;
  expect(enviado.curso).toBe("Computação");
  expect(enviado.habilidades).toEqual(["Python", "Figma"]);
  expect(enviado.areas_de_interesse).toEqual(["dados_ia"]);
});

test("fechar o cadastro depois de seguir sem habilidades não pede a escolha de novo", async () => {
  const { calls } = abrirAplicacao();
  await esperar();
  await reabrirCadastro();
  preencher(false);
  clicar("#next-step");
  clicar("#continue-without-skills");
  fecharComEsc();
  await reabrirCadastro();

  expect(passoAtivo()).toBe("4");
  clicar("#next-step");
  expect(passoAtivo()).toBe("1");
  expect(campo("senha").value).toBe("");
  expect(campo("email").value).toBe("");
  alterarCampo("email", usuario.email);
  alterarCampo("senha", "uma-senha-forte");
  enviar("#signup-form");
  await esperar();
  expect(chamada(calls, "signup")[1].options.data.cadastro_radar.perfil.habilidades).toEqual([]);
});

test("perfil carregado da conta não reaparece no cadastro depois que a sessão acaba", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  expect(campo("curso").value).toBe("Computação");
  sessaoPassaASer(cliente, null);
  clicar("#back-to-site");
  await reabrirCadastro();

  expect(passoAtivo()).toBe("2");
  expect(campo("curso").value).toBe("");
  expect(campo("cidade").value).toBe("");
  expect(habilidadesNaTela()).toEqual([]);
});

test.each(["esc", "x", "voltar"])(
  "fechar o cadastro (%s) apaga senha e e-mail e volta a esconder a senha, mantendo o resto do rascunho",
  async (como) => {
    abrirAplicacao();
    await esperar();
    await reabrirCadastro();
    preencher();
    for (let passo = 0; passo < 3; passo += 1) clicar("#next-step");
    await esperar();
    clicar('[data-toggle-password="senha"]');
    expect(campo("senha").type).toBe("text");

    if (como === "esc") fecharComEsc();
    else if (como === "x") clicar("#close-dialog");
    else fireEvent.popState(window);
    await reabrirCadastro();

    conferirSenhaVaziaEEscondida(como);
    expect(campo("curso").value).toBe("Computação");
    expect(campo("email").value).toBe("");
    expect(passoAtivo()).toBe("1");
  },
);

test("senha de um login recusado não fica no campo ao fechar e reabrir", async () => {
  const { cliente } = abrirAplicacao();
  await esperar();
  cliente.auth.signInWithPassword = async () => ({
    data: { session: null },
    error: { code: "invalid_credentials", message: "Invalid login credentials", status: 400 },
  });
  await reabrirCadastro();
  clicar("#toggle-auth-mode");
  alterarCampo("email", "a@x.com");
  alterarCampo("senha", "senha-da-pessoa-A");
  clicar('[data-toggle-password="senha"]');
  enviar("#signup-form");
  await esperar();
  expect($("#form-message").textContent).toMatch(/E-mail ou senha incorretos/);

  fecharComEsc();
  await reabrirCadastro();
  conferirSenhaVaziaEEscondida("login recusado");
});

test("rascunho e e-mail de uma conta não aparecem para quem abre o cadastro depois que a sessão acaba", async () => {
  const comPerfil = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado });
  await esperar();
  await reabrirCadastro();
  expect($("#account-page").hidden).toBe(false);
  clicar("#close-account");
  sessaoPassaASer(comPerfil.cliente, null);
  await reabrirCadastro();
  conferirCadastroVazio("conta com perfil");

  const semPerfil = abrirAplicacao({ sessao: { user: usuario }, url: "/?conta" });
  await esperar();
  expect(campo("email").value).toBe(usuario.email);
  alterarCampo("curso", "Direito");
  clicar("#back-to-site");
  sessaoPassaASer(semPerfil.cliente, null);
  await reabrirCadastro();
  conferirCadastroVazio("conta sem perfil");
  expect($("#credenciais").hidden).toBe(false);
});

test("outra conta que entra na mesma página não vê o rascunho da conta anterior", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, url: "/?conta" });
  await esperar();
  alterarCampo("curso", "Direito");
  clicar("#back-to-site");
  sessaoPassaASer(cliente, { user: outraPessoa });
  await reabrirCadastro();

  expect($("#missing-profile-deletion").hidden).toBe(false);
  expect(campo("curso").value).toBe("");
  expect(campo("email").value).toBe(outraPessoa.email);
});

test("visitante que confirma a conta criada daqui continua com o próprio rascunho", async () => {
  const { calls, cliente } = abrirAplicacao();
  await esperar();
  await reabrirCadastro();
  preencher();
  for (let passo = 0; passo < 3; passo += 1) clicar("#next-step");
  enviar("#signup-form");
  await esperar();
  expect(chamada(calls, "signup")[1].email).toBe(usuario.email);
  fecharComEsc();
  sessaoPassaASer(cliente, { user: usuario });
  await reabrirCadastro();

  expect($("#missing-profile-deletion").hidden).toBe(false);
  expect(campo("curso").value).toBe("Computação");
  expect(habilidadesNaTela()).toEqual(["Python"]);
  expect(campo("email").value).toBe(usuario.email);
});

test("sair ou excluir a conta deixa o cadastro vazio para a próxima pessoa", async () => {
  const saindo = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado });
  await esperar();
  await reabrirCadastro();
  clicar("#edit-profile");
  await esperar();
  clicar("#back-to-site");
  await reabrirCadastro();
  clicar("#logout-account");
  await esperar();
  sessaoPassaASer(saindo.cliente, null);
  await reabrirCadastro();
  conferirCadastroVazio("logout depois de editar");

  const semPerfil = abrirAplicacao({ sessao: { user: usuario }, url: "/?conta" });
  await esperar();
  alterarCampo("curso", "Direito");
  clicar("#delete-account-without-profile");
  clicar("#account-confirm-yes");
  await esperar();
  sessaoPassaASer(semPerfil.cliente, null);
  clicar("#finish-signup");
  await reabrirCadastro();
  conferirCadastroVazio("exclusão sem perfil");

  const comPerfil = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado });
  await esperar();
  await reabrirCadastro();
  clicar("#delete-account");
  clicar("#account-confirm-yes");
  await esperar();
  clicar("#finish-signup");
  sessaoPassaASer(comPerfil.cliente, null);
  await reabrirCadastro();
  conferirCadastroVazio("exclusão com perfil e sessão encerrada depois");
});

test("e-mail digitado num login não fica para quem abre o cadastro depois que a sessão acaba", async () => {
  abrirAplicacao({ perfilSalvo: perfilVinculado });
  await esperar();
  await reabrirCadastro();
  clicar("#toggle-auth-mode");
  alterarCampo("email", "a@x.com");
  alterarCampo("senha", "uma-senha-forte");
  enviar("#signup-form");
  await esperar();
  expect($("#account-page").hidden).toBe(false);
  clicar("#close-account");
  await reabrirCadastro();
  conferirCadastroVazio("login e sessão encerrada");
});

test("edição aberta de uma conta não é gravada em outra que entrou em outra aba", async () => {
  const { calls, cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  sessaoPassaASer(cliente, { user: outraPessoa });
  clicar("#next-step");
  clicar("#next-step");
  enviar("#signup-form");
  await esperar();
  conferirEnvioRecusado(calls, "edição de outra conta");
});

test("perfil sendo completado por uma conta não vai para outra que entrou em outra aba", async () => {
  const { calls, cliente } = abrirAplicacao({ sessao: { user: usuario }, url: "/?conta" });
  await esperar();
  preencher();
  sessaoPassaASer(cliente, { user: outraPessoa });
  clicar("#next-step");
  clicar("#next-step");
  enviar("#signup-form");
  await esperar();
  conferirEnvioRecusado(calls, "perfil a completar de outra conta");
});

test("rascunho de visitante não é concluído numa conta que apareceu em outra aba", async () => {
  const { calls, cliente } = abrirAplicacao();
  await esperar();
  await reabrirCadastro();
  preencher();
  for (let passo = 0; passo < 3; passo += 1) clicar("#next-step");
  await esperar();
  sessaoPassaASer(cliente, { user: usuario });
  enviar("#signup-form");
  await esperar();
  conferirEnvioRecusado(calls, "rascunho de visitante numa sessão de outra aba");
});

test("sessão que falha ao renovar não deixa o perfil da conta no formulário nem para o próximo login", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  expect(campo("curso").value).toBe("Computação");
  clicar("#back-to-site");
  cliente.auth.getSession = async () => ({
    data: { session: null },
    error: new Error("Invalid Refresh Token: Refresh Token Not Found"),
  });
  await reabrirCadastro();
  expect($("#form-message").textContent).toMatch(/Não conseguimos carregar sua conta/);

  clicar("#toggle-auth-mode");
  expect(campo("curso").value, "Criar conta depois do erro").toBe("");
  expect(campo("cidade").value, "Criar conta depois do erro").toBe("");
  expect(habilidadesNaTela(), "Criar conta depois do erro").toEqual([]);

  clicar("#toggle-auth-mode");
  sessaoPassaASer(cliente, null);
  cliente.auth.signInWithPassword = async () => ({ data: { session: { user: outraPessoa } } });
  contaSemPerfilNoBanco(cliente);
  alterarCampo("email", outraPessoa.email);
  alterarCampo("senha", "senha-da-outra-pessoa");
  enviar("#signup-form");
  await esperar();

  expect($("#missing-profile-deletion").hidden).toBe(false);
  expect(campo("curso").value, "login seguinte").toBe("");
  expect(habilidadesNaTela(), "login seguinte").toEqual([]);
  expect(campo("email").value).toBe(outraPessoa.email);
});

test("login de outra conta pelo diálogo não herda o rascunho do visitante", async () => {
  const { cliente } = abrirAplicacao();
  await rascunhoDeVisitanteFechado();
  await reabrirCadastro();
  clicar("#toggle-auth-mode");
  cliente.auth.signInWithPassword = async () => ({ data: { session: { user: outraPessoa } } });
  alterarCampo("email", outraPessoa.email);
  alterarCampo("senha", "senha-da-outra-pessoa");
  enviar("#signup-form");
  await esperar();
  conferirPerfilACompletarVazio("login pelo diálogo");
});

test("sessão de outra conta que chega de outra aba não herda o rascunho do visitante", async () => {
  const { cliente } = abrirAplicacao();
  await rascunhoDeVisitanteFechado();
  sessaoPassaASer(cliente, { user: outraPessoa });
  await reabrirCadastro();
  conferirPerfilACompletarVazio("sessão de outra aba");
});
