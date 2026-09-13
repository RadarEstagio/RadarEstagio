import { textoDeBusca } from "./texto.js";

export const MAXIMO_DE_CIDADES_SUGERIDAS = 8;

export function prepararCidades(nomes) {
  return nomes.map((nome) => ({
    nome,
    busca: textoDeBusca(nome),
    municipio: textoDeBusca(nome.slice(0, nome.lastIndexOf(","))),
  }));
}

export function homonimasDe(catalogo, busca) {
  return catalogo.filter((cidade) => cidade.municipio === busca);
}

export function cidadeDaLista(catalogo, texto) {
  const busca = textoDeBusca(texto);
  if (!catalogo || !busca) return null;
  const exata = catalogo.find((cidade) => cidade.busca === busca);
  if (exata) return exata.nome;
  const homonimas = homonimasDe(catalogo, busca);
  return homonimas.length === 1 ? homonimas[0].nome : null;
}

export function cidadesParecidas(catalogo, texto) {
  const busca = textoDeBusca(texto);
  if (!busca) return catalogo.slice(0, MAXIMO_DE_CIDADES_SUGERIDAS);
  const noComeco = [];
  const emOutraPalavra = [];
  for (const cidade of catalogo) {
    if (cidade.busca.startsWith(busca)) noComeco.push(cidade);
    else if (cidade.busca.includes(` ${busca}`)) emOutraPalavra.push(cidade);
    if (noComeco.length === MAXIMO_DE_CIDADES_SUGERIDAS) break;
  }
  return [...noComeco, ...emOutraPalavra].slice(0, MAXIMO_DE_CIDADES_SUGERIDAS);
}
