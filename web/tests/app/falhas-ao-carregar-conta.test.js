import { expect, test } from "vitest";
import {
  $,
  abrirAplicacao,
  chamadas,
  clicar,
  dialogoAberto,
  enviar,
  esperar,
  passoAtivo,
  perfil,
  preencher,
  usuario,
  visivel,
} from "./ambiente.js";

const CONTA_INDISPONIVEL = /Não conseguimos carregar sua conta/;
const perfilVinculado = { ...perfil, telegram_chat_id: "123" };

test("erro ao abrir minha conta na tela de ativação aparece na própria tela", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfil, url: "/?conta" });
  await esperar();
  expect(visivel("#success-state")).toBe(true);
  cliente.auth.getSession = async () => ({ data: { session: null } });
  clicar("#success-account");
  await esperar();
  expect($("#success-message").textContent).toMatch(/sessão expirou/);
  expect(visivel("#success-message")).toBe(true);
  expect(visivel("#success-state")).toBe(true);
});

test("sessão que não renova abre o login com aviso honesto, sem dizer que a conta foi criada", async () => {
  abrirAplicacao({
    erroDaSessao: Object.assign(new Error("Invalid Refresh Token: Refresh Token Not Found"), {
      code: "refresh_token_not_found",
      status: 400,
    }),
  });
  await esperar();
  const mensagem = $("#form-message").textContent;
  expect(dialogoAberto()).toBe(true);
  expect($("#conta-titulo").textContent).toBe("Entre na sua conta");
  expect(passoAtivo()).toBe("1");
  expect(mensagem).toMatch(CONTA_INDISPONIVEL);
  expect(mensagem).not.toMatch(/conta foi criada/);
});

test("falha de rede ao ler o perfil na volta do link não diz que o perfil falta", async () => {
  abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: perfilVinculado,
    url: "/#access_token=fake",
    erroDoPerfil: new TypeError("Failed to fetch"),
  });
  await esperar();
  const mensagem = $("#form-message").textContent;
  expect($("#conta-titulo").textContent).toBe("Entre na sua conta");
  expect(mensagem).toMatch(CONTA_INDISPONIVEL);
  expect(mensagem).not.toMatch(/perfil ainda não foi salvo/);
});

test("falha de rede ao abrir minha conta leva ao login, não ao começo do cadastro", async () => {
  abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: perfilVinculado,
    erroDoPerfil: new TypeError("Failed to fetch"),
  });
  await esperar();
  expect(dialogoAberto()).toBe(false);
  clicar('[data-event-origin="cabecalho"]');
  await esperar();
  expect(dialogoAberto()).toBe(true);
  expect($("#conta-titulo").textContent).toBe("Entre na sua conta");
  expect(passoAtivo()).toBe("1");
  expect($("#form-message").textContent).toMatch(CONTA_INDISPONIVEL);
});

test("falha de rede ao salvar a edição do perfil não diz que a conta foi criada", async () => {
  const { cliente } = abrirAplicacao({ sessao: { user: usuario }, perfilSalvo: perfilVinculado, url: "/?conta" });
  await esperar();
  clicar("#edit-profile");
  await esperar();
  const from = cliente.from;
  cliente.from = (tabela) => {
    const consulta = from(tabela);
    consulta.single = async () => ({ data: null, error: new TypeError("Failed to fetch") });
    return consulta;
  };
  enviar("#signup-form");
  await esperar();
  const mensagem = $("#form-message").textContent;
  expect(mensagem).not.toMatch(/conta foi criada/);
  expect(mensagem).toMatch(/conexão/);
});

test("conta confirmada sem perfil que falha ao salvar o perfil recebe o aviso de perfil pendente", async () => {
  const { calls, cliente } = abrirAplicacao({ sessao: { user: usuario }, url: "/?conta" });
  await esperar();
  cliente.rpc = async (nome, args) => {
    calls.push(["rpc", nome, args]);
    return { error: new TypeError("Failed to fetch") };
  };
  enviar(preencher());
  await esperar();
  expect(chamadas(calls, "rpc").map(([, nome]) => nome)).toEqual(["concluir_meu_cadastro"]);
  expect($("#form-message").textContent).toMatch(/Sua conta foi criada, mas o perfil ainda não foi salvo/);
  expect(visivel("#form-message")).toBe(true);
});
