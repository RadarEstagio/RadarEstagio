import { erroDeValidacao } from "../domain/perfil.js";

const ENDERECO_DO_TURNSTILE =
  "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=radarCaptchaReady&render=explicit";

export function criarCaptcha({ janela, chave, aoFalhar }) {
  const elemento = janela.document.createElement("div");
  elemento.id = "captcha-container";
  let widget = null;
  let token = "";

  function exigir() {
    if (!chave) return undefined;
    if (!token) throw erroDeValidacao("Conclua a verificação de segurança antes de continuar.");
    return token;
  }

  function reiniciar() {
    token = "";
    if (widget !== null) janela.turnstile?.reset(widget);
  }

  function carregar() {
    if (!chave) return;
    janela.radarCaptchaReady = () => {
      widget = janela.turnstile.render(elemento, {
        sitekey: chave,
        callback: (novoToken) => {
          token = novoToken;
        },
        "expired-callback": () => {
          token = "";
        },
        "error-callback": () => {
          token = "";
          aoFalhar("A verificação de segurança falhou. Confira sua conexão e tente novamente.");
        },
      });
    };
    const script = janela.document.createElement("script");
    script.src = ENDERECO_DO_TURNSTILE;
    script.async = true;
    script.onerror = () => aoFalhar("Não foi possível carregar a verificação de segurança. Recarregue a página.");
    janela.document.head.append(script);
  }

  return { elemento, exigir, reiniciar, carregar };
}
