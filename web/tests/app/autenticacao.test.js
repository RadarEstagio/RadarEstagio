import { expect, test } from "vitest";
import {
  $,
  abrirAplicacao,
  chamada,
  chamadas,
  clicar,
  dialogoAberto,
  digitar,
  enviar,
  esperar,
  executar,
  passoAtivo,
  perfil,
  preencher,
  usuario,
} from "./ambiente.js";

function captchaComToken(token) {
  let widget;
  let reinicios = 0;
  window.turnstile = {
    render: (_, opcoes) => {
      widget = opcoes;
      return 1;
    },
    reset: () => {
      reinicios += 1;
    },
  };
  window.radarCaptchaReady();
  expect(widget).toBeTruthy();
  widget.callback(token);
  return () => reinicios;
}

test("confirmação em outro aparelho consulta banco sem perfil no navegador", async () => {
  const { calls } = abrirAplicacao({
    sessao: { user: usuario },
    perfilSalvo: perfil,
    url: "/#access_token=fake",
  });
  await esperar();
  expect($("#success-state").hidden).toBe(false);
  expect($("#telegram-link").hidden).toBe(false);
  expect($("#telegram-link").getAttribute("href")).toBe("https://t.me/bot?start=token");
  expect(calls.filter(([nome]) => nome === "rpc" || nome === "update")).toHaveLength(0);
});

test("login preserva perfil existente mesmo com formulário diferente", async () => {
  const { calls, controlador } = abrirAplicacao({ perfilSalvo: { ...perfil, telegram_chat_id: "123" } });
  const formulario = preencher();
  executar(() => controlador.definirModo("login"));
  digitar(formulario.elements.cidade, "Outra cidade");
  enviar(formulario);
  await esperar();
  expect(chamadas(calls, "login")).toHaveLength(1);
  expect(calls.filter(([nome]) => nome === "update" || nome === "rpc")).toHaveLength(0);
  expect($("#account-state").hidden).toBe(false);
});

test("CAPTCHA válido segue na autenticação e é descartado após tentativa", async () => {
  const { calls, controlador } = abrirAplicacao({ chave: "chave-publica" });
  const reinicios = captchaComToken("token-valido");
  enviar(preencher());
  await esperar();
  expect(chamada(calls, "signup")[1].options.captchaToken).toBe("token-valido");
  expect(reinicios()).toBe(1);
  expect(() => controlador.exigirCaptcha()).toThrow();
});

test("reenvio usa e-mail editado e bloqueia clique repetido por um minuto", async () => {
  const { calls, controlador } = abrirAplicacao();
  executar(() => controlador.mostrarAssistencia("resend", usuario.email));
  digitar("#assistance-email", "corrigido@example.com");
  enviar("#assistance-form");
  await esperar();
  enviar("#assistance-form");
  await esperar();
  expect(chamadas(calls, "resend")).toHaveLength(1);
  expect(chamada(calls, "resend")[1].email).toBe("corrigido@example.com");
  expect($("#assistance-submit").disabled).toBe(true);
  expect($("#assistance-submit").textContent).toMatch(/Reenviar em \d+s/);
});

test("link expirado oferece e-mail editável sem contexto local", async () => {
  abrirAplicacao({ url: "/#error_code=otp_expired" });
  await esperar();
  expect($("#auth-assistance").hidden).toBe(false);
  expect($("#assistance-email").required).toBe(true);
  expect($("#assistance-message").textContent).toMatch(/expirou/);
});

test("CAPTCHA configurado impede autenticação sem token", async () => {
  const { calls } = abrirAplicacao({ chave: "public-key" });
  enviar(preencher());
  await esperar();
  expect(chamadas(calls, "signup")).toHaveLength(0);
  expect($("#form-message").textContent).toMatch(/verificação de segurança/);
});

