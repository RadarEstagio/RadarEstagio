import { prepararCidades } from "../domain/cidades.js";

export function criarCatalogos(janela) {
  let areas = null;
  let cidades = null;
  let carregamentoDeCidades = null;

  async function carregarAreas() {
    if (areas) return areas;
    try {
      const resposta = await janela.fetch("assets/areas.json");
      areas = resposta.ok ? await resposta.json() : null;
    } catch {
      areas = null;
    }
    return areas;
  }

  function carregarCidades() {
    if (cidades) return Promise.resolve(cidades);
    carregamentoDeCidades ??= Promise.resolve()
      .then(() => janela.fetch("assets/cidades.json"))
      .then((resposta) => (resposta.ok ? resposta.json() : null))
      .catch(() => null)
      .then((lista) => {
        carregamentoDeCidades = null;
        cidades = Array.isArray(lista) ? prepararCidades(lista) : null;
        return cidades;
      });
    return carregamentoDeCidades;
  }

  return {
    carregarAreas,
    carregarCidades,
    areasCarregadas: () => areas,
    cidadesCarregadas: () => cidades,
  };
}
