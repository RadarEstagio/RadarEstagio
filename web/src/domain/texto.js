export function normalizarTexto(texto) {
  return texto
    .replace(/[\u2010\u2011\u2013\u2014\u2212]/g, "-")
    .normalize("NFKD")
    .replace(/[\u0080-\uffff]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

export function textoDeBusca(texto) {
  return normalizarTexto(texto.replace(/[\u2018\u2019\u02bc\u2032]/g, " "))
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}
