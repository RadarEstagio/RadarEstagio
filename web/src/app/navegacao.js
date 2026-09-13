export function lerRetornoDoAuth(localizacao) {
  const fragmento = new URLSearchParams(localizacao.hash.slice(1));
  const consulta = new URLSearchParams(localizacao.search);
  return {
    consulta,
    voltandoDoAuth: fragmento.has("access_token") || consulta.has("code"),
    voltandoDaRecuperacao: fragmento.get("type") === "recovery" || consulta.get("fluxo") === "recuperar",
    erroDoLink:
      fragmento.get("error_code") || consulta.get("error_code") || fragmento.get("error") || consulta.get("error"),
  };
}

export function enderecoDeRetorno(localizacao) {
  return localizacao.origin + localizacao.pathname;
}
