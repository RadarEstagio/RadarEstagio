export const ROLAGEM_MINIMA_ATE_CHAT = 90;

export function iniciarDemonstracao(janela) {
  const demonstracaoDoChat = janela.document.querySelector("[data-chat-demo]");
  if (!demonstracaoDoChat) return () => {};

  function reproduzir() {
    demonstracaoDoChat.classList.remove("is-waiting");
    demonstracaoDoChat.classList.add("is-playing");
  }

  if (janela.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
    reproduzir();
    return () => {};
  }

  function reproduzirChatAoRolar() {
    const limitesDoChat = demonstracaoDoChat.getBoundingClientRect();
    const chatEntrouNaAreaUtil = limitesDoChat.top <= janela.innerHeight * 0.82 && limitesDoChat.bottom >= 0;
    if (janela.scrollY < ROLAGEM_MINIMA_ATE_CHAT || !chatEntrouNaAreaUtil) return;
    reproduzir();
    janela.removeEventListener("scroll", reproduzirChatAoRolar);
  }

  janela.addEventListener("scroll", reproduzirChatAoRolar, { passive: true });
  return () => janela.removeEventListener("scroll", reproduzirChatAoRolar);
}
