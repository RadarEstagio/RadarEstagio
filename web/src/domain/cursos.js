import { normalizarTexto } from "./texto.js";

export function normalizarCurso(curso, catalogo) {
  const sufixo = new RegExp(`(?:\\s*[-\\u2013|:]\\s*|\\s+)(?:${catalogo.sufixos.join("|")})$`);
  let texto = normalizarTexto(curso)
    .replace(/\s+/g, " ")
    .replace(/\s*(?:\(.*\)|[-\u2013|/].*)$/, "")
    .replace(sufixo, "");
  const conhecidos = new Set(catalogo.areas.flatMap((area) => area.cursos));
  const prefixo = new RegExp(
    `^(?:${catalogo.prefixos.join("|")})(?: (?:${catalogo.conectores.join("|")}))?\\s+`,
  );
  for (;;) {
    if (catalogo.genericos.includes(texto)) return "";
    if (Object.hasOwn(catalogo.sinonimos, texto)) return catalogo.sinonimos[texto];
    if (conhecidos.has(texto)) return texto;
    const encontrado = texto.match(prefixo);
    if (!encontrado) return texto;
    texto = texto.slice(encontrado[0].length);
  }
}

export function areaDoCurso(curso, catalogo) {
  if (!catalogo) return null;
  const normalizado = normalizarCurso(curso, catalogo);
  if (!normalizado) return null;
  const encontrada = catalogo.areas.find((area) => area.cursos.includes(normalizado));
  if (encontrada) return encontrada;
  if (normalizarTexto(curso).startsWith("licenciatura")) {
    return catalogo.areas.find((area) => area.nome === "educacao") ?? null;
  }
  return null;
}
