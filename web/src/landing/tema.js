const CHAVE_DO_TEMA = "radar-tema";

export function iniciarTema(janela) {
  const documento = janela.document;
  const botao = documento.querySelector("#theme-toggle");
  if (!botao) return () => {};

  function mostrarTema(tema) {
    documento.documentElement.dataset.tema = tema;
    botao.setAttribute("aria-pressed", String(tema === "escuro"));
  }

  function alternarTema() {
    const tema = documento.documentElement.dataset.tema === "escuro" ? "claro" : "escuro";
    mostrarTema(tema);
    try {
      janela.localStorage.setItem(CHAVE_DO_TEMA, tema);
    } catch {
      return;
    }
  }

  mostrarTema(documento.documentElement.dataset.tema === "escuro" ? "escuro" : "claro");
  botao.addEventListener("click", alternarTema);
  return () => botao.removeEventListener("click", alternarTema);
}
