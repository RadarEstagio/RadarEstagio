import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";
import { areaDoCurso, normalizarCurso } from "../../src/domain/cursos.js";

const pastaDoTeste = dirname(fileURLToPath(import.meta.url));
const lerJson = (caminho) => JSON.parse(readFileSync(resolve(pastaDoTeste, caminho), "utf8"));
const catalogo = lerJson("../../assets/areas.json");
const esperado = lerJson("../../../tests/fixtures/cursos_normalizados.json");

test.each(Object.entries(esperado))("normalização do curso %s bate com a do backend", (curso, [normalizado, area]) => {
  expect(normalizarCurso(curso, catalogo)).toBe(normalizado);
  expect(areaDoCurso(curso, catalogo)?.nome ?? null).toBe(area);
});