test("recuperação exige evento autenticado antes de trocar senha", async () => {
  const { calls, controlador, eventoDeAuth } = abrirAplicacao({ sessao: { user: usuario } });
  await esperar();
  executar(() => controlador.mostrarAssistencia("new-password"));
  const tentar = () => {
    digitar("#assistance-password", "nova-senha-forte");
    enviar("#assistance-form");
  };
  tentar();
  await esperar();
  expect(chamadas(calls, "password")).toHaveLength(0);
  eventoDeAuth("PASSWORD_RECOVERY");
  await esperar();
  tentar();
  await esperar();
  expect(chamadas(calls, "password")).toHaveLength(1);
  expect($("#assistance-password").value).toBe("");
  expect($("#form-notice").textContent).toBe("Senha atualizada. Entre com sua nova senha.");
});

test("endereço da conta sem sessão exige login", async () => {
  abrirAplicacao({ url: "/?conta" });
  await esperar();
  expect($("#account-page").hidden).toBe(true);
  expect(dialogoAberto()).toBe(true);
  expect($("#signup-form").hidden).toBe(false);
});

test("aviso de perfil pendente não usa o visual de erro", async () => {
  abrirAplicacao({ sessao: { user: usuario }, url: "/#access_token=fake" });
  await esperar();
  const mensagem = $("#form-notice");
  expect(mensagem.hidden).toBe(false);
  expect(mensagem.textContent).toContain("Complete seu perfil");
  expect(mensagem.classList.contains("form-message-aviso")).toBe(true);
});

test("botão de entrar abre a conta sem passar pela triagem", async () => {
  abrirAplicacao();
  await esperar();
  clicar(".js-open-login");
  await esperar();
  expect(passoAtivo()).toBe("1");
  expect($("#submit-label").textContent).toBe("Entrar e continuar");
  expect($("#signup-consent").hidden).toBe(true);
  expect($("#conta-titulo").textContent).toBe("Entre na sua conta");
  expect($("#toggle-auth-mode").textContent).toBe("Criar conta");
});

test("controle de senha usa ícone e anuncia mostrar e ocultar", async () => {
  abrirAplicacao();
  await esperar();
  const senha = $('input[name="senha"]');
  const alternar = $('[data-toggle-password="senha"]');
  expect(alternar.querySelector("svg")).toBeTruthy();
  expect(alternar.textContent.trim()).toBe("");
  expect(alternar.getAttribute("aria-label")).toBe("Mostrar senha");
  expect(senha.getAttribute("type")).toBe("password");
  clicar(alternar);
  expect(senha.getAttribute("type")).toBe("text");
  expect(alternar.getAttribute("aria-label")).toBe("Ocultar senha");
  expect(alternar.getAttribute("aria-pressed")).toBe("true");
  clicar(alternar);
  expect(senha.getAttribute("type")).toBe("password");
  expect(alternar.getAttribute("aria-label")).toBe("Mostrar senha");
  expect(alternar.getAttribute("aria-pressed")).toBe("false");
});

test("CAPTCHA acompanha o reenvio da confirmação", async () => {
  const { calls, controlador } = abrirAplicacao({ chave: "chave-publica" });
  captchaComToken("token-do-reenvio");
  executar(() => controlador.mostrarAssistencia("resend", usuario.email));
  enviar("#assistance-form");
  await esperar();
  expect(chamada(calls, "resend")[1].options.captchaToken).toBe("token-do-reenvio");
});

test("CAPTCHA acompanha o pedido de recuperação de senha", async () => {
  const { calls, controlador } = abrirAplicacao({ chave: "chave-publica" });
  captchaComToken("token-da-recuperacao");
  executar(() => controlador.mostrarAssistencia("reset", usuario.email));
  enviar("#assistance-form");
  await esperar();
  const pedido = chamada(calls, "reset");
  expect(pedido[2].captchaToken).toBe("token-da-recuperacao");
  expect(pedido[2].redirectTo.endsWith("?fluxo=recuperar")).toBe(true);
});

test("CAPTCHA fica no mesmo elemento quando o painel passa do modal para a conta", async () => {
  abrirAplicacao({ chave: "chave-publica", sessao: { user: usuario }, perfilSalvo: perfil });
  const elemento = $("#captcha-container");
  expect(elemento.closest("#signup-dialog")).toBeTruthy();
  clicar(".js-open-signup");
  await esperar();
  expect($("#captcha-container")).toBe(elemento);
  expect(elemento.closest("#account-content")).toBeTruthy();
  expect(elemento.hidden).toBe(true);
});
