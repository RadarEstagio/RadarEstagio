const CHAVE_DA_SESSAO_DE_EVENTOS = "radar-sessao-eventos";
const CHAVE_DA_LANDING_VISTA = "radar-landing-vista";
const PADRAO_DE_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TAMANHO_MAXIMO_DO_TEXTO_DO_EVENTO = 40;

export function propriedadesDoEvento(propriedades) {
  return Object.fromEntries(
    Object.entries(propriedades).map(([chave, valor]) => [
      chave,
      typeof valor === "string" ? Array.from(valor).slice(0, TAMANHO_MAXIMO_DO_TEXTO_DO_EVENTO).join("") : valor,
    ]),
  );
}

export function criarEventos({ janela, obterCliente }) {
  let sessaoEmMemoria = null;

  function idDaSessao() {
    let existente = null;
    try {
      existente = janela.localStorage.getItem(CHAVE_DA_SESSAO_DE_EVENTOS);
    } catch {}
    if (existente && PADRAO_DE_UUID.test(existente)) return existente;
    sessaoEmMemoria ??= janela.crypto.randomUUID();
    try {
      janela.localStorage.setItem(CHAVE_DA_SESSAO_DE_EVENTOS, sessaoEmMemoria);
    } catch {}
    return sessaoEmMemoria;
  }

  async function registrar(nome, propriedades = {}) {
    try {
      const cliente = obterCliente();
      const { data } = await cliente.auth.getSession();
      const { error } = await cliente.from("eventos_produto").insert({
        nome,
        sessao_id: idDaSessao(),
        user_id: data.session?.user.id ?? null,
        propriedades: propriedadesDoEvento(propriedades),
      });
      if (error) throw error;
    } catch (erro) {
      console.warn(`Radar: o evento "${nome}" não foi registrado.`, erro);
      return false;
    }
    return true;
  }

  function landingJaContadaNestaSessao() {
    try {
      if (janela.sessionStorage.getItem(CHAVE_DA_LANDING_VISTA)) return true;
      janela.sessionStorage.setItem(CHAVE_DA_LANDING_VISTA, "1");
      return false;
    } catch {
      return false;
    }
  }

  return { idDaSessao, registrar, landingJaContadaNestaSessao };
}
