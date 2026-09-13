export function criarPaginas(documento) {
  const landing = documento.querySelector("#landing-page");
  const conta = documento.querySelector("#account-page");
  const dialogo = documento.querySelector("#signup-dialog");
  const chamadasDeCadastro = [...documento.querySelectorAll(".js-open-signup")];
  const chamadasDeLogin = [...documento.querySelectorAll(".js-open-login")];
  const rotulosDeCadastro = new Map(chamadasDeCadastro.map((botao) => [botao, botao.firstChild.textContent]));
  const tituloDaLanding = documento.title;

  function fecharElementoDoDialogo() {
    if (dialogo.open && typeof dialogo.close === "function") dialogo.close();
    else dialogo.removeAttribute("open");
  }

  return {
    dialogo,
    conta,
    chamadasDeCadastro,
    chamadasDeLogin,
    rotularChamadas(autenticado) {
      for (const botao of chamadasDeCadastro) {
        botao.firstChild.textContent = autenticado ? `${botao.dataset.rotuloConta} ` : rotulosDeCadastro.get(botao);
      }
      for (const botao of chamadasDeLogin) botao.hidden = autenticado;
    },
    abrirDialogo() {
      if (typeof dialogo.showModal === "function") dialogo.showModal();
      else dialogo.setAttribute("open", "");
      documento.body.style.overflow = "hidden";
    },
    fecharDialogo() {
      fecharElementoDoDialogo();
      documento.body.style.overflow = "";
    },
    rotularDialogo(idDoTitulo) {
      dialogo.setAttribute("aria-labelledby", idDoTitulo);
    },
    mostrarConta() {
      fecharElementoDoDialogo();
      landing.hidden = true;
      conta.hidden = false;
      documento.body.classList.add("account-page-open");
      documento.body.style.overflow = "";
      documento.title = "Minha conta — Radar de Estágio";
    },
    esconderConta() {
      conta.hidden = true;
      landing.hidden = false;
      documento.body.classList.remove("account-page-open");
      documento.title = tituloDaLanding;
    },
    focarCadastro() {
      chamadasDeCadastro[0]?.focus();
    },
  };
}
